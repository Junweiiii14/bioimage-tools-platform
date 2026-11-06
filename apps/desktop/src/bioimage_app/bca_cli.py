"""Minimal research CLI; uses the existing asynchronous workflow lifecycle."""

import argparse
import csv
import hashlib
import json
import signal
import sys
from dataclasses import asdict
from pathlib import Path

from bca_tool.api import read_plate
from platform_runtime.api import Workspace, WorkspaceError
from PySide6.QtCore import QCoreApplication, QTimer
from tool_contracts.api import ExecutionPlan, ScientificAsset, ScientificType

from bioimage_app.bca_workflow_host import BcaHost
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus


def prepare(workspace: Path, source_path: str, record_path: str, host: BcaHost) -> ExecutionPlan:
    supplied = read_plate(source_path, record_path)
    with Workspace.create(workspace) as store:
        source = store.import_asset(
            Path(source_path), hashlib.sha256(supplied.csv_bytes).hexdigest()
        )
        record = store.import_asset(
            Path(record_path), hashlib.sha256(supplied.record_bytes).hexdigest()
        )
        identity = supplied.wells[0].plate_id
        return host.build(
            ScientificAsset(
                payload=source,
                sample_id=identity,
                producing_method=None,
                parameters_sha256=None,
                description=ScientificType(kind="analysis_result", unit="A562"),
            ),
            ScientificAsset(
                payload=record,
                sample_id=identity,
                producing_method=None,
                parameters_sha256=None,
                description=ScientificType(kind="run_manifest", unit=None),
            ),
        )


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fixed Pierce25 BCA research; no scientific admission"
    )
    parser.add_argument(
        "--workspace", required=True, help="New workspace, or existing workspace with --reopen"
    )
    parser.add_argument("--source", help="UTF-8 single-plate long CSV")
    parser.add_argument("--record", help="Explicit plate record JSON")
    parser.add_argument("--reopen", help="Verify saved execution ID without recomputation")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args(arguments)
    if not 1 <= args.timeout_seconds <= 3600:
        parser.error("timeout must be 1..3600 seconds")
    if bool(args.reopen) == bool(args.source or args.record) or (
        not args.reopen and not (args.source and args.record)
    ):
        parser.error("use --source and --record, or --reopen execution_id")
    workspace = Path(args.workspace).resolve()
    host = BcaHost()
    try:
        plan = None if args.reopen else prepare(workspace, args.source, args.record, host)
    except (ValueError, OSError, csv.Error, WorkspaceError) as error:
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
        if args.reopen:
            session.reopen(str(workspace), args.reopen)
        else:
            assert plan is not None
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
