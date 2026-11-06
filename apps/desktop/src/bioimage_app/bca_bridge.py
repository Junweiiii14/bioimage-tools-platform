"""BCA desktop input and presentation; execution uses the existing host session."""

import csv
import hashlib
import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from bca_tool.api import PlateRecord
from platform_runtime.api import WorkspaceError
from PySide6.QtCore import QObject, QStandardPaths, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QWidget
from tool_contracts.api import ExecutionPlan

from bioimage_app.bca_cli import prepare
from bioimage_app.bca_results import BcaResult, export_result, read_result
from bioimage_app.bca_workflow_host import BcaHost
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus


class _PlateIO(QThread):
    def __init__(self, operation: Callable[[], BcaResult | str], parent: QObject) -> None:
        super().__init__(parent)
        self.operation = operation
        self.value: BcaResult | str = ""
        self.error = ""

    def run(self) -> None:
        try:
            self.value = self.operation()
        except (ValueError, OSError, csv.Error, WorkspaceError, sqlite3.Error) as error:
            self.error = str(error)


class BcaBridge(QObject):
    changed = Signal(str)
    recordLoaded = Signal(str)
    idle = Signal()

    def __init__(self, window: QWidget, unavailable: Callable[[], bool]) -> None:
        super().__init__(window)
        self.window, self.unavailable = window, unavailable
        self._io: _PlateIO | None = None
        self._session: WorkflowSession | None = None
        self._closing = False
        self._cancelled = False
        self._source = ""
        self._source_hash = ""
        self._workspace = ""
        self._result: BcaResult | None = None
        self._state, self._message = "empty", "选择单板 CSV，填写或加载板记录。"
        self._deadline = QTimer(self)
        self._deadline.setSingleShot(True)
        self._deadline.timeout.connect(self.cancel)

    @property
    def busy(self) -> bool:
        return self._io is not None or self._session is not None

    @property
    def resources_closed(self) -> bool:
        return not self.busy

    @Slot()
    def refresh(self) -> None:
        result = self._result
        self.changed.emit(
            json.dumps(
                {
                    "state": self._state,
                    "message": self._message,
                    "busy": self.busy,
                    "running": self._session is not None,
                    "source": Path(self._source).name,
                    "source_sha256": self._source_hash,
                    "workspace": self._workspace,
                    "result": None
                    if result is None
                    else {
                        "wells": result.table("wells"),
                        "samples": result.table("samples"),
                        "run_id": result.run_id,
                        "source_sha256": result.source_sha256,
                        "workspace": result.workspace,
                        "provenance": json.loads(result.members["provenance"]),
                    },
                },
                ensure_ascii=False,
            )
        )

    def _error(self, message: str) -> None:
        self._state, self._message = "failed", message
        self.refresh()

    @Slot(str)
    def choose(self, action: str) -> None:
        if self.busy or self._closing or self.unavailable():
            self._error("请等待当前任务完成，或先取消运行。")
            return
        if action in {"source", "record"}:
            path, _ = QFileDialog.getOpenFileName(
                self.window,
                "选择单板 CSV" if action == "source" else "加载板记录",
                "",
                "CSV (*.csv)" if action == "source" else "板记录 (*.json)",
            )
            if path:

                def read() -> str:
                    if action == "source":
                        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
                    return PlateRecord.model_validate_json(
                        Path(path).read_bytes()
                    ).model_dump_json()

                self._start_io(read, action, path)
        elif action == "open":
            path = QFileDialog.getExistingDirectory(self.window, "打开 BCA 项目目录")
            if path:
                self._start_io(lambda: read_result(path), "result", path)
        elif action == "export" and self._result is not None:
            result = self._result
            path = QFileDialog.getExistingDirectory(self.window, "选择导出位置（另建结果目录）")
            if path:
                self._start_io(lambda: export_result(result, path), "export", path)

    def _start_io(self, operation: Callable[[], BcaResult | str], purpose: str, path: str) -> None:
        job = _PlateIO(operation, self)
        self._io = job
        self._message = "正在导出…" if purpose == "export" else "正在读取并核验…"
        job.finished.connect(lambda: self._io_finished(job, purpose, path))
        job.start()
        self.refresh()

    def _io_finished(self, job: _PlateIO, purpose: str, path: str) -> None:
        self._io = None
        job.deleteLater()
        if self._closing:
            self.idle.emit()
            return
        if job.error:
            self._error("操作未完成：" + job.error)
        elif purpose == "result":
            assert isinstance(job.value, BcaResult)
            self._result = job.value
            self._workspace = job.value.workspace
            self._source, self._source_hash = "", ""
            self._state, self._message = "succeeded", "结果已保存并核验。可导出或关闭后重开。"
        elif purpose == "source":
            assert isinstance(job.value, str)
            self._source, self._source_hash = path, job.value
            self._state, self._message = "ready", "CSV 已选择，请核对板记录后开始分析。"
        elif purpose == "record":
            assert isinstance(job.value, str)
            self.recordLoaded.emit(job.value)
            self._message = "板记录已加载，请核对来源与实际实验记录。"
        else:
            assert isinstance(job.value, str)
            self._message = "已导出至：" + job.value
        self.refresh()
        self.idle.emit()

    @Slot(str)
    def run(self, record_json: str) -> None:
        if self.busy or self._closing or self.unavailable() or not self._source:
            return
        try:
            record = PlateRecord.model_validate_json(record_json)
            if record.source_sha256 != self._source_hash:
                raise ValueError("板记录与所选 CSV 摘要不一致，请选择对应文件或核对新板记录")
        except ValueError as error:
            self._error("板记录未就绪：" + str(error))
            return
        parent = Path(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        )
        workspace = parent / "BioImage" / "Projects" / ("BCA-" + uuid4().hex[:12])
        source, host = self._source, BcaHost()
        self._workspace = str(workspace)

        def initialize() -> ExecutionPlan:
            workspace.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(prefix="bioimage-bca-record-") as directory:
                path = Path(directory) / "record.json"
                path.write_text(record.model_dump_json(), encoding="utf-8")
                return prepare(workspace, source, str(path), host)

        session = WorkflowSession(host.registry, self)
        self._session, self._cancelled = session, False
        self._state, self._message = "running", "正在分析，完成后自动保存…"
        session.changed.connect(self._progress)
        session.completed.connect(self._completed)
        session.finished.connect(self._finished)
        session.initialize(str(workspace), initialize)
        self._deadline.start(60_000)
        self.refresh()

    @Slot(object)
    def _progress(self, status: WorkflowStatus) -> None:
        if self._cancelled:
            self._message = "正在取消，等待运行进程退出…"
        elif status.state == "succeeded":
            self._message = "正在核验已保存结果…"
        elif status.message:
            self._message = status.message
        self.refresh()

    @Slot(object)
    def _completed(self, _status: WorkflowStatus) -> None:
        assert self._session is not None
        self._session.close()

    @Slot(object)
    def _finished(self, status: WorkflowStatus) -> None:
        self._deadline.stop()
        session = self._session
        assert session is not None
        ledger = session.ledger
        self._session = None
        session.deleteLater()
        if self._closing:
            self.idle.emit()
            return
        if status.state == "succeeded" and not status.message:
            path = self._workspace
            self._start_io(lambda: read_result(path), "result", path)
            return
        reason = status.message
        if ledger is not None:
            reason = ledger.reason or next(
                (
                    a.run.reason
                    for a in reversed(ledger.attempts)
                    if a.run is not None and a.run.reason
                ),
                reason,
            )
        self._state = "cancelled" if status.state == "cancelled" else "failed"
        self._message = (
            "已取消，未发布本次结果。" if self._state == "cancelled" else "分析未完成：" + reason
        )
        self.refresh()
        self.idle.emit()

    @Slot()
    def cancel(self) -> None:
        if self._session is not None:
            self._cancelled = True
            self._session.cancel()
            self._message = "正在取消，等待运行进程退出…"
            self.refresh()

    def close(self) -> None:
        self._closing = True
        if self._session is not None:
            self._session.close()
        elif self._io is None:
            self.idle.emit()
