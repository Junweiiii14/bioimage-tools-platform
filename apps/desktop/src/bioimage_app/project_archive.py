"""Resolve recorded run evidence through the storage owner without GUI file I/O."""

from collections.abc import Callable
from dataclasses import replace
from threading import Event

from PySide6.QtCore import QObject, QTimer
from tool_contracts.api import AssetRef
from wb_tool.api import ArchiveRunEvidence, WBFigureProject, imported_run, project_runs

from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply


class ProjectArchiveSession(QObject):
    def __init__(
        self,
        store: AsyncStorage,
        project: WBFigureProject,
        cancellation: Event,
        finished: Callable[[tuple[ArchiveRunEvidence, ...]], None],
    ) -> None:
        super().__init__()
        self._store = store
        self._pending = list(project_runs(project))
        self._project = project
        self._result_asset: AssetRef | None = None
        self._cancel = cancellation
        self._finished = finished
        self._entries: list[ArchiveRunEvidence] = []
        self._request_id = ""
        self._callback: Callable[[StorageReply], None] | None = None

    def start(self) -> None:
        self._store.replied.connect(self._reply)
        self._next()

    def _submit(self, command: StorageCommand, callback: Callable[[StorageReply], None]) -> None:
        self._callback = callback
        try:
            self._request_id = self._store.submit(command)
        except (ValueError, RuntimeError) as error:
            self._fail(str(error))

    def _reply(self, reply: StorageReply) -> None:
        if reply.request_id != self._request_id:
            return
        self._request_id = ""
        if reply.error_code:
            self._fail(reply.message)
        elif self._callback:
            self._callback(reply)

    def _fail(self, message: str) -> None:
        self._entries[-1] = replace(self._entries[-1], error=message)
        QTimer.singleShot(0, self._next)

    def _next(self) -> None:
        if not self._pending or self._cancel.is_set():
            self._store.replied.disconnect(self._reply)
            self._finished(tuple(self._entries))
            return
        run = self._pending.pop(0)
        self._entries.append(ArchiveRunEvidence(run))
        history = imported_run(self._project, run)
        if history:
            if history.error or history.request is None:
                self._fail(history.error or "历史请求资产缺失")
                return
            self._result_asset = history.result
            self._asset(history.request, result=False)
            return
        self._result_asset = run.result

        def checked(reply: StorageReply) -> None:
            if reply.value != run:
                self._fail("项目运行引用与工作区记录不匹配")
                return
            self._asset(run.request, result=False)

        self._submit(StorageCommand("run", run_id=run.run_id), checked)

    def _asset(self, asset: AssetRef, *, result: bool) -> None:
        def resolved(reply: StorageReply) -> None:
            if not isinstance(reply.value, str):
                self._fail("无法解析运行资产路径")
                return
            entry = self._entries[-1]
            self._entries[-1] = replace(
                entry, **{"result_path" if result else "request_path": reply.value}
            )
            if not result and self._result_asset is not None and not self._cancel.is_set():
                self._asset(self._result_asset, result=True)
            else:
                self._next()

        self._submit(StorageCommand("asset", asset=asset), resolved)
