"""The shipped green workbench can measure an original without cropping or montage."""

import json
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import tifffile
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot
from wb_tool.api import WBAnalysisProject

from tooling.qt_test_lifecycle import close_and_dispose_window


def test_real_page_manual_import_compute_save_reopen_without_automatic_or_compose(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    originals = tmp_path / "originals"
    originals.mkdir()
    source = originals / "original.tiff"
    profile = 3000 + np.arange(160) * 10
    profile[40:60] += 1000
    tifffile.imwrite(source, np.repeat(profile.astype(np.uint16)[:, None], 100, axis=1))
    original = source.read_bytes()
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    # Deliberately fail allocation once; the workbench retry must keep manual mode.
    settings.setValue("project_parent", str(originals))
    window = WebWorkbenchWindow(settings=settings)
    selections: list[bool] = []

    def js(script: str) -> object:
        received: list[object] = []

        def completed(value: object) -> None:
            received.append(value)

        window.web.page().runJavaScript(script, completed)
        qtbot.waitUntil(lambda: bool(received), timeout=10000)
        return received[0]

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Independent measurement must not detect crops or compose")

    def choose_files(*args: object) -> tuple[list[str], str]:
        selections.append(True)
        return [str(source)], ""

    def choose_parent(*args: object) -> str:
        return str(tmp_path / "projects")

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", choose_files)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", choose_parent)
    monkeypatch.setattr(window.host.automatic, "analyze", forbidden)
    monkeypatch.setattr(window.host, "compose", forbidden)
    try:
        window.show()
        qtbot.waitUntil(lambda: js("Boolean(typeof bridge !== 'undefined' && bridge)") is True)
        assert js("document.querySelector('[data-action=quant_import]').click(); true") is True
        qtbot.waitUntil(lambda: bool(selections), timeout=5000)
        qtbot.waitUntil(
            lambda: not window.host.operation_busy and "重叠" in window.host.view.status.text(),
            timeout=20000,
        )
        qtbot.waitUntil(lambda: js("!document.querySelector('#retry-location').hidden") is True)
        assert js("document.querySelector('#retry-location').click(); true") is True
        qtbot.waitUntil(
            lambda: (
                len(window.host.view.project().rows) == 1
                or (not window.host.operation_busy and "失败" in window.host.view.status.text())
            ),
            timeout=20000,
        )
        assert len(window.host.view.project().rows) == 1, window.host.view.status.text()
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=20000)
        assert not window.host.automatic.last_output_path
        assert window.host.view.project().rows[0].roi is None
        qtbot.waitUntil(lambda: js("mode === 'quant' && Boolean(row()?.preview)") is True)
        initial = window.host.view.project()
        selected = initial.rows[0]
        assert selected.source is not None
        payload: dict[str, object] = {
            "projectId": initial.project_id,
            "sessionEpoch": window.bridge.session_epoch,
            "id": selected.row_id,
            "sourceId": selected.source.sha256,
            "revision": window.host.view.generation,
            "roi": {"x": 10, "y": 38, "width": 80, "height": 24},
            "n": 2,
            "polarity": "light",
            "emptyLanes": [],
        }
        for invalid in (
            {"projectId": "another-project"},
            {"sourceId": "f" * 64},
            {"revision": -1},
            {"n": True},
            {"n": 2.5},
            {"polarity": "invalid"},
            {"roi": {"x": 10, "y": 38, "width": 80.5, "height": 24}},
            {"emptyLanes": [True]},
            {"resetBounds": 1},
        ):
            window.bridge.request("quant_target", json.dumps({**payload, **invalid}))
            assert window.host.view.project() == initial
            assert not window.host.operation_busy
            assert window.bridge.snapshot()["status"] != window.host.view.status.text()
        assert js("document.querySelector('[data-manual-quant-whole]').click(); true") is True
        changes = json.dumps({"x": 10, "y": 38, "width": 80, "height": 24})
        assert (
            js(
                f"""(() => {{
                for (const [key, value] of Object.entries({changes})) {{
                    const selector = '[data-manual-quant-coordinate=' + key + ']';
                    const input = document.querySelector(selector);
                    input.value = String(value);
                    input.dispatchEvent(new Event('input', {{bubbles:true}}));
                }}
                for (const [key, value] of Object.entries({{n:'2', polarity:'light'}})) {{
                    const input = document.querySelector('[data-manual-quant-field=' + key + ']');
                    input.value = value; input.dispatchEvent(new Event('input', {{bubbles:true}}));
                }}
                document.querySelector('[data-manual-quant-run]').click(); return true;
            }})()"""
            )
            is True
        )
        qtbot.waitUntil(lambda: bool(window.host.project_results), timeout=30000)
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=20000)
        project = window.host.view.project()
        assert isinstance(project, WBAnalysisProject)
        assert project.rows[0].roi is not None and project.rows[0].roi.width == 80
        assert project.rows[0].roi.y1 - project.rows[0].roi.y0 == 24
        assert project.template.crop_height == 60
        assert [
            lane.bands[0].signal for lane in window.host.project_results[0].result.lanes
        ] == pytest.approx([20000, 20000])
        assert window.bridge.snapshot()["montage"] is None
        qtbot.waitUntil(
            lambda: (
                js(
                    "Boolean(document.querySelector('[data-quant-profiles]') && "
                    "!document.querySelector('[data-quant-profiles]').disabled)"
                )
                is True
            )
        )
        assert js("document.querySelector('[data-quant-profiles]').click(); true") is True
        assert js("document.querySelector('#quant-profiles-dialog').open") is True
        assert js("document.querySelectorAll('#quant-profiles-all .quant-profile-row').length") == 2
        assert js("document.querySelectorAll('#quant-profiles-all .quant-fill').length") == 2
        assert js("document.querySelectorAll('#quant-profiles-all .quant-baseline').length") == 2
        assert (
            js("document.querySelectorAll('#quant-profiles-all .quant-profile-peak').length") == 2
        )
        assert js("document.querySelector('[data-profile-select=\"2\"]').click(); true") is True
        old_run = project.analyses[0].run
        assert old_run is not None
        old_baseline = project.analyses[0].request.lanes[1].bands[0].baseline
        assert old_baseline is not None
        assert (
            js(
                "document.querySelector('#quant-profile-single [data-quant-point=baselineStart]')"
                ".dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowUp',bubbles:true})); true"
            )
            is True
        )

        def updated_run() -> bool:
            current = window.host.view.project()
            return (
                isinstance(current, WBAnalysisProject)
                and current.analyses[0].run is not None
                and current.analyses[0].run != old_run
                and not window.host.operation_busy
            )

        qtbot.waitUntil(updated_run, timeout=30000)
        project = window.host.view.project()
        assert isinstance(project, WBAnalysisProject)
        baseline = project.analyses[0].request.lanes[1].bands[0].baseline
        assert baseline is not None and baseline.left_value == old_baseline.left_value + 1
        assert window.host.project_results[0].result.lanes[0].bands[0].signal == pytest.approx(
            20000
        )
        assert js("document.querySelector('[data-close-quant-profiles]').click(); true") is True
        assert js("document.querySelector('#quant-profiles-dialog').open") is False
        qtbot.waitUntil(lambda: js("!state.busy") is True)
        assert (
            js(
                "manualQuant.openProfiles(); manualQuant.closeProfiles(); "
                "switchMode('results'); true"
            )
            is True
        )
        # Native dialog close is queued. Its late event must not restore the
        # quantification inspector over the results page and hide quality reasons.
        qtbot.wait(100)
        assert js("document.querySelector('#inspector-title').textContent") == "输出结果"
        assert (
            js(
                "document.querySelector('#inspector-content').textContent.includes('原始积分不等于有效信号')"
            )
            is True
        )
        workspace = window.host.workspace_path
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )
        window = WebWorkbenchWindow(settings=settings)
        monkeypatch.setattr(window.host.automatic, "analyze", forbidden)
        monkeypatch.setattr(window.host, "compose", forbidden)
        window.open_project(workspace)
        qtbot.waitUntil(lambda: bool(window.host.project_results), timeout=30000)
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=20000)
        restored = cast(WBAnalysisProject, window.host.view.project())
        assert restored.rows == project.rows
        assert window.host.project_results[0].result.request == project.analyses[0].request
        assert source.read_bytes() == original
        # The same shipped page returns reviewed crops after reopening, using
        # local origin memory rather than an archive-supplied destination.
        qtbot.waitUntil(lambda: js("Boolean(typeof bridge !== 'undefined' && bridge)") is True)
        assert js("switchMode('review'); true") is True
        qtbot.waitUntil(
            lambda: js("Boolean(document.querySelector('[data-action=return_crop]'))") is True
        )
        current = window.host.view.project()
        selected = current.rows[0]
        assert selected.source is not None
        valid_return: dict[str, object] = {
            "projectId": current.project_id,
            "sessionEpoch": window.bridge.session_epoch,
            "id": selected.row_id,
            "sourceId": selected.source.sha256,
            "revision": window.host.view.generation,
        }
        for bad in (
            {"projectId": "other"},
            {"sourceId": "0" * 64},
            {"revision": True},
            {"revision": -1},
            {"locate": "true"},
        ):
            window.bridge.request("return_crop", json.dumps({**valid_return, **bad}))
            assert not list(originals.glob("*_WB裁图_*"))
            assert not window.host.operation_busy
        # Any extra file picker means persisted local origin lookup failed.
        monkeypatch.setattr(QFileDialog, "getOpenFileName", forbidden)
        assert js("document.querySelector('[data-action=return_crop]').click(); true") is True
        qtbot.waitUntil(
            lambda: (
                bool(list(originals.glob("*_记录.json")))
                or (not window.host.operation_busy and "失败" in window.host.view.status.text())
            ),
            timeout=30000,
        )
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=20000)
        assert len(list(originals.glob("*_记录.json"))) == 1, window.host.view.status.text()
        assert "裁图已核验并回存" in window.host.view.status.text()
        raw_path = next(originals.glob("*_原值.tiff"))
        with tifffile.TiffFile(raw_path) as image:
            page = image.pages[0]
            assert isinstance(page, tifffile.TiffPage)
            np.testing.assert_array_equal(
                page.asarray(),
                np.repeat(profile.astype(np.uint16)[:, None], 100, axis=1)[38:62, 10:90],
            )
        assert source.read_bytes() == original
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )
