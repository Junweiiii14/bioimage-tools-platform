"""Fixed-lane annotation editor and verified project table; no I/O or numerical work."""

from dataclasses import replace
from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
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
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.quantify import BandBounds, Baseline
from wb_tool.ui.canvas import ImageCanvas
from wb_tool.ui.editable_profile import EditableProfilePlot
from wb_tool.ui.project_results import ProjectResultsView


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
        self.message = QLabel("选择已审核的原图行，配置定量；首次可先计算曲线。", self)
        self.message.setWordWrap(True)
        self.message.hide()
        self.controls = QWidget()
        self.controls.setObjectName("evidenceControls")
        self.controls_layout = QVBoxLayout(self.controls)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(8)
        self.source_heading = QLabel("泳道与测量", self)
        self.source_heading.hide()
        self.source_info = QLabel(self)
        self.source_info.setWordWrap(True)
        self.source_info.hide()
        self.lane_selector = QComboBox()
        self.lane_selector.setAccessibleName("当前泳道")
        self.controls_layout.addWidget(self.lane_selector)
        self.polarity = QComboBox()
        self.polarity.addItems(["暗条带", "亮条带"])
        self.advanced = QWidget()
        form = QFormLayout(self.advanced)
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow("信号极性", self.polarity)
        self.lane_fields: dict[int, QLineEdit] = {}
        for column, label in ((2, "左边界"), (3, "右边界"), (4, "基线左值"), (5, "基线右值")):
            edit = QLineEdit()
            edit.setPlaceholderText("自动 / 未指定")
            edit.setAccessibleName(label)
            edit.textEdited.connect(partial(self._edit_lane_field, column))
            self.lane_fields[column] = edit
            form.addRow(label, edit)
        self.included = QCheckBox("包含当前泳道")
        self.included.toggled.connect(self._edit_included)
        form.addRow(self.included)
        configure = QPushButton("重新配置当前行")
        configure.clicked.connect(self.configure_requested)
        form.addRow(configure)
        self.advanced_toggle = QCheckBox("高级测量参数")
        self.advanced_toggle.toggled.connect(self.advanced.setVisible)
        self.controls_layout.addWidget(self.advanced_toggle)
        self.controls_layout.addWidget(self.advanced)
        self.advanced.hide()
        self.recalculate_button = QPushButton("重新测量当前图")
        self.recalculate_button.clicked.connect(lambda: self.run_requested.emit(False))
        self.controls_layout.addWidget(self.recalculate_button)
        self.source_canvas = ImageCanvas(self, empty_message="选择原图查看来源")
        self.source_canvas.hide()
        self.plot = EditableProfilePlot()
        self.plot.edit_committed.connect(self._curve_edited)
        self.curve_editor = QWidget()
        curve_layout = QVBoxLayout(self.curve_editor)
        curve_layout.setContentsMargins(0, 4, 0, 0)
        curve_layout.addWidget(self.plot, 1)
        curve_tools = QHBoxLayout()
        curve_tools.addWidget(QLabel("拖动边界 / 基线 · Tab 换手柄 · 方向键微调"), 1)
        self.undo_button = QPushButton("撤销曲线调整")
        self.redo_button = QPushButton("重做")
        self.undo_button.clicked.connect(lambda: self._history_step(-1))
        self.redo_button.clicked.connect(lambda: self._history_step(1))
        curve_tools.addWidget(self.undo_button)
        curve_tools.addWidget(self.redo_button)
        curve_layout.addLayout(curve_tools)
        self.curve_editor.setMaximumHeight(300)
        self._history: list[tuple[int, tuple[str, ...], tuple[str, ...]]] = []
        self._history_index = 0
        self._history_store: dict[
            str, tuple[str, list[tuple[int, tuple[str, ...], tuple[str, ...]]], int]
        ] = {}
        self._profile_cache: dict[tuple[str, int], tuple[float, ...]] = {}
        self._profile_cache_identity = ""
        self._selected_lanes: dict[str, int] = {}
        self._profile_values: tuple[float, ...] = ()
        self._profile_lane = -1
        self.review_controls = QWidget()
        review_layout = QVBoxLayout(self.review_controls)
        review_layout.setContentsMargins(0, 0, 0, 0)
        self.review_note = QLabel("选择泳道查看测量状态与原因")
        self.review_note.setWordWrap(True)
        self.review_note.setObjectName("reviewReason")
        review_layout.addWidget(self.review_note)
        self.summary = QTableWidget(0, 4)
        self.summary.setHorizontalHeaderLabels(["泳道", "有效信号", "状态", "原始积分"])
        self.summary.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.summary.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.summary.verticalHeader().hide()
        self.summary.setMaximumHeight(150)
        self.summary.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.summary.currentCellChanged.connect(self._summary_selected)
        review_layout.addWidget(self.summary)
        self.lanes = QTableWidget(0, 6, self)
        self.lanes.setHorizontalHeaderLabels(
            ["泳道", "包含", "边界左", "边界右", "基线左", "基线右"]
        )
        self.lanes.hide()
        self.result_view = ProjectResultsView()
        self.results = self.result_view.table
        layout.addWidget(self.result_view, 1)
        self.lanes.cellChanged.connect(self._edited)
        self.lanes.cellChanged.connect(self._sync_lane_editor)
        self.polarity.currentIndexChanged.connect(self._polarity_edited)
        self.lanes.currentCellChanged.connect(self._plot)
        self.lanes.currentCellChanged.connect(self._sync_lane_editor)
        self.lane_selector.activated.connect(self._select_lane)

    def _summary_selected(self, row: int, *_args: int) -> None:
        if not self._loading:
            self._select_lane(row)

    def _field_text(self, row: int, column: int) -> str:
        item = self.lanes.item(row, column)
        return item.text() if item else ""

    def row_needs_attention(self, row_id: str) -> bool:
        cells = [cell for cell in self._cells if cell.row_id == row_id]
        return not cells or any(cell.status not in ("valid", "excluded") for cell in cells)

    @staticmethod
    def _history_identity(plan: ProjectRowAnalysis) -> str:
        return repr(
            (
                plan.row_id,
                plan.request.source_sha256,
                plan.request.polarity,
                tuple(lane.roi for lane in plan.request.lanes),
                plan.empty_lanes,
            )
        )

    def reset_history(self) -> None:
        """A different project must not inherit another project's edit or profile evidence."""
        self._history_store.clear()
        self._selected_lanes.clear()
        self._profile_cache.clear()
        self._profile_cache_identity = ""
        self._history.clear()
        self._history_index = 0
        self._profile_values = ()

    def _restore_history(self, plan: ProjectRowAnalysis | None) -> None:
        if self.plan is not None:
            self._history_store[self.plan.row_id] = (
                self._history_identity(self.plan),
                self._history.copy(),
                self._history_index,
            )
        self._history, self._history_index = [], 0
        if plan is None:
            return
        saved = self._history_store.get(plan.row_id)
        if saved is None or saved[0] != self._history_identity(plan):
            self._history_store.pop(plan.row_id, None)
            return
        _, history, index = saved
        # An external reset of annotations with identical geometry must not
        # accidentally splice an incompatible command history into the new plan.
        expected: dict[int, tuple[str, ...]] = {}
        for lane, before, _after in history:
            expected.setdefault(lane, before)
        for lane, _before, after in history[:index]:
            expected[lane] = after
        for lane, fields in expected.items():
            if lane >= len(plan.request.lanes):
                return
            band = plan.request.lanes[lane].bands[0]
            actual = (
                band.bounds.left if band.bounds else None,
                band.bounds.right if band.bounds else None,
                band.baseline.left_value if band.baseline else None,
                band.baseline.right_value if band.baseline else None,
            )
            if tuple(float(value) if value else None for value in fields) != actual:
                return
        self._history, self._history_index = history.copy(), index

    def _polarity_edited(self) -> None:
        if not self._loading:
            self._history.clear()
            self._history_index = 0
            if self.plan:
                self._history_store.pop(self.plan.row_id, None)
        self._profile_values = ()
        self._edited()

    def _curve_edited(self, bounds: object, baseline: object) -> None:
        if not isinstance(bounds, BandBounds) or (
            baseline is not None and not isinstance(baseline, Baseline)
        ):
            return
        row = self.lanes.currentRow()
        if self.plan is None or row < 0:
            return
        old = tuple(self._field_text(row, c) for c in range(2, 6))
        new = (
            str(bounds.left),
            str(bounds.right),
            str(baseline.left_value) if baseline else "",
            str(baseline.right_value) if baseline else "",
        )
        if old == new:
            return
        self._history[self._history_index :] = [(row, old, new)]
        self._history_index += 1
        self._apply_curve_fields(row, new)

    def undo_curve(self) -> None:
        self._history_step(-1)

    def redo_curve(self) -> None:
        self._history_step(1)

    def _history_step(self, step: int) -> None:
        target = self._history_index - 1 if step < 0 else self._history_index
        if not 0 <= target < len(self._history):
            return
        row, old, new = self._history[target]
        self._history_index += step
        self.lanes.setCurrentCell(row, 0)
        self._apply_curve_fields(row, old if step < 0 else new)

    def _apply_curve_fields(self, row: int, values: tuple[str, ...]) -> None:
        self._loading = True
        for column, value in zip(range(2, 6), values, strict=True):
            item = self.lanes.item(row, column)
            if item is not None:
                item.setText(value)
        self._loading = False
        self._edited()
        self._sync_lane_editor()
        self._plot()
        self.undo_button.setEnabled(self._history_index > 0)
        self.redo_button.setEnabled(self._history_index < len(self._history))

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
            row = self.source_row
            if row.roi is not None:
                margin_x = max(20, row.roi.width // 8)
                margin_y = max(30, row.roi.y1 - row.roi.y0)
                self.source_canvas.set_view_region(
                    LaneROI(
                        row.row_id,
                        max(0, row.roi.x0 - margin_x),
                        max(0, row.roi.y0 - margin_y),
                        min(row.width, row.roi.x1 + margin_x),
                        min(row.height, row.roi.y1 + margin_y),
                    )
                )
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
        if index != self.lanes.currentRow():
            self._profile_values = ()
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
        if self.plan and row >= 0:
            self._selected_lanes[self.plan.row_id] = row
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
        self._show_reason()
        self.lane_changed.emit()

    def _show_summary(self) -> None:
        self.summary.blockSignals(True)
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
                    format(cell.value, ".4g") if cell and cell.value is not None else "—",
                    labels.get(status, status),
                    format(cell.raw_integral, ".4g")
                    if cell and cell.raw_integral is not None
                    else "—",
                )
            ):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(cell.reason if cell else "尚无当前参数的核验结果")
                self.summary.setItem(i, column, item)
        self.summary.resizeRowsToContents()
        self.summary.blockSignals(False)
        self._show_reason()

    def _show_reason(self) -> None:
        row = self.source_row
        cell = next(
            (
                c
                for c in self._cells
                if row and c.row_id == row.row_id and c.lane_index == self.lanes.currentRow() + 1
            ),
            None,
        )
        if cell:
            reason = cell.reason or "当前参数的测量已核验。"
            action = (
                "查看原图与曲线。质量警告不能通过确认裁剪消除；原始积分不是有效信号。"
                if cell.status == "quality_review"
                else "修改后需重新测量，旧值不会继续作为当前结果。"
                if cell.status not in ("valid", "excluded")
                else ""
            )
            self.review_note.setText(reason + ("\n\n" + action if action else ""))
        else:
            self.review_note.setText(
                "调整后等待重新测量。"
                if self.dirty
                else "尚无当前参数的核验结果。自动处理后在这里查看状态。"
            )

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
                replace(
                    lane,
                    bands=(BandAnnotation("target", bounds, baseline, included), *lane.bands[1:]),
                )
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
        self._restore_history(plan)
        self.plan, self.loaded, self.dirty = plan, loaded, False
        self.undo_button.setEnabled(self._history_index > 0)
        self.redo_button.setEnabled(self._history_index < len(self._history))
        self._profile_values = ()
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
        selected = self._selected_lanes.get(plan.row_id, 0) if plan else 0
        self.lanes.setCurrentCell(min(selected, self.lanes.rowCount() - 1), 0)
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
        if self._profile_lane != i:
            self._profile_values = ()
        self._profile_lane = i
        cache_key = (self._history_identity(self.plan), i) if self.plan else None
        if self.plan and self.polarity.currentIndex() != (
            0 if self.plan.request.polarity == "dark" else 1
        ):
            cache_key = None
            self._profile_values = ()
        if cache_key and cache_key[0] != self._profile_cache_identity:
            # Bound retained evidence to the current source/geometry only.
            self._profile_cache.clear()
            self._profile_cache_identity = cache_key[0]
        if cache_key and not self.loaded:
            self._profile_values = self._profile_cache.get(cache_key, ())
        if (
            self.loaded
            and self.plan
            and self.loaded.result.request == self.plan.request
            and 0 <= i < len(self.loaded.result.lanes)
        ):
            lane = self.loaded.result.lanes[i]
            if lane.profiles:
                self._profile_values = lane.profiles.quantitative
                if cache_key:
                    self._profile_cache[cache_key] = self._profile_values
            self.plot.measurements = tuple(b.measurement for b in lane.bands if b.measurement)
        self.plot.values = self._profile_values
        if self.plan and 0 <= i < len(self.plan.request.lanes):
            try:
                texts = [self._field_text(i, c).strip() for c in range(2, 6)]
                bounds = BandBounds(int(texts[0]), int(texts[1])) if texts[0] and texts[1] else None
                baseline = (
                    Baseline(float(texts[2]), float(texts[3])) if texts[2] and texts[3] else None
                )
                self.plot.set_annotation(bounds, baseline)
            except ValueError:
                self.plot.set_annotation(None, None)
        else:
            self.plot.set_annotation(None, None)
        self.plot.update()
