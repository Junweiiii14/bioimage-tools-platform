"""Explicit synthetic installed intake diagnostic through the real desktop bridge."""

import json
import os
import sys
import tempfile
import time
import traceback
from hashlib import sha256
from pathlib import Path
from typing import cast

SHORTCUT_PROBE_SCRIPT = """(()=>{
  if(!window.__intakeDiagnosticKeys){
    window.__intakeDiagnosticKeys=[];
    window.addEventListener('keydown',event=>{
      const entries=window.__intakeDiagnosticKeys;
      if(entries.length<12)entries.push({key:event.key,code:event.code,
        ctrl:event.ctrlKey,shift:event.shiftKey,repeat:event.repeat,
        composing:event.isComposing,busy:state.busy,focused:document.hasFocus(),
        target:event.target?.tagName,modal:!!document.querySelector('dialog[open]'),
        drawer:!document.querySelector('#drawer').hidden});
    },true);
  }
  const snapshot={project_id:state.projectId,session_epoch:state.sessionEpoch,
    busy:!!state.busy,focused:document.hasFocus(),
    loaded:!!window.workbenchActions?.loaded(),
    composing:!!window.workbenchActions?.isComposing(),
    modal:!!document.querySelector('dialog[open]'),
    drawer:!document.querySelector('#drawer').hidden,
    editable:!!document.activeElement?.closest?.(
      'input,textarea,select,[contenteditable]:not([contenteditable=false])'),
    dialog_open:!!document.querySelector('#shortcuts-dialog[open]'),
    keys:window.__intakeDiagnosticKeys};
  snapshot.ready=snapshot.focused&&snapshot.loaded&&!snapshot.busy&&
    !snapshot.composing&&!snapshot.modal&&!snapshot.drawer&&!snapshot.editable;
  return JSON.stringify(snapshot);
})()"""


