"""Multi-image row review and template editing; host owns assets and asynchronous work."""

from dataclasses import replace
from uuid import uuid4

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
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
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI
from wb_tool.ui.canvas import ImageCanvas
from wb_tool.ui.crop_suggestions import CropSuggestionPanel
from wb_tool.ui.normalization import NormalizationPanel
from wb_tool.ui.project_analysis import ProjectAnalysisPanel
from wb_tool.ui.project_metadata import ProjectMetadataPanel
from wb_tool.ui.project_ocr import ProjectOCRPanel


class FigureProjectView(QWidget):
    changed = Signal()
    source_requested = Signal(str)
    preview_requested = Signal()
    export_requested = Signal()
    image_export_requested = Signal()
    font_requested = Signal()
    detection_requested = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.generation = 0
        self._loading = False
        self._project = WBFigureProject(project_id=uuid4().hex)
        self._thumbnails: dict[str, QIcon] = {}
        root = QVBoxLayout(self)
        self.name = QLineEdit("WB 项目")
        root.addWidget(self.name)
        self.status = QLabel("批量导入原图，填写 Fig/蛋白，框选整行范围并复核。")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.history_label = QLabel()
        self.history_label.setWordWrap(True)
        root.addWidget(self.history_label)
        actions = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.addItems(
            [
                "全部行",
                "待审核",
                "已审核",
                "预标空泳道",
                "缺图",
                "建议有弱/空槽",
                "多候选",
                "无候选/失败",
            ]
        )
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
        self.table.setIconSize(QSize(96, 64))
        for index in range(3, 8):
            self.table.setColumnWidth(index, 60)
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(9, 65)
        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.table)
        tabs = QTabWidget()
        self.canvas = ImageCanvas()
        self.suggestions = CropSuggestionPanel()
        self.suggestions.run_requested.connect(self.detection_requested)
        self.suggestions.apply_requested.connect(self.apply_candidate)
        self.suggestions.candidate_changed.connect(self._overlay)
        self.suggestions.focus_requested.connect(self.focus_membrane)
        self.suggestions.reset_view_requested.connect(lambda: self.canvas.set_view_region(None))
        source_page = QWidget()
        source_layout = QVBoxLayout(source_page)
        source_layout.addWidget(self.suggestions)
        source_layout.addWidget(self.canvas, 1)
        tabs.addTab(source_page, "原图与固定泳道")
        self.metadata = ProjectMetadataPanel()
        self.metadata.preview_requested.connect(self._metadata_preview)
        self.metadata.apply_requested.connect(self._metadata_apply)
        tabs.addTab(self.metadata, "批量元信息")
        self.analysis = ProjectAnalysisPanel()
        self.analysis.configure_requested.connect(self.configure_analysis)
        self.analysis.changed.connect(self._edited)
        self._results: tuple[LoadedProjectResult, ...] = ()
        tabs.addTab(self.analysis, "原图定量与项目结果表")
        self.ocr = ProjectOCRPanel()
        self.ocr.changed.connect(self._edited)
        self.ocr.binding_requested.connect(self.bind_ocr)
        tabs.addTab(self.ocr, "拼图 OCR 与结果关联")
        self.normalization = NormalizationPanel()
        self.normalization.changed.connect(self._edited)
        self.normalization.configure_requested.connect(self.configure_normalization)
        self.normalization.remove_requested.connect(self.remove_normalization)
        tabs.addTab(self.normalization, "样本对应与归一化")
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
        self.image_export_button = QPushButton("导出拼图 TIFF / PNG")
        self.image_export_button.setToolTip("用于展示和排版；需要重新打开的完整项目请导出ZIP。")
        preview.clicked.connect(self.preview_requested)
        export.clicked.connect(self.export_requested)
        self.image_export_button.clicked.connect(self.image_export_requested)
        bottom.addWidget(preview)
        bottom.addWidget(self.image_export_button)
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
        if isinstance(self._project, WBRestoredProject):
            project = with_archive_history(
                project, self._project.archive_sources, self._project.imported_runs
            )
        return project

    def set_project(self, project: WBFigureProject) -> None:
        self._loading = True
        self._project = project
        self.history_label.setText(
            f"从归档恢复 · {len(project.archive_sources)} 个来源 · "
            f"{len(project.imported_runs)} 条历史运行。"
            "历史数值须通过资产核验；重新计算将建立本机运行。"
            if isinstance(project, WBRestoredProject)
            else ""
        )
        self.history_label.setToolTip(
            "\n".join(s.archive.sha256 for s in project.archive_sources)
            if isinstance(project, WBRestoredProject)
            else ""
        )
        self.metadata.clear_preview()
        present = {row.source.sha256 for row in project.rows if row.source}
        self._thumbnails = {key: icon for key, icon in self._thumbnails.items() if key in present}
        self.ocr.restore(project)
        self.normalization.restore(project)
        self.analysis.show_plan(None)
        self.analysis.invalidate()
        self.ocr.result_view.invalidate()
        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)
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
        self._loading = False
        self._filter_rows()

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

    def _edited(self) -> None:
        if self._loading:
            return
        self.generation += 1
        self.analysis.invalidate()
        self.ocr.result_view.invalidate()
        self.normalization.result_view.invalidate()
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("内容已修改，请重新生成预览")
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
                return
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

    def set_source_preview(self, preview: PreviewRaster) -> None:
        self.canvas.set_image(preview)
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
            self.suggestions.show_suggestion(row, suggestion, self.numbers["crop_height"].value())
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
                (mode == 1 and checked)
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
