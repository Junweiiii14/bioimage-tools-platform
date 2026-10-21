"""Compile one explicit sequence submission into a confirmed batch execution revision."""

from wb_tool.application.instrument_intake import (
    WBIntakeProject,
    confirm_intake,
    intake_digest,
    save_intake_grouping,
)
from wb_tool.application.intake_crop import (
    WBIntakeCropProject,
    review_intake_crop,
)
from wb_tool.application.intake_grouping import IntakeGrouping
from wb_tool.application.intake_revision import (
    confirm_intake_group_revision,
    revise_completed_intake_crop,
    revise_intake_grouping,
)
from wb_tool.application.intake_workflow import (
    WBIntakeWorkflowProject,
    intake_workflow_digest,
    prepare_intake_workflow,
    retry_intake_workflow_step,
)
from wb_tool.domain.lanes import LaneROI


def prepare_intake_sequence(
    project: WBIntakeProject,
    grouping: IntakeGrouping,
    *,
    expected_digest: str,
    allow_reuse: bool = False,
) -> WBIntakeWorkflowProject:
    """Pure preparation; the host must commit this exact snapshot before starting work."""
    if grouping.schema_version != 2:
        raise ValueError("一键处理需要Fig蛋白顺序配置")
    if isinstance(project, WBIntakeWorkflowProject):
        if not project.workflow.editing:
            raise ValueError("已有执行计划请继续处理，修改顺序须先进入分组修订")
        revised = revise_intake_grouping(
            project, grouping, expected_digest=expected_digest, allow_reuse=allow_reuse
        )
        return confirm_intake_group_revision(revised, expected_digest=intake_digest(revised))
    saved = save_intake_grouping(
        project, grouping, expected_digest=expected_digest, allow_reuse=allow_reuse
    )
    confirmed = confirm_intake(saved, expected_digest=intake_digest(saved))
    return prepare_intake_workflow(
        confirmed, expected_digest=intake_digest(confirmed), batch_stages=True
    )


def continue_intake_sequence(
    project: WBIntakeCropProject,
    *,
    expected_digest: str,
    crop: LaneROI | None = None,
    display_angle: float | None = None,
) -> WBIntakeCropProject:
    """Explicitly save one human correction or retry the first blocked batch item."""
    if project.workflow.policy != "intake_workflow@3" or project.workflow.editing:
        raise ValueError("请先确认当前整批执行计划")
    if intake_workflow_digest(project) != expected_digest:
        raise ValueError("阶段输入已变化，请重新核对")
    if any(s.status == "running" for s in project.workflow.steps):
        raise ValueError("请等待当前阶段退出")
    if crop is not None:
        selected = next(
            (
                s
                for s in project.workflow.steps
                if s.stage == "crop" and s.target_id == crop.lane_id
            ),
            None,
        )
        if selected is None:
            raise ValueError("裁剪行不在本批中")
        review = revise_completed_intake_crop if selected.status == "done" else review_intake_crop
        return review(
            project,
            crop.lane_id,
            crop,
            expected_digest=expected_digest,
            display_angle=display_angle,
        )
    order = {"crop": 0, "compose": 1, "measure": 2, "export": 3}
    blocked = sorted(
        (
            s
            for s in project.workflow.steps
            if s.status in {"needs_review", "failed", "cancelled", "interrupted"}
        ),
        key=lambda s: order[s.stage],
    )
    if not blocked:
        return project
    step = blocked[0]
    if step.stage == "crop" and step.status == "needs_review":
        raise ValueError("请先在对应原图确认裁剪范围，再继续自动处理")
    updated = retry_intake_workflow_step(
        project, step.stage, step.target_id, expected_digest=expected_digest
    )
    return type(project).model_validate(dict(updated))
