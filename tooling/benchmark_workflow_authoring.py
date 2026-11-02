"""Opt-in native P009 measurements. Raw timings are evidence, not scientific acceptance."""

import argparse
import json
import os
import platform
import subprocess
import time
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import patch

from pydantic import TypeAdapter

from tooling.benchmark_workbench_snapshot import (
    EventPump,
    distribution,
    javascript,
    native_target_expression,
    windows_memory,
)
from tooling.qt_test_lifecycle import close_and_dispose_window

if TYPE_CHECKING:
    from bioimage_app.web_window import WebWorkbenchWindow
    from pytestqt.qtbot import QtBot


DRIVER = r"""
(() => {
  window.p009perf={pending:false,armed:false,samples:[],errors:[],sequence:0};
  const fail=message=>{p009perf.errors.push(message);p009perf.pending=false;};
  const ready=()=>{
    if(p009perf.kind==='node') return document.querySelector(
      '[data-node="'+CSS.escape(p009perf.expected)+'"] .wf-node-title')
      .getAttribute('aria-pressed')==='true' &&
      document.querySelector('#wf-current-step').value===p009perf.expected;
    if(p009perf.kind==='preview') return (
      document.querySelector('#workflow-editor-dialog').dataset.view==='results' &&
      !document.querySelector('#wf-save').disabled &&
      !!document.querySelector('#wf-output-list img') &&
      document.querySelector('#wf-output-list img').complete);
    const status=document.querySelector('#wf-status').textContent;
    return p009perf.kind==='pause' ? status.includes('暂停') :
      status.includes('取消') || document.querySelector('#wf-cancel').hidden;
  };
  const identity=()=>JSON.stringify([document.querySelector('#wf-workspace-path').textContent,
    document.querySelector('#wf-title').value,document.querySelector('#wf-save-state').textContent]);
  window.addEventListener('error',event=>{if(p009perf.pending)fail(event.message);});
  document.addEventListener('click',event=>{
    if(!p009perf.armed || !event.target.closest(p009perf.selector)) return;
    p009perf.armed=false;
    if(!event.isTrusted){fail('Non-native click');return;}
    if(ready()){fail('Receipt already visible');return;}
    const token=++p009perf.sequence,started=event.timeStamp;
    const original=identity();
    const safe=()=>token===p009perf.sequence && !p009perf.errors.length &&
      original===identity();
    let frames=0;
    const observe=()=>{
      if(!safe()){fail('Draft changed during observation');return;}
      if(!ready()){
        if(++frames>600){fail('Missing production receipt');return;}
        requestAnimationFrame(observe);return;
      }
      requestAnimationFrame(()=>requestAnimationFrame(()=>{
        if(!safe() || !ready()){fail('Stale receipt');return;}
        const feedback=performance.now()-started;
        const settle=()=>{
          if(!safe() || !ready()){fail('Changed before settling');return;}
          if(document.querySelector('#workflow-editor-dialog').getAnimations({subtree:true})
              .some(animation=>animation.playState==='running')){
            if(++frames>600){fail('Animations did not settle');return;}
            requestAnimationFrame(settle);return;
          }
          requestAnimationFrame(()=>requestAnimationFrame(()=>{
            const elapsed=performance.now()-started;
            if(!safe() || !ready() || feedback<0 || elapsed<feedback){
              fail(JSON.stringify({error:'Invalid settled receipt',kind:p009perf.kind,
                safe:safe(),ready:ready(),original,current:identity(),feedback,elapsed}));return;
            }
            p009perf.samples.push({kind:p009perf.kind,feedback_ms:feedback,settled_ms:elapsed,
              trusted:true,theme:document.documentElement.dataset.theme});
            p009perf.pending=false;
          }));
        };
        settle();
      }));
    };
    requestAnimationFrame(observe);
  },true);
  return true;
})()
"""


class AsyncEventPump(EventPump):
    """Enter Qt's loop so queued Python worker slots can acquire the GIL."""

    def waitUntil(self, callback: Callable[[], bool], *, timeout: int = 30000) -> None:
        from PySide6.QtCore import QEventLoop, QTimer

        deadline = time.perf_counter() + timeout / 1000
        loop = QEventLoop()
        while not callback():
            if time.perf_counter() > deadline:
                raise TimeoutError("Benchmark Qt/JavaScript deadline exceeded")
            QTimer.singleShot(5, loop.quit)
            loop.exec()


