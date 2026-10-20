"""Opt-in two-Fig installed diagnostic using the shipped page and real worker processes."""

import json
import os
import sys
import tempfile
import time
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import cast
from unittest.mock import patch

CONFIGURE = """(()=>{
 const add=document.querySelector('[data-group-action=add-fig]');
 if(!add||add.disabled||state.busy)return false;
 if(!window.sequenceRequestObserver){
  window.sequenceRequestObserver=bridge.request;
  window.sequenceOutstanding=0;
  bridge.request=function(action,payload,callback){
   sequenceOutstanding++;
   return sequenceRequestObserver.call(bridge,action,payload,result=>{
    sequenceOutstanding--;if(callback)callback(result);
   });
  };
 }
 window.sequenceModes=[];window.sequenceSwitch=switchMode;
 switchMode=function(next){const result=sequenceSwitch(next);
   sequenceModes.push(mode);return result;};
 const fill=(el,value)=>{el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));};
 add.click();fill(document.querySelector('[data-group-field=fig-label]'),'First');
 fill(document.querySelector('[data-group-field=lanes]'),'4');
 fill(document.querySelector('[data-group-field=proteins]'),'Alpha');
 document.querySelector('[data-group-action=add-fig]').click();
 fill(document.querySelectorAll('[data-group-field=fig-label]')[1],'Second');
 fill(document.querySelectorAll('[data-group-field=lanes]')[1],'5');
 fill(document.querySelectorAll('[data-group-field=proteins]')[1],'Beta');
 document.querySelectorAll('[data-group-source]')[0].click();
 document.querySelectorAll('[data-group-source]')[1].click();
 const start=document.querySelector('[data-group-action=start]');
 if(start.disabled)throw new Error('Valid two-Fig sequence cannot start');
 start.click();return true;
})()"""


