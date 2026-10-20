"""Installed diagnostic startup faults still retire their real owned Qt host."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("phase", ["show", "start_from_images"])
def test_intake_diagnostic_startup_failure_closes_constructed_window(
    tmp_path: Path, phase: str
) -> None:
    report = tmp_path / "startup-failure.json"
    source = """
import sys
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from bioimage_app.web_window import WebWorkbenchWindow
from bioimage_app.installation_check_intake import verify_intake_installation

def broken(*args, **kwargs):
    raise RuntimeError('controlled startup failure ' + sys.argv[1])

with patch.object(WebWorkbenchWindow, sys.argv[1], broken):
    code = verify_intake_installation(Path(sys.argv[2]))
raise SystemExit(code)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", source, phase, str(report)],
        env={
            **os.environ,
            "QT_QPA_PLATFORM": "offscreen",
            **{
                name: "1"
                for name in (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                )
            },
        },
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 1, result.stderr
    data = json.loads(report.read_bytes())
    assert data["phase"] == "failed"
    assert any("controlled startup failure " + phase in error for error in data["errors"])
    assert "owned-resources-closed" in data["checks"]
    assert "owned-window-deleted" in data["checks"]
    assert "complete-output" not in data["checks"]


def test_original_gray_diagnostic_completes_real_cli_workflow(tmp_path: Path) -> None:
    report = tmp_path / "gray-diagnostic.json"
    result = subprocess.run(
        [sys.executable, "-I", "-m", "bioimage_app", "--verify-installation", str(report)],
        env={
            **os.environ,
            "QT_QPA_PLATFORM": "offscreen",
            "QTWEBENGINE_CHROMIUM_FLAGS": "--disable-gpu",
            "PYTHONIOENCODING": "utf-8",
            **{
                name: "1"
                for name in (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                )
            },
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, (
        result.stdout + result.stderr + report.read_text(encoding="utf-8")
    )
    data = json.loads(report.read_bytes())
    assert data["phase"] == "passed" and data["errors"] == []
    assert {
        "durable-worker",
        "offline-ocr",
        "saved-project-reopen",
        "save-failure-visible",
        "busy-exit-confirmation",
        "post-cancel-dirty-confirmation",
    }.issubset(data["checks"])


def test_grouped_diagnostic_uses_real_cli_workers_and_shipped_shortcuts(tmp_path: Path) -> None:
    report = tmp_path / "grouped-diagnostic.json"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "bioimage_app",
            "--verify-grouped-intake-installation",
            str(report),
        ],
        env={
            **os.environ,
            "QT_QPA_PLATFORM": "offscreen",
            "QTWEBENGINE_CHROMIUM_FLAGS": "--disable-gpu",
            "PYTHONIOENCODING": "utf-8",
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, (
        result.stdout + result.stderr + report.read_text(encoding="utf-8")
    )
    data = json.loads(report.read_bytes())
    assert data["diagnostic"] == "grouped_intake_installed@1"
    assert data["phase"] == "passed" and data["errors"] == []
    assert data["isolated_imports"] is True
    assert len(data["worker_pids"]) == 2 and all(pid > 0 for pid in data["worker_pids"])
    assert {
        "incomplete-group-draft",
        "grouped-stable-mapping",
        "shortcut-settings",
        "original-pixel-crops",
        "saved-project-reopen",
        "repeat-export-no-overwrite",
        "archive-imported-history",
        "archive-resume-output",
        "owned-resources-closed",
        "owned-window-deleted",
    }.issubset(data["checks"])


def test_sequence_diagnostic_uses_real_page_workers_and_stage_navigation(tmp_path: Path) -> None:
    report = tmp_path / "sequence-diagnostic.json"
    result = subprocess.run(
        [sys.executable, "-I", "-m", "bioimage_app", "--verify-sequence-installation", str(report)],
        env={
            **os.environ,
            "QT_QPA_PLATFORM": "offscreen",
            "QTWEBENGINE_CHROMIUM_FLAGS": "--disable-gpu",
            "PYTHONIOENCODING": "utf-8",
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, (
        result.stdout + result.stderr + report.read_text(encoding="utf-8")
    )
    data = json.loads(report.read_bytes())
    assert data["diagnostic"] == "fig_sequence_installed@1"
    assert data["stage_event_source"] == "committed-save-callback"
    assert len({(e["stage"], e["target"]) for e in data["stage_events"]}) == 7
    assert all(e["revision"] > 0 for e in data["stage_events"])
    assert data["phase"] == "passed" and data["errors"] == []
    assert data["isolated_imports"] is True
    assert len(data["worker_pids"]) == 2 and all(pid > 0 for pid in data["worker_pids"])
    assert all(mode in data["page_modes"] for mode in ("review", "layout", "quant", "results"))
    assert {
        "top-fields-one-start",
        "whole-batch-pause",
        "two-human-continues",
        "stage-barriers",
        "original-pixel-crops",
        "missing-is-not-zero",
        "committed-output",
        "safe-reopen",
        "originals-unchanged",
        "owned-resources-closed",
        "owned-window-deleted",
    }.issubset(data["checks"])
