"""Stable intake table identities and evidence of published, immutable output snapshots."""

import json
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Literal, cast

from pydantic import ConfigDict, Field, model_validator
from tool_contracts.api import AssetRef

from wb_tool.application.document import DocumentIO
from wb_tool.application.intake_execution import planned_intake_slots
from wb_tool.application.intake_figure import WBIntakeFigureProject
from wb_tool.application.intake_workflow import (
    IntakeWorkflowTicket,
    completed_intake_steps,
)
from wb_tool.application.laboratory_layout import FigureColumn, FigureComposition, WBLayoutProject
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    ProjectTableCell,
    fill_project_table,
)


def _content(value: object) -> object:
    if isinstance(value, dict):
        value = cast(dict[str, object], value)
        if "asset_id" in value and "sha256" in value and "size_bytes" in value:
            return {key: value[key] for key in ("sha256", "size_bytes")}
        return {key: _content(item) for key, item in value.items() if key != "confirmed_digest"}
    if isinstance(value, list):
        return [_content(item) for item in cast(list[object], value)]
    return value


def intake_output_digest(project: WBIntakeFigureProject) -> str:
    """Output content identity survives asset relocation and added archive provenance."""
    fields = project.model_dump(
        mode="json",
        exclude={
            "schema_version",
            "revision",
            "workflow",
            "intake_outputs",
            "archive_sources",
            "imported_runs",
        },
    )
    return sha256(json.dumps(_content(fields), sort_keys=True).encode()).hexdigest()


class IntakeOutputEvidence(DocumentIO):
    model_config = ConfigDict(revalidate_instances="always")

    policy: Literal["intake_output@1"] = "intake_output@1"
    output_id: str = Field(pattern="^[0-9a-f]{32}$")
    input_digest: str = Field(pattern="^[0-9a-f]{64}$")
    index: AssetRef
    destination: str = Field(min_length=1, max_length=32768)
    complete: bool
    errors: tuple[str, ...] = Field(default=(), max_length=1024)

    @model_validator(mode="after")
    def actual_completeness(self) -> "IntakeOutputEvidence":
        if self.complete == bool(self.errors):
            raise ValueError("完整输出不能有缺项；部分输出必须说明原因")
        return self


