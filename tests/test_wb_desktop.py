"""Real widget edits, original coordinate mapping and worker/storage/reopen behavior."""

import gc
import json
import os
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree import ElementTree
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from bioimage_app.api import create_wb_window
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from bioimage_app.api import WBWindow
from platform_runtime.api import Workspace
from PySide6.QtCore import QPoint, Qt, QThread
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton, QTableWidget
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot
from shiboken6 import isValid
from wb_tool.api import (
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    LaneAnnotation,
    LaneROI,
    PreviewRaster,
    WBJob,
    WBReply,
    WBWorksheetDocument,
    create_wb_background,
    create_wb_view,
    load_tiff,
    read_wb_document,
)


def cell_text(table: QTableWidget, row: int, column: int) -> str:
    item = table.item(row, column)
    assert item is not None
    return item.text()


def test_grid_draw_crop_and_reopen(
    qtbot: QtBot, tmp_path: Path, make_window: Callable[[], "WBWindow"]
) -> None:
    source = tmp_path / "blank-lanes.tif"
    pixels = np.full((30, 120), 9000, dtype=np.uint16)
    pixels[10:14, 20:30] = 4000
    pixels[10:14, 80:90] = 5000
    tifffile.imwrite(source, pixels)
    workspace = tmp_path / "grid-workspace"
    window = make_window()
    window.show()
    window.open_workspace(str(workspace), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.import_image(str(source))
    qtbot.waitUntil(window.view.analyze_button.isEnabled)
    view = window.view
    view.draw_mode.setCurrentIndex(1)
    view.lane_count.setValue(3)
    view.exclude_left.setValue(12)
    view.exclude_right.setValue(3)
    rect = view.canvas.image_rect()
    QTest.mousePress(
        view.canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(int(rect.left()) + 1, int(rect.top()) + 1),
    )
    QTest.mouseRelease(
        view.canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(int(rect.right()) - 1, int(rect.bottom()) - 1),
    )
    assert len(view.lanes) == 3  # middle sample is blank, still keeps its identity/position
    rois = tuple(lane.roi for lane in view.lanes)
    assert rois[0].x0 >= 12 and rois[-1].x1 <= 117
    assert rois[0].x1 == rois[1].x0 and rois[1].x1 == rois[2].x0
    assert view.crop_button.isEnabled()
    destination = tmp_path / "raw-crop.tif"
    window.export_crop(str(destination))
    qtbot.waitUntil(lambda: destination.exists(), timeout=10000)
    qtbot.waitUntil(view.save_button.isEnabled)
    roi = rois[0]
    with tifffile.TiffFile(destination) as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        np.testing.assert_array_equal(page.asarray(), pixels[roi.y0 : roi.y1, roi.x0 : roi.x1])
        meta = json.loads(page.description)
        assert meta["roi"]["lane_id"] == roi.lane_id
    capture = os.environ.get("BIOIMAGE_GRID_CAPTURE")
    if capture:
        assert window.grab().save(capture)
    document_id = window.documents.itemData(1)
    assert isinstance(document_id, str)
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=10000)
    reopened = make_window()
    reopened.show()
    reopened.open_workspace(str(workspace))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(document_id)
    qtbot.waitUntil(reopened.view.analyze_button.isEnabled, timeout=10000)
    assert tuple(lane.roi for lane in reopened.view.lanes) == rois
    # Parameters only apply to the next drawing; loaded ROIs never regenerate from defaults.
    reopened.view.lane_count.setValue(12)
    assert tuple(lane.roi for lane in reopened.view.lanes) == rois


