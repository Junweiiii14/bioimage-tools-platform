"""FIFO storage port: SQLite and file I/O belong exclusively to its worker thread."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from sqlite3 import Error as SQLiteError
from tempfile import TemporaryDirectory
from threading import Event, get_native_id
from time import monotonic_ns
from typing import Literal
from uuid import uuid4

from platform_runtime.api import Workspace, WorkspaceError
from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from tool_contracts.api import (
    AssetRef,
    DraftSnapshot,
    ExecutionRequest,
    ProcessExitReceipt,
    RecoveryReport,
    RunRecord,
)

from bioimage_app.module_results import commit_module_result

_LOGGER = logging.getLogger(__name__)


def _trace(phase: str, request_id: str, operation: str = "", outcome: str = "") -> None:
    if _LOGGER.isEnabledFor(logging.DEBUG):
        _LOGGER.debug(
            "storage phase=%s request=%s operation=%s outcome=%s monotonic_ns=%d native_thread=%d",
            phase,
            request_id,
            operation,
            outcome,
            monotonic_ns(),
            get_native_id(),
        )


Operation = Literal[
    "create",
    "open",
    "import",
    "import_bytes",
    "save",
    "load",
    "prepare",
    "start",
    "cancel",
    "commit",
    "cancelled",
    "failed",
    "asset",
    "read",
    "documents",
    "runs",
    "run",
    "backup",
    "close",
]
Value = (
    AssetRef
    | DraftSnapshot
    | RunRecord
    | RecoveryReport
    | tuple[DraftSnapshot, ...]
    | tuple[RunRecord, ...]
    | str
    | None
)


@dataclass(frozen=True)
class StorageCommand:
    """Explicit operations only; no callable, module name or database handle crosses threads."""

    operation: Operation
    path: str = ""
    source_sha256: str = ""
    document_id: str = ""
    tool_id: str = ""
    revision: int | None = None
    previous_revision: int | None = None
    run_id: str = ""
    pid: int = 0
    data: bytes = b""
    asset: AssetRef | None = None
    receipt: ProcessExitReceipt | None = None
    reason: str = ""
    interrupted: bool = False
    cancellation: Event | None = None
    module_request: ExecutionRequest | None = None


@dataclass(frozen=True)
class StorageReply:
    request_id: str
    value: Value = None
    data: bytes = b""
    error_code: str | None = None
    message: str = ""


class _StorageWorker(QObject):
    replied = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._owner_thread = self.thread()
        self._workspace: Workspace | None = None

    @Slot()
    def retire(self) -> None:
        worker_thread = self.thread()
        self.moveToThread(self._owner_thread)
        worker_thread.quit()

    @Slot(str, object)
    def execute(self, request_id: str, command: StorageCommand) -> None:
        _trace("execute-start", request_id, command.operation)
        try:
            value, data = self._execute(command)
            reply = StorageReply(request_id, value, data)
        except (WorkspaceError, OSError, SQLiteError, ValueError, TypeError) as error:
            reply = StorageReply(request_id, error_code=type(error).__name__, message=str(error))
        _trace("execute-end", request_id, command.operation, "error" if reply.error_code else "ok")
        _trace("reply-emit", request_id, command.operation)
        self.replied.emit(reply)

    def _execute(self, command: StorageCommand) -> tuple[Value, bytes]:
        op = command.operation
        if op in ("create", "open"):
            if self._workspace is not None:
                raise ValueError("Close the current workspace before switching")
            self._workspace = (
                Workspace.create(command.path) if op == "create" else Workspace.open(command.path)
            )
            return self._workspace.recovery, b""
        if op == "close":
            if self._workspace is not None:
                self._workspace.close()
                self._workspace = None
            return None, b""
        store = self._workspace
        if store is None:
            raise ValueError("No workspace is open")
        if op == "import":
            return store.import_asset(command.path, command.source_sha256), b""
        if op == "import_bytes":
            name = Path(command.path)
            if name.name != command.path or not name.suffix or not name.suffix[1:].isalnum():
                raise ValueError("Generated asset requires a simple filename with an extension")
            if not command.data or sha256(command.data).hexdigest() != command.source_sha256:
                raise ValueError("Generated asset bytes do not match the expected digest")
            # Only the owned temporary directory is cleaned up; no caller path is used as a target.
            with TemporaryDirectory(prefix="bioimage-asset-") as temporary:
                source = Path(temporary).resolve() / ("asset" + name.suffix)
                source.write_bytes(command.data)
                return store.import_asset(source, command.source_sha256), b""
        if op == "save":
            if command.revision is None:
                raise ValueError("Save requires a revision")
            return store.save_draft(
                command.document_id,
                command.tool_id,
                command.revision,
                command.data,
                expected_previous_revision=command.previous_revision,
            ), b""
        if op == "load":
            draft = store.load_draft(command.document_id, command.revision)
            return draft, store.read_asset(draft.asset)
        if op == "prepare":
            run = store.prepare_run(command.document_id, command.revision)
            return run, store.read_asset(run.request)
        if op == "start":
            return store.start_run(command.run_id, command.pid), b""
        if op == "cancel":
            run = store.get_run(command.run_id)
            return (run if run.state == "cancelling" else store.request_cancel(command.run_id)), b""
        if op in ("commit", "cancelled", "failed"):
            if command.receipt is None:
                raise ValueError("Terminal operation requires an observed process exit")
            if op == "commit":
                if command.module_request is not None:
                    return commit_module_result(
                        store,
                        command.run_id,
                        command.receipt,
                        command.data,
                        command.module_request,
                        command.path,
                        command.cancellation,
                    ), b""
                return store.commit_result(
                    command.run_id,
                    command.receipt,
                    command.data,
                    cancelled=command.cancellation.is_set
                    if command.cancellation is not None
                    else None,
                ), b""
            if op == "cancelled":
                return store.finish_cancelled(command.run_id, command.receipt), b""
            return store.finish_failure(
                command.run_id,
                command.receipt,
                reason=command.reason,
                interrupted=command.interrupted,
            ), b""
        if op == "asset":
            if command.asset is None:
                raise ValueError("Asset operation requires a reference")
            return str(store.asset_path(command.asset)), b""
        if op == "read":
            if command.asset is None:
                raise ValueError("Read requires a registered asset reference")
            return command.asset, store.read_asset(command.asset)
        if op == "documents":
            return store.list_documents(), b""
        if op == "runs":
            return store.list_runs(command.document_id or None), b""
        if op == "run":
            return store.get_run(command.run_id), b""
        if op == "backup":
            return str(store.backup(Path(command.path))), b""
        raise ValueError("Unsupported storage operation")


class AsyncStorage(QObject):
    """GUI-thread owner. Replies retain request identity; shutdown drains the accepted FIFO.

    Keep this object alive until ``closed``. No blocking wait, thread termination or shared
    SQLite connection. A host must stop its active process before requesting shutdown.
    """

    replied = Signal(object)
    closed = Signal()
    _requested = Signal(str, object)
    _retire_requested = Signal()

    def __init__(self, parent: QObject | None = None, *, max_pending: int = 64) -> None:
        super().__init__(parent)
        if type(max_pending) is not int or max_pending < 1:
            raise ValueError("max_pending must be a positive integer")
        self._max_pending = max_pending
        self._pending: set[str] = set()
        self._closing_id: str | None = None
        self._thread = QThread(self)
        self._worker = _StorageWorker()
        self._worker.moveToThread(self._thread)
        self._requested.connect(self._worker.execute, Qt.ConnectionType.QueuedConnection)
        self._worker.replied.connect(self._deliver, Qt.ConnectionType.QueuedConnection)
        self._retire_requested.connect(self._worker.retire, Qt.ConnectionType.QueuedConnection)
        self._worker.destroyed.connect(self._worker_destroyed, Qt.ConnectionType.QueuedConnection)
        self._thread.finished.connect(self._thread_stopped)
        self._thread.start()

    def _assert_owner(self) -> None:
        if QThread.currentThread() != self.thread():
            raise RuntimeError("Storage port must be called from its owning GUI thread")

    def submit(self, command: StorageCommand) -> str:
        self._assert_owner()
        if self._closing_id is not None:
            raise RuntimeError("Storage is closing")
        if type(command) is not StorageCommand:
            raise TypeError("Expected an immutable StorageCommand")
        if type(command.data) is not bytes:
            raise TypeError("Queued document must be immutable bytes")
        if command.operation == "close":
            raise ValueError("Use shutdown() to close the port")
        if len(self._pending) >= self._max_pending:
            raise RuntimeError("Storage queue is full")
        budget = 64 if command.operation == "import_bytes" else 16
        if len(command.data) > budget * 1024 * 1024:
            raise ValueError(f"Payload exceeds {budget} MiB storage queue budget")
        return self._enqueue(command)

    def _enqueue(self, command: StorageCommand) -> str:
        request_id = uuid4().hex
        self._pending.add(request_id)
        _trace("enqueue", request_id, command.operation)
        self._requested.emit(request_id, command)
        return request_id

    def shutdown(self) -> None:
        self._assert_owner()
        if self._closing_id is None:
            self._closing_id = self._enqueue(StorageCommand("close"))

    @Slot(object)
    def _deliver(self, reply: StorageReply) -> None:
        _trace(
            "deliver",
            reply.request_id,
            outcome="pending" if reply.request_id in self._pending else "unknown",
        )
        if reply.request_id not in self._pending:
            return
        self._pending.remove(reply.request_id)
        self.replied.emit(reply)
        if reply.request_id == self._closing_id:
            self._retire_requested.emit()

    @Slot()
    def _thread_stopped(self) -> None:
        # finished precedes TLS teardown. A zero-time join is a nonblocking probe.
        if not self._thread.wait(0):
            QTimer.singleShot(1, self._thread_stopped)
            return
        # Destruction on a worker thread can invert Qt's object lock and the GIL.
        # Retirement moved the drained worker here before stopping that thread.
        self._worker.deleteLater()

    @Slot()
    def _worker_destroyed(self) -> None:
        self.closed.emit()
