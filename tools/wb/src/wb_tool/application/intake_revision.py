"""Explicit crop corrections create a new current draft without modifying past results."""

from wb_tool.application.instrument_intake import (
    WBIntakeProject,
    intake_digest,
    intake_project_rows,
    save_intake_grouping,
    validate_intake_complete,
)
from wb_tool.application.intake_crop import WBIntakeCropProject, review_intake_crop
from wb_tool.application.intake_figure import WBIntakeFigureProject
from wb_tool.application.intake_grouping import IntakeGrouping
from wb_tool.application.intake_supervision import WBIntakeGridProject
from wb_tool.application.intake_workflow import (
    IntakeWorkflowLedger,
    IntakeWorkflowStep,
    WBIntakeWorkflowProject,
    intake_workflow_digest,
)
from wb_tool.application.laboratory_layout import FigureComposition, initial_composition
from wb_tool.domain.lanes import LaneROI


def begin_intake_group_revision(
    project: WBIntakeWorkflowProject, *, expected_digest: str
) -> WBIntakeWorkflowProject:
    """Explicitly pause execution and persist editable choices in the current revision."""
    type(project).model_validate(dict(project))
    if expected_digest != intake_digest(project):
        raise ValueError("当前清单已变化，请重新核对")
    if project.intake.grouping is None:
        raise ValueError("旧行式清单请保留原项目，不能推导采集组")
    if any(s.status == "running" for s in project.workflow.steps):
        raise ValueError("请等待阶段退出后再修改分组")
    return type(project).model_validate(
        {
            **dict(project),
            "intake": project.intake.model_copy(update={"confirmed_digest": ""}),
            "workflow": IntakeWorkflowLedger.model_validate(
                {
                    **dict(project.workflow),
                    "policy": "intake_workflow@3"
                    if project.workflow.policy == "intake_workflow@3"
                    else "intake_workflow@2",
                    "editing": True,
                    "approved": False,
                    "cancel_requested": False,
                }
            ),
        }
    )


def confirm_intake_group_revision(
    project: WBIntakeWorkflowProject, *, expected_digest: str
) -> WBIntakeWorkflowProject:
    if not project.workflow.editing or expected_digest != intake_digest(project):
        raise ValueError("当前没有匹配的分组编辑草稿")
    validate_intake_complete(project.intake)
    return type(project).model_validate(
        {
            **dict(project),
            "intake": project.intake.model_copy(update={"confirmed_digest": expected_digest}),
            "workflow": project.workflow.model_copy(
                update={
                    "editing": False,
                    "policy": "intake_workflow@3"
                    if project.intake.grouping and project.intake.grouping.schema_version == 2
                    else project.workflow.policy,
                }
            ),
        }
    )


