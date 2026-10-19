"""Explicit WB desktop assembly; numerical behavior remains in wb_tool.api."""

import sys
from collections.abc import Callable
from contextlib import suppress
from uuid import uuid4

from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolBar,
)
from tool_contracts.api import AssetRef, DraftSnapshot, RunRecord
from wb_tool.api import (
    AnalysisResult,
    PreviewRaster,
    StartFrame,
    WBDocument,
    WBJob,
    WBReply,
    create_wb_background,
    create_wb_view,
    encode_worker_frame,
)

from bioimage_app.run_session import RunCompletion, RunSession
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.wb_registration import WBProcessCodec


class WBWindow(QMainWindow):
    """One workspace per window. Close waits for save, process and both background threads."""

    closed = Signal()

    @property
    def resources_closed(self) -> bool:
        return self._store_closed and self._background_closed

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WB 自动化 · 图像与定量复核")
        self.resize(1200, 900)
        self.view = create_wb_view()
        self.setCentralWidget(self.view)
        self._store = AsyncStorage(self)
        self._background = create_wb_background()
        self._store.replied.connect(self._storage_reply)
        self._background.replied.connect(self._wb_reply)
        self._storage_callbacks: dict[str, Callable[[StorageReply], None]] = {}
        self._wb_callbacks: dict[str, Callable[[WBReply], None]] = {}
        self._workspace = ""
        self._asset: AssetRef | None = None
        self._document_id = ""
        self._saved_revision: int | None = None
        self._saved_generation = -1
        self._session: RunSession | None = None
        self._busy = False
        self._closing = False
        self._shutting_down = False
        self._store_closed = False
        self._background_closed = False
        self._store.closed.connect(self._storage_closed)
        self._background.closed.connect(self._wb_closed)
        toolbar = QToolBar("工作区与图像")
        self.addToolBar(toolbar)
        self.create_button = QPushButton("新建工作区")
        self.open_button = QPushButton("打开工作区")
        self.import_button = QPushButton("导入 TIFF")
        self.documents = QComboBox()
        self.documents.setMinimumWidth(230)
        for widget in (self.create_button, self.open_button, self.import_button, self.documents):
            toolbar.addWidget(widget)
        self.create_button.clicked.connect(self._choose_create)
        self.open_button.clicked.connect(self._choose_open)
        self.import_button.clicked.connect(self._choose_import)
        self.documents.activated.connect(self._choose_document)
        self.view.changed.connect(self._edited)
        self.view.save_requested.connect(self.save)
        self.view.analyze_requested.connect(self.analyze)
        self.view.cancel_requested.connect(self.cancel)
        self._controls()

    def _controls(self) -> None:
        idle = not self._busy and not self._closing
        self.create_button.setEnabled(not self._workspace and idle)
        self.open_button.setEnabled(not self._workspace and idle)
        self.import_button.setEnabled(bool(self._workspace) and idle and self._session is None)
        self.documents.setEnabled(idle and self._session is None)
        self.view.setEnabled(idle)
        self.view.save_button.setEnabled(bool(self._asset) and idle)
        self.view.analyze_button.setEnabled(bool(self._asset) and idle and self._session is None)
        self.view.cancel_button.setEnabled(self._session is not None and not self._closing)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._controls()

    def _error(self, message: str) -> None:
        self._set_busy(False)
        self._closing = False
        self.view.status.setText("操作失败：" + message)
        self._controls()

    def _storage(self, command: StorageCommand, callback: Callable[[StorageReply], None]) -> None:
        try:
            request_id = self._store.submit(command)
            self._storage_callbacks[request_id] = callback
        except (ValueError, RuntimeError) as error:
            self._error(str(error))

    def _wb(self, job: WBJob, callback: Callable[[WBReply], None]) -> None:
        try:
            request_id = self._background.submit(job)
            self._wb_callbacks[request_id] = callback
        except (ValueError, RuntimeError) as error:
            self._error(str(error))

    def _storage_reply(self, reply: StorageReply) -> None:
        callback = self._storage_callbacks.pop(reply.request_id, None)
        if callback is None or self._shutting_down:
            return
        if reply.error_code:
            self._error(reply.message)
        else:
            callback(reply)

    def _wb_reply(self, reply: WBReply) -> None:
        callback = self._wb_callbacks.pop(reply.request_id, None)
        if callback is None or self._shutting_down:
            return
        if reply.error:
            self._error(reply.error)
        else:
            callback(reply)

    def _choose_create(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择新建工作区的空目录")
        if path:
            self.open_workspace(path, create=True)

    def _choose_open(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "打开工作区")
        if path:
            self.open_workspace(path)

    def open_workspace(self, path: str, *, create: bool = False) -> None:
        if self._workspace or self._busy:
            self._error("此窗口已有工作区；请另开一个窗口")
            return
        self._set_busy(True)

        def opened(reply: StorageReply) -> None:
            self._workspace = path
            self.setWindowTitle("WB 自动化 · " + path)
            self._storage(StorageCommand("documents"), self._documents_loaded)

        self._storage(StorageCommand("create" if create else "open", path=path), opened)

    def _documents_loaded(self, reply: StorageReply) -> None:
        self.documents.clear()
        self.documents.addItem("选择已保存文档", "")
        if isinstance(reply.value, tuple):
            for document in reply.value:
                if isinstance(document, DraftSnapshot) and document.tool_id == "wb":
                    self.documents.addItem(document.document_id, document.document_id)
        self._set_busy(False)
        self.view.status.setText("工作区已打开；导入图像或选择已保存文档。")

    def _choose_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "导入原始 TIFF", "", "TIFF (*.tif *.tiff)")
        if path:
            self.import_image(path)

    def _may_replace(self) -> bool:
        if self._asset is not None and self._saved_generation != self.view.generation:
            return (
                QMessageBox.question(self, "未保存修改", "放弃当前未保存修改并切换图像？")
                == QMessageBox.StandardButton.Yes
            )
        return True

    def import_image(self, path: str) -> None:
        if (
            not self._workspace
            or self._busy
            or self._session is not None
            or not self._may_replace()
        ):
            return
        self._set_busy(True)

        def previewed(reply: WBReply) -> None:
            if not isinstance(reply.value, PreviewRaster):
                self._error("预览消息无效")
                return
            raster = reply.value

            def imported(reply: StorageReply) -> None:
                if not isinstance(reply.value, AssetRef):
                    self._error("输入资产无效")
                    return
                self._asset = reply.value
                self._document_id = uuid4().hex
                self._saved_revision = None
                self.view.set_image(raster)
                self._saved_generation = self.view.generation
                self._set_busy(False)

            self._storage(
                StorageCommand("import", path=path, source_sha256=raster.sha256), imported
            )

        self._wb(WBJob("preview", path=path), previewed)

    def _edited(self) -> None:
        self.view.status.setText("有未保存修改；计算将先保存当前标注。")

    def save(self, *, after: Callable[[], None] | None = None) -> None:
        if self._busy or self._asset is None:
            return
        revision = 0 if self._saved_revision is None else self._saved_revision + 1
        try:
            document = WBDocument(source=self._asset, request=self.view.request(revision))
        except ValueError as error:
            self._error(str(error))
            return
        generation = self.view.generation
        self._set_busy(True)

        def encoded(reply: WBReply) -> None:
            if not isinstance(reply.value, bytes):
                self._error("文档编码失败")
                return

            def saved(reply: StorageReply) -> None:
                self._saved_revision = revision
                self._saved_generation = generation
                self._set_busy(False)
                self.view.status.setText(f"草稿已保存 · 修订 {revision}")
                if self.documents.findData(self._document_id) < 0:
                    self.documents.addItem(self._document_id, self._document_id)
                if after is not None:
                    after()

            self._storage(
                StorageCommand(
                    "save",
                    document_id=self._document_id,
                    tool_id="wb",
                    revision=revision,
                    previous_revision=self._saved_revision,
                    data=reply.value,
                ),
                saved,
            )

        self._wb(WBJob("encode", document=document), encoded)

    def analyze(self) -> None:
        if self._session is not None or self._busy:
            return
        self.save(after=self._prepare)

    def _prepare(self) -> None:
        self._set_busy(True)
        self._storage(StorageCommand("prepare", document_id=self._document_id), self._prepared)

    def _prepared(self, reply: StorageReply) -> None:
        if not isinstance(reply.value, RunRecord):
            self._error("运行记录无效")
            return
        run = reply.value

        def decoded(reply: WBReply) -> None:
            if not isinstance(reply.value, WBDocument):
                self._error("运行文档无效")
                return
            document = reply.value

            def resolved(reply: StorageReply) -> None:
                if not isinstance(reply.value, str):
                    self._error("运行资产路径无效")
                    return
                start = StartFrame(
                    protocol_version=1,
                    kind="start",
                    sequence=0,
                    run_id=run.run_id,
                    attempt_id=uuid4().hex,
                    request_id=uuid4().hex,
                    source_path=reply.value,
                    request=document.request,
                )
                session = RunSession(self._store, run, WBProcessCodec(start), self)
                self._session = session
                generation = self.view.generation

                def completed(completion: RunCompletion) -> None:
                    self._completed(completion, generation)

                session.completed.connect(completed)
                command = (
                    (sys.executable, "--worker", "wb")
                    if "__compiled__" in globals()
                    else (sys.executable, "-I", "-m", "bioimage_app", "--worker", "wb")
                )
                session.start(
                    command,
                    self._workspace,
                    encode_worker_frame(start),
                )
                self._set_busy(False)
                self.view.status.setText("正在后台计算；可以继续编辑或取消。")

            self._storage(StorageCommand("asset", asset=document.source), resolved)

        self._wb(WBJob("document", data=reply.data), decoded)

    def cancel(self) -> None:
        if self._session is not None:
            self._session.cancel()
            self.view.status.setText("正在取消，等待进程退出确认…")

    def _completed(self, completion: RunCompletion, generation: int) -> None:
        session = self._session
        self._session = None
        if session is not None:
            # Completion follows observed process exit and decoder shutdown.
            session.deleteLater()
        self._controls()
        if self._closing:
            self._close_after_run()
            return
        if completion.error or completion.record is None:
            self._error(completion.error or "结果未保存")
        elif completion.record.state == "succeeded":
            terminal = completion.outcome.terminal
            if terminal is not None:
                self._wb(
                    WBJob("result", data=terminal.data),
                    lambda reply: self._result(reply, generation),
                )
        else:
            self.view.status.setText("运行状态：" + completion.record.state)

    def _result(self, reply: WBReply, generation: int) -> None:
        matches = False
        if isinstance(reply.value, AnalysisResult):
            with suppress(ValueError):
                matches = reply.value.request == self.view.request(reply.value.request.revision)
        if (
            generation == self.view.generation
            and matches
            and isinstance(reply.value, AnalysisResult)
        ):
            self.view.show_result(reply.value)
        else:
            self.view.status.setText("历史结果已保存；当前标注已改变，请重新计算。")

    def _choose_document(self, index: int) -> None:
        document_id = self.documents.itemData(index)
        if isinstance(document_id, str) and document_id:
            self.load_document(document_id)

    def load_document(self, document_id: str) -> None:
        if self._busy or self._session is not None or not self._may_replace():
            return
        self._set_busy(True)

        def loaded(reply: StorageReply) -> None:
            def decoded(reply: WBReply) -> None:
                if not isinstance(reply.value, WBDocument):
                    self._error("WB 文档无效")
                    return
                document = reply.value

                def resolved(reply: StorageReply) -> None:
                    if not isinstance(reply.value, str):
                        self._error("文档输入路径无效")
                        return

                    def previewed(reply: WBReply) -> None:
                        if (
                            not isinstance(reply.value, PreviewRaster)
                            or reply.value.sha256 != document.source.sha256
                        ):
                            self._error("文档来源已损坏")
                            return
                        self._asset = document.source
                        self._document_id = document_id
                        self._saved_revision = document.request.revision
                        self.view.set_image(reply.value, document.request)
                        self._saved_generation = self.view.generation
                        self._set_busy(False)
                        self._storage(
                            StorageCommand("runs", document_id=document_id), self._history
                        )

                    self._wb(WBJob("preview", path=reply.value), previewed)

                self._storage(StorageCommand("asset", asset=document.source), resolved)

            self._wb(WBJob("document", data=reply.data), decoded)

        self._storage(StorageCommand("load", document_id=document_id), loaded)

    def _history(self, reply: StorageReply) -> None:
        if not isinstance(reply.value, tuple):
            return
        generation = self.view.generation
        for run in reversed(reply.value):
            if (
                isinstance(run, RunRecord)
                and run.state == "succeeded"
                and run.revision == self._saved_revision
                and run.result is not None
            ):
                self._storage(
                    StorageCommand("read", asset=run.result),
                    lambda reply: self._wb(
                        WBJob("result", data=reply.data),
                        lambda reply, generation=generation: self._result(reply, generation),
                    ),
                )
                break

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._store_closed and self._background_closed:
            event.accept()
            return
        event.ignore()
        if self._busy:
            self.view.status.setText("操作正在完成，请稍后关闭。")
            return
        self._closing = True
        if self._session is not None:
            self.cancel()
        else:
            self._close_after_run()
        self._controls()

    def _close_after_run(self) -> None:
        if self._asset is not None and self._saved_generation != self.view.generation:
            try:
                self.view.request(0)
            except ValueError:
                answer = QMessageBox.question(
                    self,
                    "当前修改不能保存",
                    "当前标注无效。放弃未保存修改并关闭？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer == QMessageBox.StandardButton.Yes:
                    self._shutdown()
                else:
                    self._closing = False
                    self._controls()
                return
            self.save(after=self._shutdown)
        else:
            self._shutdown()

    def _shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._background.shutdown()
        self._store.shutdown()

    def _storage_closed(self) -> None:
        self._store_closed = True
        if self._background_closed:
            self.close()
            self.closed.emit()

    def _wb_closed(self) -> None:
        self._background_closed = True
        if self._store_closed:
            self.close()
            self.closed.emit()
