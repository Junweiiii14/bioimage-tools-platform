"""One editor storage owner and the same finite batch controller used by the CLI."""

import json

from PySide6.QtCore import QObject, Signal, Slot
from tool_contracts.api import DraftSnapshot

from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.workflow_authoring_models import AuthoringProjection
from bioimage_app.workflow_authoring_store import execute_authoring_store
from bioimage_app.workflow_batch_session import WorkflowBatchSession, WorkflowBatchStatus
from bioimage_app.workflow_preparation import HostRegistryFactory


class WorkflowAuthoringSession(QObject):
    # Document JSON is encoded on the storage worker, not the GUI thread.
    documentChanged = Signal(str, str, str, str)
    progressChanged = Signal(object)
    activityChanged = Signal(bool, bool)
    finished = Signal()

    def __init__(self, registry: HostRegistryFactory, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._store = AsyncStorage(self, authoring=execute_authoring_store)
        self._store.replied.connect(self._reply)
        self._store.closed.connect(self._closed)
        self._pending: dict[str, tuple[str, str]] = {}
        self._projection: AuthoringProjection | None = None
        self._batch: WorkflowBatchSession | None = None
        self._status: WorkflowBatchStatus | None = None
        self._workspace = ""
        self._document = ""
        self._initial: bytes | None = None
        self._used = False
        self._closing = False
        self._cancel_pending = False
        self._stopping_store = False
        self._resources_closed = False

    @property
    def projection(self) -> AuthoringProjection | None:
        return self._projection

    @property
    def workspace(self) -> str:
        return self._workspace

    @property
    def running(self) -> bool:
        return self._batch is not None

    @property
    def pending(self) -> bool:
        return bool(self._pending)

    @property
    def resources_closed(self) -> bool:
        return self._resources_closed

    @property
    def batch_status(self) -> WorkflowBatchStatus | None:
        return self._status

    def create(self, workspace: str, initialization: bytes) -> None:
        self._claim(workspace)
        self._initial = initialization
        self._submit("", "open", StorageCommand("create", path=workspace))

    def reopen(self, workspace: str, document_id: str = "") -> None:
        self._claim(workspace)
        self._document = document_id
        self._submit("", "open", StorageCommand("open", path=workspace))

    def _claim(self, workspace: str) -> None:
        if self._used or self._closing:
            raise RuntimeError("Editor session is single-use")
        self._used, self._workspace = True, workspace

    def request(self, token: str, data: bytes) -> None:
        if self._closing:
            self.documentChanged.emit(token, "", "", "工作流项目正在关闭，编辑仍保留。")
            return
        if self._pending:
            self.documentChanged.emit(token, "", "", "请等待当前保存回执，正在编辑的内容会保留。")
            return
        self._submit(token, "authoring", StorageCommand("workflow_authoring", data=data))

    def _submit(self, token: str, purpose: str, command: StorageCommand) -> None:
        request = self._store.submit(command)
        self._pending[request] = (token, purpose)
        self.activityChanged.emit(self.pending, self.running)

    @Slot(object)
    def _reply(self, reply: StorageReply) -> None:
        if reply.request_id not in self._pending:
            return
        token, purpose = self._pending.pop(reply.request_id)
        if reply.error_code is not None:
            self.documentChanged.emit(token, "", "", reply.error_code + ": " + reply.message)
        elif purpose == "open":
            if self._initial is not None:
                self.request("initialize", self._initial)
                self._initial = None
            elif self._document:
                self.request(
                    "load",
                    json.dumps({"operation": "load", "document_id": self._document}).encode(),
                )
            else:
                self._submit("load", "documents", StorageCommand("documents"))
        elif purpose == "documents":
            assert isinstance(reply.value, tuple)
            documents = tuple(
                d
                for d in reply.value
                if isinstance(d, DraftSnapshot) and d.tool_id == "workflow_authoring_v1"
            )
            if len(documents) != 1:
                self.documentChanged.emit(
                    token, "", "", "请选择包含一个已保存工作流草稿的项目目录。"
                )
            else:
                self._document = documents[0].document_id
                self.request(
                    token, json.dumps({"operation": "load", "document_id": self._document}).encode()
                )
        else:
            assert isinstance(reply.value, AuthoringProjection)
            value = reply.value
            if (
                self._projection is None
                or value.project.revision >= self._projection.project.revision
            ):
                self._projection = value
            self._document = value.project.document_id
            if value.batch is not None and self._batch is None:
                if value.operation == "freeze":
                    self._launch(value.batch.batch_id, resume=not self._cancel_pending)
                elif value.operation == "load" and value.batch.state in (
                    "running",
                    "pausing",
                    "paused",
                    "cancelling",
                ):
                    self._launch(value.batch.batch_id, resume=False)
            self.documentChanged.emit(token, value.operation, reply.data.decode("utf-8"), "")
        if not self._pending:
            self._cancel_pending = False
        self.activityChanged.emit(self.pending, self.running)
        self._close_if_ready()

    def _launch(self, batch_id: str, *, resume: bool) -> None:
        child = WorkflowBatchSession(self._registry, self, storage=self._store)
        self._batch = child
        resumed = False

        def changed(status: WorkflowBatchStatus) -> None:
            nonlocal resumed
            if self._batch is not child:
                return
            self._status = status
            self.progressChanged.emit(status)
            if resume and not self._closing and not resumed and status.phase == "awaiting_resume":
                resumed = child.resume()

        def completed(_status: WorkflowBatchStatus) -> None:
            if self._batch is child:
                child.close()

        def finished(status: WorkflowBatchStatus) -> None:
            if self._batch is child:
                self._batch = None
                self._status = status
                self.progressChanged.emit(status)
                self.activityChanged.emit(self.pending, self.running)
                child.deleteLater()
                self._close_if_ready()

        child.changed.connect(changed)
        child.completed.connect(completed)
        child.finished.connect(finished)
        child.reopen(self._workspace, batch_id)
        if self._closing:
            child.close()
        elif self._cancel_pending:
            child.cancel()

    def pause(self) -> bool:
        return self._batch.pause() if self._batch is not None else False

    def resume(self) -> bool:
        return self._batch.resume() if self._batch is not None else False

    def cancel(self) -> bool:
        if self._batch is not None:
            return self._batch.cancel()
        self._cancel_pending = self.pending
        return self._cancel_pending

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        if self._batch is not None:
            self._batch.close()
        self._close_if_ready()

    def _close_if_ready(self) -> None:
        if self._closing and not self._batch and not self._pending and not self._stopping_store:
            self._stopping_store = True
            self._store.shutdown()

    @Slot()
    def _closed(self) -> None:
        self._resources_closed = True
        self.finished.emit()
