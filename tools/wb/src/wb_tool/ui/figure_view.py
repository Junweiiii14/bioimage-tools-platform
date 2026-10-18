"""Multi-image row review and template editing; host owns assets and asynchronous work."""

from dataclasses import replace
from uuid import uuid4

from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.crop_suggestions import (
    WBReviewProject,
    apply_crop_suggestion,
    project_with_suggestions,
)
from wb_tool.application.desktop_data import PreviewRaster
from wb_tool.application.figure_project import (
    FigureRender,
    FigureRow,
    FigureTemplate,
    WBFigureProject,
)
from wb_tool.application.laboratory_layout import (
    initial_composition,
    with_figure_layout,
)
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    WBAnalysisProject,
    analysis_is_current,
    make_row_analysis,
    project_with_analyses,
    set_row_analysis,
    update_row_analysis_request,
)
from wb_tool.application.project_normalization import (
    WBNormalizedProject,
    make_normalization_plan,
    project_with_normalizations,
)
from wb_tool.application.project_ocr import WBProjectOCR, bind_project_ocr_row, project_with_ocr
from wb_tool.application.project_restore import WBRestoredProject, with_archive_history
from wb_tool.domain.automatic import resize_crop_for_lane_count
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI
from wb_tool.ui.canvas import ImageCanvas
from wb_tool.ui.crop_suggestions import CropSuggestionPanel
from wb_tool.ui.laboratory_layout import LaboratoryLayoutPanel
from wb_tool.ui.normalization import NormalizationPanel
from wb_tool.ui.project_analysis import ProjectAnalysisPanel
from wb_tool.ui.project_metadata import ProjectMetadataPanel
from wb_tool.ui.project_ocr import ProjectOCRPanel
from wb_tool.ui.result_workspace import ResultWorkspace


class FigurePreview(QLabel):
    """Display-only fit/actual-size preview; retains complete unscaled render pixels."""

    def __init__(self) -> None:
        super().__init__("生成预览后，可在这里检查完整拼图")
        self.full_pixmap = QPixmap()
        self.fit = True
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

    def set_render(self, pixmap: QPixmap) -> None:
        self.full_pixmap = pixmap.copy()
        self.set_fit(self.fit)

    def clear_render(self) -> None:
        self.full_pixmap = QPixmap()
        self.setMinimumSize(0, 0)
        self.setPixmap(QPixmap())
        self.setText("内容已修改，请重新生成预览")

    def set_fit(self, fit: bool) -> None:
        self.fit = fit
        self.setMinimumSize(QSize(0, 0) if fit else self.full_pixmap.size())
        self._refresh()

    def _refresh(self) -> None:
        if not self.full_pixmap.isNull():
            self.setPixmap(
                self.full_pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                if self.fit
                else self.full_pixmap
            )

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._refresh()


