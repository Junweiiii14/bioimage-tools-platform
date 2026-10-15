"""Explicit Qt segments preserve real quantitative/OCR evidence across saves and restoration."""

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import tifffile
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QTabWidget
from pytestqt.qtbot import QtBot
from wb_tool.api import WBLayoutProject, analysis_is_current

from tests.test_project_measurements import configure_normalization, item, setup
from tests.test_project_measurements import windows as windows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def test_segmented_full_image_real_ocr_results_reopen_and_template_reuse(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window, width_multiplier=80, crop_height=70)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    configure_normalization(window)
    qtbot.waitUntil(lambda: window.view.normalization.results.rowCount() == 3)
    for name, value in (("font_size", 42), ("row_gap", 55), ("label_width", 180)):
        window.view.numbers[name].setValue(value)
    before = window.view.project()
    panel = window.view.laboratory_layout
    panel.rebuild.click()
    assert isinstance(window.view.project(), WBLayoutProject), window.view.status.text()
    panel.heading.setValue(56)
    panel.cut.setValue(1)
    panel.table.selectAll()
    panel.split_button.click()
    project = window.view.project()
    assert isinstance(project, WBLayoutProject) and len(project.composition.slices) == 4
    assert project.rows == before.rows
    assert all(analysis_is_current(project, plan) for plan in project.analyses)
    qtbot.waitUntil(lambda: item(window.view.normalization.results, 0, 8).text() == "0.5")
    image = tmp_path / "segmented.tif"
    window.export_figure_image(str(image))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=15000)
    assert image.exists(), window.view.status.text()
    with tifffile.TiffFile(image) as file:
        description = getattr(file.pages[0], "description", None)
        assert isinstance(description, str)
        metadata = json.loads(description)
        assert metadata["operation"] == "figure_segmented_geometry@1"
        assert [record["source_lane_range"] for record in metadata["rows"]] == [
            [1, 1],
            [2, 3],
            [1, 1],
            [2, 3],
        ]
    window.import_ocr_image(str(image))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    window.recognize_project()
    qtbot.waitUntil(window.import_button.isEnabled, timeout=30000)
    project = window.view.project()
    assert isinstance(project, WBLayoutProject) and project.ocr and project.ocr.recognition
    assert len(project.ocr.rows) == 2, project.ocr.recognition
    window.view.bind_ocr(project.ocr.rows[0].row_id, project.rows[0].row_id)
    item(window.view.ocr.table, 0, 2).setCheckState(Qt.CheckState.Checked)
    qtbot.waitUntil(lambda: window.view.ocr.results.rowCount() >= 3)
    qtbot.waitUntil(lambda: item(window.view.ocr.results, 0, 3).text() == "4000")
    assert item(window.view.normalization.results, 0, 8).text() == "0.5"
    capture = os.environ.get("BIOIMAGE_LAYOUT_CAPTURE")
    if capture:
        tabs = window.view.findChild(QTabWidget)
        assert tabs
        tabs.setCurrentWidget(panel)
        assert window.grab().save(capture)
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    reopened = windows()
    reopened.open_workspace(str(tmp_path / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(project.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=20000)
    current = reopened.view.project()
    assert isinstance(current, WBLayoutProject) and current.composition == project.composition
    assert item(reopened.view.ocr.results, 0, 3).text() == "4000"
    assert item(reopened.view.normalization.results, 0, 8).text() == "0.5"
    assert reopened.view.history_label.text() == ""
    reopened.new_project()
    qtbot.waitUntil(reopened.import_button.isEnabled)
    fresh = reopened.view.project()
    assert isinstance(fresh, WBLayoutProject) and fresh.layout_style == project.layout_style
    assert fresh.rows == fresh.composition.slices == fresh.analyses == fresh.normalizations == ()
    assert fresh.ocr is None and fresh.archive_sources == ()


def test_variable_roi_height_invalidates_measurement_and_rebuild_recovers_bad_layout(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window, crop_height=30)
    window.view.numbers["font_size"].setValue(8)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    window.view.rebuild_layout()
    project = window.view.project()
    assert isinstance(project, WBLayoutProject)
    old = project.analyses[0]
    item(window.view.table, 0, 7).setText("25")  # original ROI now 20 high, second stays 30
    assert not analysis_is_current(window.view.project(), old)
    item(window.view.table, 0, 9).setCheckState(Qt.CheckState.Checked)
    window.view.table.selectRow(0)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.view.configure_analysis()
    assert window.view.analysis.plan and window.view.analysis.plan.crop.y1 == 25
    for lane in range(3):
        item(window.view.analysis.lanes, lane, 2).setText("2")
        item(window.view.analysis.lanes, lane, 3).setText("6")
    window.analyze_project(False)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    assert item(window.view.analysis.results, 0, 3).text() == "4000"
    assert item(window.view.analysis.results, 3, 3).text() == "8000"
    panel = window.view.laboratory_layout
    item(panel.table, 0, 4).setText("99")
    panel.rebuild.click()  # rebuild bypasses invalid edited layout fields
    assert item(panel.table, 0, 4).text() == "1"
    panel.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    panel.table.selectAll()
    panel.cut.setValue(3)
    panel.split_button.click()
    assert "分段点" in panel.status.text()
    assert panel.table.rowCount() == 2
    image = tmp_path / "heights.png"
    window.export_figure_image(str(image))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=15000)
    assert image.exists(), window.view.status.text()
