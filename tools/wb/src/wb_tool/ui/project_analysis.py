"""Fixed-lane annotation editor and verified project table; no I/O or numerical work."""

from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.analysis import AnalysisRequest, BandAnnotation, LaneAnnotation
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    ProjectRowAnalysis,
    ProjectTableCell,
)
from wb_tool.domain.quantify import BandBounds, Baseline
from wb_tool.ui.view import ProfilePlot


class ProjectAnalysisPanel(QWidget):
    changed = Signal()
    configure_requested = Signal()
    run_requested = Signal(bool)
    refresh_requested = Signal()
    export_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.plan: ProjectRowAnalysis | None = None
        self.loaded: LoadedProjectResult | None = None
        self.dirty = False
        self._loading = False
        self._cells: tuple[ProjectTableCell, ...] = ()
        layout = QVBoxLayout(self)
        self.message = QLabel("选择已审核的原图行，配置定量。首次可先计算曲线，再填写条带边界。")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        actions = QHBoxLayout()
        self.polarity = QComboBox()
        self.polarity.addItems(["暗条带", "亮条带"])
        actions.addWidget(self.polarity)
        for text, callback in (
            ("配置 / 重置所选行", self.configure_requested.emit),
            ("计算所选行", lambda: self.run_requested.emit(False)),
            ("计算全部已配置行", lambda: self.run_requested.emit(True)),
            ("刷新项目表", self.refresh_requested.emit),
            ("导出结果 XLSX", self.export_requested.emit),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        layout.addWidget(
            QLabel(
                "边界为裁剪内的行号，含两端，0 起算。两端留空表示未检测；"
                "基线两端都留空使用边界端点值。修改后需重新计算。"
            )
        )
        self.lanes = QTableWidget(0, 6)
        self.lanes.setHorizontalHeaderLabels(
            ["泳道", "包含", "边界左", "边界右", "基线左", "基线右"]
        )
        layout.addWidget(self.lanes)
        self.plot = ProfilePlot()
        layout.addWidget(self.plot)
        self.results = QTableWidget(0, 7)
        self.results.setHorizontalHeaderLabels(
            ["Fig", "蛋白", "泳道", "积分", "状态", "原因", "原图 / 运行"]
        )
        layout.addWidget(self.results)
        paging = QHBoxLayout()
        self.page = QSpinBox()
        self.page.setRange(1, 1)
        self.page_label = QLabel("0 个泳道结果")
        paging.addWidget(QLabel("结果页（每页 200 个泳道）"))
        paging.addWidget(self.page)
        paging.addWidget(self.page_label)
        layout.addLayout(paging)
        self.page.valueChanged.connect(self._show_page)
        self.lanes.cellChanged.connect(self._edited)
        self.polarity.currentIndexChanged.connect(self._edited)
        self.lanes.currentCellChanged.connect(self._plot)

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
        self._loading = False
        self.lanes.setCurrentCell(0, 0)
        self._plot()

    def invalidate(self) -> None:
        self._cells = ()
        self.results.setRowCount(0)
        self.page_label.setText("内容改变，请计算或刷新结果表")
        self.loaded = None
        self._plot()

    def show_cells(self, cells: tuple[ProjectTableCell, ...]) -> None:
        self._cells = cells
        self.page.setMaximum(max(1, (len(cells) + 199) // 200))
        self.page_label.setText(f"共 {len(cells)} 个泳道结果")
        self._show_page()

    def _show_page(self, *_args: object) -> None:
        start = (self.page.value() - 1) * 200
        cells = self._cells[start : start + 200]
        self.results.setRowCount(len(cells))
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
                )
            ):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(
                    f"row={cell.row_id}; lane={cell.lane_id}; revision={cell.request_revision}"
                )
                self.results.setItem(i, c, item)

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
