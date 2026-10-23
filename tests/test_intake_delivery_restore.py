"""A delivered project folder opens through the real main window and fresh storage."""

from hashlib import sha256
from pathlib import Path

from bioimage_app.web_window import WebWorkbenchWindow
from pytestqt.qtbot import QtBot
from wb_tool.api import (
    WBIntakeOutputProject,
    finalize_intake_delivery,
    prepare_intake_delivery,
)

from tests.test_project_navigation_session import session_window as session_window
from tools.wb.tests.test_intake_output import full_files


def test_full_directory_restores_to_new_workspace_and_keeps_delivery_unchanged(
    session_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    original, paths, runs = full_files(tmp_path)
    configured = prepare_intake_delivery(
        original,
        output_parent=str(tmp_path),
        workspace_path=str(tmp_path / "old-work"),
        delivery_id="a" * 32,
    )
    assert isinstance(configured, WBIntakeOutputProject)
    exported = finalize_intake_delivery(
        configured, paths, workspace_path=str(tmp_path / "old-work"), runs=runs
    )
    root = Path(exported.destination)
    before = {
        str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }
    window = session_window
    window.open_project(str(root))
    qtbot.waitUntil(
        lambda: (
            window.host.view.project().project_id == original.project_id
            and not window.host.operation_busy
            and not window.host.has_unsaved_changes
            and window.shutdown_stage == "idle"
        ),
        timeout=30000,
    )
    workspace = Path(window.host.workspace_path)
    assert workspace != root and workspace.parent == tmp_path / "projects"
    assert (workspace / "workspace.json").is_file()
    restored = window.host.view.project()
    assert isinstance(restored, WBIntakeOutputProject)
    assert len(restored.intake_crops) == len(original.intake_crops)
    assert tuple(e.crop for e in restored.intake_crops) == tuple(
        e.crop for e in original.intake_crops
    )
    # A restored foreign absolute output path cannot become the next output parent.
    assert window.host.intake_workflow.output_parent(restored) == str(workspace / "outputs")
    after = {
        str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }
    assert after == before
