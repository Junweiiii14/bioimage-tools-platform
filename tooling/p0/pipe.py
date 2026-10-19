"""Read control pipes without holding a Windows CRT descriptor lock during DLL load."""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes


def read_control() -> bytes:
    if sys.platform != "win32":
        return os.read(sys.stdin.fileno(), 65536)
    import msvcrt

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.ReadFile.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    kernel.ReadFile.restype = wintypes.BOOL
    buffer = ctypes.create_string_buffer(65536)
    read = wintypes.DWORD()
    handle = msvcrt.get_osfhandle(sys.stdin.fileno())
    if not kernel.ReadFile(handle, buffer, len(buffer), ctypes.byref(read), None):
        error = ctypes.get_last_error()
        if error in {109, 232}:  # broken pipe / no data
            return b""
        raise ctypes.WinError(error)
    return buffer.raw[: read.value]
