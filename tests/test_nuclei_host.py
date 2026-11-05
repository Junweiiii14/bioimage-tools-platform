"""Actual host assembly failure and workspace preservation without research deps."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from bioimage_app.nuclei_cli import prepare
from bioimage_app.nuclei_workflow_host import NucleiHost
from PIL import Image
from platform_runtime.api import WorkspaceError


def test_nuclei_workspace_has_frozen_original_and_cannot_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source.tif"
    Image.fromarray(np.zeros((16, 24), dtype=np.uint8)).save(source)
    host = NucleiHost(sys.executable, str(tmp_path / "missing-model"))
    workspace = tmp_path / "workspace"
    plan = prepare(workspace, str(source), host)
    assert len(plan.nodes) == 1
    assert plan.nodes[0].interface.module.module_id == "nuclei-stardist-research"
    assert {item.name for item in plan.outputs} == {"labels", "provenance"}
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    with pytest.raises(WorkspaceError):
        prepare(workspace, str(source), host)
    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert before == after


def test_real_host_failure_does_not_publish_empty_success(tmp_path: Path) -> None:
    source = tmp_path / "source.tif"
    Image.fromarray(np.zeros((16, 24), dtype=np.uint8)).save(source)
    original = source.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "bioimage_app.nuclei_cli",
            "--workspace",
            str(tmp_path / "workspace"),
            "--source",
            str(source),
            "--worker-python",
            sys.executable,
            "--model-directory",
            str(tmp_path / "model"),
            "--timeout-seconds",
            "20",
        ],
        capture_output=True,
        timeout=35,
        check=False,
    )
    assert result.returncode != 0
    messages = [json.loads(line) for line in result.stdout.decode().splitlines()]
    finished = messages[-1]
    assert finished["phase"] == "finished"
    assert finished["state"] == "failed"
    assert finished["outputs"] == {}
    assert source.read_bytes() == original
