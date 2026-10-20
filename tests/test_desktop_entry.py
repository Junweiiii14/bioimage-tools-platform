"""Normal command aliases must instantiate the existing web workbench."""

import subprocess
import sys

import pytest
import shiboken6
from bioimage_app.desktop_entry import create_desktop_window, desktop_mode
from bioimage_app.web_window import WebWorkbenchWindow
from pytestqt.qtbot import QtBot


def test_destroyed_workbench_releases_its_hidden_native_host(qtbot: QtBot) -> None:
    window = WebWorkbenchWindow()
    host = window.host
    try:
        assert host.isWindow()
        window.close()
        qtbot.waitUntil(lambda: host.resources_closed, timeout=15000)
        window.deleteLater()
        qtbot.waitUntil(lambda: not shiboken6.isValid(window))
        assert not shiboken6.isValid(host)
    finally:
        if shiboken6.isValid(window):
            window.close()
            qtbot.waitUntil(lambda: host.resources_closed, timeout=15000)
            window.deleteLater()
        if shiboken6.isValid(host):
            host.deleteLater()


@pytest.mark.parametrize(
    "arguments", [[], ["--web-workbench"], ["--figure-project"], ["--platform"]]
)
def test_normal_entry_opens_current_workbench(qtbot: QtBot, arguments: list[str]) -> None:
    window = create_desktop_window(desktop_mode(arguments))
    assert isinstance(window, WebWorkbenchWindow)
    qtbot.addWidget(window)
    try:
        window.show()
        assert not window.host.isVisible()
        assert window.host.automatic.crop_policy == "source_geometry@2"
        assert window.host.automatic.quant_policy == "anchored_background@1"
    finally:
        window.close()
        qtbot.waitUntil(lambda: window.host.resources_closed, timeout=15000)


@pytest.mark.parametrize(
    ("argument", "mode"),
    [
        ("--legacy-platform", "legacy-platform"),
        ("--legacy-figure-project", "legacy-figure"),
        ("--legacy-wb-manual", "legacy-manual"),
        ("--wb-manual", "legacy-manual"),
    ],
)
def test_native_compatibility_requires_explicit_option(argument: str, mode: str) -> None:
    assert desktop_mode([argument]) == mode


def test_unknown_entry_is_rejected_before_starting_qt() -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-m", "bioimage_app", "--web-workbenhc"],
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert b"unrecognized arguments" in result.stderr


@pytest.mark.parametrize("delayed", [False, True])
def test_rejected_close_keeps_workbench_without_opening_native_window(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, delayed: bool
) -> None:
    window = WebWorkbenchWindow()
    qtbot.addWidget(window)
    window.show()
    try:
        with monkeypatch.context() as patch:
            closing = [delayed]
            patch.setattr(type(window.host), "is_closing", property(lambda self: closing[0]))
            patch.setattr(window.host, "close", lambda: False)
            window.close()
            closing[0] = False
            qtbot.waitUntil(lambda: not window.host.shutdown_requested, timeout=1500)
            assert window.isVisible()
            assert not window.host.isVisible()
            assert not window.host.shutdown_requested
    finally:
        window.close()
        qtbot.waitUntil(lambda: window.host.resources_closed, timeout=15000)