def native_click(window: "WebWorkbenchWindow", pump: EventPump, selector: str) -> float:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    coordinates: list[float] = []

    def usable() -> bool:
        raw = javascript(window, pump, native_target_expression(selector))
        point = json.loads(cast(str, raw))
        if point is None:
            return False
        coordinates[:] = point
        return True

    pump.waitUntil(usable)
    if (
        not window.isActiveWindow()
        or javascript(window, pump, "document.visibilityState") != "visible"
    ):
        raise RuntimeError("Native measurement window is not active and visible")
    target = window.web.focusProxy()
    assert target is not None
    started = time.perf_counter()
    QTest.mouseClick(
        target,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(coordinates[0]), round(coordinates[1])),
    )
    return started


def observe(
    window: "WebWorkbenchWindow",
    pump: EventPump,
    kind: str,
    selector: str,
    expected: str = "",
) -> tuple[dict[str, object], float]:
    arm = {"kind": kind, "selector": selector, "expected": expected, "pending": True, "armed": True}
    javascript(window, pump, f"Object.assign(p009perf,{json.dumps(arm)});true")
    count = javascript(window, pump, "p009perf.samples.length")
    started = native_click(window, pump, selector)
    pump.waitUntil(lambda: javascript(window, pump, "!p009perf.pending") is True)
    errors = javascript(window, pump, "JSON.stringify(p009perf.errors)")
    if (
        errors != "[]"
        or javascript(window, pump, "p009perf.samples.length") != cast(int, count) + 1
    ):
        raise RuntimeError(f"Invalid observation: {errors}")
    sample = json.loads(
        cast(str, javascript(window, pump, "JSON.stringify(p009perf.samples.at(-1))"))
    )
    sample["native_foreground"] = True
    return cast(dict[str, object], sample), started


def wait_idle(window: "WebWorkbenchWindow", pump: EventPump) -> None:
    pump.waitUntil(
        lambda: (
            not window.authoring.busy
            and javascript(
                window,
                pump,
                "!workflowEditor.snapshot().pending && !workflowEditor.snapshot().running",
            )
            is True
        ),
        timeout=45000,
    )


