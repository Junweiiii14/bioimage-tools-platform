"""One finite workflow, one real RunSession at a time, and storage-confirmed notifications."""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Literal
from uuid import uuid4

from PySide6.QtCore import QObject, Signal, Slot
from tool_contracts.api import (
    ExecutionEvent,
    ExecutionPlan,
    ExecutionRequest,
    ProcessExitReceipt,
    RunRecord,
    WorkflowLedger,
)

from bioimage_app.process import ProcessEvent
from bioimage_app.run_session import RunCompletion, RunSession
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.workflow_preparation import (
    HostInputFile,
    HostRegistryFactory,
    WorkflowInitializationCommand,
    WorkflowLaunch,
    WorkflowPreparation,
    WorkflowPreparationCommand,
    WorkflowPreparationReply,
)
from bioimage_app.workflow_storage import WorkflowStoreCommand


@dataclass(frozen=True)
class WorkflowStatus:
    execution_id: str
    state: str
    revision: int | None
    completed_nodes: int
    total_nodes: int
    node_id: str
    run_id: str
    pid: int | None
    message: str
    reused_nodes: int = 0


@dataclass(frozen=True)
class _Action:
    purpose: str
    command: StorageCommand


class WorkflowSession(QObject):
    """CLI and GUI share this controller. Keep it alive until finished after close()."""

    changed = Signal(object)
    completed = Signal(object)
    finished = Signal(object)

    def __init__(self, registry: HostRegistryFactory, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._store = AsyncStorage(self)
        self._prepare = WorkflowPreparation(registry, self)
        self._store.replied.connect(self._storage_reply)
        self._prepare.replied.connect(self._preparation_reply)
        self._store.closed.connect(self._service_closed)
        self._prepare.closed.connect(self._service_closed)
        self._queue: deque[_Action] = deque()
        self._waiting: tuple[str, _Action] | None = None
        self._preparing: tuple[str, str] | None = None
        self._ledger: WorkflowLedger | None = None
        self._plan: ExecutionPlan | None = None
        self._request: ExecutionRequest | None = None
        self._run: RunRecord | None = None
        self._session: RunSession | None = None
        self._files: list[HostInputFile] = []
        self._execution_id = ""
        self._used = False
        self._reopening = False
        self._auto = False
        self._hold = False
        self._cancel_requested = False
        self._closing = False
        self._services_closing = False
        self._closed_services = 0
        self._phase = "idle"
        self._message = ""
        self._fatal = False
        self._notified_revision: int | None = None
        self._cache_execution_id = ""
        self._cache: WorkflowLedger | None = None
        self._initial_workspace = ""

    @property
    def ledger(self) -> WorkflowLedger | None:
        return self._ledger

    def status(self) -> WorkflowStatus:
        ledger, run = self._ledger, self._run
        return WorkflowStatus(
            self._execution_id,
            ledger.state if ledger else "preparing",
            ledger.revision if ledger else None,
            len(ledger.results) if ledger else 0,
            len(self._plan.nodes) if self._plan else 0,
            self._request.node_id
            if self._request
            else (ledger.results[-1].node_id if ledger and ledger.results else ""),
            run.run_id if run else "",
            run.pid if run else None,
            self._message,
            sum(item.reused for item in ledger.results) if ledger else 0,
        )

    def start(
        self,
        workspace: str,
        plan: ExecutionPlan,
        *,
        execution_id: str | None = None,
        cache_execution_id: str = "",
    ) -> None:
        self._claim()
        self._plan, self._execution_id, self._auto = plan, execution_id or uuid4().hex, True
        self._cache_execution_id = cache_execution_id
        self._enqueue("open", StorageCommand("open", path=workspace))

    def reopen(self, workspace: str, execution_id: str) -> None:
        self._claim()
        self._execution_id, self._reopening = execution_id, True
        self._enqueue("open", StorageCommand("open", path=workspace))

    def initialize(
        self,
        workspace: str,
        initialize: Callable[[], ExecutionPlan],
        *,
        cache_execution_id: str = "",
    ) -> None:
        """Trusted application setup owns and closes its workspace on the preparation thread."""
        self._claim()
        self._initial_workspace, self._execution_id, self._auto = workspace, uuid4().hex, True
        self._cache_execution_id = cache_execution_id
        self._prepare_job("initialize", WorkflowInitializationCommand(initialize))

    def _claim(self) -> None:
        if self._used or self._closing:
            raise RuntimeError("Workflow session is single-use")
        self._used = True

    def pause(self, command_id: str | None = None) -> bool:
        self._hold = True
        return self._control("pause", command_id)

    def resume(self, command_id: str | None = None) -> bool:
        ledger = self._ledger
        if (
            self._closing
            or self._fatal
            or self._preparing is not None
            or ledger is None
            or ledger.active_attempt is not None
        ):
            return False
        if ledger.state not in ("running", "paused", "failed", "interrupted"):
            return False
        self._message = command_id or uuid4().hex
        self._prepare_job("resume", WorkflowPreparationCommand("verify", ledger.plan))
        return True

    def cancel(self, command_id: str | None = None) -> bool:
        self._hold = self._cancel_requested = True
        if self._session is not None:
            self._session.cancel()
        accepted = self._control("cancel", command_id)
        if (
            self._session is None
            and self._run is not None
            and self._phase in ("paths", "launching")
        ):
            self._cancel_prepared()
        return accepted

    def _control(self, action: str, command_id: str | None) -> bool:
        if self._fatal or self._services_closing:
            return False
        if self._ledger is None:
            return True  # The local hold/cancel is applied immediately after journal creation.
        pending = sum(item.purpose == "control" for item in self._queue)
        pending += int(self._waiting is not None and self._waiting[1].purpose == "control")
        limit = 128 if action == "cancel" else 127
        if self._ledger.control_count + pending >= limit:
            return False
        self._workflow("control", action=action, command_id=command_id or uuid4().hex)
        return True

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        ledger = self._ledger
        if not self._fatal and (
            ledger is None or ledger.active_attempt is not None or ledger.state == "running"
        ):
            self.cancel()
        self._close_if_idle()

    def _enqueue(self, purpose: str, command: StorageCommand) -> None:
        self._queue.append(_Action(purpose, command))
        self._pump()

    def _workflow(
        self,
        operation: Literal[
            "create",
            "load",
            "begin",
            "prepare",
            "started",
            "worker",
            "finish",
            "recover",
            "reuse",
            "control",
            "abandon",
        ],
        *,
        plan: ExecutionPlan | None = None,
        request: ExecutionRequest | None = None,
        action: str = "",
        command_id: str = "",
        reason: str = "",
        attempt_id: str = "",
        run_id: str = "",
        event: ExecutionEvent | None = None,
        source_document_id: str = "",
        source_node_id: str = "",
    ) -> None:
        # Fixed operation names are internal literals; untrusted graph data never selects code.
        command = WorkflowStoreCommand(
            operation=operation,
            document_id=self._execution_id,
            plan=plan,
            request=request,
            action=action,
            command_id=command_id,
            reason=reason,
            attempt_id=attempt_id,
            run_id=run_id,
            event=event,
            source_document_id=source_document_id,
            source_node_id=source_node_id,
        )
        self._enqueue(operation, StorageCommand("workflow", workflow=command))

    def _pump(self) -> None:
        if self._waiting is not None or not self._queue or self._fatal:
            return
        action = self._queue.popleft()
        command = action.command
        if command.workflow is not None and command.workflow.operation not in ("create", "load"):
            if self._ledger is None:
                self._fail("Workflow journal is unavailable")
                return
            command = replace(
                command, workflow=replace(command.workflow, expected_revision=self._ledger.revision)
            )
        try:
            self._waiting = (self._store.submit(command), action)
        except (ValueError, RuntimeError) as error:
            self._fail(str(error))

    def _prepare_job(
        self, purpose: str, command: WorkflowPreparationCommand | WorkflowInitializationCommand
    ) -> None:
        if self._preparing is not None:
            raise RuntimeError("Overlapping workflow preparation")
        self._preparing = (self._prepare.submit(command), purpose)

    @Slot(object)
    def _storage_reply(self, reply: StorageReply) -> None:
        waiting = self._waiting
        if waiting is None or waiting[0] != reply.request_id:
            return
        self._waiting = None
        if reply.error_code is not None:
            self._fail(reply.error_code + ": " + reply.message)
            return
        purpose = waiting[1].purpose
        if purpose == "cache_source":
            assert isinstance(reply.value, WorkflowLedger)
            self._cache = reply.value
        elif isinstance(reply.value, WorkflowLedger):
            self._ledger = reply.value
            self._plan = reply.value.plan
        self._handle_storage(purpose, reply)
        self.changed.emit(self.status())
        self._pump()
        self._next()
        self._close_if_idle()

    def _handle_storage(self, purpose: str, reply: StorageReply) -> None:
        ledger = self._ledger
        if purpose == "open":
            if self._reopening:
                self._workflow("load")
            elif self._plan is not None:
                self._prepare_job("initial", WorkflowPreparationCommand("verify", self._plan))
        elif purpose == "load" and ledger is not None:
            if ledger.active_attempt is not None:
                self._workflow("recover")
        elif purpose == "create":
            if self._cancel_requested:
                self._workflow("control", action="cancel", command_id=uuid4().hex)
            elif self._hold:
                self._workflow("control", action="pause", command_id=uuid4().hex)
        elif purpose == "cache_source":
            self._workflow("create", plan=self._plan)
        elif purpose == "begin":
            if self._cancel_requested:
                self._workflow(
                    "abandon",
                    attempt_id=self._request.attempt_id if self._request else "",
                    reason="cancelled_before_prepare",
                )
            elif self._request is not None:
                self._phase = "preparing"
                self._workflow("prepare", request=self._request)
        elif purpose == "prepare" and ledger is not None:
            active = ledger.active_attempt
            if active is None or active.run is None:
                self._fail("Prepared workflow has no associated real run")
                return
            self._run = active.run
            self._files.clear()
            self._phase = "paths"
            if self._cancel_requested:
                self._cancel_prepared()
            else:
                self._next_path()
        elif purpose == "asset":
            req = self._request
            if req is None or not isinstance(reply.value, str):
                self._fail("Missing resolved input path")
                return
            self._files.append(HostInputFile(req.inputs[len(self._files)], reply.value))
            if not self._cancel_requested:
                self._next_path()
        elif purpose == "started":
            if (
                self._session is not None
                and ledger is not None
                and ledger.active_attempt is not None
            ):
                run = ledger.active_attempt.run
                if run is not None and run.pid is not None:
                    self._run = run
                    self._session.authorize_request(run.run_id, run.pid)
        elif purpose == "cancel_prepared" and self._run is not None:
            self._enqueue(
                "retire_prepared",
                StorageCommand(
                    "cancelled",
                    run_id=self._run.run_id,
                    receipt=ProcessExitReceipt(run_id=self._run.run_id, pid=0, exit_code=None),
                ),
            )
        elif purpose in ("retire_prepared", "fail_prepared"):
            self._finish_node()
        elif purpose in ("finish", "abandon", "reuse"):
            self._phase = "idle"
        elif purpose == "control" and ledger is not None and ledger.state == "running":
            self._auto, self._hold = True, False

    def _next_path(self) -> None:
        req, run, plan = self._request, self._run, self._plan
        if req is None or run is None or plan is None:
            self._fail("Input path preparation has no frozen attempt")
            return
        if len(self._files) < len(req.inputs):
            self._enqueue(
                "asset", StorageCommand("asset", asset=req.inputs[len(self._files)].asset)
            )
        else:
            self._phase = "launching"
            self._prepare_job(
                "launch",
                WorkflowPreparationCommand(
                    "launch", plan, request=req, run=run, files=tuple(self._files)
                ),
            )

    def _cancel_prepared(self) -> None:
        if self._run is not None and self._phase != "retiring":
            self._phase = "retiring"
            self._enqueue("cancel_prepared", StorageCommand("cancel", run_id=self._run.run_id))

    @Slot(object)
    def _preparation_reply(self, reply: WorkflowPreparationReply) -> None:
        waiting = self._preparing
        if waiting is None or waiting[0] != reply.request_id:
            return
        self._preparing = None
        purpose = waiting[1]
        if reply.error:
            self._message = reply.error
            self._auto = False
            if purpose == "launch" and self._run is not None and not self._cancel_requested:
                self._phase = "retiring"
                self._enqueue(
                    "fail_prepared",
                    StorageCommand(
                        "failed",
                        run_id=self._run.run_id,
                        receipt=ProcessExitReceipt(run_id=self._run.run_id, pid=0, exit_code=None),
                        reason="workflow_preparation_failed",
                    ),
                )
            else:
                self.completed.emit(self.status())
        elif purpose == "initialize":
            assert isinstance(reply.value, ExecutionPlan)
            self._plan = reply.value
            self._enqueue("open", StorageCommand("open", path=self._initial_workspace))
        elif purpose == "initial" and self._plan is not None:
            if self._cache_execution_id:
                self._enqueue(
                    "cache_source",
                    StorageCommand(
                        "workflow", workflow=WorkflowStoreCommand("load", self._cache_execution_id)
                    ),
                )
            else:
                self._workflow("create", plan=self._plan)
        elif purpose == "resume" and self._ledger is not None:
            if self._ledger.state == "running":
                self._auto, self._hold = True, False
            else:
                self._workflow("control", action="resume", command_id=self._message)
            self._message = ""
        elif purpose == "request" and isinstance(reply.value, str):
            if not self._hold and not self._closing:
                self._request, self._run, self._phase = None, None, "cache"
                self._workflow(
                    "reuse", source_document_id=self._cache_execution_id, source_node_id=reply.value
                )
        elif purpose == "request" and isinstance(reply.value, ExecutionRequest):
            if not self._hold and not self._closing:
                self._request = reply.value
                self._run = None
                self._phase = "intent"
                self._workflow("begin", request=reply.value)
        elif purpose == "launch" and isinstance(reply.value, WorkflowLaunch):
            if not self._cancel_requested and not self._closing and not self._fatal:
                self._launch(reply.value)
        self._pump()
        self._next()
        self._close_if_idle()

    def _launch(self, launch: WorkflowLaunch) -> None:
        req, run = launch.request, launch.run
        session = RunSession(
            self._store,
            run,
            launch.codec,
            self,
            module_request=req,
            module_output_directory=launch.output_directory,
            require_dispatch_ack=True,
        )
        self._session, self._phase = session, "running"

        def started(record: RunRecord) -> None:
            self._started(req.attempt_id, run.run_id, record)

        def received(event: ProcessEvent) -> None:
            self._event(req.attempt_id, run.run_id, event)

        def completed(result: RunCompletion) -> None:
            self._node_done(req.attempt_id, run.run_id, result)

        session.started.connect(started)
        session.received.connect(received)
        session.completed.connect(completed)
        session.start(launch.command, launch.cwd, launch.frame)

    def _source(self, attempt_id: str, run_id: str) -> bool:
        return (
            self._request is not None
            and self._run is not None
            and (self._request.attempt_id, self._run.run_id) == (attempt_id, run_id)
        )

    def _started(self, attempt_id: str, run_id: str, record: RunRecord) -> None:
        if self._source(attempt_id, run_id):
            self._run = record
            self._workflow("started", attempt_id=attempt_id, run_id=run_id)

    def _event(self, attempt_id: str, run_id: str, event: ProcessEvent) -> None:
        if not self._source(attempt_id, run_id) or self._fatal:
            return
        if event.module_event is None:
            self._fail("Workflow worker did not preserve its original protocol event")
            return
        self._workflow("worker", attempt_id=attempt_id, run_id=run_id, event=event.module_event)

    def _node_done(self, attempt_id: str, run_id: str, completion: RunCompletion) -> None:
        if not self._source(attempt_id, run_id):
            return
        if self._session is not None:
            self._session.deleteLater()
        self._session = None
        if completion.record is not None:
            self._run = completion.record
        if not self._fatal:
            if completion.record is None:
                self._fail(
                    "Node process exited but its persistence is unknown: " + completion.error
                )
            else:
                self._finish_node()
        self._close_if_idle()

    def _finish_node(self) -> None:
        if self._request is not None and self._run is not None:
            self._workflow("finish", attempt_id=self._request.attempt_id, run_id=self._run.run_id)

    def _next(self) -> None:
        ledger = self._ledger
        if (
            self._queue
            or self._waiting is not None
            or self._preparing is not None
            or self._session is not None
        ):
            return
        if ledger is not None and ledger.state in (
            "succeeded",
            "failed",
            "cancelled",
            "interrupted",
        ):
            if self._notified_revision != ledger.revision:
                self._notified_revision = ledger.revision
                self.completed.emit(self.status())
        elif (
            ledger is not None
            and ledger.state == "running"
            and ledger.active_attempt is None
            and self._phase == "idle"
            and self._auto
            and not self._hold
            and not self._closing
            and not self._fatal
        ):
            self._prepare_job(
                "request",
                WorkflowPreparationCommand(
                    "request", ledger.plan, ledger=ledger, cache=self._cache
                ),
            )

    def _fail(self, message: str) -> None:
        self._fatal, self._auto, self._hold = True, False, True
        self._message = "Persistence/execution requires recovery: " + message[:1024]
        self._queue.clear()
        if self._session is not None:
            self._session.abort("workflow_host_failed")
        self.changed.emit(self.status())
        self.completed.emit(self.status())
        self._close_if_idle()

    def _close_if_idle(self) -> None:
        if (
            self._closing
            and not self._services_closing
            and self._session is None
            and self._preparing is None
            and self._waiting is None
            and not self._queue
        ):
            self._services_closing = True
            self._prepare.shutdown()
            self._store.shutdown()

    @Slot()
    def _service_closed(self) -> None:
        self._closed_services += 1
        if self._closed_services == 2:
            self.finished.emit(self.status())
