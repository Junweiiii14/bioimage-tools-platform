"""Restart-only activation and historical refusal on the ordinary desktop shell."""

import json
from importlib.machinery import ModuleSpec
from importlib.util import find_spec
from pathlib import Path

import bioimage_app.tool_assembly as assembly_module
import pytest
from bioimage_app.tool_assembly import ToolAssembly
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings, QUrl
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from tests.test_folder_drop import native_drop
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


@pytest.mark.parametrize("availability", ["missing", "disabled"])
def test_unavailable_wb_native_drop_keeps_bca_usable(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, availability: str
) -> None:
    settings = QSettings(str(tmp_path / "drop.ini"), QSettings.Format.IniFormat)
    if availability == "disabled":
        settings.setValue("tools/wb/enabled", False)
    else:

        def installed(name: str) -> ModuleSpec | None:
            return None if name == "wb_tool" else find_spec(name)

        monkeypatch.setattr(assembly_module, "find_spec", installed)
    window = WebWorkbenchWindow(settings=settings)
    window.show()
    chosen: list[bool] = []

    def choose(*_args: object, **_kwargs: object) -> tuple[str, str]:
        chosen.append(True)
        return "", ""

    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose)
    try:
        qtbot.waitUntil(
            lambda: (
                js(window, qtbot, "document.querySelectorAll('#tool-enablement input').length") == 3
            )
        )
        original = tmp_path / "originals"
        original.mkdir()
        native_drop(window, qtbot, [QUrl.fromLocalFile(str(original))])
        qtbot.waitUntil(
            lambda: (
                window.tools.reason("wb")
                in str(
                    js(window, qtbot, "document.querySelector('#folder-drop-status').textContent")
                )
            )
        )
        # Two 150ms session polls must not escape or turn a refused drop into opening.
        qtbot.wait(350)
        assert window.shutdown_stage == "idle"
        assert not window.navigation.recent()
        js(window, qtbot, "document.querySelector('[data-bca-open]').click();true")
        qtbot.waitUntil(
            lambda: (
                js(window, qtbot, "!document.querySelector('[data-bca-choose=source]').disabled")
                is True
            )
        )
        js(window, qtbot, "document.querySelector('[data-bca-choose=source]').click();true")
        qtbot.waitUntil(lambda: bool(chosen))
        assert not window.bca.busy and original.is_dir()
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: not window.isVisible(), timeout=20000
        )