@pytest.mark.parametrize("extension", ["tif", "png"])
def test_ocr_before_roi_cross_source_and_explicit_binding(
    qtbot: QtBot, tmp_path: Path, make_window: Callable[[], "WBWindow"], extension: str
) -> None:
    source = tmp_path / "measurement.tif"
    tifffile.imwrite(source, np.repeat(np.array([[245], [235], [245]], dtype=np.uint8), 30, axis=1))
    composite = tmp_path / ("labels." + extension)
    image = Image.new("L", (500, 250), 245)
    draw = ImageDraw.Draw(image)
    for text, y in (("1G", 20), ("AKT", 120)):
        draw.text((30, y), text, font=ImageFont.load_default(size=42), fill=0)
    if extension == "png":
        image.save(composite)
    else:
        tifffile.imwrite(composite, np.array(image))
    workspace = tmp_path / "cross-source"
    window = make_window()
    window.show()
    window.open_workspace(str(workspace), create=True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    window.import_image(str(source))
    qtbot.waitUntil(lambda: window.view.raster is not None, timeout=10000)
    window.import_ocr_image(str(composite))
    qtbot.waitUntil(window.import_ocr_button.isEnabled, timeout=10000)
    window.recognize()
    qtbot.waitUntil(lambda: window.view.recognition is not None, timeout=30000)
    assert not window.view.lanes
    panel = window.view.worksheet
    state = panel.state()
    assert state is not None and len(state.rows) == 1 and not state.bindings
    assert state.rows[0].figure_name == "1G" and state.rows[0].row_name == "AKT"
    raster = window.view.raster
    assert raster is not None and (raster.width, raster.height) == (30, 3)
    window.view.tabs.setCurrentIndex(0)
    rect = window.view.canvas.image_rect()
    QTest.mousePress(
        window.view.canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(rect.left() + 2), round(rect.top() + 1)),
    )
    QTest.mouseRelease(
        window.view.canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(rect.right() - 2), round(rect.bottom() + 2)),
    )

    def click(text: str) -> None:
        button = next(
            button for button in window.findChildren(QPushButton) if button.text() == text
        )
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)

    click("添加条带")
    window.view.bounds[1].setValue(2)
    window.view.detected.setChecked(True)
    window.analyze()
    qtbot.waitUntil(lambda: window.view.quantitative_result is not None, timeout=15000)
    window.view.tabs.setCurrentWidget(panel)
    click("添加列")
    panel.table.setCurrentCell(0, 3)
    click("关联所选行/列")
    assert cell_text(panel.table, 0, 3) == "—"
    click("确认所有名称")
    assert cell_text(panel.table, 0, 3) == "10"
    # A blank edited name automatically returns the row to review and clears its value.
    name = panel.table.item(0, 1)
    assert name is not None
    name.setText("")
    assert cell_text(panel.table, 0, 3) == "—"
    click("确认所有名称")
    assert cell_text(panel.table, 0, 3) == "—"
    name.setText("AKT corrected")
    click("确认所有名称")
    assert cell_text(panel.table, 0, 3) == "10"
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=15000)
    with Workspace.open(workspace) as store:
        draft = store.list_documents()[0]
        document = read_wb_document(store.read_asset(draft.asset))
        assert isinstance(document, WBWorksheetDocument) and document.ocr_source is not None
        assert document.source.sha256 != document.ocr_source.sha256
        assert document.measurement is not None and document.worksheet is not None
        assert len(document.worksheet.bindings) == 1
    reopened = make_window()
    reopened.open_workspace(str(workspace))
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=10000)
    reopened.load_document(draft.document_id)
    qtbot.waitUntil(lambda: reopened.view.recognition is not None, timeout=10000)
    qtbot.waitUntil(reopened.import_ocr_button.isEnabled, timeout=10000)
    assert cell_text(reopened.view.worksheet.table, 0, 3) == "10"
    assert reopened.view.ocr_text.rowCount() == 2


