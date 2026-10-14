"""Actual Qt edits, worker processes, committed multi-source results and reopening."""

import os
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree import ElementTree
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from bioimage_app.api import create_figure_project_window
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QTabWidget
from pytestqt.qtbot import QtBot
from wb_tool.api import WBAnalysisProject

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def item(table: QTableWidget, row: int, column: int) -> QTableWidgetItem:
    value = table.item(row, column)
    assert value is not None
    return value


@pytest.fixture
def windows(qtbot: QtBot) -> Iterator[Callable[[], "FigureProjectWindow"]]:
    opened: list[FigureProjectWindow] = []

    def make() -> "FigureProjectWindow":
        window = create_figure_project_window()
        opened.append(window)
        window.show()
        return window

    yield make
    for window in opened:
        if not window.resources_closed:
            window.close()
            qtbot.waitUntil(lambda window=window: window.resources_closed, timeout=20000)


def setup(qtbot: QtBot, root: Path, window: "FigureProjectWindow") -> None:
    paths: list[str] = []
    profile = np.array([0, 0, 0, 1000, 2000, 1000, 0, 0, 0, 0], dtype=np.uint16)
    for i in range(2):
        pixels = np.full((20, 30), 60000, dtype=np.uint16)
        for lane, scale in enumerate((1, 2, 0)):
            pixels[5:15, lane * 10 : (lane + 1) * 10] -= (profile * (i + 1) * scale)[:, None]
        path = root / f"original{i}.tiff"
        tifffile.imwrite(path, pixels)
        paths.append(str(path))
    window.open_workspace(str(root / "workspace"), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.import_images(tuple(paths))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    view = window.view
    view.numbers["crop_height"].setValue(10)
    for row in range(2):
        for col, text in {
            2: "AKT",
            3: "3",
            4: "0",
            5: "5",
            6: "30",
            7: "15",
            8: "2" if row == 0 else "",
        }.items():
            item(view.table, row, col).setText(text)
        item(view.table, row, 9).setCheckState(Qt.CheckState.Checked)
        view.table.selectRow(row)
        qtbot.waitUntil(window.import_button.isEnabled)
        view.configure_analysis()
        assert view.analysis.plan is not None, view.status.text()
        for lane in range(3):
            item(view.analysis.lanes, lane, 2).setText("2")
            item(view.analysis.lanes, lane, 3).setText("6")
    assert isinstance(view.project(), WBAnalysisProject)


def test_multi_source_compute_reopen_edit_and_recompute(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    table = window.view.analysis.results
    assert table.rowCount() == 6, window.view.status.text()
    assert [item(table, i, 3).text() for i in range(6)] == ["4000", "", "0", "8000", "16000", "0"]
    saved = window.view.project()
    assert isinstance(saved, WBAnalysisProject)
    assert all(p.run and p.run.state == "succeeded" and p.run.pid for p in saved.analyses)
    assert len({p.run.run_id for p in saved.analyses if p.run}) == 2
    window.view.table.selectRow(0)
    qtbot.waitUntil(window.import_button.isEnabled)
    assert len(window.view.analysis.plot.values) == 10
    capture = os.environ.get("BIOIMAGE_MEASUREMENT_CAPTURE")
    if capture:
        tabs = window.view.findChild(QTabWidget)
        assert tabs is not None
        tabs.setCurrentWidget(window.view.analysis)
        assert window.grab().save(capture)
    # Metadata has no numerical effect; it must not revoke geometrical review.
    item(window.view.table, 0, 2).setText("p-AKT")
    assert item(window.view.table, 0, 9).checkState() == Qt.CheckState.Checked
    window.refresh_project_table()
    qtbot.waitUntil(window.import_button.isEnabled)
    assert item(table, 0, 3).text() == "4000"
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    reopened = windows()
    reopened.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(saved.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=20000)
    assert [item(reopened.view.analysis.results, i, 3).text() for i in range(6)] == [
        "4000",
        "",
        "0",
        "8000",
        "16000",
        "0",
    ]
    reopened.view.table.selectRow(0)
    qtbot.waitUntil(reopened.import_button.isEnabled)
    item(reopened.view.analysis.lanes, 0, 4).setText("6035")
    item(reopened.view.analysis.lanes, 0, 5).setText("6035")
    reopened.refresh_project_table()
    qtbot.waitUntil(reopened.import_button.isEnabled)
    assert item(reopened.view.analysis.results, 0, 3).text() == ""
    changed = reopened.view.project()
    assert isinstance(changed, WBAnalysisProject)
    assert next(p for p in changed.analyses if p.row_id == changed.rows[0].row_id).run is None
    assert reopened.view.analysis.plan is not None
    assert reopened.view.analysis.plan.request.lanes[0].bands[0].baseline is not None
    assert reopened.view.analysis.plan.request.lanes[0].bands[0].baseline.left_value == 6035
    reopened.analyze_project()
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=20000)
    assert item(reopened.view.analysis.results, 0, 3).text() == "2500"
    assert item(reopened.view.analysis.results, 3, 3).text() == "8000"
    output = tmp_path / "project-results.xlsx"
    reopened.export_project_table(str(output))
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=10000)
    assert output.exists(), reopened.view.status.text()
    with ZipFile(output) as archive:
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        assert [float(v.text or "nan") for v in sheet.findall(".//s:v", ns)] == [
            2500,
            0,
            8000,
            16000,
            0,
        ]


