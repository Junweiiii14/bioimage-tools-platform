"""Real WebChannel editing and execution from the workbench buttons."""

from pathlib import Path

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from tests.test_project_navigation_session import js
from tests.test_project_navigation_session import session_window as session_window


def test_web_editor_saves_and_runs_actual_fixture(
    session_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = session_window

    def directory(*_args: object, **_kwargs: object) -> str:
        return str(tmp_path)

    monkeypatch.setattr(QFileDialog, "getExistingDirectory", directory)
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!!window.workflowEditor && !!window.desktopSession") is True,
        timeout=10000,
    )
    js(window, qtbot, "document.querySelector('[data-workflow-open]').click();true")
    assert js(window, qtbot, "document.querySelector('#workflow-editor-dialog').open") is True
    js(window, qtbot, "document.querySelector('[data-wf-choose=new_example]').click();true")
    qtbot.waitUntil(
        lambda: js(window, qtbot, "window.workflowEditor.snapshot().graph?.nodes.length") == 3,
        timeout=20000,
    )
    assert window.authoring.projection is not None
    assert not window.authoring.projection.issues
    js(
        window,
        qtbot,
        "document.querySelector('#wf-title').value='界面真实运行';"
        "document.querySelector('#wf-title').dispatchEvent(new Event('input'));"
        "document.querySelector('#wf-save').click();true",
    )
    qtbot.waitUntil(
        lambda: (
            js(
                window,
                qtbot,
                "!window.workflowEditor.snapshot().pending && !window.workflowEditor.hasDraft()",
            )
            is True
        ),
        timeout=15000,
    )
    assert window.authoring.projection.project.graph.title == "界面真实运行"
    js(window, qtbot, "document.querySelector('[data-wf-select=analyze]').click();true")
    assert (
        js(window, qtbot, "!!document.querySelector('[data-wf-field=\"lanes.0.roi.x0\"]')") is True
    )
    # A save acknowledgement must not rebuild the active parameter form.
    js(
        window,
        qtbot,
        "window._wfFocus=document.querySelector('[data-wf-field=\"lanes.0.roi.x0\"]');"
        "window._wfFocus.dispatchEvent(new Event('input'));"
        "document.querySelector('#wf-save').click();window._wfFocus.focus();true",
    )
    qtbot.waitUntil(
        lambda: (
            js(
                window,
                qtbot,
                "!window.workflowEditor.snapshot().pending && !window.workflowEditor.hasDraft()",
            )
            is True
        ),
        timeout=15000,
    )
    assert (
        js(window, qtbot, "document.activeElement===window._wfFocus && window._wfFocus.isConnected")
        is True
    )
    js(window, qtbot, "document.querySelector('#wf-run').click();true")
    qtbot.waitUntil(
        lambda: (
            js(window, qtbot, "document.querySelectorAll('.wf-result-item').length > 0") is True
        ),
        timeout=40000,
    )
    assert js(window, qtbot, "document.querySelectorAll('.wf-result-item').length") == len(
        window.authoring.projection.outputs
    )
    assert (
        js(window, qtbot, "document.querySelector('#wf-output-list').textContent.includes('4000')")
        is True
    )
    assert js(window, qtbot, "!!document.querySelector('#wf-output-list img')") is True
    assert window.host.workspace_path == ""
    assert window.authoring.projection.project.last_batch_id
    first_source = window.authoring.projection.project.sources[0].asset
    js(window, qtbot, "document.querySelector('[data-wf-choose=bind_example]').click();true")
    qtbot.waitUntil(
        lambda: (
            window.authoring.projection is not None
            and window.authoring.projection.project.sources[0].asset != first_source
        ),
        timeout=15000,
    )
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!window.workflowEditor.snapshot().pending") is True,
        timeout=10000,
    )
    assert js(window, qtbot, "document.querySelectorAll('.wf-result-item').length") == 0
    js(window, qtbot, "document.querySelector('#wf-run').click();true")
    qtbot.waitUntil(
        lambda: (
            js(
                window,
                qtbot,
                "Array.from(document.querySelectorAll('#wf-output-list td'))"
                ".some(cell => cell.textContent === '40.0')",
            )
            is True
        ),
        timeout=40000,
    )
    assert not window.authoring.projection.issues
