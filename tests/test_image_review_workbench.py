"""Approved direct manipulation must invalidate measurements and preserve pixel semantics."""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QSignalSpy, QTest
from pytestqt.qtbot import QtBot
from wb_tool.api import LaneROI, PreviewRaster, WBFigureProject, create_figure_project_view

from tests.test_project_measurements import item, setup
from tests.test_project_measurements import windows as windows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def test_curve_drag_keyboard_undo_invalidates_values_but_keeps_profile_evidence(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    view = window.view
    view.table.setCurrentCell(1, 0)
    qtbot.waitUntil(window.import_button.isEnabled)
    view.show_section("analysis")
    panel = view.analysis
    plot = panel.plot
    original = tuple(plot.values)
    assert len(original) == 10
    assert item(panel.summary, 0, 1).text() == "8000"
    assert plot.bounds is not None and plot.bounds.left == 2
    area_width = plot.width() - 80
    # Bottom-left endpoint, then one original sample to the left.
    start = QPoint(round(62 + 2 * area_width / 9), plot.height() - 34)
    end = QPoint(round(62 + area_width / 9), plot.height() - 34)
    QTest.mousePress(plot, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(plot, end)
    QTest.mouseRelease(plot, Qt.MouseButton.LeftButton, pos=end)
    request = panel.request()
    assert request is not None
    assert request.lanes[0].bands[0].bounds is not None
    assert request.lanes[0].bands[0].bounds.left == 1
    assert request.lanes[0].bands[0].baseline is None  # endpoint mode preserved
    assert panel.loaded is None
    assert item(panel.summary, 0, 1).text() == "—"
    assert plot.values == original
    panel.undo_button.click()
    assert item(panel.lanes, 0, 2).text() == "2"
    assert item(panel.summary, 0, 1).text() == "—"  # undo is not a fabricated run
    panel.redo_button.click()
    assert item(panel.lanes, 0, 2).text() == "1"
    QTest.keyClick(plot, Qt.Key.Key_Right)
    assert item(panel.lanes, 0, 2).text() == "2"
    # Two Tab presses reach the baseline-left handle; up changes intensity.
    QTest.keyClick(plot, Qt.Key.Key_Tab)
    QTest.keyClick(plot, Qt.Key.Key_Tab)
    QTest.keyClick(plot, Qt.Key.Key_Up)
    request = panel.request()
    assert request is not None and request.lanes[0].bands[0].baseline is not None
    assert request.lanes[0].bands[0].baseline.left_value > original[2]
    panel.lane_selector.activated.emit(1)
    assert not plot.values  # previous lane evidence cannot masquerade as this lane


def test_keyboard_crop_uses_original_pixels_and_clamps_at_image_edge(qtbot: QtBot) -> None:
    view = create_figure_project_view()
    qtbot.addWidget(view)
    view.show()
    canvas = view.canvas
    canvas.set_image(PreviewRaster("c" * 64, 600, 160, 300, 80, b"\x90" * 24000, 16, ()))
    canvas.set_crop(LaneROI("row", 100, 50, 400, 110))
    canvas.set_view_region(LaneROI("focus", 50, 20, 550, 140))
    spy = QSignalSpy(canvas.roi_drawn)
    QTest.keyClick(canvas, Qt.Key.Key_Right)
    assert spy.at(0)[0] == (101, 50, 401, 110)
    QTest.keyClick(canvas, Qt.Key.Key_Down, Qt.KeyboardModifier.AltModifier)
    assert spy.at(1)[0] == (100, 50, 400, 111)
    canvas.set_crop(LaneROI("edge", 0, 0, 600, 160))
    QTest.keyClick(canvas, Qt.Key.Key_Left)
    assert spy.count() == 2


def test_graphical_crop_undo_redo_revoke_geometrical_confirmation(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    view.canvas.roi_drawn.emit((0, 6, 30, 16))
    assert view.selected_row() is not None
    assert item(view.table, 1, 5).text() == "6"
    assert item(view.table, 1, 9).checkState() == Qt.CheckState.Unchecked
    view.undo_review()
    assert item(view.table, 1, 5).text() == "5"
    assert item(view.table, 1, 9).checkState() == Qt.CheckState.Unchecked
    view.redo_review()
    assert item(view.table, 1, 5).text() == "6"


def test_autosave_and_recompute_preserve_selection_canvas_curve_history(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    view = window.view
    view.table.setCurrentCell(1, 0)
    qtbot.waitUntil(window.import_button.isEnabled)
    view.show_section("analysis")
    panel = view.analysis
    panel.lane_selector.activated.emit(1)
    plot = panel.plot
    assert panel.plan is not None and panel.plan.run is not None
    old_run = panel.plan.run.run_id
    source = view.selected_row()
    assert source is not None
    raster_size = view.canvas.image_rect().size()
    source_requests = QSignalSpy(view.source_requested)
    window.activateWindow()
    qtbot.waitUntil(window.isActiveWindow)
    plot.setFocus()
    qtbot.waitUntil(plot.hasFocus)
    QTest.keyClick(plot, Qt.Key.Key_Right)
    assert item(panel.lanes, 1, 2).text() == "3"
    # Real 700 ms autosave -> persisted project -> worker -> recompute, not a
    # direct show_plan simulation. The displayed source must never disappear.
    qtbot.waitUntil(
        lambda: (
            bool(panel.plan and panel.plan.run and panel.plan.run.run_id != old_run)
            and not window.operation_busy
        ),
        timeout=20000,
    )
    selected = view.selected_row()
    assert selected is not None and selected.row_id == source.row_id
    assert view.table.currentRow() == 1 and panel.lanes.currentRow() == 1
    assert view.canvas.image_rect().size() == raster_size
    assert source_requests.count() == 0
    assert plot.values and panel.undo_button.isEnabled()
    qtbot.waitUntil(plot.hasFocus)
    panel.undo_button.click()
    assert item(panel.lanes, 1, 2).text() == "2"
    assert panel.loaded is None
    assert item(panel.summary, 1, 1).text() == "—"
    # Project switching belongs to the host, so exercise identity reset on an
    # unattached view instead of placing a foreign document in an open workspace.
    detached = create_figure_project_view()
    qtbot.addWidget(detached)
    detached.set_project(view.project())
    detached.table.setCurrentCell(1, 0)
    detached.canvas.set_image(PreviewRaster("d" * 64, 10, 10, 10, 10, b"\x90" * 100, 8, ()))
    detached.set_project(WBFigureProject(project_id="another-project"))
    assert detached.table.currentRow() == -1
    assert detached.canvas.image_rect().isEmpty()
    assert not detached.analysis.undo_button.isEnabled()


def test_reopen_preview_export_and_metadata_autosave_keep_verified_results(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    original = windows()
    setup(qtbot, tmp_path, original, crop_height=40)
    original.analyze_project(True)
    qtbot.waitUntil(original.import_button.isEnabled, timeout=20000)
    document_id = original.view.project().project_id
    original.close()
    qtbot.waitUntil(lambda: original.resources_closed, timeout=20000)
    window = windows()
    window.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(window.import_button.isEnabled)
    window.load_document(document_id)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    view = window.view
    expected = ["4000", "", "0", "8000", "16000", "0"]
    assert [item(view.analysis.results, i, 3).text() for i in range(6)] == expected
    view.show_section("template")
    qtbot.waitUntil(
        lambda: (
            not window.operation_busy
            and (not view.preview_label.full_pixmap.isNull() or "失败" in view.status.text())
        ),
        timeout=20000,
    )
    assert not view.preview_label.full_pixmap.isNull(), view.status.text()
    view.show_section("export")
    assert view.analysis.results.rowCount() == 6
    assert [item(view.analysis.results, i, 3).text() for i in range(6)] == expected
    # A label-only edit schedules a save but no new measurement. Both its new
    # label and existing verified values must be automatically visible afterward.
    item(view.table, 1, 2).setText("p-AKT")
    qtbot.waitUntil(
        lambda: (
            not window.operation_busy
            and view.analysis.results.rowCount() == 6
            and item(view.analysis.results, 3, 1).text() == "p-AKT"
        ),
        timeout=20000,
    )
    assert [item(view.analysis.results, i, 3).text() for i in range(6)] == expected
