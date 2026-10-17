"""Bounded x64 Windows function stacks, never memory dumps or process contents.

Only an owned child tree is eligible, including Windows venv launchers. Contexts are copied while
briefly suspended and resumed before stack walking, which is best effort for a
running thread. DbgHelp calls are serialized in the monitor thread or CLI process.
"""

from __future__ import annotations

import argparse
import ctypes as c
import os
import platform
import struct
import sys
from ctypes import wintypes as w
from threading import Lock

_DBGHELP_LOCK = Lock()


class ProcessEntry(c.Structure):
    _fields_ = [
        ("size", w.DWORD),
        ("usage", w.DWORD),
        ("pid", w.DWORD),
        ("heap", c.c_size_t),
        ("module", w.DWORD),
        ("threads", w.DWORD),
        ("parent", w.DWORD),
        ("priority", w.LONG),
        ("flags", w.DWORD),
        ("executable", w.WCHAR * 260),
    ]


class ThreadEntry(c.Structure):
    _fields_ = [
        ("size", w.DWORD),
        ("usage", w.DWORD),
        ("tid", w.DWORD),
        ("pid", w.DWORD),
        ("base", w.LONG),
        ("delta", w.LONG),
        ("flags", w.DWORD),
    ]


class Symbol(c.Structure):
    _fields_ = [
        ("SizeOfStruct", w.ULONG),
        ("TypeIndex", w.ULONG),
        ("Reserved", c.c_ulonglong * 2),
        ("Index", w.ULONG),
        ("Size", w.ULONG),
        ("ModBase", c.c_ulonglong),
        ("Flags", w.ULONG),
        ("Value", c.c_ulonglong),
        ("Address", c.c_ulonglong),
        ("Register", w.ULONG),
        ("Scope", w.ULONG),
        ("Tag", w.ULONG),
        ("NameLen", w.ULONG),
        ("MaxNameLen", w.ULONG),
        ("Name", c.c_char * 2048),
    ]


