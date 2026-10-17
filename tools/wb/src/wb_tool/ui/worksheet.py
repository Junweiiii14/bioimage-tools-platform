"""Editable Fig/row names and explicit cell-to-measurement links; numeric cells are read-only."""

from dataclasses import replace
from uuid import uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.analysis import AnalysisResult
from wb_tool.application.worksheet import fill_worksheet, propose_worksheet
from wb_tool.domain.worksheet import (
    MeasurementBinding,
    OCRRecognition,
    Worksheet,
    WorksheetColumn,
    WorksheetRow,
    suggest_figures,
)


class WorksheetPanel(QWidget):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._worksheet: Worksheet | None = None
        self._recognition: OCRRecognition | None = None
        self._result: AnalysisResult | None = None
        self._loading = False
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Fig", "行名", "已确认"])
        self.table.itemChanged.connect(self._edited)
        self.table.currentCellChanged.connect(self._selected)
        self.note = QLabel("识别名称后核对，再确认空间关联；也可手工建表。")
        self.note.setWordWrap(True)
        self.column = QComboBox()
        self.lane = QComboBox()
        self.band = QComboBox()
        self.lane.currentIndexChanged.connect(self._lane_selected)
        self.column_name = QLineEdit()
        self.column.currentIndexChanged.connect(self._column_selected)
        rename = QPushButton("修改列名")
        rename.clicked.connect(self._rename_column)
        add_row = QPushButton("添加行")
        add_row.clicked.connect(self._add_row)
        add_column = QPushButton("添加列")
        add_column.clicked.connect(self._add_column)
        remove_row = QPushButton("删除所选行")
        remove_row.clicked.connect(self._remove_row)
        confirm = QPushButton("确认所有名称")
        confirm.clicked.connect(self._confirm)
        bind = QPushButton("关联所选行/列")
        bind.clicked.connect(self._bind)
        unbind = QPushButton("解除关联")
        unbind.clicked.connect(self._unbind)
        actions = QHBoxLayout()
        for widget in (add_row, add_column, remove_row, confirm):
            actions.addWidget(widget)
        links = QHBoxLayout()
        for widget in (QLabel("结果列"), self.column, self.column_name, rename):
            links.addWidget(widget)
        measurements = QHBoxLayout()
        for widget in (QLabel("原图泳道"), self.lane, QLabel("条带"), self.band, bind, unbind):
            measurements.addWidget(widget)
        layout = QVBoxLayout(self)
        layout.addWidget(self.note)
        layout.addWidget(self.table)
        layout.addLayout(actions)
        layout.addLayout(links)
        layout.addLayout(measurements)

    def state(self) -> Worksheet | None:
        worksheet = self._worksheet
        if worksheet is None:
            return None
        rows: list[WorksheetRow] = []
        for index, row in enumerate(worksheet.rows):
            figure, name, confirmed = (self.table.item(index, column) for column in range(3))
            if figure is None or name is None or confirmed is None:
                raise ValueError("工作表缺少行数据")
            rows.append(
                replace(
                    row,
                    figure_name=figure.text(),
                    row_name=name.text(),
                    confirmed=confirmed.checkState() == Qt.CheckState.Checked,
                )
            )
        return replace(worksheet, rows=tuple(rows))

    def reset(self, source_sha256: str) -> None:
        self._worksheet = Worksheet(source_sha256, (), ())
        self._recognition = None
        self._result = None
        self._render()

    def restore(self, worksheet: Worksheet | None, recognition: OCRRecognition | None) -> None:
        self._worksheet = worksheet
        self._recognition = recognition
        self._result = None
        self._render()

    def set_recognition(self, recognition: OCRRecognition, source_sha256: str) -> None:
        self._recognition = recognition
        if self._result is not None and recognition.source_sha256 == source_sha256:
            self._worksheet = propose_worksheet(recognition, self._result)
        else:
            rows = tuple(
                WorksheetRow(
                    token.token_id, figure.figure_id, figure.heading.text, token.text, False
                )
                for figure in suggest_figures(recognition)
                for token in figure.rows
            )
            self._worksheet = Worksheet(source_sha256, rows, ())
        self._render()
        self.changed.emit()

    def set_result(self, result: AnalysisResult) -> None:
        previous = self._worksheet
        self._result = result
        if (
            self._worksheet is None
            and self._recognition is not None
            and self._recognition.source_sha256 == result.request.source_sha256
        ):
            self._worksheet = propose_worksheet(self._recognition, result)
        elif (
            self._worksheet is not None
            and not self._worksheet.bindings
            and not self._worksheet.columns
            and self._recognition is not None
            and self._recognition.source_sha256 == result.request.source_sha256
        ):
            suggested = propose_worksheet(self._recognition, result)
            old_rows = tuple(replace(row, confirmed=False) for row in self._worksheet.rows)
            identities = {row.row_id: row.figure_id for row in old_rows}
            self._worksheet = replace(
                suggested,
                rows=old_rows,
                bindings=tuple(
                    binding
                    for binding in suggested.bindings
                    if identities.get(binding.row_id) == binding.figure_id
                ),
            )
        self._loading = True
        self.lane.clear()
        self.lane.addItems([lane.roi.lane_id for lane in result.lanes])
        self._loading = False
        self._lane_selected()
        self._render()
        if self._worksheet != previous:
            self.changed.emit()

    def invalidate_result(self) -> None:
        self._result = None
        self.lane.clear()
        self.band.clear()
        self._render_values()

    def _edited(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        if item.column() in (0, 1) and self._worksheet is not None:
            self._loading = True
            edited_row = self._worksheet.rows[item.row()]
            for index, row in enumerate(self._worksheet.rows):
                if index == item.row() or (
                    item.column() == 0 and row.figure_id == edited_row.figure_id
                ):
                    if item.column() == 0:
                        figure = self.table.item(index, 0)
                        if figure is not None:
                            figure.setText(item.text())
                    check = self.table.item(index, 2)
                    if check is not None:
                        check.setCheckState(Qt.CheckState.Unchecked)
            self._loading = False
        try:
            self._worksheet = self.state()
        except ValueError as error:
            self.note.setText(str(error))
            if item.column() == 2:
                self._loading = True
                item.setCheckState(Qt.CheckState.Unchecked)
                self._loading = False
                self._worksheet = self.state()
                self._render_values()
            self.changed.emit()
            return
        self._render_values()
        self.changed.emit()

    def _render(self) -> None:
        selected_row, selected_cell = self.table.currentRow(), self.table.currentColumn()
        selected_column = self.column.currentIndex()
        self._loading = True
        worksheet = self._worksheet
        self.column.clear()
        if worksheet is None:
            self.table.setRowCount(0)
            self._loading = False
            return
        if len(worksheet.rows) * max(1, len(worksheet.columns)) > 20000:
            raise ValueError("工作表超出界面预算，请分拆 Fig")
        self.column.addItems([column.name for column in worksheet.columns])
        self.table.setColumnCount(3 + len(worksheet.columns))
        self.table.setHorizontalHeaderLabels(
            ["Fig", "行名", "已确认", *(column.name for column in worksheet.columns)]
        )
        self.table.setRowCount(len(worksheet.rows))
        for ri, row in enumerate(worksheet.rows):
            for ci, text in enumerate((row.figure_name, row.row_name)):
                self.table.setItem(ri, ci, QTableWidgetItem(text))
            check = QTableWidgetItem()
            check.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            check.setCheckState(Qt.CheckState.Checked if row.confirmed else Qt.CheckState.Unchecked)
            self.table.setItem(ri, 2, check)
        self._loading = False
        if 0 <= selected_row < self.table.rowCount():
            self.table.setCurrentCell(
                selected_row, min(max(selected_cell, 0), self.table.columnCount() - 1)
            )
        if 0 <= selected_column < self.column.count():
            self.column.setCurrentIndex(selected_column)
        self._column_selected()
        self._render_values()
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, max(240, self.table.columnWidth(1)))

    def _render_values(self) -> None:
        worksheet = self._worksheet
        if worksheet is None:
            return
        self._loading = True
        cells = (
            {
                (cell.row_id, cell.column_id): cell
                for cell in fill_worksheet(worksheet, self._result)
            }
            if self._result is not None
            else {}
        )
        for ri, row in enumerate(worksheet.rows):
            for ci, column in enumerate(worksheet.columns, 3):
                cell = cells.get((row.row_id, column.column_id))
                item = QTableWidgetItem(
                    f"{cell.value:.6g}" if cell is not None and cell.value is not None else "—"
                )
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setToolTip(
                    (cell.status + ": " + cell.reason) if cell is not None else "需先计算当前标注"
                )
                self.table.setItem(ri, ci, item)
        self._loading = False

    def _selected(self) -> None:
        worksheet = self._worksheet
        ri, ci = self.table.currentRow(), self.table.currentColumn() - 3
        if (
            worksheet is not None
            and 0 <= ri < len(worksheet.rows)
            and 0 <= ci < len(worksheet.columns)
        ):
            self.column.setCurrentIndex(ci)
            row, column = worksheet.rows[ri], worksheet.columns[ci]
            binding = next(
                (
                    binding
                    for binding in worksheet.bindings
                    if binding.row_id == row.row_id and binding.column_id == column.column_id
                ),
                None,
            )
            if binding is not None:
                self.note.setText(
                    f"关联：{binding.lane_id} / {binding.band_id}；OCR 原文仍保留在文档中。"
                )

    def _lane_selected(self) -> None:
        self.band.clear()
        if self._result is None:
            return
        index = self.lane.currentIndex()
        if index >= 0:
            self.band.addItems(
                [band.annotation.band_id for band in self._result.lanes[index].bands]
            )

    def _column_selected(self) -> None:
        self.column_name.setText(self.column.currentText())

    def _confirm(self) -> None:
        try:
            worksheet = self.state()
            if worksheet is not None:
                self._worksheet = replace(
                    worksheet, rows=tuple(replace(row, confirmed=True) for row in worksheet.rows)
                )
                self._render()
                self.changed.emit()
        except ValueError as error:
            self.note.setText(str(error))

    def _add_row(self) -> None:
        worksheet = self.state()
        if worksheet is None:
            return
        row = WorksheetRow(uuid4().hex, uuid4().hex, "未命名 Fig", "未命名行", False)
        self._worksheet = replace(worksheet, rows=(*worksheet.rows, row))
        self._render()
        self.changed.emit()

    def _add_column(self) -> None:
        worksheet = self.state()
        if worksheet is None:
            return
        column = WorksheetColumn(uuid4().hex, f"泳道 {len(worksheet.columns) + 1}")
        self._worksheet = replace(worksheet, columns=(*worksheet.columns, column))
        self._render()
        self.changed.emit()

    def _remove_row(self) -> None:
        worksheet = self.state()
        index = self.table.currentRow()
        if worksheet is None or index < 0:
            return
        row_id = worksheet.rows[index].row_id
        self._worksheet = replace(
            worksheet,
            rows=tuple(row for row in worksheet.rows if row.row_id != row_id),
            bindings=tuple(binding for binding in worksheet.bindings if binding.row_id != row_id),
        )
        self._render()
        self.changed.emit()

    def _rename_column(self) -> None:
        worksheet = self.state()
        index = self.column.currentIndex()
        if worksheet is not None and index >= 0:
            try:
                columns = list(worksheet.columns)
                columns[index] = replace(columns[index], name=self.column_name.text())
                self._worksheet = replace(worksheet, columns=tuple(columns))
                self._render()
                self.changed.emit()
            except ValueError as error:
                self.note.setText(str(error))

    def _bind(self) -> None:
        worksheet = self.state()
        ri, ci = self.table.currentRow(), self.column.currentIndex()
        if (
            worksheet is None
            or ri < 0
            or ci < 0
            or not self.lane.currentText()
            or not self.band.currentText()
        ):
            self.note.setText("请选择表格行、结果列、原图泳道与条带")
            return
        row, column = worksheet.rows[ri], worksheet.columns[ci]
        binding = MeasurementBinding(
            row.figure_id,
            row.row_id,
            column.column_id,
            self.lane.currentText(),
            self.band.currentText(),
        )
        kept = tuple(
            old
            for old in worksheet.bindings
            if (old.row_id, old.column_id) != (binding.row_id, binding.column_id)
        )
        self._worksheet = replace(worksheet, bindings=(*kept, binding))
        self._render_values()
        self.changed.emit()

    def _unbind(self) -> None:
        worksheet = self.state()
        ri, ci = self.table.currentRow(), self.column.currentIndex()
        if worksheet is not None and ri >= 0 and ci >= 0:
            row, column = worksheet.rows[ri], worksheet.columns[ci]
            self._worksheet = replace(
                worksheet,
                bindings=tuple(
                    binding
                    for binding in worksheet.bindings
                    if (binding.row_id, binding.column_id) != (row.row_id, column.column_id)
                ),
            )
            self._render_values()
            self.changed.emit()