def test_close_cancels_batch_preserves_completed_run(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    second_id = window.view.project().rows[1].row_id

    def close_after_first(message: str) -> None:
        if second_id in message:
            window.close()

    window.measurement_progress.connect(close_after_first)
    window.analyze_project(True)
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    project = window.view.project()
    assert isinstance(project, WBAnalysisProject)
    assert project.analyses[0].run and project.analyses[0].run.state == "succeeded"
    assert project.analyses[1].run and project.analyses[1].run.state == "cancelled"
    reopened = windows()
    reopened.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(project.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=15000)
    table = reopened.view.analysis.results
    assert item(table, 0, 3).text() == "4000"
    assert item(table, 3, 3).text() == "" and item(table, 3, 4).text() == "cancelled"


@pytest.mark.parametrize("fault", ["damaged", "foreign_run"])
def test_result_damage_isolated_and_stale_geometry_does_not_fill(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"], fault: str
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    project = window.view.project()
    assert isinstance(project, WBAnalysisProject)
    run = project.analyses[0].run
    assert run and run.result
    if fault == "foreign_run":
        plans = (
            project.analyses[0].model_copy(
                update={"run": run.model_copy(update={"run_id": "foreign"})}
            ),
            *project.analyses[1:],
        )
        window.view.set_project(project.model_copy(update={"analyses": plans}))
        window.save()
        qtbot.waitUntil(window.import_button.isEnabled)
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=10000)
    # Fault injection only in this test's disposable workspace, never the user's material.
    if fault == "damaged":
        (tmp_path / "workspace" / run.result.relative_path).write_bytes(b"{}")
    reopened = windows()
    reopened.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(project.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=15000)
    table = reopened.view.analysis.results
    assert item(table, 0, 3).text() == ""
    assert item(table, 0, 4).text() == "result_unavailable"
    assert item(table, 3, 3).text() == "8000"
    item(reopened.view.table, 1, 4).setText("1")
    item(reopened.view.table, 1, 9).setCheckState(Qt.CheckState.Checked)
    reopened.refresh_project_table()
    qtbot.waitUntil(reopened.import_button.isEnabled)
    assert item(table, 3, 3).text() == "" and item(table, 3, 4).text() == "stale"
    # Removing a row removes its plan without dropping other plans or schema v3.
    reopened.view.table.selectRow(1)
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.view.remove_row()
    remaining = reopened.view.project()
    assert isinstance(remaining, WBAnalysisProject) and len(remaining.analyses) == 1


def test_late_batch_cannot_replace_edited_draft(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    second_id = window.view.project().rows[1].row_id

    def edited(message: str) -> None:
        if second_id in message:
            item(window.view.table, 0, 2).setText("edited while running")

    window.measurement_progress.connect(edited)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    project = window.view.project()
    assert isinstance(project, WBAnalysisProject)
    assert project.rows[0].protein == "edited while running"
    assert all(p.run is None for p in project.analyses)
    assert "未覆盖" in window.view.status.text()
    assert window.view.analysis.results.rowCount() == 0