def verify_sequence_installation(report_path: Path) -> int:
    import numpy as np
    import tifffile
    from PySide6.QtCore import QSettings, QTimer
    from PySide6.QtWidgets import QApplication
    from shiboken6 import isValid
    from wb_tool.api import (
        WBFigureProject,
        WBIntakeOutputProject,
        WBIntakeProject,
        WBIntakeWorkflowProject,
    )

    from bioimage_app.web_window import WebWorkbenchWindow

    with (
        report_path.open("x", encoding="utf-8") as report,
        tempfile.TemporaryDirectory(prefix="bioimage-fig-sequence-") as temporary,
    ):
        root = Path(temporary)
        sources = root / "原图"
        sources.mkdir()
        originals: dict[Path, str] = {}
        for name, value in (("A_123456 (1).tif", 1000), ("B_123456 (1).tif", 2000)):
            path = sources / name
            tifffile.imwrite(path, np.full((72, 144), value, dtype=np.uint16))
            originals[path] = sha256(path.read_bytes()).hexdigest()
        settings = QSettings(str(root / "sequence.ini"), QSettings.Format.IniFormat)
        settings.setValue("project_parent", str(root / "项目"))
        started = time.monotonic()
        phase = "import"
        failed_phase = ""
        checks: list[str] = []
        errors: list[str] = []
        modes: list[str] = []
        stage_events: list[dict[str, object]] = []
        worker_pids: list[int] = []
        corrected: set[str] = set()
        review_submitted = False
        pending_js = False
        js_value: object = None
        workspace = ""
        epoch = 0
        output: Path | None = None
        output_digest = ""
        run_ids: tuple[str, ...] = ()
        observed_status = ""
        required = {
            "top-fields-one-start",
            "whole-batch-pause",
            "two-human-continues",
            "stage-barriers",
            "real-workers",
            "original-pixel-crops",
            "missing-is-not-zero",
            "automatic-navigation",
            "committed-output",
            "safe-reopen",
            "originals-unchanged",
            "owned-resources-closed",
            "owned-window-deleted",
        }

        def record() -> None:
            report.seek(0)
            report.truncate()
            json.dump(
                {
                    "schema": 1,
                    "diagnostic": "fig_sequence_installed@1",
                    "phase": phase,
                    "failed_phase": failed_phase,
                    "checks": checks,
                    "errors": errors,
                    "elapsed": time.monotonic() - started,
                    "runtime_executable": sys.executable,
                    "package_file": __file__,
                    "isolated_imports": bool(sys.flags.isolated),
                    "release_channel": os.environ.get("BIOIMAGE_RELEASE_CHANNEL", ""),
                    "worker_pids": worker_pids,
                    "page_modes": modes,
                    "stage_events": stage_events,
                    "stage_event_source": "committed-save-callback",
                    "last_status": observed_status,
                    "corrected_rows": sorted(corrected),
                    "limitations": (
                        "Synthetic uint16 constant images, explicit source ROI, N=4/5. "
                        "Engineering page/worker/output checks; not scientific accuracy, "
                        "physical input/DPI or clean Windows acceptance."
                    ),
                },
                report,
                ensure_ascii=False,
                indent=2,
            )
            report.flush()

        record()
        try:
            app = QApplication(["BioImage Fig sequence diagnostic"])
            app.setQuitOnLastWindowClosed(False)
            window = WebWorkbenchWindow(settings=settings)
        except (ValueError, OSError, RuntimeError) as error:
            errors.append(str(error))
            phase = "failed"
            failed_phase = "construction"
            record()
            return 1

        def observed(project: WBFigureProject) -> None:
            try:
                if (
                    not isinstance(project, WBIntakeWorkflowProject)
                    or project.workflow.policy != "intake_workflow@3"
                ):
                    return
                steps = project.workflow.steps
                for step in steps:
                    if step.status != "running":
                        continue
                    earlier = {
                        "crop": (),
                        "compose": ("crop",),
                        "measure": ("crop", "compose"),
                        "export": ("crop", "compose", "measure"),
                    }[step.stage]
                    if any(s.status != "done" for s in steps if s.stage in earlier):
                        errors.append(
                            "Observed a running stage before its whole-batch prerequisites"
                        )
                    entry: dict[str, object] = {
                        "stage": step.stage,
                        "target": step.target_id,
                        "attempt": step.attempt,
                        "revision": project.revision,
                    }
                    if entry not in stage_events:
                        stage_events.append(entry)
            except (ValueError, KeyError, TypeError) as error:
                errors.append("Invalid stage snapshot: " + str(error))

        original_save = window.host.save

        def traced_save(
            after: Callable[[], None] | None = None,
            *,
            transform: Callable[[WBFigureProject], WBFigureProject] | None = None,
            install_guard: Callable[[], bool] | None = None,
        ) -> None:
            def committed() -> None:
                # Bridge publication is coalesced. Observe every installed durable
                # revision before its normal continuation can claim the next stage.
                observed(window.host.view.project())
                if after:
                    after()

            original_save(committed, transform=transform, install_guard=install_guard)

        def received(value: object) -> None:
            nonlocal pending_js, js_value
            pending_js = False
            js_value = value

        def javascript(code: str) -> None:
            nonlocal pending_js, js_value
            pending_js = True
            js_value = None
            window.web.page().runJavaScript(code, received)

        def poll() -> None:
            nonlocal phase, failed_phase, workspace, epoch, output, output_digest, run_ids
            nonlocal modes, worker_pids, js_value, observed_status
            nonlocal review_submitted
            try:
                elapsed = time.monotonic() - started
                if elapsed > 150:
                    errors.append("Owned diagnostic shutdown exceeded 150 seconds")
                    timer.stop()
                    app.exit(1)
                    return
                if phase == "dispose":
                    if not isValid(window):
                        checks.append("owned-window-deleted")
                        timer.stop()
                        app.exit(0)
                    return
                if (elapsed > 120 or errors) and phase != "close":
                    if elapsed > 120:
                        errors.append("Sequence diagnostic exceeded 120 seconds")
                    failed_phase = phase
                    phase = "close"
                    window.close()
                if phase == "close":
                    if window.shutdown_stage in {"confirm_busy", "confirm_draft", "confirm_dirty"}:
                        choice = {
                            "confirm_busy": "cancel",
                            "confirm_draft": "discard",
                            "confirm_dirty": "save",
                        }[window.shutdown_stage]
                        window.bridge.session("reply", json.dumps({"choice": choice}))
                    elif window.host.resources_closed and not window.isVisible():
                        checks.append("owned-resources-closed")
                        phase = "dispose"
                        window.deleteLater()
                    return
                if pending_js or window.shutdown_stage != "idle" or window.host.operation_busy:
                    return
                project = window.host.view.project()
                observed_status = str(window.bridge.snapshot()["status"])
                if not isinstance(project, WBIntakeProject) or not window.host.workspace_path:
                    return
                if phase == "import":
                    if len(project.intake.sources) == 2 and not window.host.has_unsaved_changes:
                        phase = "configure"
                        javascript(CONFIGURE)
                elif phase == "configure":
                    if js_value is True:
                        checks.append("top-fields-one-start")
                        phase = "processing"
                    else:
                        javascript(CONFIGURE)
                elif phase == "processing":
                    if not isinstance(project, WBIntakeWorkflowProject):
                        return
                    blocked = next(
                        (s for s in project.workflow.steps if s.status == "needs_review"), None
                    )
                    if blocked and blocked.stage == "crop" and blocked.target_id not in corrected:
                        if any(s.attempt for s in project.workflow.steps if s.stage != "crop"):
                            raise ValueError("Whole batch advanced before all crop reviews")
                        if "whole-batch-pause" not in checks:
                            checks.append("whole-batch-pause")
                        phase = "review:" + blocked.target_id
                        js_value = None
                        review_submitted = False
                    elif all(s.status == "done" for s in project.workflow.steps):
                        if not isinstance(project, WBIntakeOutputProject):
                            raise ValueError("No output project")
                        if len(corrected) != 2 or len(project.intake_figures) != 2:
                            raise ValueError("Missing two independent Fig reviews or saved images")
                        checks.append("two-human-continues")
                        worker_pids = [p.run.pid for p in project.analyses if p.run and p.run.pid]
                        run_ids = tuple(p.run.run_id for p in project.analyses if p.run)
                        if len(worker_pids) != 2 or any(
                            not p.run or p.run.state != "succeeded" for p in project.analyses
                        ):
                            raise ValueError("Missing durable real worker receipts")
                        checks.append("real-workers")
                        for crop in project.intake_crops:
                            row = next(r for r in project.rows if r.row_id == crop.row_id)
                            if (
                                crop.raw_crop is None
                                or not crop.reviewed
                                or len(crop.slots) != row.lane_count
                            ):
                                raise ValueError("Missing original crop or fixed slots")
                            with tifffile.TiffFile(
                                Path(window.host.workspace_path) / crop.raw_crop.relative_path
                            ) as image:
                                pixels = image.asarray()
                            value = 1000 if row.protein == "Alpha" else 2000
                            if (
                                pixels.dtype != np.uint16
                                or pixels.shape != (40, 120)
                                or not np.all(pixels == value)
                            ):
                                raise ValueError("Original uint16 crop changed")
                        checks.append("original-pixel-crops")
                        if len(cast(list[object], window.bridge.snapshot()["cells"])) != 9 or any(
                            b.status != "not_detected" or b.measurement is not None
                            for result in window.host.project_results
                            for lane in result.result.lanes
                            for b in lane.bands
                        ):
                            raise ValueError("Missing/flat signal was turned into valid zero")
                        checks.append("missing-is-not-zero")
                        if (
                            len(project.intake_outputs) != 1
                            or not project.intake_outputs[0].complete
                        ):
                            raise ValueError("Output was not committed")
                        output = Path(project.intake_outputs[0].destination)
                        index = json.loads((output / "index.json").read_bytes())
                        if (
                            not index["complete"]
                            or index["errors"]
                            or not (output / "measurements.xlsx").is_file()
                        ):
                            raise ValueError("Output index or workbook incomplete")
                        output_digest = sha256((output / "project.zip").read_bytes()).hexdigest()
                        checks.append("committed-output")
                        phase = "page-results"
                elif phase.startswith("review:"):
                    target = phase.split(":", 1)[1]
                    persisted = isinstance(project, WBIntakeOutputProject) and any(
                        e.row_id == target and e.reviewed for e in project.intake_crops
                    )
                    if persisted:
                        corrected.add(target)
                        phase = "processing"
                    elif review_submitted:
                        if js_value == "acknowledged":
                            raise ValueError(
                                "Review click did not commit its correction: " + observed_status
                            )
                        javascript("sequenceOutstanding===0?'acknowledged':'pending'")
                    elif js_value is True:
                        review_submitted = True
                        js_value = None
                    else:
                        javascript(
                            "(()=>{if(state.busy||sequenceOutstanding||mode!=='review'||row()?.id!=="
                            + json.dumps(target)
                            + ")return false;"
                            "commitCrop({x:12,y:10,width:120,height:40},row().roi);"
                            "const b=document.querySelector('[data-intake-crop-action=run]');"
                            "if(!b||b.disabled)return false;b.click();return true;})()"
                        )
                elif phase == "page-results":
                    if isinstance(js_value, str):
                        modes = json.loads(js_value)
                        if not all(m in modes for m in ("review", "layout", "quant", "results")):
                            raise ValueError("Shipped page did not automatically visit all stages")
                        if not isinstance(project, WBIntakeWorkflowProject) or {
                            (e["stage"], e["target"]) for e in stage_events
                        } != {(s.stage, s.target_id) for s in project.workflow.steps}:
                            raise ValueError("Not every actual running batch stage was observed")
                        checks.extend(("automatic-navigation", "stage-barriers"))
                        workspace, epoch = window.host.workspace_path, window.bridge.session_epoch
                        phase = "reopen"
                        window.open_project(workspace)
                    else:
                        javascript("mode==='results'?JSON.stringify(sequenceModes):false")
                elif phase == "reopen":
                    if window.bridge.session_epoch <= epoch:
                        return
                    if (
                        not isinstance(project, WBIntakeOutputProject)
                        or project.workflow.approved
                        or tuple(p.run.run_id for p in project.analyses if p.run) != run_ids
                    ):
                        raise ValueError("Reopen changed or resumed worker history")
                    automation = cast(
                        dict[str, object],
                        cast(dict[str, object], window.bridge.snapshot()["intake"])["automation"],
                    )
                    if (
                        automation["follow"]
                        or output is None
                        or sha256((output / "project.zip").read_bytes()).hexdigest()
                        != output_digest
                    ):
                        raise ValueError("Reopen resumed navigation or changed old output")
                    checks.append("safe-reopen")
                    if any(
                        sha256(p.read_bytes()).hexdigest() != digest
                        for p, digest in originals.items()
                    ):
                        raise ValueError("Originals changed")
                    checks.append("originals-unchanged")
                    phase = "close"
                    window.close()
                record()
            except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
                errors.append(str(error))
                failed_phase = phase
                phase = "close"
                record()
                window.close()

        timer = QTimer(app)
        timer.timeout.connect(poll)
        with patch.object(window.host, "save", new=traced_save):
            try:
                window.show()
                window.start_from_images([sources], intake=True)
            except (ValueError, OSError, RuntimeError) as error:
                errors.append(str(error))
                phase = "close"
                window.close()
            timer.start(25)
            code = app.exec()
        timer.stop()
        if code or required - set(checks):
            errors.append("Required sequence checks or owned shutdown did not complete")
        phase = "failed" if errors else "passed"
        record()
        return 1 if errors else 0
