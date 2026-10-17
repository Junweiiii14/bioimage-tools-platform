"""Composite OCR evidence, editable labels and explicit project-row selection."""

from math import ceil, floor
from uuid import uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.desktop_data import PreviewRaster
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_ocr import ProjectOCRRow, ProjectOCRState, WBProjectOCR
from wb_tool.domain.lanes import LaneROI
from wb_tool.ui.canvas import ImageCanvas
from wb_tool.ui.project_results import ProjectResultsView


class ProjectOCRPanel(QWidget):
    changed = Signal()
    import_requested = Signal()
    run_requested = Signal()
    compose_requested = Signal()
    refresh_requested = Signal()
    export_requested = Signal()
    binding_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._state: ProjectOCRState | None = None
        self._loading = False
        self._rows: tuple[ProjectOCRRow, ...] = ()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        actions = QHBoxLayout()
        self.import_button = QPushButton("导入外部拼图")
        self.import_button.clicked.connect(self.import_requested)
        self.compose_button = QPushButton("识别当前项目拼图")
        self.compose_button.setObjectName("primaryAction")
        self.compose_button.clicked.connect(self.compose_requested)
        self.run_button = QPushButton("重新识别文字")
        self.run_button.clicked.connect(self.run_requested)
        for button in (self.compose_button, self.import_button, self.run_button):
            actions.addWidget(button)
        actions.addStretch()
        self.results_toggle = QPushButton("关联结果")
        self.results_toggle.setCheckable(True)
        actions.addWidget(self.results_toggle)
        layout.addLayout(actions)
        self.note = QLabel("识别当前拼图，或导入外部拼图。识别后核对文字并关联原图。")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.body = QSplitter(Qt.Orientation.Horizontal)
        evidence = QTabWidget()
        self.canvas = ImageCanvas(
            empty_message="识别当前项目拼图，或导入外部拼图。\n识别结果会显示在这里，原图定量不会被改变。"
        )
        evidence.addTab(self.canvas, "拼图")
        self.raw = QPlainTextEdit()
        self.raw.setReadOnly(True)
        evidence.addTab(self.raw, "识别依据")
        self.body.addWidget(evidence)
        self.labels_panel = QWidget()
        label_layout = QVBoxLayout(self.labels_panel)
        label_layout.setContentsMargins(12, 0, 0, 0)
        label_layout.addWidget(QLabel("核对标签与来源"))
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Fig", "蛋白", "确认", "关联原图"])
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 45)
        label_layout.addWidget(self.table, 1)
        controls = QHBoxLayout()
        self.add_button = QPushButton("补充标签")
        self.add_button.clicked.connect(self.add_row)
        self.remove_button = QPushButton("删除所选")
        self.remove_button.clicked.connect(self.remove_row)
        controls.addWidget(self.add_button)
        controls.addWidget(self.remove_button)
        label_layout.addLayout(controls)
        self.binding_note = QLabel("选择标签，再指定对应的已审核原图。")
        self.binding_note.setWordWrap(True)
        label_layout.addWidget(self.binding_note)
        self.target = QComboBox()
        self.target.setMinimumWidth(0)
        self.target.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.target.setMinimumContentsLength(18)
        label_layout.addWidget(self.target)
        binding = QHBoxLayout()
        self.bind_button = QPushButton("关联此原图")
        self.bind_button.clicked.connect(lambda: self.bind(False))
        self.unbind_button = QPushButton("解除关联")
        self.unbind_button.clicked.connect(lambda: self.bind(True))
        binding.addWidget(self.bind_button)
        binding.addWidget(self.unbind_button)
        label_layout.addLayout(binding)
        self.body.addWidget(self.labels_panel)
        self.body.setStretchFactor(0, 3)
        self.body.setStretchFactor(1, 1)
        self.body.setSizes([780, 320])
        layout.addWidget(self.body, 1)
        self.output_panel = QWidget()
        output = QVBoxLayout(self.output_panel)
        output.setContentsMargins(0, 0, 0, 0)
        result_actions = QHBoxLayout()
        self.refresh_button = QPushButton("计算关联结果")
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.export_button = QPushButton("导出关联表 XLSX / CSV")
        self.export_button.clicked.connect(self.export_requested)
        result_actions.addWidget(self.refresh_button)
        result_actions.addStretch()
        result_actions.addWidget(self.export_button)
        output.addLayout(result_actions)
        self.result_view = ProjectResultsView()
        self.results = self.result_view.table
        output.addWidget(self.result_view, 1)
        layout.addWidget(self.output_panel, 1)
        self.results_toggle.toggled.connect(self._show_results)
        self.table.cellChanged.connect(self._edited)
        self.table.currentCellChanged.connect(self._selected)
        self.target.currentIndexChanged.connect(self._update_actions)
        self._show_results(False)
        self._update_actions()

    def _show_results(self, shown: bool) -> None:
        self.output_panel.setVisible(shown)
        self.body.setVisible(not shown)
        self.results_toggle.setText("返回拼图校正" if shown else "关联结果")

    def _update_actions(self, *_args: object) -> None:
        has_source = self._state is not None
        selected = 0 <= self.table.currentRow() < len(self._rows)
        self.run_button.setVisible(has_source)
        self.labels_panel.setVisible(has_source)
        self.results_toggle.setVisible(bool(self._rows))
        self.add_button.setEnabled(has_source)
        self.remove_button.setEnabled(selected)
        self.bind_button.setEnabled(selected and bool(self.target.currentData()))
        self.unbind_button.setEnabled(
            selected and self._rows[self.table.currentRow()].link is not None
        )
        self.refresh_button.setEnabled(bool(self._rows))
        self.export_button.setEnabled(bool(self._rows))
        self.binding_note.setText(
            "尚无已审核的原图。请先在图像复核中确认裁剪，再回来关联。"
            if self.target.count() <= 1
            else "选择对应原图并关联，核对文字后勾选确认。"
        )
        if not self._rows:
            self.results_toggle.setChecked(False)
            self._show_results(False)

    def state(self) -> ProjectOCRState | None:
        if self._state is None:
            return None
        rows: list[ProjectOCRRow] = []
        for i, row in enumerate(self._rows):
            figure, protein, check = (self.table.item(i, c) for c in range(3))
            if figure is None or protein is None or check is None:
                raise ValueError("OCR表格内容不完整")
            rows.append(
                ProjectOCRRow(
                    row_id=row.row_id,
                    heading_token_id=row.heading_token_id,
                    label_token_id=row.label_token_id,
                    figure=figure.text().strip(),
                    protein=protein.text().strip(),
                    confirmed=check.checkState() == Qt.CheckState.Checked,
                    link=row.link,
                )
            )
        old = self._state
        return ProjectOCRState(
            source=old.source,
            filename=old.filename,
            width=old.width,
            height=old.height,
            run=old.run,
            recognition=old.recognition,
            rows=tuple(rows),
        )

    def restore(self, project: WBFigureProject) -> None:
        old_source = self._state.source if self._state else None
        self._state = project.ocr if isinstance(project, WBProjectOCR) else None
        self._rows = self._state.rows if self._state else ()
        if self._state is None or self._state.source != old_source:
            self.canvas.set_image(PreviewRaster("", 0, 0, 0, 0, b"", 0, ()))
        self._loading = True
        self.table.setRowCount(len(self._rows))
        for i, row in enumerate(self._rows):
            for c, text in enumerate(
                (
                    row.figure,
                    row.protein,
                    "",
                    "未关联",
                )
            ):
                item = QTableWidgetItem(text)
                if c == 2:
                    item.setFlags(
                        (item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        & ~Qt.ItemFlag.ItemIsEditable
                    )
                    item.setCheckState(
                        Qt.CheckState.Checked if row.confirmed else Qt.CheckState.Unchecked
                    )
                if c == 3:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, c, item)
        self.refresh_targets(project)
        recognition = self._state.recognition if self._state else None
        self.raw.setPlainText(
            "\n".join(
                f"{t.token_id}\t{t.text}\t{t.confidence:.4f}\t({t.bounds.x0:.1f},{t.bounds.y0:.1f})–({t.bounds.x1:.1f},{t.bounds.y1:.1f})"
                for t in recognition.tokens
            )
            if recognition
            else "尚无已提交的OCR原文"
        )
        self.note.setText(
            (self._state.filename + "：校正Fig/蛋白，关联原图行后勾选确认。")
            if self._state
            else "识别当前项目拼图，或导入外部拼图。定量仍从原图读取。"
        )
        self._loading = False
        self.result_view.invalidate()
        self._selected()

    def refresh_targets(self, project: WBFigureProject) -> None:
        """Refresh source choices without discarding in-progress OCR label edits."""
        selected = self.target.currentData()
        self.target.clear()
        self.target.addItem("选择已审核的原图行", "")
        names: dict[str, str] = {}
        for row in project.rows:
            title = f"{row.figure} · {row.protein} · {row.filename} · N={row.lane_count}"
            names[row.row_id] = title
            if row.source and row.roi and row.reviewed:
                self.target.addItem(title, row.row_id)
        self.target.setCurrentIndex(max(0, self.target.findData(selected)))
        loading, self._loading = self._loading, True
        for i, row in enumerate(self._rows):
            item = self.table.item(i, 3)
            if item:
                item.setText(
                    names.get(row.link.target_row_id, "原图行已删除") if row.link else "未关联"
                )
        self._loading = loading
        self._update_actions()

    def _edited(self, row: int, column: int) -> None:
        if self._loading:
            return
        if column in (0, 1):
            self._loading = True
            check = self.table.item(row, 2)
            if check:
                check.setCheckState(Qt.CheckState.Unchecked)
            self._loading = False
        try:
            self.state()
        except ValueError as error:
            self.note.setText(str(error))
            if column == 2:
                self._loading = True
                check = self.table.item(row, 2)
                if check:
                    check.setCheckState(Qt.CheckState.Unchecked)
                self._loading = False
        self.result_view.invalidate()
        self.changed.emit()

    def _selected(self, *_args: object) -> None:
        regions: list[LaneROI] = []
        i = self.table.currentRow()
        self.target.setCurrentIndex(0)
        if self._state and self._state.recognition and 0 <= i < len(self._rows):
            row = self._rows[i]
            if row.link:
                self.target.setCurrentIndex(max(0, self.target.findData(row.link.target_row_id)))
            for token in self._state.recognition.tokens:
                if token.token_id in (row.heading_token_id, row.label_token_id):
                    b = token.bounds
                    regions.append(
                        LaneROI(token.text[:60], floor(b.x0), floor(b.y0), ceil(b.x1), ceil(b.y1))
                    )
        self.canvas.set_regions(tuple(regions))
        self._update_actions()

    def set_preview(self, preview: PreviewRaster) -> None:
        if self._state and preview.sha256 == self._state.source.sha256:
            self.canvas.set_image(preview)
            self._selected()

    def bind(self, clear: bool) -> None:
        i = self.table.currentRow()
        target = self.target.currentData()
        if 0 <= i < len(self._rows) and isinstance(target, str) and (clear or target):
            self.binding_requested.emit(self._rows[i].row_id, "" if clear else target)

    def add_row(self) -> None:
        if self._state:
            if len(self._rows) >= 512:
                self.note.setText("最多512个OCR行，请先删除不需要的行。")
                return
            self._loading = True
            self._rows = (*self._rows, ProjectOCRRow(row_id=uuid4().hex))
            self.table.setRowCount(len(self._rows))
            i = len(self._rows) - 1
            for c in range(4):
                item = QTableWidgetItem("未关联" if c == 3 else "")
                if c == 2:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Unchecked)
                if c >= 2:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, c, item)
            self._loading = False
            self.table.setCurrentCell(i, 0)
            self.result_view.invalidate()
            self.changed.emit()
            self._update_actions()

    def remove_row(self) -> None:
        i = self.table.currentRow()
        if 0 <= i < len(self._rows):
            self._loading = True
            self._rows = tuple(row for n, row in enumerate(self._rows) if n != i)
            self.table.removeRow(i)
            self._loading = False
            self.result_view.invalidate()
            self.changed.emit()
            self._update_actions()
