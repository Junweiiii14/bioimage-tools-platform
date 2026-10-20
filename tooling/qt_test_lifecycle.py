"""Retire one explicitly owned async test window before releasing Python references.

This helper never discovers or deletes other Qt objects, changes GC, or bypasses
the window's normal asynchronous close. Product close behavior is unchanged.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def close_and_dispose_window(
    window: QWidget,
    qtbot: "QtBot",
    *,
    resources_closed: Callable[[], bool],
    timeout: int,
) -> None:
    if not isValid(window):
        return
    if QThread.currentThread() != window.thread():
        raise RuntimeError("Test windows must retire on their GUI thread")
    window.close()
    qtbot.waitUntil(resources_closed, timeout=timeout)
    # A failed resource wait must escape without scheduling native destruction.
    window.deleteLater()
    qtbot.waitUntil(lambda: not isValid(window), timeout=10000)
