"""Shipped manual controls use durable workers and preserve completed groups."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
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
        assert js("document.querySelector('[data-action=quant_import]').click(); true") is True
        qtbot.waitUntil(
            lambda: len(window.host.view.project().rows) == 1 and not window.host.operation_busy,
            timeout=20000,
        )
        qtbot.waitUntil(lambda: js("mode==='quant'&&Boolean(row()?.preview)") is True)
        # Seed the first rectangle explicitly; copy, numeric positioning and all
        # following calculations exercise the shipped controls. Pointer drawing
        # has a separate geometry contract and is not claimed by this test.
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
