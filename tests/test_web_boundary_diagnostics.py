"""Actual host/WebChannel failures must be visible without discarding edits."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from bioimage_app.diagnostics import DesktopDiagnostics
from bioimage_app.web_bridge import WorkbenchBridge
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot

from tests.test_intake_web_ui import javascript
from tests.test_project_measurements import setup
from tests.test_web_bridge import bridge as bridge
from tooling.qt_test_lifecycle import close_and_dispose_window

SECRET = "private-source-path-and-pixels"


def records(diagnostics: DesktopDiagnostics) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for line in diagnostics.path.read_text(encoding="utf-8").splitlines():
        message = json.loads(line)["message"]
        if message.startswith("web-boundary "):
            result.append(json.loads(message.removeprefix("web-boundary ")))
    return result


@pytest.mark.parametrize("failure", [ValueError, RuntimeError, MemoryError])
def test_snapshot_failure_logs_once_and_recovers(
    bridge: WorkbenchBridge,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: type[Exception],
) -> None:
    bridge.timer.stop()
    published: list[str] = []
    bridge.stateChanged.connect(published.append)
    original = bridge.snapshot
    project = bridge.host.view.project()

    def broken() -> dict[str, object]:
        raise failure(SECRET)

    diagnostics = DesktopDiagnostics(tmp_path / "logs")
    try:
        monkeypatch.setattr(bridge, "snapshot", broken)
        for _ in range(8):
            bridge.publish()
        assert published == []
        found = records(diagnostics)
        assert len(found) == 1
        assert found[0]["action"] == "snapshot"
        assert found[0]["exception"] == failure.__name__
        assert found[0]["stack"] and found[0]["version"]
        assert SECRET not in json.dumps(found)
        assert bridge.host.view.project() == project
        monkeypatch.setattr(bridge, "snapshot", original)
        bridge.publish()
        assert len(published) == 1
    finally:
        diagnostics.close()


def test_native_incomplete_edit_is_not_a_corrupt_snapshot(
    bridge: WorkbenchBridge, tmp_path: Path
) -> None:
    bridge.timer.stop()
    published: list[str] = []
    bridge.stateChanged.connect(published.append)
    diagnostics = DesktopDiagnostics(tmp_path / "logs")
    try:
        bridge.host.view.name.setText("")
        for _ in range(4):
            bridge.publish()
        assert records(diagnostics) == []
        assert bridge.host.view.name.text() == ""
        bridge.host.view.name.setText("completed edit")
        bridge.publish()
        assert json.loads(published[-1])["projectName"] == "completed edit"
    finally:
        diagnostics.close()


@pytest.fixture
def page(qtbot: QtBot, tmp_path: Path) -> Iterator[WebWorkbenchWindow]:
    window = WebWorkbenchWindow(
        settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat)
    )
    window.show()
    try:
        qtbot.waitUntil(lambda: javascript(window, qtbot, "!!bridge") is True)
        setup(qtbot, tmp_path, window.host)
        window.bridge.publish()
        qtbot.waitUntil(lambda: javascript(window, qtbot, "state.rows.length===2") is True)
        window.bridge.timer.stop()
        javascript(window, qtbot, "advancedWorkspace.open('template');true")
        qtbot.waitUntil(
            lambda: (
                javascript(window, qtbot, "!!document.querySelector('#advanced-editor')") is True
            )
        )
        javascript(
            window,
            qtbot,
            "const field=document.querySelector('[data-adv-path=\"template.row_gap\"]');"
            "field.value=29;field.dispatchEvent(new Event('input',{bubbles:true}));true",
        )
        assert javascript(window, qtbot, "advancedWorkspace.hasDraft()") is True
        yield window
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )


@pytest.mark.parametrize("signal", ["stateChanged", "progressChanged", "sessionStateChanged"])
def test_bad_channel_payload_is_deduplicated_and_draft_survives(
    page: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path, signal: str
) -> None:
    diagnostics = DesktopDiagnostics(tmp_path / "logs")
    try:
        for _ in range(8):
            getattr(page.bridge, signal).emit('{"' + SECRET)
        qtbot.waitUntil(lambda: len(records(diagnostics)) == 1)
        # A round-trip observes all preceding queued WebChannel deliveries.
        assert javascript(page, qtbot, "advancedWorkspace.hasDraft()") is True
        assert len(records(diagnostics)) == 1
        assert "重试" in str(
            javascript(page, qtbot, "document.querySelector('#toast').textContent")
        )
        assert SECRET not in json.dumps(records(diagnostics))
        page.bridge.stateChanged.emit(json.dumps(page.bridge.snapshot() | {"probe": "recovered"}))
        qtbot.waitUntil(lambda: javascript(page, qtbot, "state.probe") == "recovered")
        assert javascript(page, qtbot, "advancedWorkspace.hasDraft()") is True
        assert (
            javascript(
                page, qtbot, "document.querySelector('[data-adv-path=\"template.row_gap\"]').value"
            )
            == "29"
        )
    finally:
        diagnostics.close()


def test_render_failure_reports_safe_stack_and_next_state_recovers(
    page: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    diagnostics = DesktopDiagnostics(tmp_path / "logs")
    try:
        javascript(
            page,
            qtbot,
            "window.originalRender=render;render=()=>{throw new TypeError('" + SECRET + "')};true",
        )
        raw = json.dumps(page.bridge.snapshot())
        for _ in range(8):
            page.bridge.stateChanged.emit(raw)
        qtbot.waitUntil(lambda: len(records(diagnostics)) == 1)
        found = records(diagnostics)[0]
        assert found["exception"] == "TypeError" and found["stack"]
        assert SECRET not in json.dumps(found)
        javascript(page, qtbot, "render=window.originalRender;true")
        page.bridge.stateChanged.emit(json.dumps(page.bridge.snapshot() | {"probe": "rendered"}))
        qtbot.waitUntil(lambda: javascript(page, qtbot, "state.probe") == "rendered")
        assert javascript(page, qtbot, "advancedWorkspace.hasDraft()") is True
        assert (
            javascript(
                page, qtbot, "document.querySelector('[data-adv-path=\"template.row_gap\"]').value"
            )
            == "29"
        )
    finally:
        javascript(page, qtbot, "render=window.originalRender;true")
        diagnostics.close()


@pytest.mark.parametrize("damage", ["json", "shape", "render"])
def test_advanced_receipt_retains_pending_read_and_unsaved_draft(
    page: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path, damage: str
) -> None:
    diagnostics = DesktopDiagnostics(tmp_path / "logs")
    try:
        javascript(
            page,
            qtbot,
            "window.originalRequest=bridge.request;"
            "bridge.request=(action,raw)=>{window.readRequest=JSON.parse(raw)};"
            "advancedWorkspace.open('template');true",
        )
        request = javascript(page, qtbot, "window.readRequest.requestId")
        response = {
            "requestId": request,
            "status": "done",
            "data": page.bridge.advanced_commands.snapshot(),
        }
        raw = json.dumps(response)
        if damage == "json":
            raw = '{"' + SECRET
        elif damage == "shape":
            raw = json.dumps({"requestId": request, "status": "done", "data": []})
        else:
            damaged = page.bridge.advanced_commands.snapshot() | {"template": None}
            raw = json.dumps(response | {"data": damaged})
        for _ in range(8):
            page.bridge.advancedStateChanged.emit(raw)
        qtbot.waitUntil(lambda: len(records(diagnostics)) == 1)
        assert javascript(page, qtbot, "advancedWorkspace.hasDraft()") is True
        assert SECRET not in json.dumps(records(diagnostics))
        # The matching valid reply is still accepted, with the remembered draft.
        page.bridge.advancedStateChanged.emit(json.dumps(response))
        qtbot.waitUntil(
            lambda: javascript(page, qtbot, "!!document.querySelector('#advanced-editor')") is True
        )
        assert (
            javascript(
                page, qtbot, "document.querySelector('[data-adv-path=\"template.row_gap\"]').value"
            )
            == "29"
        )
        assert javascript(page, qtbot, "advancedWorkspace.hasDraft()") is True
        assert page.host.view.project().template.row_gap != 29
    finally:
        javascript(page, qtbot, "bridge.request=window.originalRequest;true")
        diagnostics.close()


def test_diagnostic_sink_failure_does_not_replace_snapshot_error(
    bridge: WorkbenchBridge, monkeypatch: pytest.MonkeyPatch
) -> None:
    notices: list[str] = []
    bridge.timer.stop()
    bridge.diagnosticNotice.connect(notices.append)

    def broken() -> dict[str, object]:
        raise RuntimeError(SECRET)

    def failed_sink(_message: str) -> None:
        raise OSError("log unavailable")

    monkeypatch.setattr(bridge, "snapshot", broken)
    monkeypatch.setattr("bioimage_app.diagnostics.qWarning", failed_sink)
    bridge.publish()
    bridge.publish()
    assert len(notices) == 1 and "重试" in notices[0]


@pytest.mark.parametrize(
    "raw",
    [
        "[]",
        "null",
        '{"action":[]}',
        '{"action":"state","exception":[],"phase":{},"stack":[{},"C:/private/file.js:1:2"]}',
    ],
)
def test_diagnostic_transport_rejects_untrusted_shapes_without_paths(
    bridge: WorkbenchBridge, tmp_path: Path, raw: str
) -> None:
    bridge.timer.stop()
    diagnostics = DesktopDiagnostics(tmp_path / "logs")
    try:
        bridge.reportUiFailure(raw)
        assert "C:/private" not in json.dumps(records(diagnostics))
    finally:
        diagnostics.close()
