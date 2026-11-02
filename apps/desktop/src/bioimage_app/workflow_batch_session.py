"""Sequential samples share the existing workflow executor and one storage owner."""

from collections import deque
from dataclasses import dataclass, replace
from typing import Literal
from uuid import uuid4

from PySide6.QtCore import QObject, Signal, Slot
from tool_contracts.api import DraftSnapshot, WorkflowBatch

from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.workflow_batch_storage import WorkflowBatchStoreCommand
from bioimage_app.workflow_preparation import HostRegistryFactory
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus


@dataclass(frozen=True)
class WorkflowBatchStatus:
    batch_id: str
    state: str
    phase: str
    total: int
    succeeded: int
    issues: int
    failed: int
    cancelled: int
    sample_id: str
    child: WorkflowStatus | None
    message: str


class WorkflowBatchSession(QObject):
    changed = Signal(object)
    completed = Signal(object)
    finished = Signal(object)

    def __init__(self, registry: HostRegistryFactory, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._store = AsyncStorage(self)
        self._store.replied.connect(self._reply)
        self._store.closed.connect(self._closed)
        self._batch: WorkflowBatch | None = None
        self._initial: WorkflowBatch | None = None
        self._workspace = ""
        self._document = ""
        self._queue: deque[WorkflowBatchStoreCommand] = deque()
        self._waiting: tuple[str, str] | None = None
        self._child: WorkflowSession | None = None
        self._existing_child = False
        self._resumed_child = False
        self._child_control = ""
        self._child_error = ""
        self._need_child = False
        self._auto = False
        self._used = False
        self._closing = False
        self._shutting_down = False
        self._fatal = False
        self._phase = "idle"
        self._message = ""
        self._notified_revision: int | None = None

    @property
    def batch(self) -> WorkflowBatch | None:
        return self._batch

    def status(self) -> WorkflowBatchStatus:
        batch = self._batch
        index = batch.current_index if batch else None
        return WorkflowBatchStatus(
            self._document,
            batch.state if batch else "preparing",
            self._phase,
            len(batch.items) if batch else 0,
            sum(i.state == "succeeded" for i in batch.items) if batch else 0,
            sum(i.state == "issues" for i in batch.items) if batch else 0,
            sum(i.state == "failed" for i in batch.items) if batch else 0,
            sum(i.state == "cancelled" for i in batch.items) if batch else 0,
            batch.items[index].sample_id if batch and index is not None else "",
            self._child.status() if self._child else None,
            self._message,
        )

    def start(self, workspace: str, batch: WorkflowBatch) -> None:
        self._claim(workspace, batch.batch_id)
        self._initial, self._auto = batch, True
        self._submit("open", StorageCommand("open", path=workspace))

    def reopen(self, workspace: str, batch_id: str) -> None:
        self._claim(workspace, batch_id)
        self._submit("open", StorageCommand("open", path=workspace))

    def _claim(self, workspace: str, document: str) -> None:
        if self._used or self._closing:
            raise RuntimeError("Batch session is single-use")
        self._used = True
        self._workspace, self._document, self._phase = workspace, document, "opening"

    def pause(self, command_id: str | None = None) -> bool:
        return self._control("pause", command_id)

    def resume(self, command_id: str | None = None) -> bool:
        return self._control("resume", command_id)

    def cancel(self, command_id: str | None = None) -> bool:
        return self._control("cancel", command_id)

    def _control(
        self, action: Literal["pause", "resume", "cancel"], command_id: str | None
    ) -> bool:
        if not self._used or self._fatal or self._shutting_down:
            return False
        if command_id and self._batch is not None:
            previous = next((c for c in self._batch.controls if c.command_id == command_id), None)
            if previous is not None:
                return previous.action == action
        if action == "resume" and not (
            self._batch is not None
            and (self._batch.state == "paused" or self._phase == "awaiting_resume")
        ):
            return False
        count = len(self._batch.controls) if self._batch else 0
        count += sum(c.operation == "control" for c in self._queue)
        count += int(self._waiting is not None and self._waiting[1] == "control")
        if count >= (128 if action == "cancel" else 127):
            return False
        self._queue.append(
            WorkflowBatchStoreCommand(
                "control", self._document, action=action, command_id=command_id or uuid4().hex
            )
        )
        self._drive()
        if action == "cancel" and self._child is not None:
            self._child_control = "cancel"
            self._child.cancel()
        return True

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        if not self._fatal and (
            self._batch is None or self._batch.state in ("running", "pausing", "cancelling")
        ):
            self.cancel()
        self._drive()

    def _submit(self, purpose: str, command: StorageCommand) -> None:
        self._waiting = (self._store.submit(command), purpose)

    def _enqueue(
        self, operation: Literal["claim", "checkpoint", "input_failed"], *, reason: str = ""
    ) -> None:
        self._queue.append(WorkflowBatchStoreCommand(operation, self._document, reason=reason))

    def _drive(self) -> None:
        if self._waiting is not None or self._shutting_down:
            return
        if self._queue and not self._fatal:
            command = self._queue.popleft()
            if command.operation not in ("create", "load"):
                assert self._batch is not None
                command = replace(command, expected_revision=self._batch.revision)
            self._submit(
                command.operation, StorageCommand("workflow_batch", workflow_batch=command)
            )
            return
        batch = self._batch
        if self._child is not None:
            return
        if self._closing and (
            self._fatal or batch is None or batch.state not in ("running", "pausing", "cancelling")
        ):
            self._shutting_down = True
            self._store.shutdown()
            return
        if self._fatal or batch is None:
            return
        if batch.state in ("completed", "completed_with_issues", "cancelled"):
            if self._notified_revision != batch.revision:
                self._notified_revision = batch.revision
                self.completed.emit(self.status())
            return
        if self._need_child:
            self._need_child = False
            self._submit("documents", StorageCommand("documents"))
        elif batch.state == "cancelling" or (batch.state == "running" and self._auto):
            self._enqueue("claim")
            self._drive()

    @Slot(object)
    def _reply(self, reply: StorageReply) -> None:
        if self._waiting is None or self._waiting[0] != reply.request_id:
            return
        purpose = self._waiting[1]
        self._waiting = None
        if reply.error_code is not None:
            self._fail(reply.error_code + ": " + reply.message)
            return
        if isinstance(reply.value, WorkflowBatch):
            self._batch = reply.value
        if purpose == "open":
            self._queue.appendleft(
                WorkflowBatchStoreCommand(
                    "create" if self._initial is not None else "load",
                    self._document,
                    batch=self._initial,
                )
            )
        elif purpose == "load":
            self._phase = "awaiting_resume"
        elif purpose in ("create", "checkpoint", "input_failed"):
            self._phase = "ready"
        elif purpose == "claim":
            assert self._batch is not None
            self._need_child = self._batch.current_index is not None
            self._phase = "checking_child"
        elif purpose == "documents":
            assert self._batch is not None and self._batch.current_index is not None
            assert isinstance(reply.value, tuple)
            item = self._batch.items[self._batch.current_index]
            exists = any(
                isinstance(d, DraftSnapshot) and d.document_id == item.execution_id
                for d in reply.value
            )
            if not exists and self._batch.state == "cancelling":
                self._enqueue("checkpoint", reason="cancelled_before_child_creation")
            else:
                self._launch_child(exists)
        elif purpose == "control":
            assert self._batch is not None
            self._auto = self._batch.state == "running"
            self._apply_child_control()
        self.changed.emit(self.status())
        self._drive()

    def _launch_child(self, exists: bool) -> None:
        batch = self._batch
        assert batch is not None and batch.current_index is not None
        item = batch.items[batch.current_index]
        assert item.plan is not None
        child = WorkflowSession(self._registry, self, storage=self._store)
        self._child, self._existing_child = child, exists
        self._resumed_child, self._child_control, self._child_error = False, "", ""
        self._phase = "running"

        def changed(status: WorkflowStatus) -> None:
            if self._child is child:
                self._on_child_changed(status)

        def completed(status: WorkflowStatus) -> None:
            if self._child is child:
                self._child_error = status.message
                child.close()

        def finished(_status: WorkflowStatus) -> None:
            if self._child is child:
                self._child = None
                if (
                    self._child_error
                    and child.status().error_code == "IntegrityError"
                    and child.ledger is not None
                    and child.ledger.active_attempt is None
                    and child.ledger.state == "running"
                ):
                    self._enqueue("input_failed", reason=self._child_error)
                elif (
                    self._child_error
                    and child.ledger is not None
                    and child.ledger.state not in ("failed", "cancelled", "succeeded")
                ):
                    self._fail(self._child_error)
                elif not self._fatal:
                    self._enqueue("checkpoint", reason=self._child_error)
                child.deleteLater()
                self._drive()

        child.changed.connect(changed)
        child.completed.connect(completed)
        child.finished.connect(finished)
        if exists:
            child.reopen(self._workspace, item.execution_id)
        else:
            child.start(
                self._workspace,
                item.plan,
                execution_id=item.execution_id,
                cache_execution_id=item.cache_execution_id or "",
            )
        self._apply_child_control()

    def _apply_child_control(self) -> None:
        child, batch = self._child, self._batch
        if child is None or batch is None:
            return
        if self._child_control == "cancel":
            return
        action = (
            "cancel" if batch.state == "cancelling" else "pause" if batch.state == "pausing" else ""
        )
        if action and action != self._child_control:
            self._child_control = action
            child.cancel() if action == "cancel" else child.pause()

    def _on_child_changed(self, status: WorkflowStatus) -> None:
        child, batch = self._child, self._batch
        assert child is not None and batch is not None
        self._apply_child_control()
        ledger = child.ledger
        if ledger is not None:
            if batch.state == "pausing" and ledger.state == "paused":
                child.close()
            elif (
                self._existing_child
                and not self._resumed_child
                and self._child_control != "cancel"
                and batch.state == "running"
                and ledger.active_attempt is None
                and ledger.state in ("running", "paused", "failed", "interrupted")
            ):
                self._resumed_child = child.resume()
        self.changed.emit(self.status())

    def _fail(self, message: str) -> None:
        self._fatal, self._auto = True, False
        self._queue.clear()
        self._phase, self._message = "recovery_required", message[:1024]
        if self._child is not None:
            self._child.close()
        self.changed.emit(self.status())
        self.completed.emit(self.status())
        self._drive()

    @Slot()
    def _closed(self) -> None:
        self._phase = "closed"
        self.finished.emit(self.status())
