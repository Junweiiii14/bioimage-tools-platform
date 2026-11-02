"""Production controller automatically dispatches real nodes and persists the final journal."""

import csv
import io
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from bioimage_app.api import ProcessEvent
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.wb_workflow_host import build_wb_workflow, wb_workflow_registry
from bioimage_app.workflow_preparation import HostInputFile, WorkflowHostModule, WorkflowLaunch
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus
from platform_runtime.api import Workspace, load_workflow_ledger
from PySide6.QtCore import QThread
from pytestqt.qtbot import QtBot
from tool_contracts.api import (
    AssetRef,
    CoordinateFrame,
    DraftSnapshot,
    ExecutionPlan,
    ExecutionRequest,
    ImageMetadata,
    RunRecord,
    ScientificAsset,
    ScientificType,
    WorkflowLedger,
)
from wb_tool.api import wb_validation_input


@pytest.fixture
def workflow_fixture(tmp_path: Path) -> tuple[Path, ExecutionPlan, AssetRef, bytes]:
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
    return workspace, plan, source, fixture.source_bytes


@pytest.mark.parametrize("mode", ["complete", "pause"])
def test_workflow_controller_runs_actual_three_nodes(
    qtbot: QtBot, workflow_fixture: tuple[Path, ExecutionPlan, AssetRef, bytes], mode: str
) -> None:
    workspace, plan, source, original_bytes = workflow_fixture
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
        assert (
            store.read_asset(source)
            == (workspace.parent / "original.tif").read_bytes()
            == original_bytes
        )


@pytest.mark.parametrize("stage", ["close_early", "prepared", "gate", "running", "committed"])
def test_workflow_controller_cancel_boundaries(
    qtbot: QtBot,
    workflow_fixture: tuple[Path, ExecutionPlan, AssetRef, bytes],
    stage: str,
) -> None:
    workspace, plan, _, _ = workflow_fixture
    ended: list[WorkflowStatus] = []
    acted = False

    class CancelAtBoundary(WorkflowSession):
        def _started(self, attempt_id: str, run_id: str, record: RunRecord) -> None:
            nonlocal acted
            if stage == "gate" and not acted:
                acted = True
                assert self.cancel()
            super()._started(attempt_id, run_id, record)

        def _event(self, attempt_id: str, run_id: str, event: ProcessEvent) -> None:
            nonlocal acted
            super()._event(attempt_id, run_id, event)
            if stage == "running" and event.kind == "accepted" and not acted:
                acted = True
                assert self.cancel()

    session = CancelAtBoundary(wb_workflow_registry)

    def changed(status: WorkflowStatus) -> None:
        nonlocal acted
        if acted:
            return
        if (stage == "prepared" and status.run_id and status.pid is None) or (
            stage == "committed" and status.state == "succeeded"
        ):
            acted = True
            assert session.cancel()

    def completed(_status: WorkflowStatus) -> None:
        session.close()

    session.changed.connect(changed)
    session.completed.connect(completed)
    session.finished.connect(ended.append)
    try:
        session.start(str(workspace), plan)
        if stage == "close_early":
            session.close()
        qtbot.waitUntil(lambda: bool(ended), timeout=30000)
        assert ended[0].state == ("succeeded" if stage == "committed" else "cancelled"), ended
        assert ended[0].message == "" and session.ledger is not None
        ledger = session.ledger
        assert len(ledger.results) == (3 if stage == "committed" else 0)
        assert len(ledger.attempts) == (
            0 if stage == "close_early" else 3 if stage == "committed" else 1
        )
    finally:
        if not ended:
            session.close()
            qtbot.waitUntil(lambda: bool(ended), timeout=30000)
    with Workspace.open(workspace) as store:
        assert (
            load_workflow_ledger(
                store.read_asset(store.load_draft(ledger.execution_id).asset).decode()
            )
            == ledger
        )
        runs = store.list_runs()
        assert len(runs) == len(ledger.attempts)
        if stage == "prepared":
            assert runs[0].pid is None
        elif stage in ("gate", "running"):
            assert runs[0].pid is not None and runs[0].result is None


