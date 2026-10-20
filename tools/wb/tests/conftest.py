"""Opt-in cleanup for exact, registered plain WB test widgets."""

from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

    from tools.wb.tests.owned_widgets import WidgetOwner


@pytest.fixture
def owned_widgets(qtbot: "QtBot") -> Generator["WidgetOwner", None, None]:
    from tools.wb.tests.owned_widgets import owned_widget_scope

    with owned_widget_scope(qtbot) as own:
        yield own
