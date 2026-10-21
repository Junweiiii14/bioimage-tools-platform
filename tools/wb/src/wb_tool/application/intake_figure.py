"""Complete manifest figures before source-pixel runs; no display pixels are quantitative."""

import json
from dataclasses import replace
from hashlib import sha256
from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from tool_contracts.api import AssetRef

from wb_tool.application.analysis import AnalysisRequest
from wb_tool.application.document import DocumentIO
from wb_tool.application.figure_project import FigureRow
from wb_tool.application.intake_crop import IntakeCropEvidence, WBIntakeCropProject
from wb_tool.application.intake_execution import planned_intake_slots
from wb_tool.application.intake_workflow import (
    IntakeWorkflowLedger,
    IntakeWorkflowTicket,
    completed_intake_steps,
)
from wb_tool.application.laboratory_layout import (
    FigureColumn,
    FigureComposition,
    FigureLayoutStyle,
    WBLayoutProject,
    initial_composition,
)
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    ProjectRowAnalysis,
    analysis_is_current,
    validate_project_result,
)


def intake_figure_rows(project: WBIntakeCropProject, figure_id: str) -> tuple[FigureRow, ...]:
    ids = tuple(p.protein_id for p in project.intake.proteins if p.figure_id == figure_id)
    if not ids:
        raise ValueError("Fig身份不属于当前清单")
    rows = {r.row_id: r for r in project.rows}
    return tuple(rows[key] for key in ids)


def _ready(project: WBIntakeCropProject, figure_id: str) -> None:
    steps = {(s.stage, s.target_id): s.status for s in project.workflow.steps}
    evidence = {e.row_id: e for e in project.intake_crops}
    for row in intake_figure_rows(project, figure_id):
        crop = evidence.get(row.row_id)
        if (
            steps["crop", row.row_id] != "done"
            or crop is None
            or not crop.geometry_ready
            or crop.raw_crop is None
            or row.source is None
            or row.roi != crop.crop
        ):
            raise ValueError("完整Fig尚缺已审核原值裁剪；不能挤掉缺行后继续")


def intake_figure_projection(project: WBIntakeCropProject, figure_id: str) -> WBLayoutProject:
    """Explicit display-only projection; retain every member and its full 1..N slices."""
    _ready(project, figure_id)
    rows = intake_figure_rows(project, figure_id)
    names = {r.figure for r in rows}
    if len(names) != 1:
        raise ValueError("同一稳定Fig不能混入其他显示组")
    name = rows[0].figure
    ids = {r.row_id for r in rows}
    composition = (
        project.composition if project.composition.slices else initial_composition(project)
    )
    return WBLayoutProject(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        rows=rows,
        figure_order=(name,),
        template=project.template,
        layout_style=project.layout_style,
        composition=FigureComposition(
            slices=tuple(s for s in composition.slices if s.row_id in ids),
            columns=(FigureColumn(figure=name, column=1),),
        ),
    )


def intake_figure_digest(project: WBIntakeCropProject, figure_id: str) -> str:
    projection = intake_figure_projection(project, figure_id)
    values = projection.model_dump(mode="json", exclude={"revision", "analyses"})
    # Workspace asset locations change on restore; content identity does not.
    for row in values["rows"]:
        row["source"] = row["source"]["sha256"]
    if values["template"]["font"]:
        values["template"]["font"] = values["template"]["font"]["sha256"]
    values["raw_crops"] = [
        e.raw_crop.sha256
        for row in projection.rows
        for e in project.intake_crops
        if e.row_id == row.row_id and e.raw_crop is not None
    ]
    return sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def apply_intake_sampling_review(
    evidence: IntakeCropEvidence, request: AnalysisRequest
) -> AnalysisRequest:
    """Carry local geometric uncertainty into actual measurement quality, not display flags."""
    grid = evidence.fixed_grid
    if grid is None:
        return request
    note = "boundary_review:local_signal_ambiguity"
    return replace(
        request,
        lanes=tuple(
            replace(
                lane,
                bands=tuple(
                    replace(b, detection_notes=tuple(dict.fromkeys((*b.detection_notes, note))))
                    for b in lane.bands
                ),
            )
            if i in grid.review_positions
            else lane
            for i, lane in enumerate(request.lanes, 1)
        ),
    )


def intake_sampling_current(evidence: IntakeCropEvidence, request: AnalysisRequest) -> bool:
    grid = evidence.fixed_grid
    if grid is None:
        return True
    return len(grid.sampling_limits) == len(request.lanes) and all(
        (lane.roi.x0, lane.roi.x1) == (limit.x0, limit.x1)
        and limit.y0 <= lane.roi.y0 < lane.roi.y1 <= limit.y1
        and (
            i not in grid.review_positions
            or all(
                "boundary_review:local_signal_ambiguity" in b.detection_notes for b in lane.bands
            )
        )
        for i, (lane, limit) in enumerate(zip(request.lanes, grid.sampling_limits, strict=True), 1)
    )


def _current_intake_plan(project: WBIntakeCropProject, plan: ProjectRowAnalysis) -> bool:
    evidence = next((e for e in project.intake_crops if e.row_id == plan.row_id), None)
    if evidence is None or not analysis_is_current(project, plan):
        return False
    targets = tuple(
        replace(slot.roi, lane_id=f"{plan.row_id}:{slot.position:02d}")
        for slot in evidence.slots
        if slot.roi is not None
    )
    return (
        plan.request.geometry_policy == "anchored_context@1"
        and plan.request.quant_policy == "anchored_background@1"
        and tuple(lane.target_roi for lane in plan.request.lanes) == targets
        and len(targets) == evidence.lane_count
        and intake_sampling_current(evidence, plan.request)
    )


class IntakeFigureEvidence(DocumentIO):
    model_config = ConfigDict(revalidate_instances="always")
    policy: Literal["intake_figure@1"] = "intake_figure@1"
    figure_id: str = Field(min_length=1, max_length=80)
    row_ids: tuple[str, ...] = Field(min_length=1, max_length=512)
    slot_ids: tuple[tuple[str, ...], ...] = Field(min_length=1, max_length=512)
    input_digest: str = Field(pattern="^[0-9a-f]{64}$")
    image: AssetRef
    width: int = Field(ge=1, le=32768)
    height: int = Field(ge=1, le=32768)


