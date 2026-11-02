"""Real WebChannel editing and execution from the workbench buttons."""

import json
from pathlib import Path

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from bioimage_app.workflow_batch_session import WorkflowBatchStatus
from pydantic import TypeAdapter
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot
from wb_tool.api import wb_validation_input

from tests.test_project_navigation_session import js
from tests.test_project_navigation_session import session_window as session_window
from tests.test_workflow_batch_cli import run_batch


@pytest.fixture
def editor_window(
    session_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> WebWorkbenchWindow:
    window = session_window

    def directory(*_args: object, **_kwargs: object) -> str:
        return str(tmp_path)

    monkeypatch.setattr(QFileDialog, "getExistingDirectory", directory)
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!!window.workflowEditor?.snapshot().connected") is True,
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
    return window


def test_web_editor_saves_and_runs_actual_fixture(
    editor_window: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = editor_window
    assert window.authoring.projection is not None
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


def test_graph_editing_preflight_and_saved_reopen(
    editor_window: WebWorkbenchWindow,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = editor_window
    assert window.authoring.projection is not None
    workspace = js(window, qtbot, "document.querySelector('#wf-workspace-path').textContent")
    assert isinstance(workspace, str) and Path(workspace).is_dir()
    original = window.authoring.projection.project

    def directory(*_args: object, **_kwargs: object) -> str:
        return workspace

    monkeypatch.setattr(QFileDialog, "getExistingDirectory", directory)

    def reopen() -> None:
        assert window.authoring.projection is not None
        expected = window.authoring.projection.project
        js(window, qtbot, "document.querySelector('[data-wf-choose=open_project]').click();true")
        qtbot.waitUntil(
            lambda: js(window, qtbot, "!workflowEditor.snapshot().pending") is True,
            timeout=15000,
        )
        assert window.authoring.projection is not None
        assert window.authoring.projection.project == expected
        assert js(window, qtbot, "workflowEditor.snapshot().graph.nodes.length") == len(
            expected.graph.nodes
        )

    def save() -> None:
        js(window, qtbot, "document.querySelector('#wf-save').click();true")
        qtbot.waitUntil(
            lambda: (
                js(
                    window,
                    qtbot,
                    "!workflowEditor.snapshot().pending && !workflowEditor.hasDraft()",
                )
                is True
            ),
            timeout=15000,
        )

    js(window, qtbot, "document.querySelector('[data-wf-add=wb-publish-original]').click();true")
    assert js(window, qtbot, "workflowEditor.snapshot().graph.nodes.length") == 4
    added = js(window, qtbot, "workflowEditor.snapshot().selected")
    assert isinstance(added, str)
    save()
    assert window.authoring.projection.issues
    assert any(issue.code == "missing_input" for issue in window.authoring.projection.issues)
    # Actual port clicks first make a type-invalid wire, then replace it with the valid one.
    js(
        window,
        qtbot,
        "document.querySelector('[data-node=verify] [data-direction=output]').click();"
        f"document.querySelector('[data-node=\"{added}\"] [data-direction=input]').click();true",
    )
    save()
    assert any(issue.code == "scientific_role" for issue in window.authoring.projection.issues)
    assert (
        js(
            window,
            qtbot,
            "document.querySelector('#wf-issues').textContent.includes('端口类型不匹配')",
        )
        is True
    )
    js(
        window,
        qtbot,
        "document.querySelector('[data-node=analyze] "
        "[data-port=analysis][data-direction=output]').click();"
        f"document.querySelector('[data-node=\"{added}\"] [data-direction=input]').click();true",
    )
    save()
    assert not window.authoring.projection.issues
    reopen()
    js(window, qtbot, f"document.querySelector('[data-wf-select=\"{added}\"]').click();true")
    # Replace the added publisher by a verifier, then delete it; original edges survive.
    js(
        window,
        qtbot,
        "document.querySelector('.wf-module-settings').open=true;"
        "document.querySelector('#wf-replacement').value='wb-verify-original';"
        "document.querySelector('#wf-replace').click();true",
    )
    assert (
        js(window, qtbot, "workflowEditor.snapshot().graph.nodes.at(-1).module.module_id")
        == "wb-verify-original"
    )
    save()
    reopen()
    js(window, qtbot, f"document.querySelector('[data-wf-select=\"{added}\"]').click();true")
    js(window, qtbot, "document.querySelector('#wf-delete-node').click();true")
    save()
    assert len(window.authoring.projection.project.graph.nodes) == 3
    assert window.authoring.projection.project.graph.edges == original.graph.edges
    assert not window.authoring.projection.issues

    # Native file action verifies persisted add/wire, replacement and deletion separately.
    reopen()


def test_schema_form_boolean_empty_array_and_composition(
    editor_window: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = editor_window
    assert window.authoring.projection is not None
    js(window, qtbot, "document.querySelector('[data-wf-select=analyze]').click();true")

    def save() -> None:
        js(window, qtbot, "document.querySelector('#wf-save').click();true")
        qtbot.waitUntil(
            lambda: (
                js(
                    window,
                    qtbot,
                    "!workflowEditor.snapshot().pending && !workflowEditor.hasDraft()",
                )
                is True
            ),
            timeout=15000,
        )

    js(
        window,
        qtbot,
        "const box=document.querySelector('[data-wf-field=\"lanes.0.bands.0.included\"]');"
        "box.checked=false;box.dispatchEvent(new Event('input'));true",
    )
    save()
    node = next(
        n for n in window.authoring.projection.project.graph.nodes if n.node_id == "analyze"
    )
    assert json.loads(node.parameters_json)["lanes"][0]["bands"][0]["included"] is False
    assert not window.authoring.projection.issues
    # Empty arrays are honest incomplete drafts, restorable from catalogue defaults.
    js(window, qtbot, "document.querySelector('[data-wf-remove=\"lanes.0\"]').click();true")
    save()
    assert window.authoring.projection.issues
    js(window, qtbot, "document.querySelector('[data-wf-copy-array=lanes]').click();true")
    save()
    assert not window.authoring.projection.issues
    revision = window.authoring.projection.project.revision
    js(
        window,
        qtbot,
        "window._ime=document.querySelector('[data-wf-field=\"lanes.0.roi.lane_id\"]');"
        "window._ime.focus();window._ime.dispatchEvent(new CompositionEvent('compositionstart'));"
        "window._ime.value='泳道甲';window._ime.dispatchEvent(new Event('input'));"
        "document.querySelector('#wf-save').click();true",
    )
    assert (
        js(window, qtbot, "workflowEditor.hasDraft() && !workflowEditor.snapshot().pending") is True
    )
    assert window.authoring.projection.project.revision == revision
    assert js(window, qtbot, "document.activeElement===window._ime") is True
    js(window, qtbot, "window._ime.dispatchEvent(new CompositionEvent('compositionend'));true")
    save()
    node = next(
        n for n in window.authoring.projection.project.graph.nodes if n.node_id == "analyze"
    )
    assert json.loads(node.parameters_json)["lanes"][0]["roi"]["lane_id"] == "泳道甲"


def test_gui_template_export_new_input_and_cli_share_definition(
    editor_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = editor_window
    assert window.authoring.projection is not None
    original_id = window.authoring.projection.project.document_id
    template = tmp_path / "lab-template.json"
    source = tmp_path / "second-input.tif"
    fixture = wb_validation_input("triangle_u8")
    assert fixture.source_bytes is not None
    source.write_bytes(fixture.source_bytes)

    def save_file(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return str(template), ""

    def open_file(*args: object, **_kwargs: object) -> tuple[str, str]:
        return str(template if "模板" in str(args[1]) else source), ""

    monkeypatch.setattr(QFileDialog, "getSaveFileName", save_file)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", open_file)
    js(
        window,
        qtbot,
        "document.querySelector('[data-node=analyze] .wf-node-title')"
        ".dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));"
        "document.querySelector('#wf-save').click();true",
    )
    qtbot.waitUntil(
        lambda: (
            js(window, qtbot, "!workflowEditor.snapshot().pending && !workflowEditor.hasDraft()")
            is True
        ),
        timeout=15000,
    )
    expected_layout = window.authoring.projection.project.layout
    js(window, qtbot, "document.querySelector('[data-wf-choose=export_template]').click();true")
    qtbot.waitUntil(
        lambda: (
            template.is_file() and js(window, qtbot, "!workflowEditor.snapshot().pending") is True
        ),
        timeout=15000,
    )
    js(window, qtbot, "document.querySelector('[data-wf-choose=new_template]').click();true")
    qtbot.waitUntil(
        lambda: (
            window.authoring.projection is not None
            and window.authoring.projection.project.document_id != original_id
        ),
        timeout=15000,
    )
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!workflowEditor.snapshot().pending") is True,
        timeout=15000,
    )
    assert window.authoring.projection.project.layout == expected_layout
    assert not window.authoring.projection.issues
    js(window, qtbot, "document.querySelector('#wf-run').click();true")
    qtbot.waitUntil(
        lambda: (
            js(
                window,
                qtbot,
                "Array.from(document.querySelectorAll('#wf-output-list td'))"
                ".some(cell=>cell.textContent==='40.0')",
            )
            is True
        ),
        timeout=40000,
    )
    report = run_batch(
        tmp_path / "cli-template", "--validation", "triangle_u8", "--template", str(template)
    )
    assert report["state"] == "completed"
    assert "40.0" in Path(report["samples"][0]["outputs"]["measurements"]).read_text(
        encoding="utf-8-sig"
    )


def test_gui_dependency_reuse_and_running_draft_survives_results(
    editor_window: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = editor_window
    assert window.authoring.projection is not None
    progress: list[str] = []
    window.authoring.progressChanged.connect(progress.append)
    adapter = TypeAdapter(WorkflowBatchStatus)

    def run() -> tuple[int, int]:
        assert window.authoring.projection is not None
        previous = window.authoring.projection.project.last_batch_id
        start = len(progress)
        js(window, qtbot, "document.querySelector('#wf-run').click();true")
        qtbot.waitUntil(
            lambda: (
                window.authoring.projection is not None
                and bool(window.authoring.projection.outputs)
                and window.authoring.projection.outputs[0].batch_id != previous
                and js(
                    window,
                    qtbot,
                    "!workflowEditor.snapshot().pending && !workflowEditor.snapshot().running",
                )
                is True
            ),
            timeout=40000,
        )
        statuses = [adapter.validate_json(raw).child for raw in progress[start:]]
        physical = {(s.run_id, s.pid) for s in statuses if s is not None and s.pid is not None}
        reused = max((s.reused_nodes for s in statuses if s is not None), default=0)
        return len(physical), reused

    assert run() == (3, 0)
    js(
        window,
        qtbot,
        "document.querySelector('[data-node=analyze] .wf-node-title')"
        ".dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));true",
    )
    assert run() == (0, 3)
    js(
        window,
        qtbot,
        "document.querySelector('[data-wf-select=publish]').click();"
        "const layout=document.querySelector('[data-wf-field=layout]');"
        "layout.value='compact';layout.dispatchEvent(new Event('change'));true",
    )
    assert run() == (1, 2)
    js(
        window,
        qtbot,
        "document.querySelector('[data-wf-select=analyze]').click();"
        "const polarity=document.querySelector('[data-wf-field=polarity]');"
        "polarity.value=polarity.value==='light'?'dark':'light';"
        "polarity.dispatchEvent(new Event('change'));true",
    )
    # Edit the next draft as soon as the frozen batch has an actual worker.
    edited: list[bool] = []

    def during(raw: str) -> None:
        status = adapter.validate_json(raw)
        if not edited and status.child is not None and status.child.pid is not None:
            edited.append(True)
            window.web.page().runJavaScript(
                "const title=document.querySelector('#wf-title');title.focus();"
                "title.value='运行时的新草稿';title.dispatchEvent(new Event('input'));"
            )

    window.authoring.progressChanged.connect(during)
    assert run() == (2, 1)
    assert edited
    assert js(window, qtbot, "workflowEditor.hasDraft()") is True
    assert js(window, qtbot, "workflowEditor.snapshot().graph.title") == "运行时的新草稿"
    assert js(window, qtbot, "document.activeElement.id") == "wf-title"
    # Finish with a real save so the normal native close guard has no draft to discard.
    js(window, qtbot, "document.querySelector('#wf-save').click();true")
    qtbot.waitUntil(
        lambda: (
            js(window, qtbot, "!workflowEditor.snapshot().pending && !workflowEditor.hasDraft()")
            is True
        ),
        timeout=15000,
    )


def test_gui_bad_tiff_isolated_from_valid_batch_input(
    editor_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = editor_window
    corrupt = tmp_path / "corrupt.tif"
    corrupt.write_bytes(b"not a TIFF")
    valid = tmp_path / "valid.tif"
    fixture = wb_validation_input("triangle_u8")
    assert fixture.source_bytes is not None
    valid.write_bytes(fixture.source_bytes)

    def originals(*_args: object, **_kwargs: object) -> tuple[list[str], str]:
        return [str(corrupt), str(valid)], ""

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", originals)
    js(window, qtbot, "document.querySelector('[data-wf-choose=bind_sources]').click();true")
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!workflowEditor.snapshot().pending") is True,
        timeout=15000,
    )
    assert window.authoring.projection is not None
    sources = window.authoring.projection.project.sources
    assert len(sources) == 2 and sources[0].asset is None and sources[0].reason
    assert sources[1].asset is not None
    js(window, qtbot, "document.querySelector('#wf-run').click();true")
    qtbot.waitUntil(
        lambda: (
            js(
                window,
                qtbot,
                "Array.from(document.querySelectorAll('#wf-output-list td'))"
                ".some(cell=>cell.textContent==='40.0')",
            )
            is True
        ),
        timeout=40000,
    )
    assert window.authoring.projection.batch is not None
    assert window.authoring.projection.batch.state == "completed_with_issues"
    samples = window.authoring.projection.samples
    assert [s.state for s in samples] == ["failed", "succeeded"]
    assert samples[0].reason
    assert all(
        output.sample_id == sources[1].sample_id for output in window.authoring.projection.outputs
    )
    assert (
        js(
            window,
            qtbot,
            "document.querySelector('#wf-sample-states').textContent.includes('corrupt.tif')",
        )
        is True
    )
    assert corrupt.read_bytes() == b"not a TIFF" and valid.read_bytes() == fixture.source_bytes
