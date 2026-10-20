"""Open the saved workbench and verify rendered result cells, without injecting results."""

import json
import sys
import time
from pathlib import Path

from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

app = QApplication([])
workspace, destination = Path(sys.argv[1]), Path(sys.argv[2])
assert not destination.exists()
window = WebWorkbenchWindow(
    settings=QSettings(str(destination.with_suffix(".ini")), QSettings.Format.IniFormat)
)
window.show()


def wait(predicate):
    deadline = time.monotonic() + 120
    while not predicate():
        if time.monotonic() > deadline:
            raise TimeoutError(window.host.view.status.text())
        app.processEvents()
        QTest.qWait(5)
        time.sleep(0.005)


try:
    window.open_project(str(workspace))
    wait(lambda: not window.host.operation_busy and len(window.bridge.snapshot()["cells"]) == 48)
    window.bridge.publish()
    done = []
    window.web.page().runJavaScript(
        "document.querySelector('[data-mode=results]').click(); true",
        lambda value: done.append(value),
    )
    wait(lambda: bool(done))
    check = []
    window.web.page().runJavaScript(
        "document.querySelectorAll('.quant-table-cell').length", lambda value: check.append(value)
    )
    wait(lambda: bool(check))
    assert check[0] == 48, check
    for _ in range(20):
        app.processEvents()
        QTest.qWait(5)
        time.sleep(0.005)
    assert window.grab().save(str(destination))
    state = window.bridge.snapshot()
    destination.with_suffix(".json").write_text(
        json.dumps(
            {"busy": state["busy"], "cell_count": len(state["cells"]), "rendered_count": check[0]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
finally:
    window.close()
    wait(lambda: window.host.resources_closed)
