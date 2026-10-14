"""Multi-image row review and template editing; host owns assets and asynchronous work."""

from uuid import uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.desktop_data import PreviewRaster
from wb_tool.application.figure_project import (
    FigureRender,
    FigureRow,
    FigureTemplate,
    WBFigureProject,
)
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI
from wb_tool.ui.canvas import ImageCanvas


class FigureProjectView(QWidget):
    changed = Signal()
    source_requested = Signal(str)
    preview_requested = Signal()
    export_requested = Signal()
    font_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.generation = 0
        self._loading = False
        self._project = WBFigureProject(project_id=uuid4().hex)
        root = QVBoxLayout(self)
        self.name = QLineEdit("WB 项目")
        root.addWidget(self.name)
        self.status = QLabel("批量导入原图，填写 Fig/蛋白，框选整行范围并复核。")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        actions = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.addItems(["全部行", "待审核", "已审核", "预标空泳道", "缺图"])
        actions.addWidget(self.filter)
        for text, callback in (
            ("上移行", lambda: self.move_row(-1)),
            ("下移行", lambda: self.move_row(1)),
            ("添加缺图位", self.add_missing),
            ("删除所选行", self.remove_row),
            ("确认所选行", self.confirm_selected),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            actions.addWidget(button)
        root.addLayout(actions)
        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(
            ["原图", "Fig", "蛋白", "N", "x0", "y0", "x1", "y1", "空泳道(逗号)", "已审核", "备注"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setMinimumHeight(180)
        for index in range(3, 8):
            self.table.setColumnWidth(index, 60)
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(9, 65)
        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.table)
        tabs = QTabWidget()
        self.canvas = ImageCanvas()
        tabs.addTab(self.canvas, "原图与固定泳道")
        preview_page = QWidget()
        preview_layout = QVBoxLayout(preview_page)
        preview_layout.addWidget(
            QLabel(
                "拼图显示：RGB 按 BT.601 转灰度；16 位整除 257。"
                "归档另含未改像素的 TIFF 裁剪和原图。"
            )
        )
        self.preview_label = QLabel("修改后点击生成预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_scroll = QScrollArea()
        preview_scroll.setWidget(self.preview_label)
        preview_scroll.setWidgetResizable(True)
        preview_layout.addWidget(preview_scroll)
        tabs.addTab(preview_page, "拼图预览")
        settings = QWidget()
        form = QFormLayout(settings)
        self.figure_order = QLineEdit()
        form.addRow("Fig 顺序（逗号分隔）", self.figure_order)
        self.template_name = QLineEdit()
        form.addRow("模板名（随项目保存）", self.template_name)
        self.numbers: dict[str, QSpinBox] = {}
        for field, title, minimum, maximum in (
            ("crop_height", "统一裁剪高（原图像素）", 2, 4096),
            ("font_size", "标签字号（输出像素）", 8, 96),
            ("label_width", "标签区宽", 30, 1000),
            ("row_gap", "行间距", 2, 500),
            ("figure_gap", "Fig 间距", 2, 1000),
            ("margin", "外边距", 2, 1000),
            ("border", "边框宽", 1, 10),
            ("columns", "每排 Fig 数", 1, 12),
            ("dpi", "导出 DPI（不重采样）", 72, 1200),
        ):
            spin = QSpinBox()
            spin.setRange(minimum, maximum)
            self.numbers[field] = spin
            form.addRow(title, spin)
            spin.valueChanged.connect(self._edited)
        self.right_labels = QCheckBox("标签放在右侧")
        form.addRow(self.right_labels)
        font = QPushButton("导入标签字体 TTF / OTF / TTC")
        font.clicked.connect(self.font_requested)
        form.addRow(font)
        self.font_label = QLabel("默认：内置拉丁字体；中文标签需导入字体。")
        form.addRow(self.font_label)
        form.addRow(QLabel("调整统一高度后，请在各原图重新核对裁剪；同 Fig 宽度与 N 须一致。"))
        settings_scroll = QScrollArea()
        settings_scroll.setWidget(settings)
        settings_scroll.setWidgetResizable(True)
        tabs.addTab(settings_scroll, "模板与排序")
        split.addWidget(tabs)
        split.setStretchFactor(1, 2)
        root.addWidget(split, 1)
        bottom = QHBoxLayout()
        preview = QPushButton("生成预览")
        export = QPushButton("导出拼图归档 ZIP")
        preview.clicked.connect(self.preview_requested)
        export.clicked.connect(self.export_requested)
        bottom.addWidget(preview)
        bottom.addWidget(export)
        root.addLayout(bottom)
        self.name.textEdited.connect(self._edited)
        self.template_name.textEdited.connect(self._edited)
        self.figure_order.textEdited.connect(self._edited)
        self.right_labels.toggled.connect(self._edited)
        self.filter.currentIndexChanged.connect(self._filter_rows)
        self.table.cellChanged.connect(self._cell_changed)
        self.table.currentCellChanged.connect(self._selected)
        self.canvas.roi_drawn.connect(self._drawn)
        self.set_project(self._project)

    def _text(self, row: int, column: int) -> str:
        item = self.table.item(row, column)
        return item.text().strip() if item else ""

    def project(self, revision: int | None = None) -> WBFigureProject:
        rows: list[FigureRow] = []
        for i, original in enumerate(self._project.rows):
            roi = None
            if original.source is not None and any(self._text(i, c) for c in range(4, 8)):
                roi = LaneROI(original.row_id, *(int(self._text(i, c)) for c in range(4, 8)))
            review = self.table.item(i, 9)
            rows.append(
                FigureRow(
                    row_id=original.row_id,
                    source=original.source,
                    filename=original.filename,
                    width=original.width,
                    height=original.height,
                    bit_depth=original.bit_depth,
                    figure=self._text(i, 1),
                    protein=self._text(i, 2),
                    lane_count=int(self._text(i, 3)),
                    empty_lanes=tuple(
                        int(n.strip()) for n in self._text(i, 8).split(",") if n.strip()
                    ),
                    roi=roi,
                    reviewed=bool(review and review.checkState() == Qt.CheckState.Checked),
                    notes=self._text(i, 10),
                )
            )
        settings = self._project.template.model_dump()
        settings.update({key: spin.value() for key, spin in self.numbers.items()})
        settings.update(
            name=self.template_name.text().strip(),
            label_side="right" if self.right_labels.isChecked() else "left",
            font=self._project.template.font,
        )
        order = tuple(s.strip() for s in self.figure_order.text().split(",") if s.strip())
        return WBFigureProject(
            project_id=self._project.project_id,
            name=self.name.text().strip(),
            revision=self._project.revision if revision is None else revision,
            rows=tuple(rows),
            figure_order=order,
            template=FigureTemplate(**settings),
        )

    def set_project(self, project: WBFigureProject) -> None:
        self._loading = True
        self._project = project
        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)
        self.canvas.set_image(PreviewRaster("", 0, 0, 0, 0, b"", 0, ()))
        self.canvas.set_lanes(())
        self.name.setText(project.name)
        self.figure_order.setText(", ".join(project.figure_order))
        self.template_name.setText(project.template.name)
        for key, spin in self.numbers.items():
            spin.setValue(getattr(project.template, key))
        self.right_labels.setChecked(project.template.label_side == "right")
        self.font_label.setText(
            "字体已保存为项目资产"
            if project.template.font
            else "默认：内置拉丁字体；中文标签需导入字体。"
        )
        self.table.setRowCount(len(project.rows))
        for index, row in enumerate(project.rows):
            roi = row.roi
            values = [
                row.filename,
                row.figure,
                row.protein,
                str(row.lane_count),
                *((str(v) for v in (roi.x0, roi.y0, roi.x1, roi.y1)) if roi else ("", "", "", "")),
                ",".join(map(str, row.empty_lanes)),
                "",
                row.notes,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setToolTip(
                        f"{row.width} × {row.height} · {row.bit_depth} 位\n"
                        f"{row.source.sha256 if row.source else '缺图占位'}"
                    )
                if column == 9:
                    item.setFlags(
                        (item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        & ~Qt.ItemFlag.ItemIsEditable
                    )
                    item.setCheckState(
                        Qt.CheckState.Checked if row.reviewed else Qt.CheckState.Unchecked
                    )
                self.table.setItem(index, column, item)
        self._loading = False
        self._filter_rows()

    def _edited(self) -> None:
        if self._loading:
            return
        self.generation += 1
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("内容已修改，请重新生成预览")
        self.changed.emit()

    def _cell_changed(self, row: int, column: int) -> None:
        if self._loading:
            return
        if column != 9:
            check = self.table.item(row, 9)
            if check:
                self._loading = True
                check.setCheckState(Qt.CheckState.Unchecked)
                self._loading = False
        if column == 1:
            names = tuple(dict.fromkeys(self._text(i, 1) for i in range(self.table.rowCount())))
            self.figure_order.setText(", ".join(names))
        self._edited()
        self._filter_rows()
        self._overlay()

    def _selected(self, row: int, _column: int, _previous_row: int, _previous_column: int) -> None:
        if not self._loading and 0 <= row < len(self._project.rows):
            self.source_requested.emit(self._project.rows[row].row_id)

    def selected_row(self) -> FigureRow | None:
        index = self.table.currentRow()
        return self.project().rows[index] if 0 <= index < len(self._project.rows) else None

    def set_source_preview(self, preview: PreviewRaster) -> None:
        self.canvas.set_image(preview)
        self._overlay()

    def _overlay(self) -> None:
        try:
            row = self.selected_row()
            self.canvas.set_lanes(
                fixed_lane_grid(row.roi, row.lane_count) if row and row.roi else ()
            )
        except ValueError as error:
            self.status.setText(str(error))

    def _drawn(self, coords: tuple[int, int, int, int]) -> None:
        index = self.table.currentRow()
        if index < 0 or self._project.rows[index].source is None:
            return
        self._loading = True
        for column, value in enumerate(coords, start=4):
            item = self.table.item(index, column)
            if item:
                item.setText(str(value))
        self._loading = False
        self._cell_changed(index, 4)

    def _filter_rows(self) -> None:
        mode = self.filter.currentIndex()
        for i, row in enumerate(self._project.rows):
            review = self.table.item(i, 9)
            checked = bool(review and review.checkState() == Qt.CheckState.Checked)
            hidden = (
                (mode == 1 and checked)
                or (mode == 2 and not checked)
                or (mode == 3 and not self._text(i, 8))
                or (mode == 4 and row.source is not None)
            )
            self.table.setRowHidden(i, bool(hidden))

    def move_row(self, step: int) -> None:
        try:
            project = self.project()
            index = self.table.currentRow()
            target = index + step
            if not (0 <= index < len(project.rows) and 0 <= target < len(project.rows)):
                return
            rows = list(project.rows)
            rows[index], rows[target] = rows[target], rows[index]
            self.set_project(project.model_copy(update={"rows": tuple(rows)}))
            self.table.selectRow(target)
            self._edited()
        except ValueError as error:
            self.status.setText(str(error))

    def add_missing(self) -> None:
        try:
            project = self.project()
            figure = project.figure_order[-1] if project.figure_order else "Fig1"
            row = FigureRow(row_id=uuid4().hex, figure=figure)
            self.set_project(
                project.model_copy(
                    update={
                        "rows": (*project.rows, row),
                        "figure_order": project.figure_order or (figure,),
                    }
                )
            )
            self._edited()
        except ValueError as error:
            self.status.setText(str(error))

    def remove_row(self) -> None:
        try:
            project = self.project()
            rows = tuple(r for i, r in enumerate(project.rows) if i != self.table.currentRow())
            order = tuple(
                name for name in project.figure_order if any(r.figure == name for r in rows)
            )
            self.set_project(project.model_copy(update={"rows": rows, "figure_order": order}))
            self._edited()
        except ValueError as error:
            self.status.setText(str(error))

    def confirm_selected(self) -> None:
        for index in self.table.selectionModel().selectedRows():
            item = self.table.item(index.row(), 9)
            if item and not self.table.isRowHidden(index.row()):
                item.setCheckState(Qt.CheckState.Checked)

    def show_render(self, rendered: FigureRender) -> None:
        image = QImage(
            rendered.rgb,
            rendered.width,
            rendered.height,
            rendered.width * 3,
            QImage.Format.Format_RGB888,
        ).copy()
        self.preview_label.setPixmap(QPixmap.fromImage(image))
        self.preview_label.setMinimumSize(rendered.width, rendered.height)
