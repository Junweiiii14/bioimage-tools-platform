"""Display-only raster with original-pixel ROI coordinates."""

from math import ceil, floor

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from wb_tool.application.desktop_data import PreviewRaster
from wb_tool.domain.lanes import LaneROI


class ImageCanvas(QWidget):
    roi_drawn = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(300, 240)
        self._image = QImage()
        self._size = (0, 0)
        self._lanes: tuple[LaneROI, ...] = ()
        self._anchor: QPointF | None = None
        self.setMouseTracking(True)

    def set_image(self, raster: PreviewRaster) -> None:
        self._image = QImage(
            raster.pixels,
            raster.preview_width,
            raster.preview_height,
            raster.preview_width,
            QImage.Format.Format_Grayscale8,
        ).copy()
        self._size = (raster.width, raster.height)
        self.update()

    def set_lanes(self, lanes: tuple[LaneROI, ...]) -> None:
        self._lanes = lanes
        self.update()

    def image_rect(self) -> QRectF:
        width, height = self._size
        if not width or not height:
            return QRectF()
        scale = min((self.width() - 20) / width, (self.height() - 20) / height)
        return QRectF(
            (self.width() - width * scale) / 2,
            (self.height() - height * scale) / 2,
            width * scale,
            height * scale,
        )

    def _pixel(self, position: QPointF) -> QPointF:
        rect = self.image_rect()
        width, height = self._size
        return QPointF(
            max(0.0, min(float(width), (position.x() - rect.x()) * width / rect.width())),
            max(0.0, min(float(height), (position.y() - rect.y()) * height / rect.height())),
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#18212d"))
        rect = self.image_rect()
        if self._image.isNull():
            painter.setPen(QColor("#e1e7ef"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "导入 TIFF 后拖出泳道矩形")
            return
        painter.drawImage(rect, self._image)
        painter.setPen(QPen(QColor("#36d9b0"), 2))
        width, height = self._size
        for lane in self._lanes:
            box = QRectF(
                rect.x() + lane.x0 * rect.width() / width,
                rect.y() + lane.y0 * rect.height() / height,
                (lane.x1 - lane.x0) * rect.width() / width,
                (lane.y1 - lane.y0) * rect.height() / height,
            )
            painter.drawRect(box)
            painter.drawText(box.topLeft() + QPointF(2, 14), lane.lane_id)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.image_rect().contains(
            event.position()
        ):
            self._anchor = self._pixel(event.position())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._anchor is None or event.button() != Qt.MouseButton.LeftButton:
            return
        end = self._pixel(event.position())
        start, self._anchor = self._anchor, None
        x0, y0 = floor(min(start.x(), end.x())), floor(min(start.y(), end.y()))
        x1, y1 = ceil(max(start.x(), end.x())), ceil(max(start.y(), end.y()))
        if x1 > x0 and y1 - y0 >= 2:
            self.roi_drawn.emit((x0, y0, x1, y1))
