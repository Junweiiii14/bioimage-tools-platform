"""Editor drafts/CAS and real batches use one workspace owner, never a demo engine."""

import csv
import io
import json
from pathlib import Path

import pytest
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.wb_workflow_host import wb_workflow_registry
from bioimage_app.workflow_authoring_models import (
    AuthoringCommand,
    AuthoringGraph,
    AuthoringProjection,
)
from bioimage_app.workflow_authoring_store import execute_authoring_store, load_authoring_project
from bioimage_app.workflow_batch_session import WorkflowBatchSession, WorkflowBatchStatus
from bioimage_app.workflow_template import load_workflow_template
from platform_runtime.api import StateConflict, Workspace, load_workflow_ledger
from pytestqt.qtbot import QtBot
from tool_contracts.api import NodePosition, WorkflowLayout


def payload(operation: str, document: str, **values: object) -> bytes:
    return (
        AuthoringCommand.model_validate({"operation": operation, "document_id": document, **values})
        .model_dump_json()
        .encode()
    )


def test_portable_template_preserves_layout_and_binds_new_source(tmp_path: Path) -> None:
    exported = tmp_path / "template.json"
    with Workspace.create(tmp_path / "first") as store:
        original = execute_authoring_store(
            store, payload("initialize", "editor", validation_cases=("triangle_u16",))
        )
        layout = WorkflowLayout(positions=(NodePosition(node_id="analyze", x=720.0, y=135.0),))
        execute_authoring_store(
            store,
            payload(
                "save", "editor", previous_revision=0, graph=original.project.graph, layout=layout
            ),
        )
        execute_authoring_store(store, payload("export", "editor", destination=str(exported)))
    with Workspace.create(tmp_path / "second") as store:
        rebound = execute_authoring_store(
            store,
            payload(
                "initialize",
                "editor",
                validation_cases=("triangle_u8",),
                template_path=str(exported),
            ),
        )
        assert not rebound.issues and rebound.plan is not None
        assert rebound.project.layout == layout
        assert rebound.project.sources[0].asset != original.project.sources[0].asset
        assert rebound.project.graph.edges == original.project.graph.edges
        # Existing definition-only P007/P008 templates remain accepted by the shared CLI loader.
        legacy = load_workflow_template(original.project.seed.model_dump_json())
        assert legacy.definition == original.project.seed
        assert len(legacy.layout.positions) == len(original.project.graph.nodes)


def test_incomplete_editor_draft_and_layout_survive_cas_reopen(tmp_path: Path) -> None:
    workspace = tmp_path / "editor"
    with Workspace.create(workspace) as store:
        original = execute_authoring_store(
            store, payload("initialize", "editor", validation_cases=("triangle_u16",))
        )
        assert original.plan is not None and not original.issues
        assert len(original.catalogue) == 3
        keys = tuple(n.computation_key for n in original.plan.nodes)
        layout = WorkflowLayout(positions=(NodePosition(node_id="analyze", x=100.0, y=80.0),))
        moved = execute_authoring_store(
            store,
            payload(
                "save", "editor", previous_revision=0, graph=original.project.graph, layout=layout
            ),
        )
        assert moved.plan is not None and moved.project.graph.revision == 0
        assert tuple(n.computation_key for n in moved.plan.nodes) == keys
        with pytest.raises(StateConflict):
            execute_authoring_store(
                store,
                payload(
                    "save",
                    "editor",
                    previous_revision=0,
                    graph=original.project.graph,
                    layout=layout,
                ),
            )
        incomplete = AuthoringGraph.model_validate(
            {
                **original.project.graph.model_dump(),
                "nodes": (),
                "edges": (),
                "inputs": (),
                "outputs": (),
            }
        )
        draft = execute_authoring_store(
            store, payload("freeze", "editor", previous_revision=1, graph=incomplete, layout=layout)
        )
        assert draft.plan is None and draft.batch is None
        assert draft.issues[0].code == "draft_incomplete"
        assert not any(d.tool_id == "workflow_batch_v1" for d in store.list_documents())
        assert not store.list_runs()
    with Workspace.open(workspace) as store:
        assert load_authoring_project(store, "editor") == draft.project
        assert draft.project.layout == layout
        # A unit error in an actual bound input is rejected by the same compiler.
        inputs = tuple(
            binding.model_copy(
                update={
                    "asset": binding.asset.model_copy(
                        update={
                            "description": binding.asset.description.model_copy(
                                update={"unit": "count"}
                            )
                        }
                    )
                }
            )
            for binding in original.project.graph.inputs
        )
        wrong_unit = original.project.graph.model_copy(update={"inputs": inputs})
        refused = execute_authoring_store(
            store, payload("freeze", "editor", previous_revision=2, graph=wrong_unit, layout=layout)
        )
        assert refused.plan is None and refused.batch is None
        assert any(issue.code == "unit" for issue in refused.issues)
        assert not store.list_runs()


