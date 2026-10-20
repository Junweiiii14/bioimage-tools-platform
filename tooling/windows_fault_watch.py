"""Observe native exceptions in one verified, live owned Python process."""

from __future__ import annotations

import argparse
import contextlib
import ctypes as c
import io
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from ctypes import wintypes as w
from pathlib import Path
from threading import Event, Thread

from tooling.windows_native_stacks import capture_fault, owned_python_processes, process_entries


class ExceptionRecord(c.Structure):
    _fields_ = [
        ("code", c.c_uint32),
        ("flags", c.c_uint32),
        ("record", c.c_void_p),
        ("address", c.c_void_p),
        ("parameters", c.c_uint32),
        ("information", c.c_uint64 * 15),
    ]


class ExceptionInfo(c.Structure):
    _fields_ = [("record", ExceptionRecord), ("first_chance", c.c_uint32)]


class EventPayload(c.Union):
    # CREATE_PROCESS and LOAD_DLL both put their owned image-file handle first.
    _fields_ = [("exception", ExceptionInfo), ("file", c.c_void_p), ("raw", c.c_byte * 160)]


class DebugEvent(c.Structure):
    _fields_ = [
        ("code", c.c_uint32),
        ("pid", c.c_uint32),
        ("tid", c.c_uint32),
        ("payload", EventPayload),
    ]


