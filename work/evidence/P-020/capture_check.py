from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QFileDialog

from tests.test_project_navigation_session import js
from tests.test_project_navigation_session import session_window as session_window

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "work/evidence/P-020/screenshots"


def test_capture(session_window, qtbot, monkeypatch, tmp_path):
    w = session_window
    OUT.mkdir(exist_ok=True)
    qtbot.waitUntil(lambda: js(w, qtbot, "!!window.bcaView && !!window.desktopSession") is True)
    js(
        w,
        qtbot,
        "const style=document.createElement('style');"
        "style.textContent='*,*::before,*::after{transition:none!important;animation:none!important}';document.head.append(style);true",
    )
    qtbot.waitUntil(lambda: js(w, qtbot, "document.fonts.status") == "loaded", timeout=15000)
    for width, height in [(1440, 940), (960, 720)]:
        w.resize(width, height)
        qtbot.waitUntil(lambda width=width: js(w, qtbot, "innerWidth") == width)
        for theme in ["forest", "ember", "iris", "neutral"]:
            js(
                w,
                qtbot,
                f"document.documentElement.dataset.theme='{theme}';"
                "document.documentElement.dataset.motion='reduced';true",
            )
            qtbot.wait(1100)
            assert w.grab().save(str(OUT / f"home-{theme}-{width}.png"))
            assert (
                js(
                    w,
                    qtbot,
                    "document.querySelector('#platform-view').scrollWidth <= docu"
                    "ment.querySelector('#platform-view').clientWidth",
                )
                is True
            )
    js(
        w,
        qtbot,
        "document.documentElement.dataset.theme='forest';"
        "document.querySelector('[data-bca-open]').click();true",
    )
    qtbot.waitUntil(
        lambda: js(w, qtbot, "!document.querySelector('[data-bca-choose=source]').disabled") is True
    )
    selected = ROOT / "tools/bca/examples/synthetic.csv"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(selected), ""))
    monkeypatch.setattr(QStandardPaths, "writableLocation", lambda *a: str(tmp_path))
    js(w, qtbot, "document.querySelector('[data-bca-choose=source]').click();true")
    qtbot.waitUntil(lambda: not w.bca.busy)
    selected = ROOT / "tools/bca/examples/record.json"
    js(w, qtbot, "document.querySelector('[data-bca-choose=record]').click();true")
    qtbot.waitUntil(
        lambda: (
            js(w, qtbot, "document.querySelector('[name=instrument]').value")
            == "synthetic analytical values, no instrument"
        )
    )
    for width, height in [(1440, 940), (960, 720)]:
        w.resize(width, height)
        qtbot.waitUntil(lambda width=width: js(w, qtbot, "innerWidth") == width)
        qtbot.wait(1100)
        assert w.grab().save(str(OUT / f"bca-record-{width}.png"))
    js(w, qtbot, "document.querySelector('#bca-run').click();true")
    qtbot.waitUntil(
        lambda: js(w, qtbot, "!document.querySelector('#bca-results').hidden") is True,
        timeout=20000,
    )
    js(w, qtbot, "document.querySelector('#bca-record-panel').open=false;true")
    for width, height in [(1440, 940), (960, 720)]:
        w.resize(width, height)
        qtbot.waitUntil(lambda width=width: js(w, qtbot, "innerWidth") == width)
        qtbot.wait(1100)
        assert w.grab().save(str(OUT / f"bca-result-{width}.png"))
    js(
        w,
        qtbot,
        "document.querySelector('#bca-close').click();"
        "document.querySelector('[data-nuclei-open]').click();true",
    )
    root = "C:/Users/70236/Documents/BioImage/Projects/Nuclei-2e1ef41119f6"
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: root)
    js(w, qtbot, "document.querySelector('[data-nuclei-choose=open]').click();true")
    qtbot.waitUntil(
        lambda: (
            js(w, qtbot, "document.querySelector('#nuclei-count').textContent") == "已保存核数 46"
        ),
        timeout=15000,
    )
    for width, height in [(1440, 940), (960, 720)]:
        w.resize(width, height)
        qtbot.waitUntil(lambda width=width: js(w, qtbot, "innerWidth") == width)
        qtbot.wait(1100)
        assert w.grab().save(str(OUT / f"nuclei-result-{width}.png"))
    js(
        w,
        qtbot,
        "document.querySelector('#nuclei-close').click();"
        "document.querySelector('.workflow-entry [data-workflow-open]').click();true",
    )
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: str(tmp_path))
    js(w, qtbot, "document.querySelector('[data-wf-choose=new_example]').click();true")
    qtbot.waitUntil(
        lambda: js(w, qtbot, "window.workflowEditor.snapshot().graph?.nodes.length") == 3,
        timeout=15000,
    )
    for width, height in [(1440, 940), (960, 720)]:
        w.resize(width, height)
        qtbot.waitUntil(lambda width=width: js(w, qtbot, "innerWidth") == width)
        qtbot.wait(1100)
        assert w.grab().save(str(OUT / f"workflow-{width}.png"))
