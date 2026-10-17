"""GUI checks must stay headless and preserve failures without changing caller settings."""

import os
import subprocess
from pathlib import Path

import pytest

import dev


@pytest.mark.parametrize(
    ("module", "expected"),
    [("pytest", "offscreen"), ("tooling.installed_wheels", "offscreen"), ("ruff", "windows")],
)
def test_check_environment_is_isolated_and_exit_code_preserved(
    monkeypatch: pytest.MonkeyPatch, module: str, expected: str
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "windows")
    environments: list[dict[str, str]] = []

    def run(
        command: list[str], *, cwd: Path, env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[bytes]:
        environments.append(env)
        return subprocess.CompletedProcess(command, 19)

    monkeypatch.setattr(dev.subprocess, "run", run)
    assert dev.run_module(module) == 19
    assert environments[0]["QT_QPA_PLATFORM"] == expected
    assert os.environ["QT_QPA_PLATFORM"] == "windows"
