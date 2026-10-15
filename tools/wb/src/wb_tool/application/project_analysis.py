"""Multi-source plans and verified result references; original numerical contracts are reused."""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Literal

from pydantic import Field, TypeAdapter, model_validator
from tool_contracts.api import RunRecord

from wb_tool.application.analysis import (
    AnalysisRequest,
    AnalysisResult,
    BandAnnotation,
    LaneAnnotation,
)
from wb_tool.application.crop_suggestions import WBReviewProject
from wb_tool.application.document import DocumentIO, check_document_json
from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.worker_protocol import ResultFrame
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI, Polarity


class ProjectRowAnalysis(DocumentIO):
    row_id: str = Field(min_length=1, max_length=80)
    crop: LaneROI
    empty_lanes: tuple[int, ...] = ()
    request: AnalysisRequest
    run: RunRecord | None = None

    @model_validator(mode="after")
    def coherent(self) -> "ProjectRowAnalysis":
        lanes = self.request.lanes
        if self.crop.lane_id != self.row_id or not 1 <= len(lanes) <= 96:
            raise ValueError("项目定量行身份/泳道数无效")
        expected = fixed_lane_grid(self.crop, len(lanes))
        if tuple(lane.roi for lane in lanes) != expected:
            raise ValueError("项目定量必须保留已配置的固定N网格与顺序")
        if len(set(self.empty_lanes)) != len(self.empty_lanes) or any(
            not 1 <= n <= len(lanes) for n in self.empty_lanes
        ):
            raise ValueError("空泳道编号无效")
        for index, lane in enumerate(lanes, 1):
            if len(lane.bands) != 1 or lane.bands[0].band_id != "target":
                raise ValueError("项目每泳道须有一个稳定target条带")
            band = lane.bands[0]
            if index in self.empty_lanes and band.included:
                raise ValueError("预标空泳道必须排除，不能伪造有效零值")
            if band.bounds is not None and band.bounds.right >= self.crop.y1 - self.crop.y0:
                raise ValueError("条带边界超出整行裁剪高度")
        if self.run is not None:
            if self.run.state not in ("succeeded", "failed", "interrupted", "cancelled"):
                raise ValueError("项目仅引用已提交终态，运行中的候选不能填表")
            if self.run.revision != self.request.revision or self.run.tool_id != "wb-figure":
                raise ValueError("运行来源类型/请求修订不一致")
        return self


class WBAnalysisProject(WBReviewProject):
    schema_version: int = Field(default=3, ge=3, le=3)
    analyses: tuple[ProjectRowAnalysis, ...] = Field(default=(), max_length=512)

    @model_validator(mode="after")
    def analyses_match(self) -> "WBAnalysisProject":
        rows = {r.row_id: r for r in self.rows}
        if len({p.row_id for p in self.analyses}) != len(self.analyses):
            raise ValueError("同一行不能重复保存当前定量计划")
        for plan in self.analyses:
            if plan.row_id not in rows:
                raise ValueError("定量计划所属行不存在")
            if plan.request.revision > self.revision:
                raise ValueError("定量计划不能来自未来修订")
            if plan.run is not None and plan.run.document_id != self.project_id:
                raise ValueError("定量运行不属于该项目")
        return self


def analysis_is_current(project: WBFigureProject, plan: ProjectRowAnalysis) -> bool:
    from wb_tool.application.automatic import row_is_ready

    row = next((r for r in project.rows if r.row_id == plan.row_id), None)
    return bool(
        row
        and row_is_ready(project, row)
        and row.source
        and row.source.sha256 == plan.request.source_sha256
        and row.roi == plan.crop
        and row.lane_count == len(plan.request.lanes)
        and row.empty_lanes == plan.empty_lanes
        and 2 <= plan.crop.y1 - plan.crop.y0 <= 4096
        and plan.crop.y1 - plan.crop.y0 == project.crop_height_for(row)
    )


def project_with_analyses(
    project: WBFigureProject, analyses: tuple[ProjectRowAnalysis, ...]
) -> WBAnalysisProject:
    if isinstance(project, WBAnalysisProject):
        fields = {name: getattr(project, name) for name in type(project).model_fields}
        fields["analyses"] = analyses
        return type(project).model_validate(fields)
    return WBAnalysisProject(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        rows=project.rows,
        figure_order=project.figure_order,
        template=project.template,
        suggestions=project.suggestions if isinstance(project, WBReviewProject) else (),
        analyses=analyses,
    )


