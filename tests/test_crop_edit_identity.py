"""A stale web edit cannot overwrite or approve a newer source crop."""

import json
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.web_bridge import WorkbenchBridge
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot

from tests.test_web_bridge import bridge as bridge
from tooling.qt_test_lifecycle import close_and_dispose_window


def crop_payload(bridge: WorkbenchBridge) -> dict[str, object]:
    snapshot = bridge.snapshot()
    row = bridge.host.view.selected_row()
    assert row is not None and row.source is not None
    return {
        "cropEditContract": "legacy_crop_edit@1",
        "projectId": snapshot["projectId"],
        "sessionEpoch": snapshot["sessionEpoch"],
        "revision": snapshot["revision"],
        "id": row.row_id,
        "sourceId": row.source.sha256,
        "roi": {"x": 50, "y": 40, "width": 300, "height": 30},
        "n": 7,
    }


@pytest.mark.parametrize("action", ["crop", "confirm", "set_lanes"])
def test_stale_crop_commands_preserve_new_draft_and_fresh_edit_works(
    qtbot: QtBot,
    tmp_path: Path,
    bridge: WorkbenchBridge,
    action: str,
) -> None:
    source = tmp_path / "original.tif"
    tifffile.imwrite(source, np.full((120, 400), 40000, dtype=np.uint16))
    original = source.read_bytes()
    host = bridge.host
    host.open_workspace(str(tmp_path / "workspace"), create=True)
    qtbot.waitUntil(host.import_button.isEnabled, timeout=10000)
    host.import_images((str(source),))
    qtbot.waitUntil(host.import_button.isEnabled, timeout=10000)
    host.view.table.setCurrentCell(0, 0)
    qtbot.waitUntil(lambda: not host.operation_busy, timeout=10000)
    host.view.numbers["crop_height"].setValue(30)
    host.view.canvas.roi_drawn.emit((30, 30, 330, 60))
    stale = crop_payload(bridge)
    # Simulate a newer edit in the existing native advanced editor.
    host.view.canvas.roi_drawn.emit((40, 40, 340, 70))
    advanced = host.view.project()
    assert advanced.rows[0].roi is not None and not advanced.rows[0].reviewed
    fresh = crop_payload(bridge)
    assert fresh["revision"] != stale["revision"]
    invalid = [
        stale,
        {**fresh, "projectId": "other-project"},
        {**fresh, "sessionEpoch": int(bridge.session_epoch) + 1},
        {**fresh, "sessionEpoch": False},
        {k: v for k, v in fresh.items() if k != "revision"},
        {**fresh, "cropEditContract": "legacy_crop_edit@0"},
    ]
    for payload in invalid:
        bridge.request(action, json.dumps(payload))
        current = host.view.project()
        assert current == advanced, {
            name: (getattr(advanced, name), getattr(current, name))
            for name in type(advanced).model_fields
            if getattr(advanced, name) != getattr(current, name)
        }
        assert "改变" in str(bridge.snapshot()["status"])
    bridge.request(action, json.dumps(fresh))
    changed = host.view.project().rows[0]
    if action == "crop":
        assert changed.roi is not None and changed.roi.x0 == 50
    elif action == "confirm":
        assert changed.reviewed
    else:
        assert changed.lane_count == 7
    assert source.read_bytes() == original


@pytest.mark.parametrize("change", ["generation", "session"])
def test_real_page_cancels_old_drag_and_accepts_new_gesture(
    qtbot: QtBot,
    tmp_path: Path,
    change: str,
) -> None:
    settings = QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    window = WebWorkbenchWindow(settings=settings)
    originals = tmp_path / "originals"
    originals.mkdir()
    source = originals / "gesture-source.tif"
    tifffile.imwrite(source, np.full((120, 400), 40000, dtype=np.uint16))
    original = source.read_bytes()
    window.show()
    try:
        window.start_from_images([source], automatic=False)
        qtbot.waitUntil(
            lambda: bool(window.host.view.project().rows) and not window.host.operation_busy,
            timeout=20000,
        )
        host = window.host
        window.bridge.request("select", json.dumps({"id": host.view.project().rows[0].row_id}))
        qtbot.waitUntil(lambda: not host.operation_busy, timeout=10000)
        host.view.numbers["crop_height"].setValue(30)
        host.view.canvas.roi_drawn.emit((30, 30, 330, 60))
        assert host.view.project().rows[0].roi is not None, host.view.status.text()
        qtbot.waitUntil(
            lambda: not host.operation_busy and not host.has_unsaved_changes, timeout=10000
        )
        window.bridge.publish()

        def js(script: str) -> object:
            values: list[object] = []
            window.web.page().runJavaScript(script, values.append)
            qtbot.waitUntil(lambda: bool(values), timeout=10000)
            return values[0]

        qtbot.waitUntil(
            lambda: (
                js("typeof bridge!=='undefined' && bridge!==null && !!row()?.roi && !state.busy")
                is True
            ),
            timeout=20000,
        )
        assert (
            js(
                "(()=>{$('#home-view').hidden=true;$('#work-view').hidden=false;"
                "switchMode('review');return true})()"
            )
            is True
        )
        qtbot.waitUntil(
            lambda: (
                js(
                    "!$('#crop-overlay').hidden && "
                    "$('#crop-overlay').getBoundingClientRect().width>0"
                )
                is True
            ),
            timeout=10000,
        )

        def start_gesture() -> None:
            # Freeze the native identity once. Poll only before sending an event;
            # rejection of an actual pointerdown must fail, never trigger a retry.
            snapshot = window.bridge.snapshot()
            selected = host.view.selected_row()
            assert selected is not None and selected.source is not None
            identity = {
                "projectId": snapshot["projectId"],
                "sessionEpoch": snapshot["sessionEpoch"],
                "revision": snapshot["revision"],
                "id": selected.row_id,
                "sourceId": selected.source.sha256,
            }
            before = js("window.testGestureDispatches||0")
            assert isinstance(before, (int, float))
            start = """(()=>{const expected=EXPECTED,current=cropIdentity();
                if(state.busy||!row()?.roi||
                   !Object.keys(expected).every(key=>expected[key]===current[key]))return 'waiting';
                switchMode('review');
                const el=$('#crop-overlay'),rect=el.getBoundingClientRect();
                if(el.hidden||rect.width<=0||rect.height<=0)return 'waiting';
                el.setPointerCapture=()=>{};
                window.testGesture={x:rect.x+rect.width/2,y:rect.y+rect.height/2};
                window.testGestureDispatches=(window.testGestureDispatches||0)+1;
                el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId:1,
                    clientX:testGesture.x,clientY:testGesture.y}));
                return drag!==null;})()""".replace("EXPECTED", json.dumps(identity))

            dispatched: list[object] = []

            def attempt() -> bool:
                result = js(start)
                if result == "waiting":
                    return False
                dispatched.append(result)
                return True

            qtbot.waitUntil(attempt, timeout=10000)
            assert dispatched == [True], js(
                "JSON.stringify({busy:state.busy,mode,identity:cropIdentity(),"
                "roi:row()?.roi,intake:state.intake,dispatches:window.testGestureDispatches})"
            )
            assert js("window.testGestureDispatches") == before + 1

        # A real dispatched event rejected by the page must fail immediately,
        # even though pytest-qt retries AssertionError from waitUntil callbacks.
        assert (
            js(
                "(()=>{$('#crop-overlay').addEventListener('pointerdown',"
                "event=>event.stopImmediatePropagation(),{capture:true,once:true});return true})()"
            )
            is True
        )
        before_rejection = js("window.testGestureDispatches||0")
        assert isinstance(before_rejection, (int, float))
        with pytest.raises(AssertionError, match="busy"):
            start_gesture()
        assert js("window.testGestureDispatches") == before_rejection + 1
        start_gesture()
        if change == "generation":
            host.view.canvas.roi_drawn.emit((40, 40, 340, 70))
        else:
            window.bridge.replace_host(host)
        qtbot.waitUntil(
            lambda: not host.operation_busy and not host.has_unsaved_changes, timeout=10000
        )
        advanced = host.view.project()
        window.bridge.publish()
        qtbot.waitUntil(lambda: js("drag===null") is True, timeout=10000)
        assert (
            js(
                "(()=>{$('#crop-overlay').dispatchEvent(new PointerEvent('pointerup',"
                "{bubbles:true,pointerId:1}));return true})()"
            )
            is True
        )
        current = host.view.project()
        assert current == advanced, {
            name: (getattr(advanced, name), getattr(current, name))
            for name in type(advanced).model_fields
            if getattr(advanced, name) != getattr(current, name)
        }
        qtbot.waitUntil(lambda: not host.operation_busy, timeout=10000)
        start_gesture()
        generation = host.view.generation
        assert (
            js("""(()=>{const el=$('#crop-overlay');el.dispatchEvent(new PointerEvent('pointermove',
            {bubbles:true,pointerId:1,clientX:testGesture.x+4,clientY:testGesture.y}));
            el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerId:1}));
            return true;})()""")
            is True
        )
        qtbot.waitUntil(lambda: host.view.generation > generation, timeout=10000)
        changed = host.view.project().rows[0]
        assert changed.roi != advanced.rows[0].roi and not changed.reviewed
        assert source.read_bytes() == original
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )
