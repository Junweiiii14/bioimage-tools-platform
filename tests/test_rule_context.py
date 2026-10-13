"""A real temporary Git repository exercises rule drift and scope failures."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tooling.rule_context import CORE, RECOVERY, ROOT, git, make_receipt, validate


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
