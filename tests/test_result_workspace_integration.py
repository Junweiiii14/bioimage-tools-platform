"""Integrated result workspace delegates output and keeps contextual tools reversible."""

from dataclasses import replace

from PySide6.QtTest import QSignalSpy
from pytestqt.qtbot import QtBot
from wb_tool.api import create_figure_project_view

from tools.wb.tests.test_project_metadata import project
from tools.wb.tests.test_result_workspace_ui import cell


def test_result_workspace_uses_verified_cells_and_host_output_signal(qtbot: QtBot) -> None:
    view = create_figure_project_view()
    qtbot.addWidget(view)
    original = project()
    view.set_project(original)
    view.show_section("export")
    pending = replace(cell(), status="quality_review", value=None, reason="需核对曝光")
    view.analysis.result_view.show_cells((pending,))
    assert "待复核 1" in view.result_workspace.state_summary.text()
    assert view.analysis_tabs.currentWidget() is view.analysis
    view.set_output_location("C:/outputs/run-one")
    opened = QSignalSpy(view.output_folder_requested)
    view.result_workspace.open_output_button.click()
    assert opened.count() == 1
    exported = QSignalSpy(view.automatic_export_requested)
    view.result_workspace.export_button.click()
    assert exported.count() == 1
    view.export_disclosure.setChecked(True)
    assert not view.export_options.isHidden()
    view.set_project(original.model_copy(update={"project_id": "different-project"}))
    assert view.result_workspace.output_location.text() == "尚未导出"


def test_contextual_titles_back_navigation_preserve_project(qtbot: QtBot) -> None:
    view = create_figure_project_view()
    qtbot.addWidget(view)
    view.set_project(project())
    before = view.project()
    for section, title, page in (
        ("metadata", "批量填写实验信息", 0),
        ("advanced", "高级原图数据", 0),
        ("ocr", "OCR 识别与写表", 2),
        ("normalization", "样本对应与归一化", 2),
    ):
        view.show_section(section)
        assert view.context_title.text() == title and not view.context_header.isHidden()
        view.context_back.click()
        assert view.pages.currentIndex() == page
        assert view.context_header.isHidden()
        assert view.project() == before
    assert "识别当前项目拼图" in view.ocr.note.text()
