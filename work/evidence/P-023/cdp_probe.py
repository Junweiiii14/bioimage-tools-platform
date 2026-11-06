"""External CDP driver for a real native candidate process; no injected Python."""

import argparse
import base64
import json
import time
import urllib.request
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWebSockets import QWebSocket

parser = argparse.ArgumentParser()
parser.add_argument("expression")
parser.add_argument("--save")
parser.add_argument("--screenshot")
args = parser.parse_args()
app = QCoreApplication([])
with urllib.request.urlopen("http://127.0.0.1:9233/json", timeout=5) as response:
    target = json.load(response)[0]
socket = QWebSocket()
replies = {}
socket.textMessageReceived.connect(
    lambda raw: replies.update({json.loads(raw).get("id"): json.loads(raw)})
)
socket.open(QUrl(target["webSocketDebuggerUrl"]))


def wait(condition):
    deadline = time.monotonic() + 15
    while not condition():
        app.processEvents()
        if time.monotonic() > deadline:
            raise TimeoutError("CDP response timed out")
        time.sleep(0.01)


wait(lambda: socket.state() == QAbstractSocket.SocketState.ConnectedState)


def call(index, method, params):
    socket.sendTextMessage(json.dumps({"id": index, "method": method, "params": params}))
    wait(lambda: index in replies)
    result = replies[index]
    if "error" in result or "exceptionDetails" in result.get("result", {}):
        raise RuntimeError(result)
    return result["result"]


result = call(1, "Runtime.evaluate", {"expression": args.expression, "returnByValue": True})
print(json.dumps(result, ensure_ascii=False))
if args.save:
    Path(args.save).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
if args.screenshot:
    image = call(2, "Page.captureScreenshot", {"format": "png"})
    Path(args.screenshot).write_bytes(base64.b64decode(image["data"]))
socket.close()
app.processEvents()
