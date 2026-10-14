"""Real batch import/review/export/reopen; all storage and render work leaves the GUI thread."""

import json
import os
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from bioimage_app.api import create_figure_project_window
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QTabWidget
from pytestqt.qtbot import QtBot
from wb_tool.api import WBFigureProject

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def item(table: QTableWidget, row: int, column: int) -> QTableWidgetItem:
    result = table.item(row, column)
    assert result is not None
    return result


@pytest.fixture
def project_window(qtbot: QtBot) -> Iterator[Callable[[], "FigureProjectWindow"]]:
    windows: list[FigureProjectWindow] = []

    def make() -> "FigureProjectWindow":
        window = create_figure_project_window()
        windows.append(window)
        window.show()
        return window

    yield make
    for window in windows:
        if not window.resources_closed:
            window.close()
            qtbot.waitUntil(lambda window=window: window.resources_closed, timeout=15000)


def test_project_batch_review_export_reopen(
    qtbot: QtBot, tmp_path: Path, project_window: Callable[[], "FigureProjectWindow"]
) -> None:
    paths: list[str] = []
    for index in range(2):
        source = tmp_path / f"source-{index}.tif"
        pixels = np.full((80, 120), 51400 + 257 * index, dtype=np.uint16)
        pixels[25:30, 20:30] = 12000
        tifffile.imwrite(source, pixels)
        paths.append(str(source))
    workspace = tmp_path / "project-workspace"
    window = project_window()
    window.open_workspace(str(workspace), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.import_images(tuple([*paths, paths[0]]))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    view = window.view
    assert view.table.rowCount() == 2 and "1 个重复" in view.status.text()
    view.numbers["crop_height"].setValue(30)
    # Select and draw on the actual source canvas, then make exact integer edits.
    view.table.selectRow(0)
    qtbot.waitUntil(window.import_button.isEnabled)
    rect = view.canvas.image_rect()
    QTest.mousePress(
        view.canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(int(rect.left()) + 10, int(rect.top()) + 10),
    )
    QTest.mouseRelease(
        view.canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(int(rect.right()) - 10, int(rect.bottom()) - 10),
    )
    assert item(view.table, 0, 4).text()
    for index in range(2):
        for column, value in {2: "AKT", 3: "3", 4: "0", 5: "20", 6: "120", 7: "50", 8: "2"}.items():
            item(view.table, index, column).setText(value)
    # Preview accepts pending rows; export must refuse them.
    window.compose()
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    assert not view.preview_label.pixmap().isNull(), view.status.text()
    target = tmp_path / "reviewed.zip"
    window.compose(str(target))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    assert not target.exists() and "未审核" in view.status.text()
    for index in range(2):
        item(view.table, index, 9).setCheckState(Qt.CheckState.Checked)
    window.compose(str(target))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    assert target.exists(), view.status.text()
    with ZipFile(target) as archive:
        project = WBFigureProject.from_bytes(archive.read("project.json"))
        assert [r.protein for r in project.rows] == ["AKT", "AKT"]
        assert all(r.reviewed and r.empty_lanes == (2,) for r in project.rows)
        manifest = json.loads(archive.read("manifest.json"))
        assert len(manifest["rows"]) == 2
    # Geometry edits withdraw review and stale preview immediately.
    item(view.table, 0, 4).setText("1")
    assert item(view.table, 0, 9).checkState() == Qt.CheckState.Unchecked
    item(view.table, 0, 4).setText("0")
    item(view.table, 0, 9).setCheckState(Qt.CheckState.Checked)
    window.save()
    qtbot.waitUntil(window.import_button.isEnabled)
    capture = os.environ.get("BIOIMAGE_FIGURE_CAPTURE")
    if capture:
        window.compose()
        qtbot.waitUntil(window.import_button.isEnabled)
        tabs = view.findChild(QTabWidget)
        assert tabs is not None
        tabs.setCurrentIndex(1)
        assert window.grab().save(capture)
    saved = view.project()
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=10000)
    # The project uses workspace copies: deleting the external originals cannot break reopen.
    for path in paths:
        Path(path).unlink()
    reopened = project_window()
    reopened.open_workspace(str(workspace))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(saved.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=10000)
    assert reopened.view.project() == saved
    reopened.view.table.selectRow(1)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=10000)
    assert reopened.view.canvas.image_rect().width() > 0
    reopened.new_project()
    qtbot.waitUntil(reopened.import_button.isEnabled)
    fresh = reopened.view.project()
    assert fresh.template == saved.template and fresh.rows == ()
    assert fresh.project_id != saved.project_id


def test_close_during_batch_import_keeps_completed_rows(
    qtbot: QtBot, tmp_path: Path, project_window: Callable[[], "FigureProjectWindow"]
) -> None:
    source = tmp_path / "one.tif"
    tifffile.imwrite(source, np.full((40, 60), 220, dtype=np.uint8))
    window = project_window()
    window.open_workspace(str(tmp_path / "workspace"), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.import_images((str(source),) * 8)
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=10000)
    assert window.view.table.rowCount() == 1
