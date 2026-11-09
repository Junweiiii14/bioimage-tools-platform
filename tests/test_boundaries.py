"""Negative controls for the rules future product code will be subject to."""

from pathlib import Path

import pytest

from tooling.boundaries import check_repository, violations


@pytest.mark.parametrize(
    ("module", "source"),
    [
        ("platform_runtime.jobs", "import wb_tool.api"),
        ("desktop_sdk.ports", "from tool_contracts.internal import Secret"),
        ("tool_contracts.models", "import numpy"),
        ("imaging_core.reader", "from PySide6.QtCore import QObject"),
        ("wb_tool.domain.quantify", "import subprocess"),
        ("wb_tool.domain.quantify", "from desktop_sdk.api import ToolView"),
        ("wb_tool.domain.quantify", "from ..ui.view import View"),
        ("wb_tool.application.analyze", "from ..adapters.executor import Executor"),
        ("platform_runtime.jobs", "importlib.import_module('wb_tool')"),
    ],
)
def test_reject_invalid_dependencies(module: str, source: str) -> None:
    assert violations(source, module)


@pytest.mark.parametrize(
    ("module", "source"),
    [
        ("platform_runtime.jobs", "from tool_contracts.api import RunRequest"),
        ("wb_tool.domain.quantify", "import numpy as np"),
        ("wb_tool.ui.view", "from desktop_sdk.api import ToolView"),
        ("wb_tool.domain.quantify", "from .models import Result"),
    ],
)
def test_allow_declared_dependencies(module: str, source: str) -> None:
    assert violations(source, module) == []


def test_shared_nuclei_src_only_accepts_registered_owners(tmp_path: Path) -> None:
    src = tmp_path / "tools/nuclei/src"
    for owner in ("nuclei_tool", "nuclei_intensity", "wb_tool", "unknown"):
        (src / owner).mkdir(parents=True)
        (src / owner / "__init__.py").touch()
    count, errors = check_repository(tmp_path)
    assert count == 4
    assert len(errors) == 2
    assert all(any(owner in error for error in errors) for owner in ("wb_tool", "unknown"))
