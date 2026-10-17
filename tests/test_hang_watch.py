"""Diagnostic observation preserves child errors, privacy, and process ownership."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import dev
from tooling.hang_watch import run_with_native_watch


@pytest.mark.parametrize("capture_fails", [False, True])
def test_idle_capture_cannot_hide_child_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], capture_fails: bool
) -> None:
    observed: list[int] = []

    def capture(pid: int) -> None:
        observed.append(pid)
        if capture_fails:
            raise ValueError("private-diagnostic-error-text")

    code = (
        "import sys,time; print('start',flush=True); time.sleep(.3);"
        "print('end',flush=True); sys.exit(17)"
    )
    assert (
        run_with_native_watch(
            [sys.executable, "-I", "-c", code],
            cwd=tmp_path,
            env=dict(os.environ),
            idle_seconds=0.05,
            capture=capture,
        )
        == 17
    )
    assert observed and len(set(observed)) == 1 and observed[0] != os.getpid()
    text = capsys.readouterr().out
    assert "start" in text and "end" in text
    assert "private-diagnostic-error-text" not in text
    assert "Observed child exit=17 u32=0x00000011" in text
    if capture_fails:
        assert "Native snapshot unavailable: ValueError" in text


def test_progressing_child_has_no_snapshot(tmp_path: Path) -> None:
    observed: list[int] = []
    assert (
        run_with_native_watch(
            [sys.executable, "-I", "-c", "print('progress',flush=True)"],
            cwd=tmp_path,
            env=dict(os.environ),
            idle_seconds=3,
            capture=observed.append,
        )
        == 0
    )
    assert not observed


def test_watch_opt_in_is_not_inherited_by_the_test_child(monkeypatch: pytest.MonkeyPatch) -> None:
    environments: list[dict[str, str]] = []

    def run(
        command: list[str], *, cwd: Path, env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[bytes]:
        environments.append(env)
        return subprocess.CompletedProcess(command, 13)

    def watch(command: list[str], *, cwd: Path, env: dict[str, str]) -> int:
        environments.append(env)
        return 13

    monkeypatch.setenv("BIOIMAGE_NATIVE_STACKS", "1")
    monkeypatch.setenv("PYTHONFAULTHANDLER", "1")
    monkeypatch.setattr(dev.subprocess, "run", run)
    monkeypatch.setattr("tooling.hang_watch.run_with_native_watch", watch)
    assert dev.run_module("pytest", "-q") == 13
    assert environments[0]["QT_QPA_PLATFORM"] == "offscreen"
    assert "BIOIMAGE_NATIVE_STACKS" not in environments[0]
    assert environments[0]["PYTHONFAULTHANDLER"] == "1"
    assert os.environ["BIOIMAGE_NATIVE_STACKS"] == "1"


def test_native_collector_platform_guard_and_owned_child(tmp_path: Path) -> None:
    helper = Path(__file__).resolve().parents[1] / "tooling/windows_native_stacks.py"
    with subprocess.Popen([sys.executable, "-I", "-c", "import time; time.sleep(15)"]) as child:
        try:
            wrong_owner = subprocess.run(
                [sys.executable, "-I", str(helper), str(child.pid), str(child.pid)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            assert wrong_owner.returncode == 1
            result = subprocess.run(
                [sys.executable, "-I", str(helper), str(child.pid), str(os.getpid())],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if sys.platform == "win32":
                assert result.returncode == 0, result.stdout
                assert "NATIVE_STACKS" in result.stdout and "THREAD" in result.stdout
                assert "ntdll.dll" in result.stdout.lower()
                assert "python312.dll" in result.stdout.lower()
                assert str(tmp_path) not in result.stdout
            else:
                assert result.returncode == 1
                assert "Native capture unavailable: ValueError" in result.stdout
        finally:
            child.terminate()
            child.wait(timeout=10)