def process_entries(kernel: c.CDLL) -> dict[int, tuple[int, str]]:
    if sys.platform != "win32":
        raise ValueError("Native process enumeration requires Windows")
    kernel.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    kernel.Process32FirstW.argtypes = [w.HANDLE, c.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = kernel.Process32FirstW.argtypes
    snap = kernel.CreateToolhelp32Snapshot(2, 0)
    if snap == c.c_void_p(-1).value:
        raise c.WinError(c.get_last_error())
    entry = ProcessEntry()
    entry.size = c.sizeof(entry)
    entries: dict[int, tuple[int, str]] = {}
    try:
        more = kernel.Process32FirstW(snap, c.byref(entry))
        while more:
            entries[entry.pid] = (entry.parent, str(entry.executable).lower())
            more = kernel.Process32NextW(snap, c.byref(entry))
    finally:
        kernel.CloseHandle(snap)
    return entries


def owned_python_processes(pid: int, owner_pid: int) -> list[int]:
    if sys.platform != "win32" or c.sizeof(c.c_void_p) != 8 or platform.machine() != "AMD64":
        raise ValueError("Native capture requires x64 Windows")
    if pid <= 0 or owner_pid <= 0 or pid in (os.getpid(), owner_pid):
        raise ValueError("An owned child process is required")
    entries = process_entries(c.WinDLL("kernel32", use_last_error=True))
    current = os.getpid()
    ancestors = {current}
    for _ in range(8):
        current = entries.get(current, (0, ""))[0]
        if not current or current in ancestors:
            break
        ancestors.add(current)
    if owner_pid not in ancestors or entries.get(pid, (0, ""))[0] != owner_pid:
        raise ValueError("Target is not a child of this monitor or its ancestor")
    selected = [pid]
    for _ in range(4):
        additional = [
            candidate
            for candidate, (parent, image) in entries.items()
            if parent in selected
            and candidate not in selected
            and image in {"python.exe", "pythonw.exe"}
        ]
        selected.extend(additional[: 4 - len(selected)])
        if not additional or len(selected) >= 4:
            break
    return selected


def capture(pid: int, owner_pid: int) -> None:
    selected = owned_python_processes(pid, owner_pid)
    print("NATIVE_OWNED_TREE", selected, flush=True)
    frames = 0
    with _DBGHELP_LOCK:
        for target in selected:
            try:
                frames += _capture_process(target)
            except OSError:
                print("Native process unavailable", target, flush=True)
    if not frames:
        raise ValueError("No native frames were captured")


def capture_fault(root_pid: int, owner_pid: int, pid: int, tid: int) -> None:
    if pid not in owned_python_processes(root_pid, owner_pid):
        raise ValueError("Fault target is outside the owned Python tree")
    with _DBGHELP_LOCK:
        if not _capture_process(pid, priority_tid=tid):
            raise ValueError("No native fault frames were captured")


def _capture_process(pid: int, *, priority_tid: int | None = None) -> int:
    if sys.platform != "win32":
        raise ValueError("Native capture requires Windows")
    kernel = c.WinDLL("kernel32", use_last_error=True)
    debug = c.WinDLL("dbghelp", use_last_error=True)
    psapi = c.WinDLL("psapi", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    process = kernel.OpenProcess(0x410, False, pid)
    if not process:
        raise c.WinError(c.get_last_error())
    debug.SymInitialize.argtypes = [w.HANDLE, c.c_char_p, w.BOOL]
    debug.SymInitialize.restype = w.BOOL
    debug.SymCleanup.argtypes = [w.HANDLE]
    debug.SymSetSearchPath.argtypes = [w.HANDLE, c.c_char_p]
    debug.SymSetOptions.argtypes = [w.DWORD]
    # UNDNAME | DEFERRED_LOADS | FAIL_CRITICAL_ERRORS | IGNORE_NT_SYMPATH | NO_PROMPTS.
    debug.SymSetOptions(0x81206)
    initialized = False
    frames = 0
    try:
        if not debug.SymInitialize(process, b"", True):
            raise c.WinError(c.get_last_error())
        initialized = True
        debug.SymSetSearchPath(process, b"")
        kernel.Thread32First.argtypes = [w.HANDLE, c.POINTER(ThreadEntry)]
        kernel.Thread32Next.argtypes = kernel.Thread32First.argtypes
        snap = kernel.CreateToolhelp32Snapshot(4, 0)
        if snap == c.c_void_p(-1).value:
            raise c.WinError(c.get_last_error())
        thread_entry = ThreadEntry()
        thread_entry.size = c.sizeof(thread_entry)
        tids: list[int] = []
        try:
            more = kernel.Thread32First(snap, c.byref(thread_entry))
            while more and len(tids) < 32:
                if thread_entry.pid == pid:
                    tids.append(thread_entry.tid)
                more = kernel.Thread32Next(snap, c.byref(thread_entry))
        finally:
            kernel.CloseHandle(snap)
        if priority_tid is not None:
            tids = [priority_tid] + [tid for tid in tids if tid != priority_tid][:31]
        kernel.OpenThread.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        kernel.OpenThread.restype = w.HANDLE
        kernel.GetProcessIdOfThread.argtypes = [w.HANDLE]
        kernel.GetProcessIdOfThread.restype = w.DWORD
        kernel.SuspendThread.argtypes = [w.HANDLE]
        kernel.SuspendThread.restype = w.DWORD
        kernel.ResumeThread.argtypes = [w.HANDLE]
        kernel.ResumeThread.restype = w.DWORD
        kernel.GetThreadContext.argtypes = [w.HANDLE, c.c_void_p]
        debug.StackWalk64.argtypes = [w.DWORD, w.HANDLE, w.HANDLE] + [c.c_void_p] * 6
        debug.SymGetModuleBase64.argtypes = [w.HANDLE, c.c_ulonglong]
        debug.SymGetModuleBase64.restype = c.c_ulonglong
        debug.SymFromAddr.argtypes = [w.HANDLE, c.c_ulonglong, c.POINTER(c.c_ulonglong), c.c_void_p]
        psapi.GetModuleFileNameExW.argtypes = [w.HANDLE, w.HANDLE, w.LPWSTR, w.DWORD]
        print("NATIVE_STACKS pid", pid, "threads", len(tids), flush=True)
        for tid in tids:
            # QUERY_INFORMATION | GET_CONTEXT | SUSPEND_RESUME; no context mutation.
            thread = kernel.OpenThread(0x4A, False, tid)
            if not thread:
                continue
            try:
                if kernel.GetProcessIdOfThread(thread) != pid:
                    continue
                # No output, allocation or symbol lookup while the target is suspended.
                raw = c.create_string_buffer(1250)
                address = (c.addressof(raw) + 15) & ~15
                c.c_uint32.from_address(address + 48).value = 0x10000B
                if kernel.SuspendThread(thread) == 0xFFFFFFFF:
                    continue
                try:
                    valid = bool(kernel.GetThreadContext(thread, address))
                finally:
                    if kernel.ResumeThread(thread) == 0xFFFFFFFF:
                        raise c.WinError(c.get_last_error())
                if not valid:
                    continue
                print("THREAD", tid, flush=True)
                frame = c.create_string_buffer(4096)
                for offset, register in ((0, 248), (32, 160), (48, 152)):
                    struct.pack_into(
                        "<Q", frame, offset, c.c_uint64.from_address(address + register).value
                    )
                    struct.pack_into("<I", frame, offset + 12, 3)
                for _ in range(24):
                    pc = struct.unpack_from("<Q", frame, 0)[0]
                    if not pc:
                        break
                    module = debug.SymGetModuleBase64(process, pc)
                    name = c.create_unicode_buffer(1024)
                    psapi.GetModuleFileNameExW(process, module, name, 1024)
                    symbol = Symbol()
                    symbol.SizeOfStruct = 88
                    symbol.MaxNameLen = 2048
                    displacement = c.c_ulonglong()
                    detail = ""
                    if debug.SymFromAddr(process, pc, c.byref(displacement), c.byref(symbol)):
                        detail = (
                            bytes(symbol.Name).decode("ascii", errors="replace")
                            + "+"
                            + hex(displacement.value)
                        )
                    print(name.value.rsplit("\\", 1)[-1], hex(pc - module), detail, flush=True)
                    frames += 1
                    if not debug.StackWalk64(
                        0x8664,
                        process,
                        thread,
                        frame,
                        address,
                        None,
                        c.cast(debug.SymFunctionTableAccess64, c.c_void_p),
                        c.cast(debug.SymGetModuleBase64, c.c_void_p),
                        None,
                    ):
                        break
            finally:
                kernel.CloseHandle(thread)
    finally:
        if initialized:
            debug.SymCleanup(process)
        kernel.CloseHandle(process)
    return frames


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("owner_pid", type=int)
    args = parser.parse_args()
    try:
        capture(args.pid, args.owner_pid)
    except (OSError, ValueError) as error:
        print("Native capture unavailable:", type(error).__name__, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
