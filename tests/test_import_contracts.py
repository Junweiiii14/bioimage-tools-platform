"""Exercise Import Linter against independent positive and transitive negative graphs."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "violation",
    [
        "none",
        "storage",
        "reverse-layer",
        "independence",
        "concrete-adapter",
        "runtime-tool",
        "contracts-storage",
        "contracts-runtime",
        "host-tool",
        "lower-host",
    ],
)
def test_import_linter_rejects_transitive_dependencies(tmp_path: Path, violation: str) -> None:
    package = tmp_path / "wb_tool"
    domain = package / "domain"
    domain.mkdir(parents=True)
    application = package / "application"
    application.mkdir()
    (application / "__init__.py").write_text("", encoding="utf-8")
    (application / "analysis.py").write_text("VALUE = 1\n", encoding="utf-8")
    adapters = package / "adapters"
    adapters.mkdir()
    (adapters / "__init__.py").write_text("", encoding="utf-8")
    (adapters / "tiff_input.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    for owner in ("tool_contracts", "platform_runtime", "bioimage_app"):
        folder = tmp_path / owner
        folder.mkdir()
        (folder / "__init__.py").write_text("", encoding="utf-8")
        (folder / "api.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "bioimage_app" / "storage.py").write_text("VALUE = 1\n", encoding="utf-8")
    (domain / "__init__.py").write_text("", encoding="utf-8")
    (package / "api.py").write_text("from wb_tool.domain import quantify\n", encoding="utf-8")
    (domain / "quantify.py").write_text("from wb_tool.domain import bridge\n", encoding="utf-8")
    bridge = {
        "none": "VALUE = 1\n",
        "storage": "import sqlite3\n",
        "reverse-layer": "from wb_tool import api\n",
        "independence": "VALUE = 1\n",
        "concrete-adapter": "VALUE = 1\n",
        "runtime-tool": "VALUE = 1\n",
        "contracts-storage": "VALUE = 1\n",
        "contracts-runtime": "VALUE = 1\n",
        "host-tool": "VALUE = 1\n",
        "lower-host": "VALUE = 1\n",
    }[violation]
    (domain / "bridge.py").write_text(bridge, encoding="utf-8")
    if violation == "host-tool":
        (tmp_path / "bioimage_app" / "storage.py").write_text(
            "from bioimage_app import bridge\n", encoding="utf-8"
        )
        (tmp_path / "bioimage_app" / "bridge.py").write_text(
            "from wb_tool import api\n", encoding="utf-8"
        )
    if violation == "lower-host":
        (tmp_path / "platform_runtime" / "api.py").write_text(
            "from platform_runtime import bridge\n", encoding="utf-8"
        )
        (tmp_path / "platform_runtime" / "bridge.py").write_text(
            "from bioimage_app import api\n", encoding="utf-8"
        )
    if violation in ("runtime-tool", "contracts-storage", "contracts-runtime"):
        owner = "platform_runtime" if violation == "runtime-tool" else "tool_contracts"
        folder = tmp_path / owner
        (folder / "api.py").write_text(f"from {owner} import bridge\n", encoding="utf-8")
        dependency = {
            "runtime-tool": "from wb_tool import api\n",
            "contracts-storage": "import sqlite3\n",
            "contracts-runtime": "from platform_runtime import api\n",
        }[violation]
        (folder / "bridge.py").write_text(dependency, encoding="utf-8")
    if violation == "concrete-adapter":
        (application / "analysis.py").write_text(
            "from wb_tool.application import bridge\n", encoding="utf-8"
        )
        (application / "bridge.py").write_text(
            "from wb_tool.adapters import tiff_input\n", encoding="utf-8"
        )
    if violation == "independence":
        (adapters / "tiff_input.py").write_text(
            "from wb_tool.adapters import bridge\n", encoding="utf-8"
        )
        (adapters / "bridge.py").write_text(
            "from wb_tool.domain import quantify\n", encoding="utf-8"
        )
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
    assert ("BROKEN" if violation != "none" else "Contracts: 9 kept") in result.stdout
