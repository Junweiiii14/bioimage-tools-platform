"""The shipped WebEngine comparison UI operates real saved reports and drains on exit."""

import json
from pathlib import Path

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from tests.test_project_navigation_session import js, source_at, start
from tests.test_project_navigation_session import session_window as session_window


def test_web_comparison_run_reopen_and_old_project_preserved(
    session_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = session_window
    original = source_at(tmp_path / "old-project.tif")
    start(window, qtbot, original)
    old_project = window.host.workspace_path
    old_id = window.host.view.project().project_id
    old_bytes = original.read_bytes()

    def choose_parent(*_args: object, **_kwargs: object) -> str:
        return str(tmp_path)

    monkeypatch.setattr(QFileDialog, "getExistingDirectory", choose_parent)
    replies: list[str] = []
    window.comparison.stateChanged.connect(replies.append)
    qtbot.waitUntil(
        lambda: (
            js(
                window,
                qtbot,
                "!!window.moduleComparison && !document.querySelector('#module-run').disabled",
            )
            is True
        ),
        timeout=15000,
    )
    js(window, qtbot, "document.querySelector('[data-module-open]').click(); true")
    assert js(window, qtbot, "document.querySelector('#module-compare-dialog').open") is True
    js(window, qtbot, "document.querySelector('#module-run').click(); true")
    qtbot.waitUntil(lambda: window.comparison.busy, timeout=5000)
    qtbot.waitUntil(lambda: not window.comparison.busy, timeout=30000)
    qtbot.waitUntil(
        lambda: (
            js(
                window,
                qtbot,
                "document.querySelector('#module-table').textContent.includes('4000.0')",
            )
            is True
        )
    )
    first = json.loads(replies[-1])
    assert first["state"] == "succeeded" and first["run"]["pid"] > 0
    assert first["quality"] == "complete"
    window.resize(1440, 900)
    qtbot.waitUntil(lambda: js(window, qtbot, "innerWidth > 1300") is True)
    qtbot.waitUntil(
        lambda: (
            js(
                window,
                qtbot,
                "document.fonts.status === 'loaded' && "
                "!document.querySelector('#module-run').disabled",
            )
            is True
        )
    )
    # WebEngine's compositor may still show the preceding frame after DOM callbacks.
    qtbot.wait(250)
    assert window.grab().save(str(tmp_path / "comparison-1440.png"))
    js(window, qtbot, "document.querySelector('#module-reopen').click(); true")
    qtbot.waitUntil(lambda: window.comparison.busy, timeout=5000)
    qtbot.waitUntil(lambda: not window.comparison.busy, timeout=30000)
    reopened = json.loads(replies[-1])
    assert reopened["run"] == first["run"]
    assert reopened["tables_json"] == first["tables_json"]
    js(
        window,
        qtbot,
        "document.querySelector('#module-case').value='invalid_roi'; "
        "document.querySelector('#module-run').click(); true",
    )
    qtbot.waitUntil(lambda: window.comparison.busy, timeout=5000)
    qtbot.waitUntil(lambda: not window.comparison.busy, timeout=30000)
    qtbot.waitUntil(
        lambda: (
            js(
                window,
                qtbot,
                "document.querySelector('#module-table').textContent.includes('无效')",
            )
            is True
        )
    )
    invalid = json.loads(replies[-1])
    assert invalid["quality"] == "issues" and invalid["workspace"] != first["workspace"]
    window.resize(960, 640)
    qtbot.waitUntil(lambda: js(window, qtbot, "innerWidth < 1100") is True)
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!document.querySelector('#module-run').disabled") is True
    )
    qtbot.wait(250)
    assert window.grab().save(str(tmp_path / "comparison-960.png"))
    assert (
        js(
            window,
            qtbot,
            "document.querySelector('#module-compare-dialog').getBoundingClientRect().right "
            "<= innerWidth",
        )
        is True
    )
    js(window, qtbot, "document.querySelector('#module-close').click(); true")
    assert js(window, qtbot, "!document.querySelector('#module-compare-dialog').open") is True
    assert window.host.workspace_path == old_project
    assert window.host.view.project().project_id == old_id
    assert original.read_bytes() == old_bytes


def test_workbench_close_waits_for_comparison_services(
    session_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = session_window
    window.comparison.start_fixture_at(str(tmp_path / "cancel-on-close"))
    assert window.comparison.busy
    window.close()
    qtbot.waitUntil(
        lambda: not window.comparison.busy and window.host.resources_closed, timeout=30000
    )
    assert not window.isVisible()
