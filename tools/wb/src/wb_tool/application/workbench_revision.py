"""Explicit workbench edits preserve schema, source identities and immutable historical evidence."""

from typing import Literal, cast

from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.instrument_intake import (
    WBIntakeProject,
    intake_digest,
    save_intake_grouping,
)
from wb_tool.application.intake_crop import WBIntakeCropProject
from wb_tool.application.intake_figure import WBIntakeFigureProject
from wb_tool.application.intake_grouping import IntakeDraftFigure, IntakeGrouping
from wb_tool.application.intake_revision import begin_intake_group_revision, revise_intake_grouping
from wb_tool.application.intake_workflow import WBIntakeWorkflowProject
from wb_tool.application.project_metadata import (
    MetadataEntry,
    MetadataPreview,
    metadata_digest,
    metadata_proposal,
)


def prepare_workbench_revision(
    project: WBFigureProject,
    *,
    expected_digest: str,
    impact: Literal["outputs", "figures"] = "outputs",
    crop_rows: tuple[str, ...] = (),
    figure_ids: tuple[str, ...] = (),
    allow_group_edit: bool = False,
) -> WBFigureProject:
    """Prepare an immutable draft; callers persist only the final validated replacement.

    This never approves execution, upgrades schema10 or deletes historical runs/output assets.
    Presentation changes invalidate display evidence, retaining valid numerical plans for reuse.
    """
    type(project).model_validate(dict(project))
    if expected_digest != metadata_digest(project):
        raise ValueError("项目已改变，请刷新后核对")
    if impact not in {"outputs", "figures"} or not set(crop_rows) <= {
        r.row_id for r in project.rows
    }:
        raise ValueError("修订影响范围无效")
    if not isinstance(project, WBIntakeWorkflowProject):
        return project
    if not set(figure_ids) <= {f.figure_id for f in project.intake.figures}:
        raise ValueError("修订 Fig 身份不属于当前项目")
    if project.workflow.editing and not allow_group_edit:
        raise ValueError("请先在准备页完成分组核对")
    if any(s.status == "running" for s in project.workflow.steps):
        raise ValueError("请等待当前阶段退出后再修改")
    affected = {
        p.figure_id
        for p in project.intake.proteins
        if impact == "figures" or p.protein_id in crop_rows or p.figure_id in figure_ids
    }
    steps = tuple(
        s.model_copy(update={"status": "pending", "reason": "明确修改使当前阶段待重新处理"})
        if s.stage == "export"
        or (s.stage == "crop" and s.target_id in crop_rows)
        or (s.stage in {"compose", "measure"} and s.target_id in affected)
        else s
        for s in project.workflow.steps
    )
    data = dict(project)
    data["workflow"] = project.workflow.model_copy(
        update={
            "steps": steps,
            "approved": False,
            "cancel_requested": False,
        }
    )
    if crop_rows:
        data["analyses"] = tuple(p for p in project.analyses if p.row_id not in crop_rows)
    if isinstance(project, WBIntakeCropProject):
        data["intake_crops"] = tuple(e for e in project.intake_crops if e.row_id not in crop_rows)
    if isinstance(project, WBIntakeFigureProject):
        data["intake_figures"] = tuple(
            e for e in project.intake_figures if e.figure_id not in affected
        )
    return type(project).model_validate(data)


def workbench_project_digest(project: WBFigureProject) -> str:
    """Identity for an explicit workbench edit, including scientific configuration and revision."""
    return metadata_digest(project)


def _revise_grouping(project: WBIntakeProject, grouping: IntakeGrouping) -> WBIntakeProject:
    if grouping == project.intake.grouping:
        return project
    if isinstance(project, WBIntakeWorkflowProject):
        editable = begin_intake_group_revision(project, expected_digest=intake_digest(project))
        return revise_intake_grouping(editable, grouping, expected_digest=intake_digest(editable))
    return save_intake_grouping(project, grouping, expected_digest=intake_digest(project))


def revise_workbench_figure_order(
    project: WBFigureProject,
    order: tuple[str, ...],
    *,
    expected_digest: str,
) -> WBFigureProject:
    if metadata_digest(project) != expected_digest:
        raise ValueError("项目已改变，请刷新后核对")
    if len(set(order)) != len(order) or set(order) != set(project.figure_order):
        raise ValueError("Fig 顺序必须保留所有当前 Fig")
    if order == project.figure_order:
        return project
    if not isinstance(project, WBIntakeProject):
        return type(project).model_validate({**dict(project), "figure_order": order})
    grouping = project.intake.grouping
    if grouping is None:
        raise ValueError("旧行式清单请使用原兼容编辑入口")
    active = {f.label: f for f in grouping.figures}
    figures = tuple(active[name] for name in order)
    figures += tuple(f for f in grouping.figures if f.label not in order)
    groups = tuple(g for f in figures for g in grouping.groups if g.figure_id == f.figure_id)
    groups += tuple(g for g in grouping.groups if g.figure_id is None)
    sequence = (
        None
        if grouping.sequence is None
        else tuple(p for f in figures for p in grouping.sequence if p.figure_id == f.figure_id)
    )
    revised = IntakeGrouping.model_validate(
        {
            **dict(grouping),
            "figures": figures,
            "groups": groups,
            "sequence": sequence,
        }
    )
    return _revise_grouping(project, revised)