class IntakeFigurePreparation(DocumentIO):
    model_config = ConfigDict(revalidate_instances="always")
    path: str = Field(min_length=1, max_length=32768)
    sha256: str = Field(pattern="^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0, le=64 * 1024 * 1024)
    figure_id: str = Field(min_length=1, max_length=80)
    input_digest: str = Field(pattern="^[0-9a-f]{64}$")
    width: int = Field(ge=1, le=32768)
    height: int = Field(ge=1, le=32768)
    analyses: tuple[ProjectRowAnalysis, ...] = Field(min_length=1, max_length=512)


class WBIntakeFigureProject(WBIntakeCropProject):
    schema_version: int = Field(default=13, ge=13, le=13)
    intake_figures: tuple[IntakeFigureEvidence, ...] = Field(default=(), max_length=512)

    @model_validator(mode="after")
    def complete_figures(self) -> "WBIntakeFigureProject":
        figures = {e.figure_id: e for e in self.intake_figures}
        if len(figures) != len(self.intake_figures):
            raise ValueError("同一Fig不能有重复当前成图证据")
        statuses = {(s.stage, s.target_id): s.status for s in self.workflow.steps}
        plans = {p.row_id: p for p in self.analyses}
        for evidence in self.intake_figures:
            rows = intake_figure_rows(self, evidence.figure_id)
            if evidence.row_ids != tuple(r.row_id for r in rows) or evidence.slot_ids != tuple(
                tuple(
                    s.slot_id for s in planned_intake_slots(self.project_id, r.row_id, r.lane_count)
                )
                for r in rows
            ):
                raise ValueError("Fig成图证据偏离稳定行或完整槽位身份")
            if evidence.width * evidence.height > 32_000_000:
                raise ValueError("Fig图像超出像素预算")
        for fig in self.intake.figures:
            compose, measure = (
                statuses["compose", fig.figure_id],
                statuses["measure", fig.figure_id],
            )
            if compose == "done" or measure in {"running", "done"}:
                evidence = figures.get(fig.figure_id)
                if evidence is None or evidence.input_digest != intake_figure_digest(
                    self, fig.figure_id
                ):
                    raise ValueError("阶段缺少当前完整Fig的已持久化成图依据")
            if measure in {"running", "done"}:
                for row in intake_figure_rows(self, fig.figure_id):
                    plan = plans.get(row.row_id)
                    if plan is None or not _current_intake_plan(self, plan):
                        raise ValueError("Fig测量必须绑定当前原图、原ROI与完整N请求")
                    if measure == "done" and (
                        plan.run is None or plan.run.state != "succeeded" or plan.run.result is None
                    ):
                        raise ValueError("Fig测量完成必须具有每行真实成功RunRecord")
        return self


def prepare_intake_figures(project: WBIntakeCropProject) -> WBIntakeFigureProject:
    checked = type(project).model_validate(dict(project))
    if isinstance(checked, WBIntakeFigureProject):
        return checked
    if any(
        s.status == "running" or (s.stage != "crop" and s.attempt) for s in checked.workflow.steps
    ):
        raise ValueError("旧项目活动或后续阶段缺少版本化成图依据，不能静默升级")
    fields = dict(checked)
    if not checked.composition.slices:
        fields["composition"] = initial_composition(checked)
        if checked.layout_style == FigureLayoutStyle():
            # New intake display default only; quantitative source samples remain unchanged.
            fields["layout_style"] = FigureLayoutStyle(display_policy="standard_lane_ratio@1")
    return WBIntakeFigureProject.model_validate({**fields, "schema_version": 13})


def complete_intake_figure(
    project: WBIntakeFigureProject,
    ticket: IntakeWorkflowTicket,
    prepared: IntakeFigurePreparation,
    asset: AssetRef,
) -> WBIntakeFigureProject:
    if ticket.stage != "compose" or ticket.target_id != prepared.figure_id:
        raise ValueError("Fig成图回复不属于当前票据")
    steps = completed_intake_steps(project, ticket, "done")
    if project.workflow.cancel_requested:
        return type(project).model_validate(
            {**dict(project), "workflow": project.workflow.model_copy(update={"steps": steps})}
        )
    rows = intake_figure_rows(project, ticket.target_id)
    if (
        prepared.input_digest != intake_figure_digest(project, ticket.target_id)
        or (asset.sha256, asset.size_bytes) != (prepared.sha256, prepared.size_bytes)
        or tuple(p.row_id for p in prepared.analyses) != tuple(r.row_id for r in rows)
    ):
        raise ValueError("Fig成图或请求未对应冻结输入与已导入资产")
    for plan in prepared.analyses:
        ProjectRowAnalysis.model_validate(dict(plan))
        if plan.run is not None or not _current_intake_plan(project, plan):
            raise ValueError("Fig准备不能夹带运行，且请求必须为当前原图几何")
    evidence = IntakeFigureEvidence(
        figure_id=ticket.target_id,
        row_ids=tuple(r.row_id for r in rows),
        slot_ids=tuple(
            tuple(
                s.slot_id for s in planned_intake_slots(project.project_id, r.row_id, r.lane_count)
            )
            for r in rows
        ),
        input_digest=prepared.input_digest,
        image=asset,
        width=prepared.width,
        height=prepared.height,
    )
    ids = set(evidence.row_ids)
    previous = {p.row_id: p for p in project.analyses}
    merged = tuple(
        old
        if (
            project.workflow.policy in {"intake_workflow@2", "intake_workflow@3"}
            and (old := previous.get(plan.row_id)) is not None
            and _current_intake_plan(project, old)
            and old.crop == plan.crop
            and old.empty_lanes == plan.empty_lanes
            and replace(old.request, revision=plan.request.revision) == plan.request
            and old.run is not None
            and old.run.state == "succeeded"
            and old.run.result is not None
        )
        else plan
        for plan in prepared.analyses
    )
    # A new display label/order does not create a new numerical run. Keep the actual
    # run and prior attempt identity only when every frozen numerical input agrees.
    if all(p.run is not None for p in merged):
        steps = tuple(
            s.model_copy(update={"status": "done", "reason": ""})
            if s.stage == "measure" and s.target_id == ticket.target_id and s.attempt > 0
            else s
            for s in steps
        )
    return type(project).model_validate(
        {
            **dict(project),
            "workflow": IntakeWorkflowLedger.model_validate(
                {**dict(project.workflow), "steps": steps}
            ),
            "intake_figures": (
                *[e for e in project.intake_figures if e.figure_id != ticket.target_id],
                evidence,
            ),
            "analyses": (*[p for p in project.analyses if p.row_id not in ids], *merged),
        }
    )


def prepare_intake_measurement_revision(
    project: WBIntakeFigureProject, figure_id: str, revision: int
) -> WBIntakeFigureProject:
    if revision != project.revision + 1 or any(
        s.status == "running" for s in project.workflow.steps
    ):
        raise ValueError("测量请求须在claim之前绑定下一个真实CAS修订")
    ids = {r.row_id for r in intake_figure_rows(project, figure_id)}
    return type(project).model_validate(
        {
            **dict(project),
            "revision": revision,
            "analyses": tuple(
                ProjectRowAnalysis(
                    row_id=p.row_id,
                    crop=p.crop,
                    empty_lanes=p.empty_lanes,
                    request=replace(p.request, revision=revision),
                )
                if p.row_id in ids
                else p
                for p in project.analyses
            ),
        }
    )


def complete_intake_measurement(
    project: WBIntakeFigureProject,
    ticket: IntakeWorkflowTicket,
    committed: tuple[ProjectRowAnalysis, ...],
    results: tuple[LoadedProjectResult, ...],
    *,
    error: str = "",
) -> WBIntakeFigureProject:
    if ticket.stage != "measure":
        raise ValueError("测量回复不属于当前阶段")
    expected = {p.row_id: p for p in project.analyses}
    ids = {r.row_id for r in intake_figure_rows(project, ticket.target_id)}
    updates = {p.row_id: p for p in committed}
    if len(updates) != len(committed) or set(updates) - ids:
        raise ValueError("测量回复重复或混入其他Fig")
    decoded = {r.row_id: r for r in results}
    if len(decoded) != len(results) or set(decoded) - ids:
        raise ValueError("已解码结果重复或不属于当前Fig")
    for key, plan in updates.items():
        ProjectRowAnalysis.model_validate(dict(plan))
        base = expected.get(key)
        if (
            base is None
            or plan.request != base.request
            or plan.crop != base.crop
            or plan.empty_lanes != base.empty_lanes
            or plan.run is None
        ):
            raise ValueError("运行回复与冻结的原图请求不一致")
        if plan.run.document_id != project.project_id:
            raise ValueError("运行不属于当前项目")
        if plan.run.state == "succeeded":
            result = decoded.get(key)
            if (
                result is None
                or plan.run.result is None
                or result.run_id != plan.run.run_id
                or result.asset_sha256 != plan.run.result.sha256
            ):
                raise ValueError("成功运行缺少同一已核验结果")
            validate_project_result(plan, result.result)
    done = ids == set(updates) and all(p.run and p.run.state == "succeeded" for p in committed)
    steps = completed_intake_steps(
        project,
        ticket,
        "done" if done and not error else "failed",
        reason=error or ("部分原图运行未完成，请重试本Fig" if not done else ""),
    )
    return type(project).model_validate(
        {
            **dict(project),
            "workflow": IntakeWorkflowLedger.model_validate(
                {**dict(project.workflow), "steps": steps}
            ),
            "analyses": tuple(updates.get(p.row_id, p) for p in project.analyses),
        }
    )
