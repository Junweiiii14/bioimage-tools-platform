"""Cleanup follows registered ownership even when a test body fails."""

import pytest
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot
from shiboken6 import isValid

from tools.wb.tests.owned_widgets import owned_widget_scope


def test_owned_cleanup_retires_native_widget_without_sweeping_other_widgets(qtbot: QtBot) -> None:
    unrelated = QWidget()
    widget = QWidget()
    try:
        with (
            pytest.raises(ValueError, match="synthetic failed body"),
            owned_widget_scope(qtbot) as own,
        ):
            own(widget)
            raise ValueError("synthetic failed body")
        assert not isValid(widget)
        assert isValid(unrelated)
    finally:
        with owned_widget_scope(qtbot) as own:
            own(unrelated)
