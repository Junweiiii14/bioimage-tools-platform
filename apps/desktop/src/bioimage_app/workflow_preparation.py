"""Trusted host registrations and bounded background preparation; no workspace handles."""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import Literal
from uuid import uuid4

from platform_runtime.api import ModuleRegistration, verify_execution_plan
from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from tool_contracts.api import (
    BoundAsset,
    ExecutionPlan,
    ExecutionRequest,
    RunRecord,
    RuntimeVersion,
    WorkflowLedger,
)

from bioimage_app.process import ProcessCodec


@dataclass(frozen=True)
class HostInputFile:
    binding: BoundAsset
    path: str


@dataclass(frozen=True)
class WorkflowLaunch:
    request: ExecutionRequest
    run: RunRecord
    command: tuple[str, ...]
    cwd: str
    frame: bytes
    output_directory: str
    codec: ProcessCodec


@dataclass(frozen=True)
class WorkflowHostModule:
    """Only application code constructs these callbacks; nothing is loaded from a graph."""

    registration: ModuleRegistration
    environment: tuple[RuntimeVersion, ...]
    launch: Callable[[ExecutionRequest, RunRecord, tuple[HostInputFile, ...], str], WorkflowLaunch]


HostRegistryFactory = Callable[[ExecutionPlan], tuple[WorkflowHostModule, ...]]


@dataclass(frozen=True)
class WorkflowInitializationCommand:
    initialize: Callable[[], ExecutionPlan]


@dataclass(frozen=True)
class WorkflowPreparationCommand:
    operation: Literal["verify", "request", "launch"]
    plan: ExecutionPlan
    ledger: WorkflowLedger | None = None
    request: ExecutionRequest | None = None
    run: RunRecord | None = None
    files: tuple[HostInputFile, ...] = ()
    cache: WorkflowLedger | None = None


@dataclass(frozen=True)
class WorkflowPreparationReply:
    request_id: str
    value: ExecutionPlan | ExecutionRequest | WorkflowLaunch | str | None = None
    error: str = ""


class _PrepareWorker(QObject):
    replied = Signal(object)

    def __init__(self, factory: HostRegistryFactory) -> None:
        super().__init__()
        self._owner = self.thread()
        self._factory = factory
        self._temporary: list[TemporaryDirectory[str]] = []
        self._modules: dict[str, WorkflowHostModule] = {}

    @Slot(str, object)
    def execute(
        self, request_id: str, command: WorkflowPreparationCommand | WorkflowInitializationCommand
    ) -> None:
        try:
            value = self._execute(command)
            reply = WorkflowPreparationReply(request_id, value)
        except (ValueError, OSError, TypeError, RuntimeError, ImportError, LookupError) as error:
            reply = WorkflowPreparationReply(
                request_id, error=type(error).__name__ + ": " + str(error)
            )
        self.replied.emit(reply)

    def _execute(
        self, command: WorkflowPreparationCommand | WorkflowInitializationCommand
    ) -> ExecutionPlan | ExecutionRequest | WorkflowLaunch | str:
        if isinstance(command, WorkflowInitializationCommand):
            return command.initialize()
        if command.operation == "verify":
            modules = self._factory(command.plan)
            self._modules = {item.registration.interface.module.module_id: item for item in modules}
            verify_execution_plan(command.plan, tuple(item.registration for item in modules))
            for node in command.plan.nodes:
                if self._modules[node.interface.module.module_id].environment != node.environment:
                    raise ValueError("Current environment does not admit the frozen workflow")
            return command.plan
        if command.operation == "request":
            ledger = command.ledger
            assert ledger is not None  # Internal command shape established by WorkflowSession.
            node = command.plan.nodes[len(ledger.results)]
            if command.cache is not None:
                key = node.computation_key
                cached = next(
                    (item for item in command.cache.results if item.computation_key == key), None
                )
                if cached is not None:
                    return cached.node_id
            previous = {item.node_id: item for item in ledger.results}
            bindings: list[BoundAsset] = []
            for item in node.inputs:
                if item.asset is not None:
                    ref = item.asset.payload
                else:
                    upstream = previous[item.source_node or ""]
                    ref = next(
                        output.asset
                        for output in upstream.outputs
                        if output.port == item.source_port
                    )
                bound_port = next(
                    port for port in node.interface.module.input_ports if port.name == item.port
                )
                bindings.append(BoundAsset(port=item.port, kind=bound_port.kind, asset=ref))
            return ExecutionRequest(
                request_id=uuid4().hex,
                execution_id=ledger.execution_id,
                node_id=node.node_id,
                attempt_id=uuid4().hex,
                document_id=uuid4().hex,
                revision=0,
                module=node.interface.module,
                inputs=tuple(bindings),
                parameters_json=node.parameters_json,
                parameters_sha256=hashlib.sha256(node.parameters_json.encode()).hexdigest(),
                environment=node.environment,
            )
        req, run = command.request, command.run
        assert req is not None and run is not None
        temporary = TemporaryDirectory(prefix="bioimage-workflow-")
        self._temporary.append(temporary)
        return self._modules[req.module.module_id].launch(req, run, command.files, temporary.name)

    @Slot()
    def retire(self) -> None:
        for temporary in self._temporary:
            temporary.cleanup()
        self._temporary.clear()
        thread = self.thread()
        self.moveToThread(self._owner)
        thread.quit()


