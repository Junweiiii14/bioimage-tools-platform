"""Fixed-lane annotation editor and verified project table; no I/O or numerical work."""

from dataclasses import replace
from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.analysis import AnalysisRequest, BandAnnotation, LaneAnnotation
from wb_tool.application.desktop_data import PreviewRaster
from wb_tool.application.figure_project import FigureRow
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    ProjectRowAnalysis,
    ProjectTableCell,
)
from wb_tool.domain.quantify import BandBounds, Baseline
from wb_tool.ui.canvas import ImageCanvas
from wb_tool.ui.project_results import ProjectResultsView
from wb_tool.ui.view import ProfilePlot


class ProjectAnalysisPanel(QWidget):
    changed = Signal()
    configure_requested = Signal()
    run_requested = Signal(bool)
    refresh_requested = Signal()
    export_requested = Signal()
    lane_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.plan: ProjectRowAnalysis | None = None
        self.loaded: LoadedProjectResult | None = None
        self.dirty = False
        self._loading = False
        self._syncing = False
        self._cells: tuple[ProjectTableCell, ...] = ()
        self.source_row: FigureRow | None = None
        self.source_preview_sha256 = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.message = QLabel("选择已审核的原图行，配置定量；首次可先计算曲线。")
        self.message.setWordWrap(True)
        self.message.hide()
        self.evidence_tabs = QTabWidget()
        layout.addWidget(self.evidence_tabs, 1)
        workbench = QWidget()
        workbench.setObjectName("evidenceWorkbench")
        columns = QHBoxLayout(workbench)
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(10)
        self.controls = QWidget()
        self.controls.setObjectName("evidenceControls")
        self.controls_layout = QVBoxLayout(self.controls)
        self.controls_layout.setSpacing(5)
        self.source_heading = QLabel("原图来源")
        self.source_heading.setObjectName("evidenceHeading")
        self.controls_layout.addWidget(self.source_heading)
        self.source_info = QLabel("选择原图后查看来源与位深。")
        self.source_info.setObjectName("evidenceSummary")
        self.source_info.setWordWrap(True)
        self.controls_layout.addWidget(self.source_info)
        self.lane_selector = QComboBox()
        self.polarity = QComboBox()
        self.polarity.addItems(["暗条带", "亮条带"])
        form = QFormLayout()
        form.addRow("当前泳道", self.lane_selector)
        form.addRow("信号极性", self.polarity)
        self.controls_layout.addLayout(form)
        pairs = QGridLayout()
        pairs.setHorizontalSpacing(8)
        pairs.setVerticalSpacing(3)
        self.lane_fields: dict[int, QLineEdit] = {}
        for column, label in ((2, "左边界 L"), (3, "右边界 R"), (4, "基线左值"), (5, "基线右值")):
            edit = QLineEdit()
            edit.setPlaceholderText("留空")
            edit.setAccessibleName(label)
            edit.textEdited.connect(partial(self._edit_lane_field, column))
            self.lane_fields[column] = edit
            pair_row = 0 if column < 4 else 2
            pair_column = column % 2
            pairs.addWidget(QLabel(label), pair_row, pair_column)
            pairs.addWidget(edit, pair_row + 1, pair_column)
        self.controls_layout.addLayout(pairs)
        self.included = QCheckBox("包含当前泳道")
        self.included.toggled.connect(self._edit_included)
        self.controls_layout.addWidget(self.included)
        bounds_help = QLabel(
            "边界：裁剪内 0 起算，含两端。\n边界双空＝未检测；基线双空＝端点。修改后需重算。"
        )
        bounds_help.setWordWrap(True)
        self.controls_layout.addWidget(bounds_help)
        configure = QPushButton("配置 / 重置所选行")
        configure.clicked.connect(self.configure_requested)
        self.controls_layout.addWidget(configure)
        self.controls_layout.addStretch()
        control_scroll = QScrollArea()
        control_scroll.setWidgetResizable(True)
        control_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        control_scroll.setFixedWidth(220)
        control_scroll.setWidget(self.controls)
        columns.addWidget(control_scroll)
        stage = QWidget()
        stage.setObjectName("evidenceStage")
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(0, 0, 0, 0)
        stage_layout.addWidget(QLabel("原图与测量证据"))
        self.source_canvas = ImageCanvas(empty_message="选择原图后显示来源证据；裁剪请返回第一步。")
        self.source_canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.source_canvas.setMinimumSize(280, 190)
        self.plot = ProfilePlot()
        evidence_split = QSplitter(Qt.Orientation.Vertical)
        evidence_split.addWidget(self.source_canvas)
        curve = QWidget()
        curve_layout = QVBoxLayout(curve)
        curve_layout.setContentsMargins(0, 4, 0, 0)
        curve_layout.addWidget(QLabel("当前泳道原始曲线 · 仅显示已核验结果"))
        curve_layout.addWidget(self.plot, 1)
        evidence_split.addWidget(curve)
        evidence_split.setSizes([340, 210])
        evidence_split.setChildrenCollapsible(False)
        stage_layout.addWidget(evidence_split, 1)
        columns.addWidget(stage, 1)
        review = QWidget()
        review.setObjectName("evidenceReview")
        review_layout = QVBoxLayout(review)
        heading = QLabel("当前结果与复核")
        heading.setObjectName("evidenceHeading")
        review_layout.addWidget(heading)
        self.summary = QTableWidget(0, 4)
        self.summary.setHorizontalHeaderLabels(["泳道", "有效信号", "状态", "原始积分\n（待复核）"])
        self.summary.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.summary.verticalHeader().hide()
        self.summary.setMinimumHeight(130)
        self.summary.setMaximumHeight(180)
        review_layout.addWidget(self.summary)
        self.review_note = QLabel(
            "原始积分保留待复核测量，不等于有效信号，也不进入归一化。修改参数后需重新计算。"
        )
        self.review_note.setWordWrap(True)
        review_layout.addWidget(self.review_note)
        for text, callback in (
            ("计算所选行", lambda: self.run_requested.emit(False)),
            ("计算全部已配置行", lambda: self.run_requested.emit(True)),
            ("刷新项目表", self.refresh_requested.emit),
            ("导出结果 XLSX / CSV", self.export_requested.emit),
        ):
            button = QPushButton(text)
            if text == "计算所选行":
                button.setObjectName("primaryAction")
            button.clicked.connect(callback)
            review_layout.addWidget(button)
        review_layout.addStretch()
        review_scroll = QScrollArea()
        review_scroll.setWidgetResizable(True)
        review_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        review_scroll.setFixedWidth(250)
        review_scroll.setWidget(review)
        columns.addWidget(review_scroll)
        self.evidence_tabs.addTab(workbench, "证据工作台")
        self.lanes = QTableWidget(0, 6)
        self.lanes.setHorizontalHeaderLabels(
            ["泳道", "包含", "边界左", "边界右", "基线左", "基线右"]
        )
        self.lanes.horizontalHeader().setMinimumSectionSize(48)
        self.lanes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.evidence_tabs.addTab(self.lanes, "全部泳道参数")
        self.result_view = ProjectResultsView()
        self.results = self.result_view.table
        self.evidence_tabs.addTab(self.result_view, "完整项目结果")
        self.lanes.cellChanged.connect(self._edited)
        self.lanes.cellChanged.connect(self._sync_lane_editor)
        self.polarity.currentIndexChanged.connect(self._edited)
        self.lanes.currentCellChanged.connect(self._plot)
        self.lanes.currentCellChanged.connect(self._sync_lane_editor)
        self.lane_selector.activated.connect(self._select_lane)

    def set_source_context(self, row: FigureRow | None) -> None:
        if (
            row is None
            or self.source_row is None
            or row.row_id != self.source_row.row_id
            or row.source != self.source_row.source
        ):
            self.clear_source_preview()
        self.source_row = row
        self.source_info.setText(
            f"{row.protein} · {row.bit_depth} 位 · N = {row.lane_count}"
            if row and row.source
            else "所选行缺少原图。"
            if row
            else "选择原图后查看来源与位深。"
        )
        self.source_info.setToolTip(
            f"{row.filename}\n{row.figure} · 原图 SHA256：{row.source.sha256}"
            if row and row.source
            else "无原图来源"
        )
        self._show_summary()

    def clear_source_preview(self) -> None:
        self.source_preview_sha256 = ""
        self.source_canvas.set_image(PreviewRaster("", 0, 0, 0, 0, b"", 0, ()))
        self.source_canvas.set_lanes(())
        self.source_canvas.set_regions(())

    def set_source_preview(self, preview: PreviewRaster) -> None:
        if (
            self.source_row
            and self.source_row.source
            and self.source_row.source.sha256 == preview.sha256
        ):
            self.source_preview_sha256 = preview.sha256
            self.source_canvas.set_image(preview)
            self._source_overlay()

    def _source_overlay(self) -> None:
        if (
            self.plan is None
            or self.source_row is None
            or self.source_row.source is None
            or self.plan.row_id != self.source_row.row_id
            or self.plan.request.source_sha256 != self.source_row.source.sha256
        ):
            self.source_canvas.set_lanes(())
            return
        self.source_canvas.set_regions(())
        self.source_canvas.set_lanes(
            tuple(
                replace(
                    lane.roi,
                    lane_id=f"泳道 {i + 1}" + (" · 当前" if i == self.lanes.currentRow() else ""),
                )
                for i, lane in enumerate(self.plan.request.lanes)
            )
            if self.plan
            else ()
        )

    def _select_lane(self, index: int) -> None:
        self.lanes.setCurrentCell(index, 0)

    def _edit_lane_field(self, column: int, text: str) -> None:
        item = self.lanes.item(self.lanes.currentRow(), column)
        if not self._syncing and item is not None:
            item.setText(text)

    def _edit_included(self, included: bool) -> None:
        item = self.lanes.item(self.lanes.currentRow(), 1)
        if not self._syncing and item is not None and item.flags() & Qt.ItemFlag.ItemIsEnabled:
            item.setCheckState(Qt.CheckState.Checked if included else Qt.CheckState.Unchecked)

    def _sync_lane_editor(self, *_args: object) -> None:
        if self._loading:
            return
        self._syncing = True
        row = self.lanes.currentRow()
        self.lane_selector.setCurrentIndex(row)
        for column, editor in self.lane_fields.items():
            item = self.lanes.item(row, column)
            editor.setText(item.text() if item else "")
            editor.setEnabled(item is not None)
        included = self.lanes.item(row, 1)
        self.included.setChecked(bool(included and included.checkState() == Qt.CheckState.Checked))
        self.included.setEnabled(bool(included and included.flags() & Qt.ItemFlag.ItemIsEnabled))
        self._syncing = False
        self._source_overlay()
        self.lane_changed.emit()

    def _show_summary(self) -> None:
        row = self.source_row
        cells = {c.lane_index: c for c in self._cells if row and c.row_id == row.row_id}
        self.summary.setRowCount(row.lane_count if row else 0)
        labels = {
            "valid": "有效",
            "not_detected": "未检测",
            "excluded": "排除",
            "not_run": "待计算",
            "unconfigured": "未配置",
            "result_unavailable": "结果不可用",
            "quality_review": "需质量复核",
            "failed": "失败",
            "stale": "已过期",
            "pending_review": "待审核",
            "cancelled": "已取消",
            "interrupted": "已中断",
            "invalid": "无效",
            "missing_source": "缺少原图",
        }
        for i in range(self.summary.rowCount()):
            cell = cells.get(i + 1)
            status = (
                cell.status
                if cell
                else "excluded"
                if row and i + 1 in row.empty_lanes
                else "not_run"
                if self.plan
                else "unconfigured"
            )
            for column, value in enumerate(
                (
                    str(i + 1),
                    format(cell.value, ".12g") if cell and cell.value is not None else "—",
                    labels.get(status, status),
                    format(cell.raw_integral, ".12g")
                    if cell and cell.raw_integral is not None
                    else "—",
                )
            ):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(cell.reason if cell else "尚无当前参数的核验结果")
                self.summary.setItem(i, column, item)

    def _edited(self, *_args: object) -> None:
        if not self._loading and self.plan is not None:
            self.dirty = True
            self.invalidate()
            self.changed.emit()

    def request(self) -> AnalysisRequest | None:
        if self.plan is None or not self.dirty:
            return None
        lanes: list[LaneAnnotation] = []
        for i, lane in enumerate(self.plan.request.lanes):
            values = [self.lanes.item(i, c) for c in range(2, 6)]
            texts = [v.text().strip() if v else "" for v in values]
            if bool(texts[0]) != bool(texts[1]) or bool(texts[2]) != bool(texts[3]):
                raise ValueError(f"泳道 {i + 1} 的边界/基线必须成对填写或同时留空")
            bounds = BandBounds(int(texts[0]), int(texts[1])) if texts[0] else None
            baseline = Baseline(float(texts[2]), float(texts[3])) if texts[2] else None
            if baseline is not None and bounds is None:
                raise ValueError("人工基线需要明确的条带边界")
            item = self.lanes.item(i, 1)
            included = bool(item and item.checkState() == Qt.CheckState.Checked)
            lanes.append(
                replace(lane, bands=(BandAnnotation("target", bounds, baseline, included),))
            )
        return replace(
            self.plan.request,
            polarity="dark" if self.polarity.currentIndex() == 0 else "light",
            lanes=tuple(lanes),
        )

    def show_plan(
        self, plan: ProjectRowAnalysis | None, loaded: LoadedProjectResult | None = None
    ) -> None:
        self._loading = True
        self.plan, self.loaded, self.dirty = plan, loaded, False
        self.lanes.setRowCount(len(plan.request.lanes) if plan else 0)
        if plan:
            self.polarity.setCurrentIndex(0 if plan.request.polarity == "dark" else 1)
            self.message.setText(
                f"行 {plan.row_id} · 原图 {plan.request.source_sha256[:16]} · "
                "修改边界/基线后重新计算"
            )
            for i, lane in enumerate(plan.request.lanes):
                band = lane.bands[0]
                texts = [
                    str(i + 1),
                    "",
                    *(map(str, (band.bounds.left, band.bounds.right)) if band.bounds else ("", "")),
                    *(
                        map(str, (band.baseline.left_value, band.baseline.right_value))
                        if band.baseline
                        else ("", "")
                    ),
                ]
                for c, text in enumerate(texts):
                    item = QTableWidgetItem(text)
                    if c == 0:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if c == 1:
                        item.setFlags(
                            (item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                            & ~Qt.ItemFlag.ItemIsEditable
                        )
                        item.setCheckState(
                            Qt.CheckState.Checked if band.included else Qt.CheckState.Unchecked
                        )
                        if i + 1 in plan.empty_lanes:
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                            item.setToolTip("预标空泳道保留位置且排除")
                    self.lanes.setItem(i, c, item)
        else:
            self.message.setText("所选行尚未配置，或裁剪/泳道已改变。请审核后重新配置。")
        self.lane_selector.clear()
        if plan:
            self.lane_selector.addItems(
                [
                    f"泳道 {i + 1}" + (" · 排除" if i + 1 in plan.empty_lanes else "")
                    for i in range(len(plan.request.lanes))
                ]
            )
        self._loading = False
        self.lanes.setCurrentCell(0, 0)
        self._sync_lane_editor()
        self._show_summary()
        self._plot()

    def invalidate(self) -> None:
        self.result_view.invalidate()
        self._cells = ()
        self._show_summary()
        self.loaded = None
        self._plot()

    def show_cells(self, cells: tuple[ProjectTableCell, ...]) -> None:
        self._cells = cells
        self.result_view.show_cells(cells)
        self._show_summary()

    def _plot(self, *_args: object) -> None:
        self.plot.values, self.plot.measurements = (), ()
        i = self.lanes.currentRow()
        if (
            self.loaded
            and self.plan
            and self.loaded.result.request == self.plan.request
            and 0 <= i < len(self.loaded.result.lanes)
        ):
            lane = self.loaded.result.lanes[i]
            if lane.profiles:
                self.plot.values = lane.profiles.quantitative
            self.plot.measurements = tuple(b.measurement for b in lane.bands if b.measurement)
        self.plot.update()
