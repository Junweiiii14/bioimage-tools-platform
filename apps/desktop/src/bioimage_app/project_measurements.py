"""Sequential WB project runs, using committed assets and the existing process lifecycle."""

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

from PySide6.QtCore import QObject, QTimer, Signal
from tool_contracts.api import RunRecord
from wb_tool.api import (
    LoadedProjectResult,
    ProjectRowAnalysis,
    StartFrame,
    WBAnalysisProject,
    WBJob,
    WBReply,
    encode_worker_frame,
    record_project_run,
)

from bioimage_app.run_session import RunCompletion, RunSession
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.wb_registration import WBProcessCodec

if TYPE_CHECKING:
    from wb_tool.api import WBBackground


@dataclass(frozen=True)
class ProjectBatchCompletion:
    project: WBAnalysisProject
    results: tuple[LoadedProjectResult, ...]
    errors: tuple[str, ...]
    cancelled: bool


class ProjectMeasurementSession(QObject):
    progress = Signal(str)
    finished = Signal(object)

    def __init__(
        self, store: AsyncStorage, background: "WBBackground", parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._store, self._background = store, background
        self._storage_callbacks: dict[str, Callable[[StorageReply], None]] = {}
        self._wb_callbacks: dict[str, Callable[[WBReply], None]] = {}
        self._session: RunSession | None = None
        self._cancelled = False
        self._started = False
        self._restore = False
        self._pending: list[ProjectRowAnalysis] = []
        self._results: list[LoadedProjectResult] = []
        self._errors: list[str] = []
        self._loaded_bytes = 0
        self._store.replied.connect(self._storage_reply)
        self._background.replied.connect(self._wb_reply)

    def start(
        self,
        project: WBAnalysisProject,
        row_ids: tuple[str, ...],
        workspace: str,
        *,
        restore: bool = False,
    ) -> None:
        if self._started:
            raise RuntimeError("项目运行会话不能重复启动")
        self._started = True
        self._project = self._frozen = project
        self._workspace, self._restore = workspace, restore
        self._pending = [p for p in project.analyses if p.row_id in row_ids]
        self._next()

    def cancel(self) -> None:
        self._cancelled = True
        if self._session:
            self._session.cancel()

    def _storage(self, command: StorageCommand, callback: Callable[[StorageReply], None]) -> None:
        self._storage_callbacks[self._store.submit(command)] = callback

    def _wb(self, job: WBJob, callback: Callable[[WBReply], None]) -> None:
        self._wb_callbacks[self._background.submit(job)] = callback

    def _storage_reply(self, reply: StorageReply) -> None:
        callback = self._storage_callbacks.pop(reply.request_id, None)
        if callback:
            try:
                if reply.error_code:
                    raise ValueError(reply.message)
                callback(reply)
            except (ValueError, RuntimeError) as error:
                self._failed(str(error))

    def _wb_reply(self, reply: WBReply) -> None:
        callback = self._wb_callbacks.pop(reply.request_id, None)
        if callback:
            try:
                if reply.error:
                    raise ValueError(reply.error)
                callback(reply)
            except (ValueError, RuntimeError) as error:
                self._failed(str(error))

    def _failed(self, error: str) -> None:
        self._errors.append(error)
        # A failed row does not fabricate a value or stop later independent sources.
        QTimer.singleShot(0, self._next)

    def _check_run(self, plan: ProjectRowAnalysis, reply: StorageReply) -> None:
        if not isinstance(reply.value, RunRecord) or reply.value != plan.run:
            raise ValueError(f"{plan.row_id} 的运行引用与工作区历史不一致")
        self._read_result(plan)

    def _next(self) -> None:
        if self._cancelled or not self._pending:
            self._finish()
            return
        plan = self._pending.pop(0)
        self.progress.emit(
            f"{'校验结果' if self._restore else '计算'}：{plan.row_id}；"
            f"剩余 {len(self._pending)} 行"
        )
        if self._restore:
            if plan.run is None:
                QTimer.singleShot(0, self._next)
            else:
                self._storage(
                    StorageCommand("run", run_id=plan.run.run_id),
                    lambda reply: self._check_run(plan, reply),
                )
        else:
            self._storage(
                StorageCommand(
                    "prepare", document_id=self._frozen.project_id, revision=self._frozen.revision
                ),
                lambda reply: self._prepared(plan, reply),
            )

    def _prepared(self, plan: ProjectRowAnalysis, reply: StorageReply) -> None:
        if not isinstance(reply.value, RunRecord):
            raise ValueError("运行准备未返回记录")
        run = reply.value

        def decoded(decoded_reply: WBReply) -> None:
            if decoded_reply.value != self._frozen or run.revision != plan.request.revision:
                raise ValueError("冻结项目与定量请求不一致")
            row = next(r for r in self._frozen.rows if r.row_id == plan.row_id)
            if row.source is None:
                raise ValueError("定量原图缺失")
            self._storage(
                StorageCommand("asset", asset=row.source),
                lambda resolved: self._launch(plan, run, resolved),
            )

        self._wb(WBJob("figure_document", data=reply.data), decoded)

    def _launch(self, plan: ProjectRowAnalysis, run: RunRecord, reply: StorageReply) -> None:
        if not isinstance(reply.value, str):
            raise ValueError("定量原图路径无效")
        start = StartFrame(
            protocol_version=1,
            kind="start",
            sequence=0,
            run_id=run.run_id,
            attempt_id=uuid4().hex,
            request_id=uuid4().hex,
            source_path=reply.value,
            request=plan.request,
        )
        session = RunSession(self._store, run, WBProcessCodec(start), self)
        self._session = session

        def completed(completion: RunCompletion) -> None:
            self._completed(plan, completion)

        session.completed.connect(completed)
        command = (
            (sys.executable, "--worker", "wb")
            if "__compiled__" in globals()
            else (sys.executable, "-I", "-m", "bioimage_app", "--worker", "wb")
        )
        session.start(command, self._workspace, encode_worker_frame(start))
        if self._cancelled:
            session.cancel()

    def _completed(self, plan: ProjectRowAnalysis, completion: RunCompletion) -> None:
        session, self._session = self._session, None
        if session:
            session.deleteLater()
        try:
            if completion.error or completion.record is None:
                raise ValueError(completion.error or "运行未提交")
            self._project = record_project_run(
                self._project, plan.row_id, plan.request, completion.record
            )
            updated = next(p for p in self._project.analyses if p.row_id == plan.row_id)
            self._read_result(updated)
        except (ValueError, RuntimeError) as error:
            self._failed(str(error))

    def _read_result(self, plan: ProjectRowAnalysis) -> None:
        if plan.run is None or plan.run.state != "succeeded" or plan.run.result is None:
            QTimer.singleShot(0, self._next)
            return
        if self._loaded_bytes + plan.run.result.size_bytes > 64 * 1024 * 1024:
            self._failed("本次结果曲线超过 64 MiB 显示预算，未载入的结果保留在历史")
            return

        def read(reply: StorageReply) -> None:
            self._loaded_bytes += len(reply.data)

            def decoded(result: WBReply) -> None:
                if not isinstance(result.value, LoadedProjectResult):
                    raise ValueError("已提交结果解码失败")
                self._results.append(result.value)
                self._next()

            self._wb(WBJob("project_result", data=reply.data, analysis_plan=plan), decoded)

        self._storage(StorageCommand("read", asset=plan.run.result), read)

    def _finish(self) -> None:
        self._store.replied.disconnect(self._storage_reply)
        self._background.replied.disconnect(self._wb_reply)
        self.finished.emit(
            ProjectBatchCompletion(
                self._project, tuple(self._results), tuple(self._errors), self._cancelled
            )
        )
