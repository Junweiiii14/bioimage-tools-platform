"""Host arbitration: persisted PID before request; observed exit before terminal commit."""

from dataclasses import dataclass
from threading import Event

from PySide6.QtCore import QObject, Signal, Slot
from tool_contracts.api import ExecutionRequest, ProcessExitReceipt, RunRecord

from bioimage_app.process import ProcessCodec, ProcessOutcome, ProcessRunner
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply


@dataclass(frozen=True)
class RunCompletion:
    run_id: str
    record: RunRecord | None
    outcome: ProcessOutcome
    error: str = ""


class RunSession(QObject):
    """Own until completed. Tools get neither Workspace nor DB; results retain run revision."""

    received = Signal(object)
    completed = Signal(object)

    def __init__(
        self,
        storage: AsyncStorage,
        prepared: RunRecord,
        codec: ProcessCodec,
        parent: QObject | None = None,
        *,
        module_request: ExecutionRequest | None = None,
        module_output_directory: str = "",
    ) -> None:
        super().__init__(parent)
        if prepared.state != "prepared" or prepared.pid is not None:
            raise ValueError("Session requires a frozen prepared run")
        if (module_request is None) != (not module_output_directory):
            raise ValueError("Module publication requires both request and staging directory")
        self._module_request = (
            ExecutionRequest.model_validate_json(module_request.model_dump_json())
            if module_request is not None
            else None
        )
        if module_request is not None and (prepared.document_id, prepared.revision) != (
            module_request.document_id,
            module_request.revision,
        ):
            raise ValueError("Module request differs from the prepared document revision")
        self._module_output_directory = module_output_directory
        self._store = storage
        self._prepared = prepared
        self._runner = ProcessRunner(codec, self)
        self._pending: dict[str, str] = {}
        self._cancellation = Event()
        self._cancel_recorded = False
        self._start_registered = False
        self._start_failed = False
        self._outcome: ProcessOutcome | None = None
        self._terminal_submitted = False
        self._done = False
        self._store.replied.connect(self._reply)
        self._runner.started.connect(self._started)
        self._runner.received.connect(self.received)
        self._runner.finished.connect(self._exited)

    def start(self, command: tuple[str, ...], cwd: str, request: bytes) -> None:
        self._runner.start(command, cwd, request)

    def _submit(self, purpose: str, command: StorageCommand) -> None:
        try:
            request_id = self._store.submit(command)
        except (ValueError, RuntimeError):
            self._start_failed = True
            self._runner.abort("storage_queue_unavailable")
            if self._outcome is not None:
                self._finish(None, "storage_queue_unavailable")
            return
        self._pending[request_id] = purpose

    @Slot(int)
    def _started(self, pid: int) -> None:
        self._submit("start", StorageCommand("start", run_id=self._prepared.run_id, pid=pid))

    def cancel(self) -> None:
        if self._done:
            return
        self._cancellation.set()
        if self._start_registered or self._outcome is not None and self._outcome.pid == 0:
            self._record_cancel()

    def _record_cancel(self) -> None:
        if self._cancel_recorded or "cancel" in self._pending.values():
            return
        self._submit("cancel", StorageCommand("cancel", run_id=self._prepared.run_id))

    @Slot(object)
    def _reply(self, reply: StorageReply) -> None:
        purpose = self._pending.pop(reply.request_id, None)
        if purpose is None or self._done:
            return
        if reply.error_code is not None:
            if (
                purpose == "commit"
                and self._cancellation.is_set()
                and reply.error_code == "StateConflict"
            ):
                self._terminal_submitted = False
                self._record_cancel()
                return
            self._start_failed = True
            self._runner.abort("storage_" + reply.error_code)
            if self._outcome is not None:
                self._finish(None, reply.error_code)
            return
        if purpose == "start":
            self._start_registered = True
            if self._cancellation.is_set():
                self._record_cancel()
            else:
                self._runner.allow_request(self._runner_pid(reply))
        elif purpose == "cancel":
            self._cancel_recorded = True
            self._runner.cancel()
        elif purpose in ("commit", "cancelled", "failed"):
            if not isinstance(reply.value, RunRecord):
                self._finish(None, "invalid_storage_reply")
            else:
                self._finish(reply.value, "")
            return
        self._try_terminal()

    @staticmethod
    def _runner_pid(reply: StorageReply) -> int:
        if not isinstance(reply.value, RunRecord) or reply.value.pid is None:
            raise ValueError("Storage did not confirm process ownership")
        return reply.value.pid

    @Slot(object)
    def _exited(self, outcome: ProcessOutcome) -> None:
        self._outcome = outcome
        if self._start_failed:
            self._finish(None, "process_state_not_persisted")
            return
        if self._cancellation.is_set():
            self._record_cancel()
        self._try_terminal()

    def _try_terminal(self) -> None:
        outcome = self._outcome
        if outcome is None or self._terminal_submitted or self._done or self._pending:
            return
        receipt = ProcessExitReceipt(
            run_id=self._prepared.run_id,
            pid=outcome.pid,
            exit_code=outcome.exit_code,
        )
        run_id = self._prepared.run_id
        if self._cancellation.is_set():
            if not self._cancel_recorded:
                self._record_cancel()
                return
            command = StorageCommand("cancelled", run_id=run_id, receipt=receipt)
        elif (
            outcome.error
            or outcome.terminal is None
            or outcome.terminal.kind != "result"
            or outcome.exit_code != 0
            or (outcome.terminal.payload_kind == "module_manifest")
            != (self._module_request is not None)
        ):
            reason = outcome.error or (
                outcome.terminal.reason if outcome.terminal else "missing_result"
            )
            command = StorageCommand(
                "failed",
                run_id=run_id,
                receipt=receipt,
                reason=reason
                or (
                    "module_publication_binding_missing"
                    if outcome.exit_code == 0
                    and outcome.terminal is not None
                    and (outcome.terminal.payload_kind == "module_manifest")
                    != (self._module_request is not None)
                    else "worker_nonzero_exit"
                ),
                interrupted=bool(outcome.error),
            )
        else:
            command = StorageCommand(
                "commit",
                run_id=run_id,
                receipt=receipt,
                data=outcome.terminal.data,
                cancellation=self._cancellation,
                module_request=self._module_request,
                path=self._module_output_directory,
            )
        self._terminal_submitted = True
        self._submit(command.operation, command)

    def _finish(self, record: RunRecord | None, error: str) -> None:
        if self._done or self._outcome is None:
            return
        self._done = True
        self._store.replied.disconnect(self._reply)
        self.completed.emit(RunCompletion(self._prepared.run_id, record, self._outcome, error))
