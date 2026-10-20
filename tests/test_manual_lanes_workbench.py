"""Shipped manual controls use durable workers and preserve completed groups."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot
from wb_tool.api import WBAnalysisProject

from tooling.qt_test_lifecycle import close_and_dispose_window


def test_copy_manual_multipeak_history_new_group_save_and_reopen(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "originals").mkdir()
    source = tmp_path / "originals/source.tif"
    y = np.arange(120)
    signal = 20 + np.maximum(0, 100 - 10 * np.abs(y - 30)) + np.maximum(0, 80 - 8 * np.abs(y - 80))
    tifffile.imwrite(source, np.repeat((255 - signal).astype(np.uint8)[:, None], 100, axis=1))
    original = source.read_bytes()
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    (tmp_path / "projects").mkdir()

    def choose_files(*args: object) -> tuple[list[str], str]:
        return [str(source)], ""

    def choose_parent(*args: object) -> str:
        return str(tmp_path / "projects")

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", choose_files)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", choose_parent)
    window = WebWorkbenchWindow(settings=settings)

    def js(code: str) -> object:
        values: list[object] = []
        window.web.page().runJavaScript(code, values.append)
        qtbot.waitUntil(lambda: bool(values), timeout=10000)
        return values[0]

    def idle_result() -> bool:
        return bool(window.host.project_results) and not window.host.operation_busy

    def plan():
        p = window.host.view.project()
        assert isinstance(p, WBAnalysisProject)
        return p.analyses[0]

    def synced() -> None:
        selected = window.host.view.selected_row()
        assert selected is not None
        qtbot.waitUntil(
            lambda: (
                js(
                    f"!state.busy && state.quant?.revision==={window.host.view.generation}"
                    f" && state.quant?.rowId==={selected.row_id!r}"
                    f" && row()?.id==={selected.row_id!r}"
                )
                is True
            ),
            timeout=10000,
        )

    try:
        window.show()
        qtbot.waitUntil(lambda: js("Boolean(typeof bridge!=='undefined'&&bridge)") is True)
        js(
            "window.initialQuantRoute=null;bridge.sessionStateChanged.connect(raw=>{"
            "const next=JSON.parse(raw);if(next.route?.projectId&&next.route.mode==='quant')"
            "window.initialQuantRoute=next.route;});true"
        )
        assert js("document.querySelector('[data-action=quant_import]').click(); true") is True
        qtbot.waitUntil(
            lambda: len(window.host.view.project().rows) == 1 and not window.host.operation_busy,
            timeout=20000,
        )
        qtbot.waitUntil(lambda: js("mode==='quant'&&Boolean(row()?.preview)") is True)
        # Import's first quant snapshot can precede the session's initial route.
        # Consume that received route before zoom/pointer coordinates are established;
        # the same route token cannot then reset zoom during the real Qt gesture.
        qtbot.waitUntil(
            lambda: (
                js(
                    "initialQuantRoute?.projectId===state.projectId && !state.busy && "
                    "state.quant?.rowId===row()?.id"
                )
                is True
            ),
            timeout=10000,
        )
        js("desktopSession.route();true")
        # Real Qt pointer events verify view translation, cancellation and the
        # original-coordinate mapping after zoom/pan; numerical fixtures follow.
        js("manualLanes.activate();focusCrop=false;zoom=1.4;render();true")
        qtbot.wait(100)

        def image_point(x: int, y: int) -> QPoint:
            coords = js(
                "(()=>{const b=$('#image-transform').getBoundingClientRect();"
                f"return JSON.stringify([b.left+{x}/row().width*b.width,"
                f"b.top+{y}/row().height*b.height])"
                "})()"
            )
            assert isinstance(coords, str)
            coords = json.loads(coords)
            return QPoint(round(coords[0]), round(coords[1]))

        target_widget = window.web.focusProxy()
        assert target_widget is not None
        js("document.querySelector('.image-actions .button').click();true")
        start = image_point(50, 60)
        QTest.mousePress(target_widget, Qt.MouseButton.LeftButton, pos=start)
        qtbot.waitUntil(lambda: js("Boolean(imagePan.drag)") is True)
        QTest.mouseMove(target_widget, start + QPoint(40, 25))
        qtbot.waitUntil(lambda: js("imagePan.x===40&&imagePan.y===25") is True)
        QTest.mouseRelease(target_widget, Qt.MouseButton.LeftButton, pos=start + QPoint(40, 25))
        qtbot.waitUntil(lambda: js("imagePan.drag===null") is True)
        assert js("JSON.stringify([imagePan.x,imagePan.y,manualLanes.boxes.length])") == "[40,25,0]"
        # Cancel restores only the view; it must not create or alter lane boxes.
        QTest.mousePress(target_widget, Qt.MouseButton.LeftButton, pos=start)
        qtbot.waitUntil(lambda: js("Boolean(imagePan.drag)") is True)
        QTest.mouseMove(target_widget, start + QPoint(15, 10))
        qtbot.waitUntil(lambda: js("imagePan.x===55&&imagePan.y===35") is True)
        js("$('#image-viewport').dispatchEvent(new PointerEvent('pointercancel'));true")
        assert js("imagePan.drag===null&&imagePan.x===40&&imagePan.y===25") is True
        QTest.mouseRelease(target_widget, Qt.MouseButton.LeftButton, pos=start + QPoint(15, 10))
        assert js("JSON.stringify([imagePan.x,imagePan.y,manualLanes.boxes.length])") == "[40,25,0]"
        js("document.querySelector('.image-actions .button').click();true")
        # Space must activate focused native controls rather than start panning.
        js("document.querySelector('.image-actions .button').focus();true")
        QTest.keyClick(target_widget, Qt.Key.Key_Space)
        qtbot.waitUntil(lambda: js("imagePan.hand&&!imagePan.space") is True)
        QTest.keyClick(target_widget, Qt.Key.Key_Space)
        qtbot.waitUntil(lambda: js("!imagePan.hand&&!imagePan.space") is True)
        js("document.querySelector('#manual-lane-tools summary').focus();true")
        QTest.keyClick(target_widget, Qt.Key.Key_Space)
        qtbot.waitUntil(lambda: js("document.querySelector('[data-manual-tools]').open") is True)
        QTest.keyClick(target_widget, Qt.Key.Key_Space)
        qtbot.waitUntil(lambda: js("!document.querySelector('[data-manual-tools]').open") is True)
        assert (
            js(
                "(()=>{const e=new KeyboardEvent('keydown',"
                "{code:'Space',bubbles:true,cancelable:true});"
                "$('#image-viewport').dispatchEvent(e);"
                "return e.defaultPrevented&&imagePan.space})()"
            )
            is True
        )
        js("document.dispatchEvent(new KeyboardEvent('keyup',{code:'Space'}));true")
        assert js("!imagePan.space") is True
        # Native details toggles may schedule layout. Observe its completed frames
        # before mapping source points; do not loosen the original-coordinate oracle.
        js(
            "window.pointerLayoutReady=false;requestAnimationFrame(()=>{fitImage();"
            "requestAnimationFrame(()=>{window.pointerLayoutReady=true;});});true"
        )
        qtbot.waitUntil(lambda: js("pointerLayoutReady") is True, timeout=10000)
        assert js("zoom===1.4") is True
        QTest.mousePress(target_widget, Qt.MouseButton.LeftButton, pos=image_point(35, 40))
        qtbot.waitUntil(lambda: js("Boolean(manualLanes.dragging)") is True)
        QTest.mouseMove(target_widget, image_point(55, 80))
        qtbot.waitUntil(lambda: js("Boolean(manualLanes.dragging?.next)") is True)
        QTest.mouseRelease(target_widget, Qt.MouseButton.LeftButton, pos=image_point(55, 80))
        qtbot.waitUntil(lambda: js("manualLanes.boxes.length") == 1)
        box = js("JSON.stringify(manualLanes.boxes[0])")
        assert isinstance(box, str)
        box = json.loads(box)
        assert box == pytest.approx({"x": 35, "y": 40, "width": 20, "height": 40}, abs=1)
        assert (
            js(
                "manualLanes.boxes=[{x:5,y:0,width:20,height:120}];"
                "manualLanes.activate();render();"
                "document.querySelector('[data-lane-action=copy]').click(); true"
            )
            is True
        )
        assert js("manualLanes.boxes.length") == 2
        assert (
            js(
                "document.querySelector('[data-manual-lane-field=x]').value=60;"
                "document.querySelector('[data-manual-lane-field=x]')"
                ".dispatchEvent(new Event('change',{bubbles:true}));"
                "document.querySelector('[data-manual-quant-run]').click();true"
            )
            is True
        )
        qtbot.waitUntil(idle_result, timeout=30000)
        synced()
        assert [len(lane.bands) for lane in plan().request.lanes] == [2, 2]
        assert [
            [b.signal for b in lane.bands] for lane in window.host.project_results[0].result.lanes
        ] == [[1000, 800], [1000, 800]]
        # T046 lands on the approved whole-group review after calculation.
        # Re-enter the retained manual tools before testing their original controls.
        qtbot.waitUntil(lambda: js("document.querySelectorAll('.gr-curve').length===2") is True)
        assert js("document.querySelectorAll('.gr-curve .gr-baseline').length") == 4
        assert js("document.querySelector('[data-gr-action=manual]').click();true") is True
        qtbot.waitUntil(
            lambda: js("Boolean(document.querySelector('[data-quant-profiles]'))") is True
        )
        before = plan().request
        assert (
            js(
                "send('quant_band',{...manualLanes.identity(),lane:1,operation:'add',start:100,end:110});true"
            )
            is True
        )
        qtbot.waitUntil(
            lambda: len(plan().request.lanes[0].bands) == 3 and not window.host.operation_busy,
            timeout=30000,
        )
        synced()
        assert js("send('quant_history',{...manualLanes.identity(),direction:'undo'});true") is True
        qtbot.waitUntil(
            lambda: (
                replace(plan().request, revision=0) == replace(before, revision=0)
                and not window.host.operation_busy
            ),
            timeout=30000,
        )
        synced()
        assert js("send('quant_history',{...manualLanes.identity(),direction:'redo'});true") is True
        qtbot.waitUntil(
            lambda: len(plan().request.lanes[0].bands) == 3 and not window.host.operation_busy,
            timeout=30000,
        )
        completed = plan()
        synced()
        assert js("document.querySelector('[data-lane-action=reselect]').click();true") is True
        assert js("manualLanes.boxes.length") == 0
        assert plan() == completed
        assert js("send('quant_new_group',{...manualLanes.identity(),name:'Fig2B'});true") is True
        qtbot.waitUntil(
            lambda: len(window.host.view.project().rows) == 2 and not window.host.operation_busy,
            timeout=20000,
        )
        assert plan() == completed
        synced()
        assert (
            js(
                "send('quant_move_row',{...manualLanes.identity(),figure:'Fig1',protein:'手动新排'});true"
            )
            is True
        )
        qtbot.waitUntil(lambda: window.host.view.project().figure_order == ("Fig1",), timeout=10000)
        synced()
        assert (
            js(
                "send('quant_rename',{...manualLanes.identity(),figure:'Fig1A',protein:'手动新排'});true"
            )
            is True
        )
        qtbot.waitUntil(
            lambda: window.host.view.project().figure_order == ("Fig1A",), timeout=10000
        )
        assert {r.figure for r in window.host.view.project().rows} == {"Fig1A"}
        assert plan() == completed
        window.host.save()
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=20000)
        workspace = window.host.workspace_path
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )
        window = WebWorkbenchWindow(settings=settings)
        window.open_project(workspace)
        qtbot.waitUntil(idle_result, timeout=30000)
        assert len(window.host.view.project().rows) == 2
        assert plan().request == completed.request and source.read_bytes() == original
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )
