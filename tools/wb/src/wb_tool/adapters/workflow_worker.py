"""Run one fixed original-value node and emit candidates; never commit a workspace."""

import sys
from threading import Event, Lock, Thread

from tool_contracts.api import ExecutionEvent

from wb_tool.adapters.module_protocol import WBModuleCancel, module_frame_json
from wb_tool.adapters.worker import LineReader
from wb_tool.adapters.workflow_nodes import execute_wb_workflow_node
from wb_tool.adapters.workflow_protocol import WBWorkflowStart, encode_wb_workflow_frame
from wb_tool.application.analysis import AnalysisCancelled


def _emit(event: ExecutionEvent) -> None:
    sys.stdout.buffer.write(encode_wb_workflow_frame(event))
    sys.stdout.buffer.flush()


def main() -> int:
    _emit(ExecutionEvent(kind="hello", sequence=0))
    reader = LineReader(sys.stdin.fileno())
    try:
        first = reader.read()
        if first is None:
            raise ValueError("Missing workflow start")
        start = WBWorkflowStart.model_validate_json(module_frame_json(first))
    except (ValueError, OSError) as error:
        print("invalid_workflow_start:" + type(error).__name__, file=sys.stderr)
        return 2
    cancelled, invalid = Event(), Event()
    terminal = Lock()

    def listen() -> None:
        try:
            while (line := reader.read()) is not None:
                control = WBModuleCancel.model_validate_json(module_frame_json(line))
                with terminal:
                    if cancelled.is_set() or control.identity != start.identity:
                        invalid.set()
                        return
                    cancelled.set()
        except (ValueError, OSError):
            with terminal:
                invalid.set()

    Thread(target=listen, daemon=True, name="wb-workflow-cancel").start()
    _emit(ExecutionEvent(kind="accepted", sequence=1, identity=start.identity))
    try:
        manifest = execute_wb_workflow_node(
            start, cancelled=lambda: cancelled.is_set() or invalid.is_set()
        )
        response = ExecutionEvent(
            kind="result", sequence=2, identity=start.identity, manifest=manifest
        )
    except AnalysisCancelled:
        response = ExecutionEvent(kind="cancelled", sequence=2, identity=start.identity)
    except (ValueError, OSError, KeyError) as error:
        print(type(error).__name__, file=sys.stderr)
        response = ExecutionEvent(
            kind="failure",
            sequence=2,
            identity=start.identity,
            reason="Original-value node failed: " + type(error).__name__,
        )
    with terminal:
        if invalid.is_set():
            response = ExecutionEvent(
                kind="failure",
                sequence=2,
                identity=start.identity,
                reason="Invalid workflow cancellation protocol",
            )
        elif cancelled.is_set():
            response = ExecutionEvent(kind="cancelled", sequence=2, identity=start.identity)
        try:
            _emit(response)
        except ValueError:
            _emit(
                ExecutionEvent(
                    kind="failure",
                    sequence=2,
                    identity=start.identity,
                    reason="Workflow candidate exceeds protocol budget",
                )
            )
            return 2
    return 0 if response.kind in ("result", "cancelled") else 2
