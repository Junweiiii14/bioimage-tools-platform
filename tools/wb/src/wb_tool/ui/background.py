"""Bounded one-shot background requests for preview and document/result codecs."""

from math import ceil
from uuid import uuid4

import numpy as np
from pydantic import TypeAdapter
from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot

from wb_tool.adapters.crop_export import export_crop
from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.adapters.worksheet_export import export_worksheet
from wb_tool.application.analysis import AnalysisResult
from wb_tool.application.desktop_data import PreviewRaster, WBJob, WBReply
from wb_tool.application.document import WBDocument, WBWorksheetDocument, read_wb_document
from wb_tool.domain.worksheet import OCRRecognition


class _Work(QObject):
    replied = Signal(object)

    @Slot(str, object)
    def execute(self, request_id: str, job: WBJob) -> None:
        try:
            value: (
                PreviewRaster
                | WBDocument
                | WBWorksheetDocument
                | AnalysisResult
                | OCRRecognition
                | bytes
                | str
            )
            if job.operation == "preview":
                image = load_tiff(job.path)
                height, width = image.pixels.shape
                step = max(1, ceil(max(height, width) / 2048))
                sampled = image.pixels[::step, ::step]
                display = (sampled // 257).astype(np.uint8) if image.bit_depth == 16 else sampled
                ph, pw = display.shape
                value = PreviewRaster(
                    image.sha256,
                    width,
                    height,
                    pw,
                    ph,
                    display.tobytes(),
                    image.bit_depth,
                    image.warnings,
                )
            elif job.operation == "document":
                value = read_wb_document(job.data)
            elif job.operation == "result":
                value = TypeAdapter(AnalysisResult).validate_json(job.data, strict=True)
            elif job.operation == "ocr_result":
                value = TypeAdapter(OCRRecognition).validate_json(job.data, strict=True)
            elif job.operation == "stored_result":
                value = TypeAdapter(AnalysisResult | OCRRecognition).validate_json(
                    job.data, strict=True
                )
            elif job.operation == "export":
                if job.worksheet is None or job.result is None:
                    raise ValueError("缺少已复核工作表/测量")
                value = str(export_worksheet(job.worksheet, job.result, job.path))
            elif job.operation == "crop":
                if job.crop is None:
                    raise ValueError("缺少原图裁剪范围")
                value = export_crop(job.path, job.crop, job.destination)
            else:
                if job.document is None:
                    raise ValueError("缺少文档")
                value = job.document.model_dump_json().encode("utf-8")
            reply = WBReply(request_id, value)
        except (ValueError, OSError, TypeError) as error:
            reply = WBReply(request_id, error=str(error))
        self.replied.emit(reply)


class WBBackground(QObject):
    replied = Signal(object)
    closed = Signal()
    _requested = Signal(str, object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread = QThread(self)
        self._work = _Work()
        self._work.moveToThread(self._thread)
        self._requested.connect(self._work.execute, Qt.ConnectionType.QueuedConnection)
        self._work.replied.connect(self._reply, Qt.ConnectionType.QueuedConnection)
        self._thread.finished.connect(self._work.deleteLater)
        self._thread.finished.connect(self._thread_stopped)
        self._pending: set[str] = set()
        self._closing = False
        self._thread.start()

    def submit(self, job: WBJob) -> str:
        if QThread.currentThread() != self.thread():
            raise RuntimeError("WB 后台端口只能由所属 GUI 线程调用")
        if self._closing or len(self._pending) >= 8 or len(job.data) > 16 * 1024 * 1024:
            raise RuntimeError("WB 后台队列不可用或超出预算")
        request_id = uuid4().hex
        self._pending.add(request_id)
        self._requested.emit(request_id, job)
        return request_id

    @Slot(object)
    def _reply(self, reply: WBReply) -> None:
        self._pending.discard(reply.request_id)
        self.replied.emit(reply)
        if self._closing and not self._pending:
            self._thread.quit()

    def shutdown(self) -> None:
        if QThread.currentThread() != self.thread():
            raise RuntimeError("WB 后台端口只能由所属 GUI 线程关闭")
        self._closing = True
        if not self._pending:
            self._thread.quit()

    @Slot()
    def _thread_stopped(self) -> None:
        if not self._thread.wait(0):
            QTimer.singleShot(1, self._thread_stopped)
            return
        self.closed.emit()
