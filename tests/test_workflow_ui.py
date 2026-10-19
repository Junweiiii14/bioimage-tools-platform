"""Workflow navigation preserves scientific edits and uses existing host commands."""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QScrollArea
from pytestqt.qtbot import QtBot
from wb_tool.api import FigureRender, WBAnalysisProject

from tests.test_project_measurements import item, setup
from tests.test_project_measurements import windows as windows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def test_navigation_keeps_draft_selection_and_dirty_annotation(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    item(view.analysis.lanes, 0, 2).setText("1")
    before = view.project()
    generation = view.generation
    row = view.table.currentRow()
    assert view.analysis.dirty
    for section in (
        "source",
        "metadata",
        "analysis",
        "normalization",
        "layout",
        "template",
        "preview",
        "ocr",
        "export",
    ):
        view.show_section(section)
        assert view.project() == before
        assert view.generation == generation
        assert view.table.currentRow() == row
        assert view.analysis.dirty
    view.show_section("analysis")
    assert not view.table.isVisible()
    assert view.analysis_source.currentIndex() == row
    view.show_section("source")
    assert view.source_list.isVisible()
    assert not view.table.isVisible()
    view.source_tabs.setCurrentIndex(2)
    assert view.table.isVisible()


def test_source_selector_preserves_invalid_edits_and_commits_valid_previous_row(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    view.show_section("analysis")
    original_index = view.table.currentRow()
    assert original_index == 1
    assert view.analysis.plan is not None
    original_id = view.analysis.plan.row_id
    item(view.analysis.lanes, 0, 3).setText("")
    view.analysis_source.setCurrentIndex(0)
    view.analysis_source.activated.emit(0)
    assert view.table.currentRow() == original_index
    assert view.analysis_source.currentIndex() == original_index
    assert view.analysis.plan.row_id == original_id
    assert item(view.analysis.lanes, 0, 3).text() == ""
    # Direct table selection gets the same guard and does not display one row while editing another.
    view.table.setCurrentCell(0, 0)
    assert view.table.currentRow() == original_index
    assert view.analysis.plan.row_id == original_id
    item(view.analysis.lanes, 0, 3).setText("7")
    view.analysis_source.setCurrentIndex(0)
    view.analysis_source.activated.emit(0)
    qtbot.waitUntil(window.import_button.isEnabled)
    assert view.table.currentRow() == 0
    assert view.analysis.plan.row_id != original_id
    project = view.project()
    assert isinstance(project, WBAnalysisProject)
    old_plan = next(plan for plan in project.analyses if plan.row_id == original_id)
    assert old_plan.request.lanes[0].bands[0].bounds is not None
    assert old_plan.request.lanes[0].bands[0].bounds.right == 7


def test_export_page_emits_existing_commands(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    # Disconnect host dialogs; verify each action's actual command signal.
    for button, signal in (
        (view.archive_export_button, view.export_requested),
        (view.image_export_button, view.image_export_requested),
        (view.table_export_button, view.analysis.export_requested),
        (view.ocr_export_button, view.ocr.export_requested),
        (view.normalization_export_button, view.normalization.export_requested),
    ):
        signal.disconnect()
        spy = QSignalSpy(signal)
        view.show_section("export")
        assert button.isVisible()
        button.click()
        assert spy.count() == 1


def test_welcome_and_menu_follow_existing_busy_guards(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    assert window.surface.currentWidget() is window.welcome
    assert all(button.isEnabled() for button, _ in window.welcome_buttons)
    assert not window.view.isEnabled()
    window.open_workspace(str(tmp_path / "workspace"), create=True)
    assert not any(button.isEnabled() for button, _ in window.welcome_buttons)
    assert not any(action.isEnabled() for action, _ in window.project_actions)
    assert window.cancel_button.isEnabled()
    qtbot.waitUntil(window.import_button.isEnabled)
    assert window.surface.currentWidget() is window.view
    assert window.view.isEnabled()
    assert [action.isEnabled() for action, _ in window.project_actions] == [
        False,
        False,
        False,
        True,
    ]


def test_failed_workspace_open_is_visible_on_welcome(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    window.open_workspace(str(tmp_path / "does-not-exist"))
    qtbot.waitUntil(window.open_button.isEnabled)
    assert window.surface.currentWidget() is window.welcome
    assert "失败" in window.welcome_status.text()
    assert window.welcome_status.text() == window.view.status.text()


def test_preview_fit_and_actual_size_are_display_only(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    before = view.project()
    generation = view.generation
    rendered = FigureRender(1800, 800, bytes((31, 127, 221)) * (1800 * 800), "{}")
    view.show_section("preview")
    view.show_render(rendered)
    changes = QSignalSpy(view.changed)
    full_image = view.preview_label.full_pixmap.toImage()
    assert full_image.width() == 1800 and full_image.height() == 800
    assert full_image.pixelColor(900, 400).getRgb() == (31, 127, 221, 255)
    for width, height in ((1100, 780), (1280, 860)):
        window.resize(width, height)
        qtbot.waitUntil(lambda: view.preview_label.pixmap().width() <= view.preview_label.width())
        assert view.preview_label.pixmap().height() <= view.preview_label.height()
        assert view.preview_label.full_pixmap.toImage() == full_image
    view.preview_scale.setCurrentIndex(1)
    assert view.preview_label.pixmap().size() == full_image.size()
    view.preview_scale.setCurrentIndex(0)
    assert view.preview_label.full_pixmap.toImage() == full_image
    assert view.project() == before and view.generation == generation
    assert changes.count() == 0
    assert rendered.rgb == bytes((31, 127, 221)) * (1800 * 800)


def test_coordinate_and_detection_disclosure_do_not_change_parameters(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    before = view.project()
    generation = view.generation
    row = before.rows[0]
    detection = view.suggestions.settings(row, before.template.crop_height)
    assert all(view.table.isColumnHidden(i) for i in range(4, 8))
    view.exact_coordinates.setChecked(True)
    assert all(not view.table.isColumnHidden(i) for i in range(4, 8))
    view.exact_coordinates.setChecked(False)
    view.suggestions_toggle.setChecked(True)
    view.suggestions.advanced_toggle.setChecked(True)
    view.suggestions.advanced_toggle.setChecked(False)
    assert view.suggestions.settings(row, before.template.crop_height) == detection
    assert view.project() == before and view.generation == generation


def test_layout_controls_fit_small_window_without_horizontal_page_scroll(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.view.rebuild_layout()
    window.view.show_section("layout")
    window.resize(1100, 780)
    page = window.view.pages.currentWidget()
    assert isinstance(page, QScrollArea)
    table = window.view.laboratory_layout.table
    qtbot.waitUntil(lambda: page.horizontalScrollBar().maximum() == 0)
    qtbot.waitUntil(lambda: table.horizontalHeader().length() <= table.viewport().width())
    assert window.view.preview_scale.isVisible()
    assert all(table.columnWidth(column) >= 48 for column in range(7))


def test_ocr_results_belong_to_quantification_without_requiring_composition(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    before = view.project()
    generation = view.generation
    assert not view.laboratory_layout.active
    view.show_section("ocr")
    assert view.steps.currentRow() == 1
    assert view.analysis_tabs.currentWidget() is view.ocr
    assert view.analysis_tabs.tabText(view.analysis_tabs.currentIndex()) == "OCR / 结果表"
    assert view.layout_tabs.indexOf(view.ocr) == -1
    view.show_section("source")
    view.show_section("analysis")
    assert view.analysis_tabs.currentWidget() is view.analysis
    view.show_section("normalization")
    assert view.analysis_tabs.currentWidget() is view.normalization
    view.show_section("export")
    assert view.table_export_button.isVisible()
    assert view.project() == before and view.generation == generation
    assert not view.laboratory_layout.active


def test_source_controls_stay_beside_larger_canvas_at_small_width(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.view.show_section("source")
    window.resize(1100, 780)
    view = window.view
    page = view.pages.currentWidget()
    assert isinstance(page, QScrollArea)
    qtbot.waitUntil(lambda: page.horizontalScrollBar().maximum() == 0)
    qtbot.waitUntil(lambda: view.canvas.width() > view.source_controls_scroll.width())
    assert (
        view.source_list.mapToGlobal(QPoint()).x() + view.source_list.width()
        < view.canvas.mapToGlobal(QPoint()).x()
    )
    assert (
        view.canvas.mapToGlobal(QPoint()).x() + view.canvas.width()
        < view.source_controls_scroll.mapToGlobal(QPoint()).x()
    )
    before = view.project()
    generation = view.generation
    view.suggestions_toggle.setChecked(True)
    view.suggestions.advanced_toggle.setChecked(True)
    assert view.suggestions.advanced_settings.isVisible()
    assert view.project() == before and view.generation == generation
