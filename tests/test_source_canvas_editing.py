"""Graphical crop edits commit original pixels, including zoomed and focused views."""

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot
from wb_tool.api import LaneROI, PreviewRaster, create_figure_project_view, fixed_lane_grid


def test_graphical_move_resize_and_zoom_preserve_original_pixel_mapping(qtbot: QtBot) -> None:
    view = create_figure_project_view()
    qtbot.addWidget(view)
    view.resize(1200, 780)
    view.show()
    canvas = view.canvas
    raster = PreviewRaster("a" * 64, 600, 160, 300, 80, b"\x90" * 24000, 16, ())
    canvas.set_image(raster)
    crop = LaneROI("row", 100, 50, 400, 110)
    canvas.set_crop(crop)
    canvas.set_lanes(fixed_lane_grid(crop, 3))
    spy = QSignalSpy(canvas.roi_drawn)

    def point(x: int, y: int, bounds: tuple[int, int, int, int] = (0, 0, 600, 160)) -> QPoint:
        rect = canvas.image_rect()
        ox, oy, width, height = bounds
        return QPoint(
            round(rect.x() + (x - ox) * rect.width() / width),
            round(rect.y() + (y - oy) * rect.height() / height),
        )

    QTest.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=point(200, 80))
    assert spy.count() == 0  # Inspecting a crop must not stale saved results.
    QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=point(200, 80))
    QTest.mouseMove(canvas, point(220, 90))
    QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=point(220, 90))
    assert spy.count() == 1
    assert all(abs(a - b) <= 1 for a, b in zip(spy.at(0)[0], (120, 60, 420, 120), strict=True))

    # A focused image still emits absolute source coordinates, never preview coordinates.
    canvas.set_view_region(LaneROI("focus", 50, 20, 550, 140))
    bounds = (50, 20, 500, 120)
    QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=point(400, 110, bounds))
    QTest.mouseMove(canvas, point(450, 125, bounds))
    QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=point(450, 125, bounds))
    assert spy.count() == 2
    assert all(abs(a - b) <= 1 for a, b in zip(spy.at(1)[0], (100, 50, 450, 125), strict=True))

    center = QPointF(canvas.rect().center())
    event = QWheelEvent(
        center,
        center,
        QPoint(),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    old_width = canvas.image_rect().width()
    QApplication.sendEvent(canvas, event)
    assert canvas.image_rect().width() > old_width
    QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=point(200, 80, bounds))
    QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=point(230, 80, bounds))
    assert all(abs(a - b) <= 1 for a, b in zip(spy.at(2)[0], (130, 50, 430, 110), strict=True))
    canvas.reset_zoom()
    assert canvas.image_rect().width() == old_width


def test_dragging_outside_source_clamps_crop_without_negative_pixels(qtbot: QtBot) -> None:
    view = create_figure_project_view()
    qtbot.addWidget(view)
    view.resize(1200, 780)
    view.show()
    canvas = view.canvas
    canvas.set_image(PreviewRaster("b" * 64, 600, 160, 300, 80, b"\x90" * 24000, 16, ()))
    canvas.set_crop(LaneROI("row", 100, 50, 400, 110))
    spy = QSignalSpy(canvas.roi_drawn)
    rect = canvas.image_rect()
    start = QPoint(round(rect.x() + rect.width() / 3), round(rect.center().y()))
    QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(-100, -100))
    assert spy.at(0)[0] == (0, 0, 300, 60)
