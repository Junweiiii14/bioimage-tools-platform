"""Owned process trees; never use a PID recovered from a workspace to terminate processes."""

from __future__ import annotations

import ctypes
import os
import signal
from contextlib import suppress
from ctypes import wintypes


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("ProcessTime", ctypes.c_int64),
        ("JobTime", ctypes.c_int64),
        ("Flags", wintypes.DWORD),
        ("MinWorkingSet", ctypes.c_size_t),
        ("MaxWorkingSet", ctypes.c_size_t),
        ("ActiveLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("Priority", wintypes.DWORD),
        ("Scheduling", wintypes.DWORD),
    ]


class _IOCounters(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_uint64)
        for name in (
            "ReadOperations",
            "WriteOperations",
            "OtherOperations",
            "ReadBytes",
            "WriteBytes",
            "OtherBytes",
        )
    ]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("Basic", _BasicLimits),
        ("IO", _IOCounters),
        ("ProcessMemory", ctypes.c_size_t),
        ("JobMemory", ctypes.c_size_t),
        ("PeakProcessMemory", ctypes.c_size_t),
        ("PeakJobMemory", ctypes.c_size_t),
    ]


class _Accounting(ctypes.Structure):
    _fields_ = [
        ("UserTime", ctypes.c_int64),
        ("KernelTime", ctypes.c_int64),
        ("PeriodUserTime", ctypes.c_int64),
        ("PeriodKernelTime", ctypes.c_int64),
        ("PageFaults", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TerminatedProcesses", wintypes.DWORD),
    ]


class OwnedProcessTree:
    """Attach immediately after QProcess.started, before allowing a worker request.

    Registered workers must wait for that request before spawning children. Windows job
    inheritance then contains descendants and KILL_ON_JOB_CLOSE also protects host crashes.
    POSIX workers start in a new session, retaining the owned process group.
    """

    def __init__(self, pid: int) -> None:
        if pid <= 0:
            raise ValueError("Expected a newly observed positive PID")
        self.pid = pid
        self._job: int | None = None
        if os.name != "nt":
            return
        self._kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self._kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self._kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel.OpenProcess.restype = wintypes.HANDLE
        self._kernel.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        self._kernel.SetInformationJobObject.restype = wintypes.BOOL
        self._kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self._kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        self._kernel.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]
        self._kernel.QueryInformationJobObject.restype = wintypes.BOOL
        self._kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self._kernel.TerminateJobObject.restype = wintypes.BOOL
        self._kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel.CloseHandle.restype = wintypes.BOOL
        job = self._kernel.CreateJobObjectW(None, None)
        if not job:
            raise ctypes.WinError(ctypes.get_last_error())
        self._job = job
        try:
            limits = _ExtendedLimits()
            limits.Basic.Flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not self._kernel.SetInformationJobObject(
                job, 9, ctypes.byref(limits), ctypes.sizeof(limits)
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            process = self._kernel.OpenProcess(0x0101, False, pid)  # SET_QUOTA | TERMINATE
            if not process:
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                if not self._kernel.AssignProcessToJobObject(job, process):
                    raise ctypes.WinError(ctypes.get_last_error())
            finally:
                self._kernel.CloseHandle(process)
        except OSError:
            self.close()
            raise

    def terminate(self) -> None:
        if os.name == "nt":
            if self._job is not None and not self._kernel.TerminateJobObject(self._job, 1):
                raise ctypes.WinError(ctypes.get_last_error())
        else:
            with suppress(ProcessLookupError):
                os.killpg(self.pid, signal.SIGKILL)

    def empty(self) -> bool:
        if os.name == "nt":
            if self._job is None:
                return True
            accounting = _Accounting()
            if not self._kernel.QueryInformationJobObject(
                self._job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            return accounting.ActiveProcesses == 0
        try:
            os.killpg(self.pid, 0)
        except ProcessLookupError:
            return True
        return False

    def close(self) -> None:
        if os.name == "nt" and self._job is not None:
            self._kernel.CloseHandle(self._job)
            self._job = None
