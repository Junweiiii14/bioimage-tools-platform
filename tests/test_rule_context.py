"""A real temporary Git repository exercises rule drift and scope failures."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tooling.rule_context import (
    CORE,
    RECOVERY,
    ROOT,
    IntegrationContext,
    git,
    make_integration_context,
    make_receipt,
    validate,
)


def commit(root: Path, message: str) -> str:
    git(root, "add", ".")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD").decode().strip()


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str]:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "core.autocrlf", "false")
    for name in CORE:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("Original rule\n", encoding="utf-8")
    base = commit(tmp_path, "base")
    task = tmp_path / "work/tasks/F-002-example.md"
    task.parent.mkdir(parents=True)
    task.write_text("Scoped example", encoding="utf-8")
    return tmp_path, base


def record(root: Path, base: str, scopes: list[str] | None = None) -> None:
    receipt = make_receipt(root, "F-002", scopes or ["."], base)
    output = root / "work/evidence/F-002/rules-context.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt), encoding="utf-8")


def test_missing_receipt_is_rejected(repo: tuple[Path, str]) -> None:
    root, base = repo
    assert "exactly one" in validate(root, base, commit(root, "no receipt"))[0]


def test_valid_receipt_passes(repo: tuple[Path, str]) -> None:
    root, base = repo
    record(root, base)
    assert validate(root, base, commit(root, "valid")) == []


def test_changed_rule_requires_reload(repo: tuple[Path, str]) -> None:
    root, base = repo
    record(root, base)
    (root / "AGENTS.md").write_text("New rule\n", encoding="utf-8")
    assert "rules changed" in validate(root, base, commit(root, "stale"))[0]
    record(root, base)
    assert validate(root, base, commit(root, "refreshed")) == []


def test_new_nested_rule_requires_reload(repo: tuple[Path, str]) -> None:
    root, base = repo
    record(root, base)
    (root / "work/AGENTS.md").write_text("Nested rule\n", encoding="utf-8")
    assert "nested rules" in validate(root, base, commit(root, "new nested"))[0]


def test_override_cannot_hide_base_rule(repo: tuple[Path, str]) -> None:
    root, base = repo
    (root / "AGENTS.override.md").write_text("Override\n", encoding="utf-8")
    record(root, base)
    receipt = make_receipt(root, "F-002", ["."], base)
    assert {"AGENTS.md", "AGENTS.override.md"} <= receipt["rules"].keys()


def test_scope_expansion_requires_reload(repo: tuple[Path, str]) -> None:
    root, base = repo
    record(root, base, ["work"])
    (root / "unexpected.py").write_text("print('hello')\n", encoding="utf-8")
    assert "outside loaded scope" in validate(root, base, commit(root, "extra scope"))[0]


def test_scoped_receipt_loads_ancestors_and_descendants_without_sibling_rules(
    repo: tuple[Path, str],
) -> None:
    root, _ = repo
    applicable = {
        "tools/AGENTS.md",
        "tools/wb/AGENTS.md",
        "tools/wb/AGENTS.override.md",
        "tools/wb/ui/AGENTS.md",
    }
    siblings = {"tools/if/AGENTS.md", "apps/AGENTS.md"}
    for name in applicable | siblings:
        rule = root / name
        rule.parent.mkdir(parents=True, exist_ok=True)
        rule.write_text(f"Rule for {name}\n", encoding="utf-8")
    base = commit(root, "separate module rules")
    scopes = ["tools/wb", "work"]
    receipt = make_receipt(root, "F-002", scopes, base)
    assert set(receipt["rules"]) == set(CORE) | applicable
    assert set(receipt["base_rules"]) == set(CORE) | applicable
    record(root, base, scopes)
    (root / "tools/wb/ui/changed.py").write_text("pass\n", encoding="utf-8")
    assert validate(root, base, commit(root, "covered module update")) == []

    (root / "tools/wb/ui/AGENTS.md").write_text("Changed nested rule\n", encoding="utf-8")
    assert "rules changed" in validate(root, base, commit(root, "nested rule drift"))[0]
    record(root, base, scopes)
    assert validate(root, base, commit(root, "reload scoped rule")) == []


@pytest.mark.parametrize("outside", ["tools/if/changed.py", "tools/wb_extra/changed.py"])
def test_scoped_receipt_cannot_cover_a_sibling_or_same_prefix_directory(
    repo: tuple[Path, str], outside: str
) -> None:
    root, base = repo
    record(root, base, ["tools/wb", "work"])
    extra = root / outside
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("pass\n", encoding="utf-8")
    error = validate(root, base, commit(root, "outside module update"))[0]
    assert "outside loaded scope" in error and outside in error


def test_stale_base_is_rejected(repo: tuple[Path, str]) -> None:
    root, base = repo
    record(root, base)
    head = commit(root, "record old base")
    # Advance the baseline separately; make sure a reused receipt cannot claim a new base.
    git(root, "checkout", "-qb", "new-base", base)
    (root / "base-update.txt").write_text("new baseline", encoding="utf-8")
    new_base = commit(root, "advance baseline")
    assert "base is stale" in validate(root, new_base, head)[0]


def test_malformed_receipt_fails_closed(repo: tuple[Path, str]) -> None:
    root, base = repo
    record(root, base)
    (root / "work/evidence/F-002/rules-context.json").write_text("[]", encoding="utf-8")
    assert "must be an object" in validate(root, base, commit(root, "bad json"))[0]


@pytest.mark.parametrize("scope", ["../outside", "/absolute", "C:/outside", "work\\tasks"])
def test_unsafe_scopes_are_rejected(repo: tuple[Path, str], scope: str) -> None:
    root, base = repo
    with pytest.raises(ValueError):
        make_receipt(root, "F-002", [scope], base)


def test_crlf_receipt_matches_lf_git_rules(repo: tuple[Path, str]) -> None:
    root, base = repo
    (root / "AGENTS.md").write_bytes(b"Original rule\r\n")
    record(root, base)
    (root / "AGENTS.md").write_bytes(b"Original rule\n")
    assert validate(root, base, commit(root, "portable receipt")) == []


def test_missing_core_rule_is_rejected(repo: tuple[Path, str]) -> None:
    root, base = repo
    record(root, base)
    (root / "AGENTS.md").unlink()
    assert "missing" in validate(root, base, commit(root, "deleted rules"))[0]


def test_cli_emits_readable_utf8_in_legacy_windows_encoding(repo: tuple[Path, str]) -> None:
    root, base = repo
    script = root / "tooling/rule_context.py"
    script.parent.mkdir()
    shutil.copyfile(ROOT / "tooling/rule_context.py", script)
    for name in RECOVERY:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("Recovery state", encoding="utf-8")
    (root / "AGENTS.md").write_text("规则：原始图像不可覆盖。\n", encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "cp936"}
    result = subprocess.run(
        [sys.executable, str(script), "load", "--task", "F-002", "--scope", ".", "--base", base],
        capture_output=True,
        env=env,
        check=True,
    )
    assert "规则：原始图像不可覆盖。" in result.stdout.decode("utf-8")


def historical_tasks(root: Path, base: str) -> IntegrationContext:
    for task in ("T-001", "T-002"):
        task_file = root / f"work/tasks/{task}-historic.md"
        task_file.write_text("Historic scoped task", encoding="utf-8")
        output = root / f"work/evidence/{task}/rules-context.json"
        output.parent.mkdir(parents=True)
        output.write_text(json.dumps(make_receipt(root, task, ["."], base)), encoding="utf-8")
        commit(root, task)
    record(root, base)
    return make_integration_context(root, "F-002", base)


def save_integration(root: Path, integration: IntegrationContext) -> None:
    (root / "work/evidence/F-002/integration-context.json").write_text(
        json.dumps(integration), encoding="utf-8"
    )


def test_multiple_receipts_still_require_explicit_manifest(repo: tuple[Path, str]) -> None:
    root, base = repo
    historical_tasks(root, base)
    assert "exactly one" in validate(root, base, commit(root, "no manifest"))[0]


def test_integration_preserves_and_checks_every_historical_source(repo: tuple[Path, str]) -> None:
    root, base = repo
    integration = historical_tasks(root, base)
    originals = {
        path: git(root, "show", f"{source}:{path}")
        for path, source in integration["historical_receipts"].items()
    }
    save_integration(root, integration)
    assert validate(root, base, commit(root, "explicit integration")) == []
    assert all((root / path).read_bytes() == data for path, data in originals.items())


@pytest.mark.parametrize(
    "change", ["missing", "extra", "wrong-base", "wrong-task", "invalid-source"]
)
def test_integration_manifest_fails_closed(repo: tuple[Path, str], change: str) -> None:
    root, base = repo
    integration = historical_tasks(root, base)
    if change == "missing":
        integration["historical_receipts"].pop("work/evidence/T-001/rules-context.json")
    elif change == "extra":
        integration["historical_receipts"]["../outside.json"] = base
    elif change == "wrong-base":
        integration["base_commit"] = integration["source_head"]
    elif change == "wrong-task":
        integration["task"] = "T-001"
    else:
        integration["historical_receipts"]["work/evidence/T-001/rules-context.json"] = "HEAD"
    save_integration(root, integration)
    assert validate(root, base, commit(root, "invalid integration"))


def test_integration_rejects_changed_historical_bytes(repo: tuple[Path, str]) -> None:
    root, base = repo
    integration = historical_tasks(root, base)
    historic = root / "work/evidence/T-001/rules-context.json"
    historic.write_text(historic.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    save_integration(root, integration)
    assert "immutable source" in validate(root, base, commit(root, "changed original"))[0]


def test_recording_integration_rejects_uncommitted_history_edits(repo: tuple[Path, str]) -> None:
    root, base = repo
    historical_tasks(root, base)
    (root / "work/evidence/T-001/rules-context.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Commit and verify"):
        make_integration_context(root, "F-002", base)


def test_historical_rule_drift_requires_auditable_reload(repo: tuple[Path, str]) -> None:
    root, base = repo
    integration = historical_tasks(root, base)
    path = "work/evidence/T-001/rules-context.json"
    historic = make_receipt(root, "T-001", ["."], base)
    historic["rules"]["AGENTS.md"] = "0" * 64
    (root / path).write_text(json.dumps(historic), encoding="utf-8")
    bad_source = commit(root, "stale history record")
    integration["source_head"] = bad_source
    integration["historical_receipts"][path] = bad_source
    save_integration(root, integration)
    assert "rules changed" in validate(root, base, commit(root, "cannot waive drift"))[0]
    original_bytes = git(root, "show", f"{bad_source}:{path}")
    (root / path).write_text(json.dumps(make_receipt(root, "T-001", ["."], base)), encoding="utf-8")
    corrected = commit(root, "explicit historical rule reload")
    record(root, base)
    integration = make_integration_context(root, "F-002", base)
    assert integration["historical_receipts"][path] == corrected
    save_integration(root, integration)
    assert validate(root, base, commit(root, "integration after recorded reload")) == []
    assert git(root, "show", f"{bad_source}:{path}") == original_bytes


def test_historical_source_from_another_branch_is_rejected(repo: tuple[Path, str]) -> None:
    root, base = repo
    integration = historical_tasks(root, base)
    actual = git(root, "rev-parse", "HEAD").decode().strip()
    git(root, "checkout", "-qb", "unrelated", base)
    (root / "unrelated.txt").write_text("other branch", encoding="utf-8")
    other = commit(root, "unrelated source")
    git(root, "checkout", "--detach", actual)
    record(root, base)
    integration["historical_receipts"]["work/evidence/T-001/rules-context.json"] = other
    save_integration(root, integration)
    assert "not an ancestor" in validate(root, base, commit(root, "foreign source"))[0]


@pytest.mark.parametrize("change", ["scope", "head-rule", "base", "task"])
def test_integration_does_not_waive_current_checks(repo: tuple[Path, str], change: str) -> None:
    root, base = repo
    integration = historical_tasks(root, base)
    if change == "scope":
        record(root, base, ["work"])
        (root / "outside.py").write_text("pass\n", encoding="utf-8")
    elif change == "head-rule":
        (root / "AGENTS.md").write_text("Changed current rules", encoding="utf-8")
    elif change == "base":
        receipt = make_receipt(root, "F-002", ["."], integration["source_head"])
        (root / "work/evidence/F-002/rules-context.json").write_text(
            json.dumps(receipt), encoding="utf-8"
        )
    else:
        (root / "work/tasks/F-002-example.md").unlink()
    save_integration(root, integration)
    assert validate(root, base, commit(root, "current context invalid"))
