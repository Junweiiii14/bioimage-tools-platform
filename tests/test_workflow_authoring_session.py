"""Actual asynchronous editor lifecycle, frozen execution and pending-close boundary."""

import json
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest
from bioimage_app.wb_workflow_host import wb_workflow_registry
from bioimage_app.workflow_authoring_models import AuthoringProject
from bioimage_app.workflow_authoring_session import WorkflowAuthoringSession
from bioimage_app.workflow_authoring_store import load_authoring_project
from bioimage_app.workflow_batch_session import WorkflowBatchStatus
from bioimage_app.workflow_batch_storage import WorkflowBatchStoreCommand, execute_batch_store
from bioimage_app.workflow_preparation import HostInputFile, WorkflowHostModule, WorkflowLaunch
from platform_runtime.api import Workspace
from pytestqt.qtbot import QtBot
from tool_contracts.api import DraftSnapshot, ExecutionPlan, ExecutionRequest, RunRecord

from tests.test_workflow_authoring_store import payload


def test_async_editor_old_run_preserves_new_draft_and_encodes_on_storage(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "editor-session"
    session = WorkflowAuthoringSession(wb_workflow_registry)
    documents: list[tuple[str, str, str, str]] = []
    finished: list[bool] = []
    edited = False

    def received(token: str, operation: str, data: str, error: str) -> None:
        documents.append((token, operation, data, error))

    session.documentChanged.connect(received)
    session.finished.connect(lambda: finished.append(True))

    def progress(status: WorkflowBatchStatus) -> None:
        nonlocal edited
        if status.child and status.child.pid and not edited:
            edited = True
            assert session.projection is not None
            project = session.projection.project
            session.request(
                "new-draft",
                payload(
                    "save",
                    "editor",
                    previous_revision=project.revision,
                    graph=project.graph.model_copy(update={"title": "旧任务不覆盖的新草稿"}),
                    layout=project.layout,
                ),
            )

    session.progressChanged.connect(progress)
    try:
        session.create(
            str(workspace), payload("initialize", "editor", validation_cases=("triangle_u16",))
        )
        qtbot.waitUntil(lambda: session.projection is not None, timeout=15000)
        assert session.projection is not None
        initial = session.projection.project
        session.request(
            "run",
            payload(
                "freeze",
                "editor",
                previous_revision=initial.revision,
                graph=initial.graph,
                layout=initial.layout,
            ),
        )
        qtbot.waitUntil(
            lambda: session.batch_status is not None and not session.running, timeout=45000
        )
        assert session.batch_status is not None and session.batch_status.state == "completed"
        assert edited and session.projection.project.graph.title == "旧任务不覆盖的新草稿"
        session.request("outputs", payload("results", "editor"))
        qtbot.waitUntil(lambda: any(d[0] == "outputs" for d in documents))
        reply = next(d for d in documents if d[0] == "outputs")
        assert not reply[3], documents
        wire = json.loads(reply[2])
        assert wire["operation"] == "results" and "plan" not in wire and "batch" not in wire
        assert "seed" not in wire["project"]
        assert any("4000.0" in output["text"] for output in wire["outputs"])
        assert not finished
    finally:
        session.close()
        qtbot.waitUntil(lambda: bool(finished), timeout=30000)
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 3
        assert load_authoring_project(store, "editor").graph.title == "旧任务不覆盖的新草稿"


@pytest.mark.parametrize("action", ["close", "cancel"])
def test_close_before_freeze_receipt_does_not_dispatch_a_worker(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    entered, release = Event(), Event()
    original = Workspace.save_draft

    def save(
        owner: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None,
    ) -> DraftSnapshot:
        if tool_id == "workflow_authoring_v1":
            project = AuthoringProject.model_validate_json(data, strict=True)
            if project.last_batch_id and not entered.is_set():
                entered.set()
                if not release.wait(10):
                    raise TimeoutError("Owned editor freeze barrier was not released")
        return original(
            owner,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )

    monkeypatch.setattr(Workspace, "save_draft", save)
    workspace = tmp_path / "close-freeze"
    session = WorkflowAuthoringSession(wb_workflow_registry)
    closed: list[bool] = []
    session.finished.connect(lambda: closed.append(True))
    try:
        session.create(
            str(workspace), payload("initialize", "editor", validation_cases=("triangle_u8",))
        )
        qtbot.waitUntil(lambda: session.projection is not None, timeout=15000)
        assert session.projection is not None
        project = session.projection.project
        session.request(
            "run",
            payload(
                "freeze", "editor", previous_revision=0, graph=project.graph, layout=project.layout
            ),
        )
        qtbot.waitUntil(entered.is_set, timeout=15000)
        if action == "close":
            session.close()
        else:
            assert session.cancel()
        release.set()
        if action == "cancel":
            qtbot.waitUntil(
                lambda: session.batch_status is not None and not session.running, timeout=15000
            )
            assert not closed
            session.close()
        qtbot.waitUntil(lambda: bool(closed), timeout=15000)
        assert session.resources_closed
    finally:
        release.set()
        session.close()
        qtbot.waitUntil(lambda: bool(closed), timeout=30000)
    with Workspace.open(workspace) as store:
        project = load_authoring_project(store, "editor")
        batch = execute_batch_store(store, WorkflowBatchStoreCommand("load", project.last_batch_id))
        assert batch.state == "cancelled" and not store.list_runs()


def test_running_batch_exposes_only_actual_committed_intermediate_outputs(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    entered, release = Event(), Event()

    def registry(plan: ExecutionPlan) -> tuple[WorkflowHostModule, ...]:
        modules = wb_workflow_registry(plan)
        analysis = next(
            m for m in modules if m.registration.interface.module.module_id == "wb-analyze-original"
        )

        def launch(
            request: ExecutionRequest, run: RunRecord, files: tuple[HostInputFile, ...], output: str
        ) -> WorkflowLaunch:
            entered.set()
            if not release.wait(10):
                raise TimeoutError("Owned analysis launch barrier was not released")
            return analysis.launch(request, run, files, output)

        return tuple(
            replace(m, launch=launch)
            if m.registration.interface.module.module_id == "wb-analyze-original"
            else m
            for m in modules
        )

    session = WorkflowAuthoringSession(registry)
    documents: list[tuple[str, str, str, str]] = []
    closed: list[bool] = []

    def received(token: str, operation: str, data: str, error: str) -> None:
        documents.append((token, operation, data, error))

    session.documentChanged.connect(received)
    session.finished.connect(lambda: closed.append(True))
    try:
        session.create(
            str(tmp_path / "intermediate"),
            payload("initialize", "editor", validation_cases=("triangle_u16",)),
        )
        qtbot.waitUntil(lambda: session.projection is not None, timeout=15000)
        assert session.projection is not None
        project = session.projection.project
        session.request(
            "run",
            payload(
                "freeze", "editor", previous_revision=0, graph=project.graph, layout=project.layout
            ),
        )
        qtbot.waitUntil(entered.is_set, timeout=15000)
        session.request("intermediate", payload("results", "editor", node_id="verify"))
        qtbot.waitUntil(lambda: any(d[0] == "intermediate" for d in documents))
        receipt = next(d for d in documents if d[0] == "intermediate")
        assert not receipt[3], documents
        actual = json.loads(receipt[2])
        assert actual["samples"][0]["state"] == "running"
        assert actual["matches_run"] is True
        assert len(actual["execution_nodes"]) == 3
        assert [o["port"] for o in actual["outputs"]] == ["validation"]
        assert actual["outputs"][0]["asset"]["sha256"]
        release.set()
        qtbot.waitUntil(
            lambda: session.batch_status is not None and not session.running, timeout=30000
        )
        assert session.batch_status is not None and session.batch_status.state == "completed"
    finally:
        release.set()
        session.close()
        qtbot.waitUntil(lambda: bool(closed), timeout=30000)


def test_editor_reopens_paused_batch_and_resumes_same_real_child(
    qtbot: QtBot, tmp_path: Path
) -> None:
    workspace = tmp_path / "paused-editor"
    first = WorkflowAuthoringSession(wb_workflow_registry)
    first_closed: list[bool] = []
    first.finished.connect(lambda: first_closed.append(True))
    requested = False

    def progress(status: WorkflowBatchStatus) -> None:
        nonlocal requested
        if status.child and status.child.pid and not requested:
            requested = first.pause()

    first.progressChanged.connect(progress)
    try:
        first.create(
            str(workspace), payload("initialize", "editor", validation_cases=("triangle_u16",))
        )
        qtbot.waitUntil(lambda: first.projection is not None, timeout=15000)
        assert first.projection is not None
        project = first.projection.project
        first.request(
            "run",
            payload(
                "freeze", "editor", previous_revision=0, graph=project.graph, layout=project.layout
            ),
        )
        qtbot.waitUntil(
            lambda: first.batch_status is not None and first.batch_status.state == "paused",
            timeout=20000,
        )
    finally:
        first.close()
        qtbot.waitUntil(lambda: bool(first_closed), timeout=30000)
    with Workspace.open(workspace) as store:
        project = load_authoring_project(store, "editor")
        batch = execute_batch_store(store, WorkflowBatchStoreCommand("load", project.last_batch_id))
        execution_id = batch.items[0].execution_id
        assert batch.state == "paused" and len(store.list_runs()) == 1
    second = WorkflowAuthoringSession(wb_workflow_registry)
    second_closed: list[bool] = []
    second.finished.connect(lambda: second_closed.append(True))
    try:
        second.reopen(str(workspace))
        qtbot.waitUntil(
            lambda: (
                second.batch_status is not None and second.batch_status.phase == "awaiting_resume"
            ),
            timeout=15000,
        )
        assert second.running and second.batch_status is not None
        assert second.batch_status.state == "paused" and second.batch_status.child is None
        assert second.resume()
        qtbot.waitUntil(lambda: not second.running, timeout=30000)
        assert second.batch_status.state == "completed"
    finally:
        second.close()
        qtbot.waitUntil(lambda: bool(second_closed), timeout=30000)
    with Workspace.open(workspace) as store:
        batch = execute_batch_store(store, WorkflowBatchStoreCommand("load", project.last_batch_id))
        assert batch.items[0].execution_id == execution_id
        assert len(store.list_runs()) == 3
