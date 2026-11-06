"""Desktop graph → worker → commit → template reuse and verified cold reads."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from tests.test_project_navigation_session import js
from tests.test_project_navigation_session import session_window as session_window
from tests.test_research_authoring import plate_at


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
