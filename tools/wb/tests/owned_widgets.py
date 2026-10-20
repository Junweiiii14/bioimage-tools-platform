"""Explicit ownership for plain WB test widgets; never discover or sweep Qt objects.

Async application windows must use their resource-aware desktop close fixture instead.
"""

from collections.abc import Callable, Generator
from contextlib import contextmanager

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot
from shiboken6 import isValid

type WidgetOwner = Callable[[QWidget], None]


@contextmanager
def owned_widget_scope(qtbot: QtBot) -> Generator[WidgetOwner, None, None]:
    widgets: list[QWidget] = []

    def own(widget: QWidget) -> None:
        qtbot.addWidget(widget)
        widgets.append(widget)

    try:
        yield own
    finally:
        for widget in reversed(widgets):
            if not isValid(widget):
                continue
            if QThread.currentThread() != widget.thread():
                raise RuntimeError("Owned test widgets must retire on their GUI thread")
            widget.close()
            widget.deleteLater()
            qtbot.waitUntil(lambda widget=widget: not isValid(widget), timeout=10000)
