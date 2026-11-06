"""Installed isolated worker entry; protocol hello precedes numerical imports."""

import os
import sys
from contextlib import redirect_stdout
from threading import Event, Lock, Thread

from tool_contracts.api import ExecutionEvent

from bca_tool.adapters.protocol import (
    MAX_FRAME,
    BcaCancel,
    BcaStart,
    encode_frame,
    frame_json,
)


class LineReader:
    def __init__(self, descriptor: int) -> None:
        self.descriptor = descriptor
        self.buffer = bytearray()
        self.stopped = Event()
        # Python 3.12 supports nonblocking pipes on Windows. A blocking CRT read
        # in the listener can deadlock concurrent native-module initialization.
        os.set_blocking(descriptor, False)

    def read(self) -> bytes | None:
        while b"\n" not in self.buffer:
            if self.stopped.is_set():
                return None
            if len(self.buffer) > MAX_FRAME:
                raise ValueError("Protocol frame exceeds budget")
            try:
                chunk = os.read(self.descriptor, 4096)
            except BlockingIOError:
                self.stopped.wait(0.02)
                continue
            if not chunk:
                if self.buffer:
                    raise ValueError("Incomplete protocol frame")
                return None
            self.buffer.extend(chunk)
        line, _, rest = self.buffer.partition(b"\n")
        self.buffer = bytearray(rest)
        if len(line) > MAX_FRAME:
            raise ValueError("Protocol frame exceeds budget")
        return bytes(line)


def _emit(event: ExecutionEvent) -> None:
    sys.stdout.buffer.write(encode_frame(event))
    sys.stdout.buffer.flush()


def main() -> int:
    _emit(ExecutionEvent(kind="hello", sequence=0))
    reader = LineReader(sys.stdin.fileno())
    try:
        first = reader.read()
        if first is None:
            raise ValueError("Missing start")
        start = BcaStart.model_validate_json(frame_json(first))
    except (ValueError, OSError) as error:
        print(f"invalid_start: {error}", file=sys.stderr)
        return 2
    cancelled, invalid = Event(), Event()
    terminal = Lock()

    def listen() -> None:
        try:
            while (line := reader.read()) is not None:
                control = BcaCancel.model_validate_json(frame_json(line))
                with terminal:
                    if cancelled.is_set() or control.identity != start.identity:
                        invalid.set()
                        return
                    cancelled.set()
        except (ValueError, OSError):
            with terminal:
                invalid.set()

    def stop_requested() -> bool:
        return cancelled.is_set() or invalid.is_set()

    listener = Thread(target=listen, daemon=True, name="bca-cancel")
    listener.start()
    _emit(ExecutionEvent(kind="accepted", sequence=1, identity=start.identity))
    # All third-party diagnostics are stderr; stdout remains the bounded protocol.
    from bca_tool.adapters.execute import BcaCancelled

    try:
        with redirect_stdout(sys.stderr):
            from bca_tool.adapters.execute import execute

            manifest = execute(start, stop_requested)
        response = ExecutionEvent(
            kind="result", sequence=2, identity=start.identity, manifest=manifest
        )
    except BcaCancelled:
        response = ExecutionEvent(kind="cancelled", sequence=2, identity=start.identity)
    except Exception as error:
        # Boundary converts any model/runtime error to failure, never a zero count.
        reason = f"{type(error).__name__}: {error}"[:1024]
        print(reason, file=sys.stderr)
        response = ExecutionEvent(
            kind="failure", sequence=2, identity=start.identity, reason=reason
        )
    with terminal:
        if invalid.is_set():
            response = ExecutionEvent(
                kind="failure",
                sequence=2,
                identity=start.identity,
                reason="Invalid cancel protocol",
            )
        elif cancelled.is_set():
            response = ExecutionEvent(kind="cancelled", sequence=2, identity=start.identity)
        _emit(response)
    reader.stopped.set()
    listener.join(timeout=1)
    return 0 if response.kind in ("result", "cancelled") else 2


if __name__ == "__main__":
    raise SystemExit(main())
