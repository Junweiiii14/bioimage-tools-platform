"""Group receipts and asynchronously delivered evidence must remain truthful."""

import json
from pathlib import Path

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot
from wb_tool.api import quant_group_reviewed

from tooling.qt_test_lifecycle import close_and_dispose_window
from tools.wb.tests.test_project_analysis import complete, configured


def no_source_read(row_id: str) -> None:
    """Keep synthetic evidence delivery independent of the source file picker."""


@pytest.mark.parametrize("failure", ["encode", "storage"])
def test_failed_review_save_never_installs_receipt(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    project, paths = configured(tmp_path)
    project, _ = complete(project, paths)
    window = WebWorkbenchWindow(
        settings=QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    )
    try:
        host = window.host
        monkeypatch.setattr(host, "select_source", no_source_read)
        host.view.set_project(project)
        host.view.table.setCurrentCell(0, 0)
        monkeypatch.setattr(host, "_workspace", str(tmp_path))
        monkeypatch.setattr(host, "_saved_revision", project.revision)
        generation = host.view.generation
        monkeypatch.setattr(host, "_saved_generation", generation)

        def fail(*args: object, **kwargs: object) -> str:
            raise RuntimeError("injected save failure")

        with monkeypatch.context() as patch:
            backend = getattr(host, "_background" if failure == "encode" else "_store")
            patch.setattr(backend, "submit", fail)
            window.bridge.request(
                "quant_review_group",
                json.dumps(
                    {
                        "projectId": project.project_id,
                        "sessionEpoch": window.bridge.session_epoch,
                        "figure": "Fig1",
                        "revision": generation,
                    }
                ),
            )
            assert not quant_group_reviewed(host.view.project(), "Fig1")
            qtbot.waitUntil(lambda: not host.operation_busy, timeout=10000)
            assert "injected save failure" in host.view.status.text(), window.bridge.snapshot()[
                "status"
            ]
            assert not quant_group_reviewed(host.view.project(), "Fig1")
            assert host.view.generation == generation
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )


def test_same_revision_restore_and_cross_group_result_link(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, paths = configured(tmp_path)
    project, results = complete(project, paths)
    project = project.model_copy(
        update={"rows": (project.rows[0], project.rows[1].model_copy(update={"figure": "Fig2"}))}
    )
    window = WebWorkbenchWindow(
        settings=QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    )

    def js(script: str) -> object:
        replies: list[object] = []
        window.web.page().runJavaScript(script, replies.append)
        qtbot.waitUntil(lambda: bool(replies), timeout=10000)
        return replies[0]

    try:
        # The test controls evidence arrival, not source decoding or a second worker.
        monkeypatch.setattr(window.host, "select_source", no_source_read)
        window.host.view.set_project(project)
        window.show()
        qtbot.waitUntil(lambda: js("typeof bridge!=='undefined'&&!!bridge") is True)
        window.bridge.publish()
        qtbot.waitUntil(lambda: js("state.rows.length") == 2)
        js("switchMode('quant');true")
        qtbot.waitUntil(lambda: js("document.querySelectorAll('.gr-curve').length") == 3)
        assert js("document.querySelectorAll('.gr-curve .gr-line').length") == 0
        generation = window.host.view.generation
        for evidence in (results, (), results):
            monkeypatch.setattr(window.host, "_project_results", evidence)
            window.bridge.publish()
            expected = 3 if evidence else 0
            qtbot.waitUntil(
                lambda count=expected: (
                    js("document.querySelectorAll('.gr-curve .gr-line').length") == count
                )
            )
            assert window.host.view.generation == generation
        js("switchMode('results');true")
        qtbot.waitUntil(
            lambda: (
                js("!!document.querySelector('[data-gr-value=row1][data-gr-lane=\"2\"]')") is True
            )
        )
        js("document.querySelector('[data-gr-value=row1][data-gr-lane=\"2\"]').click();true")

        def target_selected() -> bool:
            selected = window.host.view.selected_row()
            return selected is not None and selected.row_id == "row1"

        qtbot.waitUntil(target_selected)
        qtbot.waitUntil(
            lambda: (
                js(
                    "state.quant.group.figure==='Fig2'&&!!document.querySelector('.gr-editor')&&"
                    "document.querySelector('.gr-editor h3').textContent.includes('泳道 2')"
                )
                is True
            )
        )
        qtbot.wait(100)  # A queued old-row selection must not win after the target renders.
        assert js("state.selectedId") == "row1"
        assert js("document.querySelector('#gr-band').value") == "target"
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )
