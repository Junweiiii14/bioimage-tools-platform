"""Real batch import/review/export/reopen; all storage and render work leaves the GUI thread."""

import json
import os
from collections.abc import Callable, Iterator
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from bioimage_app.api import create_figure_project_window
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
from pytestqt.qtbot import QtBot
from wb_tool.api import CropDetectionSettings, CropSuggestion, WBFigureProject, WBReviewProject

from tooling.qt_test_lifecycle import close_and_dispose_window

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
        close_and_dispose_window(
            window,
            qtbot,
            resources_closed=lambda window=window: window.resources_closed,
            timeout=15000,
        )


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
        view.show_section("preview")
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


def candidate_sources(tmp_path: Path, count: int = 1) -> tuple[str, ...]:
    paths: list[str] = []
    for index in range(count):
        pixels = np.full((220, 300), 1000, dtype=np.uint16)
        pixels[20:200, 20:260] = 50000
        pixels[45:53, 40:60] = 22000
        pixels[130:138, 40:60] = 22000
        for centre in (110, 170, 230):
            if centre != 170:
                pixels[77:87, centre - 15 : centre + 15] = 20000
            pixels[145:153, centre - 15 : centre + 15] = 34000
        pixels[0, 0] += index  # Independent source identity without changing the known bands.
        path = tmp_path / f"candidate-{index}.tif"
        tifffile.imwrite(path, pixels)
        paths.append(str(path))
    return tuple(paths)


def prepare_candidates(
    window: "FigureProjectWindow", qtbot: QtBot, tmp_path: Path, count: int = 1
) -> None:
    window.open_workspace(str(tmp_path / "workspace"), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.import_images(candidate_sources(tmp_path, count))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    for row in range(count):
        item(window.view.table, row, 3).setText("3")
    window.view.numbers["crop_height"].setValue(30)
    window.view.table.selectRow(0)
    qtbot.waitUntil(window.import_button.isEnabled)


def test_detect_apply_edit_restore_and_reopen_suggestions(
    qtbot: QtBot, tmp_path: Path, project_window: Callable[[], "FigureProjectWindow"]
) -> None:
    window = project_window()
    prepare_candidates(window, qtbot, tmp_path)
    view, panel = window.view, window.view.suggestions
    QTest.mouseClick(panel.run_one, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(window.import_button.isEnabled)
    project = view.project()
    assert isinstance(project, WBReviewProject)
    assert project.rows[0].roi is None  # Recording suggestions alone never applies geometry.
    result = project.suggestions[0].result
    assert result is not None and len(result.candidates) == 2
    assert panel.candidates.count() == 2 and panel.apply.isEnabled()
    panel.candidates.setCurrentIndex(1)
    assert "可能空槽：(2,)" in panel.details.text()
    QTest.mouseClick(panel.apply, Qt.MouseButton.LeftButton)
    assert not view.project().rows[0].reviewed
    applied = view.project().rows[0].roi
    assert applied is not None and applied.y0 == result.candidates[1].roi.y0
    assert applied.y0 <= 77 and applied.y1 >= 87 and applied.y1 - applied.y0 == 30
    item(view.table, 0, 9).setCheckState(Qt.CheckState.Checked)
    item(view.table, 0, 5).setText(str(applied.y0 + 1))
    assert item(view.table, 0, 9).checkState() == Qt.CheckState.Unchecked
    QTest.mouseClick(panel.restore, Qt.MouseButton.LeftButton)
    restored = view.project().rows[0].roi
    assert restored is not None and restored.y0 == result.candidates[0].roi.y0
    assert restored != applied and restored.y0 <= 145 and restored.y1 >= 153
    # Old parameter snapshots remain inspectable but cannot be reapplied after N changes.
    item(view.table, 0, 3).setText("4")
    assert not panel.apply.isEnabled() and "重新检测" in panel.details.text()
    item(view.table, 0, 3).setText("3")
    assert panel.apply.isEnabled()
    view.filter.setCurrentIndex(5)
    assert not view.table.isRowHidden(0)
    view.filter.setCurrentIndex(0)
    QTest.mouseClick(panel.focus, Qt.MouseButton.LeftButton)
    rect = view.canvas.image_rect()
    QTest.mousePress(
        view.canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(rect.x() + rect.width() * 0.25), round(rect.y() + rect.height() * 0.25)),
    )
    QTest.mouseRelease(
        view.canvas,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(rect.x() + rect.width() * 0.75), round(rect.y() + rect.height() * 0.75)),
    )
    zoomed = view.project().rows[0].roi
    assert zoomed is not None
    assert (zoomed.x0, zoomed.y0, zoomed.x1, zoomed.y1) == pytest.approx((80, 65, 200, 155), abs=1)
    QTest.mouseClick(panel.restore, Qt.MouseButton.LeftButton)
    capture = os.environ.get("BIOIMAGE_CANDIDATE_CAPTURE")
    if capture:
        assert window.grab().save(capture)
    window.save()
    qtbot.waitUntil(window.import_button.isEnabled)
    saved = view.project()
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed)
    reopened = project_window()
    reopened.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(saved.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled)
    assert reopened.view.project() == saved
    reopened.view.table.selectRow(0)
    qtbot.waitUntil(reopened.import_button.isEnabled)
    assert reopened.view.suggestions.candidates.count() == 2
    reopened.view.remove_row()
    assert isinstance(reopened.view.project(), WBReviewProject)
    assert not reopened.view.project().rows


