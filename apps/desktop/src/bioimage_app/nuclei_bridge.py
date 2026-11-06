"""Single-image research UI; WorkflowSession owns all model execution and commits."""

import base64
import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from nuclei_tool.api import NucleiInput, original_png, read_nuclei_input, verify_model
from platform_runtime.api import WorkspaceError
from PySide6.QtCore import QObject, QSettings, QStandardPaths, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import QDialog, QFileDialog, QTextBrowser, QVBoxLayout, QWidget
from tool_contracts.api import ExecutionPlan

from bioimage_app.nuclei_cli import prepare
from bioimage_app.nuclei_results import NucleiResult, export_result, read_result
from bioimage_app.nuclei_workflow_host import NucleiHost
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus


class _ImageIO(QThread):
    """One bounded image read/export; no database connection crosses threads."""

    def __init__(
        self,
        operation: Callable[[], NucleiResult | tuple[NucleiInput, bytes] | str],
        parent: QObject,
    ) -> None:
        super().__init__(parent)
        self.operation = operation
        self.value: NucleiResult | tuple[NucleiInput, bytes] | str | None = None
        self.error = ""

    def run(self) -> None:
        try:
            self.value = self.operation()
        except (
            ValueError,
            OSError,
            EOFError,
            RuntimeError,
            WorkspaceError,
            sqlite3.Error,
        ) as error:
            self.error = str(error)


