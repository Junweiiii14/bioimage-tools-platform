"""Packaged command path and shared asynchronous session, without a GUI window."""

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import tifffile
from bioimage_app.api import create_comparison_session
from platform_runtime.api import Workspace
from pydantic import TypeAdapter
from pytestqt.qtbot import QtBot
from wb_tool.api import AnalysisRequest, wb_validation_input


def cli(tmp_path: Path, *arguments: str, expected_code: int = 0) -> dict[str, Any]:
    env = dict(os.environ)
    env.update(TEMP=str(tmp_path), TMP=str(tmp_path), PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, "-I", "-m", "bioimage_app", *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=45,
        check=False,
    )
    assert result.returncode == expected_code, (result.stdout, result.stderr)
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    "case, status, expected",
    [
        ("triangle_u8", "valid", "40.0"),
        ("triangle_u16", "valid", "4000.0"),
        ("flat_zero", "valid", "0.0"),
        ("invalid_roi", "invalid", ""),
        ("dtype_limits", "quality_review", ""),
    ],
)
def test_headless_command_analytical_cases_and_reopen(
    tmp_path: Path, case: str, status: str, expected: str
) -> None:
    path = tmp_path / case
    result = cli(tmp_path, "--v0-compare", str(path), "--case", case)
    assert result["state"] == "succeeded" and result["run"]["pid"] > 0
    assert result["quality"] == ("complete" if status == "valid" else "issues")
    table = json.loads(result["tables_json"]["measurements"])
    values = dict(zip(table["columns"], table["rows"][0], strict=True))
    assert values["value"] == expected and values["status"] == status
    differences = json.loads(result["tables_json"]["differences"])
    diff = dict(zip(differences["columns"], differences["rows"][0], strict=True))
    assert diff["exact_match"] == "True"
    assert diff["difference"] == ("0.0" if status == "valid" else "")
    reopened = cli(tmp_path, "--v0-open", str(path))
    assert reopened["run"] == result["run"]
    assert reopened["tables_json"] == result["tables_json"]
    assert reopened["files"] == result["files"]
    for name in ("measurements.csv", "differences.csv", "run-manifest.json"):
        assert (path / "v0-compare" / name).is_file()


def test_headless_explicit_input_is_preserved_and_existing_destination_rejected(
    tmp_path: Path,
) -> None:
    fixture = wb_validation_input("triangle_u16")
    source = tmp_path / "source.tif"
    source.write_bytes(fixture.source_bytes)
    parameters = tmp_path / "parameters.json"
    parameters.write_bytes(TypeAdapter(AnalysisRequest).dump_json(fixture.request))
    path = tmp_path / "explicit"
    result = cli(
        tmp_path,
        "--v0-compare",
        str(path),
        "--source",
        str(source),
        "--parameters",
        str(parameters),
    )
    assert result["state"] == "succeeded"
    rejected = cli(tmp_path, "--v0-compare", str(path), expected_code=2)
    assert rejected["state"] == "failed"
    assert source.read_bytes() == fixture.source_bytes
    reopened = cli(tmp_path, "--v0-open", str(path))
    assert reopened["run"] == result["run"]
    corrupted = Path(result["files"]["differences"])
    corrupted.write_bytes(b"corrupted")
    invalid = cli(tmp_path, "--v0-open", str(path), expected_code=2)
    assert invalid["state"] == "failed" and not invalid["files"] and not invalid["tables_json"]


@pytest.mark.parametrize("when", ["preparing", "running"])
def test_shared_session_cancel_drains_services(qtbot: QtBot, tmp_path: Path, when: str) -> None:
    session = create_comparison_session()
    replies: list[str] = []
    session.finished.connect(replies.append)

    def changed(payload: str) -> None:
        if json.loads(payload)["state"] == when:
            session.cancel()

    session.changed.connect(changed)
    session.start_fixture(str(tmp_path / "cancelled"))
    qtbot.waitUntil(lambda: bool(replies), timeout=30000)
    result = json.loads(replies[0])
    assert result["state"] == "cancelled"
    if when == "running":
        assert result["run"]["state"] == "cancelled" and result["run"]["pid"] > 0
        with Workspace.open(tmp_path / "cancelled") as store:
            assert store.get_run(result["run"]["run_id"]).state == "cancelled"
    session.deleteLater()


def test_headless_worker_rejects_unsupported_dtype_with_saved_failure(tmp_path: Path) -> None:
    fixture = wb_validation_input("triangle_u16")
    source = tmp_path / "float.tif"
    tifffile.imwrite(source, np.ones((5, 3), dtype=np.float32), metadata=None)
    original = source.read_bytes()
    parameters = tmp_path / "float-request.json"
    request = replace(fixture.request, source_sha256=hashlib.sha256(original).hexdigest())
    parameters.write_bytes(TypeAdapter(AnalysisRequest).dump_json(request))
    path = tmp_path / "unsupported"
    result = cli(
        tmp_path,
        "--v0-compare",
        str(path),
        "--source",
        str(source),
        "--parameters",
        str(parameters),
        expected_code=2,
    )
    assert result["state"] == "failed"
    assert result["run"]["pid"] > 0 and result["run"]["result"] is None
    assert result["run"]["reason"]
    assert source.read_bytes() == original
    reopened = cli(tmp_path, "--v0-open", str(path), expected_code=2)
    assert reopened["run"] == result["run"] and not reopened["files"]
