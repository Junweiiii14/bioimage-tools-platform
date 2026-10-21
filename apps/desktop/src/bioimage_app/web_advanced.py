"""Guarded web commands for existing WB use cases; no synthetic widget input."""

import json
from dataclasses import asdict, replace
from hashlib import sha256
from typing import TYPE_CHECKING, cast

from PySide6.QtWidgets import QFileDialog
from wb_tool.api import (
    FigureComposition,
    FigureLayoutStyle,
    FigureTemplate,
    MetadataBook,
    MetadataCell,
    MetadataEntry,
    MetadataKey,
    MetadataPreview,
    NormalizationPlan,
    ProjectOCRRow,
    ProjectOCRState,
    ReferenceKind,
    WBFigureProject,
    WBLayoutProject,
    WBNormalizedProject,
    WBProjectOCR,
    apply_workbench_metadata,
    bind_project_ocr_row,
    filename_metadata,
    initial_composition,
    make_normalization_plan,
    prepare_workbench_revision,
    preview_metadata,
    project_with_normalizations,
    project_with_ocr,
    revise_workbench_figure_order,
    with_figure_layout,
    workbench_project_digest,
)

if TYPE_CHECKING:
    from bioimage_app.web_bridge import WorkbenchBridge

FIELDS = ("project_name", "figure", "protein", "lane_count", "empty_lanes", "order", "notes")
TEMPLATE_FIELDS = {
    "name",
    "font_size",
    "label_width",
    "label_side",
    "crop_height",
    "row_gap",
    "figure_gap",
    "margin",
    "border",
    "columns",
    "dpi",
}


def text(value: object, limit: int = 2000) -> str:
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("文字格式无效或超过长度限制")
    return value


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("操作内容必须是对象")
    return cast(dict[str, object], value)


def items(value: object, limit: int = 512) -> list[object]:
    if not isinstance(value, list) or len(cast(list[object], value)) > limit:
        raise ValueError("操作列表无效或超过数量限制")
    return cast(list[object], value)


