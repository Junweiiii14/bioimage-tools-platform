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
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QTabWidget
from pytestqt.qtbot import QtBot
from wb_tool.api import WBAnalysisProject, WBNormalizedProject, WBProjectOCR

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


def test_real_project_ocr_bind_fill_export_reopen_and_cancel(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    original = window.view.project()
    assert isinstance(original, WBAnalysisProject)
    figure = Image.new("L", (1200, 500), 245)
    draw = ImageDraw.Draw(figure)
    font = ImageFont.load_default(size=42)
    for x, title in ((30, "Fig 1A"), (630, "Fig 2B")):
        draw.text((x, 20), title, font=font, fill=0)
        draw.text((x, 150), "AKT", font=font, fill=0)
    source = tmp_path / "composite.tif"
    tifffile.imwrite(source, np.array(figure))
    window.import_ocr_image(str(source))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    window.recognize_project()
    qtbot.waitUntil(window.import_button.isEnabled, timeout=30000)
    project = window.view.project()
    assert isinstance(project, WBProjectOCR), window.view.status.text()
    assert project.ocr is not None
    assert project.ocr.run and project.ocr.run.state == "succeeded", window.view.status.text()
    assert project.ocr.recognition and len(project.ocr.rows) == 2
    assert [r.figure.replace(" ", "") for r in project.ocr.rows] == ["Fig1A", "Fig2B"]
    assert all(r.protein == "AKT" and r.link is None and not r.confirmed for r in project.ocr.rows)
    panel = window.view.ocr
    # Source choices follow review changes without losing editable OCR labels.
    item(panel.table, 0, 1).setText("AKT edited")
    item(window.view.table, 0, 9).setCheckState(Qt.CheckState.Unchecked)
    qtbot.waitUntil(lambda: panel.target.findData(project.rows[0].row_id) == -1)
    assert item(panel.table, 0, 1).text() == "AKT edited"
    item(window.view.table, 0, 9).setCheckState(Qt.CheckState.Checked)
    qtbot.waitUntil(lambda: panel.target.findData(project.rows[0].row_id) > 0)
    item(panel.table, 0, 1).setText("AKT")
    for i in range(2):
        panel.table.setCurrentCell(i, 0)
        panel.target.setCurrentIndex(panel.target.findData(project.rows[i].row_id))
        panel.bind(False)
        item(panel.table, i, 2).setCheckState(Qt.CheckState.Checked)
    qtbot.waitUntil(
        lambda: panel.results.rowCount() == 6 and item(panel.results, 0, 3).text() == "4000",
        timeout=10000,
    )
    assert [item(panel.results, i, 3).text() for i in range(6)] == [
        "4000",
        "",
        "0",
        "8000",
        "16000",
        "0",
    ]
    assert panel.canvas.image_rect().width() > 0
    assert "AKT" in panel.raw.toPlainText()
    configure_normalization(window)
    qtbot.waitUntil(lambda: window.view.normalization.results.rowCount() == 3)
    window.view.normalization.result_view.labels.setCurrentIndex(1)
    assert item(window.view.normalization.results, 0, 0).text() == "Fig 1A"
    assert item(window.view.normalization.results, 0, 8).text() == "0.5"
    normalized = window.view.project()
    assert isinstance(normalized, WBNormalizedProject) and normalized.ocr is not None
    assert normalized.ocr.run == project.ocr.run
    capture = os.environ.get("BIOIMAGE_PROJECT_OCR_CAPTURE")
    if capture:
        tabs = window.view.findChild(QTabWidget)
        assert tabs is not None
        tabs.setCurrentWidget(panel)
        panel.table.setCurrentCell(0, 0)
        assert window.grab().save(capture)
    item(panel.table, 0, 1).setText("=AKT")
    assert item(panel.table, 0, 2).checkState() == Qt.CheckState.Unchecked
    qtbot.waitUntil(
        lambda: panel.results.rowCount() == 6 and item(panel.results, 0, 4).text() == "unconfirmed",
        timeout=10000,
    )
    item(panel.table, 0, 2).setCheckState(Qt.CheckState.Checked)
    qtbot.waitUntil(
        lambda: panel.results.rowCount() == 6 and item(panel.results, 0, 3).text() == "4000",
        timeout=10000,
    )
    assert window.view.project().rows[0].protein == "AKT"
    output = tmp_path / "ocr-results.xlsx"
    window.export_project_table(str(output), ocr=True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    assert output.exists(), window.view.status.text()
    with ZipFile(output) as archive:
        raw = archive.read("xl/worksheets/sheet1.xml")
        assert b"=AKT" in raw and b"<f>" not in raw
        sheet = ElementTree.fromstring(raw)
        ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        assert [float(v.text or "nan") for v in sheet.findall(".//s:v", ns)] == [
            4000,
            0,
            8000,
            16000,
            0,
        ]
        audit = archive.read("xl/worksheets/sheet2.xml").decode()
        assert project.ocr.run.run_id in audit
        assert all(r.row_id in audit for r in original.rows)
    saved = window.view.project()
    assert isinstance(saved, WBProjectOCR)
    window.recognize_project()
    qtbot.waitUntil(lambda: "正在后台识别" in window.view.status.text(), timeout=10000)
    window.cancel()
    qtbot.waitUntil(window.import_button.isEnabled, timeout=15000)
    cancelled = window.view.project()
    assert isinstance(cancelled, WBProjectOCR) and cancelled.ocr == saved.ocr
    assert "之前关联保留" in window.view.status.text()
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=15000)
    reopened = windows()
    reopened.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(project.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=20000)
    restored = reopened.view.project()
    assert (
        isinstance(restored, WBProjectOCR)
        and restored.ocr is not None
        and restored.ocr == saved.ocr
    )
    assert item(reopened.view.ocr.results, 0, 3).text() == "4000"
    assert item(reopened.view.ocr.results, 3, 3).text() == "8000"
    item(reopened.view.table, 0, 4).setText("1")
    item(reopened.view.table, 0, 9).setCheckState(Qt.CheckState.Checked)
    qtbot.waitUntil(
        lambda: (
            reopened.view.ocr.results.rowCount() == 6
            and item(reopened.view.ocr.results, 0, 4).text() == "stale"
        ),
        timeout=10000,
    )
    assert item(reopened.view.ocr.results, 0, 3).text() == ""
    ocr_run = restored.ocr.run
    assert ocr_run and ocr_run.result
    reopened.close()
    qtbot.waitUntil(lambda: reopened.resources_closed, timeout=15000)
    (tmp_path / "workspace" / ocr_run.result.relative_path).write_bytes(b"{}")
    damaged = windows()
    damaged.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(damaged.import_button.isEnabled)
    damaged.load_document(project.project_id)
    qtbot.waitUntil(damaged.import_button.isEnabled, timeout=20000)
    assert item(damaged.view.ocr.results, 3, 4).text() == "ocr_unavailable"
    assert item(damaged.view.ocr.results, 3, 3).text() == ""
    assert item(damaged.view.analysis.results, 3, 3).text() == "8000"


@pytest.mark.parametrize("action", ["close", "edit"])
def test_project_ocr_inflight_close_or_edit_does_not_overwrite(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"], action: str
) -> None:
    window = windows()
    source = tmp_path / "labels.tif"
    figure = Image.new("L", (600, 400), 245)
    draw = ImageDraw.Draw(figure)
    draw.text((30, 20), "Fig 1A", font=ImageFont.load_default(size=42), fill=0)
    draw.text((30, 150), "AKT", font=ImageFont.load_default(size=42), fill=0)
    tifffile.imwrite(source, np.array(figure))
    window.open_workspace(str(tmp_path / "workspace"), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.import_ocr_image(str(source))
    qtbot.waitUntil(window.import_button.isEnabled)
    window.recognize_project()
    qtbot.waitUntil(lambda: "正在后台识别" in window.view.status.text(), timeout=10000)
    if action == "close":
        window.close()
    else:
        window.view.name.setText("edited while OCR runs")
        window.view.name.textEdited.emit("edited while OCR runs")
        qtbot.waitUntil(window.import_button.isEnabled, timeout=30000)
        assert window.view.project().name == "edited while OCR runs"
        window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    project = window.view.project()
    assert isinstance(project, WBProjectOCR) and project.ocr is not None
    assert project.ocr.run is None and not project.ocr.rows


def test_late_ocr_import_preserves_new_edits(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    source = tmp_path / "labels.tif"
    tifffile.imwrite(source, np.full((100, 100), 245, dtype=np.uint8))
    window.open_workspace(str(tmp_path / "workspace"), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.import_ocr_image(str(source))
    window.view.name.setText("new edit during import")
    window.view.name.textEdited.emit("new edit during import")
    qtbot.waitUntil(window.import_button.isEnabled)
    assert window.view.project().name == "new edit during import"
    assert not isinstance(window.view.project(), WBProjectOCR)
    assert "未替换拼图" in window.view.status.text()


def configure_normalization(window: "FigureProjectWindow") -> None:
    project = window.view.project()
    panel = window.view.normalization
    panel.target.setCurrentIndex(panel.target.findData(project.rows[0].row_id))
    panel.reference.setCurrentIndex(panel.reference.findData(project.rows[1].row_id))
    panel.kind.setCurrentIndex(panel.kind.findData("housekeeping"))
    panel.configure()
    assert panel.pairs.rowCount() == 3, window.view.status.text()
    for row, sample, reference in ((0, "control", "1"), (2, "=zero", "2")):
        item(panel.pairs, row, 1).setText(sample)
        item(panel.pairs, row, 2).setText(reference)
    item(panel.pairs, 0, 4).setCheckState(Qt.CheckState.Checked)
    panel.mode.setCurrentIndex(panel.mode.findData("single_control"))
    panel.confirmed.setChecked(True)


def test_project_normalization_ui_mapping_controls_export_reopen_and_stale(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    configure_normalization(window)
    panel = window.view.normalization
    qtbot.waitUntil(
        lambda: panel.results.rowCount() == 3 and item(panel.results, 0, 8).text() == "0.5"
    )
    assert [item(panel.results, i, 10).text() for i in range(3)] == ["1", "", "0"]
    project = window.view.project()
    assert isinstance(project, WBNormalizedProject) and project.ocr is None
    assert project.normalizations[0].confirmed
    assert item(window.view.table, 0, 9).checkState() == Qt.CheckState.Checked
    # Select two explicit controls: zero is a valid ratio, not a missing value.
    item(panel.pairs, 2, 4).setCheckState(Qt.CheckState.Checked)
    assert not panel.confirmed.isChecked()
    panel.confirmed.setChecked(True)
    qtbot.waitUntil(
        lambda: panel.results.rowCount() == 3 and item(panel.results, 0, 10).text() == ""
    )
    assert "一个对照" in item(panel.results, 0, 12).text()
    panel.mode.setCurrentIndex(panel.mode.findData("control_mean"))
    panel.confirmed.setChecked(True)
    qtbot.waitUntil(
        lambda: panel.results.rowCount() == 3 and item(panel.results, 0, 10).text() == "2"
    )
    assert item(panel.results, 0, 9).text() == "0.25"
    # A selected control with a zero denominator invalidates all relative values, not raw ratios.
    item(panel.pairs, 2, 2).setText("3")
    panel.confirmed.setChecked(True)
    qtbot.waitUntil(
        lambda: panel.results.rowCount() == 3 and "未跳过" in item(panel.results, 0, 12).text()
    )
    assert item(panel.results, 0, 8).text() == "0.5"
    assert item(panel.results, 0, 10).text() == ""
    item(panel.pairs, 2, 2).setText("2")
    panel.confirmed.setChecked(True)
    qtbot.waitUntil(
        lambda: panel.results.rowCount() == 3 and item(panel.results, 0, 10).text() == "2"
    )
    capture = os.environ.get("BIOIMAGE_NORMALIZATION_CAPTURE")
    if capture:
        tabs = window.view.findChild(QTabWidget)
        assert tabs is not None
        tabs.setCurrentWidget(panel)
        assert window.grab().save(capture)
    output = tmp_path / "normalized.xlsx"
    window.export_project_table(str(output), normalization=True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    assert output.exists(), window.view.status.text()
    with ZipFile(output) as archive:
        raw = archive.read("xl/worksheets/sheet1.xml")
        assert b"=zero" in raw and b"<f>" not in raw and b"0.25" in raw
        audit = archive.read("xl/worksheets/sheet2.xml").decode()
        assert all(plan.run and plan.run.run_id in audit for plan in project.analyses)
    saved = window.view.project()
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=15000)
    reopened = windows()
    reopened.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(saved.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=20000)
    restored = reopened.view.project()
    assert isinstance(restored, WBNormalizedProject) and restored == saved
    assert [item(reopened.view.normalization.results, i, 10).text() for i in range(3)] == [
        "2",
        "",
        "0",
    ]
    item(reopened.view.table, 1, 4).setText("1")
    item(reopened.view.table, 1, 9).setCheckState(Qt.CheckState.Checked)
    qtbot.waitUntil(
        lambda: (
            reopened.view.normalization.results.rowCount() == 3
            and "过期" in item(reopened.view.normalization.results, 0, 11).text()
        )
    )
    assert all(item(reopened.view.normalization.results, i, 8).text() == "" for i in range(3))
