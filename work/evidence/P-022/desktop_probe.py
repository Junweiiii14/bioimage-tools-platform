"""P022 author probe: installed wheels, ordinary __main__, real WebChannel and workers.
No pytest or source-tree imports in the isolated desktop environment.
"""

import hashlib
import json
import os
import sys
import time
import traceback
from importlib.metadata import distributions
from pathlib import Path

from bioimage_app import desktop_entry
from bioimage_app.__main__ import main
from PySide6.QtCore import QMimeData, QPoint, QPointF, QSettings, Qt, QTimer, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QFileDialog

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
output = Path(config["output"])
output.mkdir(parents=True, exist_ok=True)
os.environ["BIOIMAGE_RELEASE_CHANNEL"] = "wb-acceptance-" + config.get(
    "settings_name", config["name"]
)
settings = QSettings("BioImageTools", "Acceptance-" + config.get("settings_name", config["name"]))
for key in () if config.get("preserve_settings") else ("wb", "nuclei", "bca"):
    settings.setValue(f"tools/{key}/enabled", key not in config.get("disabled", []))
settings.setValue("nuclei_worker_v1", config.get("worker", ""))
settings.setValue("nuclei_model_v1", config.get("model", ""))
settings.sync()
started = time.perf_counter()
report = {
    "configuration": config,
    "runs": [],
    "errors": [],
    "inventory": sorted((d.metadata["Name"], d.version) for d in distributions()),
}
create = desktop_entry.create_desktop_window