def test_editor_runs_rebinds_and_reuses_style_on_same_storage(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "shared-editor"
    port = AsyncStorage()
    replies: list[StorageReply] = []
    closed: list[bool] = []
    port.replied.connect(replies.append)
    port.closed.connect(lambda: closed.append(True))
    sessions: list[tuple[WorkflowBatchSession, list[WorkflowBatchStatus]]] = []

    def call(command: StorageCommand) -> StorageReply:
        request = port.submit(command)
        qtbot.waitUntil(lambda: any(r.request_id == request for r in replies), timeout=20000)
        result = next(r for r in replies if r.request_id == request)
        assert result.error_code is None, result
        return result

    def authoring(operation: str, **values: object) -> AuthoringProjection:
        reply = call(
            StorageCommand("workflow_authoring", data=payload(operation, "editor", **values))
        )
        assert isinstance(reply.value, AuthoringProjection)
        return reply.value

    draft_saved = ""
    try:
        call(StorageCommand("create", path=str(workspace)))
        current = authoring("initialize", validation_cases=("triangle_u16",))
        original_ref = current.project.sources[0].asset
        assert original_ref is not None
        first_batch = ""
        for index in range(3):
            if index == 1:
                exported = tmp_path / "laboratory-template.json"
                authoring("export", destination=str(exported))
                assert json.loads(exported.read_text(encoding="utf-8"))["definition"]["nodes"]
                current = authoring(
                    "bind",
                    previous_revision=current.project.revision,
                    validation_cases=("triangle_u8",),
                )
            if index == 2:
                nodes = tuple(
                    node.model_copy(
                        update={
                            "parameters_json": json.dumps(
                                {**json.loads(node.parameters_json), "layout": "compact"}
                            )
                        }
                    )
                    if node.module.module_id == "wb-publish-original"
                    else node
                    for node in current.project.graph.nodes
                )
                current = current.model_copy(
                    update={
                        "project": current.project.model_copy(
                            update={
                                "graph": current.project.graph.model_copy(update={"nodes": nodes})
                            }
                        )
                    }
                )
            current = authoring(
                "freeze",
                previous_revision=current.project.revision,
                graph=current.project.graph,
                layout=current.project.layout,
            )
            assert current.batch is not None and not current.issues
            if index == 0:
                first_batch = current.batch.batch_id
            session = WorkflowBatchSession(wb_workflow_registry, storage=port)
            ended: list[WorkflowBatchStatus] = []
            sessions.append((session, ended))
            resumed = False

            def changed(
                status: WorkflowBatchStatus,
                owned: WorkflowBatchSession = session,
                frozen: AuthoringProjection = current,
                batch_index: int = index,
            ) -> None:
                nonlocal resumed, draft_saved
                if status.phase == "awaiting_resume" and not resumed:
                    resumed = owned.resume()
                if batch_index == 0 and status.child and status.child.pid and not draft_saved:
                    graph = frozen.project.graph.model_copy(update={"title": "运行中的新草稿"})
                    draft_saved = port.submit(
                        StorageCommand(
                            "workflow_authoring",
                            data=payload(
                                "save",
                                "editor",
                                previous_revision=frozen.project.revision,
                                graph=graph,
                                layout=frozen.project.layout,
                            ),
                        )
                    )

            def completed(
                _status: WorkflowBatchStatus, owned: WorkflowBatchSession = session
            ) -> None:
                owned.close()

            session.changed.connect(changed)
            session.completed.connect(completed)
            session.finished.connect(ended.append)
            session.reopen(str(workspace), current.batch.batch_id)
            qtbot.waitUntil(lambda current=ended: bool(current), timeout=45000)
            assert ended[0].state == "completed" and not ended[0].message
            assert not closed
            if index == 0:
                qtbot.waitUntil(lambda: any(r.request_id == draft_saved for r in replies))
                assert next(r for r in replies if r.request_id == draft_saved).error_code is None
            current = authoring("load")
            assert current.project.graph.title == "运行中的新草稿"
            assert current.project.last_batch_id
            outputs = authoring("results")
            table = next(o for o in outputs.outputs if o.port == "measurements")
            rows = list(csv.DictReader(io.StringIO(table.text)))
            assert rows[0]["value"] == ("4000.0" if index == 0 else "40.0")
            assert table.batch_id == current.project.last_batch_id
            opened = authoring(
                "open",
                batch_id=table.batch_id,
                sample_id=table.sample_id,
                node_id=table.node_id,
                port=table.port,
            )
            assert Path(opened.opened_path).is_file()
        records = call(StorageCommand("runs"))
        assert isinstance(records.value, tuple) and len(records.value) == 7
    finally:
        for session, ended in sessions:
            session.close()
            qtbot.waitUntil(lambda outcomes=ended: bool(outcomes), timeout=30000)
        port.shutdown()
        qtbot.waitUntil(lambda: bool(closed), timeout=30000)
    with Workspace.open(workspace) as store:
        assert store.asset_path(original_ref.payload).is_file()
        project = load_authoring_project(store, "editor")
        assert project.last_batch_id != first_batch
        batch = sessions[-1][0].batch
        assert batch is not None
        child = load_workflow_ledger(
            store.read_asset(store.load_draft(batch.items[0].execution_id).asset).decode()
        )
        assert [r.reused for r in child.results] == [True, True, False]
        assert len(store.list_runs()) == 7
