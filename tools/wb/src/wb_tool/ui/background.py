"""Bounded one-shot background requests for preview and document/result codecs."""

from dataclasses import replace
from hashlib import file_digest
from math import ceil
from pathlib import Path
from uuid import uuid4

import numpy as np
from pydantic import TypeAdapter
from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot

from wb_tool.adapters.crop_export import export_crop
from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.adapters.worksheet_export import export_worksheet
from wb_tool.application.analysis import AnalysisResult
from wb_tool.application.crop_suggestions import CropSuggestion, read_figure_project
from wb_tool.application.desktop_data import PreviewRaster, ProjectDerivedTables, WBJob, WBReply
from wb_tool.application.document import WBDocument, WBWorksheetDocument, read_wb_document
from wb_tool.application.figure_project import FigurePNG, FigureRender, WBFigureProject
from wb_tool.application.figure_template import LoadedFigureTemplate
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    ProjectTableSnapshot,
    fill_project_table,
    read_project_result,
)
from wb_tool.application.project_metadata import MetadataBook
from wb_tool.application.project_normalization import (
    NormalizationSnapshot,
    WBNormalizedProject,
    fill_project_normalization,
)
from wb_tool.application.project_ocr import (
    LoadedProjectOCR,
    WBProjectOCR,
    fill_project_ocr_table,
    install_project_recognition,
    read_project_ocr_result,
)
from wb_tool.application.project_restore import RestoredProjectResults
from wb_tool.domain.worksheet import OCRRecognition