def test_workflow_controller_reopens_paused_execution(
    qtbot: QtBot,
    workflow_fixture: tuple[Path, ExecutionPlan, AssetRef, bytes],
) -> None:
    workspace, plan, _, _ = workflow_fixture
    first = WorkflowSession(wb_workflow_registry)
    ended: list[WorkflowStatus] = []
    asked = False

    def changed(status: WorkflowStatus) -> None:
        nonlocal asked
        if status.pid is not None and not asked:
            asked = True
            assert first.pause()
        elif status.state == "paused":
            first.close()

    first.changed.connect(changed)
    first.finished.connect(ended.append)
    first.start(str(workspace), plan)
    try:
        qtbot.waitUntil(lambda: bool(ended), timeout=30000)
        assert first.ledger is not None and first.ledger.state == "paused"
        original_run = first.ledger.results[0].run
        second = WorkflowSession(wb_workflow_registry)
        resumed = False
        completed: list[WorkflowStatus] = []

        def reopen_changed(status: WorkflowStatus) -> None:
            nonlocal resumed
            if status.state == "paused" and not resumed:
                resumed = second.resume()

        def finished(_status: WorkflowStatus) -> None:
            second.close()

        second.changed.connect(reopen_changed)
        second.completed.connect(finished)
        second.finished.connect(completed.append)
        second.reopen(str(workspace), first.ledger.execution_id)
        try:
            qtbot.waitUntil(lambda: bool(completed), timeout=30000)
            assert completed[0].state == "succeeded" and completed[0].message == "", completed
            assert second.ledger is not None and second.ledger.results[0].run == original_run
            assert len(second.ledger.attempts) == 3
        finally:
            if not completed:
                second.close()
                qtbot.waitUntil(lambda: bool(completed), timeout=30000)
    finally:
        if not ended:
            first.close()
            qtbot.waitUntil(lambda: bool(ended), timeout=30000)


@pytest.mark.parametrize(
    "fault", ["nonzero_after_manifest", "crash", "duplicate", "wrong_identity"]
)
def test_workflow_fault_retry_preserves_real_attempts(
    qtbot: QtBot,
    workflow_fixture: tuple[Path, ExecutionPlan, AssetRef, bytes],
    fault: str,
) -> None:
    workspace, plan, _, _ = workflow_fixture
    injected = False

    def registry(frozen: ExecutionPlan) -> tuple[WorkflowHostModule, ...]:
        modules = wb_workflow_registry(frozen)
        ordinary = modules[0].launch

        def launch(
            req: ExecutionRequest, run: RunRecord, files: tuple[HostInputFile, ...], directory: str
        ) -> WorkflowLaunch:
            nonlocal injected
            actual = ordinary(req, run, files, directory)
            if injected:
                return actual
            injected = True
            if fault == "nonzero_after_manifest":
                script = (
                    "import sys;from wb_tool.api import run_wb_workflow_worker;"
                    "run_wb_workflow_worker();sys.exit(7)"
                )
            else:
                script = (
                    "import os,sys;from tool_contracts.api import ExecutionEvent;"
                    "from wb_tool.api import WBWorkflowStart,encode_wb_workflow_frame;"
                    "out=sys.stdout.buffer;out.write(encode_wb_workflow_frame(ExecutionEvent(kind='hello',sequence=0)));out.flush();"
                    "start=WBWorkflowStart.model_validate_json(sys.stdin.buffer.readline());"
                    "identity=start.identity;"
                )
                if fault == "wrong_identity":
                    script += "identity=identity.model_copy(update={'run_id':'another_run'});"
                script += (
                    "accepted=ExecutionEvent(kind='accepted',sequence=1,identity=identity);"
                    "out.write(encode_wb_workflow_frame(accepted));out.flush();"
                )
                script += (
                    "out.write(encode_wb_workflow_frame(accepted));out.flush();"
                    if fault == "duplicate"
                    else ""
                )
                script += "os._exit(9)"
            return replace(actual, command=(sys.executable, "-I", "-c", script))

        return tuple(replace(module, launch=launch) for module in modules)

    session = WorkflowSession(registry)
    ended: list[WorkflowStatus] = []
    failed_attempts: list[str] = []
    expected_failure = "failed" if fault == "nonzero_after_manifest" else "interrupted"

    def completed(status: WorkflowStatus) -> None:
        if not failed_attempts:
            assert status.state == expected_failure and session.ledger is not None, status
            assert not session.ledger.results
            failed_attempts.append(session.ledger.attempts[0].attempt_id)
            assert session.resume()
        else:
            session.close()

    session.completed.connect(completed)
    session.finished.connect(ended.append)
    try:
        session.start(str(workspace), plan)
        qtbot.waitUntil(lambda: bool(ended), timeout=30000)
        assert ended[0].state == "succeeded" and ended[0].message == "", ended
        assert session.ledger is not None and len(session.ledger.attempts) == 4
        assert len({attempt.attempt_id for attempt in session.ledger.attempts}) == 4
        assert session.ledger.attempts[0].attempt_id == failed_attempts[0]
        failed = session.ledger.attempts[0].run
        assert failed is not None and failed.state == expected_failure and failed.result is None
    finally:
        if not ended:
            session.close()
            qtbot.waitUntil(lambda: bool(ended), timeout=30000)
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 4 and store.get_run(failed.run_id) == failed


