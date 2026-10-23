"""Entry routing and lifecycle choices use real async storage and owned Qt hosts."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import tifffile
from bioimage_app.project_navigation import ProjectNavigation
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from tooling.qt_test_lifecycle import close_and_dispose_window


@pytest.fixture
def session_window(qtbot: QtBot, tmp_path: Path) -> Iterator[WebWorkbenchWindow]:
    settings = QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    window = WebWorkbenchWindow(settings=settings)
    window.show()
    try:
        yield window
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )


def source_at(path: Path) -> Path:
    directory = path.parent / "originals"
    directory.mkdir(exist_ok=True)
    path = directory / path.name
    pixels = np.full((90, 180), 50000, dtype=np.uint16)
    pixels[35:45, 40:65] = 10000
    pixels[35:45, 100:125] = 15000
    tifffile.imwrite(path, pixels)
    return path


def start(window: WebWorkbenchWindow, qtbot: QtBot, path: Path) -> None:
    window.start_from_images([path], automatic=False)
    qtbot.waitUntil(
        lambda: (
            bool(window.host.view.project().rows)
            and not window.host.operation_busy
            and not window.host.has_unsaved_changes
            and window.shutdown_stage == "idle"
        ),
        timeout=25000,
    )


def js(window: WebWorkbenchWindow, qtbot: QtBot, code: str) -> object:
    replies: list[object] = []
    window.web.page().runJavaScript(code, replies.append)
    qtbot.waitUntil(lambda: bool(replies), timeout=10000)
    return replies[0]


def test_manual_import_routes_to_quant_and_records_only_real_project(
    session_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = session_window
    original = source_at(tmp_path / "original.tif")
    before = original.read_bytes()
    start(window, qtbot, original)
    qtbot.waitUntil(lambda: js(window, qtbot, "mode") == "quant", timeout=10000)
    assert js(window, qtbot, "!document.querySelector('#work-view').hidden") is True
    assert js(window, qtbot, "!!desktopSession && !!bridge") is True
    recent = window.navigation.recent()
    assert len(recent) == 1
    assert recent[0]["path"] == window.host.workspace_path
    assert recent[0]["projectId"] == window.host.view.project().project_id
    assert original.read_bytes() == before


def test_platform_browsing_keeps_owned_host_and_recent_switch_keeps_draft_guard(
    session_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = session_window
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!!window.platformHome && !!window.desktopSession") is True
    )
    assert js(window, qtbot, "platformHome.current()") == "platform"
    start(window, qtbot, source_at(tmp_path / "platform.tif"))
    qtbot.waitUntil(lambda: js(window, qtbot, "mode") == "quant", timeout=10000)
    owned_host, workspace = window.host, window.host.workspace_path
    assert js(window, qtbot, "platformHome.show('platform');true") is True
    window.bridge.publish()
    window.bridge.session("refresh", "{}")
    qtbot.wait(150)
    assert js(window, qtbot, "platformHome.current()") == "platform"
    assert window.host is owned_host and window.host.workspace_path == workspace
    assert js(window, qtbot, "document.querySelector('.installed-tool').click();true") is True
    assert js(window, qtbot, "platformHome.current()") == "wb"
    assert js(window, qtbot, "platformHome.show('project');true") is True
    assert js(window, qtbot, "mode") == "quant"
    # The new recent-project surface delegates to the original host command; it
    # cannot silently replace a session with an unapplied curve/ROI draft.
    assert (
        js(
            window,
            qtbot,
            "manualQuant.active=true;manualQuant.current().n=row().lanes+1;"
            "platformHome.show('platform');true",
        )
        is True
    )
    assert js(window, qtbot, "desktopSession.hasDraft()") is True
    js(
        window,
        qtbot,
        "document.querySelector('#platform-recents [data-session=recent]').click();true",
    )
    qtbot.waitUntil(lambda: window.shutdown_stage == "confirm_draft")
    assert window.host is owned_host and window.host.workspace_path == workspace
    window.bridge.session("reply", '{"choice":"return"}')
    qtbot.waitUntil(lambda: window.shutdown_stage == "idle")
    js(window, qtbot, "manualQuant.active=false;manualQuant.draft=null;true")
    assert js(window, qtbot, "desktopSession.hasDraft()") is False
    window.bridge.session(
        "position",
        json.dumps(
            {"projectId": window.host.view.project().project_id, "mode": "quant", "draft": False}
        ),
    )


@pytest.mark.parametrize("entry", ["images", "folder"])
@pytest.mark.parametrize("workflow", ["quant", "review"])
def test_wb_home_new_project_keeps_existing_project_and_draft_until_confirmed(
    session_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
    workflow: str,
) -> None:
    window = session_window
    original = source_at(tmp_path / "first.tif")
    start(window, qtbot, original)
    qtbot.waitUntil(lambda: js(window, qtbot, "mode") == "quant", timeout=10000)
    old_host, workspace = window.host, window.host.workspace_path
    project_id = old_host.view.project().project_id
    second_parent = tmp_path / "second"
    second_parent.mkdir()
    second = source_at(second_parent / "second.tif")

    def choose_images(*args: object, **kwargs: object) -> tuple[list[str], str]:
        return [str(second)], ""

    def choose_folder(*args: object, **kwargs: object) -> str:
        return str(second.parent)

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", choose_images)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", choose_folder)
    click = (
        "platformHome.show('wb');document.querySelector('.session-secondary').open=true;"
        f"document.querySelector('[name=session-workflow][value={workflow}]').checked=true;"
        f"document.querySelector('[data-session={entry}]').click();true"
    )
    js(window, qtbot, "manualQuant.active=true;manualQuant.current().n=row().lanes+1;true")
    try:
        assert js(window, qtbot, "desktopSession.hasDraft()") is True
        js(window, qtbot, click)
        qtbot.waitUntil(lambda: window.shutdown_stage == "confirm_draft")
        assert window.host is old_host and window.host.workspace_path == workspace
        assert len(old_host.view.project().rows) == 1
        assert js(window, qtbot, "desktopSession.hasDraft()") is True
        window.bridge.session("reply", '{"choice":"return"}')
        qtbot.waitUntil(lambda: window.shutdown_stage == "idle")
        assert window.host is old_host and window.host.view.project().project_id == project_id
        if entry == "images" and workflow == "quant":
            js(window, qtbot, click)
            qtbot.waitUntil(lambda: window.shutdown_stage == "confirm_draft")
            window.bridge.session("reply", '{"choice":"discard"}')
            qtbot.waitUntil(
                lambda: (
                    window.host is not old_host
                    and window.shutdown_stage == "idle"
                    and not window.host.operation_busy
                    and len(window.host.view.project().rows) == 1
                ),
                timeout=25000,
            )
            assert window.host.workspace_path != workspace
            assert window.host.view.project().project_id != project_id
            assert Path(workspace).is_dir() and original.is_file() and second.is_file()
    finally:
        js(window, qtbot, "manualQuant.active=false;manualQuant.draft=null;true")
        window.bridge.session(
            "position",
            json.dumps(
                {
                    "projectId": window.host.view.project().project_id,
                    "mode": "quant",
                    "draft": False,
                }
            ),
        )


def test_same_window_switch_saves_then_restores_mode_and_source(
    session_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = session_window
    start(window, qtbot, source_at(tmp_path / "first.tif"))
    project = window.host.view.project()
    workspace = window.host.workspace_path
    qtbot.waitUntil(lambda: js(window, qtbot, "mode") == "quant", timeout=10000)
    assert js(window, qtbot, "switchMode('results');true") is True
    qtbot.waitUntil(
        lambda: window.navigation.read(workspace).get("mode") == "results", timeout=10000
    )
    old_host = window.host
    old_state = json.dumps(window.bridge.snapshot())
    window.bridge.session("home", "{}")
    qtbot.waitUntil(lambda: window.host is not old_host, timeout=20000)
    assert window.host.workspace_path == ""
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!document.querySelector('#home-view').hidden") is True,
        timeout=10000,
    )
    window.bridge.stateChanged.emit(old_state)
    qtbot.wait(200)
    assert (
        js(window, qtbot, "state.rows.length===0 && !document.querySelector('#home-view').hidden")
        is True
    )
    window.open_project(workspace)
    qtbot.waitUntil(
        lambda: (
            window.host.view.project().project_id == project.project_id
            and not window.host.operation_busy
            and window.shutdown_stage == "idle"
        ),
        timeout=25000,
    )
    qtbot.waitUntil(lambda: js(window, qtbot, "mode") == "results", timeout=10000)
    selected = window.host.view.selected_row()
    assert selected is not None and selected.row_id == project.rows[0].row_id


def test_busy_close_is_not_accepted_until_user_cancels(
    session_window: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = session_window
    window.host.begin_operation()
    window.close()
    assert window.isVisible()
    assert window.shutdown_stage == "confirm_busy"
    assert not window.host.is_closing
    window.bridge.session("reply", '{"choice":"return"}')
    assert window.shutdown_stage == "idle"
    assert window.isVisible()
    window.host.finish_operation("测试任务结束")
    qtbot.waitUntil(lambda: not window.host.operation_busy)


def test_close_save_failure_is_visible_and_can_return_to_work(
    session_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = session_window
    start(window, qtbot, source_at(tmp_path / "source.tif"))
    window.host.pause_auto_save(True)
    window.host.view.generation += 1
    window.close()
    assert window.shutdown_stage == "confirm_dirty"

    def failed_save(*args: object, **kwargs: object) -> None:
        window.host.fail_operation("模拟磁盘不可写")

    monkeypatch.setattr(window.host, "save", failed_save)
    window.bridge.session("reply", '{"choice":"save"}')
    qtbot.waitUntil(lambda: window.shutdown_stage == "failed", timeout=3000)
    assert window.isVisible()
    assert window.host.has_unsaved_changes
    assert not window.host.shutdown_requested
    window.bridge.session("reply", '{"choice":"return"}')
    monkeypatch.undo()


def test_navigation_ignores_corruption_and_rejects_unknown_modes(tmp_path: Path) -> None:
    settings = QSettings(str(tmp_path / "navigation.ini"), QSettings.Format.IniFormat)
    nav = ProjectNavigation(settings)
    path = str(tmp_path / "project")
    settings.setValue(nav.key(path), "broken json")
    settings.setValue("recent_projects_v1", '{"not":"a list"}')
    assert nav.read(path) == {}
    assert nav.recent() == []
    nav.remember(path, {"mode": "javascript:unexpected", "projectId": "p"})
    assert nav.recent() == []
    nav.remember(path, {"mode": "quant", "projectId": "p", "secret": "not persisted"})
    assert "secret" not in nav.read(path)
    assert cast(str, nav.recent()[0]["path"]) == path


def test_wrong_original_folder_is_not_modified_and_can_start_new_quant(
    session_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = session_window
    source = source_at(tmp_path / "source.tif")
    before = {p.name: p.read_bytes() for p in source.parent.iterdir()}
    window.open_project(str(source.parent))
    qtbot.waitUntil(lambda: window.shutdown_stage == "entry_error", timeout=10000)
    assert window.host.workspace_path == ""
    assert {p.name: p.read_bytes() for p in source.parent.iterdir()} == before
    window.bridge.session("new_from_folder", "{}")
    qtbot.waitUntil(
        lambda: (
            window.shutdown_stage == "idle"
            and not window.host.operation_busy
            and len(window.host.view.project().rows) == 1
        ),
        timeout=25000,
    )
    assert {p.name: p.read_bytes() for p in source.parent.iterdir()} == before


def test_discarding_unapplied_draft_does_not_also_discard_unsaved_project(
    session_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = session_window
    start(window, qtbot, source_at(tmp_path / "source.tif"))
    window.host.pause_auto_save(True)
    window.host.view.generation += 1
    project = window.host.view.project()
    window.bridge.session(
        "position", json.dumps({"projectId": project.project_id, "mode": "quant", "draft": True})
    )
    window.close()
    assert window.shutdown_stage == "confirm_draft"
    window.bridge.session("reply", '{"choice":"discard"}')
    assert window.shutdown_stage == "confirm_dirty"
    assert window.host.has_unsaved_changes
    assert not window.host.is_closing
    window.bridge.session("reply", '{"choice":"return"}')


def test_busy_cancel_rechecks_draft_then_unsaved_changes_before_shutdown(
    session_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = session_window
    start(window, qtbot, source_at(tmp_path / "source.tif"))
    window.host.pause_auto_save(True)
    window.host.view.generation += 1
    project_id = window.host.view.project().project_id
    window.bridge.session(
        "position", json.dumps({"projectId": project_id, "mode": "quant", "draft": True})
    )
    window.host.begin_operation()
    window.close()
    assert window.shutdown_stage == "confirm_busy"
    window.bridge.session("reply", '{"choice":"cancel"}')
    assert window.shutdown_stage == "cancel"
    window.host.finish_operation("任务已取消")
    # A queued pre-close heartbeat cannot clear the captured unapplied draft.
    window.bridge.session(
        "position", json.dumps({"projectId": project_id, "mode": "quant", "draft": False})
    )
    qtbot.waitUntil(lambda: window.shutdown_stage == "confirm_draft", timeout=3000)
    assert window.isVisible() and not window.host.is_closing
    window.bridge.session("reply", '{"choice":"discard"}')
    assert window.shutdown_stage == "confirm_dirty"
    window.bridge.session("reply", '{"choice":"return"}')
    assert window.isVisible() and window.host.has_unsaved_changes
    window.host.pause_auto_save(True)
    window.close()
    assert window.shutdown_stage == "confirm_dirty"
    window.bridge.session("reply", '{"choice":"save"}')
    qtbot.waitUntil(lambda: window.host.resources_closed, timeout=20000)