def test_actual_ocr_desktop_table_save_reopen_export(
    qtbot: QtBot, tmp_path: Path, make_window: Callable[[], "WBWindow"]
) -> None:
    image = Image.new("L", (1200, 500), 245)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=42)
    for text, x, y in (
        ("Fig 1A", 30, 20),
        ("AKT", 30, 150),
        ("GAPDH", 30, 320),
        ("Fig 2B", 650, 20),
        ("ERK1/2", 650, 150),
        ("beta-actin", 650, 320),
    ):
        draw.text((x, y), text, font=font, fill=0)
    for x in (280, 380, 900, 1000):
        draw.rectangle((x, 165, x + 19, 185), fill=100)
        draw.rectangle((x, 335, x + 19, 355), fill=150)
    source = tmp_path / "拼图.tif"
    tifffile.imwrite(source, np.array(image))
    workspace = tmp_path / "OCR工作区"
    window = make_window()
    window.show()
    window.open_workspace(str(workspace), create=True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    window.import_image(str(source))
    qtbot.waitUntil(lambda: window.view.raster is not None, timeout=10000)
    lanes = tuple(
        LaneAnnotation(
            LaneROI(f"L{index}", x, 120, x + 20, 400),
            (
                BandAnnotation("top", BandBounds(40, 70)),
                BandAnnotation("bottom", BandBounds(210, 240)),
            ),
        )
        for index, x in enumerate((280, 380, 900, 1000))
    )
    raster = window.view.raster
    assert raster is not None
    window.view.set_image(raster, AnalysisRequest(raster.sha256, 0, "dark", lanes))
    window.analyze()
    qtbot.waitUntil(lambda: window.view.quantitative_result is not None, timeout=15000)
    window.recognize()
    qtbot.waitUntil(lambda: window.view.recognition is not None, timeout=30000)
    panel = window.view.worksheet
    state = panel.state()
    assert state is not None and len(state.rows) == 4 and len(state.bindings) == 8
    assert cell_text(panel.table, 0, 3) == "—"
    name = panel.table.item(0, 1)
    assert name is not None
    name.setText("AKT（人工复核）")
    for row in range(4):
        check = panel.table.item(row, 2)
        assert check is not None
        check.setCheckState(Qt.CheckState.Checked)
    assert [cell_text(panel.table, row, column) for row in range(4) for column in (3, 4)] == [
        "3045",
        "3045",
        "1995",
        "1995",
    ] * 2
    panel.table.setCurrentCell(0, 3)
    next(
        button for button in panel.findChildren(QPushButton) if button.text() == "确认所有名称"
    ).click()
    assert (panel.table.currentRow(), panel.table.currentColumn()) == (0, 3)
    capture = os.environ.get("BIOIMAGE_OCR_CAPTURE")
    if capture:
        assert window.grab().save(capture)
    destination = tmp_path / "自动结果.xlsx"
    window.export_table(str(destination))
    qtbot.waitUntil(lambda: destination.exists(), timeout=10000)
    qtbot.waitUntil(window.view.save_button.isEnabled, timeout=10000)
    with ZipFile(destination) as archive:
        root = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        assert [float(node.text or "nan") for node in root.findall(".//s:v", ns)] == [
            3045,
            3045,
            1995,
            1995,
            3045,
            3045,
            1995,
            1995,
        ]
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=15000)
    with Workspace.open(workspace) as store:
        draft = store.list_documents()[0]
        document = read_wb_document(store.read_asset(draft.asset))
        assert isinstance(document, WBWorksheetDocument)
        assert document.recognition is not None and document.measurement is not None
        assert document.worksheet is not None
        assert document.worksheet.rows[0].row_name == "AKT（人工复核）"
        assert all(row.confirmed for row in document.worksheet.rows)
        runs = store.list_runs(draft.document_id)
        assert len(runs) == 2 and all(run.state == "succeeded" for run in runs)
    reopened = make_window()
    reopened.open_workspace(str(workspace))
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=10000)
    reopened.load_document(draft.document_id)
    qtbot.waitUntil(lambda: reopened.view.quantitative_result is not None, timeout=10000)
    assert cell_text(reopened.view.worksheet.table, 0, 1) == "AKT（人工复核）"
    assert cell_text(reopened.view.worksheet.table, 0, 3) == "3045"
    current = reopened.view.quantitative_result
    assert current is not None
    # Geometry changes invalidate values, while name edits above preserved them.
    reopened.view.coordinates[0].setValue(281)
    assert reopened.view.quantitative_result is None
    assert cell_text(reopened.view.worksheet.table, 0, 3) == "—"


def _dispose_owned_windows(windows: list["WBWindow"], qtbot: QtBot) -> None:
    for window in windows:
        if not window.resources_closed:
            window.close()
            qtbot.waitUntil(lambda window=window: window.resources_closed, timeout=15000)
        window.deleteLater()
        qtbot.waitUntil(lambda window=window: not isValid(window), timeout=10000)