def verify_intake_installation(report_path: Path, *, grouped: bool = False) -> int:
    import numpy as np
    import tifffile
    from PySide6.QtCore import QSettings, QTimer
    from PySide6.QtWidgets import QApplication
    from shiboken6 import isValid
    from tool_contracts.api import RunRecord
    from wb_tool.api import (
        WBIntakeOutputProject,
        WBIntakeProject,
        WBIntakeWorkflowProject,
        intake_digest,
        intake_workflow_digest,
    )

    from bioimage_app.storage import StorageCommand, StorageReply

    # Only this newly created report and this owned temporary corpus are written.
    with (
        report_path.open("x", encoding="utf-8") as report,
        tempfile.TemporaryDirectory(prefix="bioimage-e7-intake-") as temporary,
    ):
        root = Path(temporary)
        sources = root / "仪器原图"
        sources.mkdir()
        originals: dict[Path, str] = {}
        for filename, value in (("a.tif", 1000), ("b.tif", 2000)):
            path = sources / filename
            tifffile.imwrite(path, np.full((72, 144), value, dtype=np.uint16))
            originals[path] = sha256(path.read_bytes()).hexdigest()
        settings = QSettings(str(root / "intake.ini"), QSettings.Format.IniFormat)
        settings.setValue("project_parent", str(root / "中文项目"))
        started = time.monotonic()
        checks: list[str] = []
        errors: list[str] = []
        phase = "bootstrap"
        failed_phase = ""
        shortcut_probe: dict[str, object] = {}
        workspace = ""
        epoch = 0
        saved_runs: tuple[RunRecord, ...] = ()
        saved_outputs: tuple[str, ...] = ()
        original_zip = b""
        js_pending = False
        dom_ready = False
        closed = False
        archive_runs: list[StorageReply] = []
        required = {
            "confirmed-stable-intake",
            "fixed-eight-slot-review",
            "durable-real-workers",
            "missing-is-not-zero",
            "complete-output",
            "saved-project-reopen",
            "repeat-export-no-overwrite",
            "originals-unchanged",
            "real-dom-webchannel",
            "owned-resources-closed",
            "owned-window-deleted",
            "original-pixel-crops",
            "archive-imported-history",
            "archive-resume-output",
        }
        if grouped:
            required.update(
                {"incomplete-group-draft", "grouped-stable-mapping", "shortcut-settings"}
            )

        def record() -> None:
            report.seek(0)
            report.truncate()
            json.dump(
                {
                    "schema": 1,
                    "diagnostic": "grouped_intake_installed@1" if grouped else "intake_installed@1",
                    "phase": phase,
                    "failed_phase": failed_phase,
                    "shortcut_probe": shortcut_probe,
                    "checks": checks,
                    "errors": errors,
                    "elapsed": time.monotonic() - started,
                    "runtime_executable": sys.executable,
                    "package_file": __file__,
                    "isolated_imports": bool(sys.flags.isolated),
                    "release_channel": os.environ.get("BIOIMAGE_RELEASE_CHANNEL", ""),
                    "worker_pids": [run.pid for run in saved_runs],
                    "limitations": (
                        "Synthetic constant uint16 inputs, explicit reviewed source ROI and N=8. "
                        "Flat bands correctly remain not_detected, never valid zero. "
                        "Real worker/OS commits, bridge, export/reopen are engineering checks; "
                        "not scientific accuracy, instrument throughput, native input or DPI."
                    ),
                },
                report,
                ensure_ascii=False,
                indent=2,
            )
            report.flush()

        record()
        try:
            app = QApplication(["BioImage E7 intake diagnostic"])
        except BaseException:
            errors.append(traceback.format_exc())
            phase = "failed"
            record()
            return 1
        app.setQuitOnLastWindowClosed(False)
        window = None
        try:
            from bioimage_app.web_window import WebWorkbenchWindow

            window = WebWorkbenchWindow(settings=settings)
            window.show()
            window.start_from_images([sources], intake=True)
        except BaseException:
            errors.append(traceback.format_exc())
        if window is None:
            errors.append("Window construction failed; owned shutdown cannot be confirmed")
            phase = "failed"
            record()
            return 1
        # Once construction succeeded, even a show/import exception must drain
        # this owned host and delete its window before removing the corpus.
        phase = "close" if errors else "import"

        def current() -> WBIntakeProject:
            project = window.host.view.project()
            if not isinstance(project, WBIntakeProject):
                raise ValueError("Intake diagnostic did not open an intake project")
            return project

        def request(action: str, **data: object) -> None:
            project = current()
            window.bridge.request(
                action,
                json.dumps(
                    {
                        "projectId": project.project_id,
                        "sessionEpoch": window.bridge.session_epoch,
                        "digest": intake_digest(project),
                        **data,
                    }
                ),
            )

        def received(value: object) -> None:
            nonlocal js_pending, dom_ready
            js_pending = False
            dom_ready = value is True

        def shortcut_observed(value: object) -> None:
            nonlocal js_pending, dom_ready, shortcut_probe
            js_pending = False
            if not isinstance(value, str):
                shortcut_probe = {"transport_type": type(value).__name__}
                dom_ready = False
                return
            try:
                decoded: object = json.loads(value)
            except ValueError:
                shortcut_probe = {"transport_error": "Invalid JSON probe"}
                dom_ready = False
                return
            if not isinstance(decoded, dict):
                shortcut_probe = {"transport_error": "Probe must be an object"}
                dom_ready = False
                return
            shortcut_probe = cast(dict[str, object], decoded)
            if phase == "shortcut-open":
                dom_ready = shortcut_probe.get("dialog_open") is True
            elif phase == "shortcut-focus":
                dom_ready = (
                    shortcut_probe.get("ready") is True
                    and shortcut_probe.get("project_id") == current().project_id
                    and shortcut_probe.get("session_epoch") == window.bridge.session_epoch
                )
            else:
                dom_ready = False

        def poll() -> None:
            nonlocal phase, workspace, epoch, saved_runs, saved_outputs, original_zip
            nonlocal js_pending, closed, dom_ready, failed_phase
            try:
                elapsed = time.monotonic() - started
                if elapsed > 150:
                    errors.append("Diagnostic did not finish owned shutdown within 150 seconds")
                    record()
                    timer.stop()
                    app.exit(1)
                    return
                if phase == "dispose":
                    if not isValid(window):
                        checks.append("owned-window-deleted")
                        timer.stop()
                        app.exit(0 if not errors else 1)
                    return
                if elapsed > 120 and phase != "close":
                    errors.append("Diagnostic exceeded 120 seconds")
                    failed_phase = phase
                    phase = "close"
                    record()
                    window.close()
                if phase == "close":
                    if window.shutdown_stage in {"confirm_busy", "confirm_draft"}:
                        choice = "cancel" if window.shutdown_stage == "confirm_busy" else "discard"
                        window.bridge.session("reply", json.dumps({"choice": choice}))
                    elif window.shutdown_stage == "confirm_dirty":
                        window.bridge.session("reply", '{"choice":"save"}')
                    elif window.host.resources_closed and not window.isVisible():
                        closed = True
                        checks.append("owned-resources-closed")
                        phase = "dispose"
                        window.deleteLater()
                    return
                if window.shutdown_stage != "idle" or window.host.operation_busy:
                    return
                if phase == "home-restore" and not window.host.workspace_path:
                    phase = "archive"
                    window.host.restore_archive(
                        str(Path(saved_outputs[0]) / "project.zip"), str(root / "中文恢复")
                    )
                    return
                if not window.host.workspace_path or window.host.has_unsaved_changes:
                    return
                project = current()
                if phase == "import":
                    if len(project.intake.sources) != 2:
                        raise ValueError("Two independent sources were not imported")
                    if grouped:
                        phase = "group-draft"
                        request(
                            "intake_grouping",
                            grouping={
                                "schema_version": 1,
                                "figures": [{"figure_id": "fig-a", "label": "Fig 1"}],
                                "groups": [
                                    {
                                        "group_id": key,
                                        "source_ids": [source.source_id],
                                        "figure_id": "fig-a",
                                        "protein_label": "GAPDH",
                                    }
                                    for key, source in zip(
                                        ("protein-a", "protein-b"),
                                        project.intake.sources,
                                        strict=True,
                                    )
                                ],
                            },
                        )
                        return
                    phase = "plan"
                    request(
                        "intake_plan",
                        figures=[{"figure_id": "fig-a", "label": "Fig 1", "lane_count": 8}],
                        proteins=[
                            {"protein_id": key, "figure_id": "fig-a", "label": "GAPDH"}
                            for key in ("protein-a", "protein-b")
                        ],
                    )
                elif phase == "group-draft":
                    draft = project.intake.grouping
                    if (
                        draft is None
                        or draft.figures[0].lane_count is not None
                        or any(group.selected_source_id is not None for group in draft.groups)
                        or project.rows
                        or project.intake.confirmed_digest
                    ):
                        raise ValueError("Incomplete grouped draft invented executable rows")
                    checks.append("incomplete-group-draft")
                    phase = "group-complete"
                    request(
                        "intake_grouping",
                        grouping={
                            "schema_version": 1,
                            "figures": [{"figure_id": "fig-a", "label": "Fig 1", "lane_count": 8}],
                            "groups": [
                                {
                                    **group.model_dump(mode="json"),
                                    "selected_source_id": group.source_ids[0],
                                }
                                for group in draft.groups
                            ],
                        },
                    )
                elif phase == "group-complete":
                    if {row.row_id for row in project.rows} != {"protein-a", "protein-b"}:
                        raise ValueError("Grouped mapping did not retain stable row identities")
                    checks.append("grouped-stable-mapping")
                    phase = "confirm"
                    request("intake_confirm")
                elif phase == "plan":
                    phase = "assign"
                    by_name = {
                        source.original_name: source.source_id for source in project.intake.sources
                    }
                    request(
                        "intake_assign",
                        bindings=[
                            {"protein_id": key, "source_id": by_name[name]}
                            for key, name in (("protein-a", "a.tif"), ("protein-b", "b.tif"))
                        ],
                    )
                elif phase == "assign":
                    phase = "confirm"
                    request("intake_confirm")
                elif phase == "confirm":
                    if not project.intake.confirmed_digest:
                        raise ValueError("Explicit intake confirmation was not persisted")
                    checks.append("confirmed-stable-intake")
                    phase = "prepare"
                    request("intake_prepare")
                elif phase == "prepare":
                    if not isinstance(project, WBIntakeWorkflowProject):
                        raise ValueError("Execution plan was not saved")
                    phase = "proposal"
                    request("intake_run", workflowDigest=intake_workflow_digest(project))
                elif phase == "proposal":
                    if (
                        not isinstance(project, WBIntakeWorkflowProject)
                        or sum(
                            step.stage == "crop" and step.status == "needs_review"
                            for step in project.workflow.steps
                        )
                        != 2
                    ):
                        raise ValueError("Flat sources must require two explicit crop reviews")
                    phase = "review-a"
                    request(
                        "intake_crop_review",
                        rowId="protein-a",
                        workflowDigest=intake_workflow_digest(project),
                        roi={"x": 12, "y": 10, "width": 120, "height": 40},
                    )
                elif phase == "review-a":
                    if not isinstance(project, WBIntakeWorkflowProject):
                        raise ValueError("Reviewed intake type changed")
                    phase = "review-b"
                    request(
                        "intake_crop_review",
                        rowId="protein-b",
                        workflowDigest=intake_workflow_digest(project),
                        roi={"x": 12, "y": 10, "width": 120, "height": 40},
                    )
                elif phase == "review-b":
                    if not isinstance(project, WBIntakeWorkflowProject):
                        raise ValueError("Reviewed intake type changed")
                    checks.append("fixed-eight-slot-review")
                    phase = "run"
                    request("intake_run", workflowDigest=intake_workflow_digest(project))
                elif phase == "run":
                    if not isinstance(project, WBIntakeOutputProject):
                        raise ValueError("Batch did not produce schema14 output")
                    if not all(step.status == "done" for step in project.workflow.steps):
                        raise ValueError("Batch has incomplete stages")
                    if len(project.analyses) != 2 or len(window.host.project_results) != 2:
                        raise ValueError("Batch did not commit both real worker results")
                    saved_runs = tuple(item.run for item in project.analyses if item.run)
                    if len(saved_runs) != 2 or any(
                        run.state != "succeeded" or not run.pid or run.pid <= 0
                        for run in saved_runs
                    ):
                        raise ValueError("Missing durable worker OS receipts")
                    checks.append("durable-real-workers")
                    if len(project.intake_crops) != 2:
                        raise ValueError("Reviewed original-pixel crop evidence missing")
                    for evidence in project.intake_crops:
                        if (
                            not evidence.raw_crop
                            or not evidence.reviewed
                            or len(evidence.slots) != 8
                        ):
                            raise ValueError("Reviewed fixed-slot raw crop missing")
                        raw_path = (
                            Path(window.host.workspace_path) / evidence.raw_crop.relative_path
                        )
                        with tifffile.TiffFile(raw_path) as image:
                            raw_pixels = image.asarray()
                        value = {"protein-a": 1000, "protein-b": 2000}[evidence.row_id]
                        if (
                            raw_pixels.dtype != np.dtype(np.uint16)
                            or raw_pixels.shape != (40, 120)
                            or not np.all(raw_pixels == value)
                        ):
                            raise ValueError("Raw crop pixels or uint16 depth changed")
                    checks.append("original-pixel-crops")
                    if (
                        any(
                            len(result.result.lanes) != 8
                            or any(len(lane.bands) != 1 for lane in result.result.lanes)
                            for result in window.host.project_results
                        )
                        or not all(
                            band.status == "not_detected" and band.measurement is None
                            for result in window.host.project_results
                            for lane in result.result.lanes
                            for band in lane.bands
                        )
                        or len(cast(list[object], window.bridge.snapshot()["cells"])) != 16
                    ):
                        raise ValueError("Flat input or stable slot result semantics changed")
                    checks.append("missing-is-not-zero")
                    if len(project.intake_outputs) != 1 or not project.intake_outputs[0].complete:
                        raise ValueError("Complete output receipt missing")
                    destination = Path(project.intake_outputs[0].destination)
                    index = json.loads((destination / "index.json").read_bytes())
                    if index["complete"] is not True or index["errors"]:
                        raise ValueError("Output index is incomplete")
                    if not (destination / "measurements.xlsx").is_file():
                        raise ValueError("XLSX output missing")
                    original_zip = (destination / "project.zip").read_bytes()
                    saved_outputs = tuple(item.destination for item in project.intake_outputs)
                    checks.append("complete-output")
                    workspace, epoch = window.host.workspace_path, window.bridge.session_epoch
                    phase = "reopen"
                    window.open_project(workspace)
                elif phase == "reopen":
                    if window.bridge.session_epoch <= epoch:
                        return
                    if (
                        not isinstance(project, WBIntakeOutputProject)
                        or tuple(item.run for item in project.analyses) != saved_runs
                        or project.workflow.approved
                    ):
                        raise ValueError("Saved batch identity/history was not restored safely")
                    checks.append("saved-project-reopen")
                    phase = "repeat"
                    request("intake_export", workflowDigest=intake_workflow_digest(project))
                elif phase == "repeat":
                    if not isinstance(project, WBIntakeOutputProject) or (
                        len(project.intake_outputs) != 2
                        or not project.intake_outputs[-1].complete
                        or project.intake_outputs[-1].destination in saved_outputs
                        or (Path(saved_outputs[0]) / "project.zip").read_bytes() != original_zip
                    ):
                        raise ValueError("Repeated export replaced an old result")
                    checks.append("repeat-export-no-overwrite")
                    if any(
                        sha256(path.read_bytes()).hexdigest() != digest
                        for path, digest in originals.items()
                    ):
                        raise ValueError("Original input was modified")
                    checks.append("originals-unchanged")
                    phase = "home-restore"
                    window.bridge.session("home", "{}")
                elif phase == "archive":
                    if (
                        not isinstance(project, WBIntakeOutputProject)
                        or len(project.imported_runs) != 2
                        or len(window.host.project_results) != 2
                        or next(s for s in project.workflow.steps if s.stage == "export").status
                        != "interrupted"
                    ):
                        raise ValueError(
                            "Archive result evidence was not restored as imported history"
                        )
                    phase = "archive-runs"
                    window.host.submit_storage_job(StorageCommand("runs"), archive_runs.append)
                elif phase == "archive-runs":
                    if not archive_runs:
                        return
                    if archive_runs[0].error_code or archive_runs[0].value != ():
                        raise ValueError("Imported history was mistaken for local process runs")
                    if not isinstance(project, WBIntakeOutputProject):
                        raise ValueError("Imported output project changed")
                    checks.append("archive-imported-history")
                    phase = "archive-export"
                    request("intake_export", workflowDigest=intake_workflow_digest(project))
                elif phase == "archive-export":
                    if (
                        not isinstance(project, WBIntakeOutputProject)
                        or not project.intake_outputs
                        or not project.intake_outputs[-1].complete
                        or next(s for s in project.workflow.steps if s.stage == "export").status
                        != "done"
                        or (Path(saved_outputs[0]) / "project.zip").read_bytes() != original_zip
                    ):
                        raise ValueError("Imported batch failed output-only recovery")
                    checks.append("archive-resume-output")
                    phase = "dom"
                elif phase == "dom":
                    if dom_ready:
                        checks.append("real-dom-webchannel")
                        if grouped:
                            window.activateWindow()
                            window.web.setFocus()
                            dom_ready = False
                            phase = "shortcut-focus"
                        else:
                            phase = "close"
                            window.close()
                    elif not js_pending:
                        js_pending = True
                        window.web.page().runJavaScript(
                            "typeof bridge !== 'undefined' && bridge !== null && "
                            "document.readyState === 'complete'",
                            received,
                        )
                elif phase == "shortcut-focus":
                    if dom_ready:
                        from PySide6.QtCore import Qt
                        from PySide6.QtTest import QTest

                        proxy = window.web.focusProxy()
                        if proxy is None:
                            raise ValueError("WebEngine keyboard focus proxy missing")
                        QTest.keyClick(
                            proxy,
                            Qt.Key.Key_K,
                            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
                        )
                        dom_ready = False
                        phase = "shortcut-open"
                    elif not js_pending:
                        js_pending = True
                        window.web.page().runJavaScript(
                            "(()=>{document.body.tabIndex=-1;document.body.focus();"
                            "return " + SHORTCUT_PROBE_SCRIPT + ";})()",
                            shortcut_observed,
                        )
                elif phase == "shortcut-open":
                    if dom_ready:
                        phase = "shortcut-save"
                        window.web.page().runJavaScript(
                            "(()=>{const f=document.querySelector("
                            "'[data-shortcut-record=\"project.save\"]');"
                            "f.focus();f.dispatchEvent(new KeyboardEvent('keydown',"
                            "{key:'s',code:'KeyS',ctrlKey:true,shiftKey:true,bubbles:true,"
                            "cancelable:true}));document.querySelector("
                            "'[data-shortcut-command=save]').click();return "
                            + SHORTCUT_PROBE_SCRIPT
                            + ";})()",
                            shortcut_observed,
                        )
                    elif not js_pending:
                        js_pending = True
                        window.web.page().runJavaScript(SHORTCUT_PROBE_SCRIPT, shortcut_observed)
                elif phase == "shortcut-save":
                    if window.shortcuts.bindings["project.save"] == "Ctrl+Shift+S":
                        from bioimage_app.shortcuts import WorkbenchShortcuts

                        reloaded = WorkbenchShortcuts(
                            QSettings(str(root / "intake.ini"), QSettings.Format.IniFormat)
                        )
                        if reloaded.bindings != window.shortcuts.bindings or reloaded.error:
                            raise ValueError("Saved shortcut settings did not reload exactly")
                        checks.append("shortcut-settings")
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
        timer.start(25)
        if errors:
            window.close()
        code = app.exec()
        timer.stop()
        if code or not closed or required - set(checks):
            errors.append("Diagnostic did not complete every required check and owned shutdown")
        phase = "failed" if errors else "passed"
        record()
        return 1 if errors else 0