class AdvancedCommands:
    def __init__(self, bridge: "WorkbenchBridge") -> None:
        self.bridge = bridge
        self.book: MetadataBook | None = None
        self.preview: MetadataPreview | None = None
        self.response: dict[str, object] = {}
        self.waiting: tuple[str, str, int, str] | None = None
        self._saved = False
        self.tables: dict[str, object] = {}
        self.section = ""
        self._table_identity: tuple[object, ...] = ()
        self._book_header = (0, 0)
        self._committing = False
        self._preview_page = 0
        self._preview_serial = 0

    def snapshot(self) -> dict[str, object]:
        host = self.bridge.host
        project = host.view.project()
        if self._table_identity != host.advanced_evidence_identity:
            self.tables.clear()
        layout = project if isinstance(project, WBLayoutProject) else None
        return {
            "schema_version": 1,
            "projectId": project.project_id,
            "sessionEpoch": self.bridge.session_epoch,
            "revision": host.view.generation,
            "name": project.name,
            "busy": host.operation_busy,
            "rows": [
                {
                    "id": r.row_id,
                    "figure": r.figure,
                    "protein": r.protein,
                    "filename": r.filename,
                    "lanes": r.lane_count,
                    "reviewed": r.reviewed,
                    "source": r.source.sha256 if r.source else "",
                    "notes": r.notes,
                    "empty_lanes": list(r.empty_lanes),
                }
                for r in project.rows
            ],
            "template": project.template.model_dump(mode="json"),
            "figureOrder": list(project.figure_order),
            "style": (layout.layout_style if layout else FigureLayoutStyle()).model_dump(
                mode="json"
            ),
            "composition": (
                layout.composition if layout else initial_composition(project)
            ).model_dump(mode="json"),
            "ocr": project.ocr.model_dump(mode="json")
            if isinstance(project, WBProjectOCR) and project.ocr
            else None,
            "normalizations": [p.model_dump(mode="json") for p in project.normalizations]
            if isinstance(project, WBNormalizedProject)
            else [],
            "metadataPreview": self.preview_page(),
            "book": self.book_summary(),
            "persisted": host.current_draft_saved,
            "preparationOnly": project.schema_version == 10,
            "tables": self.tables,
        }

    def preview_page(self) -> dict[str, object] | None:
        if self.preview is None:
            return None
        offset = self._preview_page * 20
        return {
            "id": self._preview_serial,
            "source": self.preview.source,
            "total": len(self.preview.entries),
            "offset": offset,
            "pageSize": 20,
            "entries": [asdict(e) for e in self.preview.entries[offset : offset + 20]],
        }

    def book_summary(self) -> dict[str, object] | None:
        if self.book is None:
            return None
        sheet, row = self._book_header
        cells = self.book.sheets[sheet].rows[row] if self.book.sheets[sheet].rows else ()
        return {
            "sha256": self.book.sha256,
            "sheets": [{"name": s.name, "rowCount": len(s.rows)} for s in self.book.sheets],
            "header": {
                "sheet": sheet,
                "row": row,
                "cells": [{"text": c.text[:256], "error": c.error[:256]} for c in cells],
            },
        }

    def emit(self, request: str, status: str, error: str = "") -> None:
        self.response = {
            "requestId": request,
            "status": status,
            "error": error,
            "data": self.snapshot(),
        }
        self.bridge.advancedStateChanged.emit(json.dumps(self.response, ensure_ascii=False))

    def poll(self) -> None:
        if not self.waiting or self.bridge.host.operation_busy:
            return
        request, project_id, epoch, operation = self.waiting
        host = self.bridge.host
        if epoch != self.bridge.session_epoch:
            self.waiting = None
            return
        current = host.view.project()
        if current.project_id != project_id and operation != "template_import":
            self.waiting = None
            return
        error = host.operation_error
        if host.cancellation.is_set():
            error = error or "操作已取消；已提交历史保留。"
        if (
            not error
            and operation in {"font_import", "ocr_import", "template_import"}
            and not self._committing
        ):
            self._committing = True
            self._saved = False

            def saved_import() -> None:
                self._saved = True
                self.poll()

            host.save(after=saved_import)
            return
        if (
            operation.endswith("_apply")
            or operation
            in {
                "normalization_create",
                "normalization_remove",
                "font_import",
                "ocr_import",
                "template_import",
                "ocr_recognize",
                "ocr_composed",
            }
        ) and not self._saved:
            error = error or "未收到完整保存回执，编辑保留，请重试。"
        self.waiting = None
        self.emit(request, "failed" if error else "done", error)

    def command(self, data: dict[str, object]) -> None:
        request = text(data.get("requestId"), 80)
        if not request:
            raise ValueError("操作请求身份缺失")
        try:
            if data.get("schema_version") != 1:
                raise ValueError("高级工具接口版本不支持")
            host = self.bridge.host
            project = host.view.project()
            if (
                data.get("projectId") != project.project_id
                or data.get("sessionEpoch") != self.bridge.session_epoch
                or data.get("revision") != host.view.generation
            ):
                raise ValueError("项目或修订已改变；编辑已保留，请刷新后核对。")
            if host.operation_busy or host.is_closing:
                raise ValueError("当前任务仍在处理中，请等待或取消。")
            operation = text(data.get("operation"), 80)
            value = mapping(data.get("value", {}))
            if operation == "open":
                section = text(value.get("section"), 32)
                if section not in {"template", "metadata", "ocr", "normalization"}:
                    raise ValueError("未知高级工具")
                self.section = section
                self.emit(request, "done")
                return
            if not host.workspace_path:
                raise ValueError("请先打开或创建项目。")
            if operation == "metadata_headers":
                sheet, header = value.get("sheet"), value.get("header")
                if (
                    self.book is None
                    or type(sheet) is not int
                    or type(header) is not int
                    or not (
                        0 <= sheet < len(self.book.sheets)
                        and 0 <= header < len(self.book.sheets[sheet].rows)
                    )
                ):
                    raise ValueError("工作表或表头行不存在")
                self._book_header = (sheet, header)
                self.emit(request, "done")
                return
            if project.schema_version == 10 and operation.startswith(("ocr_", "normalization_")):
                raise ValueError("请先完成准备并开始处理，再使用 OCR 与归一化")
            updated: WBFigureProject | None = None
            if operation == "template_apply":
                raw = mapping(value.get("template"))
                if set(raw) - TEMPLATE_FIELDS:
                    raise ValueError("模板包含不可编辑字段")
                template = FigureTemplate.model_validate_json(
                    json.dumps({**project.template.model_dump(mode="json"), **raw})
                )
                ordered = revise_workbench_figure_order(
                    project,
                    tuple(text(v, 120) for v in items(value.get("figureOrder"))),
                    expected_digest=workbench_project_digest(project),
                )
                prepared = prepare_workbench_revision(
                    ordered,
                    expected_digest=workbench_project_digest(ordered),
                    impact="figures",
                    allow_group_edit=ordered != project,
                )
                updated = type(prepared).model_validate({**dict(prepared), "template": template})
                updated = with_figure_layout(
                    updated,
                    FigureComposition.model_validate_json(json.dumps(value.get("composition"))),
                    FigureLayoutStyle.model_validate_json(json.dumps(value.get("style"))),
                )
            elif operation == "metadata_preview":
                mode = value.get("mode")
                selected = tuple(text(v, 80) for v in items(value.get("rows")))
                if mode == "filename":
                    self.preview = filename_metadata(
                        project,
                        selected,
                        text(value.get("separator"), 8),
                        tuple(text(v, 32) for v in items(value.get("fields"), 20)),
                    )
                elif mode == "table":
                    if self.book is None:
                        raise ValueError("请先读取元信息表")
                    sheet, header, key = (
                        value.get("sheet"),
                        value.get("header"),
                        value.get("keyColumn"),
                    )
                    if (
                        type(sheet) is not int
                        or not 0 <= sheet < len(self.book.sheets)
                        or type(header) is not int
                        or type(key) is not int
                    ):
                        raise ValueError("工作表、表头或匹配列无效")
                    columns = mapping(value.get("columns"))
                    if any(type(v) is not int for v in columns.values()):
                        raise ValueError("映射列必须是整数")
                    self.preview = preview_metadata(
                        project,
                        self.book.sheets[sheet],
                        header,
                        cast(MetadataKey, text(value.get("keyKind"))),
                        key,
                        tuple((k, cast(int, v)) for k, v in columns.items()),
                        source=self.book.sha256,
                    )
                elif mode == "common":
                    if not selected or not set(selected) <= {r.row_id for r in project.rows}:
                        raise ValueError("请选择当前项目原图行")
                    values = mapping(value.get("common"))
                    if set(values) - set(FIELDS):
                        raise ValueError("未知元信息字段")
                    cells = tuple((k, MetadataCell(text(v))) for k, v in values.items())
                    self.preview = MetadataPreview(
                        sha256(project.model_dump_json().encode()).hexdigest(),
                        "共同值",
                        tuple(
                            MetadataEntry(i + 1, r.filename, (r.row_id,), r.row_id, cells)
                            for i, r in enumerate(project.rows)
                            if r.row_id in selected
                        ),
                    )
                else:
                    raise ValueError("请选择元信息来源")
                self._preview_page = 0
                self._preview_serial += 1
                self.emit(request, "done")
                return
            elif operation == "metadata_page":
                page = value.get("page")
                if (
                    self.preview is None
                    or value.get("previewId") != self._preview_serial
                    or type(page) is not int
                    or not 0 <= page < max(1, (len(self.preview.entries) + 19) // 20)
                ):
                    raise ValueError("预览已改变或页码无效，请重新生成预览")
                self._preview_page = page
                self.emit(request, "done")
                return
            elif operation == "metadata_apply":
                if self.preview is None:
                    raise ValueError("请先生成元信息预览")
                if value.get("previewId") != self._preview_serial:
                    raise ValueError("预览已改变，不能应用旧记录")
                entries: list[MetadataEntry] = []
                for raw_entry in items(value.get("entries")):
                    entry = mapping(raw_entry)
                    index = entry.get("index")
                    if type(index) is not int or not 0 <= index < len(self.preview.entries):
                        raise ValueError("预览记录身份无效")
                    original = self.preview.entries[index]
                    corrected = mapping(entry.get("values"))
                    cells = tuple(
                        (field, MetadataCell(text(corrected[field])))
                        if field in corrected
                        else (field, cell)
                        for field, cell in original.values
                    )
                    entries.append(
                        replace(original, target_id=text(entry.get("target"), 80), values=cells)
                    )
                updated = apply_workbench_metadata(
                    project,
                    self.preview,
                    tuple(entries),
                    tuple(text(v, 32) for v in items(value.get("fields"), 7)),
                )
            elif operation == "ocr_apply":
                if not isinstance(project, WBProjectOCR) or project.ocr is None:
                    raise ValueError("请先导入拼图或识别当前成图")
                originals = {r.row_id: r for r in project.ocr.rows}
                corrected_rows: list[ProjectOCRRow] = []
                bindings: list[tuple[str, str]] = []
                confirmations: dict[str, bool] = {}
                for item in items(value.get("rows")):
                    raw = mapping(item)
                    row_id = text(raw.get("row_id"), 80)
                    prior = originals.get(row_id, ProjectOCRRow(row_id=row_id))
                    confirmed = raw.get("confirmed")
                    if type(confirmed) is not bool:
                        raise ValueError("确认状态无效")
                    corrected_rows.append(
                        ProjectOCRRow(
                            row_id=row_id,
                            heading_token_id=prior.heading_token_id,
                            label_token_id=prior.label_token_id,
                            figure=text(raw.get("figure"), 512),
                            protein=text(raw.get("protein"), 512),
                            confirmed=False,
                            link=prior.link,
                        )
                    )
                    target = text(raw.get("target", ""), 80)
                    if target != (prior.link.target_row_id if prior.link else ""):
                        bindings.append((row_id, target))
                    confirmations[row_id] = confirmed
                ocr = ProjectOCRState.model_validate(
                    {**dict(project.ocr), "rows": tuple(corrected_rows)}
                )
                amended = project_with_ocr(
                    prepare_workbench_revision(
                        project, expected_digest=workbench_project_digest(project)
                    ),
                    ocr,
                )
                for row_id, target in bindings:
                    amended = bind_project_ocr_row(amended, row_id, target or None)
                assert amended.ocr is not None
                final_rows = tuple(
                    ProjectOCRRow.model_validate({**dict(r), "confirmed": confirmations[r.row_id]})
                    for r in amended.ocr.rows
                )
                updated = project_with_ocr(
                    amended,
                    ProjectOCRState.model_validate({**dict(amended.ocr), "rows": final_rows}),
                )
            elif operation in {
                "normalization_create",
                "normalization_apply",
                "normalization_remove",
            }:
                plans = project.normalizations if isinstance(project, WBNormalizedProject) else ()
                target = text(value.get("target"), 80)
                plan = None
                if operation == "normalization_create":
                    kind = text(value.get("kind"), 32)
                    if kind not in {"housekeeping", "phospho_total"}:
                        raise ValueError("请选择参照类型")
                    plan = make_normalization_plan(
                        project, target, text(value.get("reference"), 80), cast(ReferenceKind, kind)
                    )
                elif operation == "normalization_apply":
                    old = next((p for p in plans if p.target.row_id == target), None)
                    if old is None:
                        raise ValueError("样本关系已改变")
                    fields = mapping(value.get("plan"))
                    if set(fields) != {"kind", "control_mode", "pairs", "confirmed", "notes"}:
                        raise ValueError("样本对应配置字段无效")
                    plan = NormalizationPlan.model_validate_json(
                        json.dumps({**old.model_dump(mode="json"), **fields})
                    )
                updated = project_with_normalizations(
                    prepare_workbench_revision(
                        project, expected_digest=workbench_project_digest(project)
                    ),
                    tuple(p for p in plans if p.target.row_id != target)
                    + ((plan,) if plan else ()),
                )
            elif operation in {
                "metadata_import",
                "template_import",
                "template_export",
                "font_import",
                "ocr_import",
                "ocr_recognize",
                "ocr_composed",
                "template_preview",
                "figure_export",
                "ocr_export",
                "normalization_export",
                "tables_refresh",
            }:
                self._run_host(operation, request, value)
                return
            else:
                raise ValueError("未知高级工具操作")
            assert updated is not None
            generation = host.view.generation
            self.waiting = (request, project.project_id, self.bridge.session_epoch, operation)
            self._saved = False

            def saved() -> None:
                self._saved = True
                self.preview = None
                self.poll()

            host.save(
                after=saved,
                transform=lambda current: type(updated).model_validate(
                    {**dict(updated), "revision": current.revision}
                ),
                install_guard=lambda: (
                    host is self.bridge.host
                    and host.view.generation == generation
                    and not host.cancellation.is_set()
                ),
            )
            self.emit(request, "pending")
        except (ValueError, TypeError, OSError) as error:
            self.waiting = None
            self.emit(request, "failed", str(error))

    def _run_host(self, operation: str, request: str, value: dict[str, object]) -> None:
        host = self.bridge.host
        project = host.view.project()
        epoch = self.bridge.session_epoch
        generation = host.view.generation
        # All paths come from a system dialog, never from page-supplied arbitrary URLs.
        file = ""
        if operation in {"metadata_import", "template_import", "font_import", "ocr_import"}:
            filters = {
                "metadata_import": "Excel / CSV (*.xlsx *.csv)",
                "template_import": "WB 模板 (*.wbtemplate)",
                "font_import": "字体 (*.ttf *.otf *.ttc)",
                "ocr_import": "图像 (*.tif *.tiff *.png)",
            }
            file, _ = QFileDialog.getOpenFileName(host, "选择文件", "", filters[operation])
        elif operation in {
            "template_export",
            "figure_export",
            "ocr_export",
            "normalization_export",
        }:
            filters = {
                "template_export": "WB 模板 (*.wbtemplate)",
                "figure_export": "PNG (*.png);;TIFF (*.tif)",
                "ocr_export": "Excel (*.xlsx);;CSV (*.csv)",
                "normalization_export": "Excel (*.xlsx);;CSV (*.csv)",
            }
            file, _ = QFileDialog.getSaveFileName(
                host,
                "另存为新文件",
                "",
                filters[operation],
                options=QFileDialog.Option.DontConfirmOverwrite,
            )
        if operation.endswith(("_import", "_export")) and not file:
            self.waiting = None
            self.emit(request, "cancelled")
            return
        if (
            host is not self.bridge.host
            or generation != host.view.generation
            or epoch != self.bridge.session_epoch
        ):
            raise ValueError("文件选择期间项目已改变，请重试")
        self.waiting = (request, project.project_id, epoch, operation)
        host.operation_error = ""
        self._committing = False
        self._saved = False

        def saved_recognition() -> None:
            if host is self.bridge.host and epoch == self.bridge.session_epoch:
                self._saved = True

        if operation == "metadata_import":

            def received(book: MetadataBook) -> None:
                if (
                    host is self.bridge.host
                    and epoch == self.bridge.session_epoch
                    and generation == host.view.generation
                ):
                    self.book = book
                    self._book_header = (0, 0)
                    self.preview = None

            host.import_metadata(file, received=received)
        elif operation == "template_import":
            host.import_template(file)
        elif operation == "template_export":
            host.export_template(file)
        elif operation == "font_import":
            host.import_font(file)
        elif operation == "ocr_import":
            host.import_ocr_image(file)
        elif operation == "ocr_recognize":
            host.recognize_project(after=saved_recognition)
        elif operation == "ocr_composed":
            host.recognize_composed_figure(after=saved_recognition)
        elif operation == "template_preview":
            host.compose()
        elif operation == "figure_export":
            host.export_figure_image(file)
        elif operation in {"ocr_export", "normalization_export"}:
            host.export_project_table(
                file,
                ocr=operation == "ocr_export",
                normalization=operation == "normalization_export",
                ocr_labels=value.get("ocrLabels") is True,
            )
        elif operation == "tables_refresh":

            def tables_received(tables: object) -> None:
                from wb_tool.api import ProjectDerivedTables

                if isinstance(tables, ProjectDerivedTables):
                    self.tables = asdict(tables)
                    self._table_identity = host.advanced_evidence_identity

            host.read_advanced_tables(tables_received)
        self.emit(request, "pending")