def _created(kernel: c.CDLL, handle: int) -> int:
    if sys.platform != "win32":
        raise ValueError("Process identity requires Windows")
    values = [w.FILETIME() for _ in range(4)]
    kernel.GetProcessTimes.argtypes = [w.HANDLE] + [c.POINTER(w.FILETIME)] * 4
    if not kernel.GetProcessTimes(handle, *(c.byref(value) for value in values)):
        raise c.WinError(c.get_last_error())
    return (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime


def _has_python(kernel: c.CDLL, handle: int) -> bool:
    if sys.platform != "win32":
        raise ValueError("Interpreter inspection requires Windows")
    psapi = c.WinDLL("psapi", use_last_error=True)
    modules = (w.HMODULE * 256)()
    needed = w.DWORD()
    psapi.EnumProcessModules.argtypes = [w.HANDLE, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)]
    if not psapi.EnumProcessModules(handle, modules, c.sizeof(modules), c.byref(needed)):
        return False
    psapi.GetModuleBaseNameW.argtypes = [w.HANDLE, w.HMODULE, w.LPWSTR, w.DWORD]
    for module in modules[: min(256, needed.value // c.sizeof(w.HMODULE))]:
        name = c.create_unicode_buffer(256)
        psapi.GetModuleBaseNameW(handle, module, name, 256)
        if name.value.lower() == "python312.dll":
            return True
    return False


def _target(kernel: c.CDLL, root: int, owner: int, stopped: Event) -> tuple[int, list[int]]:
    if sys.platform != "win32":
        raise ValueError("Interpreter selection requires Windows")
    owned_python_processes(root, owner)
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
    kernel.WaitForSingleObject.restype = w.DWORD
    # Keep identity handles open: PID reuse cannot replace these live process objects.
    root_handle = kernel.OpenProcess(0x100410, False, root)
    if not root_handle:
        raise c.WinError(c.get_last_error())
    handles = [root_handle]
    try:
        created = _created(kernel, root_handle)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not stopped.is_set():
            if kernel.WaitForSingleObject(root_handle, 0) != 258:
                raise ValueError("Owned launcher is no longer live")
            if _has_python(kernel, root_handle):
                return root, handles
            entries = process_entries(kernel)
            candidates = [
                pid
                for pid, (parent, image) in entries.items()
                if parent == root and image in {"python.exe", "pythonw.exe"}
            ]
            if len(candidates) > 1:
                raise ValueError("Ambiguous owned interpreter")
            if candidates:
                pid = candidates[0]
                handle = kernel.OpenProcess(0x100410, False, pid)
                if handle:
                    keep = False
                    try:
                        if (
                            kernel.WaitForSingleObject(handle, 0) == 258
                            and _created(kernel, handle) >= created
                            and _has_python(kernel, handle)
                        ):
                            handles.append(handle)
                            keep = True
                            return pid, handles
                    finally:
                        if not keep:
                            kernel.CloseHandle(handle)
            stopped.wait(0.02)
        raise ValueError("Owned interpreter was not ready")
    except BaseException:
        for handle in handles:
            kernel.CloseHandle(handle)
        raise


def watch_exceptions(
    root: int,
    owner: int,
    stopped: Event,
    *,
    ready: Callable[[], None] | None = None,
    capture: Callable[[int, int, int, int], None] = capture_fault,
) -> None:
    if sys.platform != "win32" or c.sizeof(c.c_void_p) != 8:
        raise ValueError("Native exception observation requires x64 Windows")
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.DebugActiveProcess.argtypes = [w.DWORD]
    kernel.DebugActiveProcess.restype = w.BOOL
    kernel.DebugActiveProcessStop.argtypes = [w.DWORD]
    kernel.DebugActiveProcessStop.restype = w.BOOL
    kernel.DebugSetProcessKillOnExit.argtypes = [w.BOOL]
    kernel.DebugSetProcessKillOnExit.restype = w.BOOL
    kernel.WaitForDebugEvent.argtypes = [c.POINTER(DebugEvent), w.DWORD]
    kernel.WaitForDebugEvent.restype = w.BOOL
    kernel.ContinueDebugEvent.argtypes = [w.DWORD, w.DWORD, w.DWORD]
    kernel.ContinueDebugEvent.restype = w.BOOL
    handles: list[int] = []
    attached = False
    pid = 0
    kill_safe = False
    initial_breakpoint = True
    try:
        if c.sizeof(DebugEvent) != 176 or DebugEvent.payload.offset != 16:
            raise ValueError("Unexpected native debug event ABI")
        pid, handles = _target(kernel, root, owner, stopped)
        if not kernel.DebugActiveProcess(pid):
            raise c.WinError(c.get_last_error())
        attached = True
        kill_safe = bool(kernel.DebugSetProcessKillOnExit(False))
        if not kill_safe:
            if kernel.DebugActiveProcessStop(pid):
                attached = False
                raise c.WinError(c.get_last_error())
            print("Native kill policy unavailable; retaining event pump", flush=True)
        captured: set[tuple[int, int]] = set()
        while True:
            event = DebugEvent()
            if not kernel.WaitForDebugEvent(c.byref(event), 200):
                if stopped.is_set():
                    break
                if c.get_last_error() not in (0, 121):
                    raise c.WinError(c.get_last_error())
                continue
            status = 0x00010002  # DBG_CONTINUE for non-exception notifications.
            finished = event.code == 5
            try:
                if event.code in (3, 6) and event.payload.file:
                    kernel.CloseHandle(event.payload.file)
                if event.code == 1:
                    info = event.payload.exception
                    code, chance = int(info.record.code), int(info.first_chance)
                    status = 0x80010001  # DBG_EXCEPTION_NOT_HANDLED preserves dispatch.
                    if initial_breakpoint and code == 0x80000003:
                        initial_breakpoint = False
                        status = 0x00010002
                        if kill_safe:
                            print("NATIVE_EXCEPTION_ATTACHED pid", pid, flush=True)
                        if kill_safe and ready is not None:
                            ready()
                    elif kill_safe and (
                        not chance or code in (0xC0000005, 0x40000015, 0x80000003, 0xC0000409)
                    ):
                        key = (code, chance)
                        if key not in captured and len(captured) < 8:
                            captured.add(key)
                            print(
                                "NATIVE_EXCEPTION",
                                hex(code),
                                "first_chance",
                                chance,
                                "pid",
                                event.pid,
                                "tid",
                                event.tid,
                                "at",
                                hex(info.record.address or 0),
                                flush=True,
                            )
                            try:
                                capture(root, owner, int(event.pid), int(event.tid))
                            except (OSError, ValueError, RuntimeError, c.ArgumentError) as error:
                                print("Native exception capture unavailable:", type(error).__name__)
            finally:
                if not kernel.ContinueDebugEvent(event.pid, event.tid, status):
                    raise c.WinError(c.get_last_error())
            if finished:
                attached = False
                return
    except (OSError, ValueError, RuntimeError, c.ArgumentError) as error:
        print("Native exception observer unavailable:", type(error).__name__, flush=True)
    finally:
        if attached and not kernel.DebugActiveProcessStop(pid):
            print("Native exception detach unavailable", flush=True)
            if not kill_safe:
                # Do not let this debugger thread exit with the OS default kill policy.
                # Drain without collecting until the owned target naturally exits.
                while kernel.WaitForSingleObject(handles[-1], 200) == 258:
                    event = DebugEvent()
                    if kernel.WaitForDebugEvent(c.byref(event), 200):
                        status = 0x00010002
                        if event.code in (3, 6) and event.payload.file:
                            kernel.CloseHandle(event.payload.file)
                        if event.code == 1:
                            status = 0x80010001
                            if (
                                initial_breakpoint
                                and event.payload.exception.record.code == 0x80000003
                            ):
                                initial_breakpoint = False
                                status = 0x00010002
                        kernel.ContinueDebugEvent(event.pid, event.tid, status)
                        if event.code == 5:
                            break
        for handle in handles:
            kernel.CloseHandle(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true", required=True)
    parser.parse_args()
    folder = Path(__file__).resolve().parents[1] / ".local/t043/ci011-controls"
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("zero", "seventeen", "fault", "capture-fails", "attach-fails"):
        work = Path(tempfile.mkdtemp(prefix=name + "-", dir=folder))
        marker = work / "attached"
        code = (
            "import ctypes as c,os,pathlib,time; "
            "c.windll.kernel32.SetErrorMode(3); "
            f"marker=pathlib.Path({str(marker)!r}); "
            "deadline=time.monotonic()+12; "
            "exec('while not marker.exists() and time.monotonic()<deadline: time.sleep(.01)'); "
            "assert marker.exists(); "
        )
        if name in ("fault", "capture-fails"):
            code += (
                "k=c.windll.kernel32; "
                "k.CreateThread.argtypes=[c.c_void_p,c.c_size_t,c.c_void_p,c.c_void_p,"
                "c.c_uint32,c.c_void_p]; k.CreateThread.restype=c.c_void_p; "
                "k.CreateThread(None,0,None,None,0,None); time.sleep(5); raise SystemExit(19)"
            )
        else:
            code += "raise SystemExit(" + ("0" if name == "zero" else "17") + ")"
        output = io.StringIO()
        stopped = Event()

        def ready(marker: Path = marker) -> None:
            marker.touch(exist_ok=False)

        def broken_capture(_root: int, _owner: int, _pid: int, _tid: int) -> None:
            raise ValueError("private-capture-error-text")

        with (
            contextlib.redirect_stdout(output),
            subprocess.Popen(
                [sys.executable, "-I", "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            ) as child,
        ):
            observer = Thread(
                target=watch_exceptions,
                args=(child.pid, child.pid if name == "attach-fails" else os.getpid(), stopped),
                kwargs={
                    "ready": ready,
                    "capture": broken_capture if name == "capture-fails" else capture_fault,
                },
            )
            observer.start()
            if name == "attach-fails":
                observer.join(timeout=3)
                marker.touch(exist_ok=False)
            text, _ = child.communicate(timeout=20)
            stopped.set()
            observer.join(timeout=3)
            result = child.returncode
        observed = output.getvalue()
        print(observed, end="", flush=True)
        print(text, end="", flush=True)
        print("Native control", name, "exit", result, flush=True)
        if observer.is_alive() or "private-capture-error-text" in observed:
            return 1
        expected = (
            0
            if name == "zero"
            else 0xC0000005
            if name == "fault" or name == "capture-fails"
            else 17
        )
        if result != expected:
            return 1
        if name in ("fault", "capture-fails") and "NATIVE_EXCEPTION 0xc0000005" not in observed:
            return 1
        if name != "attach-fails" and "NATIVE_EXCEPTION_ATTACHED" not in observed:
            return 1
    print("Native exception controls passed; original child exits preserved", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
