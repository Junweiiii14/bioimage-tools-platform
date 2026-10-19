"""WB controls and result presentation; no file reads, computation or database access."""

from dataclasses import replace
from uuid import uuid4

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen, QPolygonF
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.analysis import (
    AnalysisRequest,
    AnalysisResult,
    BandAnnotation,
    LaneAnnotation,
)
from wb_tool.application.desktop_data import PreviewRaster
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.quantify import BandBounds, Baseline, ProfileMeasurement
from wb_tool.ui.canvas import ImageCanvas


class ProfilePlot(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.values: tuple[float, ...] = ()
        self.measurements: tuple[ProfileMeasurement, ...] = ()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#f4f7fb"))
        painter.setPen(QColor("#344256"))
        painter.drawText(12, 18, "原始均值剖面（定量极性）；横轴：泳道内像素位置")
        if len(self.values) < 2:
            return
        maximum = (
            max(
                (
                    *self.values,
                    *(
                        value
                        for measurement in self.measurements
                        for value in (
                            measurement.baseline.left_value,
                            measurement.baseline.right_value,
                        )
                    ),
                )
            )
            or 1.0
        )
        points = QPolygonF(
            [
                QPointF(
                    12 + i * (self.width() - 24) / (len(self.values) - 1),
                    self.height() - 12 - value * (self.height() - 40) / maximum,
                )
                for i, value in enumerate(self.values)
            ]
        )
        painter.setPen(QPen(QColor("#176ac6"), 2))
        painter.drawPolyline(points)
        for measurement in self.measurements:
            left, right = measurement.bounds.left, measurement.bounds.right
            x0 = 12 + left * (self.width() - 24) / (len(self.values) - 1)
            x1 = 12 + right * (self.width() - 24) / (len(self.values) - 1)
            painter.setPen(QPen(QColor("#db4f42"), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x0, 30), QPointF(x0, self.height() - 12))
            painter.drawLine(QPointF(x1, 30), QPointF(x1, self.height() - 12))
            painter.setPen(QPen(QColor("#db4f42"), 2))
            painter.drawLine(
                QPointF(
                    x0,
                    self.height()
                    - 12
                    - measurement.baseline.left_value * (self.height() - 40) / maximum,
                ),
                QPointF(
                    x1,
                    self.height()
                    - 12
                    - measurement.baseline.right_value * (self.height() - 40) / maximum,
                ),
            )


class WBView(QWidget):
    changed = Signal()
    save_requested = Signal()
    analyze_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.raster: PreviewRaster | None = None
        self.lanes: list[LaneAnnotation] = []
        self.generation = 0
        self._loading = False
        self._validation_error = ""
        self._result: AnalysisResult | None = None
        self.canvas = ImageCanvas()
        self.canvas.roi_drawn.connect(self._drawn)
        self.polarity = QComboBox()
        self.polarity.addItems(["暗条带", "亮条带"])
        self.polarity.currentIndexChanged.connect(self._edited)
        self.lane_selector = QComboBox()
        self.lane_selector.currentIndexChanged.connect(self._select_lane)
        self.coordinates = [QSpinBox() for _ in range(4)]
        for control in self.coordinates:
            control.setMaximum(1000000)
            control.valueChanged.connect(self._roi_edited)
        self.band_selector = QComboBox()
        self.band_selector.currentIndexChanged.connect(self._select_band)
        self.detected = QCheckBox("已标注边界")
        self.included = QCheckBox("纳入定量")
        self.manual_baseline = QCheckBox("人工基线（否则采用边界端点）")
        self.bounds = [QSpinBox(), QSpinBox()]
        for control in self.bounds:
            control.setMaximum(1000000)
            control.valueChanged.connect(self._band_edited)
        self.baseline = [QDoubleSpinBox(), QDoubleSpinBox()]
        for control in self.baseline:
            control.setMaximum(65535)
            control.setDecimals(3)
            control.valueChanged.connect(self._band_edited)
        for control in (self.detected, self.included, self.manual_baseline):
            control.toggled.connect(self._band_edited)
        add_band = QPushButton("添加条带")
        add_band.clicked.connect(self._add_band)
        remove_lane = QPushButton("移除所选泳道")
        remove_lane.clicked.connect(self._remove_lane)
        self.save_button = QPushButton("保存草稿")
        self.analyze_button = QPushButton("计算并复核")
        self.cancel_button = QPushButton("取消计算")
        self.save_button.clicked.connect(self.save_requested)
        self.analyze_button.clicked.connect(self.analyze_requested)
        self.cancel_button.clicked.connect(self.cancel_requested)
        self.cancel_button.setEnabled(False)
        form = QFormLayout()
        form.addRow("条带极性", self.polarity)
        form.addRow("泳道", self.lane_selector)
        for label, control in zip(
            ("左 x0", "上 y0", "右 x1（不含）", "下 y1（不含）"), self.coordinates, strict=True
        ):
            form.addRow(label, control)
        form.addRow(remove_lane)
        form.addRow("条带", self.band_selector)
        form.addRow(add_band)
        form.addRow(self.detected)
        form.addRow(self.included)
        form.addRow("左边界（含）", self.bounds[0])
        form.addRow("右边界（含）", self.bounds[1])
        form.addRow(self.manual_baseline)
        form.addRow("基线左值", self.baseline[0])
        form.addRow("基线右值", self.baseline[1])
        sidebar = QWidget()
        sidebar.setLayout(form)
        splitter = QSplitter()
        splitter.addWidget(self.canvas)
        splitter.addWidget(sidebar)
        splitter.setStretchFactor(0, 1)
        self.plot = ProfilePlot()
        self.results = QTableWidget(0, 5)
        self.results.setHorizontalHeaderLabels(
            ["泳道", "条带", "有效信号", "状态", "原因/质量提示"]
        )
        self.results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.status = QLabel("导入图像后，在画布上拖出泳道；条带边界相对于该泳道。")
        self.status.setWordWrap(True)
        actions = QHBoxLayout()
        for button in (self.save_button, self.analyze_button, self.cancel_button):
            actions.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addWidget(splitter, 3)
        layout.addWidget(self.plot, 1)
        layout.addWidget(self.results, 1)
        layout.addLayout(actions)

    def set_image(self, raster: PreviewRaster, request: AnalysisRequest | None = None) -> None:
        self._result = None
        self._validation_error = ""
        self.raster = raster
        self.canvas.set_image(raster)
        self._loading = True
        self.lanes = list(request.lanes) if request is not None else []
        self.polarity.setCurrentIndex(
            1 if request is not None and request.polarity == "light" else 0
        )
        self._loading = False
        self._refresh_lanes()
        self.status.setText(
            f"{raster.width} × {raster.height} · {raster.bit_depth} 位 · 原始 TIFF；预览仅用于显示"
        )
        self.status.setToolTip("；".join(raster.warnings))
        self.results.setRowCount(0)
        self.plot.values = ()
        self.plot.update()
        self.generation += 1

    def request(self, revision: int) -> AnalysisRequest:
        if self._validation_error:
            raise ValueError(self._validation_error)
        if self.raster is None:
            raise ValueError("请先导入图像")
        li, bi = self.lane_selector.currentIndex(), self.band_selector.currentIndex()
        if li >= 0:
            lane = self.lanes[li]
            visible_roi = LaneROI(
                lane.roi.lane_id, *(control.value() for control in self.coordinates)
            )
            if visible_roi != lane.roi:
                raise ValueError("当前泳道字段尚未形成有效 ROI")
            if bi >= 0:
                band = lane.bands[bi]
                bounds = (
                    BandBounds(*(control.value() for control in self.bounds))
                    if self.detected.isChecked()
                    else None
                )
                baseline = (
                    Baseline(*(control.value() for control in self.baseline))
                    if self.manual_baseline.isChecked() and bounds
                    else None
                )
                visible_band = BandAnnotation(
                    band.band_id, bounds, baseline, self.included.isChecked()
                )
                if visible_band != band:
                    raise ValueError("当前条带字段尚未形成有效标注")
        return AnalysisRequest(
            self.raster.sha256,
            revision,
            "light" if self.polarity.currentIndex() else "dark",
            tuple(self.lanes),
        )

    def _edited(self) -> None:
        if self._loading:
            return
        self.generation += 1
        self.results.setRowCount(0)
        self.plot.values = ()
        self.plot.measurements = ()
        self._result = None
        self.plot.update()
        self.changed.emit()

    def _refresh_lanes(self) -> None:
        index = self.lane_selector.currentIndex()
        self._loading = True
        self.lane_selector.clear()
        self.lane_selector.addItems([lane.roi.lane_id for lane in self.lanes])
        self.lane_selector.setCurrentIndex(min(max(index, 0), len(self.lanes) - 1))
        self.canvas.set_lanes(tuple(lane.roi for lane in self.lanes))
        self._loading = False
        self._select_lane()

    def _drawn(self, coordinates: tuple[int, int, int, int]) -> None:
        lane = LaneAnnotation(LaneROI("L" + uuid4().hex[:6], *coordinates), ())
        self.lanes.append(lane)
        self._refresh_lanes()
        self.lane_selector.setCurrentIndex(len(self.lanes) - 1)
        self._edited()

    def _select_lane(self) -> None:
        if self._loading:
            return
        index = self.lane_selector.currentIndex()
        if index < 0:
            return
        self._loading = True
        lane = self.lanes[index]
        for control, value in zip(
            self.coordinates, (lane.roi.x0, lane.roi.y0, lane.roi.x1, lane.roi.y1), strict=True
        ):
            control.setValue(value)
        self.band_selector.clear()
        self.band_selector.addItems([band.band_id for band in lane.bands])
        self._loading = False
        self._select_band()
        self._update_plot()

    def _roi_edited(self) -> None:
        index = self.lane_selector.currentIndex()
        if self._loading or index < 0:
            return
        old = self.lanes[index]
        try:
            roi = LaneROI(old.roi.lane_id, *(control.value() for control in self.coordinates))
        except ValueError as error:
            self._validation_error = str(error)
            self.status.setText(str(error))
            return
        self.lanes[index] = replace(old, roi=roi)
        self._validation_error = ""
        self.canvas.set_lanes(tuple(lane.roi for lane in self.lanes))
        self._edited()

    def _add_band(self) -> None:
        index = self.lane_selector.currentIndex()
        if index < 0:
            self.status.setText("请先绘制泳道")
            return
        lane = self.lanes[index]
        self.lanes[index] = replace(
            lane, bands=(*lane.bands, BandAnnotation("B" + uuid4().hex[:6], None))
        )
        self._select_lane()
        self.band_selector.setCurrentIndex(len(self.lanes[index].bands) - 1)
        self._edited()

    def _remove_lane(self) -> None:
        index = self.lane_selector.currentIndex()
        if index >= 0:
            self.lanes.pop(index)
            self._refresh_lanes()
            self._edited()

    def _select_band(self) -> None:
        li, bi = self.lane_selector.currentIndex(), self.band_selector.currentIndex()
        if self._loading or li < 0 or bi < 0:
            return
        band = self.lanes[li].bands[bi]
        self._loading = True
        self.detected.setChecked(band.bounds is not None)
        self.included.setChecked(band.included)
        self.manual_baseline.setChecked(band.baseline is not None)
        self.bounds[0].setValue(band.bounds.left if band.bounds else 0)
        self.bounds[1].setValue(band.bounds.right if band.bounds else 1)
        for control, value in zip(
            self.baseline,
            (band.baseline.left_value, band.baseline.right_value) if band.baseline else (0.0, 0.0),
            strict=True,
        ):
            control.setValue(value)
        self._loading = False

    def _band_edited(self) -> None:
        li, bi = self.lane_selector.currentIndex(), self.band_selector.currentIndex()
        if self._loading or li < 0 or bi < 0:
            return
        lane = self.lanes[li]
        old = lane.bands[bi]
        try:
            bounds = (
                BandBounds(self.bounds[0].value(), self.bounds[1].value())
                if self.detected.isChecked()
                else None
            )
            baseline = (
                Baseline(self.baseline[0].value(), self.baseline[1].value())
                if self.manual_baseline.isChecked() and bounds
                else None
            )
            band = BandAnnotation(old.band_id, bounds, baseline, self.included.isChecked())
        except ValueError as error:
            self._validation_error = str(error)
            self.status.setText(str(error))
            return
        bands = list(lane.bands)
        bands[bi] = band
        self.lanes[li] = replace(lane, bands=tuple(bands))
        self._validation_error = ""
        self._edited()

    def show_result(self, result: AnalysisResult) -> None:
        self._result = result
        self.results.setRowCount(0)
        labels = {
            "valid": "有效",
            "invalid": "无效",
            "quality_review": "需质量复核",
            "excluded": "已排除",
            "not_detected": "未标注/未检出",
        }
        for lane in result.lanes:
            for band in lane.bands:
                row = self.results.rowCount()
                self.results.insertRow(row)
                for column, value in enumerate(
                    (
                        lane.roi.lane_id,
                        band.annotation.band_id,
                        f"{band.signal:.6g}" if band.signal is not None else "—",
                        labels[band.status],
                        band.reason or ", ".join(band.quality_flags),
                    )
                ):
                    self.results.setItem(row, column, QTableWidgetItem(value))
        self._update_plot()
        self.status.setText(
            f"结果已保存 · 修订 {result.request.revision}；红线：边界与基线；单位 intensity*pixel。"
        )

    def _update_plot(self) -> None:
        selected = self.lane_selector.currentIndex()
        result = self._result
        if result is not None and 0 <= selected < len(result.lanes):
            lane = result.lanes[selected]
            profiles = lane.profiles
            if profiles is not None:
                self.plot.values = profiles.quantitative
                self.plot.measurements = tuple(
                    band.measurement for band in lane.bands if band.measurement is not None
                )
                self.plot.update()
