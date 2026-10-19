"""Reviewed composite labels and explicit links to multi-source quantitative rows."""

from dataclasses import dataclass, replace
from hashlib import sha256

from pydantic import Field, TypeAdapter, model_validator
from tool_contracts.api import AssetRef, RunRecord

from wb_tool.application.crop_suggestions import WBReviewProject
from wb_tool.application.document import DocumentIO, check_document_json
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.ocr_protocol import OCRResultFrame
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    ProjectCellStatus,
    ProjectTableCell,
    WBAnalysisProject,
    fill_project_table,
)
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.worksheet import OCRRecognition, suggest_figures


class ProjectOCRLink(DocumentIO):
    target_row_id: str = Field(min_length=1, max_length=80)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    crop: LaneROI
    lane_count: int = Field(ge=1, le=96)

    @model_validator(mode="after")
    def identity(self) -> "ProjectOCRLink":
        if self.crop.lane_id != self.target_row_id or self.crop.x1 - self.crop.x0 < self.lane_count:
            raise ValueError("OCR关联的行/网格身份无效")
        return self


class ProjectOCRRow(DocumentIO):
    row_id: str = Field(min_length=1, max_length=80)
    heading_token_id: str | None = None
    label_token_id: str | None = None
    figure: str = Field(default="", max_length=512)
    protein: str = Field(default="", max_length=512)
    confirmed: bool = False
    link: ProjectOCRLink | None = None

    @model_validator(mode="after")
    def named(self) -> "ProjectOCRRow":
        if self.confirmed and (not self.figure.strip() or not self.protein.strip()):
            raise ValueError("确认OCR行必须填写Fig和蛋白名")
        return self


class ProjectOCRState(DocumentIO):
    source: AssetRef
    filename: str = Field(min_length=1, max_length=512)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    run: RunRecord | None = None
    recognition: OCRRecognition | None = None
    rows: tuple[ProjectOCRRow, ...] = Field(default=(), max_length=512)

    @model_validator(mode="after")
    def evidence(self) -> "ProjectOCRState":
        if (self.run is None) != (self.recognition is None):
            raise ValueError("OCR识别副本必须伴随已提交运行")
        if self.run is not None and (
            self.run.state != "succeeded" or self.run.tool_id != "wb-figure"
        ):
            raise ValueError("项目OCR只引用已提交成功的识别")
        tokens: set[str] = set()
        if self.recognition is not None:
            if self.recognition.source_sha256 != self.source.sha256 or (
                self.recognition.width,
                self.recognition.height,
            ) != (self.width, self.height):
                raise ValueError("OCR识别来源/尺寸不符")
            assert self.run is not None
            validate_ocr_recognition(self.recognition, self.run.revision)
            tokens = {token.token_id for token in self.recognition.tokens}
        if len({r.row_id for r in self.rows}) != len(self.rows):
            raise ValueError("OCR行身份重复")
        for row in self.rows:
            if any(
                key is not None and key not in tokens
                for key in (row.heading_token_id, row.label_token_id)
            ):
                raise ValueError("OCR行引用不存在的原文token")
        return self


class WBProjectOCR(WBAnalysisProject):
    schema_version: int = Field(default=4, ge=4, le=4)
    ocr: ProjectOCRState | None = None

    @model_validator(mode="after")
    def owned(self) -> "WBProjectOCR":
        if self.ocr is None and self.schema_version == 4:
            raise ValueError("v4项目必须包含OCR状态")
        run = self.ocr.run if self.ocr else None
        if run is not None and (run.document_id != self.project_id or run.revision > self.revision):
            raise ValueError("OCR运行不属于此项目/修订")
        return self


def project_with_ocr(project: WBFigureProject, ocr: ProjectOCRState) -> WBProjectOCR:
    if isinstance(project, WBProjectOCR):
        fields = {name: getattr(project, name) for name in type(project).model_fields}
        fields["ocr"] = ocr
        return type(project).model_validate(fields)
    return WBProjectOCR(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        rows=project.rows,
        figure_order=project.figure_order,
        template=project.template,
        suggestions=project.suggestions if isinstance(project, WBReviewProject) else (),
        analyses=project.analyses if isinstance(project, WBAnalysisProject) else (),
        ocr=ocr,
    )


def require_project_ocr(project: WBProjectOCR) -> ProjectOCRState:
    if project.ocr is None:
        raise ValueError("请先导入独立拼图")
    return project.ocr


