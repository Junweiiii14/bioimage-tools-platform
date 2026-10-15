"""Display-only raster with original-pixel ROI coordinates."""

from math import ceil, floor

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from wb_tool.application.desktop_data import PreviewRaster
from wb_tool.domain.lanes import LaneROI


class ImageCanvas(QWidget):
    roi_drawn = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        empty_message: str = "导入 TIFF 后拖出泳道矩形",
    ) -> None:
        super().__init__(parent)
        self.empty_message = empty_message
        self.setMinimumSize(300, 240)
        self._image = QImage()
        self._size: tuple[int, int] = (0, 0)
        self._view_region: LaneROI | None = None
        self._lanes: tuple[LaneROI, ...] = ()
        self._regions: tuple[LaneROI, ...] = ()
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
        self._view_region = None
        self._anchor = None
        self.update()

    def set_lanes(self, lanes: tuple[LaneROI, ...]) -> None:
        self._lanes = lanes
        self.update()

    def set_regions(self, regions: tuple[LaneROI, ...]) -> None:
        self._regions = regions
        self.update()

    def set_view_region(self, region: LaneROI | None) -> None:
        if region and (region.x1 > self._size[0] or region.y1 > self._size[1]):
            raise ValueError("显示范围超出原图")
        self._view_region = region
        self._anchor = None
        self.update()

    def _view_bounds(self) -> tuple[int, int, int, int]:
        region = self._view_region
        return (
            (region.x0, region.y0, region.width, region.y1 - region.y0)
            if region
            else (0, 0, *self._size)
        )

    def image_rect(self) -> QRectF:
        _, _, width, height = self._view_bounds()
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
        x, y, width, height = self._view_bounds()
        return QPointF(
            x + max(0.0, min(float(width), (position.x() - rect.x()) * width / rect.width())),
            y + max(0.0, min(float(height), (position.y() - rect.y()) * height / rect.height())),
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#18212d"))
        rect = self.image_rect()
        if self._image.isNull():
            painter.setPen(QColor("#e1e7ef"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.empty_message)
            return
        x, y, width, height = self._view_bounds()
        sx, sy = self._image.width() / self._size[0], self._image.height() / self._size[1]
        painter.drawImage(rect, self._image, QRectF(x * sx, y * sy, width * sx, height * sy))
        painter.setClipRect(rect.adjusted(-2, -18, 2, 2))
        for lane, color, label_y in [
            *((r, "#ffbb52", 14 if i == 1 else -4) for i, r in enumerate(self._regions)),
            *((r, "#36d9b0", 14) for r in self._lanes),
        ]:
            painter.setPen(QPen(QColor(color), 2))
            box = QRectF(
                rect.x() + (lane.x0 - x) * rect.width() / width,
                rect.y() + (lane.y0 - y) * rect.height() / height,
                (lane.x1 - lane.x0) * rect.width() / width,
                (lane.y1 - lane.y0) * rect.height() / height,
            )
            painter.drawRect(box)
            label_position = box.topLeft() + QPointF(4, label_y)
            label_box = QRectF(painter.fontMetrics().boundingRect(lane.lane_id))
            label_box.translate(label_position)
            painter.fillRect(label_box.adjusted(-3, -1, 3, 2), QColor("#172126"))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(label_position, lane.lane_id)

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
