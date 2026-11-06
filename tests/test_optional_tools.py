"""Restart-only activation and historical refusal on the ordinary desktop shell."""

import json
from pathlib import Path

from bioimage_app.tool_assembly import ToolAssembly
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot

from tests.test_project_navigation_session import js
from tooling.qt_test_lifecycle import close_and_dispose_window


def test_disabled_tools_keep_platform_settings_and_shutdown(qtbot: QtBot, tmp_path: Path) -> None:
    settings = QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat)
    for tool in ("wb", "nuclei", "bca"):
        settings.setValue(f"tools/{tool}/enabled", False)
    window = WebWorkbenchWindow(settings=settings)
    window.show()
    try:
        qtbot.waitUntil(
            lambda: (
                js(window, qtbot, "document.querySelectorAll('#tool-enablement input').length") == 3
            )
        )
        assert (
            js(window, qtbot, "document.querySelector('#runtime-badge').textContent")
            == "桌面工作台"
        )
        window.tools.setEnabled("bca", True)
        assert not window.tools.available("bca")
        assert ToolAssembly(settings).available("bca")
        messages: list[str] = []
        window.session_bridge.sessionStateChanged.connect(messages.append)
        window.session_bridge.session("open", "{}")
        assert "WB已停用" in messages[-1]
        assert not list(tmp_path.glob("**/*.sqlite*"))
        window.session_bridge.session("reply", json.dumps({"choice": "return"}))
        js(window, qtbot, "document.querySelector('[data-bca-open]').click();true")
        assert js(window, qtbot, "document.querySelector('#bca-dialog').open") is False
        assert "BCA已停用" in str(
            js(window, qtbot, "document.querySelector('#tool-enablement-note').textContent")
        )
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: not window.isVisible(), timeout=20000
        )
