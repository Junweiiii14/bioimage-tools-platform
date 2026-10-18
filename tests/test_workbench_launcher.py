"""A contaminated caller must not silently launch a different checkout."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tooling.launch_workbench import verify_checkout

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tooling/launch_workbench.py"


def test_isolated_launcher_ignores_old_package_in_caller_and_pythonpath(tmp_path: Path) -> None:
    decoy = tmp_path / "bioimage_app"
    decoy.mkdir()
    (decoy / "__init__.py").write_text("raise RuntimeError('OLD CHECKOUT')\n", encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(tmp_path), "PYTHONUTF8": "1"}
    result = subprocess.run(
        [sys.executable, "-I", str(LAUNCHER), "--verify-launch"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    identity = json.loads(result.stdout)
    assert Path(identity["checkout"]) == ROOT
    assert Path(identity["module"]) == ROOT / "apps/desktop/src/bioimage_app"
    assert Path(identity["interface"]) == ROOT / "apps/desktop/src/bioimage_app/web_ui"
    assert "OLD CHECKOUT" not in result.stderr


def test_launcher_rejects_unisolated_dispatch() -> None:
    result = subprocess.run(
        [sys.executable, str(LAUNCHER), "--verify-launch"],
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 2


def test_wrong_editable_install_is_rejected_before_gui(tmp_path: Path) -> None:
    # A different root, even with complete-looking assets, must not use this
    # environment's installed module. No Qt import or fallback is performed.
    assets = tmp_path / "apps/desktop/src/bioimage_app/web_ui"
    assets.mkdir(parents=True)
    for name in ("index.html", "app.js", "manual_quant.js"):
        (assets / name).write_text("old", encoding="utf-8")
    with pytest.raises(RuntimeError, match="不是此开发目录"):
        verify_checkout(tmp_path)


def test_launcher_dispatches_real_entry_with_arguments() -> None:
    result = subprocess.run(
        [sys.executable, "-I", str(LAUNCHER), "--web-workbenhc"],
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 2
    assert b"unrecognized arguments" in result.stderr