class IntakeOutputPreparation(DocumentIO):
    output_id: str = Field(pattern="^[0-9a-f]{32}$")
    project_id: str
    revision: int = Field(ge=0)
    input_digest: str = Field(pattern="^[0-9a-f]{64}$")
    destination: str = Field(min_length=1, max_length=32768)
    path: str = Field(min_length=1, max_length=32768)
    sha256: str = Field(pattern="^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0, le=16 * 1024 * 1024)
    complete: bool
    errors: tuple[str, ...] = Field(default=(), max_length=1024)


class WBIntakeOutputProject(WBIntakeFigureProject):
    schema_version: int = Field(default=14, ge=14, le=14)
    intake_outputs: tuple[IntakeOutputEvidence, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def published_outputs(self) -> "WBIntakeOutputProject":
        ids = [item.output_id for item in self.intake_outputs]
        if len(ids) != len(set(ids)):
            raise ValueError("输出快照身份重复")
        if any(s.stage == "export" and s.status == "done" for s in self.workflow.steps):
            current = intake_output_digest(self)
            if not any(
                item.complete and item.input_digest == current for item in self.intake_outputs
            ):
                raise ValueError("输出阶段完成需要当前内容的真实完整输出索引")
        return self


def prepare_intake_outputs(project: WBIntakeFigureProject) -> WBIntakeOutputProject:
    checked = type(project).model_validate(dict(project))
    if isinstance(checked, WBIntakeOutputProject):
        return checked
    if any(
        s.status == "running" or (s.stage == "export" and s.attempt) for s in checked.workflow.steps
    ):
        raise ValueError("活动阶段或旧输出缺少索引证据，不能静默升级")
    return WBIntakeOutputProject.model_validate({**dict(checked), "schema_version": 14})


def intake_archive_projection(project: WBIntakeOutputProject) -> WBLayoutProject:
    """A display projection of complete figures only; the archive retains every input."""
    done = {
        s.target_id for s in project.workflow.steps if s.stage == "compose" and s.status == "done"
    }
    ids = {
        row_id
        for item in project.intake_figures
        if item.figure_id in done
        for row_id in item.row_ids
    }
    rows = tuple(row for row in project.rows if row.row_id in ids)
    if not rows:
        raise ValueError("尚无完整Fig；未生成虚假归档拼图")
    names = {row.figure for row in rows}
    columns = tuple(col for col in project.composition.columns if col.figure in names)
    compact = {number: i for i, number in enumerate(sorted({col.column for col in columns}), 1)}
    return WBLayoutProject(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        rows=rows,
        figure_order=tuple(name for name in project.figure_order if name in names),
        template=project.template,
        layout_style=project.layout_style,
        composition=FigureComposition(
            slices=tuple(part for part in project.composition.slices if part.row_id in ids),
            columns=tuple(
                FigureColumn(figure=col.figure, column=compact[col.column]) for col in columns
            ),
        ),
    )


def record_intake_output(
    project: WBIntakeOutputProject,
    prepared: IntakeOutputPreparation,
    asset: AssetRef,
    *,
    ticket: IntakeWorkflowTicket | None = None,
) -> WBIntakeOutputProject:
    """The host supplies the imported index; partial snapshots never complete the batch."""
    fields = dict(project)
    if ticket is not None:
        if ticket.stage != "export" or ticket.target_id != project.project_id:
            raise ValueError("输出回复不属于当前阶段")
        outcome = "done" if prepared.complete else "failed"
        steps = completed_intake_steps(
            project, ticket, outcome, reason="；".join(prepared.errors)[:2000]
        )
        fields["workflow"] = project.workflow.model_copy(update={"steps": steps})
        if project.workflow.cancel_requested:
            return type(project).model_validate(fields)
    elif any(s.status == "running" for s in project.workflow.steps):
        raise ValueError("活动或取消中的阶段不能接受其他输出快照")
    if (
        prepared.project_id != project.project_id
        or prepared.revision != project.revision
        or prepared.input_digest != intake_output_digest(project)
        or (asset.sha256, asset.size_bytes) != (prepared.sha256, prepared.size_bytes)
        or (
            prepared.complete
            and any(s.stage == "measure" and s.status != "done" for s in project.workflow.steps)
        )
    ):
        raise ValueError("输出索引未对应当前冻结内容、修订或已导入资产")
    evidence = IntakeOutputEvidence(
        output_id=prepared.output_id,
        input_digest=prepared.input_digest,
        index=asset,
        destination=prepared.destination,
        complete=prepared.complete,
        errors=prepared.errors,
    )
    fields["intake_outputs"] = (*project.intake_outputs, evidence)
    return type(project).model_validate(fields)


@dataclass(frozen=True)
class IntakeResultCell:
    figure_id: str
    slot_id: str
    cell: ProjectTableCell


def fill_intake_table(
    project: WBIntakeFigureProject,
    results: tuple[LoadedProjectResult, ...],
) -> tuple[IntakeResultCell, ...]:
    """Resolve by explicit identities, never a display index, label or sample guess."""
    cells = {(cell.row_id, cell.lane_index): cell for cell in fill_project_table(project, results)}
    figures = {fig.figure_id: fig for fig in project.intake.figures}
    stages = {(s.stage, s.target_id): s for s in project.workflow.steps}
    output: list[IntakeResultCell] = []
    for protein in project.intake.proteins:
        fig = figures[protein.figure_id]
        crop, measure = stages["crop", protein.protein_id], stages["measure", fig.figure_id]
        for slot in planned_intake_slots(project.project_id, protein.protein_id, fig.lane_count):
            cell = cells[protein.protein_id, slot.position]
            if cell.status in {"pending_review", "unconfigured", "not_run"}:
                failed = next(
                    (
                        s
                        for s in (crop, measure)
                        if s.status in {"failed", "cancelled", "interrupted"}
                    ),
                    None,
                )
                if failed is not None:
                    cell = replace(
                        cell,
                        status=failed.status,
                        reason=failed.reason,
                        value=None,
                        raw_integral=None,
                    )
            output.append(IntakeResultCell(fig.figure_id, slot.slot_id, cell))
    return tuple(output)
