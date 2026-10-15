"""Display-only raster with original-pixel ROI coordinates."""

from math import ceil, floor

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import QWidget

from wb_tool.application.desktop_data import PreviewRaster
from wb_tool.domain.lanes import LaneROI


class ImageCanvas(QWidget):
    roi_drawn = Signal(object)
    lane_selected = Signal(int)

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
        self._crop: LaneROI | None = None
        self._drag_crop: LaneROI | None = None
        self._drag_mode = ""
        self._zoom = 1.0
        self._pan = QPointF()
        self._pan_anchor: QPointF | None = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("原图裁剪；方向键移动，Alt 加方向键调整右下边缘，Shift 加速")

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
        self._crop = None
        self._drag_crop = None
        self.reset_zoom()
        self.update()

    def set_crop(self, crop: LaneROI | None) -> None:
        """Enable direct editing of a source crop, independently of evidence overlays."""
        self._crop = crop
        self._drag_crop = None
        self.update()

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        self._pan = QPointF()
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
        self.reset_zoom()
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
        scale = min((self.width() - 20) / width, (self.height() - 20) / height) * self._zoom
        return QRectF(
            (self.width() - width * scale) / 2 + self._pan.x(),
            (self.height() - height * scale) / 2 + self._pan.y(),
            width * scale,
            height * scale,
        )

    def _box(self, roi: LaneROI) -> QRectF:
        rect = self.image_rect()
        x, y, width, height = self._view_bounds()
        return QRectF(
            rect.x() + (roi.x0 - x) * rect.width() / width,
            rect.y() + (roi.y0 - y) * rect.height() / height,
            roi.width * rect.width() / width,
            (roi.y1 - roi.y0) * rect.height() / height,
        )

    def _hit(self, position: QPointF) -> str:
        if self._crop is None:
            return "draw"
        box = self._box(self._crop)
        if not box.adjusted(-7, -7, 7, 7).contains(position):
            return "draw"
        edge = ""
        if abs(position.x() - box.left()) <= 7:
            edge += "l"
        elif abs(position.x() - box.right()) <= 7:
            edge += "r"
        if abs(position.y() - box.top()) <= 7:
            edge += "t"
        elif abs(position.y() - box.bottom()) <= 7:
            edge += "b"
        return edge or "move"

    def _pixel(self, position: QPointF) -> QPointF:
        rect = self.image_rect()
        x, y, width, height = self._view_bounds()
        return QPointF(
            x + max(0.0, min(float(width), (position.x() - rect.x()) * width / rect.width())),
            y + max(0.0, min(float(height), (position.y() - rect.y()) * height / rect.height())),
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#252729"))
        rect = self.image_rect()
        if self._image.isNull():
            painter.setPen(QColor("#e1e7ef"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.empty_message)
            return
        x, y, width, height = self._view_bounds()
        sx, sy = self._image.width() / self._size[0], self._image.height() / self._size[1]
        painter.drawImage(rect, self._image, QRectF(x * sx, y * sy, width * sx, height * sy))
        painter.setClipRect(rect.adjusted(-2, -18, 2, 2))
        lanes = self._lanes
        if self._drag_crop and self._crop and lanes:
            crop = self._drag_crop
            lanes = tuple(
                LaneROI(
                    lane.lane_id,
                    crop.x0 + i * crop.width // len(lanes),
                    crop.y0,
                    crop.x0 + (i + 1) * crop.width // len(lanes),
                    crop.y1,
                )
                for i, lane in enumerate(lanes)
            )
        for lane, color, label_y in [
            *((r, "#ffbb52", 14 if i == 1 else -4) for i, r in enumerate(self._regions)),
            *((r, "#36d9b0", 14) for r in lanes),
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
        crop = self._drag_crop or self._crop
        if crop:
            box = self._box(crop)
            painter.setPen(QPen(QColor("#36d9b0"), 2))
            painter.drawRect(box)
            painter.setBrush(QColor("#ffffff"))
            for point in (box.topLeft(), box.topRight(), box.bottomLeft(), box.bottomRight()):
                painter.drawRect(QRectF(point.x() - 4, point.y() - 4, 8, 8))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._image.isNull():
            return
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_anchor = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if event.button() == Qt.MouseButton.LeftButton and self.image_rect().contains(
            event.position()
        ):
            self._anchor = self._pixel(event.position())
            self._drag_mode = self._hit(event.position())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._image.isNull():
            return
        if self._pan_anchor is not None:
            self._pan += event.position() - self._pan_anchor
            self._pan_anchor = event.position()
            self.update()
            return
        mode = self._drag_mode if self._anchor is not None else self._hit(event.position())
        cursors = {
            "move": Qt.CursorShape.SizeAllCursor,
            "l": Qt.CursorShape.SizeHorCursor,
            "r": Qt.CursorShape.SizeHorCursor,
            "t": Qt.CursorShape.SizeVerCursor,
            "b": Qt.CursorShape.SizeVerCursor,
            "lt": Qt.CursorShape.SizeFDiagCursor,
            "rb": Qt.CursorShape.SizeFDiagCursor,
            "rt": Qt.CursorShape.SizeBDiagCursor,
            "lb": Qt.CursorShape.SizeBDiagCursor,
        }
        self.setCursor(cursors.get(mode, Qt.CursorShape.CrossCursor))
        if self._anchor is not None:
            self._drag_crop = self._drag_geometry(self._pixel(event.position()))
            self.update()

    def _drag_geometry(self, end: QPointF) -> LaneROI | None:
        start = self._anchor
        if start is None:
            return None
        crop, mode = self._crop, self._drag_mode
        if crop and mode != "draw":
            x0, y0, x1, y1 = crop.x0, crop.y0, crop.x1, crop.y1
            dx, dy = round(end.x() - start.x()), round(end.y() - start.y())
            if mode == "move":
                dx = max(-x0, min(self._size[0] - x1, dx))
                dy = max(-y0, min(self._size[1] - y1, dy))
                return LaneROI(crop.lane_id, x0 + dx, y0 + dy, x1 + dx, y1 + dy)
            minimum_width = max(1, len(self._lanes))
            if "l" in mode:
                x0 = min(x1 - minimum_width, round(end.x()))
            if "r" in mode:
                x1 = max(x0 + minimum_width, round(end.x()))
            if "t" in mode:
                y0 = min(y1 - 2, round(end.y()))
            if "b" in mode:
                y1 = max(y0 + 2, round(end.y()))
        else:
            x0, y0 = floor(min(start.x(), end.x())), floor(min(start.y(), end.y()))
            x1, y1 = ceil(max(start.x(), end.x())), ceil(max(start.y(), end.y()))
        if x1 - x0 >= max(1, len(self._lanes)) and y1 - y0 >= 2:
            return LaneROI("裁剪", x0, y0, x1, y1)
        return None

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_anchor = None
            self.unsetCursor()
            return
        if self._anchor is None or event.button() != Qt.MouseButton.LeftButton:
            return
        crop = self._drag_geometry(self._pixel(event.position()))
        self._anchor = None
        self._drag_crop = None
        unchanged = bool(
            crop
            and self._crop
            and (crop.x0, crop.y0, crop.x1, crop.y1)
            == (self._crop.x0, self._crop.y0, self._crop.x1, self._crop.y1)
        )
        if unchanged:
            point = self._pixel(event.position())
            for index, lane in enumerate(self._lanes):
                if lane.x0 <= point.x() < lane.x1 and lane.y0 <= point.y() < lane.y1:
                    self.lane_selected.emit(index)
                    break
        if crop and not unchanged:
            self.roi_drawn.emit((crop.x0, crop.y0, crop.x1, crop.y1))
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._anchor = None
            self._drag_crop = None
            self.update()
            event.accept()
            return
        crop = self._crop
        if crop and event.key() in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        ):
            step = 5 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
            dx = step * (int(event.key() == Qt.Key.Key_Right) - int(event.key() == Qt.Key.Key_Left))
            dy = step * (int(event.key() == Qt.Key.Key_Down) - int(event.key() == Qt.Key.Key_Up))
            x0, y0, x1, y1 = crop.x0, crop.y0, crop.x1, crop.y1
            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                x1 = max(x0 + max(1, len(self._lanes)), min(self._size[0], x1 + dx))
                y1 = max(y0 + 2, min(self._size[1], y1 + dy))
            else:
                dx = max(-x0, min(self._size[0] - x1, dx))
                dy = max(-y0, min(self._size[1] - y1, dy))
                x0, x1, y0, y1 = x0 + dx, x1 + dx, y0 + dy, y1 + dy
            if (x0, y0, x1, y1) != (crop.x0, crop.y0, crop.x1, crop.y1):
                self.roi_drawn.emit((x0, y0, x1, y1))
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._image.isNull():
            return
        old = self.image_rect()
        self._zoom = max(
            1.0, min(12.0, self._zoom * (1.2 if event.angleDelta().y() > 0 else 1 / 1.2))
        )
        factor = self.image_rect().width() / old.width()
        center = QPointF(self.width() / 2, self.height() / 2)
        self._pan = (event.position() - center) * (1 - factor) + self._pan * factor
        if self._zoom == 1.0:
            self._pan = QPointF()
        self.update()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._anchor = None
            self.reset_zoom()