def revise_intake_grouping(
    project: WBIntakeWorkflowProject,
    grouping: IntakeGrouping,
    *,
    expected_digest: str,
    allow_reuse: bool = False,
) -> WBIntakeWorkflowProject:
    """Apply identity-scoped invalidation without mutating any historical revision or asset."""
    type(project).model_validate(dict(project))
    if not project.workflow.editing or expected_digest != intake_digest(project):
        raise ValueError("请先明确进入分组修改，并刷新当前草稿")
    previous = project.intake.grouping
    if previous is None or {g.group_id: g.source_ids for g in previous.groups} != {
        g.group_id: g.source_ids for g in grouping.groups
    }:
        raise ValueError("执行后修改必须保留采集组及其原始成员身份")
    # Use the schema10 editor's exact normalization, reuse and region validation.
    rows = intake_project_rows(project.intake)
    editing = WBIntakeProject(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        intake=project.intake.model_copy(update={"confirmed_digest": ""}),
        rows=rows,
        figure_order=tuple(dict.fromkeys(r.figure for r in rows)),
    )
    edited = save_intake_grouping(
        editing, grouping, expected_digest=expected_digest, allow_reuse=allow_reuse
    )
    if edited.intake == editing.intake:
        return project
    current = edited.intake.grouping
    assert current is not None
    old_groups = {g.group_id: g for g in previous.groups}
    old_figs = {f.figure_id: f for f in previous.figures}
    new_figs = {f.figure_id: f for f in current.figures}
    invalid_rows: set[str] = set()
    affected_figs = {
        key for key in old_figs.keys() | new_figs.keys() if old_figs.get(key) != new_figs.get(key)
    }
    for group in current.groups:
        old = old_groups[group.group_id]
        old_fig, new_fig = old_figs.get(old.figure_id or ""), new_figs.get(group.figure_id or "")
        if (
            old.selected_source_id != group.selected_source_id
            or old.region_index != group.region_index
            or old.figure_id != group.figure_id
            or (old_fig.lane_count if old_fig else None)
            != (new_fig.lane_count if new_fig else None)
        ):
            invalid_rows.add(group.group_id)
        if old != group or group.group_id in invalid_rows:
            affected_figs.update(f for f in (old.figure_id, group.figure_id) if f)
    for key in old_figs.keys() | new_figs.keys():
        if tuple(g.group_id for g in previous.groups if g.figure_id == key) != tuple(
            g.group_id for g in current.groups if g.figure_id == key
        ):
            affected_figs.add(key)
    old_rows = {r.row_id: r for r in project.rows}
    new_rows = tuple(
        row.model_copy(
            update={
                "roi": old_rows[row.row_id].roi,
                "reviewed": old_rows[row.row_id].reviewed,
                "empty_lanes": old_rows[row.row_id].empty_lanes,
                "notes": old_rows[row.row_id].notes,
            }
        )
        if row.row_id in old_rows and row.row_id not in invalid_rows
        else row
        for row in edited.rows
    )
    fields = {
        **dict(project),
        "intake": edited.intake,
        "rows": new_rows,
        "figure_order": edited.figure_order,
    }
    if isinstance(project, WBIntakeGridProject) and project.grid.order:
        active_ids = {f.figure_id for f in edited.intake.figures}
        surviving = tuple(key for key in project.grid.order if key in active_ids)
        appended = tuple(f.figure_id for f in edited.intake.figures if f.figure_id not in surviving)
        fields["grid"] = project.grid.model_copy(update={"order": surviving + appended})
    retained_ids = {r.row_id for r in new_rows} - invalid_rows
    fields["analyses"] = tuple(p for p in project.analyses if p.row_id in retained_ids)
    if isinstance(project, WBIntakeCropProject):
        fields["intake_crops"] = tuple(e for e in project.intake_crops if e.row_id in retained_ids)
    if isinstance(project, WBIntakeFigureProject):
        fields["intake_figures"] = tuple(
            e for e in project.intake_figures if e.figure_id not in affected_figs
        )
    old_steps = {(s.stage, s.target_id): s for s in project.workflow.steps}
    addresses = [
        *(("crop", r.row_id) for r in new_rows),
        *((stage, f.figure_id) for f in edited.intake.figures for stage in ("compose", "measure")),
        ("export", project.project_id),
    ]
    steps: list[IntakeWorkflowStep] = []
    for stage, target in addresses:
        old_step = old_steps.get((stage, target))
        reset = stage == "export" or (
            target in invalid_rows if stage == "crop" else target in affected_figs
        )
        steps.append(
            IntakeWorkflowStep.model_validate(
                {
                    **(dict(old_step) if old_step else {}),
                    "stage": stage,
                    "target_id": target,
                    **({"status": "pending", "reason": "分组修改使当前结果过期"} if reset else {}),
                }
            )
        )
    fields["workflow"] = IntakeWorkflowLedger.model_validate(
        {
            **dict(project.workflow),
            "intake_digest": intake_digest(edited),
            "steps": tuple(steps),
        }
    )
    # Retain custom layout of untouched Figs; changed Figs get complete new placeholders.
    fresh = initial_composition(edited.model_copy(update={"template": project.template}))
    positioned = {s.figure for s in project.composition.slices}
    old_names = {
        f.label
        for f in project.intake.figures
        if f.figure_id not in affected_figs and f.label in positioned
    }
    fields["composition"] = FigureComposition(
        slices=tuple(s for s in project.composition.slices if s.figure in old_names)
        + tuple(s for s in fresh.slices if s.figure not in old_names),
        columns=tuple(c for c in project.composition.columns if c.figure in old_names)
        + tuple(c for c in fresh.columns if c.figure not in old_names),
    )
    return type(project).model_validate(fields)


def revise_completed_intake_crop(
    project: WBIntakeCropProject,
    row_id: str,
    crop: LaneROI,
    *,
    expected_digest: str,
    display_angle: float | None = None,
) -> WBIntakeCropProject:
    """Revoke only this row's crop, its Fig's derived results, and current export approval.

    The host must persist this immutable replacement as a normal CAS revision. Past
    workspace revisions, RunRecords, assets and published output directories remain intact.
    """
    type(project).model_validate(dict(project))
    if project.workflow.editing:
        raise ValueError("分组编辑中不能同时修正裁剪")
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
        reset_project,
        row_id,
        crop,
        expected_digest=intake_workflow_digest(reset_project),
        display_angle=display_angle,
    )
