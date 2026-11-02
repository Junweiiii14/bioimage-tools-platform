"""Native host entry retains the old workspace and drains both owners on exit."""

from pathlib import Path

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from bioimage_app.workflow_batch_session import WorkflowBatchStatus
from platform_runtime.api import Workspace
from pydantic import TypeAdapter
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from tests.test_workflow_authoring_store import payload
from tooling.qt_test_lifecycle import close_and_dispose_window


@pytest.mark.parametrize("stop", ["cancel", "pause"])
def test_native_workbench_exits_after_actual_workflow_cancel(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stop: str,
) -> None:
    window = WebWorkbenchWindow(
        settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat)
    )
    window.show()
    progress: list[str] = []
    window.authoring.progressChanged.connect(progress.append)

    def parent(*_args: object, **_kwargs: object) -> str:
        return str(tmp_path)

    monkeypatch.setattr(QFileDialog, "getExistingDirectory", parent)
    workspace = ""
    try:
        window.authoring.choose("new", "new_example", '{"validation":"triangle_u16"}')
        qtbot.waitUntil(lambda: window.authoring.projection is not None, timeout=15000)
        assert window.authoring.projection is not None
        project = window.authoring.projection.project
        assert window.host.workspace_path == ""
        window.authoring.command(
            "run",
            payload(
                "freeze",
                project.document_id,
                previous_revision=project.revision,
                graph=project.graph,
                layout=project.layout,
            ).decode("utf-8"),
        )
        adapter = TypeAdapter(WorkflowBatchStatus)
        qtbot.waitUntil(
            lambda: any(
                status.child is not None and status.child.pid is not None
                for status in map(adapter.validate_json, progress)
            ),
            timeout=20000,
        )
        # The normal application close path owns both legacy and editor services.
        if stop == "pause":
            window.authoring.control("pause")
            qtbot.waitUntil(
                lambda: any(adapter.validate_json(raw).state == "paused" for raw in progress),
                timeout=20000,
            )
            assert not window.authoring.busy
        window.close()
        if stop == "cancel":
            assert window.shutdown_stage == "confirm_busy"
            window.bridge.session("reply", '{"choice":"cancel"}')
        else:
            assert window.shutdown_stage == "shutdown"
        qtbot.waitUntil(
            lambda: window.authoring.resources_closed and window.host.resources_closed,
            timeout=30000,
        )
        assert not window.authoring.busy
        directories = tuple(tmp_path.glob("工作流-*"))
        assert len(directories) == 1
        workspace = str(directories[0])
    finally:
        close_and_dispose_window(
            window,
            qtbot,
            resources_closed=lambda: (
                window.host.resources_closed and window.authoring.resources_closed
            ),
            timeout=30000,
        )
    with Workspace.open(workspace) as store:
        runs = store.list_runs()
        assert runs and all(r.state in ("succeeded", "cancelled") and r.pid for r in runs)
        if stop == "cancel":
            assert any(r.state == "cancelled" for r in runs)
        else:
            assert len(runs) == 1 and runs[0].state == "succeeded"
            batch_id = next(
                d.document_id for d in store.list_documents() if d.tool_id == "workflow_batch_v1"
            )
            from bioimage_app.workflow_batch_storage import (
                WorkflowBatchStoreCommand,
                execute_batch_store,
            )

            assert (
                execute_batch_store(store, WorkflowBatchStoreCommand("load", batch_id)).state
                == "paused"
            )
