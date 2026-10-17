"""Real widget edits, original coordinate mapping and worker/storage/reopen behavior."""

import gc
import os
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
import tifffile
from bioimage_app.api import create_wb_window

if TYPE_CHECKING:
    from bioimage_app.api import WBWindow
from platform_runtime.api import Workspace
from PySide6.QtCore import QPoint, Qt, QThread
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot
from wb_tool.api import (
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    LaneAnnotation,
    LaneROI,
    PreviewRaster,
    WBDocument,
    WBJob,
    WBReply,
    create_wb_background,
    create_wb_view,
    load_tiff,
)


@pytest.fixture
def make_window(qtbot: QtBot) -> Iterator[Callable[[], "WBWindow"]]:
    windows: list[WBWindow] = []

    def make() -> "WBWindow":
        window = create_wb_window()
        windows.append(window)
        return window

    yield make
    for window in windows:
        if not window.resources_closed:
            window.close()
            qtbot.waitUntil(lambda window=window: window.resources_closed, timeout=15000)


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
        assert (
            not WBDocument.from_bytes(store.read_asset(draft.asset))
            .request.lanes[0]
            .bands[0]
            .included
        )


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
