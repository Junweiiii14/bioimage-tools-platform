"""Local per-session Qt/Python crash evidence. Never loaded by static worker routes."""

import faulthandler
import json
import re
import sys
import threading
import traceback
from contextlib import suppress
from datetime import UTC, datetime
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from types import TracebackType
from uuid import uuid4

from PySide6.QtCore import (
    QMessageLogContext,
    QtMsgType,
    qFormatLogMessage,
    qInstallMessageHandler,
    qWarning,
)


class WebBoundaryDiagnostics:
    """Bounded, payload-free events routed through the existing desktop Qt sink."""

    def __init__(self) -> None:
        self._failed: set[str] = set()
        self._version = version("bioimage-app")

    def recovered(self, action: str) -> None:
        self._failed.discard(action)

    def report(
        self,
        action: str,
        exception: str,
        stack: list[str],
        *,
        project: str,
        epoch: int,
        revision: int,
        request: str = "",
        operation: str = "",
        phase: str = "render",
    ) -> bool:
        if action in self._failed:
            return False
        self._failed.add(action)
        # IDs are correlation tokens, never user names, payloads or filesystem paths.
        record = {
            "contract": "web-boundary@1",
            "version": self._version,
            "action": action,
            "phase": phase,
            "project": sha256(project.encode()).hexdigest()[:16],
            "session": epoch,
            "revision": revision,
            "request": sha256(request.encode()).hexdigest()[:16] if request else "",
            "operation": operation if re.fullmatch(r"[a-z_]{1,48}", operation) else "",
            "exception": exception,
            "stack": stack[:8],
        }
        # A failed log sink must not suppress the actionable UI notice/recovery.
        with suppress(Exception):
            qWarning("web-boundary " + json.dumps(record, ensure_ascii=True))
        return True

    def python_failure(
        self, action: str, error: Exception, *, project: str, epoch: int, revision: int
    ) -> bool:
        frames = traceback.extract_tb(error.__traceback__)[-8:]
        return self.report(
            action,
            type(error).__name__,
            [f"{Path(f.filename).name}:{f.lineno}:{f.name}" for f in frames],
            project=project,
            epoch=epoch,
            revision=revision,
        )


class DesktopDiagnostics:
    """Keep the fatal-error file descriptor alive until the desktop event loop has ended."""

    def __init__(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / ("session-" + uuid4().hex + ".log")
        self._file = self.path.open("x", encoding="utf-8")
        self._lock = threading.RLock()
        self._written = 0
        self._closed = False
        self._write("session", f"Python {sys.version.split()[0]}")
        self._previous_exception = sys.excepthook
        self._previous_qt = qInstallMessageHandler(self._qt_message)
        self._owns_fatal_handler = not faulthandler.is_enabled()
        if self._owns_fatal_handler:
            faulthandler.enable(self._file, all_threads=True)
        sys.excepthook = self._exception

    def _write(self, kind: str, message: str, *, fatal: bool = False) -> None:
        with self._lock:
            if self._closed or self._written >= 1024 * 1024 and not fatal:
                return
            record = (
                json.dumps(
                    {
                        "time": datetime.now(UTC).isoformat(),
                        "thread": threading.get_native_id(),
                        "kind": kind,
                        "message": message[:8192],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            try:
                self._file.write(record)
                self._file.flush()
                self._written += len(record.encode("utf-8"))
            except OSError:
                # Diagnostic I/O must never replace the original Qt/Python error.
                pass

    def _qt_message(self, level: QtMsgType, context: QMessageLogContext, message: str) -> None:
        self._write(level.name, message, fatal=level == QtMsgType.QtFatalMsg)
        if level == QtMsgType.QtFatalMsg:
            with self._lock:
                if not self._closed:
                    # Qt can terminate through fast-fail instead of a Python fatal signal.
                    with suppress(OSError):
                        faulthandler.dump_traceback(file=self._file, all_threads=True)
        if self._previous_qt is not None:
            self._previous_qt(level, context, message)
        elif sys.stderr is not None:
            try:
                sys.stderr.write(qFormatLogMessage(level, context, message) + "\n")
                sys.stderr.flush()
            except (OSError, ValueError):
                pass

    def _exception(
        self,
        exception_type: type[BaseException],
        exception: BaseException,
        tb: TracebackType | None,
    ) -> None:
        self._write(
            "uncaught_exception", "".join(traceback.format_exception(exception_type, exception, tb))
        )
        self._previous_exception(exception_type, exception, tb)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            sys.excepthook = self._previous_exception
            qInstallMessageHandler(self._previous_qt)
            if self._owns_fatal_handler:
                faulthandler.disable()
            self._write("session_end", "desktop event loop returned")
            self._closed = True
            self._file.close()
