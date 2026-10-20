"""Opt-in read-only timing observer for existing real desktop/process regressions.

Load explicitly with -p tests.intake_timing_observer and a new output directory.
No scientific input, expected result, grace period, or timeout is changed.
"""

import json
import os
import time
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from bioimage_app.web_window import WebWorkbenchWindow
    from pytestqt.qtbot import QtBot


class ItemRequest(Protocol):
    node: pytest.Item


@pytest.fixture(autouse=True)
def observe_intake_timing(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, qtbot: "QtBot"
) -> Generator[None, None, None]:
    item = cast(ItemRequest, request).node
    directory = os.environ.get("BIOIMAGE_INTAKE_TIMING_DIR")
    if not directory:
        yield
        return
    from bioimage_app.api import ProcessOutcome, ProcessRunner
    from PySide6.QtCore import QTimer
    from shiboken6 import isValid
    from wb_tool.api import WBIntakeWorkflowProject

    phases: list[dict[str, object]] = []
    cancellations: list[dict[str, object]] = []
    running: dict[tuple[str, str, str, int], float] = {}
    cancel_times: list[float] = []
    window = None
    if item.name.startswith(("test_complete_intake_fig_", "test_cancelled_intake_measurement_")):
        window = cast("WebWorkbenchWindow", request.getfixturevalue("intake_window"))
        original_host_cancel = window.host.cancel

        def cancelled() -> None:
            if window.host.operation_busy:
                cancel_times.append(time.perf_counter())
            original_host_cancel()

        monkeypatch.setattr(window.host, "cancel", cancelled)

    original_cancel = ProcessRunner.cancel

    def process_cancel(runner: ProcessRunner, *, grace_ms: int = 5000) -> None:
        started = time.perf_counter()

        def completed(outcome: ProcessOutcome) -> None:
            cancellations.append(
                {
                    "scope": "owned_process_tree",
                    "seconds": time.perf_counter() - started,
                    "grace_ms": grace_ms,
                    "pid": outcome.pid,
                    "exit_code": outcome.exit_code,
                    "cancel_requested": outcome.cancel_requested,
                    "error": outcome.error,
                }
            )

        runner.finished.connect(completed)
        original_cancel(runner, grace_ms=grace_ms)

    monkeypatch.setattr(ProcessRunner, "cancel", process_cancel)

    def observe() -> None:
        if window is None or not isValid(window) or not isValid(window.host):
            return
        now = time.perf_counter()
        try:
            project = window.host.view.project()
        except ValueError:
            return
        if isinstance(project, WBIntakeWorkflowProject):
            for step in project.workflow.steps:
                key = (project.project_id, step.stage, step.target_id, step.attempt)
                if step.status == "running":
                    running.setdefault(key, now)
                elif key in running:
                    phases.append(
                        {
                            "stage": step.stage,
                            "target_id": step.target_id,
                            "attempt": step.attempt,
                            "observed_seconds": now - running.pop(key),
                            "terminal": step.status,
                        }
                    )
        if not window.host.operation_busy and not window.host.has_unsaved_changes:
            while cancel_times:
                cancellations.append(
                    {
                        "scope": "intake_controller_to_saved_idle",
                        "seconds": now - cancel_times.pop(0),
                    }
                )

    timer = QTimer()
    timer.timeout.connect(observe)
    timer.start(10)
    try:
        yield
    finally:
        observe()
        timer.stop()
        timer.deleteLater()
        qtbot.waitUntil(lambda: not isValid(timer), timeout=10000)
        folder = Path(directory)
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / (item.name + "-" + uuid4().hex + ".json")
        with target.open("x", encoding="utf-8") as stream:
            json.dump(
                {
                    "test": item.nodeid,
                    "poll_resolution_seconds": 0.010,
                    "phases": phases,
                    "cancellations": cancellations,
                    "limitations": (
                        "Observed committed stage transitions with a 10ms GUI timer; "
                        "may miss very short stages. One synthetic two-source real-worker "
                        "scenario, not actual instrument performance or a percentile population. "
                        "Controller cancellation holds the next worker before launch; "
                        "process-tree cancellation uses a separate synthetic stubborn "
                        "subprocess with explicit unchanged grace."
                    ),
                },
                stream,
                indent=2,
            )
