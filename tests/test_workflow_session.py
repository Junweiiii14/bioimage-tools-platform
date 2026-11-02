"""Production controller automatically dispatches real nodes and persists the final journal."""

import csv
import io
from pathlib import Path

import pytest
from bioimage_app.wb_workflow_host import build_wb_workflow, wb_workflow_registry
from bioimage_app.workflow_preparation import WorkflowHostModule
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus
from platform_runtime.api import Workspace, load_workflow_ledger
from PySide6.QtCore import QThread
from pytestqt.qtbot import QtBot
from tool_contracts.api import (
    CoordinateFrame,
    ExecutionPlan,
    ImageMetadata,
    ScientificAsset,
    ScientificType,
)
from wb_tool.api import wb_validation_input


@pytest.mark.parametrize("mode", ["complete", "pause"])
def test_workflow_controller_runs_actual_three_nodes(
    qtbot: QtBot, tmp_path: Path, mode: str
) -> None:
    fixture = wb_validation_input("triangle_u16")
    original = tmp_path / "original.tif"
    original.write_bytes(fixture.source_bytes)
    workspace = tmp_path / "workspace"
    with Workspace.create(workspace) as store:
        source = store.import_asset(original, fixture.request.source_sha256)
    description = ImageMetadata(
        dtype="uint16",
        axes=("y", "x"),
        shape=(5, 3),
        acquisition_bit_depth=None,
        acquisition_range=None,
        acquisition_range_source=None,
        frame=CoordinateFrame(
            frame_id="original_pixels",
            origin_asset_sha256=source.sha256,
            physical_pixel_size_yx=None,
            physical_unit=None,
        ),
    )
    scientific = ScientificAsset(
        payload=source,
        sample_id="sample",
        producing_method=None,
        parameters_sha256=None,
        description=ScientificType(kind="raw_image", unit="pixel_intensity", image=description),
    )
    _, plan = build_wb_workflow(scientific, fixture.request, revision=7)
    inspections: list[QThread] = []

    def registry(frozen: ExecutionPlan) -> tuple[WorkflowHostModule, ...]:
        inspections.append(QThread.currentThread())
        return wb_workflow_registry(frozen)

    session = WorkflowSession(registry)
    statuses: list[WorkflowStatus] = []
    ended: list[WorkflowStatus] = []
    paused: list[WorkflowStatus] = []
    requested_pause = False

    def changed(status: WorkflowStatus) -> None:
        nonlocal requested_pause
        statuses.append(status)
        if (
            mode == "pause"
            and not requested_pause
            and status.pid is not None
            and status.state == "running"
        ):
            requested_pause = True
            assert session.pause()
        elif mode == "pause" and status.state == "paused" and not paused:
            paused.append(status)
            assert status.completed_nodes == 1
            assert session.resume()

    def completed(_status: WorkflowStatus) -> None:
        session.close()

    session.changed.connect(changed)
    session.completed.connect(completed)
    session.finished.connect(ended.append)
    try:
        session.start(str(workspace), plan)
        qtbot.waitUntil(lambda: bool(ended), timeout=30000)
        assert ended[0].state == "succeeded" and ended[0].message == "", ended
        assert ended[0].completed_nodes == 3 and session.ledger is not None
        ledger = session.ledger
        assert ledger.plan.revision == 7 and len(ledger.attempts) == 3
        assert all(attempt.revision == 0 and attempt.run is not None for attempt in ledger.attempts)
        assert len(inspections) == (2 if mode == "pause" else 1)
        assert all(thread != session.thread() for thread in inspections)
        if mode == "pause":
            assert paused and any(status.state == "pausing" for status in statuses)
    finally:
        if not ended:
            session.close()
            qtbot.waitUntil(lambda: bool(ended), timeout=30000)
    with Workspace.open(workspace) as store:
        actual = load_workflow_ledger(
            store.read_asset(store.load_draft(ledger.execution_id).asset).decode()
        )
        assert actual == ledger and len(store.list_runs()) == 3
        assert all(store.get_run(item.run.run_id) == item.run for item in actual.results)
        outputs = {item.port: item.asset for item in actual.results[-1].outputs}
        rows = list(
            csv.DictReader(
                io.StringIO(store.read_asset(outputs["measurements"]).decode("utf-8-sig"))
            )
        )
        assert rows[0]["value"] == "4000.0" and rows[0]["status"] == "text:valid"
        assert store.read_asset(source) == original.read_bytes() == fixture.source_bytes
