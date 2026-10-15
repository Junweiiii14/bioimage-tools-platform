"""Result navigation and output readiness; no calculation or file operations."""

from collections import Counter
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_analysis import ProjectTableCell
from wb_tool.ui.project_results import STATUS_LABELS, ProjectResultsView


class ResultWorkspace(QWidget):
    export_requested = Signal()
    section_requested = Signal(str)
    format_requested = Signal(str)
    open_output_requested = Signal()

    def __init__(self, results: QWidget) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        navigation = QWidget()
        navigation.setFixedWidth(136)
        left = QVBoxLayout(navigation)
        left.setContentsMargins(0, 8, 0, 0)
        left.setSpacing(8)
        left.addWidget(QLabel("结果内容"))
        self.navigation: dict[str, QPushButton] = {}
        for title, section in (
            ("测量结果", "analysis"),
            ("OCR 关联", "ocr"),
            ("归一化", "normalization"),
        ):
            button = QPushButton(title)
            button.setCheckable(True)
            button.setChecked(section == "analysis")
            button.clicked.connect(lambda _checked=False, key=section: self._navigate(key))
            self.navigation[section] = button
            left.addWidget(button)
        left.addStretch()
        layout.addWidget(navigation)
        layout.addWidget(results, 1)
        self.summary_panel = QWidget()
        self.summary_panel.setFixedWidth(260)
        right = QVBoxLayout(self.summary_panel)
        right.setContentsMargins(12, 8, 0, 0)
        right.setSpacing(14)
        title = QLabel("输出结果")
        title.setObjectName("sectionTitle")
        right.addWidget(title)
        self.source_count = QLabel("尚未载入项目")
        self.source_count.setWordWrap(True)
        right.addWidget(self.source_count)
        self.state_summary = QLabel("尚未载入测量结果")
        self.state_summary.setWordWrap(True)
        right.addWidget(self.state_summary)
        self.readiness = QLabel("导出前请核对结果状态。")
        self.readiness.setWordWrap(True)
        right.addWidget(self.readiness)
        self.selected_title = QLabel("选择泳道，查看详情")
        self.selected_title.setWordWrap(True)
        right.addWidget(self.selected_title)
        self.selected_reason = QPlainTextEdit()
        self.selected_reason.setReadOnly(True)
        self.selected_reason.setMaximumHeight(120)
        self.selected_reason.setAccessibleName("所选泳道的完整状态原因")
        self.selected_reason.hide()
        right.addWidget(self.selected_reason)
        self.export_button = QPushButton("导出结果包")
        self.export_button.setObjectName("primaryAction")
        self.export_button.clicked.connect(self.export_requested)
        self.export_button.setEnabled(False)
        right.addWidget(self.export_button)
        self.formats_toggle = QPushButton("单独导出格式")
        self.formats_toggle.setCheckable(True)
        right.addWidget(self.formats_toggle)
        self.formats = QWidget()
        formats = QVBoxLayout(self.formats)
        formats.setContentsMargins(0, 0, 0, 0)
        formats.setSpacing(6)
        for text, key in (
            ("测量表 XLSX", "xlsx"),
            ("测量表 CSV", "csv"),
            ("拼图 PNG", "png"),
            ("拼图 TIFF", "tiff"),
            ("可恢复项目 ZIP", "archive"),
        ):
            button = QPushButton(text)
            button.clicked.connect(
                lambda _checked=False, value=key: self.format_requested.emit(value)
            )
            formats.addWidget(button)
        right.addWidget(self.formats)
        self.formats.hide()
        self.formats_toggle.toggled.connect(self.formats.setVisible)
        right.addStretch()
        right.addWidget(QLabel("最近输出"))
        self.output_location = QLabel("尚未导出")
        self.output_location.setWordWrap(True)
        right.addWidget(self.output_location)
        self.open_output_button = QPushButton("打开结果文件夹")
        self.open_output_button.clicked.connect(self.open_output_requested)
        self.open_output_button.setEnabled(False)
        right.addWidget(self.open_output_button)
        layout.addWidget(self.summary_panel)
        if isinstance(results, ProjectResultsView):
            results.selection_changed.connect(self.set_selected_cell)

    def set_selected_cell(self, cell: ProjectTableCell | None) -> None:
        if cell is None:
            self.selected_title.setText("选择泳道，查看详情")
            self.selected_reason.clear()
            self.selected_reason.hide()
            return
        protein = "未指定" if cell.protein in ("", "Unassigned") else cell.protein
        self.selected_title.setText(f"{cell.figure} · {protein} · 泳道 {cell.lane_index}")
        self.selected_reason.setPlainText(
            f"{STATUS_LABELS[cell.status]}\n{cell.reason or '未报告额外原因'}"
        )
        self.selected_reason.show()

    def _navigate(self, section: str) -> None:
        for key, button in self.navigation.items():
            button.setChecked(key == section)
        self.section_requested.emit(section)

    def set_summary(
        self,
        project: WBFigureProject,
        cells: tuple[ProjectTableCell, ...],
        output_path: str = "",
    ) -> None:
        sources = {row.source.sha256 for row in project.rows if row.source is not None}
        unlocated = sum(row.source is not None and row.roi is None for row in project.rows)
        self.source_count.setText(
            f"{len(sources)} 张原图 · {len(project.rows)} 个图像行"
            + (f"\n其中 {unlocated} 个图像行待定位" if unlocated else "")
        )
        counts = Counter(cell.status for cell in cells)
        valid = sum(cell.status == "valid" and cell.value is not None for cell in cells)
        review = sum(counts[key] for key in ("pending_review", "quality_review", "unconfirmed"))
        excluded = counts["excluded"]
        incomplete = len(cells) - valid - review - excluded
        self.state_summary.setText(
            f"结果项 {len(cells)}（含待定位占位）\n"
            f"有效 {valid} · 待复核 {review}\n已排除 {excluded} · 未完成 {incomplete}"
            if cells
            else "尚未载入测量结果"
        )
        represented = {cell.row_id for cell in cells}
        unknown = sum(row.row_id not in represented for row in project.rows)
        if unknown or review or incomplete or not cells:
            message = "当前为待复核结果。缺失和无效值保持空白，原始积分不等于有效信号。"
            if unknown:
                message += f"\n另有 {unknown} 个图像行尚无已载入结果。"
        else:
            message = "已载入结果可查看与导出；已排除项不参与有效信号。"
        self.readiness.setText(message)
        self.export_button.setEnabled(bool(project.rows))
        self.formats_toggle.setEnabled(bool(project.rows))
        self.formats.setEnabled(bool(project.rows))
        self.output_location.setText(Path(output_path).name if output_path else "尚未导出")
        self.output_location.setToolTip(output_path)
        self.open_output_button.setEnabled(bool(output_path))