@pytest.fixture
def make_window(qtbot: QtBot) -> Iterator[Callable[[], "WBWindow"]]:
    windows: list[WBWindow] = []

    def make() -> "WBWindow":
        window = create_wb_window()
        windows.append(window)
        return window

    yield make
    _dispose_owned_windows(windows, qtbot)


def test_owned_fixture_windows_are_destroyed_on_gui_before_worker_collection(qtbot: QtBot) -> None:
    window = create_wb_window()
    destroyed_threads: list[int] = []

    def record_destroyed(*_args: object) -> None:
        destroyed_threads.append(threading.get_ident())

    window.destroyed.connect(record_destroyed, Qt.ConnectionType.DirectConnection)
    # A retained reference cycle may be collected by the next allocating worker.
    # Teardown must dispose its native widgets before releasing these references.
    holder: dict[str, object] = {"window": window}
    holder["cycle"] = holder
    try:
        _dispose_owned_windows([window], qtbot)
        assert not isValid(window)
        assert destroyed_threads == [threading.get_ident()]
        del holder
        collector = threading.Thread(target=gc.collect)
        collector.start()
        collector.join(timeout=10)
        assert not collector.is_alive()
        assert destroyed_threads == [threading.get_ident()]
    finally:
        if isValid(window):
            window.deleteLater()
            qtbot.waitUntil(lambda: not isValid(window), timeout=10000)


def test_desktop_draw_compute_save_reopen(
    qtbot: QtBot,
    tmp_path: Path,
    make_window: Callable[[], "WBWindow"],
) -> None:
    source = tmp_path / "解析条带.tif"
    tifffile.imwrite(source, np.repeat(np.array([[245], [235], [245]], dtype=np.uint8), 30, axis=1))
    workspace = tmp_path / "中文工作区"
    window = make_window()
    window.show()
    window.open_workspace(str(workspace), create=True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    window.import_image(str(source))
    qtbot.waitUntil(lambda: window.view.raster is not None, timeout=10000)
    canvas = window.view.canvas
    rectangle = canvas.image_rect()
    QTest.mousePress(
        canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(rectangle.left() + 2), round(rectangle.top() + 1)),
    )
    QTest.mouseRelease(
        canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(rectangle.right() - 2), round(rectangle.bottom() + 2)),
    )
    assert len(window.view.lanes) == 1
    assert window.view.lanes[0].roi.y0 == 0 and window.view.lanes[0].roi.y1 == 3
    add_band = next(
        button for button in window.findChildren(QPushButton) if button.text() == "添加条带"
    )
    QTest.mouseClick(add_band, Qt.MouseButton.LeftButton)
    window.view.bounds[1].setValue(2)
    window.view.detected.setChecked(True)
    QTest.mouseClick(window.view.analyze_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.view.results.rowCount() == 1, timeout=15000)
    signal = window.view.results.item(0, 2)
    assert signal is not None and signal.text() == "10"
    assert window.view.plot.values == (10.0, 20.0, 10.0)
    assert len(window.view.plot.measurements) == 1
    capture = os.environ.get("BIOIMAGE_CAPTURE")
    if capture:
        assert window.grab().save(capture)
    document_id = window.documents.itemData(1)
    assert isinstance(document_id, str)
    window.close()
    qtbot.waitUntil(lambda: not window.isVisible(), timeout=10000)
    reopened = make_window()
    reopened.show()
    reopened.open_workspace(str(workspace))
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=10000)
    reopened.load_document(document_id)
    qtbot.waitUntil(lambda: reopened.view.results.rowCount() == 1, timeout=15000)
    assert tuple(reopened.view.lanes) == tuple(window.view.lanes)
    restored_signal = reopened.view.results.item(0, 2)
    assert restored_signal is not None and restored_signal.text() == "10"
    reopened.view.included.setChecked(False)
    reopened.close()
    qtbot.waitUntil(lambda: not reopened.isVisible(), timeout=10000)
    with Workspace.open(workspace) as store:
        draft = store.load_draft(document_id)
        assert draft.revision == 1
        restored = read_wb_document(store.read_asset(draft.asset))
        assert restored.request is not None
        assert not restored.request.lanes[0].bands[0].included