def run_case(folder: Path, nodes: int, warmup: int, samples: int) -> dict[str, object]:
    from bioimage_app.web_window import WebWorkbenchWindow
    from bioimage_app.workflow_batch_session import WorkflowBatchStatus
    from platform_runtime.api import Workspace
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QFileDialog

    folder.mkdir()
    pump = AsyncEventPump()
    window = WebWorkbenchWindow(
        settings=QSettings(str(folder / "ui.ini"), QSettings.Format.IniFormat)
    )
    window.show()
    window.raise_()
    window.activateWindow()
    events: list[tuple[float, WorkflowBatchStatus]] = []
    adapter = TypeAdapter(WorkflowBatchStatus)

    def progress(raw: str) -> None:
        events.append((time.perf_counter(), adapter.validate_json(raw)))

    window.authoring.progressChanged.connect(progress)
    receipt_errors: list[str] = []

    def document(_token: str, operation: str, _data: str, error: str) -> None:
        if error:
            receipt_errors.append(error)
        with (folder / "receipts.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"operation": operation, "error": error}) + "\n")

    window.authoring.documentChanged.connect(document)
    groups: dict[str, object] = {}
    workspace = ""
    try:
        pump.waitUntil(window.isActiveWindow)
        pump.waitUntil(
            lambda: (
                javascript(window, pump, "!!window.workflowEditor?.snapshot().connected") is True
            )
        )
        javascript(window, pump, "document.querySelector('[data-workflow-open]').click();true")
        with patch.object(QFileDialog, "getExistingDirectory", return_value=str(folder)):
            window.authoring.choose("benchmark", "new_example", '{"validation":"triangle_u16"}')
            pump.waitUntil(lambda: window.authoring.projection is not None or bool(receipt_errors))
            if receipt_errors:
                raise RuntimeError(receipt_errors[-1])
        wait_idle(window, pump)
        workspace = cast(
            str,
            javascript(window, pump, "document.querySelector('#wf-workspace-path').textContent"),
        )
        # Twelve explicit synthetic annotations exercise a normal-size parameter form.
        # Repeated ROI coordinates are a UI workload, not independent biological samples.
        javascript(
            window,
            pump,
            """
          document.querySelector('[data-wf-select=analyze]').click();
          const input=document.querySelector('#wf-parameters'),params=JSON.parse(input.value);
          params.lanes=Array.from({length:12},(_,i)=>{
            const lane=structuredClone(params.lanes[0]);lane.roi.lane_id='bench-'+(i+1);return lane;
          });
          input.value=JSON.stringify(params);input.dispatchEvent(new Event('input'));
          document.querySelector('#wf-apply-json').click();
          document.querySelector('[data-wf-select=publish]').click();
          const rows=document.querySelector('[data-wf-field=expected_rows]');
          rows.value='12';rows.dispatchEvent(new Event('input'));
          document.querySelector('#wf-save').click();true
        """,
        )
        wait_idle(window, pump)
        if nodes == 64:
            javascript(
                window,
                pump,
                """
              for(let i=0;i<61;i++)
                document.querySelector('[data-wf-add=wb-verify-original]').click();
              document.querySelector('#wf-save').click();true
            """,
            )
            wait_idle(window, pump)
        else:
            javascript(window, pump, "document.querySelector('#wf-run').click();true")
            pump.waitUntil(
                lambda: (
                    javascript(window, pump, "!!document.querySelector('#wf-output-list img')")
                    is True
                )
            )
            wait_idle(window, pump)
        assert window.authoring.projection is not None
        assert len(window.authoring.projection.project.graph.nodes) == nodes
        assert not window.authoring.projection.issues
        javascript(window, pump, DRIVER)
        # Reject an untrusted click before collecting any real sample.
        javascript(
            window,
            pump,
            """
          Object.assign(p009perf,{armed:true,pending:true,kind:'node',expected:'verify',
            selector:'[data-node=verify] .wf-node-title'});
          document.querySelector('[data-node=verify] .wf-node-title').click();true
        """,
        )
        assert javascript(window, pump, "JSON.stringify(p009perf.errors)") == '["Non-native click"]'
        javascript(window, pump, "p009perf.errors=[];true")
        for theme in ("forest", "ember", "iris", "neutral"):
            native_click(window, pump, "#wf-hide")
            pump.waitUntil(
                lambda: (
                    javascript(
                        window, pump, "!document.querySelector('#workflow-editor-dialog').open"
                    )
                    is True
                )
            )
            native_click(window, pump, '[data-action="settings"]')
            native_click(window, pump, f'[data-appearance-theme="{theme}"]')
            pump.waitUntil(lambda theme=theme: window.appearance.values["theme"] == theme)
            pump.waitUntil(
                lambda: (
                    javascript(
                        window,
                        pump,
                        "document.querySelector('#appearance-status').textContent.includes('已保存')",
                    )
                    is True
                )
            )
            native_click(window, pump, '[data-action="close-drawer"]')
            pump.waitUntil(
                lambda: javascript(window, pump, "document.querySelector('#drawer').hidden") is True
            )
            native_click(window, pump, "[data-workflow-open]")
            pump.waitUntil(
                lambda: (
                    javascript(
                        window,
                        pump,
                        "!document.querySelector('#workflow-editor-dialog').getAnimations({subtree:true}).some(a=>a.playState==='running')",
                    )
                    is True
                )
            )
            for kind in ("node", "preview") if nodes == 3 else ("node",):
                raw: list[dict[str, object]] = []
                for index in range(warmup + samples):
                    javascript(
                        window, pump, "document.querySelector('[data-wf-view=graph]').click();true"
                    )
                    wait_idle(window, pump)
                    if kind == "node":
                        selected = javascript(window, pump, "workflowEditor.snapshot().selected")
                        expected = "analyze" if selected != "analyze" else "verify"
                        selector = f"[data-node={expected}] .wf-node-title"
                        javascript(
                            window,
                            pump,
                            f"document.querySelector({json.dumps(selector)}).scrollIntoView({{block:'nearest',inline:'nearest'}});true",
                        )
                    else:
                        expected, selector = "", "[data-wf-view=results]"
                    observed, _started = observe(window, pump, kind, selector, expected)
                    raw.append({"warmup": index < warmup, **observed})
                name = f"{theme}-{kind}"
                (folder / f"{name}-raw.json").write_text(
                    json.dumps(raw, indent=2), encoding="utf-8"
                )
                formal = raw[warmup:]
                groups[name] = {
                    "feedback_ms": distribution([cast(float, s["feedback_ms"]) for s in formal]),
                    "settled_ms": distribution([cast(float, s["settled_ms"]) for s in formal]),
                }
        controls: list[dict[str, object]] = []
        if nodes == 3:
            for index in range(warmup + samples):
                assert (
                    javascript(
                        window,
                        pump,
                        """(() => {
                  document.querySelector('[data-wf-view=graph]').click();
                  document.querySelector('[data-wf-select=analyze]').click();
                  const polarity=document.querySelector('[data-wf-field=polarity]');
                  polarity.value=polarity.value==='light'?'dark':'light';
                  polarity.dispatchEvent(new Event('change'));
                  document.querySelector('#wf-run').click();return true;
                })()""",
                    )
                    is True
                )
                pump.waitUntil(
                    lambda: (
                        bool(events)
                        and events[-1][1].state == "running"
                        and events[-1][1].child is not None
                        and events[-1][1].child.pid is not None
                    ),
                    timeout=30000,
                )
                before = events[-1][1]
                assert before.child is not None
                paused_run = before.child.run_id
                pause, start = observe(window, pump, "pause", "#wf-pause")
                pump.waitUntil(lambda: events[-1][1].state == "paused")
                ack = next(t for t, s in events if t >= start and s.state in ("pausing", "paused"))
                paused = events[-1]
                native_click(window, pump, "#wf-resume")
                pump.waitUntil(
                    lambda paused_run=paused_run: (
                        events[-1][1].state == "running"
                        and events[-1][1].child is not None
                        and events[-1][1].child.pid is not None
                        and events[-1][1].child.run_id != paused_run
                    )
                )
                cancel_before = events[-1][1]
                cancel, cancel_start = observe(window, pump, "cancel", "#wf-cancel")
                pump.waitUntil(lambda: events[-1][1].phase == "closed")
                end = events[-1]
                assert end[1].state == "cancelled"
                cancel_ack = next(
                    t
                    for t, s in events
                    if t >= cancel_start and s.state in ("cancelling", "cancelled")
                )
                wait_idle(window, pump)
                controls.append(
                    {
                        "warmup": index < warmup,
                        "pause": pause,
                        "cancel": cancel,
                        "pause_ack_ms": (ack - start) * 1000,
                        "pause_boundary_ms": (paused[0] - start) * 1000,
                        "cancel_ack_ms": (cancel_ack - cancel_start) * 1000,
                        "cancel_to_batch_closed_ms": (end[0] - cancel_start) * 1000,
                        "pause_request": asdict(before),
                        "cancel_request": asdict(cancel_before),
                        "terminal": asdict(end[1]),
                        "editor_store_retained": not window.authoring.resources_closed,
                    }
                )
                (folder / "controls-raw.json").write_text(
                    json.dumps(controls, indent=2), encoding="utf-8"
                )
            formal_controls = controls[warmup:]
            groups["neutral-controls"] = {
                key: distribution([cast(float, s[key]) for s in formal_controls])
                for key in (
                    "pause_ack_ms",
                    "pause_boundary_ms",
                    "cancel_ack_ms",
                    "cancel_to_batch_closed_ms",
                )
            }
        result: dict[str, object] = {
            "nodes": nodes,
            "synthetic_annotations": 12,
            "groups": groups,
            "memory_host": windows_memory(os.getpid()),
            "memory_renderer": windows_memory(int(window.web.page().renderProcessPid())),
            "workspace": workspace,
            "environment": json.loads(
                cast(
                    str,
                    javascript(
                        window,
                        pump,
                        "JSON.stringify({viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,visibility:document.visibilityState})",
                    ),
                )
            ),
            "non_native_guard": "rejected",
        }
    finally:
        close_and_dispose_window(
            window,
            cast("QtBot", pump),
            resources_closed=lambda: (
                window.host.resources_closed and window.authoring.resources_closed
            ),
            timeout=30000,
        )
    with Workspace.open(workspace) as store:
        result["runs"] = [r.model_dump(mode="json") for r in store.list_runs()]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--case", choices=("standard", "upper", "both"), default="both")
    args = parser.parse_args()
    if platform.system() != "Windows" or os.environ.get("QT_QPA_PLATFORM", "windows") != "windows":
        parser.error("Requires native Windows Qt platform")
    if args.samples < 1 or args.warmup < 0:
        parser.error("Invalid sample counts")
    from PySide6.QtCore import qVersion
    from PySide6.QtWidgets import QApplication

    output = args.output.resolve()
    output.mkdir(parents=True)
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    cases = (3, 64) if args.case == "both" else (3,) if args.case == "standard" else (64,)
    results = [run_case(output / f"nodes-{n}", n, args.warmup, args.samples) for n in cases]
    report = {
        "schema_version": 1,
        "source_commit": source_commit,
        "qpa": app.platformName(),
        "samples": args.samples,
        "warmup": args.warmup,
        "qt": qVersion(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "gpu_flags": os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", ""),
        "results": results,
        "scope": (
            "Native trusted input; DOM plus two RAF; settled separately. "
            "No physical scanout/science/target-fleet claim. "
            "Cancel closes batch, editor store intentionally remains open."
        ),
    }
    (output / "results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps({"output": str(output), "cases": list(cases), "samples": args.samples}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
