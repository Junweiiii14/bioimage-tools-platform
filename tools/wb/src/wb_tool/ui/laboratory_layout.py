"""Explicit layout editor; source geometry and scientific bindings are edited elsewhere."""

from contextlib import suppress

from PySide6.QtCore import QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.laboratory_layout import (
    FigureColumn,
    FigureComposition,
    FigureLayoutStyle,
    FigureSlice,
    WBLayoutProject,
)


class LaboratoryLayoutPanel(QWidget):
    changed = Signal()
    rebuild_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.active = False
        self._loading = False
        self._rows: dict[str, FigureRow] = {}
        self._style = FigureLayoutStyle()
        self._original_slices: tuple[FigureSlice, ...] = ()
        root = QVBoxLayout(self)
        self.rebuild = QPushButton("根据原图更新排版")
        self.rebuild.clicked.connect(self.rebuild_requested)
        root.addWidget(self.rebuild)
        note = QLabel("在中央查看拼图，在这里调整所选来源的排列。分段不会改变原图或定量。")
        note.setWordWrap(True)
        root.addWidget(note)
        self.editor = QWidget()
        content = QVBoxLayout(self.editor)
        form = QFormLayout()
        self.heading = QSpinBox()
        self.heading.setRange(8, 128)
        self.gap = QSpinBox()
        self.gap.setRange(2, 500)
        self.flow = QComboBox()
        self.flow.addItems(["各列独立纵向排列", "按Fig顺序逐排排列"])
        self.alignment = QComboBox()
        self.alignment.addItems(["标签右对齐", "标签左对齐"])
        for text, widget in (
            ("Fig字号", self.heading),
            ("段间白色间隔", self.gap),
            ("排布方式", self.flow),
            ("标签对齐", self.alignment),
        ):
            form.addRow(text, widget)
        content.addLayout(form)
        self.segment = QComboBox()
        self.segment.setMinimumContentsLength(14)
        self.segment.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        content.addWidget(QLabel("当前来源与片段"))
        content.addWidget(self.segment)
        self.selection_note = QLabel("选择片段以调整排列。")
        self.selection_note.setWordWrap(True)
        content.addWidget(self.selection_note)
        selected_form = QFormLayout()
        self.segment_fields: dict[int, QSpinBox] = {}
        for column, title in ((2, "显示行"), (3, "段序"), (6, "Fig 列")):
            field = QSpinBox()
            field.setRange(1, 10000)
            field.valueChanged.connect(lambda value=0, c=column: self._set_segment_field(c, value))
            self.segment_fields[column] = field
            selected_form.addRow(title, field)
        content.addLayout(selected_form)
        self.advanced_toggle = QPushButton("完整分段表")
        self.advanced_toggle.setCheckable(True)
        content.addWidget(self.advanced_toggle)
        self.advanced = QWidget()
        advanced_layout = QVBoxLayout(self.advanced)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["原图行", "Fig", "显示行", "段序", "起始", "结束", "Fig列"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(48)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 76)
        self.table.setMinimumWidth(0)
        self.table.setMaximumHeight(230)
        for column, description in (
            (4, "起始泳道（原图序号，含本泳道）"),
            (5, "结束泳道（原图序号，含本泳道）"),
        ):
            heading = self.table.horizontalHeaderItem(column)
            if heading is not None:
                heading.setToolTip(description)
        advanced_layout.addWidget(self.table, 1)
        column_hint = QLabel("在表内编辑显示行、段序和起止泳道；悬停原图行可查看完整文件名。")
        column_hint.setWordWrap(True)
        advanced_layout.addWidget(column_hint)
        content.addWidget(self.advanced)
        self.advanced.hide()
        self.advanced_toggle.toggled.connect(self.advanced.setVisible)
        split = QHBoxLayout()
        self.cut = QSpinBox()
        self.cut.setRange(1, 95)
        split.addWidget(QLabel("在原泳道"))
        split.addWidget(self.cut)
        self.split_button = QPushButton("之后拆分")
        self.split_button.clicked.connect(self.split_selected)
        split.addWidget(self.split_button)
        content.addLayout(split)
        content.addStretch()
        root.addWidget(self.editor, 1)
        self.status = QLabel("尚未启用；现有项目继续使用原版式。")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.heading.valueChanged.connect(self._edited)
        self.gap.valueChanged.connect(self._edited)
        self.flow.currentIndexChanged.connect(self._edited)
        self.alignment.currentIndexChanged.connect(self._edited)
        self.table.itemChanged.connect(self._edited)
        self.segment.currentIndexChanged.connect(self._select_segment)
        self.table.currentCellChanged.connect(self._table_selected)
        self.restore(WBFigureProject(project_id="empty"))

    def _select_segment(self, index: int) -> None:
        if self._loading or not 0 <= index < self.table.rowCount():
            return
        # The compact selector names one segment even while a modifier is held.
        self.table.setCurrentCell(
            index,
            0,
            QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QItemSelectionModel.SelectionFlag.Rows,
        )
        self._show_segment(index)

    def _table_selected(self, row: int, *_args: object) -> None:
        if self._loading or not 0 <= row < self.table.rowCount():
            return
        self.segment.blockSignals(True)
        self.segment.setCurrentIndex(row)
        self.segment.blockSignals(False)
        self._show_segment(row)

    def _show_segment(self, row: int) -> None:
        loading, self._loading = self._loading, True
        for column, field in self.segment_fields.items():
            item = self.table.item(row, column)
            if item is not None:
                # Invalid advanced text remains visible for correction.
                with suppress(ValueError):
                    field.setValue(int(item.text()))
        first, last, source = (self.table.item(row, c) for c in (4, 5, 0))
        if first is not None and last is not None and source is not None:
            self.selection_note.setText(f"{source.text()} · 泳道 {first.text()}–{last.text()}")
            self.selection_note.setToolTip(source.toolTip())
        self._loading = loading

    def _set_segment_field(self, column: int, value: int) -> None:
        if self._loading:
            return
        item = self.table.item(self.segment.currentIndex(), column)
        if item is not None:
            item.setText(str(value))

    def _edited(self) -> None:
        if not self._loading:
            if self.table.currentRow() >= 0:
                self._show_segment(self.table.currentRow())
            self.changed.emit()

    def layout_style(self) -> FigureLayoutStyle:
        return self._style.model_copy(
            update={
                "heading_size": self.heading.value(),
                "segment_gap": self.gap.value(),
                "flow": "columns" if self.flow.currentIndex() == 0 else "rows",
                "label_alignment": "right" if self.alignment.currentIndex() == 0 else "left",
            }
        )

    def composition(self) -> FigureComposition:
        parts: list[FigureSlice] = []
        columns: dict[str, int] = {}
        for index in range(self.table.rowCount()):
            items = [self.table.item(index, column) for column in range(7)]
            if any(item is None for item in items):
                raise ValueError("版式表有缺失字段")
            source = items[0]
            assert source is not None
            identity: object = source.data(Qt.ItemDataRole.UserRole)
            if not isinstance(identity, str):
                raise ValueError("版式来源行身份无效")
            values = [item.text().strip() for item in items if item is not None]
            column = int(values[6])
            if values[1] in columns and columns[values[1]] != column:
                raise ValueError("同一Fig的列号不一致")
            columns[values[1]] = column
            part = FigureSlice(
                row_id=identity,
                figure=values[1],
                line=int(values[2]),
                position=int(values[3]),
                first_lane=int(values[4]),
                last_lane=int(values[5]),
            )
            original = next(
                (
                    s
                    for s in self._original_slices
                    if (s.row_id, s.figure, s.line, s.position, s.first_lane, s.last_lane)
                    == (
                        part.row_id,
                        part.figure,
                        part.line,
                        part.position,
                        part.first_lane,
                        part.last_lane,
                    )
                ),
                None,
            )
            if original is not None:
                part = part.model_copy(update={"display_frame": original.display_frame})
            parts.append(part)
        return FigureComposition(
            slices=tuple(parts),
            columns=tuple(
                FigureColumn(figure=name, column=column) for name, column in columns.items()
            ),
        )

    def restore(self, project: WBFigureProject) -> None:
        self._loading = True
        self.active = isinstance(project, WBLayoutProject)
        self.editor.setEnabled(self.active)
        self._rows = {row.row_id: row for row in project.rows}
        style = (
            project.layout_style if isinstance(project, WBLayoutProject) else FigureLayoutStyle()
        )
        composition = (
            project.composition if isinstance(project, WBLayoutProject) else FigureComposition()
        )
        self._style = style
        self.heading.setValue(style.heading_size)
        self.gap.setValue(style.segment_gap)
        self.flow.setCurrentIndex(0 if style.flow == "columns" else 1)
        self.alignment.setCurrentIndex(0 if style.label_alignment == "right" else 1)
        self._fill(composition)
        self.status.setText(
            f"{len(composition.slices)} 个片段 · 选择来源调整排列。"
            if self.active
            else "当前使用原版式。更新排版后可调整片段与显示顺序。"
        )
        self._loading = False
        if self.table.rowCount():
            self._select_segment(max(0, self.segment.currentIndex()))

    def _fill(self, composition: FigureComposition) -> None:
        self._original_slices = composition.slices
        selected = self.segment.currentIndex()
        self.segment.clear()
        columns = {entry.figure: entry.column for entry in composition.columns}
        self.table.setRowCount(len(composition.slices))
        for index, part in enumerate(composition.slices):
            row = self._rows.get(part.row_id)
            number = next((i for i, key in enumerate(self._rows, 1) if key == part.row_id), 0)
            values = [
                f"{number:03d} · {row.protein}" if row else "来源行已删除",
                part.figure,
                str(part.line),
                str(part.position),
                str(part.first_lane),
                str(part.last_lane),
                str(columns.get(part.figure, 1)),
            ]
            self.segment.addItem(
                f"{values[0]} · {part.figure} · 泳道 {part.first_lane}–{part.last_lane}"
            )
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                if column < 2:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, part.row_id)
                    item.setToolTip(
                        f"{row.protein} · {row.filename}\n来源行：{part.row_id}" if row else text
                    )
                self.table.setItem(index, column, item)

        if self.segment.count():
            self.segment.setCurrentIndex(min(max(0, selected), self.segment.count() - 1))

    def split_selected(self) -> None:
        try:
            composition = self.composition()
            selected = sorted(
                {index.row() for index in self.table.selectionModel().selectedRows()}, reverse=True
            )
            if not selected:
                raise ValueError("请选择要分段的原图行")
            cut = self.cut.value()
            parts = list(composition.slices)
            if any(
                not parts[index].first_lane <= cut < parts[index].last_lane for index in selected
            ):
                raise ValueError("分段点须在所选各段的原泳道范围内，且两侧至少一个泳道")
            for index in selected:
                original = parts[index]
                parts = [
                    part.model_copy(update={"position": part.position + 1})
                    if (part.figure, part.line) == (original.figure, original.line)
                    and part.position > original.position
                    else part
                    for part in parts
                ]
                parts[index : index + 1] = [
                    original.model_copy(update={"last_lane": cut, "display_frame": None}),
                    original.model_copy(
                        update={
                            "first_lane": cut + 1,
                            "position": original.position + 1,
                            "display_frame": None,
                        }
                    ),
                ]
            self._loading = True
            self._fill(composition.model_copy(update={"slices": tuple(parts)}))
            self.status.setText("已分段；其他蛋白行须配置对应段列，然后生成预览核对。")
            self.changed.emit()
        except ValueError as error:
            self.status.setText(str(error))
        finally:
            self._loading = False
            if self.table.rowCount():
                self._select_segment(max(0, self.segment.currentIndex()))
