"""Result summary reflects actual cells, preserving missing values and full precision evidence."""

from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from pytestqt.qtbot import QtBot
from wb_tool.api import ProjectTableCell
from wb_tool.ui.project_results import ProjectResultsView
from wb_tool.ui.result_workspace import ResultWorkspace

from tools.wb.tests.test_project_metadata import project


def cell() -> ProjectTableCell:
    return ProjectTableCell(
        "r0", "Fig1", "Unassigned", 1, "a" * 64, "lane1", "target", 1, "run-1", 0.0, "valid", ""
    )


def test_summary_distinguishes_zero_pending_and_unloaded_rows(qtbot: QtBot) -> None:
    table = ProjectResultsView()
    workspace = ResultWorkspace(table)
    qtbot.addWidget(workspace)
    zero = cell()
    pending = replace(
        zero,
        row_id="r1",
        value=None,
        status="quality_review",
        reason="原始像素达到位深上限，需要核对曝光",
        raw_integral=123.123456789012,
    )
    cells = (zero, pending)
    table.show_cells(cells)
    workspace.set_summary(project(), cells)
    valid_item, missing = table.table.item(0, 3), table.table.item(1, 3)
    assert valid_item is not None and valid_item.text() == "0"
    assert missing is not None and missing.text() == ""
    status = table.table.item(1, 4)
    assert status is not None and status.text() == "质量待复核"
    assert status.data(Qt.ItemDataRole.UserRole) == "quality_review"
    raw = table.table.item(1, 8)
    assert raw is not None and raw.data(Qt.ItemDataRole.UserRole) == pending.raw_integral
    assert repr(pending.raw_integral) in raw.toolTip()
    assert "有效 1 · 待复核 1" in workspace.state_summary.text()
    assert "1 个图像行尚无已载入结果" in workspace.readiness.text()
    assert table.cells == cells
    assert table.table.isColumnHidden(6)
    table.details_toggle.setChecked(True)
    assert not table.table.isColumnHidden(6)
    table.table.setCurrentCell(1, 4)
    assert pending.reason in workspace.selected_reason.toPlainText()
    assert "未指定" in workspace.selected_title.text()
    table.invalidate()
    workspace.set_summary(project(), table.cells)
    assert workspace.state_summary.text() == "尚未载入测量结果"
    assert "有效 0" not in workspace.state_summary.text()


def test_result_export_and_navigation_emit_only_explicit_actions(qtbot: QtBot) -> None:
    workspace = ResultWorkspace(ProjectResultsView())
    qtbot.addWidget(workspace)
    export = QSignalSpy(workspace.export_requested)
    navigation = QSignalSpy(workspace.section_requested)
    workspace.set_summary(project(), (cell(),), "C:/results/WB-20261016")
    assert workspace.output_location.text() == "WB-20261016"
    assert workspace.open_output_button.isEnabled()
    assert export.count() == 0
    workspace.export_button.click()
    assert export.count() == 1
    workspace.navigation["ocr"].click()
    assert navigation.at(0) == ["ocr"]
    assert workspace.formats.isHidden()