def make_row_analysis(
    project: WBFigureProject, row_id: str, polarity: Polarity
) -> ProjectRowAnalysis:
    row = next((r for r in project.rows if r.row_id == row_id), None)
    from wb_tool.application.automatic import row_is_ready

    if row is None or row.source is None or row.roi is None or not row_is_ready(project, row):
        raise ValueError("请先确认有原图的行及裁剪范围")
    if (
        not 2 <= row.roi.y1 - row.roi.y0 <= 4096
        or row.roi.y1 - row.roi.y0 != project.crop_height_for(row)
    ):
        raise ValueError("裁剪高度与当前模板不一致，请重新复核")
    lanes = tuple(
        LaneAnnotation(roi, (BandAnnotation("target", None, included=i not in row.empty_lanes),))
        for i, roi in enumerate(fixed_lane_grid(row.roi, row.lane_count), 1)
    )
    return ProjectRowAnalysis(
        row_id=row_id,
        crop=row.roi,
        empty_lanes=row.empty_lanes,
        request=AnalysisRequest(row.source.sha256, project.revision, polarity, lanes),
    )


def set_row_analysis(project: WBFigureProject, plan: ProjectRowAnalysis) -> WBAnalysisProject:
    plan = ProjectRowAnalysis(
        row_id=plan.row_id,
        crop=plan.crop,
        empty_lanes=plan.empty_lanes,
        request=plan.request,
        run=plan.run,
    )
    if not analysis_is_current(project, plan):
        raise ValueError("定量计划与当前原图/裁剪/泳道或审核状态不一致")
    previous = project.analyses if isinstance(project, WBAnalysisProject) else ()
    return project_with_analyses(project, (*(p for p in previous if p.row_id != plan.row_id), plan))


def update_row_analysis_request(
    project: WBAnalysisProject, row_id: str, request: AnalysisRequest
) -> WBAnalysisProject:
    """Parameter edits clear the current run; immutable historical runs remain in storage."""
    plan = next((p for p in project.analyses if p.row_id == row_id), None)
    if plan is None:
        raise ValueError("请先配置该行定量")
    if request == plan.request:
        return project
    if (
        request.source_sha256 != plan.request.source_sha256
        or request.revision != plan.request.revision
        or tuple(lane.roi for lane in request.lanes)
        != tuple(lane.roi for lane in plan.request.lanes)
    ):
        raise ValueError("参数编辑不能更换来源、固定网格或运行修订")
    updated = ProjectRowAnalysis(
        row_id=row_id, crop=plan.crop, empty_lanes=plan.empty_lanes, request=request
    )
    return project_with_analyses(
        project, tuple(updated if p.row_id == row_id else p for p in project.analyses)
    )


def prepare_project_analyses(
    project: WBAnalysisProject, row_ids: tuple[str, ...], revision: int
) -> WBAnalysisProject:
    if (
        not row_ids
        or len(set(row_ids)) != len(row_ids)
        or set(row_ids) - {p.row_id for p in project.analyses}
    ):
        raise ValueError("请选择已配置且不重复的定量行")
    if type(revision) is not int or revision < project.revision:
        raise ValueError("不能用旧修订覆盖当前定量计划")
    for plan in project.analyses:
        if plan.row_id in row_ids and not analysis_is_current(project, plan):
            raise ValueError("所选计划已过期，请重新配置并复核")
    plans = tuple(
        ProjectRowAnalysis(
            row_id=p.row_id,
            crop=p.crop,
            empty_lanes=p.empty_lanes,
            request=replace(p.request, revision=revision),
        )
        if p.row_id in row_ids
        else p
        for p in project.analyses
    )
    return project_with_analyses(project.model_copy(update={"revision": revision}), plans)


def record_project_run(
    project: WBAnalysisProject, row_id: str, request: AnalysisRequest, run: RunRecord
) -> WBAnalysisProject:
    plan = next((p for p in project.analyses if p.row_id == row_id), None)
    if plan is None or not analysis_is_current(project, plan) or plan.request != request:
        raise ValueError("旧运行不能覆盖当前定量计划")
    updated = ProjectRowAnalysis(
        row_id=row_id, crop=plan.crop, empty_lanes=plan.empty_lanes, request=request, run=run
    )
    return set_row_analysis(project, updated)


@dataclass(frozen=True)
class LoadedProjectResult:
    row_id: str
    run_id: str
    asset_sha256: str
    result: AnalysisResult


def read_project_result(plan: ProjectRowAnalysis, data: bytes) -> LoadedProjectResult:
    """Run in a background codec: verify published bytes before exposing any measurements."""
    run = plan.run
    if run is None or run.state != "succeeded" or run.result is None:
        raise ValueError("没有已提交成功的结果资产")
    if (
        len(data) > 8 * 1024 * 1024
        or len(data) != run.result.size_bytes
        or sha256(data).hexdigest() != run.result.sha256
    ):
        raise ValueError("结果资产大小或摘要不一致")
    # Same duplicate-field rejection as portable documents, then strict domain decoding.
    check_document_json(data)
    result = TypeAdapter(AnalysisResult).validate_json(data, strict=True)
    validate_project_result(plan, result)
    return LoadedProjectResult(plan.row_id, run.run_id, run.result.sha256, result)


