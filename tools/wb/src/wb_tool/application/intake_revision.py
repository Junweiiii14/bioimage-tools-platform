"""Explicit crop corrections create a new current draft without modifying past results."""

from wb_tool.application.intake_crop import WBIntakeCropProject, review_intake_crop
from wb_tool.application.intake_figure import WBIntakeFigureProject
from wb_tool.application.intake_workflow import IntakeWorkflowLedger, intake_workflow_digest
from wb_tool.domain.lanes import LaneROI


def revise_completed_intake_crop(
    project: WBIntakeCropProject, row_id: str, crop: LaneROI, *, expected_digest: str
) -> WBIntakeCropProject:
    """Revoke only this row's crop, its Fig's derived results, and current export approval.

    The host must persist this immutable replacement as a normal CAS revision. Past
    workspace revisions, RunRecords, assets and published output directories remain intact.
    """
    type(project).model_validate(dict(project))
    if expected_digest != intake_workflow_digest(project):
        raise ValueError("裁剪修正输入已变化，请重新核对")
    if any(s.status == "running" for s in project.workflow.steps):
        raise ValueError("请等待当前阶段退出后再修正裁剪")
    step = next(
        (s for s in project.workflow.steps if s.stage == "crop" and s.target_id == row_id), None
    )
    if step is None or step.status != "done":
        raise ValueError("此操作仅用于明确修正已完成裁剪")
    figure_id = next(p.figure_id for p in project.intake.proteins if p.protein_id == row_id)
    affected_rows = {p.protein_id for p in project.intake.proteins if p.figure_id == figure_id}
    reset = {("compose", figure_id), ("measure", figure_id), ("export", project.project_id)}
    steps = tuple(
        s.model_copy(update={"status": "needs_review", "reason": "明确修正已完成裁剪"})
        if s.stage == "crop" and s.target_id == row_id
        else s.model_copy(update={"status": "pending", "reason": "裁剪修正使当前结果过期"})
        if (s.stage, s.target_id) in reset
        else s
        for s in project.workflow.steps
    )
    fields = dict(project)
    fields["workflow"] = IntakeWorkflowLedger.model_validate(
        {**dict(project.workflow), "steps": steps, "approved": False, "cancel_requested": False}
    )
    fields["analyses"] = tuple(p for p in project.analyses if p.row_id not in affected_rows)
    if isinstance(project, WBIntakeFigureProject):
        fields["intake_figures"] = tuple(
            e for e in project.intake_figures if e.figure_id != figure_id
        )
    reset_project = type(project).model_validate(fields)
    return review_intake_crop(
        reset_project, row_id, crop, expected_digest=intake_workflow_digest(reset_project)
    )
