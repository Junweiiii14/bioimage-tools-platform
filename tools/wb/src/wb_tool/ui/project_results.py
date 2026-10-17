"""Bounded read-only result presentation shared by project and OCR association tables."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.project_analysis import ProjectTableCell


class ProjectResultsView(QWidget):
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
        layout.addWidget(self.table)
        paging = QHBoxLayout()
        self.page = QSpinBox()
        self.page.setRange(1, 1)
        self.label = QLabel("0 个泳道结果")
        paging.addWidget(QLabel("结果页（每页 200 个泳道）"))
        paging.addWidget(self.page)
        paging.addWidget(self.label)
        layout.addLayout(paging)
        self.page.valueChanged.connect(self._show_page)

    def invalidate(self) -> None:
        self._cells = ()
        self.table.setRowCount(0)
        self.label.setText("内容改变，正在等待计算或刷新结果表")

    def show_cells(self, cells: tuple[ProjectTableCell, ...]) -> None:
        self._cells = cells
        self.page.setMaximum(max(1, (len(cells) + 199) // 200))
        self.label.setText(f"共 {len(cells)} 个泳道结果")
        self._show_page()

    def _show_page(self, *_args: object) -> None:
        start = (self.page.value() - 1) * 200
        cells = self._cells[start : start + 200]
        self.table.setRowCount(len(cells))
        for i, cell in enumerate(cells):
            for c, value in enumerate(
                (
                    cell.figure,
                    cell.protein,
                    str(cell.lane_index),
                    "" if cell.value is None else format(cell.value, ".12g"),
                    cell.status,
                    cell.reason,
                    f"{cell.source_sha256} / {cell.run_id}",
                    cell.evidence_origin,
                    "" if cell.raw_integral is None else format(cell.raw_integral, ".12g"),
                )
            ):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(
                    f"row={cell.row_id}; lane={cell.lane_id}; revision={cell.request_revision}"
                    + (f"\n来源归档 SHA256：{cell.archive_sha256}" if cell.archive_sha256 else "")
                )
                self.table.setItem(i, c, item)
