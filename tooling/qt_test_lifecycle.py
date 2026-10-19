"""Retire one explicitly owned async test window before releasing Python references.

This helper never discovers or deletes other Qt objects, changes GC, or bypasses
the window's normal asynchronous close. Product close behavior is unchanged.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from bioimage_app.web_window import WebWorkbenchWindow
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

    def close_completed() -> bool:
        # Fixture cleanup explicitly accepts the same save/cancel choices as a user.
        # Individual lifecycle tests assert the prompts before entering this cleanup.
        if isinstance(window, WebWorkbenchWindow):
            choice = {
                "confirm_dirty": "save",
                "confirm_draft": "discard",
                "confirm_busy": "cancel",
            }.get(window.shutdown_stage)
            if choice:
                window.bridge.session("reply", '{"choice":"' + choice + '"}')
        return resources_closed()

    qtbot.waitUntil(close_completed, timeout=timeout)
    # A failed resource wait must escape without scheduling native destruction.
    window.deleteLater()
    qtbot.waitUntil(lambda: not isValid(window), timeout=10000)