class NucleiBridge(QObject):
    changed = Signal(str)
    idle = Signal()

    def __init__(
        self, window: QWidget, settings: QSettings, unavailable: Callable[[], bool]
    ) -> None:
        super().__init__(window)
        self.window, self.settings, self.unavailable = window, settings, unavailable
        self._io: _ImageIO | None = None
        self._session: WorkflowSession | None = None
        self._closing = False
        self._cancelled = False
        self._source = ""
        self._source_hash = ""
        self._workspace = ""
        self._result: NucleiResult | None = None
        self._original = ""
        self._overlay = ""
        self._message = "选择一张原始 TIFF，开始核分割。"
        self._state = "empty"
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
    def help(self) -> None:
        dialog = QDialog(self.window)
        dialog.setWindowTitle("核分割准备指南")
        dialog.resize(800, 620)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser(dialog)
        text.setMarkdown(
            (Path(__file__).parent / "web_ui" / "nuclei_setup.md").read_text(encoding="utf-8")
        )
        layout.addWidget(text)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.show()

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
                    "original": self._original,
                    "overlay": self._overlay,
                    "count": result.display.count if result else None,
                    "run_id": result.run_id if result else "",
                    "workspace": self._workspace,
                    "source_sha256": result.source_sha256 if result else self._source_hash,
                    "worker": str(self.settings.value("nuclei_worker_v1", "")),
                    "model": str(self.settings.value("nuclei_model_v1", "")),
                },
                ensure_ascii=False,
            )
        )

    def _publish_error(self, message: str) -> None:
        self._state, self._message = "failed", message
        self.refresh()

    @Slot(str)
    def choose(self, action: str) -> None:
        if self.busy or self._closing or self.unavailable():
            self._message = "请等待当前任务完成，或先取消运行。"
            self.refresh()
            return
        if action == "worker":
            path, _ = QFileDialog.getOpenFileName(self.window, "选择已准备的核分割运行程序")
            if path:
                self.settings.setValue("nuclei_worker_v1", path)
        elif action == "model":
            path = QFileDialog.getExistingDirectory(self.window, "选择 2D_versatile_fluo 模型目录")
            if path:
                self.settings.setValue("nuclei_model_v1", path)
        elif action == "source":
            path, _ = QFileDialog.getOpenFileName(
                self.window, "选择单张 8 位灰度原图", "", "原始 TIFF (*.tif *.tiff)"
            )
            if path:

                def read() -> tuple[NucleiInput, bytes]:
                    source = read_nuclei_input(path)
                    return source, original_png(source)

                self._start_io(read, "source", path)
        elif action == "open":
            path = QFileDialog.getExistingDirectory(self.window, "打开核分割项目目录")
            if path:
                self._start_io(lambda: read_result(path), "result", path)
        elif action == "export":
            result = self._result
            if result is not None:
                path = QFileDialog.getExistingDirectory(self.window, "选择导出位置（另建结果目录）")
                if path:
                    self._start_io(lambda: export_result(result, path), "export", path)
        self.settings.sync()
        if self.settings.status() != QSettings.Status.NoError:
            self._publish_error("设置未能保存，请检查用户目录权限后重试。")
        else:
            self.refresh()

    def _start_io(
        self,
        operation: Callable[[], NucleiResult | tuple[NucleiInput, bytes] | str],
        purpose: str,
        path: str,
    ) -> None:
        job = _ImageIO(operation, self)
        self._io = job
        self._message = "正在读取并核验…" if purpose != "export" else "正在导出…"
        job.finished.connect(lambda: self._io_finished(job, purpose, path))
        job.start()
        self.refresh()

    def _io_finished(self, job: _ImageIO, purpose: str, path: str) -> None:
        self._io = None
        job.deleteLater()
        if self._closing:
            self.idle.emit()
            return
        if job.error:
            self._publish_error("操作未完成：" + job.error)
        elif purpose == "source":
            assert isinstance(job.value, tuple)
            source, png = job.value
            self._source, self._source_hash = path, source.sha256
            self._result, self._workspace, self._overlay = None, "", ""
            self._original = self._data_url(png)
            self._state, self._message = "ready", "原图已就绪，点击开始分析。"
        elif purpose == "result":
            assert isinstance(job.value, NucleiResult)
            result = job.value
            self._result, self._workspace = result, result.workspace
            self._source, self._source_hash = "", result.source_sha256
            self._original = self._data_url(result.display.original_png)
            self._overlay = self._data_url(result.display.overlay_png)
            self._state, self._message = "succeeded", "结果已保存。可导出或关闭后重新打开项目。"
        else:
            assert isinstance(job.value, str)
            self._message = "已导出至：" + job.value
        self.refresh()
        self.idle.emit()

    @staticmethod
    def _data_url(data: bytes) -> str:
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")

    @Slot()
    def run(self) -> None:
        if self.busy or self._closing or self.unavailable() or not self._source:
            return
        worker = str(self.settings.value("nuclei_worker_v1", ""))
        model = str(self.settings.value("nuclei_model_v1", ""))
        if not worker or not model:
            self._publish_error("尚未配置运行环境和模型。打开“运行设置”，选择已准备的两个位置。")
            return
        try:
            host = NucleiHost(worker, model)
        except (ValueError, OSError) as error:
            self._publish_error("运行环境不可用，请在运行设置重新选择：" + str(error))
            return
        source, expected = self._source, self._source_hash
        parent = Path(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        )
        workspace = parent / "BioImage" / "Projects" / ("Nuclei-" + uuid4().hex[:12])
        self._workspace = str(workspace)

        def initialize() -> ExecutionPlan:
            verify_model(model)
            workspace.parent.mkdir(parents=True, exist_ok=True)
            return prepare(workspace, source, host, expected_sha256=expected)

        session = WorkflowSession(host.registry, self)
        self._session, self._cancelled = session, False
        self._state, self._message = "running", "正在分析，完成后自动保存…"
        session.changed.connect(self._progress)
        session.completed.connect(self._completed)
        session.finished.connect(self._finished)
        session.initialize(str(workspace), initialize)
        self._deadline.start(300_000)
        self.refresh()

    @Slot(object)
    def _completed(self, _status: WorkflowStatus) -> None:
        assert self._session is not None
        self._session.close()

    @Slot(object)
    def _progress(self, status: WorkflowStatus) -> None:
        if self._cancelled:
            self._message = "正在取消，等待运行进程退出…"
        elif status.message:
            self._message = status.message
        elif status.state == "succeeded":
            self._message = "正在核验已保存结果…"
        self.refresh()

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
                    attempt.run.reason
                    for attempt in reversed(ledger.attempts)
                    if attempt.run is not None and attempt.run.reason
                ),
                reason,
            )
        self._state = "cancelled" if status.state == "cancelled" else "failed"
        self._message = (
            "已取消，未发布本次结果。可重新开始。"
            if self._state == "cancelled"
            else "分析未完成，可检查运行设置后重试：" + reason
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
