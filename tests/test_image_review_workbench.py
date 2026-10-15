"""Approved direct manipulation must invalidate measurements and preserve pixel semantics."""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QSignalSpy, QTest
from pytestqt.qtbot import QtBot
from wb_tool.api import LaneROI, PreviewRaster, create_figure_project_view

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
