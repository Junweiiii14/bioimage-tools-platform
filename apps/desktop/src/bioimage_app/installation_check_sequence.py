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


def verify_sequence_installation(
    report_path: Path, *, automatic: bool = False, supervision: bool = False
) -> int:
    import numpy as np
    import tifffile
    from PySide6.QtCore import QSettings, QTimer
    from PySide6.QtWidgets import QApplication
    from shiboken6 import isValid
    from wb_tool.api import (
        WBFigureProject,
        WBIntakeCropProject,
        WBIntakeOutputProject,
        WBIntakeProject,
        WBIntakeWorkflowProject,
        intake_workflow_digest,
        intake_workflow_snapshot,
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
            pixels = np.full((72, 144), value, dtype=np.uint16)
            if automatic:
                # Signal direction differs from its same-acquisition white-light guide.
                count, angle = (4, 3) if value == 1000 else (5, -3)
                yy, xx = np.mgrid[:300, :700]
                c, s = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
                u, v = (xx - 350) * c + (yy - 150) * s, -(xx - 350) * s + (yy - 150) * c
                width = count * 48 + 20
                pixels = np.tile(np.linspace(43000, 63000, 700).astype(np.uint16), (300, 1))
                gc, gs = np.cos(np.deg2rad(angle * 8 / 3)), np.sin(np.deg2rad(angle * 8 / 3))
                gu, gv = (xx - 350) * gc + (yy - 150) * gs, -(xx - 350) * gs + (yy - 150) * gc
                guide = np.full(xx.shape, 15, dtype=np.uint16)
                guide[(np.abs(gu) < width / 2) & (np.abs(gv) < 45)] = 50000
                merged = guide.copy()
                for index in range(count):
                    pixels[(np.abs(u - (-width / 2 + 34 + index * 48)) < 17) & (np.abs(v) < 7)] = (
                        8000
                    )
                    merged[(np.abs(u - (-width / 2 + 34 + index * 48)) < 17) & (np.abs(v) < 7)] = (
                        8000
                    )
                for peer, peer_pixels in ((2, guide), (3, merged)):
                    peer_path = sources / name.replace("(1)", f"({peer})")
                    tifffile.imwrite(peer_path, peer_pixels)
                    originals[peer_path] = sha256(peer_path.read_bytes()).hexdigest()
            tifffile.imwrite(path, pixels)
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
        observed_shutdown = ""
        required = {
            "top-fields-one-start",
            "review-required-before-own-fig",
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
        if automatic:
            required.difference_update(("review-required-before-own-fig", "two-human-continues"))
            required.update(
                (
                    "no-human-crop-confirmations",
                    "display-correction",
                    "visible-gray-image",
                    "visible-results-table",
                    "signal-direction-independent-of-guide",
                    "original-preview-replaces-thumbnail",
                )
            )

        if supervision:
            required.update(("supervision-curve-grid-export", "grid-safe-reopen"))

        def record() -> None:
            report.seek(0)
            report.truncate()
            json.dump(
                {
                    "schema": 1,
                    "diagnostic": "supervision_installed@1"
                    if supervision
                    else "automatic_flow_installed@1"
                    if automatic
                    else "fig_sequence_installed@1",
                    "phase": phase,
                    "failed_phase": failed_phase,
                    "shutdown_stage": observed_shutdown,
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
                        (
                            "Synthetic uint16 paired-guide images, automatic crop, N=4/5. "
                            if automatic
                            else "Synthetic uint16 constant images, explicit source ROI, N=4/5. "
                        )
                        + "Engineering page/worker/output checks; not scientific accuracy, "
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

        from bioimage_app.installation_check_supervision import SupervisionCheck

        supervision_check = SupervisionCheck(window, root)

        def observed(project: WBFigureProject) -> None:
            try:
                if not isinstance(
                    project, WBIntakeWorkflowProject
                ) or project.workflow.policy not in {"intake_workflow@3", "intake_workflow@4"}:
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
                    prerequisites = [s for s in steps if s.stage in earlier]
                    if project.workflow.policy == "intake_workflow@4":
                        if step.stage == "export":
                            statuses = {(s.stage, s.target_id): s.status for s in steps}
                            for other in steps:
                                if other.stage == "export":
                                    continue
                                members = [
                                    p.protein_id
                                    for p in project.intake.proteins
                                    if p.figure_id == other.target_id
                                ]
                                ready = (
                                    other.stage == "crop"
                                    or (
                                        other.stage == "compose"
                                        and bool(members)
                                        and all(statuses["crop", row] == "done" for row in members)
                                    )
                                    or (
                                        other.stage == "measure"
                                        and statuses["compose", other.target_id] == "done"
                                    )
                                )
                                if other.status == "running" or (
                                    other.status == "pending" and ready
                                ):
                                    errors.append("Export began before runnable Fig work drained")
                        members = {
                            p.protein_id
                            for p in project.intake.proteins
                            if p.figure_id == step.target_id
                        }
                        prerequisites = [
                            s
                            for s in prerequisites
                            if (step.stage == "compose" and s.target_id in members)
                            or (
                                step.stage == "measure"
                                and s.stage == "compose"
                                and s.target_id == step.target_id
                            )
                        ]
                    if any(s.status != "done" for s in prerequisites):
                        errors.append("Observed a running stage before its Fig prerequisites")
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
            nonlocal modes, worker_pids, js_value, observed_status, observed_shutdown
            nonlocal review_submitted
            try:
                observed_shutdown = window.shutdown_stage
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
                if phase == "reopen" and window.shutdown_stage.startswith("confirm_"):
                    raise ValueError(
                        "Reopen requested a transition confirmation: " + window.shutdown_stage
                    )
                if pending_js or window.shutdown_stage != "idle" or window.host.operation_busy:
                    return
                project = window.host.view.project()
                observed_status = str(window.bridge.snapshot()["status"])
                if not isinstance(project, WBIntakeProject) or not window.host.workspace_path:
                    return
                if phase == "import":
                    if (
                        len(project.intake.sources) == (6 if automatic else 2)
                        and not window.host.has_unsaved_changes
                    ):
                        phase = "configure"
                        javascript(
                            CONFIGURE.replace("[1].click();", "[3].click();")
                            if automatic
                            else CONFIGURE
                        )
                elif phase == "configure":
                    if js_value is True:
                        checks.append("top-fields-one-start")
                        phase = "processing"
                    else:
                        javascript(
                            CONFIGURE.replace("[1].click();", "[3].click();")
                            if automatic
                            else CONFIGURE
                        )
                elif phase == "processing":
                    if not isinstance(project, WBIntakeWorkflowProject):
                        return
                    blocked = next(
                        (s for s in project.workflow.steps if s.status == "needs_review"), None
                    )
                    if blocked and blocked.stage == "crop" and blocked.target_id not in corrected:
                        if automatic:
                            raise ValueError(
                                "Reliable geometry unexpectedly required human confirmation"
                            )
                        automation = window.host.intake_workflow.batch_snapshot(project)
                        # UI I/O may briefly be idle between callbacks. The v4
                        # ledger must also finish draining other work/partial export.
                        if (
                            not automation
                            or not automation["paused"]
                            or any(s.status == "running" for s in project.workflow.steps)
                            or intake_workflow_snapshot(project)["pending_ready"]
                        ):
                            return
                        blocked_fig = next(
                            p.figure_id
                            for p in project.intake.proteins
                            if p.protein_id == blocked.target_id
                        )
                        if any(
                            s.attempt
                            for s in project.workflow.steps
                            if s.stage in {"compose", "measure"} and s.target_id == blocked_fig
                        ):
                            raise ValueError("Blocked Fig advanced before its crop review")
                        if isinstance(project, WBIntakeOutputProject) and any(
                            output.complete for output in project.intake_outputs
                        ):
                            raise ValueError("Incomplete project was labelled complete")
                        javascript(
                            "select("
                            + json.dumps(blocked.target_id)
                            + ");switchMode('review');'selected'"
                        )
                        if "review-required-before-own-fig" not in checks:
                            checks.append("review-required-before-own-fig")
                        phase = "review:" + blocked.target_id
                        js_value = None
                        review_submitted = False
                    elif all(s.status == "done" for s in project.workflow.steps):
                        if not isinstance(project, WBIntakeOutputProject):
                            raise ValueError("No output project")
                        if (
                            len(corrected) != (0 if automatic else 2)
                            or len(project.intake_figures) != 2
                        ):
                            raise ValueError("Missing two independent Fig reviews or saved images")
                        checks.append(
                            "no-human-crop-confirmations" if automatic else "two-human-continues"
                        )
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
                                or not crop.geometry_ready
                                or (automatic and (crop.policy != "intake_crop@3" or crop.reviewed))
                                or len(crop.slots) != row.lane_count
                            ):
                                raise ValueError("Missing original crop or fixed slots")
                            with tifffile.TiffFile(
                                Path(window.host.workspace_path) / crop.raw_crop.relative_path
                            ) as image:
                                pixels = image.asarray()
                            if automatic:
                                assert crop.crop is not None
                                source = sources / (
                                    "A_123456 (1).tif"
                                    if row.protein == "Alpha"
                                    else "B_123456 (1).tif"
                                )
                                with tifffile.TiffFile(source) as original:
                                    raw = original.asarray()
                                r = crop.crop
                                if not np.array_equal(pixels, raw[r.y0 : r.y1, r.x0 : r.x1]):
                                    raise ValueError(
                                        "Automatic crop changed original uint16 samples"
                                    )
                                frame = next(
                                    s.display_frame
                                    for s in project.composition.slices
                                    if s.row_id == row.row_id
                                )
                                if frame is None or abs(abs(frame.angle_degrees) - 3) > 1:
                                    raise ValueError("Small-angle correction was lost")
                                if crop.geometry_policy != "instrument_guided_geometry@2":
                                    raise ValueError(
                                        "Diagnostic did not exercise paired-guide path"
                                    )
                            elif (
                                pixels.dtype != np.uint16
                                or pixels.shape != (40, 120)
                                or not np.all(pixels == (1000 if row.protein == "Alpha" else 2000))
                            ):
                                raise ValueError("Original uint16 crop changed")
                        checks.append("original-pixel-crops")
                        if automatic:
                            checks.append("display-correction")
                            checks.append("signal-direction-independent-of-guide")
                        if len(cast(list[object], window.bridge.snapshot()["cells"])) != 9 or any(
                            (b.status != "not_detected" or b.measurement is not None)
                            if not automatic
                            else (b.status == "not_detected" and b.measurement is not None)
                            for result in window.host.project_results
                            for lane in result.result.lanes
                            for b in lane.bands
                        ):
                            raise ValueError("Missing/flat signal was turned into valid zero")
                        checks.append("missing-is-not-zero")
                        if not project.intake_outputs or not project.intake_outputs[-1].complete:
                            raise ValueError("Output was not committed")
                        output = Path(project.intake_outputs[-1].destination)
                        index = json.loads((output / "index.json").read_bytes())
                        if (
                            not index["complete"]
                            or index["errors"]
                            or not (output / "灰度汇总.xlsx").is_file()
                        ):
                            raise ValueError("Output index or workbook incomplete")
                        output_digest = sha256((output / "项目恢复.zip").read_bytes()).hexdigest()
                        checks.append("committed-output")
                        phase = "page-automatic" if automatic else "page-results"
                        js_value = None
                elif phase.startswith("review:"):
                    target = phase.split(":", 1)[1]
                    if isinstance(project, WBIntakeWorkflowProject) and any(
                        s.status == "running" for s in project.workflow.steps
                    ):
                        return
                    persisted = isinstance(project, WBIntakeCropProject) and any(
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
                    # A source-selection callback is not a review-click receipt.
                    elif js_value == "submitted":
                        review_submitted = True
                        js_value = None
                    else:
                        if not isinstance(project, WBIntakeWorkflowProject):
                            raise ValueError("Review lost its workflow snapshot")
                        javascript(
                            "(()=>{if(state.busy||sequenceOutstanding||mode!=='review'||row()?.id!=="
                            + json.dumps(target)
                            + "||state.intake?.workflow?.digest!=="
                            + json.dumps(intake_workflow_digest(project))
                            + "||state.intake.workflow.steps.some(s=>s.status==='running'))"
                            "return 'waiting';"
                            "commitCrop({x:12,y:10,width:120,height:40},row().roi);"
                            "const b=document.querySelector('[data-intake-crop-action=run]');"
                            "if(!b||b.disabled)return 'waiting';b.click();return 'submitted';})()"
                        )
                elif phase == "page-automatic":
                    if isinstance(js_value, str):
                        modes = json.loads(js_value)
                        if not all(m in modes for m in ("review", "layout", "quant", "results")):
                            raise ValueError("Automatic navigation missed a real stage")
                        phase, js_value = "page-original", None
                        javascript("select(state.rows[0].id);switchMode('review');false")
                    else:
                        javascript("mode==='results'?JSON.stringify(sequenceModes):false")
                elif phase == "page-original":
                    if js_value is True:
                        checks.append("original-preview-replaces-thumbnail")
                        phase, js_value = "page-gray", None
                        javascript("switchMode('quant');false")
                    else:
                        javascript("document.querySelector('#source-image').naturalWidth===700")
                elif phase == "page-gray":
                    if js_value is True:
                        checks.append("visible-gray-image")
                        phase, js_value = "page-results", None
                        javascript("switchMode('results');false")
                    else:
                        javascript(
                            "(()=>{const img=document.querySelector('.intake-measure-raster img');"
                            "return !!img&&img.checkVisibility()&&img.naturalWidth>0&&"
                            "document.querySelectorAll('.intake-measure-raster polygon')"
                            ".length>=4;})()"
                        )
                elif phase == "page-results":
                    if automatic:
                        if js_value is not True:
                            javascript(
                                "mode==='results'&&"
                                "document.querySelector('.results-scroll table')"
                                ".checkVisibility()&&"
                                "document.querySelectorAll('#results-body tr').length===9"
                            )
                            return
                        checks.append("visible-results-table")
                        js_value = json.dumps(modes)
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
                        phase = "supervision" if supervision else "reopen"
                        if not supervision:
                            window.open_project(workspace)
                    else:
                        javascript("mode==='results'?JSON.stringify(sequenceModes):false")
                elif phase == "supervision":
                    if supervision_check.poll():
                        checks.append("supervision-curve-grid-export")
                        run_ids = tuple(p.run.run_id for p in project.analyses if p.run)
                        phase = "reopen"
                        window.open_project(workspace)
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
                        or sha256((output / "项目恢复.zip").read_bytes()).hexdigest()
                        != output_digest
                    ):
                        raise ValueError("Reopen resumed navigation or changed old output")
                    checks.append("safe-reopen")
                    if supervision:
                        from wb_tool.api import WBIntakeGridProject

                        if (
                            not isinstance(project, WBIntakeGridProject)
                            or project.grid.columns != 1
                            or project.grid.gap != 17
                        ):
                            raise ValueError("Saved grid changed on reopen")
                        checks.append("grid-safe-reopen")
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
        with (
            patch.object(window.host, "save", new=traced_save),
            patch(
                "PySide6.QtWidgets.QFileDialog.getSaveFileName",
                side_effect=supervision_check.destination,
            ),
        ):
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
