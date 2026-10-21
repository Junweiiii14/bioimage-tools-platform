"""Capture the shared workbench fixture in the pinned Qt renderer."""

import argparse
import base64
import json
import os
import socket
import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWebEngineCore import QWebEnginePage, qWebEngineChromiumVersion
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebSockets import QWebSocket
from PySide6.QtWidgets import QApplication


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--performance", action="store_true")
    args = parser.parse_args()
    output: Path = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        debug_port = listener.getsockname()[1]
    os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = f"127.0.0.1:{debug_port}"
    app = QApplication([])
    view = QWebEngineView()
    messages: list[dict[str, object]] = []

    class Page(QWebEnginePage):
        def javaScriptConsoleMessage(
            self,
            level: QWebEnginePage.JavaScriptConsoleMessageLevel,
            message: str,
            line: int,
            source: str,
        ) -> None:
            messages.append(
                {"level": str(level), "message": message, "line": line, "source": source}
            )

    page = Page(view)
    page.setBackgroundColor(QColor("#f1f3e9"))
    view.setPage(page)
    view.resize(1440, 900)
    view.show()
    url = QUrl.fromLocalFile(str(args.assets.resolve() / "index.html"))
    url.setQuery("preview=1&view=home")
    view.setUrl(url)

    def pause(milliseconds: int) -> None:
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)
        loop.exec()

    def javascript(code: str) -> Any:
        received: list[object] = []
        loop = QEventLoop()

        def done(value: object) -> None:
            received.append(value)
            loop.quit()

        page.runJavaScript(code, done)
        QTimer.singleShot(10000, loop.quit)
        loop.exec()
        if not received:
            raise RuntimeError("JavaScript callback timed out")
        return received[0]

    until = time.monotonic() + 25
    while time.monotonic() < until:
        if javascript(
            "!!window.previewAdapter && document.fonts.check('14px \"WB Sans\"','原图 Figure 123')"
        ):
            break
        pause(100)
    else:
        raise RuntimeError("Preview or pinned font failed to initialize: " + json.dumps(messages))
    network = QNetworkAccessManager()
    response = network.get(QNetworkRequest(QUrl(f"http://127.0.0.1:{debug_port}/json")))
    loop = QEventLoop()
    response.finished.connect(loop.quit)
    QTimer.singleShot(10000, loop.quit)
    loop.exec()
    endpoints = json.loads(bytes(response.readAll().data()))
    response.deleteLater()
    websocket = QWebSocket()
    replies: dict[int, dict[str, Any]] = {}
    sequence = 0
    frames: list[dict[str, object]] = []

    def message(raw: str) -> None:
        value = json.loads(raw)
        if "id" in value and value["id"] < 1000000:
            replies[value["id"]] = value
        if value.get("method") == "Page.screencastFrame":
            data = value["params"]
            name = f"frame-{len(frames):05d}.jpg"
            (output / name).write_bytes(base64.b64decode(data["data"], validate=True))
            frames.append({"file": name, "timestamp": data["metadata"]["timestamp"]})
            websocket.sendTextMessage(
                json.dumps(
                    {
                        "id": 1000000 + len(frames),
                        "method": "Page.screencastFrameAck",
                        "params": {"sessionId": data["sessionId"]},
                    }
                )
            )

    websocket.textMessageReceived.connect(message)
    websocket.open(QUrl(endpoints[0]["webSocketDebuggerUrl"]))
    pause(200)

    def cdp(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        nonlocal sequence
        sequence += 1
        websocket.sendTextMessage(
            json.dumps({"id": sequence, "method": method, "params": params or {}})
        )
        timeout = time.monotonic() + 10
        while sequence not in replies and time.monotonic() < timeout:
            pause(20)
        value = replies.pop(sequence, {})
        if "result" not in value:
            raise RuntimeError(f"{method} failed: {value}")
        return value["result"]

    def capture(path: Path) -> None:
        result = cdp("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        path.write_bytes(base64.b64decode(result["data"], validate=True))

    cdp("Page.enable")
    cdp("DOM.enable")
    cdp("CSS.enable")
    records: list[dict[str, object]] = []
    cases = [
        ("home", ""),
        ("preparation", "previewAdapter.openProject(true)"),
        ("crop", "previewAdapter.openProject(false);switchMode('review')"),
        ("layout", "switchMode('layout')"),
        ("quant", "switchMode('quant')"),
        ("results", "switchMode('results')"),
        ("template", "advancedWorkspace.open('template')"),
        ("metadata", "advancedWorkspace.open('metadata')"),
        ("ocr", "advancedWorkspace.open('ocr')"),
        ("normalization", "advancedWorkspace.open('normalization')"),
        ("settings", "workbenchAppearance.open()"),
    ]
    if args.probe:
        cases = [("settings", "workbenchAppearance.open()")]
    for width, height in [(1440, 900)] if args.probe else [(1440, 900), (960, 640)]:
        view.resize(width, height)
        javascript("closeDrawer();previewAdapter.channel.session('home','{}');true")
        pause(400)
        for name, command in cases:
            if command:
                javascript(command + ";true")
            pause(400)
            settled = time.monotonic() + 6
            while time.monotonic() < settled:
                if javascript(
                    "document.getAnimations().length===0 && "
                    "!document.querySelector('.advanced-loading')"
                ):
                    break
                pause(100)
            path = output / f"{width}-{name}.png"
            capture(path)
            metrics = javascript(
                "JSON.stringify({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,font:getComputedStyle(document.body).fontFamily,bodyWidth:document.body.scrollWidth,theme:document.documentElement.dataset.theme,headings:[...document.querySelectorAll('h1,h2')].filter(e=>e.getClientRects().length).map(e=>e.textContent),fonts:[...document.fonts].map(f=>({family:f.family,status:f.status})),pending:document.getAnimations().length})"
            )
            selector = javascript(
                "document.querySelector('#drawer:not([hidden])')?'#drawer-title':"
                "!document.querySelector('#home-view').hidden?'#home-view h1':"
                "document.querySelector('#intake-workspace:not([hidden]) h1')?"
                "'#intake-workspace h1':'#image-title'"
            )
            document = cdp("DOM.getDocument")
            node = cdp(
                "DOM.querySelector", {"nodeId": document["root"]["nodeId"], "selector": selector}
            )
            fonts = cdp("CSS.getPlatformFontsForNode", {"nodeId": node["nodeId"]})
            records.append(
                {
                    "name": name,
                    "image": path.name,
                    "metrics": json.loads(metrics),
                    "platformFonts": fonts,
                }
            )
    view.resize(1440, 900)
    for theme in ("forest", "ember", "iris", "neutral"):
        javascript(
            "closeDrawer();previewAdapter.openProject(false);workbenchAppearance.open();document.querySelector('[data-appearance-theme=\""
            + theme
            + "\"]').click();closeDrawer();true"
        )
        pause(400)
        capture(output / ("theme-" + theme + ".png"))
        actual = javascript("document.documentElement.dataset.theme")
        if actual != theme:
            raise RuntimeError(f"Theme mismatch: requested {theme}, actual {actual}")
    if args.record:
        javascript("closeDrawer();previewAdapter.channel.session('home','{}');true")
        pause(400)
        cdp("Page.startScreencast", {"format": "jpeg", "quality": 90, "everyNthFrame": 1})
        actions = [
            ("home focus", "document.querySelector('.home-art').focus()", 600),
            ("project", "previewAdapter.openProject(false)", 600),
            (
                "rapid navigation",
                "switchMode('review');setTimeout(()=>switchMode('layout'),80);setTimeout(()=>switchMode('quant'),160)",
                700,
            ),
            ("matrix editor", "document.querySelector('[data-iq-row][data-iq-lane]').click()", 700),
            ("matrix return", "document.querySelector('[data-iq-action=all]').click()", 600),
            (
                "grid",
                "switchMode('layout');document.querySelector('[data-ig-view=__all__]').click()",
                600,
            ),
            ("order", "document.querySelector('[data-ig-down]').click()", 500),
            ("save", "document.querySelector('[data-ig-save]').click()", 600),
            (
                "drawer reverse",
                "workbenchAppearance.open();setTimeout(closeDrawer,90);setTimeout(()=>workbenchAppearance.open(),150)",
                700,
            ),
            ("theme", "document.querySelector('[data-appearance-theme=forest]').click()", 600),
            ("return", "closeDrawer();previewAdapter.channel.session('home','{}')", 600),
        ]
        for _, command, milliseconds in actions:
            javascript(command + ";true")
            pause(milliseconds)
        cdp("Page.stopScreencast")
        (output / "frames.json").write_text(json.dumps(frames, indent=2), encoding="utf-8")
        (output / "actions.json").write_text(
            json.dumps(actions, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    performance: object = None
    if args.performance:
        javascript("closeDrawer();previewAdapter.openProject(false);true")
        pause(400)
        javascript("""window.frameProbe={samples:[],started:performance.now()};
          requestAnimationFrame(function frame(t){frameProbe.samples.push(t);
            if(t-frameProbe.started<1800)requestAnimationFrame(frame);});
          workbenchAppearance.open();setTimeout(closeDrawer,400);
          setTimeout(()=>switchMode('layout'),700);setTimeout(()=>switchMode('quant'),1000);true""")
        pause(2000)
        performance = json.loads(javascript("JSON.stringify(frameProbe)"))
    (output / "report.json").write_text(
        json.dumps(
            {
                "chromium": qWebEngineChromiumVersion(),
                "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
                "chromium_flags": os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS"),
                "scale": os.environ.get("QT_SCALE_FACTOR"),
                "records": records,
                "performance": performance,
                "console": messages,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    view.close()
    websocket.close()
    view.deleteLater()
    pause(200)
    app.quit()
    print(
        json.dumps(
            {"output": str(output), "captures": len(records) + 4, "console": messages},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
