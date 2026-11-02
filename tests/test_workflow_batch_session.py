"""Finite batches use real worker graphs and actual parent/child workspace records."""

import csv
import io
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest
from bioimage_app.wb_workflow_host import build_wb_workflow, wb_workflow_registry
from bioimage_app.workflow_batch_session import WorkflowBatchSession, WorkflowBatchStatus
from bioimage_app.workflow_batch_storage import WorkflowBatchStoreCommand, execute_batch_store
from platform_runtime.api import StateConflict, Workspace, load_workflow_ledger
from pytestqt.qtbot import QtBot
from tool_contracts.api import (
    AssetRef,
    CoordinateFrame,
    DraftSnapshot,
    ImageMetadata,
    ProcessExitReceipt,
    RunRecord,
    ScientificAsset,
    ScientificType,
    WorkflowBatch,
    WorkflowBatchItem,
)
from wb_tool.api import load_tiff, wb_validation_input


@pytest.fixture
def batch_fixture(tmp_path: Path) -> tuple[Path, WorkflowBatch, tuple[AssetRef, ...]]:
    workspace = tmp_path / "batch"
    items: list[WorkflowBatchItem] = []
    sources: list[AssetRef] = []
    with Workspace.create(workspace) as store:
        for index, case in enumerate(("triangle_u16", "triangle_u8")):
            supplied = wb_validation_input(case)
            original = tmp_path / f"original-{index}.tif"
            original.write_bytes(supplied.source_bytes)
            ref = store.import_asset(original, supplied.request.source_sha256)
            image = load_tiff(store.asset_path(ref))
            source = ScientificAsset(
                payload=ref,
                sample_id=f"sample_{index}",
                producing_method=None,
                parameters_sha256=None,
                description=ScientificType(
                    kind="raw_image",
                    unit="pixel_intensity",
                    image=ImageMetadata(
                        dtype="uint16" if image.pixels.dtype.itemsize == 2 else "uint8",
                        axes=("y", "x"),
                        shape=image.pixels.shape,
                        acquisition_bit_depth=None,
                        acquisition_range=None,
                        acquisition_range_source=None,
                        frame=CoordinateFrame(
                            frame_id="original_pixels",
                            origin_asset_sha256=ref.sha256,
                            physical_pixel_size_yx=None,
                            physical_unit=None,
                        ),
                    ),
                ),
            )
            _, plan = build_wb_workflow(source, supplied.request)
            items.append(
                WorkflowBatchItem(sample_id=source.sample_id, execution_id=uuid4().hex, plan=plan)
            )
            sources.append(ref)
    return workspace, WorkflowBatch(batch_id=uuid4().hex, items=tuple(items)), tuple(sources)


@pytest.mark.parametrize(
    "mode", ["complete", "bad_first_source", "cancel_before_dispatch", "cancel_running"]
)
def test_batch_runs_real_samples_and_isolates_failure(
    qtbot: QtBot, batch_fixture: tuple[Path, WorkflowBatch, tuple[AssetRef, ...]], mode: str
) -> None:
    workspace, batch, sources = batch_fixture
    if mode == "bad_first_source":
        with Workspace.open(workspace) as store:
            store.asset_path(sources[0]).write_bytes(b"owned synthetic corrupted TIFF")
    session = WorkflowBatchSession(wb_workflow_registry)
    ended: list[WorkflowBatchStatus] = []
    cancel_requested = False

    def changed(status: WorkflowBatchStatus) -> None:
        nonlocal cancel_requested
        if mode == "cancel_running" and status.child and status.child.pid and not cancel_requested:
            cancel_requested = True
            assert session.cancel()

    def completed(_status: WorkflowBatchStatus) -> None:
        session.close()

    session.completed.connect(completed)
    session.changed.connect(changed)
    session.finished.connect(ended.append)
    try:
        session.start(str(workspace), batch)
        if mode == "cancel_before_dispatch":
            session.close()
        qtbot.waitUntil(lambda: bool(ended), timeout=45000)
        assert not ended[0].message, ended
        expected = (
            "cancelled"
            if mode in ("cancel_before_dispatch", "cancel_running")
            else ("completed_with_issues" if mode == "bad_first_source" else "completed")
        )
        assert ended[0].state == expected
        assert session.batch is not None
        actual = session.batch
    finally:
        session.close()
        qtbot.waitUntil(lambda: bool(ended), timeout=30000)
    with Workspace.open(workspace) as store:
        assert (
            execute_batch_store(store, WorkflowBatchStoreCommand("load", batch.batch_id)) == actual
        )
        assert (
            len(store.list_runs())
            == {
                "complete": 6,
                "bad_first_source": 4,
                "cancel_before_dispatch": 0,
                "cancel_running": 1,
            }[mode]
        )
        if mode not in ("cancel_before_dispatch", "cancel_running"):
            assert actual.items[1].state == "succeeded"
            child = load_workflow_ledger(
                store.read_asset(store.load_draft(actual.items[1].execution_id).asset).decode()
            )
            table = next(
                item.asset for item in child.results[-1].outputs if item.port == "measurements"
            )
            rows = list(csv.DictReader(io.StringIO(store.read_asset(table).decode("utf-8-sig"))))
            assert rows[0]["value"] == "40.0"
        if mode == "bad_first_source":
            assert actual.items[0].state == "failed" and actual.items[0].reason
            assert actual.items[0].completed_nodes == 0
            child = load_workflow_ledger(
                store.read_asset(store.load_draft(actual.items[0].execution_id).asset).decode()
            )
            assert child.state == "failed"
            assert child.attempts[0].run is not None
            physical = store.get_run(child.attempts[0].run.run_id)
            assert physical == child.attempts[0].run
            assert physical.state == "failed" and physical.pid is None
        if mode == "cancel_running":
            assert cancel_requested and actual.items[1].state == "cancelled"
            assert actual.items[1].child_revision is None
            assert store.list_runs()[0].pid is not None


