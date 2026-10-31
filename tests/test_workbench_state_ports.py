"""Selection, operation outcome and retry intent are data, not widget presentation."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot
from wb_tool.api import PreviewRaster, create_figure_project_view

from tooling.qt_test_lifecycle import close_and_dispose_window
from tools.wb.tests.test_project_analysis import configured

from .test_project_navigation_session import source_at, start


class StateWindow(WebWorkbenchWindow):
    def probe_open_completion(self) -> None:
        self._ready_project = ""
        self._starting = True
        self._stage = "opening"
        self._poll_session()

    @property
    def ready_project(self) -> str:
        return self._ready_project

    @property
    def route_project(self) -> object:
        return self._route.get("projectId")


def test_blocked_widget_projection_cannot_change_selected_source(
    qtbot: QtBot, tmp_path: Path
) -> None:
    project, _ = configured(tmp_path)
    view = create_figure_project_view()
    qtbot.addWidget(view)
    view.set_project(project)
    view.table.setCurrentCell(0, 0)
    before = view.presentation_key
    # A repaint may update a hidden widget while signals are blocked. It must
    # not become a second writer of the semantic selection.
    view.table.blockSignals(True)
    view.table.setCurrentCell(1, 0)
    view.table.blockSignals(False)
    selected = view.selected_row()
    assert selected is not None and selected.row_id == project.rows[0].row_id
    assert view.presentation_key == before
    source = project.rows[0].source
    assert source is not None
    preview = PreviewRaster(source.sha256, 30, 20, 30, 20, bytes(600), 16, ())
    view.set_source_preview(preview)
    assert view.source_preview is preview
    other = project.rows[1].source
    assert other is not None
    view.set_source_preview(PreviewRaster(other.sha256, 30, 20, 30, 20, bytes(600), 16, ()))
    assert view.source_preview is preview


def test_selection_preserves_identity_on_reorder_but_not_replaced_source(
    qtbot: QtBot, tmp_path: Path
) -> None:
    project, _ = configured(tmp_path)
    view = create_figure_project_view()
    qtbot.addWidget(view)
    view.set_project(project)
    view.table.setCurrentCell(0, 0)
    reordered = project.model_copy(update={"rows": tuple(reversed(project.rows))})
    view.set_project(reordered)
    assert view.selected_row_id == project.rows[0].row_id
    assert view.selection_index == len(project.rows) - 1
    assert view.table.currentRow() == view.selection_index
    replaced = project.rows[0].model_copy(update={"source": project.rows[1].source})
    view.set_project(project.model_copy(update={"rows": (replaced, *project.rows[1:])}))
    assert view.selected_row_id == ""
    assert view.selected_row() is None
    assert view.select_row(project.rows[1].row_id)
    view.set_project(project.model_copy(update={"project_id": "another-project"}))
    assert view.selected_row_id == ""


def test_selection_commits_valid_native_edits_and_rejects_incomplete_ones(
    qtbot: QtBot, tmp_path: Path
) -> None:
    project, _ = configured(tmp_path)
    view = create_figure_project_view()
    qtbot.addWidget(view)
    view.set_project(project)
    view.table.setCurrentCell(0, 0)
    lane_count = view.table.item(0, 3)
    protein = view.table.item(0, 2)
    assert lane_count is not None and protein is not None
    lane_count.setText("")
    assert not view.select_row(project.rows[1].row_id)
    assert view.selected_row_id == project.rows[0].row_id
    assert view.table.currentRow() == 0
    view.table.setCurrentCell(1, 0)
    assert view.table.currentRow() == 0
    assert view.selected_row_id == project.rows[0].row_id
    lane_count.setText(str(project.rows[0].lane_count))
    protein.setText("Renamed")
    assert view.select_row(project.rows[1].row_id)
    assert view.project().rows[0].protein == "Renamed"
    assert view.selected_row_id == project.rows[1].row_id
    assert view.source_list.currentRow() == 1
    assert not view.select_row("retired-row")
    assert view.selected_row_id == project.rows[1].row_id


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path) -> Iterator[StateWindow]:
    settings = QSettings(str(tmp_path / "ports.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    window = StateWindow(settings=settings)
    window.show()
    try:
        yield window
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )


@pytest.mark.parametrize("cancelled", [False, True])
def test_successful_committed_open_ignores_status_wording_and_late_cancel(
    window: StateWindow, qtbot: QtBot, tmp_path: Path, cancelled: bool
) -> None:
    start(window, qtbot, source_at(tmp_path / "original.tif"))
    project = window.host.view.project()
    window.host.view.status.setText("操作失败只是示例文字，当前项目已经完整提交")
    if cancelled:
        window.host.cancellation.set()
    window.probe_open_completion()
    assert window.shutdown_stage == "idle"
    assert window.ready_project == project.project_id
    assert window.route_project == project.project_id


@pytest.mark.parametrize("failure", ["storage failure", ""])
def test_failed_open_cannot_become_success_when_status_is_reworded(
    window: StateWindow, qtbot: QtBot, tmp_path: Path, failure: str
) -> None:
    start(window, qtbot, source_at(tmp_path / "original.tif"))
    window.host.begin_operation()
    window.host.fail_operation(failure)
    window.host.view.status.setText("请检查保存位置")
    window.probe_open_completion()
    assert window.shutdown_stage == "entry_error"
    assert window.ready_project == ""
    assert window.host.operation_error == failure
    window.host.begin_operation()
    window.host.finish_operation("已恢复")
    assert window.host.operation_error == ""


def test_bridge_and_quant_projection_read_selection_data_not_hidden_table(
    window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, paths = configured(tmp_path)
    window.host.view.set_project(project)
    monkeypatch.setattr(
        window.host,
        "_paths",
        {
            row.source.sha256: str(path)
            for row, path in zip(project.rows, paths, strict=False)
            if row.source is not None
        },
    )
    window.host.view.table.setCurrentCell(0, 0)
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=10000)

    def forbidden_read() -> int:
        raise AssertionError("Semantic selection queried a widget")

    monkeypatch.setattr(window.host.view.table, "currentRow", forbidden_read)
    snapshot = window.bridge.snapshot()
    assert snapshot["selectedId"] == project.rows[0].row_id
    assert isinstance(snapshot["quant"], dict)
    assert snapshot["quant"]["rowId"] == project.rows[0].row_id


def test_advanced_empty_failure_never_emits_success(window: WebWorkbenchWindow) -> None:
    advanced = window.bridge.advanced_commands
    advanced.waiting = (
        "failed-empty",
        window.host.view.project_identity,
        window.bridge.session_epoch,
        "metadata_import",
    )
    window.host.begin_operation()
    window.host.fail_operation("")
    advanced.poll()
    assert advanced.response["status"] == "failed"
    assert advanced.response["error"]


def test_retry_location_uses_pending_intent_and_retains_it_after_dialog_cancel(
    window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = source_at(tmp_path / "original.tif")
    window.settings.setValue("project_parent", str(source.parent / "forbidden"))
    window.start_from_images([source.parent], automatic=False)
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=15000)
    assert window.host.operation_error
    window.host.retry_location_button.hide()
    assert window.bridge.snapshot()["canRetryLocation"] is True

    def cancel_directory(*args: object, **kwargs: object) -> str:
        return ""

    def select_directory(*args: object, **kwargs: object) -> str:
        return str(tmp_path / "recovered")

    monkeypatch.setattr(QFileDialog, "getExistingDirectory", cancel_directory)
    window.choose("retry_location")
    assert window.host.can_retry_location
    assert not window.host.workspace_path
    assert window.bridge.snapshot()["canRetryLocation"] is True
    window.host.begin_operation()
    assert not window.host.can_retry_location
    window.host.finish_operation("检查结束，仍待重新选择位置")
    assert window.host.can_retry_location
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", select_directory)
    window.choose("retry_location")
    qtbot.waitUntil(
        lambda: (
            not window.host.operation_busy
            and bool(window.host.workspace_path)
            and not window.host.has_unsaved_changes
            and window.shutdown_stage == "idle"
        ),
        timeout=25000,
    )
    window.host.retry_location_button.show()
    assert not window.host.can_retry_location
    assert window.bridge.snapshot()["canRetryLocation"] is False
    with pytest.raises(ValueError, match="当前没有等待"):
        window.choose("retry_location")
