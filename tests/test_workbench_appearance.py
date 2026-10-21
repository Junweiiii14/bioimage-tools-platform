"""Persistence failure, cross-window preferences and interruptible WebEngine feedback."""

import json
from pathlib import Path

from bioimage_app.appearance import DEFAULTS, KEY, WorkbenchAppearance
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot

from tests.test_intake_web_ui import intake_page as intake_page
from tests.test_intake_web_ui import javascript
from tooling.qt_test_lifecycle import close_and_dispose_window


def test_appearance_persists_and_refreshes_other_window_without_project_data(
    tmp_path: Path,
) -> None:
    path = str(tmp_path / "appearance.ini")
    first = WorkbenchAppearance(QSettings(path, QSettings.Format.IniFormat))
    second = WorkbenchAppearance(QSettings(path, QSettings.Format.IniFormat))
    assert first.values == DEFAULTS and not first.configured
    chosen = {"theme": "iris", "density": "compact", "motion": "gentle"}
    first.update(chosen, "request-1", 1)
    second.refresh()
    assert second.values == chosen and second.configured
    assert first.receipt == "request-1" and not first.error
    first.update({**chosen, "motion": "unknown"}, "request-2", 1)
    assert first.values == chosen and first.error
    first.update(DEFAULTS, "request-3", 2)
    assert first.values == chosen and first.error
    assert set(first.settings.allKeys()) == {KEY}


def test_corrupt_preferences_are_preserved(tmp_path: Path) -> None:
    settings = QSettings(str(tmp_path / "invalid.ini"), QSettings.Format.IniFormat)
    original = json.dumps({"schema_version": 200, "values": DEFAULTS})
    settings.setValue(KEY, original)
    appearance = WorkbenchAppearance(settings)
    assert appearance.error and appearance.values == DEFAULTS
    assert settings.value(KEY) == original


def test_open_windows_receive_theme_from_host_timer(qtbot: QtBot, tmp_path: Path) -> None:
    path = str(tmp_path / "windows.ini")
    windows = [
        WebWorkbenchWindow(settings=QSettings(path, QSettings.Format.IniFormat)) for _ in range(2)
    ]
    try:
        for window in windows:
            window.show()
            qtbot.waitUntil(
                lambda window=window: javascript(window, qtbot, "!!window.desktopSession") is True
            )
        javascript(
            windows[0],
            qtbot,
            "workbenchAppearance.open();document.querySelector('[data-appearance-theme=iris]').click();true",
        )
        qtbot.waitUntil(lambda: windows[0].appearance.values["theme"] == "iris", timeout=10000)
        qtbot.waitUntil(lambda: windows[1].appearance.values["theme"] == "iris", timeout=10000)
        assert javascript(windows[1], qtbot, "document.documentElement.dataset.theme") == "iris"
    finally:
        for window in windows:
            close_and_dispose_window(
                window,
                qtbot,
                resources_closed=lambda window=window: window.host.resources_closed,
                timeout=20000,
            )


def test_failed_write_rolls_back_and_is_not_a_successful_receipt(tmp_path: Path) -> None:
    class FailingSettings(QSettings):
        fail = False

        def status(self) -> QSettings.Status:
            return QSettings.Status.AccessError if self.fail else super().status()

    settings = FailingSettings(str(tmp_path / "failed.ini"), QSettings.Format.IniFormat)
    appearance = WorkbenchAppearance(settings)
    appearance.update(DEFAULTS, "first", 1)
    previous = settings.value(KEY)
    settings.fail = True
    appearance.update({**DEFAULTS, "theme": "ember"}, "failed", 1)
    assert appearance.error and appearance.receipt == "failed"
    assert appearance.values == DEFAULTS and settings.value(KEY) == previous


def test_drawer_reverse_keeps_latest_panel_focus_and_real_local_font(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    javascript(
        window, qtbot, "workbenchAppearance.open();closeDrawer();workbenchAppearance.open();true"
    )
    qtbot.waitUntil(
        lambda: (
            javascript(
                window, qtbot, "document.querySelector('#drawer').getAnimations().length===0"
            )
            is True
        )
    )
    assert javascript(window, qtbot, "!document.querySelector('#drawer').hidden")
    assert javascript(window, qtbot, "document.querySelector('.app-shell').inert")
    assert javascript(window, qtbot, "!!document.activeElement.closest('#drawer')")
    qtbot.waitUntil(
        lambda: (
            javascript(window, qtbot, "document.fonts.check('14px \"WB Sans\"','原图 Figure 123')")
            is True
        ),
        timeout=15000,
    )
    assert javascript(
        window, qtbot, "getComputedStyle(document.body).fontFamily.includes('WB Sans')"
    )
    javascript(window, qtbot, "closeDrawer();true")
    qtbot.waitUntil(
        lambda: javascript(window, qtbot, "document.querySelector('#drawer').hidden") is True
    )
    assert javascript(window, qtbot, "!document.querySelector('.app-shell').inert")
