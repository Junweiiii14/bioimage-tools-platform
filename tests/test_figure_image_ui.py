"""Saved full-resolution image export, real TIFF OCR and cancellation through actual Qt ports."""

import json
import os
from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any

import pytest
import tifffile
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot
from wb_tool.api import WBNormalizedProject, render_figure

from tests.test_project_measurements import configure_normalization, item, setup
from tests.test_project_measurements import windows as windows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def test_full_tiff_png_export_real_ocr_fill_and_reopen(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window, width_multiplier=80, crop_height=50)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    configure_normalization(window)
    qtbot.waitUntil(lambda: window.view.normalization.results.rowCount() == 3)
    for key, value in (("font_size", 42), ("row_gap", 55), ("label_width", 180)):
        window.view.numbers[key].setValue(value)
    qtbot.waitUntil(window.import_button.isEnabled)
    before = window.view.project()
    assert isinstance(before, WBNormalizedProject)
    tiff = tmp_path / "full.tif"
    window.export_figure_image(str(tiff))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=15000)
    assert tiff.exists(), window.view.status.text()
    exported = window.view.project()
    with tifffile.TiffFile(tiff) as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        metadata = json.loads(page.description)
        assert metadata["project"] == exported.model_dump(mode="json")
        assert page.imagewidth > 2048

    # Exercise the format selector and automatic suffix without a native OS dialog.
    def picked(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return str(tmp_path / "full-png"), "PNG (*.png)"

    monkeypatch.setattr(QFileDialog, "getSaveFileName", picked)
    QTest.mouseClick(window.view.image_export_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=15000)
    png = tmp_path / "full-png.png"
    assert png.exists(), window.view.status.text()
    with Image.open(tiff) as first, Image.open(png) as second:
        assert first.size == second.size and first.tobytes() == second.tobytes()
    # A display TIFF is admitted for OCR but is not appended to quantitative sources.
    window.import_images((str(tiff),))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    assert len(window.view.project().rows) == len(before.rows)
    assert "显示拼图" in window.view.status.text()
    window.import_ocr_image(str(tiff))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    window.recognize_project()
    qtbot.waitUntil(window.import_button.isEnabled, timeout=30000)
    project = window.view.project()
    assert isinstance(project, WBNormalizedProject) and project.ocr and project.ocr.recognition, (
        window.view.status.text()
    )
    assert project.analyses == before.analyses and project.normalizations == before.normalizations
    assert project.ocr.width > 2048 and len(project.ocr.rows) == 2
    assert not project.ocr.recognition.preprocess_id.startswith("ocr_png_")
    assert all(not row.confirmed and row.link is None for row in project.ocr.rows)
    window.view.bind_ocr(project.ocr.rows[0].row_id, project.rows[0].row_id)
    item(window.view.ocr.table, 0, 2).setCheckState(Qt.CheckState.Checked)
    qtbot.waitUntil(
        lambda: (
            window.view.ocr.results.rowCount() >= 3
            and item(window.view.ocr.results, 0, 3).text() == "4000"
        )
    )
    assert item(window.view.normalization.results, 0, 8).text() == "0.5"
    capture = os.environ.get("BIOIMAGE_DIRECT_IMAGE_CAPTURE")
    if capture:
        window.view.show_section("ocr")
        assert window.grab().save(capture)
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    reopened = windows()
    reopened.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(project.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=20000)
    assert item(reopened.view.ocr.results, 0, 3).text() == "4000"
    assert item(reopened.view.normalization.results, 0, 8).text() == "0.5"


@pytest.mark.parametrize("action", ["cancel", "close", "edit"])
def test_late_render_does_not_publish_after_cancel_close_or_edit(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    from wb_tool.adapters import figure_image_export

    window = windows()
    setup(qtbot, tmp_path, window)
    window.view.numbers["font_size"].setValue(8)
    entered, release = Event(), Event()

    def delayed(*args: Any, **kwargs: Any):
        entered.set()
        if not release.wait(5):
            raise ValueError("image render test timed out")
        return render_figure(*args, **kwargs)

    monkeypatch.setattr(figure_image_export, "render_figure", delayed)
    target = tmp_path / "late.tif"
    window.export_figure_image(str(target))
    try:
        qtbot.waitUntil(entered.is_set)
        if action == "close":
            window.close()
            assert not window.resources_closed
        elif action == "cancel":
            window.cancel()
        else:
            item(window.view.table, 0, 2).setText("new label")
    finally:
        release.set()
    qtbot.waitUntil(
        (lambda: window.resources_closed) if action == "close" else window.import_button.isEnabled,
        timeout=15000,
    )
    assert not target.exists() and not list(tmp_path.glob(".wb-image-*"))
    if action == "edit":
        assert window.view.project().rows[0].protein == "new label"


@pytest.mark.parametrize("action", ["cancel", "close", "edit"])
def test_export_saved_callback_does_not_restart_cancelled_work(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"], action: str
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.view.numbers["font_size"].setValue(8)
    target = tmp_path / "save-cancel.png"
    window.export_figure_image(str(target))
    if action == "close":
        window.close()
    elif action == "cancel":
        window.cancel()
    else:
        window.view.name.setText("newer label")
        window.view.name.textEdited.emit("newer label")
    qtbot.waitUntil(
        (lambda: window.resources_closed) if action == "close" else window.import_button.isEnabled,
        timeout=15000,
    )
    assert not target.exists()
    if action == "edit":
        assert window.view.project().name == "newer label"


def test_late_close_keeps_already_published_image(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wb_tool.adapters import figure_image_export

    window = windows()
    setup(qtbot, tmp_path, window)
    window.view.numbers["font_size"].setValue(8)
    entered, release = Event(), Event()
    original: Callable[..., str] = figure_image_export.export_figure_image

    def published(*args: Any, **kwargs: Any):
        result = original(*args, **kwargs)
        entered.set()
        if not release.wait(5):
            raise ValueError("published image test timed out")
        return result

    monkeypatch.setattr(figure_image_export, "export_figure_image", published)
    target = tmp_path / "published.png"
    window.export_figure_image(str(target))
    try:
        qtbot.waitUntil(entered.is_set, timeout=10000)
        window.close()
        assert not window.resources_closed
    finally:
        release.set()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=15000)
    with Image.open(target) as image:
        assert image.mode == "RGB" and image.info["wb_provenance"]


def test_unreviewed_and_existing_target_errors_remain_visible(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.view.numbers["font_size"].setValue(8)
    item(window.view.table, 0, 9).setCheckState(Qt.CheckState.Unchecked)
    target = tmp_path / "rejected.tif"
    window.export_figure_image(str(target))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    assert not target.exists() and "未审核" in window.view.status.text()
    item(window.view.table, 0, 9).setCheckState(Qt.CheckState.Checked)
    target.write_bytes(b"existing image")
    window.export_figure_image(str(target))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    assert target.read_bytes() == b"existing image" and "已存在" in window.view.status.text()
