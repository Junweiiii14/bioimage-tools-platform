"""A failed resource retirement must not destroy a still-owned native window."""

import pytest
from PySide6.QtWidgets import QWidget
from pytest import MonkeyPatch
from pytestqt.exceptions import TimeoutError as QtTimeoutError
from pytestqt.qtbot import QtBot
from shiboken6 import isValid

from tooling.qt_test_lifecycle import close_and_dispose_window


def test_failed_resource_wait_does_not_schedule_native_destruction(
    qtbot: QtBot, monkeypatch: MonkeyPatch
) -> None:
    window = QWidget()
    scheduled: list[bool] = []
    try:
        with monkeypatch.context() as patch:
            patch.setattr(window, "deleteLater", lambda: scheduled.append(True))
            with pytest.raises(QtTimeoutError):
                close_and_dispose_window(window, qtbot, resources_closed=lambda: False, timeout=20)
            assert not scheduled
            assert isValid(window)
    finally:
        # This plain QWidget owns no asynchronous resources.
        close_and_dispose_window(window, qtbot, resources_closed=lambda: True, timeout=1000)
    assert not isValid(window)
