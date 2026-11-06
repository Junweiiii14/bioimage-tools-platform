import json
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QFileDialog, QTextBrowser

from tests.test_project_navigation_session import js
from tests.test_project_navigation_session import session_window as session_window


def test_actual_nuclei(session_window, qtbot, monkeypatch, tmp_path):
    w = session_window
    w.settings.setValue(
        "nuclei_worker_v1",
        "C:/Users/70236/ResearchVault/Codex-Workbench/p015-research/worker-env/Scripts/python.exe",
    )
    w.settings.setValue(
        "nuclei_model_v1",
        "C:/Users/70236/ResearchVault/Codex-Workbench/p014-research/models/2D_versatile_fluo",
    )
    source = (
        "C:/Users/70236/ResearchVault/Codex-Workbench/p014-research/"
        "evaluation-input/Ganglioneuroblastoma_10.tif"
    )
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (source, ""))
    monkeypatch.setattr(QStandardPaths, "writableLocation", lambda *a: str(tmp_path))
    states = []
    w.nuclei.changed.connect(lambda raw: states.append(json.loads(raw)))
    qtbot.waitUntil(lambda: js(w, qtbot, "!!window.nucleiView && !!window.desktopSession") is True)
    qtbot.waitUntil(
        lambda: (
            js(w, qtbot, "!document.querySelector('[data-nuclei-choose=source]').disabled") is True
        )
    )
    js(
        w,
        qtbot,
        "document.querySelector('[data-nuclei-open]').click();"
        "document.querySelector('#nuclei-settings-toggle').click();document.querySelector('#nuclei-help').click();true",
    )
    qtbot.waitUntil(lambda: w.findChild(QTextBrowser) is not None)
    browser = w.findChild(QTextBrowser)
    assert "uv venv" in browser.toPlainText()
    browser.parentWidget().close()
    js(w, qtbot, "document.querySelector('[data-nuclei-choose=source]').click();true")
    qtbot.waitUntil(lambda: states and states[-1]["state"] == "ready" and not states[-1]["busy"])
    js(
        w,
        qtbot,
        "document.querySelector('#nuclei-run').click();"
        "document.querySelector('#nuclei-close').click();true",
    )
    qtbot.waitUntil(
        lambda: states[-1]["state"] == "succeeded" and not states[-1]["busy"], timeout=90000
    )
    result = states[-1]
    assert result["count"] == 46
    code = (
        "from bioimage_app.nuclei_results import read_result; import sys,json;"
        " r=read_result(sys.argv[1]); print(json.dumps([r.run_id,r.source_sha256,r.display.count]))"
    )
    output = subprocess.run(
        [sys.executable, "-I", "-c", code, result["workspace"]],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    assert json.loads(output.stdout) == [result["run_id"], result["source_sha256"], 46]
    for key in ["original", "overlay"]:
        result.pop(key)
    Path("work/evidence/P-020/nuclei-run.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
