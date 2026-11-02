"""Command-line adapter for the same production workflow session used by the GUI."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from platform_runtime.api import Workspace, WorkspaceError
from PySide6.QtCore import QCoreApplication
from tool_contracts.api import CoordinateFrame, ImageMetadata, ScientificAsset, ScientificType
from wb_tool.api import load_tiff, read_wb_module_input, wb_validation_input

from bioimage_app.wb_workflow_host import build_wb_workflow, wb_workflow_registry
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus


def run_workflow_cli(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run the original-image WB workflow")
    parser.add_argument("--workspace", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source")
    group.add_argument(
        "--validation",
        choices=("triangle_u8", "triangle_u16", "flat_zero", "invalid_roi", "dtype_limits"),
    )
    group.add_argument("--resume", metavar="EXECUTION_ID")
    parser.add_argument("--parameters")
    args = parser.parse_args(arguments)
    if bool(args.source) != bool(args.parameters):
        parser.error("--source and --parameters must be supplied together")
    plan = None
    workspace = Path(args.workspace).resolve()
    try:
        if not args.resume:
            supplied = (
                read_wb_module_input(args.source, args.parameters)
                if args.source
                else wb_validation_input(args.validation)
            )
            with (
                Workspace.create(workspace) as store,
                TemporaryDirectory(prefix="bioimage-workflow-input-") as temporary,
            ):
                if supplied.source_bytes:
                    input_path = Path(temporary) / "original.tif"
                    input_path.write_bytes(supplied.source_bytes)
                else:
                    input_path = Path(supplied.source_path)
                ref = store.import_asset(input_path, supplied.request.source_sha256)
                image = load_tiff(store.asset_path(ref))
                metadata = ImageMetadata(
                    dtype="uint16" if image.pixels.dtype.itemsize == 2 else "uint8",
                    axes=("y", "x"),
                    shape=image.pixels.shape,
                    acquisition_bit_depth=None,
                    acquisition_range=None,
                    acquisition_range_source=None,
                    frame=CoordinateFrame(
                        frame_id="original_pixels",
                        origin_asset_sha256=ref.sha256,
                        physical_pixel_size_yx=None,
                        physical_unit=None,
                    ),
                )
                source = ScientificAsset(
                    payload=ref,
                    sample_id="sample",
                    producing_method=None,
                    parameters_sha256=None,
                    description=ScientificType(
                        kind="raw_image", unit="pixel_intensity", image=metadata
                    ),
                )
                _, plan = build_wb_workflow(source, supplied.request)
    except (ValueError, OSError, WorkspaceError) as error:
        print(
            json.dumps({"state": "input_failed", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2

    app = QCoreApplication.instance() or QCoreApplication([sys.argv[0]])
    session = WorkflowSession(wb_workflow_registry)
    exit_code = 2
    requested_resume = False

    def changed(status: WorkflowStatus) -> None:
        nonlocal requested_resume
        print(json.dumps({"phase": "progress", **asdict(status)}, ensure_ascii=False), flush=True)
        ledger = session.ledger
        if (
            args.resume
            and not requested_resume
            and ledger is not None
            and ledger.active_attempt is None
            and ledger.state in ("running", "paused", "failed", "interrupted")
        ):
            requested_resume = session.resume()

    def completed(_status: WorkflowStatus) -> None:
        session.close()

    def finished(status: WorkflowStatus) -> None:
        nonlocal exit_code
        outputs: dict[str, str] = {}
        ledger = session.ledger
        if ledger is not None:
            selected = {item.node_id: item for item in ledger.results}
            for result in ledger.plan.outputs:
                if result.node_id in selected:
                    ref = next(
                        item.asset
                        for item in selected[result.node_id].outputs
                        if item.port == result.port
                    )
                    outputs[result.name] = str(workspace / ref.relative_path)
        print(
            json.dumps(
                {
                    "phase": "finished",
                    **asdict(status),
                    "workspace": str(workspace),
                    "quality": (
                        "issues"
                        if any(item.quality == "issues" for item in ledger.results)
                        else "complete"
                    )
                    if ledger and ledger.state == "succeeded"
                    else None,
                    "outputs": outputs,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        exit_code = 0 if status.state == "succeeded" and not status.message else 2
        app.quit()

    session.changed.connect(changed)
    session.completed.connect(completed)
    session.finished.connect(finished)
    if args.resume:
        session.reopen(str(workspace), args.resume)
    else:
        assert plan is not None
        session.start(str(workspace), plan)
    app.exec()
    return exit_code
