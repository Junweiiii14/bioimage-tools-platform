"""Desktop graph → worker → commit → template reuse and verified cold reads."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from tests.test_project_navigation_session import js
from tests.test_project_navigation_session import session_window as session_window
from tests.test_research_authoring import plate_at
from tests.test_workflow_authoring_web import editor_window as editor_window


def test_bca_graph_run_template_reuse_and_integrity(
    session_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = session_window
    paths = list(plate_at(tmp_path, "first"))
    template = tmp_path / "plate-template.json"

    def choose(*_args: object, **_kw: object) -> tuple[str, str]:
        return paths.pop(0), ""

    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose)

    def directory(*_args: object, **_kw: object) -> str:
        return str(tmp_path)

    def save_file(*_args: object, **_kw: object) -> tuple[str, str]:
        return str(template), ""

    monkeypatch.setattr(QFileDialog, "getExistingDirectory", directory)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", save_file)
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!!window.workflowEditor?.snapshot().connected") is True
    )
    js(
        window,
        qtbot,
        "document.querySelector('[data-workflow-open]').click();"
        "document.querySelector('[data-wf-choose=new_bca]').click();true",
    )

    def idle() -> None:
        qtbot.waitUntil(
            lambda: js(window, qtbot, "!workflowEditor.snapshot().pending") is True, timeout=20000
        )

    idle()
    assert window.authoring.projection is not None
    assert window.authoring.projection.project.tool == "bca"
    assert not window.authoring.projection.issues
    assert js(window, qtbot, "document.querySelector('#wf-parameters').readOnly") is True
    # Real port clicks reject a provenance-to-A562 connection, then source binding repairs it.
    js(window, qtbot, "document.querySelector('[data-wf-add=bca-pierce25-research]').click();true")
    added = js(window, qtbot, "workflowEditor.snapshot().selected")
    assert isinstance(added, str)
    js(
        window,
        qtbot,
        "document.querySelector('[data-node=quantify] "
        "[data-port=provenance][data-direction=output]').click();"
        f'document.querySelector(\'[data-node="{added}"] '
        "[data-port=source][data-direction=input]').click();"
        "document.querySelector('#wf-save').click();true",
    )
    idle()
    assert any(i.node_id == added for i in window.authoring.projection.issues)
    js(
        window,
        qtbot,
        "document.querySelector('#wf-bind-raw').click();"
        "document.querySelector('#wf-save').click();true",
    )
    idle()
    assert not window.authoring.projection.issues
    js(
        window,
        qtbot,
        "document.querySelector('#wf-delete-node').click();"
        "document.querySelector('#wf-save').click();true",
    )
    idle()
    js(window, qtbot, "document.querySelector('[data-wf-choose=export_template]').click();true")
    idle()
    before = template.read_bytes()

    def run() -> tuple[str, str]:
        js(window, qtbot, "document.querySelector('#wf-run').click();true")
        qtbot.waitUntil(
            lambda: (
                js(
                    window,
                    qtbot,
                    "document.querySelector('#wf-output-list').textContent.includes('5008.680555')",
                )
                is True
            ),
            timeout=40000,
        )
        qtbot.waitUntil(lambda: not window.authoring.busy, timeout=15000)
        assert window.authoring.projection is not None
        outputs = window.authoring.projection.outputs
        assert {o.port for o in outputs} == {"wells", "samples", "provenance"}
        table = next(o for o in outputs if o.port == "samples").table
        assert sum("partial" in row for row in table) == 4
        workspace = js(window, qtbot, "document.querySelector('#wf-workspace-path').textContent")
        assert isinstance(workspace, str)
        return workspace, window.authoring.projection.project.document_id

    first_workspace, first_document = run()
    paths[:] = [str(template), *plate_at(tmp_path, "second")]
    js(window, qtbot, "document.querySelector('[data-wf-choose=new_template]').click();true")
    idle()
    second_workspace, _second_document = run()
    assert second_workspace != first_workspace
    assert template.read_bytes() == before
    # The old workspace is released by switching. A new process verifies actual assets.
    code = (
        "import sys,json; from platform_runtime.api import Workspace; "
        "from bioimage_app.workflow_authoring_store import execute_authoring_store as run; "
        "s=Workspace.open(sys.argv[1]); "
        "r=run(s,json.dumps({'operation':'results','document_id':sys.argv[2]}).encode()); "
        "print(json.dumps([o.port for o in r.outputs])); s.close()"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, first_workspace, first_document],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert set(json.loads(result.stdout)) == {"wells", "samples", "provenance"}
    # A changed raw input invalidates reading even though the ledger still says completed.
    from bioimage_app.workflow_authoring_store import load_authoring_project
    from platform_runtime.api import Workspace

    with Workspace.open(first_workspace) as store:
        project = load_authoring_project(store, first_document)
        assert project.sources[0].asset is not None
        source = store.asset_path(project.sources[0].asset.payload)
    source.write_bytes(b"corrupted test input")
    failed = subprocess.run(
        [sys.executable, "-I", "-c", code, first_workspace, first_document],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert failed.returncode != 0


@pytest.mark.parametrize("action", ["new_nuclei", "new_bca"])
def test_failed_research_switch_disables_old_editor_and_recovers(
    editor_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    window = editor_window
    assert window.authoring.projection is not None
    old_id = window.authoring.projection.project.document_id
    # A pre-dialog dirty rejection has not switched the host and must keep its draft usable.
    js(
        window,
        qtbot,
        "document.querySelector('#wf-title').value='保留草稿';"
        "document.querySelector('#wf-title').dispatchEvent(new Event('input'));"
        f"document.querySelector('[data-wf-choose={action}]').click();true",
    )
    qtbot.waitUntil(lambda: js(window, qtbot, "!workflowEditor.snapshot().pending") is True)
    assert window.authoring.projection.project.document_id == old_id
    assert js(window, qtbot, "document.querySelector('#wf-save').disabled") is False
    assert js(window, qtbot, "workflowEditor.hasDraft()") is True
    js(window, qtbot, "document.querySelector('#wf-save').click();true")
    qtbot.waitUntil(lambda: js(window, qtbot, "!workflowEditor.snapshot().pending") is True)

    def cancel(*_args: object, **_kw: object) -> tuple[str, str]:
        return "", ""

    monkeypatch.setattr(QFileDialog, "getOpenFileName", cancel)
    js(window, qtbot, f"document.querySelector('[data-wf-choose={action}]').click();true")
    qtbot.waitUntil(lambda: js(window, qtbot, "!workflowEditor.snapshot().pending") is True)
    assert window.authoring.projection.project.document_id == old_id
    assert js(window, qtbot, "document.querySelector('#wf-run').disabled") is False
    assert js(window, qtbot, "document.querySelector('#wf-workspace').hidden") is False
    if action == "new_bca":
        source, record = plate_at(tmp_path, "invalid")
        Path(record).write_text("{}", encoding="utf-8")
        paths = [source, record]
    else:
        source = tmp_path / "unsupported.tif"
        tifffile.imwrite(source, np.zeros((20, 25), dtype=np.uint16))
        paths = [str(source)]

    def choose(*_args: object, **_kw: object) -> tuple[str, str]:
        return paths.pop(0), ""

    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose)
    js(window, qtbot, f"document.querySelector('[data-wf-choose={action}]').click();true")
    qtbot.waitUntil(
        lambda: js(window, qtbot, "document.querySelector('#wf-status').dataset.error") == "true",
        timeout=15000,
    )
    assert window.authoring.projection is None
    assert js(window, qtbot, "document.querySelector('#wf-workspace').hidden") is True
    assert js(window, qtbot, "document.querySelector('#wf-start').hidden") is False
    assert js(window, qtbot, "document.querySelector('#wf-run').disabled") is True
    assert js(window, qtbot, "document.querySelector('#wf-save').disabled") is True
    js(window, qtbot, "document.querySelector('[data-wf-choose=new_example]').click();true")
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!workflowEditor.snapshot().pending") is True,
        timeout=15000,
    )
    assert window.authoring.projection is not None
    assert window.authoring.projection.project.document_id != old_id
    assert not window.authoring.projection.issues
    assert js(window, qtbot, "document.querySelector('#wf-workspace').hidden") is False
    assert js(window, qtbot, "document.querySelector('#wf-run').disabled") is False
