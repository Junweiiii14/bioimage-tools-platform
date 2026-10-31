"""One real comparison attempt; never commits a Workspace or claims publication."""

import sys
from threading import Event, Lock, Thread

from tool_contracts.api import ExecutionEvent

from wb_tool.adapters.module_compare import compare_wb_module
from wb_tool.adapters.module_protocol import (
    WBModuleCancel,
    WBModuleStart,
    encode_module_frame,
    module_frame_json,
)
from wb_tool.adapters.worker import LineReader
from wb_tool.application.analysis import AnalysisCancelled


def _emit(event: ExecutionEvent) -> None:
    sys.stdout.buffer.write(encode_module_frame(event))
    sys.stdout.buffer.flush()


def main() -> int:
    _emit(ExecutionEvent(kind="hello", sequence=0))
    reader = LineReader(sys.stdin.fileno())
    try:
        first = reader.read()
        if first is None:
            raise ValueError("Missing start")
        start = WBModuleStart.model_validate_json(module_frame_json(first))
    except (ValueError, OSError) as exc:
        print("invalid_start:" + type(exc).__name__, file=sys.stderr)
        return 2
    cancelled = Event()
    invalid = Event()
    terminal_lock = Lock()

    def listen() -> None:
        try:
            while (line := reader.read()) is not None:
                control = WBModuleCancel.model_validate_json(module_frame_json(line))
                with terminal_lock:
                    if cancelled.is_set() or control.identity != start.identity:
                        invalid.set()
                        return
                    cancelled.set()
        except (ValueError, OSError):
            with terminal_lock:
                invalid.set()

    def stop_requested() -> bool:
        return cancelled.is_set() or invalid.is_set()

    Thread(target=listen, daemon=True, name="wb-module-cancel").start()
    _emit(ExecutionEvent(kind="accepted", sequence=1, identity=start.identity))
    try:
        manifest = compare_wb_module(start, cancelled=stop_requested)
        response = ExecutionEvent(
            kind="result", sequence=2, identity=start.identity, manifest=manifest
        )
    except AnalysisCancelled:
        response = ExecutionEvent(kind="cancelled", sequence=2, identity=start.identity)
    except (ValueError, OSError, KeyError) as exc:
        print(type(exc).__name__, file=sys.stderr)
        response = ExecutionEvent(
            kind="failure",
            sequence=2,
            identity=start.identity,
            reason="对照输入、冻结请求或产物写入失败：" + type(exc).__name__,
        )
    with terminal_lock:
        if invalid.is_set():
            response = ExecutionEvent(
                kind="failure", sequence=2, identity=start.identity, reason="取消协议或身份无效"
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
                    reason="对照事件超过协议预算",
                )
            )
            return 2
    return 0 if response.kind in ("result", "cancelled") else 2