@pytest.mark.parametrize("interruption", ["pause", "parent_write"])
def test_batch_reopen_preserves_real_child_and_reconciles_parent(
    qtbot: QtBot,
    batch_fixture: tuple[Path, WorkflowBatch, tuple[AssetRef, ...]],
    monkeypatch: pytest.MonkeyPatch,
    interruption: str,
) -> None:
    workspace, batch, _sources = batch_fixture
    first = WorkflowBatchSession(wb_workflow_registry)
    first_ended: list[WorkflowBatchStatus] = []
    pause_requested = False
    injected = False
    original_save = Workspace.save_draft

    def save(
        owner: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None,
    ) -> DraftSnapshot:
        nonlocal injected
        if tool_id == "workflow_batch_v1" and not injected:
            proposed = WorkflowBatch.model_validate_json(data, strict=True)
            if proposed.items[0].state == "succeeded":
                injected = True
                raise OSError(28, "injected ENOSPC after child commit before parent checkpoint")
        return original_save(
            owner,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )

    def changed(status: WorkflowBatchStatus) -> None:
        nonlocal pause_requested
        if interruption == "pause":
            if status.child and status.child.pid is not None and not pause_requested:
                pause_requested = True
                assert first.pause()
            if status.state == "paused":
                first.close()

    def first_completed(_status: WorkflowBatchStatus) -> None:
        first.close()

    first.changed.connect(changed)
    first.completed.connect(first_completed)
    first.finished.connect(first_ended.append)
    with monkeypatch.context() as patch:
        if interruption == "parent_write":
            patch.setattr(Workspace, "save_draft", save)
        try:
            first.start(str(workspace), batch)
            qtbot.waitUntil(lambda: bool(first_ended), timeout=45000)
            if interruption == "pause":
                assert first_ended[0].state == "paused" and not first_ended[0].message
            else:
                assert injected and "ENOSPC" in first_ended[0].message
                assert first_ended[0].state != "completed"
        finally:
            first.close()
            qtbot.waitUntil(lambda: bool(first_ended), timeout=30000)
    with Workspace.open(workspace) as store:
        original_runs = store.list_runs()
        assert len(original_runs) == (1 if interruption == "pause" else 3)
        assert all(run.state == "succeeded" and run.pid for run in original_runs)
    second = WorkflowBatchSession(wb_workflow_registry)
    second_ended: list[WorkflowBatchStatus] = []
    resumed = False

    def reopened(status: WorkflowBatchStatus) -> None:
        nonlocal resumed
        if status.phase == "awaiting_resume" and not resumed:
            resumed = second.resume()

    def second_completed(_status: WorkflowBatchStatus) -> None:
        second.close()

    second.changed.connect(reopened)
    second.completed.connect(second_completed)
    second.finished.connect(second_ended.append)
    try:
        second.reopen(str(workspace), batch.batch_id)
        qtbot.waitUntil(lambda: bool(second_ended), timeout=45000)
        assert second_ended[0].state == "completed" and not second_ended[0].message
        assert second.batch is not None and all(i.state == "succeeded" for i in second.batch.items)
    finally:
        second.close()
        qtbot.waitUntil(lambda: bool(second_ended), timeout=30000)
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 6
        assert tuple(store.get_run(run.run_id) for run in original_runs) == original_runs


def test_batch_controls_keep_idempotence_and_reserve_cancel_budget(
    batch_fixture: tuple[Path, WorkflowBatch, tuple[AssetRef, ...]],
) -> None:
    workspace, batch, _sources = batch_fixture
    with Workspace.open(workspace) as store:
        current = execute_batch_store(
            store, WorkflowBatchStoreCommand("create", batch.batch_id, batch=batch)
        )
        for index in range(127):
            current = execute_batch_store(
                store,
                WorkflowBatchStoreCommand(
                    "control",
                    batch.batch_id,
                    expected_revision=current.revision,
                    action="pause" if index % 2 == 0 else "resume",
                    command_id=f"control_{index}",
                ),
            )
        repeated = execute_batch_store(
            store,
            WorkflowBatchStoreCommand(
                "control",
                batch.batch_id,
                expected_revision=0,
                action="pause",
                command_id="control_126",
            ),
        )
        assert repeated == current and len(current.controls) == 127
        with pytest.raises(StateConflict):
            execute_batch_store(
                store,
                WorkflowBatchStoreCommand(
                    "control",
                    batch.batch_id,
                    expected_revision=current.revision,
                    action="resume",
                    command_id="control_126",
                ),
            )
        with pytest.raises(StateConflict):
            execute_batch_store(
                store,
                WorkflowBatchStoreCommand(
                    "control",
                    batch.batch_id,
                    expected_revision=current.revision,
                    action="resume",
                    command_id="one_too_many",
                ),
            )
        cancelled = execute_batch_store(
            store,
            WorkflowBatchStoreCommand(
                "control",
                batch.batch_id,
                expected_revision=current.revision,
                action="cancel",
                command_id="reserved_cancel",
            ),
        )
        assert cancelled.state == "cancelled" and len(cancelled.controls) == 128
        assert all(item.state == "cancelled" for item in cancelled.items)
        assert not store.list_runs()