def bind_project_ocr_row(
    project: WBProjectOCR, ocr_row_id: str, target_row_id: str | None
) -> WBProjectOCR:
    ocr = require_project_ocr(project)
    if ocr_row_id not in {r.row_id for r in ocr.rows}:
        raise ValueError("请选择已有OCR行")
    link = None
    if target_row_id is not None:
        row = next((r for r in project.rows if r.row_id == target_row_id), None)
        if row is None or row.source is None or row.roi is None or not row.reviewed:
            raise ValueError("请选择有原图且裁剪已审核的项目行")
        link = ProjectOCRLink(
            target_row_id=row.row_id,
            source_sha256=row.source.sha256,
            crop=row.roi,
            lane_count=row.lane_count,
        )
    rows = tuple(
        r.model_copy(update={"link": link, "confirmed": False}) if r.row_id == ocr_row_id else r
        for r in ocr.rows
    )
    return project_with_ocr(project, ocr.model_copy(update={"rows": rows}))


def ocr_link_is_current(project: WBFigureProject, link: ProjectOCRLink) -> bool:
    row = next((r for r in project.rows if r.row_id == link.target_row_id), None)
    return bool(
        row
        and row.reviewed
        and row.source
        and row.source.sha256 == link.source_sha256
        and row.roi == link.crop
        and row.lane_count == link.lane_count
    )


def validate_ocr_recognition(recognition: OCRRecognition, revision: int) -> None:
    OCRResultFrame(
        protocol_version=1,
        kind="result",
        sequence=2,
        run_id="project",
        attempt_id="project",
        request_id="project",
        revision=revision,
        result=recognition,
    )


@dataclass(frozen=True)
class LoadedProjectOCR:
    run: RunRecord
    recognition: OCRRecognition


def read_project_ocr_result(project: WBProjectOCR, run: RunRecord, data: bytes) -> LoadedProjectOCR:
    ocr = require_project_ocr(project)
    if (
        run.state != "succeeded"
        or run.result is None
        or run.tool_id != "wb-figure"
        or run.document_id != project.project_id
        or run.revision > project.revision
    ):
        raise ValueError("OCR运行不是此项目的已提交结果")
    if (
        len(data) > 4 * 1024 * 1024
        or len(data) != run.result.size_bytes
        or sha256(data).hexdigest() != run.result.sha256
    ):
        raise ValueError("OCR结果资产大小/摘要不一致")
    check_document_json(data)
    result = TypeAdapter(OCRRecognition).validate_json(data, strict=True)
    validate_ocr_recognition(result, run.revision)
    if result.source_sha256 != ocr.source.sha256 or (result.width, result.height) != (
        ocr.width,
        ocr.height,
    ):
        raise ValueError("OCR结果不是当前拼图")
    return LoadedProjectOCR(run, result)


def install_project_recognition(project: WBProjectOCR, loaded: LoadedProjectOCR) -> WBProjectOCR:
    ocr = require_project_ocr(project)
    rows = tuple(
        ProjectOCRRow(
            row_id=token.token_id,
            heading_token_id=figure.heading.token_id,
            label_token_id=token.token_id,
            figure=figure.heading.text[:512],
            protein=token.text[:512],
        )
        for figure in suggest_figures(loaded.recognition)
        for token in figure.rows
    )
    state = ProjectOCRState(
        source=ocr.source,
        filename=ocr.filename,
        width=ocr.width,
        height=ocr.height,
        run=loaded.run,
        recognition=loaded.recognition,
        rows=rows,
    )
    return project_with_ocr(project, state)


def fill_project_ocr_table(
    project: WBProjectOCR, results: tuple[LoadedProjectResult, ...], loaded: LoadedProjectOCR | None
) -> tuple[ProjectTableCell, ...]:
    if project.ocr is None:
        return ()
    measurements = {(c.row_id, c.lane_index): c for c in fill_project_table(project, results)}
    evidence_valid = bool(
        loaded and loaded.run == project.ocr.run and loaded.recognition == project.ocr.recognition
    )
    cells: list[ProjectTableCell] = []
    for row in project.ocr.rows:
        link = row.link
        for index in range(1, (link.lane_count if link else 1) + 1):
            measurement = measurements.get((link.target_row_id, index)) if link else None
            status: ProjectCellStatus | None = None
            reason = ""
            if not evidence_valid:
                status, reason = "ocr_unavailable", "OCR运行/结果尚未校验"
            elif not row.confirmed:
                status, reason = "unconfirmed", "Fig/蛋白名称与关联尚未确认"
            elif link is None:
                status, reason = "unbound", "未关联原图行"
            elif not ocr_link_is_current(project, link):
                status, reason = "stale", "关联原图/裁剪/固定N已改变，请重新关联"
            if not status and measurement:
                cells.append(
                    replace(measurement, row_id=row.row_id, figure=row.figure, protein=row.protein)
                )
            else:
                cells.append(
                    ProjectTableCell(
                        row.row_id,
                        row.figure,
                        row.protein,
                        index,
                        link.source_sha256 if link else "",
                        "",
                        "target",
                        None,
                        "",
                        None,
                        status or "unbound",
                        reason or "对应测量不存在",
                    )
                )
    return tuple(cells)
