"""Explicit batch supervision and display-only aggregate layout, schema15."""

from pydantic import Field, model_validator

from wb_tool.application.document import DocumentIO
from wb_tool.application.intake_figure import WBIntakeFigureProject
from wb_tool.application.intake_output import WBIntakeOutputProject
from wb_tool.application.intake_workflow import IntakeWorkflowStep
from wb_tool.application.quant_supervision import update_quant_lane
from wb_tool.domain.quantify import BandBounds, Baseline


class IntakeGrid(DocumentIO):
    policy: str = Field(default="intake_grid@1", pattern="^intake_grid@1$")
    columns: int = Field(default=3, ge=1, le=12)
    gap: int = Field(default=40, ge=2, le=1000)
    order: tuple[str, ...] = Field(default=(), max_length=512)


class WBIntakeGridProject(WBIntakeOutputProject):
    schema_version: int = Field(default=15, ge=15, le=15)
    grid: IntakeGrid = Field(default_factory=IntakeGrid)

    @model_validator(mode="after")
    def grid_identities(self) -> "WBIntakeGridProject":
        ids = {f.figure_id for f in self.intake.figures}
        if self.grid.order and (set(self.grid.order) != ids or len(self.grid.order) != len(ids)):
            raise ValueError("总图顺序必须包含全部Fig且不重复")
        return self


def _invalidate(project: WBIntakeFigureProject, figure_id: str = "") -> WBIntakeFigureProject:
    if project.workflow.editing or any(s.status == "running" for s in project.workflow.steps):
        raise ValueError("请等待当前阶段结束并退出分组编辑")
    steps = tuple(
        IntakeWorkflowStep(stage=s.stage, target_id=s.target_id, attempt=s.attempt)
        if s.stage == "export" or (s.stage == "measure" and s.target_id == figure_id)
        else s
        for s in project.workflow.steps
    )
    return type(project).model_validate(
        {
            **dict(project),
            "workflow": project.workflow.model_copy(
                update={
                    "steps": steps,
                    "approved": False,
                    "cancel_requested": False,
                }
            ),
        }
    )


def revise_intake_quant(
    project: WBIntakeFigureProject,
    row_id: str,
    lane_id: str,
    *,
    band_id: str,
    bounds: BandBounds,
    baseline: Baseline,
) -> WBIntakeFigureProject:
    protein = next((p for p in project.intake.proteins if p.protein_id == row_id), None)
    if protein is None:
        raise ValueError("蛋白身份不属于当前批次")
    if not any(
        s.stage == "compose" and s.target_id == protein.figure_id and s.status == "done"
        for s in project.workflow.steps
    ):
        raise ValueError("请先完成所属Fig成图")
    updated = update_quant_lane(
        _invalidate(project, protein.figure_id),
        row_id,
        lane_id,
        bounds=bounds,
        baseline=baseline,
        band_id=band_id,
    )
    if not isinstance(updated, WBIntakeFigureProject):
        raise ValueError("批次定量类型丢失")
    return updated


def revise_intake_grid(project: WBIntakeOutputProject, grid: IntakeGrid) -> WBIntakeGridProject:
    checked = _invalidate(project)
    return WBIntakeGridProject.model_validate(
        {
            **dict(checked),
            "schema_version": 15,
            "grid": grid,
        }
    )