def test_uint16_preview_is_separate_and_background_closes(qtbot: QtBot, tmp_path: Path) -> None:
    pixels = np.array([[1, 257, 65534]], dtype=np.uint16)
    source = tmp_path / "16bit.tif"
    tifffile.imwrite(source, pixels)
    background = create_wb_background()
    replies: list[WBReply] = []
    background.replied.connect(replies.append)
    background.submit(WBJob("preview", path=str(source)))
    qtbot.waitUntil(lambda: bool(replies), timeout=10000)
    assert replies[0].error == "" and isinstance(replies[0].value, PreviewRaster)
    assert replies[0].value.pixels == bytes([0, 1, 254])
    assert replies[0].value.bit_depth == 16
    assert np.array_equal(load_tiff(source).pixels, pixels)
    with qtbot.waitSignal(background.closed, timeout=10000):
        background.shutdown()


def test_invalid_visible_fields_block_old_parameter_calculation(qtbot: QtBot) -> None:
    view = create_wb_view()
    qtbot.addWidget(view)
    raster = PreviewRaster("a" * 64, 10, 5, 10, 5, bytes([245] * 50), 8, ())
    request = AnalysisRequest(
        "a" * 64,
        0,
        "dark",
        (LaneAnnotation(LaneROI("L", 0, 0, 10, 5), (BandAnnotation("B", BandBounds(0, 2)),)),),
    )
    view.set_image(raster, request)
    view.bounds[0].setValue(2)
    with pytest.raises(ValueError):
        view.request(1)
    view.bounds[1].setValue(4)
    assert view.request(1).lanes[0].bands[0].bounds == BandBounds(2, 4)
    view.included.setChecked(False)
    assert not view.request(1).lanes[0].bands[0].included


def test_window_cancel_then_close_confirms_terminal(
    qtbot: QtBot,
    tmp_path: Path,
    make_window: Callable[[], "WBWindow"],
) -> None:
    source = tmp_path / "cancel.tif"
    tifffile.imwrite(source, np.array([[245], [235], [245]], dtype=np.uint8))
    workspace = tmp_path / "cancel-workspace"
    window = make_window()
    window.show()
    window.open_workspace(str(workspace), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.import_image(str(source))
    qtbot.waitUntil(lambda: window.view.raster is not None)
    raster = window.view.raster
    assert raster is not None
    request = AnalysisRequest(
        raster.sha256,
        0,
        "dark",
        (LaneAnnotation(LaneROI("L", 0, 0, 1, 3), (BandAnnotation("B", BandBounds(0, 2)),)),),
    )
    window.view.set_image(raster, request)
    window.analyze()
    qtbot.waitUntil(window.view.cancel_button.isEnabled, timeout=10000)
    QTest.mouseClick(window.view.cancel_button, Qt.MouseButton.LeftButton)
    window.close()
    qtbot.waitUntil(lambda: not window.isVisible(), timeout=15000)
    with Workspace.open(workspace) as store:
        runs = store.list_runs()
        assert len(runs) == 1 and runs[0].state == "cancelled"
        assert runs[0].pid is not None


def test_repeated_window_close_and_collection(qtbot: QtBot) -> None:
    for _ in range(20):
        window = create_wb_window()
        window.show()
        window.close()
        qtbot.waitUntil(lambda window=window: window.resources_closed, timeout=10000)
        del window
        gc.collect()


def test_close_waits_for_nonblocking_thread_join(qtbot: QtBot, monkeypatch: MonkeyPatch) -> None:
    original = QThread.wait
    attempts: list[int] = []

    def delayed_join(thread: QThread, timeout: int) -> bool:
        assert timeout == 0
        attempts.append(timeout)
        return False if len(attempts) < 3 else original(thread, timeout)

    monkeypatch.setattr(QThread, "wait", delayed_join)
    background = create_wb_background()
    emitted: list[int] = []
    background.closed.connect(lambda: emitted.append(len(attempts)))
    background.shutdown()
    qtbot.waitUntil(lambda: bool(emitted), timeout=10000)
    assert emitted[0] >= 3
