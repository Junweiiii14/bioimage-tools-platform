"""Candidate provenance, immutable failure/recovery reports and Windows shell boundaries."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tooling import build_runtime_candidate as builder
from tooling import candidate_acceptance as acceptance
from tooling.acceptance_profile import acceptance_identity
from tooling.runtime_integrity import payload_inventory


def save(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def candidate(tmp_path: Path) -> dict[str, Any]:
    repo = tmp_path / "检出 空格"
    repo.mkdir()
    for name, prefix in acceptance.PACKAGES.items():
        target = repo / prefix / "__init__.py"
        target.parent.mkdir(parents=True)
        target.write_text(f'"""{name} synthetic fixture."""\n', encoding="utf-8", newline="\n")
    sequence = repo / "apps/desktop/src/bioimage_app/installation_check_sequence.py"
    sequence.write_text('"""Synthetic fixture."""\n', encoding="utf-8", newline="\n")
    (repo / "tooling").mkdir()
    (repo / ".gitattributes").write_bytes(b"* text=auto eol=lf\n*.cmd text eol=crlf\n")
    (repo / "tooling/probe.cmd").write_bytes(b"@echo off\nexit /b 0\n")
    (repo / "tooling/toolchain-lock.json").write_text("{}", encoding="utf-8")
    (repo / "uv.lock").write_text("version = 1\n", encoding="utf-8", newline="\n")
    (repo / "pyproject.toml").write_bytes(b"# fixture\n")
    (repo / "dev.py").write_bytes(b"# fixture\n")
    for arguments in (
        ["init", "-q"],
        ["config", "user.name", "Fixture"],
        ["config", "user.email", "fixture@example.invalid"],
        ["config", "core.autocrlf", "false"],
        ["add", "."],
        ["commit", "-qm", "fixture"],
    ):
        subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    output = tmp_path / "候选 空格"
    root = output / "app"
    root.mkdir(parents=True)
    for name, prefix in acceptance.PACKAGES.items():
        shutil.copytree(repo / prefix, root / "runtime/Lib/site-packages" / name)
    (root / "runtime/python.exe").write_bytes(b"fixture private runtime, never executed")
    launcher = root / "BioImageWB-Acceptance.exe"
    launcher.write_bytes(b"fixture launcher, never executed")
    archive = root / "source-code.zip"
    # Only existing fixture paths; the verifier's broader pathspec also finds these.
    subprocess.run(
        [
            "git",
            "archive",
            "--format=zip",
            "--output=" + str(archive),
            commit,
            *acceptance.SOURCE_PATHS,
        ],
        cwd=repo,
        check=True,
    )
    installer = output / "Fixture-Setup.exe"
    installer.write_bytes(b"fixture installer, never executed")
    manifest: dict[str, Any] = {
        "schema": 2,
        "commit": commit,
        "compile_exit": 0,
        "build_inputs_contract": "verified-runtime-inputs@1",
        "uv_lock_sha256": acceptance.digest(repo / "uv.lock"),
        "toolchain": {
            "toolchain_lock_sha256": acceptance.digest(repo / "tooling/toolchain-lock.json")
        },
        "launcher_sha256": acceptance.digest(launcher),
        "runtime_python_sha256": acceptance.digest(root / "runtime/python.exe"),
        **acceptance_identity("t082-probe"),
    }
    fixture = {
        "repo": repo,
        "candidate": output,
        "root": root,
        "commit": commit,
        "installer": installer,
        "manifest": manifest,
    }
    freeze(fixture)
    return fixture


def freeze(fixture: dict[str, Any]) -> None:
    root = fixture["root"]
    manifest = fixture["manifest"]
    save(
        root / "payload-files.json",
        {"schema": 1, "commit": fixture["commit"], "files": payload_inventory(root)},
    )
    manifest["payload_manifest_sha256"] = acceptance.digest(root / "payload-files.json")
    save(root / "build-manifest.json", manifest)
    installer = fixture["installer"]
    save(
        fixture["candidate"] / "build-manifest.json",
        {
            **manifest,
            "installer_exit": 0,
            "artifacts": {
                installer.name: {
                    "sha256": acceptance.digest(installer),
                    "size": installer.stat().st_size,
                }
            },
        },
    )


def arguments(fixture: dict[str, Any], report: Path) -> list[str]:
    return [
        "verify",
        "--candidate",
        str(fixture["candidate"]),
        "--installer",
        str(fixture["installer"]),
        "--installer-sha256",
        acceptance.digest(fixture["installer"]),
        "--source-commit",
        fixture["commit"],
        "--source-repo",
        str(fixture["repo"]),
        "--report-directory",
        str(report),
    ]


def verify(fixture: dict[str, Any], installed: Path | None = None) -> dict[str, Any]:
    return acceptance.verify_candidate(
        fixture["candidate"],
        fixture["installer"],
        acceptance.digest(fixture["installer"]),
        fixture["commit"],
        fixture["repo"],
        installed,
    )


def test_new_checkout_candidate_and_installed_payload_match_exact_source(
    candidate: dict[str, Any], tmp_path: Path
) -> None:
    result = verify(candidate)
    assert result["source"]["shipped_source_files"] == 5
    installed = tmp_path / "安装 空格"
    shutil.copytree(candidate["root"], installed)
    (installed / "unins000.dat").write_bytes(b"installer bookkeeping")
    installed_result = verify(candidate, installed)
    assert installed_result["state"] == "supplied-installation-directory"
    assert installed_result["payload"]["unverified_installer_or_cache_files"] == ["unins000.dat"]


def test_unfrozen_bytecode_is_never_an_execution_input(candidate: dict[str, Any]) -> None:
    cache = candidate["root"] / "runtime/Lib/site-packages/bioimage_app/__pycache__/bad.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"untrusted cache")
    with pytest.raises(ValueError, match="Unexpected"):
        verify(candidate, candidate["root"])
    observed = acceptance.verify_payload(
        candidate["root"], candidate["manifest"], installed=True, allow_generated_caches=True
    )
    assert observed["unverified_installer_or_cache_files"] == [
        "runtime/Lib/site-packages/bioimage_app/__pycache__/bad.pyc"
    ]


@pytest.mark.parametrize("changed", ["payload", "installer", "embedded", "extra", "source"])
def test_tampered_candidate_is_rejected(candidate: dict[str, Any], changed: str) -> None:
    if changed == "payload":
        (candidate["root"] / "runtime/python.exe").write_bytes(b"tampered")
    elif changed == "installer":
        candidate["installer"].write_bytes(b"tampered")
    elif changed == "embedded":
        save(candidate["root"] / "build-manifest.json", {})
    elif changed == "extra":
        (candidate["root"] / "unexpected.dll").write_bytes(b"unexpected")
    else:
        (candidate["root"] / "runtime/Lib/site-packages/bioimage_app/__init__.py").write_text(
            "changed", encoding="utf-8"
        )
        freeze(candidate)  # A rewritten payload manifest cannot conceal a wrong source module.
    with pytest.raises(ValueError):
        verify(candidate)


@pytest.mark.parametrize(
    "path",
    ["../escape", "/absolute", "C:/external", "runtime\\evil", "runtime//evil", "runtime/./evil"],
)
def test_payload_members_cannot_escape_root(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        acceptance.member(tmp_path, path)


def test_failure_and_recovery_keep_distinct_reports(
    candidate: dict[str, Any], tmp_path: Path
) -> None:
    failed = tmp_path / "failed"
    broken = arguments(candidate, failed)
    broken[broken.index("--installer-sha256") + 1] = "0" * 64
    assert acceptance.main(broken) == 1
    previous = failed / "acceptance.json"
    previous_bytes = previous.read_bytes()
    assert json.loads(previous_bytes)["phase"] == "failed"
    recovered = tmp_path / "recovered"
    assert (
        acceptance.main([*arguments(candidate, recovered), "--previous-report", str(previous)]) == 0
    )
    assert previous.read_bytes() == previous_bytes
    recovery = acceptance.document(recovered / "acceptance.json")
    assert recovery["previous_report"]["sha256"] == acceptance.digest(previous)
    with pytest.raises(FileExistsError):
        acceptance.main(arguments(candidate, recovered))


@pytest.mark.parametrize("identifier", ["", "A", "../lab", "lab.name", "a" * 33, 'a"b', "中文"])
def test_disposable_identity_rejects_unsafe_tokens(identifier: str) -> None:
    with pytest.raises(ValueError):
        acceptance_identity(identifier)


@pytest.mark.parametrize("options", [["--acceptance-id", ""], ["--acceptance-id", "test"]])
def test_acceptance_build_rejects_empty_or_nonlaboratory_identity(
    monkeypatch: pytest.MonkeyPatch, options: list[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["builder", "--iscc", "unused", "--gcc", "unused", *options])
    with pytest.raises((ValueError, SystemExit)):
        builder.main()


def test_crlf_equivalence_is_explicit_and_payload_bytes_remain_checked(
    candidate: dict[str, Any],
) -> None:
    module = candidate["root"] / "runtime/Lib/site-packages/bioimage_app/__init__.py"
    module.write_bytes(module.read_bytes().replace(b"\n", b"\r\n"))
    freeze(candidate)
    result = verify(candidate)
    assert result["source"]["crlf_only_source_differences"] == [
        "runtime/Lib/site-packages/bioimage_app/__init__.py"
    ]
    module.write_bytes(module.read_bytes().replace(b"\r\n", b"\n"))
    with pytest.raises(ValueError, match="SHA256"):
        verify(candidate)


def test_diagnostics_refuse_laboratory_identity(candidate: dict[str, Any], tmp_path: Path) -> None:
    verified = verify(candidate)
    verified["manifest"]["distribution_id"] = "BioImageTools.WB.Laboratory"
    with pytest.raises(ValueError, match="inconsistent"):
        acceptance.run_diagnostics(verified, tmp_path, {"processes": [], "diagnostics": []})


def fake_process(fixture: dict[str, Any], *, failed_exit: bool = False, wrong_module: bool = False):
    def execute(
        args: list[str], directory: Path, name: str, timeout: float, env: dict[str, str]
    ) -> dict[str, Any]:
        assert "PYTHONPATH" not in env
        root = fixture["root"]
        if name == "module-probe":
            save(
                directory / f"{name}.stdout",
                {
                    "executable": str(root / "runtime/python.exe"),
                    "isolated": True,
                    "modules": {
                        package: str(root / "runtime/Lib/site-packages" / package / "__init__.py")
                        for package in acceptance.PACKAGES
                    },
                },
            )
        else:
            save(
                Path(args[-1]),
                {
                    "phase": "passed",
                    "checks": ["synthetic"],
                    "errors": [],
                    "diagnostic": "supervision_installed@1",
                    "isolated_imports": True,
                    "release_channel": fixture["manifest"]["release_channel"],
                    "runtime_executable": str(root / "runtime/python.exe"),
                    "package_file": str(
                        root
                        / "runtime/Lib/site-packages/bioimage_app/installation_check_sequence.py"
                    )
                    if not wrong_module
                    else "C:/foreign/module.py",
                    "worker_pids": [1234],
                },
            )
        return {"exit_code": 7 if failed_exit and name == "diagnostic-0" else 0, "timed_out": False}

    return execute


@pytest.mark.parametrize("failure", ["exit", "module", "worker"])
def test_passing_report_cannot_hide_process_or_provenance_failure(
    candidate: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    monkeypatch.setattr(
        acceptance,
        "process",
        fake_process(candidate, failed_exit=failure == "exit", wrong_module=failure == "module"),
    )

    def exited(pid: int) -> bool:
        return failure != "worker"

    monkeypatch.setattr(acceptance, "worker_has_exited", exited)
    verified = verify(candidate)
    message = {
        "exit": "did not exit normally",
        "module": "provenance mismatch",
        "worker": "remains active",
    }[failure]
    with pytest.raises(ValueError, match=message):
        acceptance.run_diagnostics(verified, tmp_path, {"processes": [], "diagnostics": []})


def test_owned_process_timeout_and_real_nonzero_exit(tmp_path: Path) -> None:
    env = dict(os.environ)
    failed = acceptance.process(
        [sys.executable, "-c", "raise SystemExit(7)"], tmp_path, "exit", 10, env
    )
    assert failed["exit_code"] == 7 and failed["timed_out"] is False
    timed_out = acceptance.process(
        [sys.executable, "-c", "import time; time.sleep(30)"], tmp_path, "timeout", 0.1, env
    )
    assert timed_out["timed_out"] is True and timed_out["exit_code"] != 0


def test_two_diagnostics_retain_module_worker_and_process_evidence(
    candidate: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(acceptance, "process", fake_process(candidate))

    def exited(pid: int) -> bool:
        return True

    monkeypatch.setattr(acceptance, "worker_has_exited", exited)
    report: dict[str, Any] = {"processes": [], "diagnostics": []}
    acceptance.run_diagnostics(verify(candidate), tmp_path, report)
    assert len(report["processes"]) == 3
    assert len(report["diagnostics"]) == 2
    assert all(value["reported_workers_exited"] for value in report["diagnostics"])
    assert report["runtime_identity"]["isolated"] is True


@pytest.mark.skipif(sys.platform != "win32", reason="Actual Windows PowerShell 5.1/7 boundary")
@pytest.mark.parametrize("shell", ["powershell.exe", "pwsh.exe"])
def test_windows_wrapper_preserves_unicode_paths_failure_and_recovery(
    candidate: dict[str, Any], tmp_path: Path, shell: str
) -> None:
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} is not installed on this host")
    script = Path(__file__).resolve().parents[1] / "tooling/windows_candidate_acceptance.ps1"
    common = [
        executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-Python",
        sys.executable,
        "-Candidate",
        str(candidate["candidate"]) + "\\",
        "-Installer",
        str(candidate["installer"]),
        "-SourceCommit",
        candidate["commit"],
        "-SourceRepo",
        str(candidate["repo"]) + "\\",
    ]
    failed = tmp_path / "失败 报告"
    result = subprocess.run(
        [*common, "-InstallerSha256", "0" * 64, "-ReportDirectory", str(failed)],
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert acceptance.document(failed / "acceptance.json")["phase"] == "failed"
    recovered = tmp_path / "恢复 报告"
    result = subprocess.run(
        [
            *common,
            "-InstallerSha256",
            acceptance.digest(candidate["installer"]),
            "-ReportDirectory",
            str(recovered),
            "-PreviousReport",
            str(failed / "acceptance.json"),
        ],
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = acceptance.document(recovered / "acceptance.json")
    assert report["environment"]["powershell"]["version"]
    assert report["previous_report"]["phase"] == "failed"
    protected = candidate["root"] / "must-not-create"
    before = payload_inventory(candidate["root"])
    result = subprocess.run(
        [
            *common,
            "-InstallerSha256",
            acceptance.digest(candidate["installer"]),
            "-ReportDirectory",
            str(protected),
        ],
        capture_output=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert not protected.exists()
    assert payload_inventory(candidate["root"]) == before