def test_parent_process_crash_after_claim_creates_child_once_on_resume(
    qtbot: QtBot,
    batch_fixture: tuple[Path, WorkflowBatch, tuple[AssetRef, ...]],
) -> None:
    workspace, batch, _sources = batch_fixture
    script = """
import os,sys
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
from PySide6.QtCore import QCoreApplication
from bioimage_app.workflow_batch_session import WorkflowBatchSession
from bioimage_app.wb_workflow_host import wb_workflow_registry
from tool_contracts.api import WorkflowBatch
batch=WorkflowBatch.model_validate_json(sys.stdin.buffer.read(1048577),strict=True)
class CrashAtClaim(WorkflowBatchSession):
    def _reply(self,reply):
        if isinstance(reply.value,WorkflowBatch) and reply.value.dispatches==1:
            os._exit(37)
        super()._reply(reply)
app=QCoreApplication([])
session=CrashAtClaim(wb_workflow_registry)
session.start(sys.argv[1],batch)
app.exec()
"""
    crashed = subprocess.run(
        [sys.executable, "-I", "-c", script, str(workspace)],
        input=batch.model_dump_json().encode(),
        capture_output=True,
        timeout=30,
    )
    assert crashed.returncode == 37, crashed.stderr
    with Workspace.open(workspace) as store:
        claimed = execute_batch_store(store, WorkflowBatchStoreCommand("load", batch.batch_id))
        assert claimed.items[0].state == "running" and claimed.dispatches == 1
        assert not store.list_runs()
        assert batch.items[0].execution_id not in {d.document_id for d in store.list_documents()}
    session = WorkflowBatchSession(wb_workflow_registry)
    ended: list[WorkflowBatchStatus] = []
    resumed = False

    def changed(status: WorkflowBatchStatus) -> None:
        nonlocal resumed
        if status.phase == "awaiting_resume" and not resumed:
            resumed = session.resume()

    def completed(_status: WorkflowBatchStatus) -> None:
        session.close()

    session.changed.connect(changed)
    session.completed.connect(completed)
    session.finished.connect(ended.append)
    try:
        session.reopen(str(workspace), batch.batch_id)
        qtbot.waitUntil(lambda: bool(ended), timeout=45000)
        assert ended[0].state == "completed" and not ended[0].message
        assert session.batch is not None
        assert tuple(i.execution_id for i in session.batch.items) == tuple(
            i.execution_id for i in batch.items
        )
    finally:
        session.close()
        qtbot.waitUntil(lambda: bool(ended), timeout=30000)
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 6


def test_batch_cancel_signals_current_commit_before_parent_storage_ack(
    qtbot: QtBot,
    batch_fixture: tuple[Path, WorkflowBatch, tuple[AssetRef, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, batch, _sources = batch_fixture
    entered, release = Event(), Event()
    original_commit = Workspace.commit_result

    def commit(
        owner: Workspace,
        run_id: str,
        receipt: ProcessExitReceipt,
        data: bytes,
        *,
        cancelled: Callable[[], bool] | None = None,
    ) -> RunRecord:
        if not entered.is_set():
            entered.set()
            if not release.wait(10):
                raise TimeoutError("owned commit barrier was not released")
        return original_commit(owner, run_id, receipt, data, cancelled=cancelled)

    monkeypatch.setattr(Workspace, "commit_result", commit)
    session = WorkflowBatchSession(wb_workflow_registry)
    ended: list[WorkflowBatchStatus] = []

    def completed(_status: WorkflowBatchStatus) -> None:
        session.close()

    session.completed.connect(completed)
    session.finished.connect(ended.append)
    try:
        session.start(str(workspace), batch)
        qtbot.waitUntil(entered.is_set, timeout=15000)
        assert session.cancel()
        release.set()
        qtbot.waitUntil(lambda: bool(ended), timeout=15000)
        assert ended[0].state == "cancelled" and not ended[0].message
        with Workspace.open(workspace) as store:
            runs = store.list_runs()
            assert len(runs) == 1 and runs[0].state == "cancelled"
            assert runs[0].result is None and runs[0].pid is not None
    finally:
        release.set()
        session.close()
        qtbot.waitUntil(lambda: bool(ended), timeout=30000)
