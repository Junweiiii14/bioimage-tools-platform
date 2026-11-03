"""One batched real-workbench capture; synthetic input only, no visual verdict."""

import json
import os
from pathlib import Path

from tests.test_project_navigation_session import js
from tests.test_workflow_authoring_web import editor_window as editor_window
from tests.test_workflow_authoring_web import session_window as session_window


def test_capture_authoring_surface(editor_window, qtbot):
    window = editor_window
    destination = Path(os.environ.get("P009_CAPTURE_OUTPUT", ".local/p009-ui-main"))
    destination.mkdir(parents=True, exist_ok=True)
    js(window, qtbot, "document.querySelector('#wf-run').click();true")
    qtbot.waitUntil(
        lambda: js(window, qtbot, "document.querySelectorAll('.wf-result-item').length>0") is True,
        timeout=40000,
    )
    captures = []
    js(
        window,
        qtbot,
        "const captureStyle=document.createElement('style');"
        "captureStyle.textContent='*,*::before,*::after{transition:none!important;animation:none!important}';"
        "document.head.append(captureStyle);true",
    )
    cases = [(theme, 1440, 940, "graph") for theme in ("forest", "ember", "iris", "neutral")]
    cases += [(theme, 960, 640, "parameters") for theme in ("forest", "ember", "iris", "neutral")]
    cases += [("forest", 640, 720, view) for view in ("graph", "parameters", "results")]
    cases += [("forest", 1440, 940, "results")]
    for theme, width, height, view in cases:
        window.resize(width, height)
        window.raise_()
        window.activateWindow()
        qtbot.waitUntil(window.isActiveWindow, timeout=10000)
        js(
            window,
            qtbot,
            f"document.documentElement.dataset.theme='{theme}';"
            "document.querySelector('[data-wf-select=analyze]').click();"
            f"document.querySelector('[data-wf-view={view}]').click();"
            "window._wfPaint=false;document.fonts.ready.then(()=>"
            "requestAnimationFrame(()=>requestAnimationFrame(()=>window._wfPaint=true)));true",
        )
        qtbot.waitUntil(lambda: js(window, qtbot, "window._wfPaint") is True, timeout=10000)
        # QWidget readback is a separate native compositor delivery from the DOM RAF.
        # This capture-only settling time is not included in interaction latency measurements.
        qtbot.wait(500)
        filename = f"{theme}-{width}x{height}-{view}.png"
        capture = window.web.grab()
        assert capture.save(str(destination / filename))
        pixels = capture.toImage()
        colors = {
            pixels.pixelColor(x, y).rgba()
            for x in range(0, pixels.width(), 16)
            for y in range(0, pixels.height(), 16)
        }
        assert len(colors) > 8, "Blank capture cannot support a visual verdict"
        button = json.loads(
            js(
                window,
                qtbot,
                """JSON.stringify((()=>{
            const button=document.querySelector('#wf-run'),box=button.getBoundingClientRect();
            return {x:box.x+6,y:box.y+box.height/2,
                color:getComputedStyle(button).backgroundColor.match(/[\\d.]+/g).slice(0,3).map(Number)};
        })())""",
            )
        )
        dpr = capture.devicePixelRatio()
        pixel = pixels.pixelColor(round(button["x"] * dpr), round(button["y"] * dpr))
        actual = [pixel.red(), pixel.green(), pixel.blue()]
        assert max(abs(a - b) for a, b in zip(actual, button["color"], strict=True)) <= 2, (
            actual,
            button,
        )
        metrics = json.loads(
            js(
                window,
                qtbot,
                """JSON.stringify((()=>{
            const dialog=document.querySelector('#workflow-editor-dialog');
            const box=dialog.getBoundingClientRect();
            const footer=dialog.querySelector('.wf-footer').getBoundingClientRect();
            return {viewport:[innerWidth,innerHeight],
                documentWidth:document.documentElement.scrollWidth,
                dialog:[box.x,box.y,box.width,box.height],footerBottom:footer.bottom,
                theme:document.documentElement.dataset.theme,view:dialog.dataset.view,
                nodeCount:document.querySelectorAll('.wf-node').length,
                results:document.querySelectorAll('.wf-result-item').length,
                font:getComputedStyle(dialog).fontFamily};
        })())""",
            )
        )
        captures.append({"file": filename, **metrics})
    (destination / "captures.json").write_text(
        json.dumps(captures, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    assert all(c["documentWidth"] <= c["viewport"][0] for c in captures)
