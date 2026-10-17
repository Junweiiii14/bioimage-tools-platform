"""Direct manipulation of verified profiles; emits annotations, never computed values."""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPaintEvent, QPen, QPolygonF

from wb_tool.domain.quantify import BandBounds, Baseline
from wb_tool.ui.view import ProfilePlot


class EditableProfilePlot(ProfilePlot):
    edit_committed = Signal(object, object)

    def __init__(self) -> None:
        super().__init__()
        self.bounds: BandBounds | None = None
        self.baseline: Baseline | None = None
        self._handle = 0
        self._dragging = False
        self._start: tuple[BandBounds | None, Baseline | None] = (None, None)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("泳道曲线；左右键移动边界，上下键调整基线，Tab 切换手柄")
        self.setMinimumHeight(210)

    def set_annotation(self, bounds: BandBounds | None, baseline: Baseline | None) -> None:
        if self._dragging:
            return
        self.bounds = bounds
        self.baseline = baseline
        self.update()

    def _area(self) -> QRectF:
        return QRectF(62, 58, max(1, self.width() - 80), max(1, self.height() - 92))

    def _level(self) -> float:
        return max(
            (
                *self.values,
                1.0,
                *((self.baseline.left_value, self.baseline.right_value) if self.baseline else ()),
            )
        )

    def _baseline(self) -> Baseline | None:
        if self.baseline:
            return self.baseline
        if self.bounds and self.bounds.right < len(self.values):
            return Baseline(self.values[self.bounds.left], self.values[self.bounds.right])
        return None

    def _point(self, index: int, value: float) -> QPointF:
        area = self._area()
        return QPointF(
            area.left() + index * area.width() / max(1, len(self.values) - 1),
            area.bottom() - value * area.height() / self._level(),
        )

    def _handles(self) -> tuple[QPointF, ...]:
        base = self._baseline()
        if not self.bounds or not base or len(self.values) < 2:
            return ()
        return (
            self._point(self.bounds.left, 0),
            self._point(self.bounds.right, 0),
            self._point(self.bounds.left, base.left_value),
            self._point(self.bounds.right, base.right_value),
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        handles = self._handles()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        painter.setPen(QColor("#485653"))
        painter.drawText(12, 20, "原始泳道曲线 · 强度均值")
        if len(self.values) < 2:
            painter.drawText(12, 70, "测量并核验后显示原始曲线；点击重新测量当前图。")
            return
        area = self._area()
        painter.setPen(QPen(QColor("#d9dedb"), 1))
        painter.drawLine(area.bottomLeft(), area.bottomRight())
        painter.drawLine(area.topLeft(), area.bottomLeft())
        painter.setPen(QColor("#485653"))
        for value in (0.0, self._level() / 2, self._level()):
            y = self._point(0, value).y()
            painter.drawText(
                QRectF(2, y - 8, 52, 16), Qt.AlignmentFlag.AlignRight, format(value, ".4g")
            )
        for index in (0, (len(self.values) - 1) // 2, len(self.values) - 1):
            x = self._point(index, 0).x()
            painter.drawText(
                QRectF(x - 20, area.bottom() + 4, 40, 18), Qt.AlignmentFlag.AlignCenter, str(index)
            )
        painter.setPen(QPen(QColor("#256f82"), 2))
        painter.drawPolyline(
            QPolygonF([self._point(i, value) for i, value in enumerate(self.values)])
        )
        if not handles:
            painter.drawText(12, 42, "点击曲线设置范围；边界尚未指定")
            return
        for label, point in zip(("左边界", "右边界"), handles[:2], strict=True):
            painter.drawText(
                QRectF(point.x() - 30, area.top() - 24, 60, 18), Qt.AlignmentFlag.AlignCenter, label
            )
        painter.setPen(QPen(QColor("#256f82"), 1.5, Qt.PenStyle.DashLine))
        for point in handles[:2]:
            painter.drawLine(point, QPointF(point.x(), self._area().top()))
        painter.setPen(QPen(QColor("#8c6434"), 2))
        painter.drawLine(handles[2], handles[3])
        for i, point in enumerate(handles):
            painter.setBrush(QColor("#256f82" if i == self._handle else "#ffffff"))
            painter.setPen(QPen(QColor("#256f82"), 2))
            painter.drawEllipse(point, 5, 5)
        if self.hasFocus():
            painter.setPen(QPen(QColor("#256f82"), 1, Qt.PenStyle.DotLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 4, 4)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or len(self.values) < 2:
            super().mousePressEvent(event)
            return
        self.setFocus()
        self._start = (self.bounds, self.baseline)
        handles = self._handles()
        if not handles:
            # Explicit user click creates a full-profile editable range, never a
            # detection claim; releasing commits an annotation requiring a run.
            self.bounds = BandBounds(0, len(self.values) - 1)
            handles = self._handles()
        self._handle = min(
            range(len(handles)), key=lambda i: (handles[i] - event.position()).manhattanLength()
        )
        self._dragging = True
        self._move_handle(event.position())
        event.accept()

    def _move_handle(self, position: QPointF) -> None:
        if not self.bounds:
            return
        area = self._area()
        if self._handle < 2:
            index = round((position.x() - area.left()) / area.width() * (len(self.values) - 1))
            left, right = self.bounds.left, self.bounds.right
            if self._handle == 0:
                left = max(0, min(index, right - 1))
            else:
                right = max(left + 1, min(index, len(self.values) - 1))
            self.bounds = BandBounds(left, right)
        else:
            base = self._baseline()
            if base:
                value = max(
                    0.0,
                    min(
                        self._level(),
                        (area.bottom() - position.y()) / area.height() * self._level(),
                    ),
                )
                self.baseline = Baseline(
                    value if self._handle == 2 else base.left_value,
                    value if self._handle == 3 else base.right_value,
                )
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            self._move_handle(event.position())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._move_handle(event.position())
            self._dragging = False
            self._commit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _commit(self) -> None:
        if self.bounds:
            self.edit_committed.emit(self.bounds, self.baseline)

    def focusNextPrevChild(self, next: bool) -> bool:
        if self.hasFocus() and ((next and self._handle < 3) or (not next and self._handle > 0)):
            self._handle += 1 if next else -1
            self.update()
            return True
        return super().focusNextPrevChild(next)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape and self._dragging:
            self.bounds, self.baseline = self._start
            self._dragging = False
            self.update()
            return
        handles = self._handles()
        if handles and event.key() in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        ):
            step = 5 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
            point = handles[self._handle]
            area = self._area()
            dx = area.width() / max(1, len(self.values) - 1) * step
            dy = area.height() / 100 * step
            direction = {
                Qt.Key.Key_Left: QPointF(-dx, 0),
                Qt.Key.Key_Right: QPointF(dx, 0),
                Qt.Key.Key_Up: QPointF(0, -dy),
                Qt.Key.Key_Down: QPointF(0, dy),
            }[Qt.Key(event.key())]
            self._move_handle(point + direction)
            self._commit()
            event.accept()
        else:
            super().keyPressEvent(event)
