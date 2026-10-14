"""Exercise Import Linter against independent positive and transitive negative graphs."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("violation", ["none", "storage", "reverse-layer"])
def test_import_linter_rejects_transitive_dependencies(tmp_path: Path, violation: str) -> None:
    package = tmp_path / "wb_tool"
    domain = package / "domain"
    domain.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (domain / "__init__.py").write_text("", encoding="utf-8")
    (package / "api.py").write_text("from wb_tool.domain import quantify\n", encoding="utf-8")
    (domain / "quantify.py").write_text("from wb_tool.domain import bridge\n", encoding="utf-8")
    bridge = {
        "none": "VALUE = 1\n",
        "storage": "import sqlite3\n",
        "reverse-layer": "from wb_tool import api\n",
    }[violation]
    (domain / "bridge.py").write_text(bridge, encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(tmp_path)}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from importlinter.cli import lint_imports_command; lint_imports_command()",
            "--config",
            str(ROOT / ".importlinter"),
            "--no-cache",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == (0 if violation == "none" else 1), result.stdout + result.stderr
    assert ("BROKEN" if violation != "none" else "Contracts: 2 kept") in result.stdout
