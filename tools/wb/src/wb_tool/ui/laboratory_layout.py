"""Explicit layout editor; source geometry and scientific bindings are edited elsewhere."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
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
        root = QVBoxLayout(self)
        self.rebuild = QPushButton("从当前原图行启用 / 重建版式")
        self.rebuild.clicked.connect(self.rebuild_requested)
        root.addWidget(self.rebuild)
        note = QLabel(
            "按原图行明确配置显示行与段序；相同显示行的蛋白名须一致。\n"
            "分段保留全部泳道及顺序，原ROI高度独立；新增/删除原图或改Fig后可重建。"
        )
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
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["原图行", "Fig", "显示行", "段序", "起始泳道", "结束泳道", "Fig列"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        content.addWidget(self.table, 1)
        split = QHBoxLayout()
        self.cut = QSpinBox()
        self.cut.setRange(1, 95)
        split.addWidget(QLabel("在原泳道"))
        split.addWidget(self.cut)
        self.split_button = QPushButton("之后拆分所选段")
        self.split_button.clicked.connect(self.split_selected)
        split.addWidget(self.split_button)
        content.addLayout(split)
        root.addWidget(self.editor, 1)
        self.status = QLabel("尚未启用；现有项目继续使用原版式。")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.heading.valueChanged.connect(self._edited)
        self.gap.valueChanged.connect(self._edited)
        self.flow.currentIndexChanged.connect(self._edited)
        self.alignment.currentIndexChanged.connect(self._edited)
        self.table.itemChanged.connect(self._edited)
        self.restore(WBFigureProject(project_id="empty"))

    def _edited(self) -> None:
        if not self._loading:
            self.changed.emit()

    def layout_style(self) -> FigureLayoutStyle:
        return FigureLayoutStyle(
            heading_size=self.heading.value(),
            segment_gap=self.gap.value(),
            flow="columns" if self.flow.currentIndex() == 0 else "rows",
            label_alignment="right" if self.alignment.currentIndex() == 0 else "left",
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
            parts.append(
                FigureSlice(
                    row_id=identity,
                    figure=values[1],
                    line=int(values[2]),
                    position=int(values[3]),
                    first_lane=int(values[4]),
                    last_lane=int(values[5]),
                )
            )
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
        self.heading.setValue(style.heading_size)
        self.gap.setValue(style.segment_gap)
        self.flow.setCurrentIndex(0 if style.flow == "columns" else 1)
        self.alignment.setCurrentIndex(0 if style.label_alignment == "right" else 1)
        self._fill(composition)
        self.status.setText(
            "已启用；调整显示行号、段序与Fig列，然后生成预览。"
            if self.active
            else "尚未启用；现有项目继续使用原版式。"
        )
        self._loading = False

    def _fill(self, composition: FigureComposition) -> None:
        columns = {entry.figure: entry.column for entry in composition.columns}
        self.table.setRowCount(len(composition.slices))
        for index, part in enumerate(composition.slices):
            row = self._rows.get(part.row_id)
            values = [
                f"{row.protein} · {row.filename}" if row else "来源行已删除",
                part.figure,
                str(part.line),
                str(part.position),
                str(part.first_lane),
                str(part.last_lane),
                str(columns.get(part.figure, 1)),
            ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                if column < 2:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, part.row_id)
                    item.setToolTip(part.row_id)
                self.table.setItem(index, column, item)
        self.table.setColumnWidth(0, 280)

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
                    original.model_copy(update={"last_lane": cut}),
                    original.model_copy(
                        update={"first_lane": cut + 1, "position": original.position + 1}
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