class WorkflowPreparation(QObject):
    """Same owner-thread shutdown protocol as storage; accepted jobs drain before retirement."""

    replied = Signal(object)
    closed = Signal()
    _requested = Signal(str, object)
    _retire = Signal()

    def __init__(self, factory: HostRegistryFactory, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pending: set[str] = set()
        self._closing = False
        self._retiring = False
        self._thread = QThread(self)
        self._worker = _PrepareWorker(factory)
        self._worker.moveToThread(self._thread)
        self._requested.connect(self._worker.execute, Qt.ConnectionType.QueuedConnection)
        self._worker.replied.connect(self._reply, Qt.ConnectionType.QueuedConnection)
        self._retire.connect(self._worker.retire, Qt.ConnectionType.QueuedConnection)
        self._thread.finished.connect(self._stopped)
        self._worker.destroyed.connect(self._destroyed, Qt.ConnectionType.QueuedConnection)
        self._thread.start()

    def submit(self, command: WorkflowPreparationCommand | WorkflowInitializationCommand) -> str:
        if QThread.currentThread() != self.thread():
            raise RuntimeError("Preparation must be used from its owning thread")
        if self._closing or len(self._pending) >= 64:
            raise RuntimeError("Preparation is closing or full")
        if type(command) not in (WorkflowPreparationCommand, WorkflowInitializationCommand):
            raise TypeError("Expected an immutable preparation command")
        request_id = uuid4().hex
        self._pending.add(request_id)
        self._requested.emit(request_id, command)
        return request_id

    @Slot(object)
    def _reply(self, reply: WorkflowPreparationReply) -> None:
        if reply.request_id not in self._pending:
            return
        self._pending.remove(reply.request_id)
        self.replied.emit(reply)
        self._retire_if_ready()

    def shutdown(self) -> None:
        if QThread.currentThread() != self.thread():
            raise RuntimeError("Preparation must close from its owning thread")
        if not self._closing:
            self._closing = True
            self._retire_if_ready()

    def _retire_if_ready(self) -> None:
        if self._closing and not self._pending and not self._retiring:
            self._retiring = True
            self._retire.emit()

    @Slot()
    def _stopped(self) -> None:
        if not self._thread.wait(0):
            QTimer.singleShot(1, self._stopped)
            return
        self._worker.deleteLater()

    @Slot()
    def _destroyed(self) -> None:
        self.closed.emit()