class FigureProjectView(QWidget):
    image_export_button: QPushButton
    archive_export_button: QPushButton
    table_export_button: QPushButton
    ocr_export_button: QPushButton
    normalization_export_button: QPushButton
    changed = Signal()
    source_requested = Signal(str)
    preview_requested = Signal()
    export_requested = Signal()
    image_export_requested = Signal()
    font_requested = Signal()
    template_export_requested = Signal()
    template_import_requested = Signal()
    detection_requested = Signal(bool)
    automatic_requested = Signal()
    automatic_export_requested = Signal()
    output_folder_requested = Signal()
    import_directory_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.generation = 0
        self._loading = False
        self._project = WBFigureProject(project_id=uuid4().hex)
        self._thumbnails: dict[str, QIcon] = {}
        self._source_preview: PreviewRaster | None = None
        self._rendered_preview: FigureRender | None = None
        self._last_review_focus: QWidget | None = None
        self._pending_review_focus: QWidget | None = None
        self._crop_history: list[
            tuple[str, tuple[int, int, int, int], tuple[int, int, int, int], int, int]
        ] = []
        self._crop_history_index = 0
        self._restoring_crop = False
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 4, 8, 8)
        root.setSpacing(5)
        project_header = QHBoxLayout()
        caption = QLabel("当前项目")
        caption.setObjectName("projectCaption")
        project_header.addWidget(caption)
        self.name = QLineEdit("WB 项目")
        self.name.setObjectName("projectName")
        project_header.addWidget(self.name, 1)
        root.addLayout(project_header)
        self.status = QLabel("导入原图文件夹后自动识别；需要修正时，直接拖动图中的裁剪框。")
        self.status.setWordWrap(True)

        self.history_label = QLabel(self)
        self.history_label.setWordWrap(True)
        self.history_label.hide()
        actions = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.addItems(
            [
                "全部原图",
                "需关注",
                "已审核",
                "预标空泳道",
                "缺图",
                "建议有弱/空槽",
                "多候选",
                "无候选/失败",
            ]
        )
        self.filter.setMinimumWidth(0)
        actions.addWidget(self.filter)
        for text, callback in (
            ("上移", lambda: self.move_row(-1)),
            ("下移", lambda: self.move_row(1)),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            actions.addWidget(button)
        more = QToolButton()
        more.setText("更多操作")
        menu = QMenu(more)
        for text, callback in (("添加缺图位", self.add_missing), ("删除所选行", self.remove_row)):
            menu.addAction(text).triggered.connect(callback)
        more.setMenu(menu)
        more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        actions.addWidget(more)
        self.exact_coordinates = QCheckBox("精确坐标")
        self.exact_coordinates.toggled.connect(self._show_coordinates)
        actions.addWidget(self.exact_coordinates)
        actions.addStretch()
        confirm = QPushButton("确认所选行")
        confirm.setObjectName("primaryAction")
        confirm.clicked.connect(self.confirm_selected)
        actions.addWidget(confirm)
        source_controls = QWidget()
        source_controls_layout = QVBoxLayout(source_controls)
        source_controls_layout.setContentsMargins(6, 4, 6, 4)
        source_controls_layout.addLayout(actions)
        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(
            ["原图", "Fig", "蛋白", "N", "x0", "y0", "x1", "y1", "空泳道(逗号)", "已审核", "备注"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setMinimumHeight(110)
        self.table.setMaximumHeight(170)
        self.table.setIconSize(QSize(96, 64))
        for index in range(3, 8):
            self.table.setColumnWidth(index, 60)
        self.table.setColumnWidth(0, 205)
        self._show_coordinates(False)
        self.table.setColumnWidth(9, 65)

        self.canvas = ImageCanvas()
        self.suggestions = CropSuggestionPanel()
        self.suggestions.run_requested.connect(self.detection_requested)
        self.suggestions.apply_requested.connect(self.apply_candidate)
        self.suggestions.candidate_changed.connect(self._overlay)
        self.suggestions.focus_requested.connect(self.focus_membrane)
        self.suggestions.reset_view_requested.connect(lambda: self.canvas.set_view_region(None))
        source_page = self._build_source_workspace()

        self.metadata = ProjectMetadataPanel()
        self.metadata.preview_requested.connect(self._metadata_preview)
        self.metadata.apply_requested.connect(self._metadata_apply)

        self.analysis = ProjectAnalysisPanel()
        self.analysis.configure_requested.connect(self.configure_analysis)
        self.analysis.changed.connect(self._edited)
        self._results: tuple[LoadedProjectResult, ...] = ()

        self.ocr = ProjectOCRPanel()
        self.ocr.changed.connect(self._edited)
        self.ocr.binding_requested.connect(self.bind_ocr)

        self.normalization = NormalizationPanel()
        self.normalization.changed.connect(self._edited)
        self.normalization.configure_requested.connect(self.configure_normalization)
        self.normalization.remove_requested.connect(self.remove_normalization)

        preview_page = QWidget()
        preview_layout = QVBoxLayout(preview_page)
        preview_page.setMinimumWidth(250)
        preview_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_label = FigurePreview()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_scroll = QScrollArea()
        preview_scroll.setWidget(self.preview_label)
        preview_scroll.setWidgetResizable(True)
        preview_layout.addWidget(preview_scroll)

        settings = QWidget()
        form = QFormLayout(settings)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        settings.setMinimumWidth(0)
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
        self.template_export_button = QPushButton("保存模板文件…")
        self.template_import_button = QPushButton("导入模板并新建项目…")
        self.template_export_button.clicked.connect(self.template_export_requested)
        self.template_import_button.clicked.connect(self.template_import_requested)
        form.addRow(self.template_export_button)
        form.addRow(self.template_import_button)
        template_note = QLabel("模板只保存排版设置和字体；导入前保存当前项目，再新建空项目。")
        template_note.setWordWrap(True)
        form.addRow(template_note)
        form.addRow(QLabel("调整统一高度后，请在各原图重新核对裁剪；同 Fig 宽度与 N 须一致。"))
        settings_scroll = QScrollArea()
        settings_scroll.setWidget(settings)
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll.setMinimumWidth(0)
        for label in settings.findChildren(QLabel):
            label.setWordWrap(True)
            label.setMinimumWidth(0)

        self.laboratory_layout = LaboratoryLayoutPanel()
        self.laboratory_layout.changed.connect(self._edited)
        self.laboratory_layout.rebuild_requested.connect(self.rebuild_layout)

        self._build_workflow(root, source_controls, source_page, settings_scroll, preview_page)
        self.name.textEdited.connect(self._edited)
        self.template_name.textEdited.connect(self._edited)
        self.figure_order.textEdited.connect(self._edited)
        self.right_labels.toggled.connect(self._edited)
        self.filter.currentIndexChanged.connect(self._filter_rows)
        self.table.cellChanged.connect(self._cell_changed)
        self.table.currentCellChanged.connect(self._selected)
        self.canvas.roi_drawn.connect(self._drawn)
        self.canvas.lane_selected.connect(self._select_graphical_lane)
        self.analysis.lane_changed.connect(self._highlight_lane)
        for editor in (
            self.canvas,
            self.analysis.plot,
            self.analysis.lane_selector,
            self.name,
            *self.source_fields.values(),
            *self.analysis.lane_fields.values(),
        ):
            editor.installEventFilter(self)
        self.set_project(self._project)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "analysis_source"):
            self._refresh_source_workspace()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.FocusIn and isinstance(watched, QWidget):
            self._last_review_focus = watched
        return super().eventFilter(watched, event)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange and self.isEnabled():
            # Child enabled states settle after the parent's changeEvent.
            QTimer.singleShot(0, self._restore_review_focus)

    def _restore_review_focus(self) -> None:
        focused = self._pending_review_focus
        if self.isEnabled() and focused is not None and focused.isVisible() and focused.isEnabled():
            self._pending_review_focus = None
            focused.setFocus()

    def _build_source_workspace(self) -> QWidget:
        workspace = QWidget()
        layout = QHBoxLayout(workspace)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)
        left = QWidget()
        left.setObjectName("sourceRail")
        left.setFixedWidth(224)
        rail = QVBoxLayout(left)
        rail.setContentsMargins(12, 14, 12, 14)
        rail.setSpacing(10)
        self.source_count = QLabel("项目原图")
        self.source_count.setObjectName("evidenceHeading")
        rail.addWidget(self.source_count)
        self.import_directory_button = QPushButton("导入原图文件夹…", self)
        self.import_directory_button.clicked.connect(self.import_directory_requested)
        self.import_directory_button.hide()
        rail.addWidget(self.filter)
        self.source_list = QListWidget()
        self.source_list.setObjectName("sourceList")
        self.source_list.setAccessibleName("项目原图列表")
        self.source_list.setIconSize(QSize(48, 40))
        self.source_list.setWordWrap(False)
        self.source_list.setMinimumHeight(150)
        self.source_list.currentRowChanged.connect(self._select_analysis_source)
        rail.addWidget(self.source_list, 1)
        self.automatic_button = QPushButton("重新自动识别")
        self.automatic_button.setObjectName("secondaryAction")
        self.automatic_button.setMinimumHeight(38)
        self.automatic_button.clicked.connect(self.automatic_requested)
        rail.addWidget(self.automatic_button)
        self.automatic_export_button = QPushButton("导出自动化结果…", self)
        self.automatic_export_button.clicked.connect(self.automatic_export_requested)
        self.automatic_export_button.hide()
        note = QLabel("选择原图查看识别结果。\n需要关注的项会保留具体原因。")
        note.setWordWrap(True)
        note.setObjectName("sourceHint")
        rail.addWidget(note)
        layout.addWidget(left)

        center = QWidget()
        evidence = QVBoxLayout(center)
        evidence.setContentsMargins(0, 0, 0, 0)
        evidence.setSpacing(8)
        tools = QHBoxLayout()
        self.source_image_title = QLabel("原图预览")
        self.source_image_title.setObjectName("evidenceHeading")
        self.source_image_title.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        tools.addWidget(self.source_image_title, 1)
        fit = QPushButton("适应窗口")
        fit.clicked.connect(lambda: self.canvas.set_view_region(None))
        tools.addWidget(fit)
        undo = QPushButton("撤销裁剪")
        undo.clicked.connect(lambda: self._crop_history_step(-1))
        tools.addWidget(undo)
        redo = QPushButton("重做")
        redo.clicked.connect(lambda: self._crop_history_step(1))
        tools.addWidget(redo)
        evidence.addLayout(tools)
        self.canvas.setMinimumSize(280, 240)
        self.canvas.empty_message = "导入 TIFF 原图文件夹\n自动识别后，在这里检查和调整裁剪"
        self.image_evidence_layout = evidence
        evidence.addWidget(self.canvas, 1)
        hint = QLabel("框内拖动：移动裁剪  ·  边角拖动：调整大小  ·  滚轮：缩放  ·  中键：平移")
        hint.setWordWrap(True)
        hint.setObjectName("sourceHint")
        evidence.addWidget(hint)
        layout.addWidget(center, 1)

        right = QWidget()
        right.setObjectName("sourceReview")
        review = QVBoxLayout(right)
        review.setContentsMargins(12, 14, 12, 14)
        review.setSpacing(12)
        heading = QLabel("当前原图 · 复核")
        heading.setObjectName("evidenceHeading")
        review.addWidget(heading)
        self.source_review_status = QLabel("导入原图后开始自动处理")
        self.source_review_status.setWordWrap(True)
        review.addWidget(self.source_review_status)
        self.source_details = QLabel()
        self.source_details.setWordWrap(True)
        self.source_details.setObjectName("sourceHint")
        review.addWidget(self.source_details)
        form = QFormLayout()
        form.setSpacing(8)
        self.source_fields: dict[int, QLineEdit] = {}
        for column, label in ((1, "Fig"), (2, "蛋白名称"), (3, "泳道数"), (8, "排除泳道")):
            field = QLineEdit()
            field.setMinimumWidth(0)
            field.setAccessibleName(label)
            field.editingFinished.connect(lambda c=column: self._source_field_edited(c))
            self.source_fields[column] = field
            form.addRow(label, field)
        self.source_fields[2].setPlaceholderText("未指定")
        self.source_fields[8].setPlaceholderText("可选，例如 3, 6")
        self.source_metadata = QWidget()
        self.source_metadata.setLayout(form)
        self.source_metadata.hide()
        details_toggle = QCheckBox("实验信息与泳道设置")
        details_toggle.toggled.connect(self.source_metadata.setVisible)
        review.addWidget(details_toggle)
        review.addWidget(self.source_metadata)
        confirm = QPushButton("确认裁剪并查看下一项")
        confirm.setObjectName("primaryAction")
        confirm.clicked.connect(self._confirm_and_next)
        review.addWidget(confirm)
        self.source_review_layout = review
        self.suggestions_toggle = QCheckBox("检测候选与高级设置")
        self.suggestions_toggle.toggled.connect(self.suggestions.setVisible)
        review.addWidget(self.suggestions_toggle)
        self.suggestions.hide()
        review.addWidget(self.suggestions)
        review.addStretch()
        self.source_controls_scroll = QScrollArea()
        self.source_controls_scroll.setWidgetResizable(True)
        self.source_controls_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.source_controls_scroll.setFixedWidth(272)
        self.source_controls_scroll.setWidget(right)
        layout.addWidget(self.source_controls_scroll)
        return workspace

    def _select_graphical_lane(self, index: int) -> None:
        if self.analysis.plan is not None:
            self.analysis.lane_selector.setCurrentIndex(index)
            self.analysis.lane_selector.activated.emit(index)
            self.curve_toggle.setChecked(True)

    def _highlight_lane(self) -> None:
        row = self.analysis.source_row
        if row and row.roi:
            self.canvas.set_lanes(
                tuple(
                    replace(
                        lane,
                        lane_id=f"泳道 {i + 1}"
                        + (" · 当前" if i == self.analysis.lanes.currentRow() else ""),
                    )
                    for i, lane in enumerate(fixed_lane_grid(row.roi, row.lane_count))
                )
            )

    def _source_field_edited(self, column: int) -> None:
        index = self.table.currentRow()
        item = self.table.item(index, column) if index >= 0 else None
        if item is not None:
            item.setText(
                self.source_fields[column].text().strip() or ("Unassigned" if column == 2 else "")
            )

    def _refresh_source_workspace(self) -> None:
        self.source_list.blockSignals(True)
        self.source_list.clear()
        self.source_count.setText(f"项目原图 · {len(self._project.rows)}")
        index = self.table.currentRow()
        for i, row in enumerate(self._project.rows):
            review = self.table.item(i, 9)
            reviewed = bool(review and review.checkState() == Qt.CheckState.Checked)
            state = (
                "裁剪已确认 · 仍需关注"
                if reviewed and self._needs_attention(i)
                else "裁剪已确认"
                if reviewed
                else "自动结果 · 待复核"
                if self._text(i, 4)
                else "未检出 · 需处理"
                if self._text(i, 10)
                else "待识别"
            )
            filename = row.filename or "缺图位"
            width = max(80, self.source_list.viewport().width() - 72)
            display = self.source_list.fontMetrics().elidedText(
                filename, Qt.TextElideMode.ElideMiddle, width
            )
            entry = QListWidgetItem(f"{display}\n{state}")
            entry.setToolTip(f"{filename}\n{state}")
            if row.source and row.source.sha256 in self._thumbnails:
                entry.setIcon(self._thumbnails[row.source.sha256])
            self.source_list.addItem(entry)
            entry.setHidden(self.table.isRowHidden(i))
        self.source_list.setCurrentRow(index)
        self.source_list.blockSignals(False)
        row = self._project.rows[index] if 0 <= index < len(self._project.rows) else None
        self.automatic_button.setEnabled(bool(self._project.rows))
        self.automatic_export_button.setEnabled(bool(self._project.rows))
        for column, field in self.source_fields.items():
            field.setEnabled(row is not None)
            if not field.hasFocus():
                text = self._text(index, column) if row else ""
                field.setText("" if column == 2 and text == "Unassigned" else text)
                if column == 2:
                    field.setToolTip("未指定蛋白，按来源文件名识别图片。中文拼图标签需要项目字体。")
        self.source_image_title.setText(row.filename if row else "原图预览")
        self.source_image_title.setToolTip(row.filename if row else "")
        self.source_details.setText(
            f"{row.width} × {row.height} 像素 · {row.bit_depth} 位原图"
            if row and row.source
            else ""
        )
        review = self.table.item(index, 9) if row else None
        self.source_review_status.setText(
            "裁剪已确认；测量状态见下方。"
            if review and review.checkState() == Qt.CheckState.Checked
            else "已找到裁剪与泳道。拖动框体或边角可调整，确认仅记录裁剪审核。"
            if row and self._text(index, 4)
            else "尚无可靠裁剪。在中央框选膜区域后重新自动识别；不必填写坐标。"
            if row
            else "选择 WB 原图后自动开始处理"
        )
        if row and self._text(index, 10):
            self.source_review_status.setText(
                self.source_review_status.text() + "\n\n" + self._text(index, 10)
            )

    def _preview_scale_changed(self, index: int) -> None:
        self.preview_label.set_fit(index == 0)

    def _show_coordinates(self, visible: bool) -> None:
        for column in range(4, 8):
            self.table.setColumnHidden(column, not visible)

    def _build_workflow(
        self,
        root: QVBoxLayout,
        source_controls: QWidget,
        source_page: QWidget,
        settings: QWidget,
        preview_page: QWidget,
    ) -> None:
        self.steps = QListWidget()
        self.steps.setObjectName("workflowSteps")
        self.steps.setAccessibleName("工作区视图")
        self.steps.addItems(["图像复核", "拼图", "结果"])
        self.steps.setFlow(QListView.Flow.LeftToRight)
        self.steps.setWrapping(False)
        self.steps.setGridSize(QSize(132, 38))
        self.steps.setFixedHeight(42)
        self.steps.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.steps.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar = QWidget()
        navigation = QHBoxLayout(self.sidebar)
        navigation.setContentsMargins(0, 0, 0, 0)
        navigation.addWidget(self.steps, 1)
        self.context_button = QToolButton()
        self.context_button.setText("项目工具")
        menu = QMenu(self.context_button)
        for label, section in (
            ("批量填写实验信息", "metadata"),
            ("高级原图数据", "advanced"),
            ("模板与样式", "template"),
            ("OCR 识别与写表", "ocr"),
            ("样本对应与归一化", "normalization"),
        ):
            menu.addAction(label).triggered.connect(
                lambda _checked=False, s=section: self.show_section(s)
            )
        self.context_button.setMenu(menu)
        self.context_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        navigation.addWidget(self.context_button)
        root.addWidget(self.sidebar)
        self.step_title, self.step_help = QLabel(self), QLabel(self)
        self.step_title.hide()
        self.step_help.hide()
        self.context_header = QWidget()
        context_layout = QHBoxLayout(self.context_header)
        context_layout.setContentsMargins(0, 0, 0, 0)
        self.context_back = QPushButton("返回图像复核")
        self.context_back.clicked.connect(lambda: self.show_section(self._context_return))
        self.context_title = QLabel()
        self.context_title.setObjectName("sectionTitle")
        context_layout.addWidget(self.context_back)
        context_layout.addWidget(self.context_title, 1)
        self._context_return = "source"
        root.addWidget(self.context_header)
        self.context_header.hide()
        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

        # The legacy tab objects remain addressable for host integrations, but are
        # contextual pages, not a second layer of visible navigation.
        self.source_tabs = QTabWidget()
        self.source_tabs.tabBar().hide()
        self.source_tabs.addTab(source_page, "图像复核")
        self.source_tabs.addTab(self.metadata, "批量填写信息")
        advanced = QWidget()
        advanced_layout = QVBoxLayout(advanced)
        advanced_layout.addWidget(source_controls)
        self.table.setMaximumHeight(16777215)
        advanced_layout.addWidget(self.table, 1)
        self.source_tabs.addTab(advanced, "高级数据表")
        self._add_step(self.source_tabs)
        self.curve_toggle = QCheckBox("查看泳道曲线")
        self.curve_toggle.setToolTip("在原始曲线上拖动边界或基线；修改后需重新测量")
        self.image_evidence_layout.insertWidget(1, self.curve_toggle)
        self.image_evidence_layout.insertWidget(3, self.analysis.curve_editor)
        self.analysis.curve_editor.hide()
        self.curve_toggle.toggled.connect(self.analysis.curve_editor.setVisible)
        self.source_review_layout.insertWidget(3, self.analysis.review_controls)
        self.source_review_layout.insertWidget(4, self.analysis.controls)
        self.analysis.controls.hide()
        self.curve_toggle.toggled.connect(self.analysis.controls.setVisible)
        self.analysis_source = QComboBox(self.analysis)
        self.analysis_source.hide()
        self.analysis_sources = QListWidget(self.analysis)
        self.analysis_sources.hide()
        self.analysis_sources.currentRowChanged.connect(self._select_analysis_source)
        self.analysis_source.activated.connect(self._select_analysis_source)

        self.layout_tabs = QTabWidget()
        self.layout_tabs.tabBar().hide()
        arrangement = QSplitter(Qt.Orientation.Horizontal)
        layout_rail = QWidget()
        layout_rail.setMaximumWidth(224)
        rail = QVBoxLayout(layout_rail)
        rail.addWidget(QLabel("拼图与模板"))
        for label, section in (
            ("排版与分段", "layout"),
            ("模板与样式", "template"),
            ("识别标签并写表", "ocr"),
        ):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, s=section: self.show_section(s))
            rail.addWidget(button)
        rail.addStretch()
        arrangement.addWidget(layout_rail)
        preview_layout = preview_page.layout()
        assert isinstance(preview_layout, QVBoxLayout)
        self.preview_button = QPushButton("更新预览")
        self.preview_button.clicked.connect(self.preview_requested)
        self.preview_scale = QComboBox()
        self.preview_scale.addItems(["适应窗口", "100%"])
        self.preview_scale.setAccessibleName("预览显示比例")
        self.preview_scale.currentIndexChanged.connect(self._preview_scale_changed)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("当前拼图"), 1)
        toolbar.addWidget(self.preview_button)
        toolbar.addWidget(self.preview_scale)
        preview_layout.insertLayout(0, toolbar)
        arrangement.addWidget(preview_page)
        self.layout_settings_tabs = QTabWidget()
        self.layout_settings_tabs.tabBar().hide()
        self.layout_settings_tabs.setMinimumWidth(240)
        self.layout_settings_tabs.addTab(self.laboratory_layout, "版式与分段")
        self.layout_settings_tabs.addTab(settings, "样式与模板")
        arrangement.addWidget(self.layout_settings_tabs)
        arrangement.setSizes([200, 720, 280])
        arrangement.setChildrenCollapsible(False)
        self.layout_tabs.addTab(arrangement, "排版与预览")
        self._add_step(self.layout_tabs)

        # Keep analysis host APIs while its result content occupies a three-column workspace.
        result_layout = self.analysis.layout()
        assert isinstance(result_layout, QVBoxLayout)
        self.result_workspace = ResultWorkspace(self.analysis.result_view)
        self._output_location = ""
        self.result_workspace.export_requested.connect(self.automatic_export_requested)
        self.result_workspace.open_output_requested.connect(self.output_folder_requested)
        self.result_workspace.section_requested.connect(
            lambda section="analysis": self.show_section(
                "export" if section == "analysis" else section
            )
        )
        result_layout.addWidget(self.result_workspace, 1)
        self.export_options = self.result_workspace.formats
        formats = self.export_options.layout()
        assert isinstance(formats, QVBoxLayout)
        while formats.count():
            entry = formats.takeAt(0)
            widget = entry.widget() if entry else None
            if widget is not None:
                widget.deleteLater()
        for attribute, label, signal in (
            ("image_export_button", "拼图 TIFF / PNG", self.image_export_requested),
            ("archive_export_button", "完整项目 ZIP", self.export_requested),
            ("table_export_button", "定量表", self.analysis.export_requested),
            ("ocr_export_button", "OCR 关联表", self.ocr.export_requested),
            ("normalization_export_button", "归一化表", self.normalization.export_requested),
        ):
            button = QPushButton(label)
            button.clicked.connect(signal)
            setattr(self, attribute, button)
            formats.addWidget(button)
        self.export_disclosure = self.result_workspace.formats_toggle
        self.analysis.result_view.cells_changed.connect(self._results_changed)
        self.result_workspace.set_summary(self._project, ())
        self.analysis_tabs = QTabWidget()
        self.analysis_tabs.tabBar().hide()
        # Analysis methods/signals remain on the same instance, while its live
        # curve and controls are now embedded in the source workbench.
        self.analysis_tabs.addTab(self.analysis, "结果")
        self.analysis_tabs.addTab(self.ocr, "OCR / 结果表")
        self.analysis_tabs.addTab(self.normalization, "样本对应与归一化")
        self.pages.addWidget(self.analysis_tabs)
        self.previous_step, self.next_step = QPushButton(self), QPushButton(self)
        self.previous_step.hide()
        self.next_step.hide()
        root.addWidget(self.status)
        self.steps.currentRowChanged.connect(self._step_changed)
        self.steps.setCurrentRow(0)

    def _add_step(self, content: QWidget) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        self.pages.addWidget(scroll)

    def _step_changed(self, index: int) -> None:
        if not 0 <= index < 3:
            return
        self.context_header.hide()
        self.pages.setCurrentIndex(index)
        self.source_tabs.setCurrentIndex(0)
        self.analysis_tabs.setCurrentIndex(0)
        self._refresh_analysis_sources()
        self.status.setText(
            (
                "检查自动结果；裁剪调整直接在图上完成，质量警告单独保留。",
                "预览当前拼图；选择右侧属性调整，模板与 OCR 在项目工具中。",
                "结果保留来源和状态；待复核的原始积分不等于有效信号。",
            )[index]
        )

    def show_section(self, section: str) -> None:
        """Navigate contextually without scientific edits or legacy tab layers."""
        sections = {
            "source": 0,
            "metadata": 0,
            "advanced": 0,
            "analysis": 0,
            "layout": 1,
            "template": 1,
            "preview": 1,
            "normalization": 2,
            "ocr": 2,
            "export": 2,
        }
        self.steps.setCurrentRow(sections[section])
        self._step_changed(sections[section])
        if section in ("source", "metadata", "advanced", "analysis"):
            self.source_tabs.setCurrentIndex({"metadata": 1, "advanced": 2}.get(section, 0))
            if section == "analysis":
                self.curve_toggle.setChecked(True)
        if section in ("ocr", "normalization"):
            self.analysis_tabs.setCurrentIndex(1 if section == "ocr" else 2)
        if section in ("layout", "template", "preview"):
            self.layout_settings_tabs.setCurrentIndex(int(section == "template"))
        contexts = {
            "metadata": ("批量填写实验信息", "source"),
            "advanced": ("高级原图数据", "source"),
            "ocr": ("OCR 识别与写表", "export"),
            "normalization": ("样本对应与归一化", "export"),
        }
        if section in contexts:
            title, self._context_return = contexts[section]
            self.context_title.setText(title)
            self.context_back.setText(
                "返回图像复核" if self._context_return == "source" else "返回结果"
            )
            self.context_header.show()
        elif section == "export":
            self.result_workspace.navigation["analysis"].setChecked(True)
            self.result_workspace.navigation["ocr"].setChecked(False)
            self.result_workspace.navigation["normalization"].setChecked(False)
        self._update_result_summary()

    def set_output_location(self, path: str) -> None:
        """Host supplies the latest successfully committed output directory."""
        self._output_location = path
        self._update_result_summary()

    def _update_result_summary(self) -> None:
        self.result_workspace.set_summary(
            self._project, self.analysis.result_view.cells, self._output_location
        )

    def _results_changed(self, _cells: object) -> None:
        self._update_result_summary()
        if not self._loading:
            self.refresh_attention()

    def _confirm_and_next(self) -> None:
        self.confirm_selected()
        current = self.table.currentRow()
        for index in (*range(current + 1, self.table.rowCount()), *range(0, current)):
            if self._needs_attention(index) and not self.table.isRowHidden(index):
                self.table.setCurrentCell(index, 0)
                return
        self.status.setText("裁剪已确认；定量质量警告仍需独立复核。")

    def _needs_attention(self, index: int) -> bool:
        item = self.table.item(index, 9)
        if item is None or item.checkState() != Qt.CheckState.Checked:
            return True
        if not 0 <= index < len(self._project.rows):
            return False
        row_id = self._project.rows[index].row_id
        return self.analysis.row_needs_attention(row_id)

    def _refresh_analysis_sources(self) -> None:
        self.analysis_source.blockSignals(True)
        self.analysis_sources.blockSignals(True)
        self.analysis_source.clear()
        self.analysis_sources.clear()
        for index, row in enumerate(self._project.rows):
            title = f"{self._text(index, 2)} · {row.filename or '缺图'}"
            self.analysis_source.addItem(title, index)
            self.analysis_sources.addItem(title)
            source_item = self.analysis_sources.item(index)
            source_item.setToolTip(title)
        self.analysis_source.setCurrentIndex(self.table.currentRow())
        self.analysis_sources.setCurrentRow(self.table.currentRow())
        self.analysis_sources.blockSignals(False)
        self.analysis_source.blockSignals(False)
        self._refresh_source_workspace()

    def _select_analysis_source(self, index: int) -> None:
        if 0 <= index < self.table.rowCount():
            try:
                self.project()
            except ValueError as error:
                self.status.setText(str(error))
                self._refresh_analysis_sources()
                return
            # The original selection path commits valid dirty annotation edits first.
            self.table.setCurrentCell(index, 0)

    def _text(self, row: int, column: int) -> str:
        item = self.table.item(row, column)
        return item.text().strip() if item else ""

    def project(
        self, revision: int | None = None, *, include_layout: bool = True
    ) -> WBFigureProject:
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
        project = WBFigureProject(
            project_id=self._project.project_id,
            name=self.name.text().strip(),
            revision=self._project.revision if revision is None else revision,
            rows=tuple(rows),
            figure_order=order,
            template=FigureTemplate(**settings),
        )
        if isinstance(self._project, WBReviewProject):
            project = project_with_suggestions(project, self._project.suggestions)
        if isinstance(self._project, WBAnalysisProject):
            project = project_with_analyses(project, self._project.analyses)
            request = self.analysis.request()
            if request is not None and self.analysis.plan is not None:
                project = update_row_analysis_request(project, self.analysis.plan.row_id, request)
        ocr = self.ocr.state()
        if ocr is not None:
            project = project_with_ocr(project, ocr)
        plans = self.normalization.plans()
        if plans or isinstance(self._project, WBNormalizedProject):
            project = project_with_normalizations(project, plans)
        if self.laboratory_layout.active:
            composition = (
                self.laboratory_layout.composition()
                if include_layout
                else initial_composition(project)
            )
            previous = {row.row_id: row for row in self._project.rows}
            changed = {
                row.row_id
                for row in rows
                if row.roi != previous[row.row_id].roi
                or row.lane_count != previous[row.row_id].lane_count
            }
            composition = composition.model_copy(
                update={
                    "slices": tuple(
                        part.model_copy(update={"display_frame": None})
                        if part.row_id in changed
                        else part
                        for part in composition.slices
                    )
                }
            )
            project = with_figure_layout(
                project, composition, self.laboratory_layout.layout_style()
            )
        if isinstance(self._project, WBRestoredProject):
            project = with_archive_history(
                project, self._project.archive_sources, self._project.imported_runs
            )
        from wb_tool.application.automatic import WBAutomaticProject, with_automatic_rows
        from wb_tool.application.fig_quant import WBPartitionProject

        if isinstance(self._project, WBPartitionProject):
            fields = {name: getattr(project, name) for name in type(project).model_fields}
            fields.update(
                schema_version=9,
                automatic_rows=self._project.automatic_rows,
                partition_sources=self._project.partition_sources,
            )
            project = WBPartitionProject.model_validate(fields)
        elif isinstance(self._project, WBAutomaticProject):
            project = with_automatic_rows(project, self._project.automatic_rows)
        return project

    def set_project(self, project: WBFigureProject) -> None:
        self._rendered_preview = None
        self.preview_label.clear_render()
        self._loading = True
        old_index = self.table.currentRow()
        selected = (
            self._project.rows[old_index] if 0 <= old_index < len(self._project.rows) else None
        )
        same_project = project.project_id == self._project.project_id
        selected_index = next(
            (
                i
                for i, row in enumerate(project.rows)
                if same_project
                and selected
                and row.row_id == selected.row_id
                and row.source == selected.source
            ),
            -1,
        )
        selected_lane = self.analysis.lanes.currentRow()
        focused = self._last_review_focus
        if not same_project:
            self._output_location = ""
            self._crop_history.clear()
            self._crop_history_index = 0
            self.analysis.reset_history()
            self._last_review_focus = None
            self._pending_review_focus = None
        self._project = project
        self.history_label.setText(
            f"从归档恢复 · {len(project.archive_sources)} 个来源 · "
            f"{len(project.imported_runs)} 条历史运行。"
            "历史数值须通过资产核验；重新计算将建立本机运行。"
            if isinstance(project, WBRestoredProject) and project.archive_sources
            else ""
        )
        self.history_label.setToolTip(
            "\n".join(s.archive.sha256 for s in project.archive_sources)
            if isinstance(project, WBRestoredProject)
            else ""
        )
        self.metadata.clear_preview()
        self.laboratory_layout.restore(project)
        present = {row.source.sha256 for row in project.rows if row.source}
        self._thumbnails = {key: icon for key, icon in self._thumbnails.items() if key in present}
        self.ocr.restore(project)
        self.normalization.restore(project)
        self.analysis.set_source_context(None)
        self.analysis.show_plan(None)
        self.analysis.invalidate()
        self.ocr.result_view.invalidate()
        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)
        if selected_index < 0:
            self._source_preview = None
            self.canvas.set_image(PreviewRaster("", 0, 0, 0, 0, b"", 0, ()))
            self.canvas.set_lanes(())
            self.canvas.set_regions(())
        self.suggestions.show_suggestion(None, None, project.template.crop_height)
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
                    if row.source and row.source.sha256 in self._thumbnails:
                        item.setIcon(self._thumbnails[row.source.sha256])
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
            self.table.setRowHeight(
                index, 68 if row.source and row.source.sha256 in self._thumbnails else 28
            )
        self.name.setToolTip(self.history_label.text())
        self.history_label.hide()
        if selected_index >= 0:
            self.table.setCurrentCell(selected_index, 0)
        self._loading = False
        if selected_index >= 0:
            self.show_analysis(selected_index)
            if self._source_preview is not None:
                self.analysis.set_source_preview(self._source_preview)
            if 0 <= selected_lane < self.analysis.lanes.rowCount():
                self.analysis.lanes.setCurrentCell(selected_lane, 0)
            self._overlay()
            if focused is not None and focused.isVisible():
                if self.isEnabled():
                    focused.setFocus()
                else:
                    self._pending_review_focus = focused
        self._refresh_analysis_sources()
        self._filter_rows(select_visible=False)
        self._refresh_source_workspace()

    def rebuild_layout(self) -> None:
        try:
            project = self.project(include_layout=False)
            project = with_figure_layout(
                project, initial_composition(project), self.laboratory_layout.layout_style()
            )
            self.set_project(project)
            self._edited()
            self.status.setText("已按原图行重建版式；每行独立，可明确设置横向段。")
        except ValueError as error:
            self.status.setText(str(error))

    def _metadata_preview(self, mode: str) -> None:
        try:
            project = self.project()
            selected = tuple(
                project.rows[index.row()].row_id
                for index in self.table.selectionModel().selectedRows()
                if not self.table.isRowHidden(index.row())
            )
            self.metadata.build_preview(mode, project, selected)
        except ValueError as error:
            self.metadata.status.setText(str(error))

    def _metadata_apply(self) -> None:
        try:
            updated = self.metadata.apply(self.project())
            self.set_project(updated)
            self._edited()
            self.metadata.status.setText("元信息已应用；N / 空泳道变化的行须重新审核和定量。")
        except ValueError as error:
            self.metadata.status.setText(str(error))

    def has_thumbnail(self, sha256: str) -> bool:
        return sha256 in self._thumbnails

    def install_thumbnail(self, raster: PreviewRaster) -> None:
        if (
            not 1 <= raster.preview_width <= 128
            or not 1 <= raster.preview_height <= 128
            or len(raster.pixels) != raster.preview_width * raster.preview_height
        ):
            raise ValueError("缩略图超出 128 像素预算或数据不完整")
        matches = [
            i
            for i, row in enumerate(self._project.rows)
            if row.source
            and row.source.sha256 == raster.sha256
            and row.width == raster.width
            and row.height == raster.height
            and row.bit_depth == raster.bit_depth
        ]
        if not matches:
            return
        icon = QIcon(
            QPixmap.fromImage(
                QImage(
                    raster.pixels,
                    raster.preview_width,
                    raster.preview_height,
                    raster.preview_width,
                    QImage.Format.Format_Grayscale8,
                ).copy()
            )
        )
        self._thumbnails[raster.sha256] = icon
        self._loading = True
        for i in matches:
            item = self.table.item(i, 0)
            if item is not None:
                item.setIcon(icon)
                self.table.setRowHeight(i, 68)
        self._loading = False
        self._refresh_source_workspace()

    def _edited(self) -> None:
        if self._loading:
            return
        self.generation += 1
        self.analysis.invalidate()
        self.ocr.result_view.invalidate()
        self.normalization.result_view.invalidate()
        self.preview_label.clear_render()
        self._rendered_preview = None
        self.changed.emit()
        self._overlay()

    def _cell_changed(self, row: int, column: int) -> None:
        if self._loading:
            return
        if column in (3, 4, 5, 6, 7, 8):
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
            try:
                self._project = self.project()
            except ValueError as error:
                self.status.setText(str(error))
                self.table.blockSignals(True)
                self.table.setCurrentCell(_previous_row, max(0, _previous_column))
                self.table.blockSignals(False)
                self._refresh_analysis_sources()
                return
            self._refresh_analysis_sources()
            self._source_preview = None
            self.canvas.set_image(PreviewRaster("", 0, 0, 0, 0, b"", 0, ()))
            self.canvas.set_lanes(())
            self.canvas.set_regions(())
            self.analysis.clear_source_preview()
            self.show_analysis(row)
            self._overlay()
            self.source_requested.emit(self._project.rows[row].row_id)

    def show_analysis(self, index: int | None = None) -> None:
        index = self.table.currentRow() if index is None else index
        project = self.project()
        # Commit editor values before show_plan clears its dirty flag.
        self._project = project
        plan = None
        if isinstance(project, WBAnalysisProject) and 0 <= index < len(project.rows):
            plan = next(
                (
                    p
                    for p in project.analyses
                    if p.row_id == project.rows[index].row_id and analysis_is_current(project, p)
                ),
                None,
            )
        loaded = next(
            (
                r
                for r in self._results
                if plan and plan.run and r.row_id == plan.row_id and r.run_id == plan.run.run_id
            ),
            None,
        )
        self.analysis.set_source_context(
            project.rows[index] if 0 <= index < len(project.rows) else None
        )
        self.analysis.show_plan(plan, loaded)
        if plan and 0 <= index < len(project.rows):
            row = project.rows[index]
            self.analysis.message.setText(
                f"{row.figure} · {row.protein} · {row.filename}；修改边界/基线后重新计算"
            )

    def configure_analysis(self) -> None:
        try:
            project = self.project()
            index = self.table.currentRow()
            if not 0 <= index < len(project.rows):
                raise ValueError("请选择已审核的行")
            plan = make_row_analysis(
                project,
                project.rows[index].row_id,
                "dark" if self.analysis.polarity.currentIndex() == 0 else "light",
            )
            self._project = set_row_analysis(project, plan)
            self.analysis.show_plan(plan)
            row = project.rows[index]
            self.analysis.message.setText(
                f"{row.figure} · {row.protein} · {row.filename}；先计算曲线或填写边界"
            )
            self._edited()
        except ValueError as error:
            self.status.setText(str(error))

    def bind_ocr(self, row_id: str, target_id: str) -> None:
        try:
            project = self.project()
            if not isinstance(project, WBProjectOCR):
                raise ValueError("请先导入拼图并识别")
            index = self.ocr.table.currentRow()
            self.set_project(bind_project_ocr_row(project, row_id, target_id or None))
            self.ocr.table.setCurrentCell(index, 0)
            self.ocr.changed.emit()
        except ValueError as error:
            self.status.setText(str(error))

    def configure_normalization(self, target_id: str, reference_id: str, kind: str) -> None:
        try:
            if kind not in ("housekeeping", "phospho_total"):
                raise ValueError("请选择参照类型")
            project = self.project()
            plan = make_normalization_plan(project, target_id, reference_id, kind)
            plans = project.normalizations if isinstance(project, WBNormalizedProject) else ()
            project = project_with_normalizations(
                project, (*(p for p in plans if p.target.row_id != target_id), plan)
            )
            self.set_project(project)
            self.normalization.selector.setCurrentIndex(
                self.normalization.selector.findData(target_id)
            )
            self.normalization.selector.activated.emit(self.normalization.selector.currentIndex())
            self._edited()
        except ValueError as error:
            self.status.setText(str(error))

    def remove_normalization(self, target_id: str) -> None:
        try:
            project = self.project()
            if isinstance(project, WBNormalizedProject):
                self.set_project(
                    project_with_normalizations(
                        project,
                        tuple(p for p in project.normalizations if p.target.row_id != target_id),
                    )
                )
                self._edited()
        except ValueError as error:
            self.status.setText(str(error))

    def install_results(self, results: tuple[LoadedProjectResult, ...]) -> None:
        self._results = results
        self.show_analysis()

    def selected_row(self) -> FigureRow | None:
        index = self.table.currentRow()
        return self.project().rows[index] if 0 <= index < len(self._project.rows) else None

    @property
    def source_preview(self) -> PreviewRaster | None:
        """Display-only raster; never a quantitative input."""
        return self._source_preview

    def set_source_preview(self, preview: PreviewRaster) -> None:
        index = self.table.currentRow()
        row = self._project.rows[index] if 0 <= index < len(self._project.rows) else None
        if row is None or row.source is None or row.source.sha256 != preview.sha256:
            return
        self._source_preview = preview
        self.canvas.set_image(preview)
        self.analysis.set_source_preview(preview)
        if row.roi is not None:
            margin_x = max(20, row.roi.width // 8)
            margin_y = max(30, row.roi.y1 - row.roi.y0)
            self.canvas.set_view_region(
                LaneROI(
                    row.row_id,
                    max(0, row.roi.x0 - margin_x),
                    max(0, row.roi.y0 - margin_y),
                    min(row.width, row.roi.x1 + margin_x),
                    min(row.height, row.roi.y1 + margin_y),
                )
            )
        self._overlay()

    def _overlay(self) -> None:
        if self._loading:
            return
        try:
            row = self.selected_row()
            suggestion = (
                next((s for s in self._project.suggestions if row and s.row_id == row.row_id), None)
                if isinstance(self._project, WBReviewProject)
                else None
            )
            height = (
                self.project().crop_height_for(row) if row else self.numbers["crop_height"].value()
            )
            self.suggestions.show_suggestion(row, suggestion, height)
            # Metadata/ROI edits can stale a plan without changing the selected row.
            # Only inspect a valid draft; incomplete annotation text remains editable.
            if self.analysis.plan and not analysis_is_current(self.project(), self.analysis.plan):
                self.analysis.show_plan(None)
            self.analysis.set_source_context(row)
            regions: list[LaneROI] = []
            if suggestion and suggestion.result:
                result = suggestion.result
                if result.membrane:
                    regions.append(replace(result.membrane, lane_id="膜候选"))
                if result.marker:
                    regions.append(replace(result.marker, lane_id="左 Marker 待核对"))
                index = self.suggestions.candidates.currentIndex()
                if 0 <= index < len(result.candidates):
                    regions.append(
                        replace(result.candidates[index].roi, lane_id=f"候选 {index + 1}")
                    )
            self.canvas.set_crop(row.roi if row else None)
            self._refresh_source_workspace()
            self.canvas.set_regions(tuple(regions))
            self.canvas.set_lanes(
                tuple(
                    replace(lane, lane_id=f"泳道 {i}")
                    for i, lane in enumerate(fixed_lane_grid(row.roi, row.lane_count), 1)
                )
                if row and row.roi
                else ()
            )
        except ValueError as error:
            self.canvas.set_regions(())
            self.canvas.set_lanes(())
            self.status.setText(str(error))

    def install_suggestions(self, project: WBReviewProject) -> None:
        """Host has checked generation; table fields are unchanged by suggestion recording."""
        self._project = project
        self._edited()
        self._filter_rows()

    def focus_membrane(self) -> None:
        try:
            row = self.selected_row()
            if row is None:
                return
            region = row.roi
            if isinstance(self._project, WBReviewProject):
                suggestion = next(
                    (s for s in self._project.suggestions if s.row_id == row.row_id), None
                )
                if suggestion and suggestion.result and suggestion.result.membrane:
                    region = suggestion.result.membrane
            if region:
                self.canvas.set_view_region(region)
        except ValueError as error:
            self.status.setText(str(error))

    def apply_candidate(self, index: int) -> None:
        try:
            row = self.selected_row()
            if row is None:
                return
            project = apply_crop_suggestion(self.project(), row.row_id, index)
            self._project = project
            updated = next(r for r in project.rows if r.row_id == row.row_id)
            assert updated.roi is not None
            self._drawn((updated.roi.x0, updated.roi.y0, updated.roi.x1, updated.roi.y1))
            self.status.setText("已应用候选；请核对 Marker、各泳道位置及目标条带，再确认所选行。")
        except ValueError as error:
            self.status.setText(str(error))

    def set_crop_lane_count(self, lane_count: int) -> None:
        """Atomically resize original-coordinate crop and N with one undo entry."""
        current = self.selected_row()
        if current is None or current.roi is None:
            raise ValueError("请先选择有裁剪框的原图")
        if any(number > lane_count for number in current.empty_lanes):
            raise ValueError("泳道数不能小于已标记空泳道的位置")
        crop = resize_crop_for_lane_count(current.roi, lane_count, current.width, current.height)
        self._drawn((crop.x0, crop.y0, crop.x1, crop.y1), lane_count=lane_count)

    def _drawn(self, coords: tuple[int, int, int, int], *, lane_count: int | None = None) -> None:
        index = self.table.currentRow()
        if index < 0 or self._project.rows[index].source is None:
            return
        current = self.selected_row()
        previous_roi = current.roi if current else None
        previous_count = current.lane_count if current else 1
        next_count = previous_count if lane_count is None else lane_count
        if previous_roi and not self._restoring_crop:
            before = (previous_roi.x0, previous_roi.y0, previous_roi.x1, previous_roi.y1)
            if before != coords or previous_count != next_count:
                self._crop_history[self._crop_history_index :] = [
                    (self._project.rows[index].row_id, before, coords, previous_count, next_count)
                ]
                self._crop_history_index += 1
        self._loading = True
        count_item = self.table.item(index, 3)
        if count_item:
            count_item.setText(str(next_count))
        for column, value in enumerate(coords, start=4):
            item = self.table.item(index, column)
            if item:
                item.setText(str(value))
        self._loading = False
        if (
            previous_roi is not None
            and not self.laboratory_layout.active
            and coords[3] - coords[1] != self._project.template.crop_height
        ):
            # A graphical resize is a per-row geometry change, never a global crop-height edit.
            project = self.project()
            project = with_figure_layout(project, initial_composition(project))
            self._project = project
            self.laboratory_layout.restore(project)
        self._cell_changed(index, 4)

    def undo_review(self) -> None:
        if self.analysis.plot.hasFocus():
            self.analysis.undo_curve()
        else:
            self._crop_history_step(-1)

    def redo_review(self) -> None:
        if self.analysis.plot.hasFocus():
            self.analysis.redo_curve()
        else:
            self._crop_history_step(1)

    def _crop_history_step(self, step: int) -> None:
        target = self._crop_history_index - 1 if step < 0 else self._crop_history_index
        if not 0 <= target < len(self._crop_history):
            return
        row_id, before, after, before_count, after_count = self._crop_history[target]
        index = next((i for i, row in enumerate(self._project.rows) if row.row_id == row_id), -1)
        if index < 0:
            return
        # Later metadata edits (especially empty slots) may invalidate an older N.
        # Validate the complete target row before changing cells, selection or history.
        try:
            current = self.project().rows[index]
            restored = current.model_dump()
            restored.update(
                roi=LaneROI(row_id, *(before if step < 0 else after)),
                lane_count=before_count if step < 0 else after_count,
                reviewed=False,
            )
            FigureRow.model_validate(restored)
        except ValueError as error:
            self.status.setText(f"无法恢复裁剪：{error}")
            return
        self.table.setCurrentCell(index, 0)
        if self.table.currentRow() != index:
            return
        self._restoring_crop = True
        try:
            self._drawn(
                before if step < 0 else after,
                lane_count=before_count if step < 0 else after_count,
            )
            self._crop_history_index += step
        finally:
            self._restoring_crop = False

    def refresh_attention(self) -> None:
        """Refresh source statuses after the host installs verified result cells."""
        self._refresh_source_workspace()
        self._filter_rows(select_visible=False)

    def _filter_rows(self, *_args: object, select_visible: bool = True) -> None:
        mode = self.filter.currentIndex()
        suggestions = (
            {s.row_id: s for s in self._project.suggestions}
            if isinstance(self._project, WBReviewProject)
            else {}
        )
        for i, row in enumerate(self._project.rows):
            suggestion = suggestions.get(row.row_id)
            result = suggestion.result if suggestion else None
            review = self.table.item(i, 9)
            checked = bool(review and review.checkState() == Qt.CheckState.Checked)
            hidden = (
                (mode == 1 and not self._needs_attention(i))
                or (mode == 2 and not checked)
                or (mode == 3 and not self._text(i, 8))
                or (mode == 4 and row.source is not None)
                or (
                    mode == 5
                    and not (
                        result
                        and any(c.weak_lanes or c.possible_empty_lanes for c in result.candidates)
                    )
                )
                or (mode == 6 and not (result and len(result.candidates) > 1))
                or (
                    mode == 7
                    and not (
                        suggestion and (suggestion.error or (result and not result.candidates))
                    )
                )
            )
            self.table.setRowHidden(i, bool(hidden))
            if i < self.source_list.count():
                self.source_list.item(i).setHidden(bool(hidden))

        current = self.table.currentRow()
        if select_visible and current >= 0 and self.table.isRowHidden(current):
            visible = next(
                (i for i in range(self.table.rowCount()) if not self.table.isRowHidden(i)), -1
            )
            if visible >= 0:
                self._select_analysis_source(visible)

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
            updated = project.model_copy(update={"rows": rows, "figure_order": order})
            if isinstance(project, WBAnalysisProject):
                updated = updated.model_copy(
                    update={
                        "analyses": tuple(
                            p for p in project.analyses if any(r.row_id == p.row_id for r in rows)
                        )
                    }
                )
            if isinstance(project, WBReviewProject):
                updated = project_with_suggestions(
                    updated,
                    tuple(
                        s for s in project.suggestions if any(r.row_id == s.row_id for r in rows)
                    ),
                )
            self.set_project(updated)
            self._edited()
        except ValueError as error:
            self.status.setText(str(error))

    def confirm_row(self, row_id: str) -> None:
        """Confirm exactly the bound row, irrespective of retained table selection."""
        project = self.project()
        index = next((i for i, row in enumerate(project.rows) if row.row_id == row_id), None)
        if index is None or self.table.isRowHidden(index):
            raise ValueError("当前原图行不可审核")
        row = project.rows[index]
        if row.source is None or row.roi is None:
            raise ValueError("请先选定原图裁剪范围")
        item = self.table.item(index, 9)
        if item is None:
            raise ValueError("当前原图行缺少审核控件")
        item.setCheckState(Qt.CheckState.Checked)

    def confirm_selected(self) -> None:
        for index in self.table.selectionModel().selectedRows():
            item = self.table.item(index.row(), 9)
            if item and not self.table.isRowHidden(index.row()):
                item.setCheckState(Qt.CheckState.Checked)

    @property
    def rendered_preview(self) -> FigureRender | None:
        """Exact current display render, including source hit regions in its manifest."""
        return self._rendered_preview

    def show_render(self, rendered: FigureRender) -> None:
        self._rendered_preview = rendered
        image = QImage(
            rendered.rgb,
            rendered.width,
            rendered.height,
            rendered.width * 3,
            QImage.Format.Format_RGB888,
        ).copy()
        self.preview_label.set_render(QPixmap.fromImage(image))