@pytest.mark.parametrize("checkpoint", ["before_intent", "after_commit"])
def test_workflow_storage_failure_and_reopen_reconcile_actual_run(
    qtbot: QtBot,
    workflow_fixture: tuple[Path, ExecutionPlan, AssetRef, bytes],
    monkeypatch: pytest.MonkeyPatch,
    checkpoint: str,
) -> None:
    workspace, plan, _, _ = workflow_fixture
    original_save = Workspace.save_draft
    injected = False

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
        if tool_id == "workflow_journal_v1" and not injected:
            value = load_workflow_ledger(data.decode())
            at_intent = bool(value.attempts) and value.attempts[0].run is None
            at_commit = len(value.results) == 1
            if (
                checkpoint == "before_intent"
                and at_intent
                or checkpoint == "after_commit"
                and at_commit
            ):
                injected = True
                raise OSError(28, "injected ENOSPC at workflow journal write")
        return original_save(
            owner,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )

    monkeypatch.setattr(Workspace, "save_draft", save)
    first = WorkflowSession(wb_workflow_registry)
    ended: list[WorkflowStatus] = []

    def completed(_status: WorkflowStatus) -> None:
        first.close()

    first.completed.connect(completed)
    first.finished.connect(ended.append)
    first.start(str(workspace), plan)
    try:
        qtbot.waitUntil(lambda: bool(ended), timeout=30000)
        assert injected and first.ledger is not None
        assert ended[0].state != "succeeded" and "ENOSPC" in ended[0].message
        execution_id = first.ledger.execution_id
        with Workspace.open(workspace) as store:
            existing = store.list_runs()
            assert len(existing) == (1 if checkpoint == "after_commit" else 0)
            if existing:
                assert existing[0].state == "succeeded" and existing[0].result is not None
        second = WorkflowSession(wb_workflow_registry)
        finished: list[WorkflowStatus] = []
        resumed = False

        def changed(status: WorkflowStatus) -> None:
            nonlocal resumed
            ledger = second.ledger
            if (
                not resumed
                and ledger is not None
                and ledger.active_attempt is None
                and status.state == "running"
            ):
                resumed = second.resume()

        def done(_status: WorkflowStatus) -> None:
            second.close()

        second.changed.connect(changed)
        second.completed.connect(done)
        second.finished.connect(finished.append)
        second.reopen(str(workspace), execution_id)
        try:
            qtbot.waitUntil(lambda: bool(finished), timeout=30000)
            assert finished[0].state == "succeeded" and finished[0].message == "", finished
            assert second.ledger is not None and len(second.ledger.attempts) == 3
            if existing:
                assert second.ledger.results[0].run == existing[0]
                assert sum(event.kind == "recovered" for event in second.ledger.events) == 1
        finally:
            if not finished:
                second.close()
                qtbot.waitUntil(lambda: bool(finished), timeout=30000)
    finally:
        if not ended:
            first.close()
            qtbot.waitUntil(lambda: bool(ended), timeout=30000)
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 3