def apply_workbench_metadata(
    project: WBFigureProject,
    preview: MetadataPreview,
    selected: tuple[MetadataEntry, ...],
    fields: tuple[str, ...],
) -> WBFigureProject:
    """Apply explicit fields with the newest Intake projection and stage invalidation rules."""
    proposal = metadata_proposal(project, preview, selected, fields)
    if not isinstance(project, WBIntakeProject):
        return type(project).model_validate(proposal)
    rows = cast(tuple[FigureRow, ...], proposal["rows"])
    previous = {r.row_id: r for r in project.rows}
    grouping = project.intake.grouping
    structural = rows != project.rows and (
        tuple(r.row_id for r in rows) != tuple(r.row_id for r in project.rows)
        or any(
            (r.figure, r.protein, r.lane_count)
            != (
                previous[r.row_id].figure,
                previous[r.row_id].protein,
                previous[r.row_id].lane_count,
            )
            for r in rows
        )
    )
    current = project
    if structural:
        if grouping is None:
            raise ValueError("旧行式清单请使用原兼容编辑入口")
        by_id = {r.row_id: r for r in rows}
        group_ids = {g.group_id: g for g in grouping.groups}
        figures: list[IntakeDraftFigure] = []
        for figure in grouping.figures:
            members = [
                by_id[g.group_id]
                for g in grouping.groups
                if g.figure_id == figure.figure_id and g.group_id in by_id
            ]
            names, counts = {r.figure for r in members}, {r.lane_count for r in members}
            if len(names) > 1 or len(counts) > 1:
                raise ValueError("同一 Fig 的名称和 N 必须一致；请选择该 Fig 全部蛋白行")
            figures.append(
                figure.model_copy(
                    update={
                        "label": next(iter(names)) if names else figure.label,
                        "lane_count": next(iter(counts)) if counts else figure.lane_count,
                    }
                )
            )
        ordered_fig_ids = tuple(dict.fromkeys(group_ids[r.row_id].figure_id for r in rows))
        blocked = tuple(
            r.row_id
            for key in ordered_fig_ids
            for r in rows
            if group_ids[r.row_id].figure_id == key
        )
        if blocked != tuple(r.row_id for r in rows):
            raise ValueError("Fig 内蛋白须连续排序，请先核对排序列")
        figures.sort(
            key=lambda f: (
                ordered_fig_ids.index(f.figure_id)
                if f.figure_id in ordered_fig_ids
                else len(ordered_fig_ids)
            )
        )
        ordered = iter(
            group_ids[r.row_id].model_copy(update={"protein_label": r.protein}) for r in rows
        )
        groups = tuple(next(ordered) if g.group_id in by_id else g for g in grouping.groups)
        sequence = grouping.sequence
        if sequence is not None:
            assigned = [g for g in grouping.groups if g.figure_id is not None]
            entries = [p for p in sequence if p.label.strip()]
            entry_map = {g.group_id: p for g, p in zip(assigned, entries, strict=True)}
            sequence = tuple(
                entry_map[g.group_id].model_copy(
                    update={
                        "figure_id": g.figure_id,
                        "label": g.protein_label,
                    }
                )
                for g in groups
                if g.figure_id is not None
            )
            sequence = tuple(
                p
                for f in figures
                for p in (*sequence, *(p for p in grouping.sequence or () if not p.label.strip()))
                if p.figure_id == f.figure_id
            )
        revised = IntakeGrouping.model_validate(
            {
                **dict(grouping),
                "figures": tuple(figures),
                "groups": groups,
                "sequence": sequence,
            }
        )
        current = _revise_grouping(project, revised)
    changed_empty = tuple(r.row_id for r in rows if r.empty_lanes != previous[r.row_id].empty_lanes)
    display_changed = proposal["name"] != project.name or any(
        r.notes != previous[r.row_id].notes for r in rows
    )
    current = cast(
        WBIntakeProject,
        prepare_workbench_revision(
            current,
            expected_digest=metadata_digest(current),
            impact="figures" if proposal["name"] != project.name else "outputs",
            figure_ids=tuple(
                p.figure_id
                for p in current.intake.proteins
                if display_changed
                and any(
                    r.row_id == p.protein_id and r.notes != previous[r.row_id].notes for r in rows
                )
            ),
            crop_rows=changed_empty,
            allow_group_edit=structural,
        ),
    )
    incoming = {r.row_id: r for r in rows}
    result_rows = tuple(
        r.model_copy(
            update={
                "notes": incoming[r.row_id].notes,
                "empty_lanes": incoming[r.row_id].empty_lanes,
                "reviewed": False if r.row_id in changed_empty else r.reviewed,
            }
        )
        for r in current.rows
    )
    if current.schema_version == 10 and any(r.notes or r.empty_lanes for r in result_rows):
        raise ValueError("准备阶段先保存 Fig、蛋白与 N；开始处理后可填写备注和空泳道")
    return type(current).model_validate(
        {**dict(current), "rows": result_rows, "name": proposal["name"]}
    )