def validate_project_result(plan: ProjectRowAnalysis, result: AnalysisResult) -> None:
    if result.request != plan.request:
        raise ValueError("结果不对应当前标注/来源/修订")
    ResultFrame(
        protocol_version=1,
        kind="result",
        sequence=2,
        run_id="project",
        attempt_id="project",
        request_id="project",
        result=result,
    )


ProjectCellStatus = Literal[
    "unconfirmed",
    "unbound",
    "ocr_unavailable",
    "valid",
    "quality_review",
    "invalid",
    "excluded",
    "not_detected",
    "missing_source",
    "pending_review",
    "unconfigured",
    "stale",
    "not_run",
    "cancelled",
    "failed",
    "interrupted",
    "result_unavailable",
]


@dataclass(frozen=True)
class ProjectTableCell:
    row_id: str
    figure: str
    protein: str
    lane_index: int
    source_sha256: str
    lane_id: str
    band_id: str
    request_revision: int | None
    run_id: str
    value: float | None
    status: ProjectCellStatus
    reason: str
    evidence_origin: str = ""
    archive_sha256: str = ""
    raw_integral: float | None = None


@dataclass(frozen=True)
class ProjectTableSnapshot:
    cells: tuple[ProjectTableCell, ...]


def _row_status(
    project: WBFigureProject,
    row: FigureRow,
    plan: ProjectRowAnalysis | None,
    loaded: LoadedProjectResult | None,
) -> tuple[ProjectCellStatus, str] | None:
    if row.source is None:
        return "missing_source", "缺少原图"
    from wb_tool.application.automatic import row_is_ready

    if not row_is_ready(project, row):
        return "pending_review", "尚未确认裁剪行或自动建议已过期"
    if plan is None:
        return "unconfigured", "未配置条带边界与基线"
    if not analysis_is_current(project, plan):
        return "stale", "原图/裁剪/泳道配置已改变，请重新配置"
    if plan.run is None:
        return "not_run", "当前计划尚无已提交运行"
    if plan.run.state in ("failed", "cancelled", "interrupted"):
        return plan.run.state, plan.run.reason or plan.run.state
    if loaded is None:
        return "result_unavailable", "结果资产尚未校验或不可读取"
    return None


def fill_project_table(
    project: WBFigureProject, results: tuple[LoadedProjectResult, ...]
) -> tuple[ProjectTableCell, ...]:
    from wb_tool.application.project_restore import run_origin

    if len({r.row_id for r in results}) != len(results):
        raise ValueError("同一行重复提供结果")
    plans = (
        {p.row_id: p for p in project.analyses} if isinstance(project, WBAnalysisProject) else {}
    )
    loaded = {r.row_id: r for r in results}
    cells: list[ProjectTableCell] = []
    for figure in project.figure_order:
        for row in (r for r in project.rows if r.figure == figure):
            plan = plans.get(row.row_id)
            value = loaded.get(row.row_id)
            # Old cached results may exist during edits; never let them bypass plan/run identity.
            if value and plan and plan.run and plan.run.result:
                if value.run_id != plan.run.run_id or value.asset_sha256 != plan.run.result.sha256:
                    value = None
                else:
                    validate_project_result(plan, value.result)
            else:
                value = None
            pending = _row_status(project, row, plan, value)
            for index in range(row.lane_count):
                signal = None
                raw_integral = None
                if pending:
                    status, reason = pending
                else:
                    assert value is not None
                    band = value.result.lanes[index].bands[0]
                    raw_integral = band.measurement.signal if band.measurement else None
                    status, reason, signal = (
                        band.status,
                        band.reason or ", ".join(band.quality_flags),
                        band.signal,
                    )
                if not pending and not row.reviewed:
                    reason = "自动建议计算，未经人工复核" + ("；" + reason if reason else "")
                cells.append(
                    ProjectTableCell(
                        row.row_id,
                        row.figure,
                        row.protein,
                        index + 1,
                        row.source.sha256 if row.source else "",
                        plan.request.lanes[index].roi.lane_id
                        if plan and index < len(plan.request.lanes)
                        else "",
                        "target",
                        plan.request.revision if plan else None,
                        plan.run.run_id if plan and plan.run else "",
                        signal,
                        status,
                        reason,
                        *run_origin(project, plan.run.run_id if plan and plan.run else ""),
                        raw_integral=raw_integral,
                    )
                )
    return tuple(cells)