@pytest.mark.parametrize(
    "change", ["revision", "layout", "analysis", "corrupt_output", "corrupt_source"]
)
def test_workflow_cache_uses_real_results_and_invalidates_only_dependencies(
    qtbot: QtBot,
    workflow_fixture: tuple[Path, ExecutionPlan, AssetRef, bytes],
    change: str,
) -> None:
    workspace, original_plan, source, _ = workflow_fixture

    def execute(plan: ExecutionPlan, cache: str = "") -> tuple[WorkflowLedger, WorkflowStatus]:
        session = WorkflowSession(wb_workflow_registry)
        ended: list[WorkflowStatus] = []

        def completed(_status: WorkflowStatus) -> None:
            session.close()

        session.completed.connect(completed)
        session.finished.connect(ended.append)
        try:
            session.start(str(workspace), plan, cache_execution_id=cache)
            qtbot.waitUntil(lambda: bool(ended), timeout=30000)
            assert session.ledger is not None
            return session.ledger, ended[0]
        finally:
            if not ended:
                session.close()
                qtbot.waitUntil(lambda: bool(ended), timeout=30000)

    first, status = execute(original_plan)
    assert status.state == "succeeded" and not status.message
    scientific = original_plan.nodes[0].inputs[0].asset
    assert scientific is not None
    planned = wb_validation_input("triangle_u16").request
    if change == "analysis":
        planned = replace(planned, polarity="dark")
    _, second_plan = build_wb_workflow(
        scientific, planned, revision=8, layout="compact" if change == "layout" else "comfortable"
    )
    original_table = next(
        item.asset for item in first.results[-1].outputs if item.port == "measurements"
    )
    with Workspace.open(workspace) as store:
        old_table_bytes = store.read_asset(original_table)
        if change in ("corrupt_output", "corrupt_source"):
            ref = first.results[1].outputs[0].asset if change == "corrupt_output" else source
            store.asset_path(ref).write_bytes(b"owned test corruption")
    second, outcome = execute(second_plan, first.execution_id)
    if change.startswith("corrupt"):
        assert "IntegrityError" in outcome.message and outcome.state != "succeeded"
        assert not second.attempts
        assert len(second.results) == (1 if change == "corrupt_output" else 0)
        expected_runs = 3
    else:
        expected_reused = {"revision": 3, "layout": 2, "analysis": 1}[change]
        assert outcome.state == "succeeded" and not outcome.message
        assert outcome.reused_nodes == expected_reused
        assert [item.reused for item in second.results] == [
            index < expected_reused for index in range(3)
        ]
        assert len(second.attempts) == 3 - expected_reused
        for index in range(expected_reused):
            assert second.results[index].run == first.results[index].run
            assert second.results[index].source_execution_id == first.execution_id
        expected_runs = 6 - expected_reused
        with Workspace.open(workspace) as store:
            table = next(
                item.asset for item in second.results[-1].outputs if item.port == "measurements"
            )
            rows = list(csv.DictReader(io.StringIO(store.read_asset(table).decode("utf-8-sig"))))
            assert rows[0]["value"] == ("0.0" if change == "analysis" else "4000.0")
            assert rows[0]["status"] == "text:valid"
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == expected_runs
        assert store.read_asset(original_table) == old_table_bytes
        assert tuple(store.get_run(item.run.run_id) for item in first.results) == tuple(
            item.run for item in first.results
        )


def test_sequential_workflows_share_one_parent_storage_owner(
    qtbot: QtBot, workflow_fixture: tuple[Path, ExecutionPlan, AssetRef, bytes]
) -> None:
    workspace, plan, _source, _original = workflow_fixture
    storage = AsyncStorage()
    replies: list[StorageReply] = []
    closed: list[bool] = []
    storage.replied.connect(replies.append)
    storage.closed.connect(lambda: closed.append(True))
    sessions: list[tuple[WorkflowSession, list[WorkflowStatus]]] = []
    try:
        opened = storage.submit(StorageCommand("open", path=str(workspace)))
        qtbot.waitUntil(lambda: any(r.request_id == opened for r in replies))
        assert next(r for r in replies if r.request_id == opened).error_code is None
        for index in range(2):
            session = WorkflowSession(wb_workflow_registry, storage=storage)
            ended: list[WorkflowStatus] = []
            sessions.append((session, ended))

            def completed(_status: WorkflowStatus, owned: WorkflowSession = session) -> None:
                owned.close()

            session.completed.connect(completed)
            session.finished.connect(ended.append)
            session.start(str(workspace), plan, execution_id=f"shared_child_{index}")
            qtbot.waitUntil(lambda current=ended: bool(current), timeout=30000)
            assert ended[0].state == "succeeded" and not ended[0].message
            assert not closed
            records_request = storage.submit(StorageCommand("runs"))
            qtbot.waitUntil(
                lambda request_id=records_request: any(r.request_id == request_id for r in replies)
            )
            reply = next(r for r in replies if r.request_id == records_request)
            assert reply.error_code is None and isinstance(reply.value, tuple)
            assert len(reply.value) == (index + 1) * 3
            assert all(
                isinstance(run, RunRecord) and run.state == "succeeded" and run.pid
                for run in reply.value
            )
    finally:
        for session, outcomes in sessions:
            session.close()
            qtbot.waitUntil(lambda current=outcomes: bool(current), timeout=30000)
        storage.shutdown()
        qtbot.waitUntil(lambda: bool(closed), timeout=30000)
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 6
        for index in range(2):
            actual = load_workflow_ledger(
                store.read_asset(store.load_draft(f"shared_child_{index}").asset).decode()
            )
            assert actual.state == "succeeded" and len(actual.results) == 3
