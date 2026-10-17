"""Observe only an owned test child; diagnosis never replaces its exit status."""

from __future__ import annotations

import ctypes
import os
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from threading import Event, Thread


def _capture(pid: int) -> None:
    from tooling.windows_native_stacks import capture

    capture(pid, os.getpid())


def run_with_native_watch(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    idle_seconds: float = 60,
    capture: Callable[[int], None] = _capture,
    watch_faults: bool = False,
) -> int:
    """Forward the stream, take one snapshot per idle interval, and preserve the result.

    The collector resumes each thread immediately after copying its CPU context;
    expensive symbol lookup runs afterward. No child timeout or termination is added.
    """
    if idle_seconds <= 0:
        raise ValueError("Idle interval must be positive")
    with subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="backslashreplace",
    ) as child:
        assert child.stdout is not None
        stopped = Event()
        last_output = time.monotonic()

        def observe() -> None:
            captured_at: float | None = None
            while not stopped.wait(min(0.25, idle_seconds / 4)):
                if child.poll() is not None:
                    return
                current_output = last_output
                if time.monotonic() - current_output < idle_seconds:
                    continue
                if captured_at == current_output:
                    continue
                captured_at = current_output
                print("Native snapshot: owned pytest child", child.pid, flush=True)
                try:
                    capture(child.pid)
                except (OSError, ValueError, RuntimeError, ctypes.ArgumentError) as error:
                    # No exception text: diagnostics must not expose arbitrary payloads.
                    print("Native snapshot unavailable:", type(error).__name__, flush=True)

        observer = Thread(target=observe, name="native-test-watch", daemon=True)
        observer.start()
        fault_observer: Thread | None = None
        if watch_faults:
            from tooling.windows_fault_watch import watch_exceptions

            fault_observer = Thread(
                target=watch_exceptions,
                args=(child.pid, os.getpid(), stopped),
                name="native-exception-watch",
                daemon=True,
            )
            fault_observer.start()
        try:
            for line in child.stdout:
                last_output = time.monotonic()
                print(line, end="", flush=True)
            code = child.wait()
            print(f"Observed child exit={code} u32=0x{code & 0xFFFFFFFF:08x}", flush=True)
            return code
        finally:
            stopped.set()
            observer.join(timeout=1)
            if fault_observer is not None:
                fault_observer.join(timeout=1)
