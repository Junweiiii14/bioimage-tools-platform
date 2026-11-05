"""Minimal research CLI; uses the existing asynchronous workflow lifecycle."""

import argparse
import json
import signal
import sys
from dataclasses import asdict
from pathlib import Path

from nuclei_tool.api import read_nuclei_input
from platform_runtime.api import Workspace, WorkspaceError
from PySide6.QtCore import QCoreApplication, QTimer
from tool_contracts.api import (
    CoordinateFrame,
    ExecutionPlan,
    ImageMetadata,
    ScientificAsset,
    ScientificType,
)

from bioimage_app.nuclei_workflow_host import NucleiHost
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus


def prepare(workspace: Path, source_path: str, host: NucleiHost) -> ExecutionPlan:
    supplied = read_nuclei_input(source_path)
    with Workspace.create(workspace) as store:
        ref = store.import_asset(Path(source_path), supplied.sha256)
        copied = read_nuclei_input(str(store.asset_path(ref)))
        source = ScientificAsset(
            payload=ref,
            sample_id="sample",
            producing_method=None,
            parameters_sha256=None,
            description=ScientificType(
                kind="raw_image",
                unit="pixel_intensity",
                image=ImageMetadata(
                    dtype="uint8",
                    axes=("y", "x"),
                    shape=copied.pixels.shape,
                    acquisition_bit_depth=None,
                    acquisition_range=None,
                    acquisition_range_source=None,
                    frame=CoordinateFrame(
                        frame_id="original_pixels",
                        origin_asset_sha256=ref.sha256,
                        physical_pixel_size_yx=None,
                        physical_unit=None,
                    ),
                ),
            ),
        )
        return host.build(source)


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fixed StarDist research; no scientific admission")
    parser.add_argument(
        "--workspace", required=True, help="New workspace; existing results rejected"
    )
    parser.add_argument(
        "--source", required=True, help="2D uint8 grayscale TIFF, original orientation"
    )
    parser.add_argument("--worker-python", required=True, help="Explicit isolated research Python")
    parser.add_argument(
        "--model-directory", required=True, help="Prepared fixed P014 model; no download"
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="1..3600 second deadline after input admission; cancels owned workflow",
    )
    args = parser.parse_args(arguments)
    if not 1 <= args.timeout_seconds <= 3600:
        parser.error("timeout must be 1..3600 seconds")
    workspace = Path(args.workspace).resolve()
    try:
        host = NucleiHost(args.worker_python, args.model_directory)
        plan = prepare(workspace, str(Path(args.source).absolute()), host)
    except (ValueError, OSError, WorkspaceError) as error:
        print(json.dumps({"state": "input_failed", "error": str(error)}), file=sys.stderr)
        return 2
    app = QCoreApplication.instance() or QCoreApplication([sys.argv[0]])
    session = WorkflowSession(host.registry)
    exit_code = 2
    stop_reason = ""

    def cancel(reason: str) -> None:
        nonlocal stop_reason
        if not stop_reason:
            stop_reason = reason
            session.cancel()

    def changed(status: WorkflowStatus) -> None:
        print(json.dumps({"phase": "progress", **asdict(status)}), flush=True)

    def finished(status: WorkflowStatus) -> None:
        nonlocal exit_code
        outputs: dict[str, str] = {}
        ledger = session.ledger
        if ledger is not None and ledger.state == "succeeded":
            for result in ledger.results:
                for item in result.outputs:
                    outputs[item.port] = str(workspace / item.asset.relative_path)
        print(
            json.dumps(
                {
                    "phase": "finished",
                    **asdict(status),
                    "outputs": outputs,
                    "stop_reason": stop_reason,
                    "failure_reason": (
                        ledger.reason
                        or next(
                            (
                                attempt.run.reason
                                for attempt in reversed(ledger.attempts)
                                if attempt.run is not None and attempt.run.reason
                            ),
                            "",
                        )
                    )
                    if ledger is not None
                    else status.message,
                    "workspace": str(workspace),
                    "readiness": "research_not_scientifically_admitted",
                }
            ),
            flush=True,
        )
        exit_code = 0 if status.state == "succeeded" and not status.message else 2
        app.quit()

    def completed(_status: WorkflowStatus) -> None:
        session.close()

    session.changed.connect(changed)
    session.completed.connect(completed)
    session.finished.connect(finished)
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(lambda: cancel("deadline"))
    # A periodic Qt callback allows Python's Ctrl+C handler to run during app.exec.
    heartbeat = QTimer()
    heartbeat.timeout.connect(lambda: None)
    previous = signal.signal(signal.SIGINT, lambda _signum, _frame: cancel("user_interrupt"))
    try:
        session.start(str(workspace), plan)
        deadline.start(args.timeout_seconds * 1000)
        heartbeat.start(100)
        app.exec()
    finally:
        deadline.stop()
        heartbeat.stop()
        signal.signal(signal.SIGINT, previous)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
