"""Bounded read-only result presentation shared by project and OCR association tables."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.project_analysis import ProjectTableCell

STATUS_LABELS = {
    "unconfirmed": "标签待确认",
    "unbound": "尚未关联",
    "ocr_unavailable": "OCR 证据不可用",
    "valid": "有效",
    "quality_review": "质量待复核",
    "invalid": "无效",
    "excluded": "已排除",
    "not_detected": "未检出",
    "missing_source": "缺少原图",
    "pending_review": "待复核",
    "unconfigured": "尚未配置",
    "stale": "已过期",
    "not_run": "尚未计算",
    "cancelled": "已取消",
    "failed": "失败",
    "interrupted": "已中断",
    "result_unavailable": "结果不可用",
}


class ProjectResultsView(QWidget):
    cells_changed = Signal(object)
    selection_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._cells: tuple[ProjectTableCell, ...] = ()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "Fig",
                "蛋白",
                "泳道",
                "有效信号",
                "状态",
                "原因",
                "原图 / 运行",
                "运行来源",
                "原始积分（待复核）",
            ]
        )
        self.table.setColumnHidden(6, True)
        self.table.setColumnHidden(7, True)
        for column, width in ((0, 65), (1, 95), (2, 55), (3, 100), (4, 100), (5, 200), (8, 140)):
            self.table.setColumnWidth(column, width)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        paging = QHBoxLayout()
        self.page = QSpinBox()
        self.page.setRange(1, 1)
        self.label = QLabel("尚无结果项")
        paging.addWidget(QLabel("结果页（每页 200 项）"))
        paging.addWidget(self.page)
        paging.addWidget(self.label)
        paging.addStretch()
        self.details_toggle = QCheckBox("来源详情")
        self.details_toggle.toggled.connect(self._show_details)
        paging.addWidget(self.details_toggle)
        layout.addLayout(paging)
        self.page.valueChanged.connect(self._show_page)
        self.table.currentCellChanged.connect(self._selection_changed)

    def _selection_changed(self, *_args: object) -> None:
        row = self.table.currentRow()
        index = (self.page.value() - 1) * 200 + row
        self.selection_changed.emit(
            self._cells[index] if row >= 0 and index < len(self._cells) else None
        )

    @property
    def cells(self) -> tuple[ProjectTableCell, ...]:
        return self._cells

    def _show_details(self, shown: bool) -> None:
        self.table.setColumnHidden(6, not shown)
        self.table.setColumnHidden(7, not shown)

    def invalidate(self) -> None:
        self._cells = ()
        self.table.setRowCount(0)
        self.label.setText("内容改变，正在等待计算或刷新结果表")
        self.cells_changed.emit(self._cells)

    def show_cells(self, cells: tuple[ProjectTableCell, ...]) -> None:
        self._cells = cells
        self.page.setMaximum(max(1, (len(cells) + 199) // 200))
        self.label.setText(f"共 {len(cells)} 个结果项")
        self._show_page()
        self.cells_changed.emit(self._cells)

    def _show_page(self, *_args: object) -> None:
        start = (self.page.value() - 1) * 200
        cells = self._cells[start : start + 200]
        self.table.setRowCount(len(cells))
        for i, cell in enumerate(cells):
            for c, value in enumerate(
                (
                    cell.figure,
                    "未指定" if cell.protein in ("", "Unassigned") else cell.protein,
                    str(cell.lane_index),
                    "" if cell.value is None else format(cell.value, ".8g"),
                    STATUS_LABELS[cell.status],
                    cell.reason,
                    f"{cell.source_sha256} / {cell.run_id}",
                    cell.evidence_origin,
                    "" if cell.raw_integral is None else format(cell.raw_integral, ".8g"),
                )
            ):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c == 4:
                    item.setData(Qt.ItemDataRole.UserRole, cell.status)
                if c in (3, 8):
                    item.setData(
                        Qt.ItemDataRole.UserRole, cell.value if c == 3 else cell.raw_integral
                    )
                item.setToolTip(
                    f"{cell.reason}\n状态：{cell.status}\n"
                    f"有效信号：{repr(cell.value) if cell.value is not None else '缺失'}\n"
                    "原始积分："
                    f"{repr(cell.raw_integral) if cell.raw_integral is not None else '缺失'}\n"
                    f"row={cell.row_id}; lane={cell.lane_id}; revision={cell.request_revision}\n"
                    f"原图 SHA256：{cell.source_sha256}\n"
                    f"运行：{cell.run_id}\n来源：{cell.evidence_origin}"
                    + (f"\n来源归档 SHA256：{cell.archive_sha256}" if cell.archive_sha256 else "")
                )
                self.table.setItem(i, c, item)
        self._selection_changed()
