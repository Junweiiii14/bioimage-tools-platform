"""Project OCR assembly: frozen draft, owned process exit, committed asset and strict decode."""

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

from PySide6.QtCore import QObject, Signal
from tool_contracts.api import RunRecord
from wb_tool.api import (
    LoadedProjectOCR,
    OCRRequest,
    OCRStartFrame,
    WBJob,
    WBProjectOCR,
    WBReply,
    encode_ocr_frame,
)

from bioimage_app.run_session import RunCompletion, RunSession
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.wb_registration import OCRProcessCodec

if TYPE_CHECKING:
    from wb_tool.api import WBBackground


@dataclass(frozen=True)
class ProjectOCRCompletion:
    loaded: LoadedProjectOCR | None = None
    state: str = ""
    error: str = ""


class ProjectOCRSession(QObject):
    finished = Signal(object)

    def __init__(
        self, store: AsyncStorage, background: "WBBackground", parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._store, self._background = store, background
        self._storage_callbacks: dict[str, Callable[[StorageReply], None]] = {}
        self._wb_callbacks: dict[str, Callable[[WBReply], None]] = {}
        self._session: RunSession | None = None
        self._cancelled = self._started = False
        self._store.replied.connect(self._storage_reply)
        self._background.replied.connect(self._wb_reply)

    def start(self, project: WBProjectOCR, workspace: str, *, restore: bool = False) -> None:
        if self._started:
            raise RuntimeError("OCR会话不能重复开始")
        self._started = True
        self._project, self._workspace, self._restore = project, workspace, restore
        if restore:
            if project.ocr.run is None:
                self._finish(ProjectOCRCompletion(state="empty"))
            else:
                self._storage(StorageCommand("run", run_id=project.ocr.run.run_id), self._restored)
        else:
            self._storage(
                StorageCommand(
                    "prepare", document_id=project.project_id, revision=project.revision
                ),
                self._prepared,
            )

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
                self._finish(ProjectOCRCompletion(error=str(error)))

    def _wb_reply(self, reply: WBReply) -> None:
        callback = self._wb_callbacks.pop(reply.request_id, None)
        if callback:
            try:
                if reply.error:
                    raise ValueError(reply.error)
                callback(reply)
            except (ValueError, RuntimeError) as error:
                self._finish(ProjectOCRCompletion(error=str(error)))

    def _prepared(self, reply: StorageReply) -> None:
        if not isinstance(reply.value, RunRecord):
            raise ValueError("OCR运行记录无效")
        run = reply.value

        def decoded(response: WBReply) -> None:
            if response.value != self._project or run.revision != self._project.revision:
                raise ValueError("OCR冻结项目不一致")
            self._storage(
                StorageCommand("asset", asset=self._project.ocr.source),
                lambda source: self._launch(run, source),
            )

        self._wb(WBJob("figure_document", data=reply.data), decoded)

    def _launch(self, run: RunRecord, reply: StorageReply) -> None:
        if not isinstance(reply.value, str):
            raise ValueError("拼图资产路径无效")
        start = OCRStartFrame(
            protocol_version=1,
            kind="start",
            sequence=0,
            run_id=run.run_id,
            attempt_id=uuid4().hex,
            request_id=uuid4().hex,
            source_path=reply.value,
            request=OCRRequest(
                source_sha256=self._project.ocr.source.sha256, revision=self._project.revision
            ),
        )
        session = RunSession(self._store, run, OCRProcessCodec(start), self)
        self._session = session
        session.completed.connect(self._completed)
        command = (
            (sys.executable, "--worker", "wb_ocr")
            if "__compiled__" in globals()
            else (sys.executable, "-I", "-m", "bioimage_app", "--worker", "wb_ocr")
        )
        session.start(command, self._workspace, encode_ocr_frame(start))
        if self._cancelled:
            session.cancel()

    def _completed(self, completion: RunCompletion) -> None:
        session, self._session = self._session, None
        if session:
            session.deleteLater()
        if completion.error or completion.record is None:
            self._finish(ProjectOCRCompletion(error=completion.error or "OCR运行未提交"))
        elif completion.record.state != "succeeded":
            self._finish(ProjectOCRCompletion(state=completion.record.state))
        else:
            try:
                self._read_result(completion.record)
            except (ValueError, RuntimeError) as error:
                self._finish(ProjectOCRCompletion(error=str(error)))

    def _restored(self, reply: StorageReply) -> None:
        if not isinstance(reply.value, RunRecord) or reply.value != self._project.ocr.run:
            raise ValueError("OCR引用与工作区记录不一致")
        self._read_result(reply.value)

    def _read_result(self, run: RunRecord) -> None:
        if run.result is None:
            raise ValueError("OCR已提交资产缺失")

        def read(reply: StorageReply) -> None:
            def decoded(result: WBReply) -> None:
                if not isinstance(result.value, LoadedProjectOCR):
                    raise ValueError("OCR结果未通过校验")
                if self._restore and result.value.recognition != self._project.ocr.recognition:
                    raise ValueError("OCR原文副本与已提交资产不一致")
                self._finish(ProjectOCRCompletion(result.value, "succeeded"))

            self._wb(
                WBJob("project_ocr_result", document=self._project, ocr_run=run, data=reply.data),
                decoded,
            )

        self._storage(StorageCommand("read", asset=run.result), read)

    def _finish(self, completion: ProjectOCRCompletion) -> None:
        self._store.replied.disconnect(self._storage_reply)
        self._background.replied.disconnect(self._wb_reply)
        self.finished.emit(completion)
