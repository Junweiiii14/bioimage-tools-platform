"""One task per process, control thread stays responsive during numerical work."""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

from tooling.p0.metrics import peak_memory
from tooling.p0.pipe import read_control
from tooling.p0.protocol import Decoder, Frame, Sequence, encode


def main() -> int:
    decoder = Decoder()
    try:
        initial: list[Frame] = []
        while not initial:
            chunk = read_control()
            if not chunk:
                raise ValueError("No initial frame")
            initial.extend(decoder.feed(chunk))
        if len(initial) != 1:
            raise ValueError("Expected one initial request")
        request = initial[0]
        if request.kind != "run" or not request.paths:
            raise ValueError("Expected run with paths")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    cancelled = threading.Event()
    output_lock = threading.Lock()
    seq = 0
    incoming = Sequence(request.run_id)
    incoming.accept(request)

    def send(kind: str, **data: object) -> None:
        nonlocal seq
        with output_lock:
            frame = Frame.model_validate(
                {"run_id": request.run_id, "seq": seq, "kind": kind, **data}
            )
            seq += 1
            sys.stdout.buffer.write(encode(frame))
            sys.stdout.buffer.flush()

    def controls() -> None:
        while True:
            control = read_control()
            if not control:
                cancelled.set()
                return
            try:
                for frame in decoder.feed(control):
                    if incoming.accept(frame) and frame.kind == "cancel":
                        cancelled.set()
                        send("ack")
            except ValueError:
                cancelled.set()
                return

    send(
        "hello",
        detail=f"pid={os.getpid()};qt_imported={any(n.startswith('PySide6') for n in sys.modules)}",
    )
    threading.Thread(target=controls, daemon=True).start()
    if request.mode == "crash":
        os._exit(23)
    if request.mode == "stubborn":
        while True:
            time.sleep(1)
    timings: list[float] = []
    checksums: list[str] = []
    last_progress = 0.0
    try:
        import numpy as np

        from tooling.p0.imaging import digest, load
        from tooling.p0.numerics import smooth

        for path in request.paths:
            if cancelled.is_set():
                break
            started = time.perf_counter()
            raw = load(Path(path))
            before = digest(raw)
            plane = raw if raw.ndim == 2 else raw[:, :, 0]
            work = np.asarray(plane, dtype=np.float32)
            scratch = np.empty_like(work)
            for _ in range(request.passes):
                if cancelled.is_set():
                    break
                smooth(work, scratch)
                work, scratch = scratch, work
            if digest(raw) != before:
                raise RuntimeError("Raw array was mutated")
            del work, scratch, plane, raw
            if cancelled.is_set():
                break
            timings.append(time.perf_counter() - started)
            checksums.append(before)
            if time.perf_counter() - last_progress >= 0.1:
                send("progress", completed=len(timings), peak_bytes=peak_memory())
                last_progress = time.perf_counter()
        send(
            "cancelled" if cancelled.is_set() else "result",
            seconds=timings,
            checksums=checksums,
            completed=len(timings),
            peak_bytes=peak_memory(),
        )
        return 0
    except (OSError, ValueError, RuntimeError, MemoryError) as exc:
        send("error", detail=f"{type(exc).__name__}: {exc}", peak_bytes=peak_memory())
        return 1
