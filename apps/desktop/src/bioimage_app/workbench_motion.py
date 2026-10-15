"""Small, interruptible native motion for navigation; scientific imagery stays still."""

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPropertyAnimation,
    QRect,
    QSettings,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QListWidget, QWidget


class NavigationMotion(QObject):
    def __init__(self, navigation: QListWidget, settings: QSettings) -> None:
        super().__init__(navigation)
        self.navigation = navigation
        self.settings = settings
        viewport = navigation.viewport()
        self.indicator = QWidget(viewport)
        self.indicator.setObjectName("navigationIndicator")
        self.indicator.setStyleSheet("background: #256f82; border-radius: 1px;")
        self.indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.animation = QPropertyAnimation(self.indicator, b"geometry", self)
        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        navigation.currentRowChanged.connect(self.move)
        viewport.installEventFilter(self)
        self.move()

    def reduced(self) -> bool:
        return bool(self.settings.value("reduce_motion", False, type=bool)) or not (
            QApplication.isEffectEnabled(Qt.UIEffect.UI_AnimateCombo)
        )

    def move(self, _index: int = -1) -> None:
        if self.navigation.currentRow() < 0:
            self.indicator.hide()
            return
        item = self.navigation.currentItem()
        rect = self.navigation.visualItemRect(item)
        target = QRect(rect.x() + 12, rect.bottom() - 2, max(0, rect.width() - 24), 2)
        self.animation.stop()
        if self.reduced() or not self.indicator.isVisible():
            self.indicator.setGeometry(target)
        else:
            self.animation.setStartValue(self.indicator.geometry())
            self.animation.setEndValue(target)
            self.animation.start()
        self.indicator.show()
        self.indicator.raise_()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            QTimer.singleShot(0, self.move)
        elif event.type() == QEvent.Type.Hide:
            self.animation.stop()
        return super().eventFilter(watched, event)


class PanelReveal(QObject):
    """Brief feedback on newly opened controls only; no image or numeric interpolation."""

    def __init__(self, panel: QWidget, navigation: NavigationMotion) -> None:
        super().__init__(panel)
        self.panel = panel
        self.navigation = navigation
        self.effect = QGraphicsOpacityEffect(panel)
        self.effect.setOpacity(1)
        panel.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity", self)
        self.animation.setDuration(140)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        panel.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Show, QEvent.Type.Hide):
            self.animation.stop()
            self.effect.setOpacity(1)
            if event.type() == QEvent.Type.Show and not self.navigation.reduced():
                self.animation.setStartValue(0.7)
                self.animation.setEndValue(1.0)
                self.animation.start()
        return super().eventFilter(watched, event)