def capture(mode):
    window = create(mode)
    report["states"] = window.tools.states

    def wait(predicate, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            QApplication.processEvents()
            if predicate():
                return
            time.sleep(0.01)
        raise TimeoutError("Probe condition timed out")

    def js(script):
        replies = []
        window.web.page().runJavaScript(script, replies.append)
        wait(lambda: bool(replies))
        return replies[0]

    def click(selector):
        wait(
            lambda: (
                js(
                    "!!document.querySelector("
                    + json.dumps(selector)
                    + ") && !document.querySelector("
                    + json.dumps(selector)
                    + ").disabled"
                )
                is True
            )
        )
        js("document.querySelector(" + json.dumps(selector) + ").click(); true")

    def idle():
        wait(lambda: js("!workflowEditor.snapshot().pending") is True)
        assert js("document.querySelector('#wf-status').dataset.error") != "true", js(
            "document.querySelector('#wf-status').textContent"
        )

    def digests(path):
        return {
            str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob("*")
            if p.is_file() and ("assets" in p.parts or "results" in p.parts)
        }

    def scenario():
        try:
            wait(
                lambda: js("document.querySelector('#runtime-badge')?.textContent") == "桌面工作台"
            )
            wait(lambda: js("!!window.workflowEditor?.snapshot().connected") is True)
            report["startup_seconds_warm_cache"] = time.perf_counter() - started
            report["availability_text"] = js(
                "document.querySelector('#tool-enablement').textContent"
            )
            if config.get("capture_home"):
                js("document.querySelector('#tool-enablement').closest('details').open=true;true")
                painted = time.monotonic() + 0.3
                wait(lambda: time.monotonic() >= painted)
                window.grab().save(str(output / "home.png"))
            for key, state in window.tools.states.items():
                if state != "enabled":
                    assert not any(
                        n == {"wb": "wb_tool", "nuclei": "nuclei_tool", "bca": "bca_tool"}[key]
                        or n.startswith(
                            {"wb": "wb_tool.", "nuclei": "nuclei_tool.", "bca": "bca_tool."}[key]
                        )
                        for n in sys.modules
                    )
            if config.get("native_drop"):
                folder = output / "original-folder"
                folder.mkdir()
                raw = js(
                    "JSON.stringify((()=>{const r=document.querySelector('[data-folder-drop]')"
                    ".getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})())"
                )
                x, y = json.loads(raw)
                point = QPoint(
                    round(x * window.web.zoomFactor()), round(y * window.web.zoomFactor())
                )
                mime = QMimeData()
                mime.setUrls([QUrl.fromLocalFile(str(folder))])
                receiver = window.web.focusProxy() or window.web
                enter = QDragEnterEvent(
                    point,
                    Qt.DropAction.CopyAction,
                    mime,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier,
                )
                QApplication.sendEvent(receiver, enter)
                drop = QDropEvent(
                    QPointF(point),
                    Qt.DropAction.CopyAction,
                    mime,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier,
                )
                QApplication.sendEvent(receiver, drop)
                assert enter.isAccepted() and drop.isAccepted()
                wait(
                    lambda: (
                        window.tools.reason("wb")
                        in js("document.querySelector('#folder-drop-status').textContent")
                    )
                )
                deadline = time.monotonic() + 0.4
                wait(lambda: time.monotonic() >= deadline)
                assert window.shutdown_stage == "idle"
                choices = []
                QFileDialog.getOpenFileName = lambda *a, **k: (choices.append(True) or "", "")
                click("[data-bca-open]")
                click("[data-bca-choose=source]")
                wait(lambda: bool(choices))
                js("document.querySelector('#bca-dialog').close();true")
                report["native_drop"] = {
                    "accepted": True,
                    "stage": window.shutdown_stage,
                    "bca_source_dialog": True,
                    "message": js("document.querySelector('#folder-drop-status').textContent"),
                }
            if config.get("missing_model"):
                click("[data-nuclei-open]")
                report["model_readiness"] = js(
                    "document.querySelector('#nuclei-readiness').textContent"
                )
                assert "准备" in report["model_readiness"]
                click("#nuclei-close")
            click("[data-workflow-open]")
            selected = []
            directory = [str(output)]
            QFileDialog.getOpenFileName = lambda *a, **k: (selected.pop(0), "")
            QFileDialog.getExistingDirectory = lambda *a, **k: directory[0]
            for tool in config.get("run_tools", []):
                before = time.perf_counter()
                if tool == "bca":
                    selected[:] = [config["csv"], config["record"]]
                elif tool == "nuclei":
                    selected[:] = [config["image"]]
                click(
                    "[data-wf-choose="
                    + {"wb": "new_example", "bca": "new_bca", "nuclei": "new_nuclei"}[tool]
                    + "]"
                )
                idle()
                wait(
                    lambda tool=tool: (
                        window.authoring.projection is not None
                        and window.authoring.projection.project.tool == tool
                    )
                )
                assert not window.authoring.projection.issues
                click("#wf-run")
                wait(
                    lambda: bool(
                        window.authoring.projection and window.authoring.projection.outputs
                    ),
                    150,
                )
                wait(
                    lambda: (
                        not window.authoring.busy
                        and window.authoring.projection.batch.state
                        in ("completed", "completed_with_issues")
                    )
                )
                projection = window.authoring.projection
                assert projection.batch.state in ("completed", "completed_with_issues")
                if tool == "nuclei":
                    assert any(o.port == "labels" and "46" in o.text for o in projection.outputs)
                path = Path(js("document.querySelector('#wf-workspace-path').textContent"))
                data = projection.model_dump(mode="json")
                for item in data["outputs"]:
                    item["preview"] = "[display only omitted]"
                report["runs"].append(
                    {
                        "tool": tool,
                        "workspace": str(path),
                        "seconds": time.perf_counter() - before,
                        "projection": data,
                        "assets": digests(path),
                    }
                )
                click("[data-wf-view=results]")
                window.grab().save(str(output / (tool + "-results.png")))
            for previous in config.get("reopen", []):
                path = Path(previous["workspace"])
                before = digests(path)
                directory[0] = str(path)
                click("[data-wf-choose=open_project]")
                idle()
                click("[data-wf-view=results]")
                wait(lambda: bool(window.authoring.projection.outputs))
                assert digests(path) == before == previous["assets"]
                report.setdefault("reopened", []).append(str(path))
            for previous in config.get("unavailable_history", []):
                path = Path(previous["workspace"])
                before = digests(path)
                directory[0] = str(path)
                click("[data-wf-choose=open_project]")
                wait(lambda: js("!workflowEditor.snapshot().pending") is True)
                error = js("document.querySelector('#wf-status').textContent")
                assert "不可执行" in error, error
                assert digests(path) == before == previous["assets"]
                report.setdefault("preserved_history", []).append(
                    {"workspace": str(path), "message": error}
                )
            if config.get("toggle"):
                tool = config["toggle"]
                assert window.tools.available(tool)
                window.tools.setEnabled(tool, False)
                assert window.tools.available(tool)
                assert settings.value(f"tools/{tool}/enabled", True, type=bool) is False
                report["restart_only"] = tool
            report["ok"] = True
        except Exception:
            report["errors"].append(traceback.format_exc())
            report["ok"] = False
        finally:
            output.joinpath("report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            window.close()

            def finish_close():
                choice = {
                    "confirm_dirty": "save",
                    "confirm_draft": "discard",
                    "confirm_busy": "cancel",
                }.get(window.shutdown_stage)
                if choice:
                    window.session_bridge.session("reply", json.dumps({"choice": choice}))
                if not window._exit_ready:
                    QTimer.singleShot(100, finish_close)

            QTimer.singleShot(100, finish_close)

    QTimer.singleShot(100, scenario)
    QTimer.singleShot(240000, lambda: QApplication.instance().exit(92))
    return window


desktop_entry.create_desktop_window = capture
sys.argv = ["bioimage_app"]
code = main()
assert code == 0 and report.get("ok"), (code, report["errors"])
print(json.dumps({"ok": True, "report": str(output / "report.json")}, ensure_ascii=False))
