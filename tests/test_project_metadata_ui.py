"""Real Qt batch editing, save/reopen, stale results and asynchronous parse cancellation."""

import os
from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING

import numpy as np
import pytest
import tifffile
from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtWidgets import QComboBox, QTabWidget
from pytestqt.qtbot import QtBot
from wb_tool.api import MetadataBook, WBNormalizedProject

from tests.test_project_measurements import configure_normalization, item, setup
from tests.test_project_measurements import windows as windows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def select_sources(window: "FigureProjectWindow") -> None:
    table = window.view.table
    for row in range(table.rowCount()):
        table.selectionModel().select(
            table.model().index(row, 0),
            QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
        )


def test_batch_metadata_preserves_runs_then_invalidates_changed_geometry_and_reopens(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    assert all(not item(window.view.table, i, 0).icon().isNull() for i in range(2))
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    configure_normalization(window)
    qtbot.waitUntil(lambda: window.view.normalization.results.rowCount() == 3)
    before = window.view.project()
    assert isinstance(before, WBNormalizedProject)
    path = tmp_path / "metadata.csv"
    path.write_text(
        f"row_id,蛋白,N,备注\n{before.rows[0].row_id},p-AKT,0,first\n{before.rows[1].row_id},Total-AKT,0,second\n",
        encoding="utf-8",
    )
    window.import_metadata(str(path))
    qtbot.waitUntil(window.import_button.isEnabled)
    panel = window.view.metadata
    panel.key_kind.setCurrentIndex(panel.key_kind.findData("row_id"))
    panel.preview_requested.emit("table")
    assert panel.table.rowCount() == 2, panel.status.text()
    assert all(item(panel.table, i, 0).checkState() == Qt.CheckState.Unchecked for i in range(2))
    assert window.view.project() == before
    panel.enabled["protein"].setChecked(True)
    panel.enabled["notes"].setChecked(True)
    panel.select_entries(True)
    item(panel.table, 1, 5).setText("total-AKT corrected")
    panel.apply_requested.emit()
    named = window.view.project()
    assert isinstance(named, WBNormalizedProject)
    assert named.rows[0].protein == "p-AKT" and named.rows[1].protein == "total-AKT corrected"
    assert all(r.reviewed for r in named.rows)
    assert named.analyses == before.analyses and named.normalizations == before.normalizations
    assert tuple(r.source for r in named.rows) == tuple(r.source for r in before.rows)
    qtbot.waitUntil(lambda: window.view.normalization.results.rowCount() == 3)
    assert item(window.view.normalization.results, 0, 8).text() == "0.5"
    window.refresh_project_table()
    qtbot.waitUntil(window.import_button.isEnabled)
    assert [item(window.view.analysis.results, i, 3).text() for i in range(6)] == [
        "4000",
        "",
        "0",
        "8000",
        "16000",
        "0",
    ]
    select_sources(window)
    for check in panel.enabled.values():
        check.setChecked(False)
    panel.enabled["lane_count"].setChecked(True)
    panel.common["lane_count"].setText("1")
    panel.preview_requested.emit("common")
    panel.select_entries(True)
    panel.apply_requested.emit()
    assert "空泳道" in panel.status.text()
    assert window.view.project() == named  # Row 0's empty slot 2 is incompatible; no partial edits.
    panel.enabled["empty_lanes"].setChecked(True)
    panel.common["empty_lanes"].setText("无")
    panel.preview_requested.emit("common")
    panel.select_entries(True)
    capture = os.environ.get("BIOIMAGE_METADATA_CAPTURE")
    if capture:
        tabs = window.view.findChild(QTabWidget)
        assert tabs is not None
        tabs.setCurrentWidget(panel)
        assert window.grab().save(capture)
    panel.apply_requested.emit()
    changed = window.view.project()
    assert isinstance(changed, WBNormalizedProject)
    assert all(r.lane_count == 1 and r.empty_lanes == () and not r.reviewed for r in changed.rows)
    assert changed.analyses == before.analyses and changed.normalizations == before.normalizations
    qtbot.waitUntil(lambda: window.view.normalization.results.rowCount() == 3)
    assert item(window.view.normalization.results, 0, 8).text() == ""
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    reopened = windows()
    reopened.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(changed.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=20000)
    loaded = reopened.view.project()
    assert isinstance(loaded, WBNormalizedProject)
    assert loaded.rows == changed.rows and loaded.analyses == changed.analyses
    assert loaded.normalizations == changed.normalizations
    assert all(item(reopened.view.analysis.results, i, 3).text() == "" for i in range(2))
    reopened.load_thumbnails()
    qtbot.waitUntil(reopened.import_button.isEnabled)
    assert all(not item(reopened.view.table, i, 0).icon().isNull() for i in range(2))


def test_preview_stale_formula_correction_and_ambiguous_target(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    panel = window.view.metadata
    path = tmp_path / "metadata.csv"
    path.write_text("filename,蛋白\noriginal0.tiff,=1+1\nunknown.tif,Other\n", encoding="utf-8")
    window.import_metadata(str(path))
    qtbot.waitUntil(window.import_button.isEnabled)
    panel.preview_requested.emit("table")
    panel.enabled["protein"].setChecked(True)
    panel.select_entries(True)
    panel.apply_requested.emit()
    assert "明确关联" in panel.status.text()
    target = panel.table.cellWidget(1, 2)
    assert isinstance(target, QComboBox)
    target.setCurrentIndex(2)
    panel.apply_requested.emit()
    assert "公式" in panel.status.text()
    item(panel.table, 0, 5).setText("corrected")
    item(window.view.table, 0, 10).setText("new edit")
    panel.apply_requested.emit()
    assert "已修改" in panel.status.text()
    assert window.view.project().rows[0].protein == "AKT"
    panel.preview_requested.emit("table")
    item(panel.table, 0, 5).setText("corrected")
    item(panel.table, 0, 0).setCheckState(Qt.CheckState.Checked)
    panel.apply_requested.emit()
    assert window.view.project().rows[0].protein == "corrected"
    assert window.view.project().rows[1].protein == "AKT"


@pytest.mark.parametrize("action", ["cancel", "edit", "close"])
def test_late_parse_keeps_previous_book_and_draft(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    windows: Callable[[], "FigureProjectWindow"],
    action: str,
) -> None:
    from wb_tool.adapters import metadata_input

    window = windows()
    setup(qtbot, tmp_path, window)
    path = tmp_path / "metadata.csv"
    path.write_text("filename,蛋白\noriginal0.tiff,changed\n", encoding="utf-8")
    window.import_metadata(str(path))
    qtbot.waitUntil(window.import_button.isEnabled)
    original = window.view.metadata.book
    assert original is not None
    entered, release = Event(), Event()
    read = metadata_input.read_metadata_file

    def delayed(path: str | Path, *, cancelled: Callable[[], bool] = lambda: False) -> MetadataBook:
        entered.set()
        if not release.wait(5):
            raise ValueError("测试同步未及时释放")
        return read(path)  # Deliberately return a successful old result after cancel/close.

    monkeypatch.setattr(metadata_input, "read_metadata_file", delayed)
    window.import_metadata(str(path))
    try:
        qtbot.waitUntil(entered.is_set)
        if action == "cancel":
            window.cancel()
        elif action == "close":
            window.close()
        else:
            item(window.view.table, 0, 10).setText("edit during parse")
    finally:
        release.set()
    if action == "close":
        qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    else:
        qtbot.waitUntil(window.import_button.isEnabled)
        assert window.view.metadata.book is original
    assert window.view.project().rows[0].protein == "AKT"
    if action == "edit":
        assert window.view.project().rows[0].notes == "edit during parse"


def test_failed_parse_retains_previous_book_preview_and_draft(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    path = tmp_path / "metadata.csv"
    path.write_text("filename,蛋白\noriginal0.tiff,proposal\n", encoding="utf-8")
    window.import_metadata(str(path))
    qtbot.waitUntil(window.import_button.isEnabled)
    panel = window.view.metadata
    panel.preview_requested.emit("table")
    book, preview, project = panel.book, panel.preview, window.view.project()
    broken = tmp_path / "broken.xlsx"
    broken.write_bytes(b"invalid")
    window.import_metadata(str(broken))
    qtbot.waitUntil(window.import_button.isEnabled)
    assert "无法读取" in window.view.status.text()
    assert panel.book is book and panel.preview is preview
    assert window.view.project() == project


def test_bad_import_continues_and_thumbnail_pixels_are_bounded(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
) -> None:
    window = windows()
    path = tmp_path / "Fig2_AKT_3.tiff"
    pixels = np.full((160, 3000), 50000, dtype=np.uint16)
    pixels[20:40, 100:200] = 3000
    tifffile.imwrite(path, pixels)
    bad = tmp_path / "bad.tif"
    bad.write_bytes(b"invalid tiff")
    window.open_workspace(str(tmp_path / "workspace"), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.import_images((str(bad), str(path), str(path)))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    project = window.view.project()
    assert (
        len(project.rows) == 1 and project.rows[0].width == 3000 and project.rows[0].bit_depth == 16
    )
    assert "1 个重复原图" in window.view.status.text() and "1 个失败" in window.view.status.text()
    assert not item(window.view.table, 0, 0).icon().isNull()
    with tifffile.TiffFile(path) as source:
        assert np.array_equal(source.asarray(), pixels)
    select_sources(window)
    panel = window.view.metadata
    panel.preview_requested.emit("filename")
    panel.select_entries(True)
    for field in ("figure", "protein", "lane_count"):
        panel.enabled[field].setChecked(True)
    panel.apply_requested.emit()
    assert window.view.project().rows[0].figure == "Fig2"
    assert window.view.project().rows[0].protein == "AKT"
    assert window.view.project().rows[0].lane_count == 3