def test_batch_failure_continues_and_records_error(
    qtbot: QtBot, tmp_path: Path, project_window: Callable[[], "FigureProjectWindow"]
) -> None:
    window = project_window()
    prepare_candidates(window, qtbot, tmp_path, 2)
    source = window.view.project().rows[0].source
    assert source is not None
    (tmp_path / "workspace" / source.relative_path).unlink()
    QTest.mouseClick(window.view.suggestions.run_all, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(window.import_button.isEnabled)
    project = window.view.project()
    assert isinstance(project, WBReviewProject)
    assert project.suggestions[0].error and project.suggestions[0].result is None
    assert project.suggestions[1].result is not None
    assert "完成 1 行，失败 1 行" in window.view.status.text()
    window.view.filter.setCurrentIndex(7)
    assert not window.view.table.isRowHidden(0) and window.view.table.isRowHidden(1)


@pytest.mark.parametrize("action", ["cancel", "close", "edit"])
def test_batch_cancel_close_and_edit_do_not_publish_late_results(
    qtbot: QtBot,
    tmp_path: Path,
    project_window: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    from wb_tool.adapters.crop_suggestions import suggest_crops as original

    entered, release = Event(), Event()
    calls: list[str] = []

    def controlled(
        source: str,
        sha: str,
        row_id: str,
        revision: int,
        settings: CropDetectionSettings,
        *,
        cancelled: Callable[[], bool],
    ) -> CropSuggestion:
        calls.append(row_id)
        if len(calls) == 2:
            entered.set()
            while not release.wait(0.005):
                if cancelled():
                    raise ValueError("候选检测已取消")
        return original(source, sha, row_id, revision, settings, cancelled=cancelled)

    monkeypatch.setattr("wb_tool.adapters.crop_suggestions.suggest_crops", controlled)
    window = project_window()
    prepare_candidates(window, qtbot, tmp_path, 3)
    window.detect_crops(True)
    try:
        qtbot.waitUntil(entered.is_set)
        if action == "edit":
            item(window.view.table, 0, 2).setText("changed while running")
        elif action == "close":
            window.close()
        else:
            QTest.mouseClick(window.cancel_button, Qt.MouseButton.LeftButton)
    finally:
        release.set()
    if action == "close":
        qtbot.waitUntil(lambda: window.resources_closed)
    else:
        qtbot.waitUntil(window.import_button.isEnabled)
    project = window.view.project()
    assert len(calls) == 2  # The third source is never started after cancellation/staleness.
    if action == "edit":
        assert not isinstance(project, WBReviewProject)
        assert project.rows[0].protein == "changed while running"
        assert "已丢弃" in window.view.status.text()
    else:
        assert isinstance(project, WBReviewProject) and len(project.suggestions) == 1
        assert project.rows[0].roi is None
    if action == "close":
        reopened = project_window()
        reopened.open_workspace(str(tmp_path / "workspace"))
        qtbot.waitUntil(reopened.import_button.isEnabled)
        reopened.load_document(project.project_id)
        qtbot.waitUntil(reopened.import_button.isEnabled)
        assert reopened.view.project() == project