class _Work(QObject):
    replied = Signal(object)

    @Slot(str, object)
    def execute(self, request_id: str, job: WBJob) -> None:
        try:
            cancel = job.cancellation.is_set if job.cancellation is not None else lambda: False
            if (
                job.operation
                in ("project_export", "project_ocr_export", "project_normalization_export")
                and job.archive_runs is not None
            ):
                from wb_tool.adapters.project_evidence import verify_project_evidence

                if not isinstance(job.document, WBFigureProject):
                    raise ValueError("缺少项目文档")
                evidence = verify_project_evidence(job.document, job.archive_runs, cancelled=cancel)
                job = replace(
                    job, project_results=evidence.results, project_ocr_result=evidence.ocr
                )
            value: (
                PreviewRaster
                | WBDocument
                | WBWorksheetDocument
                | WBFigureProject
                | FigureRender
                | FigurePNG
                | LoadedFigureTemplate
                | MetadataBook
                | CropSuggestion
                | LoadedProjectResult
                | ProjectTableSnapshot
                | LoadedProjectOCR
                | ProjectDerivedTables
                | RestoredProjectResults
                | AnalysisResult
                | OCRRecognition
                | bytes
                | str
            )
            if job.operation == "project_evidence":
                from wb_tool.adapters.project_evidence import verify_project_evidence

                if not isinstance(job.document, WBFigureProject) or job.archive_runs is None:
                    raise ValueError("缺少项目证据")
                verified = verify_project_evidence(job.document, job.archive_runs, cancelled=cancel)
                value = RestoredProjectResults(
                    verified.results,
                    verified.ocr,
                    tuple(
                        str(record["reason"])
                        for record in verified.records
                        if record["verification"] == "unavailable"
                    ),
                )
            elif job.operation == "metadata_read":
                from wb_tool.adapters.metadata_input import read_metadata_file

                value = read_metadata_file(
                    job.path,
                    cancelled=job.cancellation.is_set if job.cancellation else lambda: False,
                )
            elif job.operation == "project_derived_tables":
                if not isinstance(job.document, WBProjectOCR):
                    raise ValueError("缺少项目派生结果配置")
                value = ProjectDerivedTables(
                    fill_project_ocr_table(
                        job.document, job.project_results, job.project_ocr_result
                    ),
                    fill_project_normalization(
                        job.document, job.project_results, job.project_ocr_result
                    )
                    if isinstance(job.document, WBNormalizedProject)
                    else NormalizationSnapshot(),
                )
            elif job.operation == "project_normalization_export":
                from wb_tool.adapters.normalization_export import export_project_normalization

                if not isinstance(job.document, WBNormalizedProject):
                    raise ValueError("缺少归一化配置")
                value = str(
                    export_project_normalization(
                        job.document,
                        job.project_results,
                        job.project_ocr_result,
                        job.destination,
                        ocr_labels=job.ocr_labels,
                        cancelled=cancel,
                    )
                )
            elif job.operation in (
                "project_ocr_result",
                "project_ocr_install",
                "project_ocr_table",
                "project_ocr_export",
            ):
                if not isinstance(job.document, WBProjectOCR):
                    raise ValueError("缺少项目OCR状态")
                if job.operation == "project_ocr_result":
                    if job.ocr_run is None:
                        raise ValueError("缺少OCR运行记录")
                    value = read_project_ocr_result(job.document, job.ocr_run, job.data)
                elif job.operation == "project_ocr_install":
                    if job.project_ocr_result is None:
                        raise ValueError("缺少已校验OCR结果")
                    value = install_project_recognition(job.document, job.project_ocr_result)
                elif job.operation == "project_ocr_export":
                    from wb_tool.adapters.project_ocr_export import export_project_ocr_table

                    value = str(
                        export_project_ocr_table(
                            job.document,
                            job.project_results,
                            job.project_ocr_result,
                            job.destination,
                            cancelled=cancel,
                        )
                    )
                else:
                    value = ProjectTableSnapshot(
                        fill_project_ocr_table(
                            job.document, job.project_results, job.project_ocr_result
                        )
                    )
            elif job.operation == "project_result":
                if job.analysis_plan is None:
                    raise ValueError("缺少结果所属定量计划")
                value = read_project_result(job.analysis_plan, job.data)
            elif job.operation in ("project_table", "project_export"):
                if not isinstance(job.document, WBFigureProject):
                    raise ValueError("缺少项目文档")
                if job.operation == "project_export":
                    from wb_tool.adapters.project_export import export_project_table

                    value = str(
                        export_project_table(
                            job.document, job.project_results, job.destination, cancelled=cancel
                        )
                    )
                else:
                    value = ProjectTableSnapshot(
                        fill_project_table(job.document, job.project_results)
                    )
            elif job.operation == "crop_suggest":
                from wb_tool.adapters.crop_suggestions import suggest_crops

                if job.detection_settings is None:
                    raise ValueError("缺少候选检测参数")
                value = suggest_crops(
                    job.path,
                    job.source_sha256,
                    job.row_id,
                    job.revision,
                    job.detection_settings,
                    cancelled=job.cancellation.is_set if job.cancellation else lambda: False,
                )
            elif job.operation in ("template_read", "template_export"):
                from wb_tool.adapters.figure_template_io import (
                    export_figure_template,
                    read_figure_template,
                )

                if job.operation == "template_read":
                    value = read_figure_template(job.path, cancelled=cancel)
                else:
                    if not isinstance(job.document, WBFigureProject):
                        raise ValueError("缺少模板所属项目")
                    value = export_figure_template(
                        job.document, job.sources, job.destination, cancelled=cancel
                    )
            elif job.operation == "font_digest":
                path = Path(job.path)
                if (
                    path.suffix.lower() not in (".ttf", ".ttc", ".otf")
                    or path.stat().st_size > 32 * 1024 * 1024
                ):
                    raise ValueError("请选择不超过 32 MiB 的字体文件")
                with path.open("rb") as stream:
                    value = file_digest(stream, "sha256").hexdigest()
            elif job.operation == "figure_document":
                value = read_figure_project(job.data)
            elif job.operation == "figure_image_export":
                from wb_tool.adapters.figure_image_export import export_figure_image

                if not isinstance(job.document, WBFigureProject):
                    raise ValueError("缺少拼图项目")
                value = export_figure_image(
                    job.document, job.sources, job.destination, cancelled=cancel
                )
            elif job.operation in ("figure_preview", "figure_export", "figure_ocr"):
                from wb_tool.adapters.figure_export import (
                    encode_figure_png,
                    export_figure_bundle,
                    render_figure,
                )

                if not isinstance(job.document, WBFigureProject):
                    raise ValueError("缺少拼图项目")
                cancel = job.cancellation.is_set if job.cancellation is not None else lambda: False
                if job.operation == "figure_ocr":
                    rendered = render_figure(job.document, job.sources, cancelled=cancel)
                    if cancel():
                        raise ValueError("生成拼图已取消")
                    value = encode_figure_png(rendered, job.document.template.dpi)
                    if cancel():
                        raise ValueError("生成拼图已取消")
                elif job.operation == "figure_preview":
                    from PIL import Image

                    value = render_figure(
                        job.document, job.sources, require_review=False, cancelled=cancel
                    )
                    if max(value.width, value.height) > 2048:
                        preview = Image.frombytes("RGB", (value.width, value.height), value.rgb)
                        preview.thumbnail((2048, 2048), Image.Resampling.NEAREST)
                        value = FigureRender(
                            preview.width, preview.height, preview.tobytes(), value.manifest_json
                        )
                else:
                    value = export_figure_bundle(
                        job.document,
                        job.sources,
                        job.destination,
                        cancelled=cancel,
                        runs=job.archive_runs or (),
                    )
            elif job.operation == "ocr_preview":
                from wb_tool.adapters.ocr_input import load_ocr_image

                ocr_image = load_ocr_image(job.path)
                height, width = ocr_image.pixels.shape
                step = max(1, ceil(max(height, width) / 2048))
                sampled = ocr_image.pixels[::step, ::step]
                ph, pw = sampled.shape
                value = PreviewRaster(
                    ocr_image.sha256,
                    width,
                    height,
                    pw,
                    ph,
                    sampled.tobytes(),
                    ocr_image.bit_depth,
                    ocr_image.warnings,
                )
            elif job.operation == "preview":
                if not 1 <= job.preview_edge <= 2048:
                    raise ValueError("预览边长必须位于 1..2048")
                image = load_tiff(job.path)
                height, width = image.pixels.shape
                step = max(1, ceil(max(height, width) / job.preview_edge))
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
