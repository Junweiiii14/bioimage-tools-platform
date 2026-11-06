"""Real desktop WebChannel → worker → verified result; no scientific admission."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from bioimage_app.bca_results import read_result
from bioimage_app.web_window import WebWorkbenchWindow
from platform_runtime.api import WorkspaceError
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from tests.test_project_navigation_session import js
from tests.test_project_navigation_session import session_window as session_window

EXAMPLES = Path(__file__).parents[1] / "tools/bca/examples"


def test_bca_desktop_commit_export_reopen_and_corruption(
    session_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = session_window

    def directory(*_args: object, **_kw: object) -> str:
        return str(tmp_path)

    monkeypatch.setattr(QStandardPaths, "writableLocation", directory)
    selected = EXAMPLES / "synthetic.csv"

    def choose(*_args: object, **_kw: object) -> tuple[str, str]:
        return str(selected), ""

    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose)
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!!window.bcaView && !!window.desktopSession") is True
    )
    assert (
        js(window, qtbot, "document.querySelectorAll('.tool-catalogue .installed-tool').length")
        == 3
    )
    js(window, qtbot, "document.querySelector('[data-bca-open]').click();true")
    qtbot.waitUntil(
        lambda: (
            js(window, qtbot, "!document.querySelector('[data-bca-choose=source]').disabled")
            is True
        )
    )
    assert js(window, qtbot, "document.querySelectorAll('#bca-record input:checked').length") == 0
    js(window, qtbot, "document.querySelector('[data-bca-choose=source]').click();true")
    qtbot.waitUntil(
        lambda: (
            js(window, qtbot, "document.querySelector('#bca-source').textContent")
            == "synthetic.csv"
        )
    )
    selected = EXAMPLES / "record.json"
    js(window, qtbot, "document.querySelector('[data-bca-choose=record]').click();true")
    qtbot.waitUntil(
        lambda: (
            js(window, qtbot, "document.querySelector('[name=instrument]').value")
            == "synthetic analytical values, no instrument"
        )
    )
    js(window, qtbot, "document.querySelector('#bca-run').click();true")
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!document.querySelector('#bca-results').hidden") is True,
        timeout=20000,
    )
    result = read_result(str(next((tmp_path / "BioImage/Projects").iterdir())))
    rows = result.table("samples")
    assert float(
        next(r for r in rows if r["sample_id"] == "S1")["mean_original_ug_ml"]
    ) == pytest.approx(5008.680555555556)
    assert sum(r["status"] == "partial" and r["mean_original_ug_ml"] == "" for r in rows) == 4
    qtbot.waitUntil(
        lambda: (
            js(window, qtbot, "document.querySelectorAll('#bca-samples tbody tr').length")
            == len(rows)
        )
    )
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", directory)
    js(window, qtbot, "document.querySelector('[data-bca-choose=export]').click();true")
    qtbot.waitUntil(lambda: list(tmp_path.glob("BCA结果-*/export.json")) != [])
    qtbot.waitUntil(lambda: not window.bca.busy)
    exported = next(tmp_path.glob("BCA结果-*/export.json"))
    assert json.loads(exported.read_text())["run_id"] == result.run_id
    # A new process reads through the same UI read_result path, not a ledger-only shortcut.
    code = (
        "from bioimage_app.bca_results import read_result; import json,sys; "
        "r=read_result(sys.argv[1]); print(json.dumps([r.run_id,r.source_sha256]))"
    )
    reopened = subprocess.run(
        [sys.executable, "-I", "-c", code, result.workspace],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    assert json.loads(reopened.stdout) == [result.run_id, result.source_sha256]
    # Closing the surface only browses home; the committed project remains available.
    js(
        window,
        qtbot,
        "document.querySelector('#bca-close').click();document.querySelector('[data-bca-open]').click();true",
    )
    assert (
        js(
            window,
            qtbot,
            "document.querySelector('#bca-provenance').textContent.includes("
            + json.dumps(result.run_id)
            + ")",
        )
        is True
    )
    # A damaged result is rejected without rewriting history or exposing a new success.
    paths = list(Path(result.workspace).rglob("*.csv"))
    output = next(p for p in paths if p.read_bytes() == result.members["samples"])
    output.write_bytes(b"damaged")
    with pytest.raises((ValueError, WorkspaceError)):
        read_result(result.workspace)
    assert output.read_bytes() == b"damaged"


def test_bca_form_keeps_chinese_input_focus_and_browsing(
    session_window: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = session_window
    qtbot.waitUntil(lambda: js(window, qtbot, "!!window.bcaView") is True)
    js(
        window,
        qtbot,
        "document.querySelector('[data-bca-open]').click();"
        "const f=document.querySelector('[name=diluent]');f.focus();"
        "f.dispatchEvent(new CompositionEvent('compositionstart'));f.value='缓冲液';true",
    )
    window.bca.refresh()
    qtbot.wait(100)
    assert js(window, qtbot, "document.activeElement.name") == "diluent"
    assert js(window, qtbot, "document.activeElement.value") == "缓冲液"
    js(
        window,
        qtbot,
        "document.activeElement.dispatchEvent(new CompositionEvent('compositionend'));"
        "document.querySelector('#bca-close').click();"
        "document.querySelector('[data-bca-open]').click();true",
    )
    assert js(window, qtbot, "document.querySelector('[name=diluent]').value") == "缓冲液"
