"""Saved explicit sample pairs, with derived values rebuilt from verified measurement evidence."""

from dataclasses import dataclass, replace
from typing import Literal

from pydantic import Field, model_validator

from wb_tool.application.crop_suggestions import WBReviewProject
from wb_tool.application.document import DocumentIO
from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    ProjectTableCell,
    WBAnalysisProject,
    fill_project_table,
)
from wb_tool.application.project_ocr import (
    LoadedProjectOCR,
    WBProjectOCR,
    fill_project_ocr_table,
)
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.normalization import NORMALIZATION_ALGORITHM, control_mean, signal_ratio

ReferenceKind = Literal["housekeeping", "phospho_total"]
ControlMode = Literal["ratio_only", "single_control", "control_mean"]


class NormalizationSource(DocumentIO):
    row_id: str = Field(min_length=1, max_length=80)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    crop: LaneROI
    lane_count: int = Field(ge=1, le=96)

    @model_validator(mode="after")
    def identity(self) -> "NormalizationSource":
        if self.crop.lane_id != self.row_id or self.crop.width < self.lane_count:
            raise ValueError("归一化来源身份或泳道数无效")
        return self


class SamplePair(DocumentIO):
    target_lane: int = Field(ge=1, le=96)
    sample: str = Field(default="", max_length=128)
    reference_lane: int | None = Field(default=None, ge=1, le=96)
    included: bool = True
    control: bool = False


class NormalizationPlan(DocumentIO):
    target: NormalizationSource
    reference: NormalizationSource
    kind: ReferenceKind
    control_mode: ControlMode = "ratio_only"
    pairs: tuple[SamplePair, ...] = Field(min_length=1, max_length=96)
    confirmed: bool = False
    notes: str = Field(default="", max_length=2000)
    algorithm_id: Literal["lane_reference_ratio@1"] = NORMALIZATION_ALGORITHM

    @model_validator(mode="after")
    def coherent(self) -> "NormalizationPlan":
        if self.target.row_id == self.reference.row_id:
            raise ValueError("目标与参照必须是不同的蛋白行")
        if tuple(p.target_lane for p in self.pairs) != tuple(range(1, self.target.lane_count + 1)):
            raise ValueError("须保留目标行全部固定泳道槽及顺序")
        references = [p.reference_lane for p in self.pairs if p.included and p.reference_lane]
        if any(n > self.reference.lane_count for n in references) or len(references) != len(
            set(references)
        ):
            raise ValueError("所含样本须一对一关联已有参照泳道")
        samples = [p.sample.strip() for p in self.pairs if p.included and p.sample.strip()]
        if len(samples) != len(set(samples)):
            raise ValueError("同一关系内样本名称必须唯一；重复样本请明确重复编号")
        if any(p.control and not p.included for p in self.pairs):
            raise ValueError("排除样本不能作为对照")
        return self


class WBNormalizedProject(WBProjectOCR):
    schema_version: int = Field(default=5, ge=5, le=5)
    normalizations: tuple[NormalizationPlan, ...] = Field(default=(), max_length=512)

    @model_validator(mode="after")
    def unique_targets(self) -> "WBNormalizedProject":
        if len({p.target.row_id for p in self.normalizations}) != len(self.normalizations):
            raise ValueError("同一目标行只能有一个当前归一化配置")
        return self


def project_with_normalizations(
    project: WBFigureProject, plans: tuple[NormalizationPlan, ...]
) -> WBNormalizedProject:
    return WBNormalizedProject(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        rows=project.rows,
        figure_order=project.figure_order,
        template=project.template,
        suggestions=project.suggestions if isinstance(project, WBReviewProject) else (),
        analyses=project.analyses if isinstance(project, WBAnalysisProject) else (),
        ocr=project.ocr if isinstance(project, WBProjectOCR) else None,
        normalizations=plans,
    )


def normalization_source(row: FigureRow) -> NormalizationSource:
    if not row.source or not row.roi or not row.reviewed:
        raise ValueError("请先审核目标和参照原图的裁剪行")
    return NormalizationSource(
        row_id=row.row_id, source_sha256=row.source.sha256, crop=row.roi, lane_count=row.lane_count
    )


def make_normalization_plan(
    project: WBFigureProject, target_id: str, reference_id: str, kind: ReferenceKind
) -> NormalizationPlan:
    rows = {r.row_id: r for r in project.rows}
    if target_id not in rows or reference_id not in rows:
        raise ValueError("请选择已有目标和参照行")
    target, reference = rows[target_id], rows[reference_id]
    return NormalizationPlan(
        target=normalization_source(target),
        reference=normalization_source(reference),
        kind=kind,
        pairs=tuple(
            SamplePair(target_lane=i, included=i not in target.empty_lanes)
            for i in range(1, target.lane_count + 1)
        ),
    )


def normalization_is_current(project: WBFigureProject, plan: NormalizationPlan) -> bool:
    rows = {r.row_id: r for r in project.rows}
    for source in (plan.target, plan.reference):
        row = rows.get(source.row_id)
        if row is None or not row.reviewed or row.source is None or row.roi is None:
            return False
        if normalization_source(row) != source:
            return False
    return True


@dataclass(frozen=True)
class NormalizedCell:
    target_row_id: str
    reference_row_id: str
    figure: str
    protein: str
    sample: str
    target_lane: int
    reference_lane: int | None
    control: bool
    kind: ReferenceKind
    control_mode: ControlMode
    target: ProjectTableCell | None
    reference: ProjectTableCell | None
    ratio: float | None = None
    ratio_status: str = "unconfigured"
    ratio_reason: str = ""
    control_mean: float | None = None
    relative: float | None = None
    relative_status: str = "not_requested"
    relative_reason: str = ""
    control_samples: tuple[str, ...] = ()
    ocr_row_id: str = ""
    algorithm_id: str = NORMALIZATION_ALGORITHM


@dataclass(frozen=True)
class NormalizationSnapshot:
    cells: tuple[NormalizedCell, ...] = ()
    ocr_cells: tuple[NormalizedCell, ...] = ()


def _ratio(
    cell: NormalizedCell, plan: NormalizationPlan, pair: SamplePair, current: bool
) -> NormalizedCell:
    status = reason = ""
    if not current:
        status, reason = "stale", "来源/裁剪/泳道或审核已改变，请重建关联"
    elif not plan.confirmed:
        status, reason = "pending_review", "尚未确认参照与样本对应"
    elif not pair.included:
        status, reason = "excluded", "该样本已排除"
    elif not pair.sample.strip() or pair.reference_lane is None:
        status, reason = "unmatched", "缺少样本名或对应参照泳道"
    elif cell.target is None or cell.target.status != "valid" or cell.target.value is None:
        status, reason = (
            "invalid_target",
            "目标测量不可用："
            + (cell.target.reason or cell.target.status if cell.target else "缺少行"),
        )
    elif cell.reference is None or cell.reference.status != "valid" or cell.reference.value is None:
        status, reason = (
            "invalid_reference",
            "参照测量不可用："
            + (cell.reference.reason or cell.reference.status if cell.reference else "缺少行"),
        )
    else:
        try:
            return replace(
                cell,
                ratio=signal_ratio(cell.target.value, cell.reference.value),
                ratio_status="valid",
            )
        except ValueError as error:
            status, reason = "invalid_ratio", str(error)
    return replace(cell, ratio_status=status, ratio_reason=reason)


def _controls(cells: tuple[NormalizedCell, ...], mode: ControlMode) -> tuple[NormalizedCell, ...]:
    if mode == "ratio_only":
        return cells
    controls = tuple(c for c in cells if c.control)
    names = tuple(c.sample for c in controls)
    reason = ""
    mean = None
    if not controls or (mode == "single_control" and len(controls) != 1):
        reason = "请选择恰好一个对照" if mode == "single_control" else "尚未选择对照样本"
    elif any(c.ratio_status != "valid" or c.ratio is None for c in controls):
        reason = "有选中的对照无有效比值；未跳过该对照"
    else:
        try:
            mean = control_mean(tuple(c.ratio for c in controls if c.ratio is not None))
        except ValueError as error:
            reason = str(error)
    output: list[NormalizedCell] = []
    for cell in cells:
        value = None
        status, detail = "control_unavailable", reason
        if cell.ratio is None:
            status, detail = cell.ratio_status, cell.ratio_reason
        elif mean is not None:
            try:
                value = signal_ratio(cell.ratio, mean)
                status, detail = "valid", ""
            except ValueError as error:
                status, detail = "invalid_ratio", str(error)
        output.append(
            replace(
                cell,
                control_mean=mean,
                control_samples=names,
                relative=value,
                relative_status=status,
                relative_reason=detail,
            )
        )
    return tuple(output)


def fill_project_normalization(
    project: WBNormalizedProject,
    results: tuple[LoadedProjectResult, ...],
    loaded_ocr: LoadedProjectOCR | None = None,
) -> NormalizationSnapshot:
    measured = {(c.row_id, c.lane_index): c for c in fill_project_table(project, results)}
    rows = {r.row_id: r for r in project.rows}
    values: list[NormalizedCell] = []
    for plan in project.normalizations:
        current = normalization_is_current(project, plan)
        row = rows.get(plan.target.row_id)
        cells: list[NormalizedCell] = []
        for pair in plan.pairs:
            cell = NormalizedCell(
                plan.target.row_id,
                plan.reference.row_id,
                row.figure if row else "已删除",
                row.protein if row else "已删除",
                pair.sample,
                pair.target_lane,
                pair.reference_lane,
                pair.control,
                plan.kind,
                plan.control_mode,
                measured.get((plan.target.row_id, pair.target_lane)),
                measured.get((plan.reference.row_id, pair.reference_lane))
                if pair.reference_lane
                else None,
            )
            cells.append(_ratio(cell, plan, pair, current))
        values.extend(_controls(tuple(cells), plan.control_mode))
    ocr_cells: list[NormalizedCell] = []
    if project.ocr:
        by_target = {(c.target_row_id, c.target_lane): c for c in values}
        labels = {r.row_id: r for r in project.ocr.rows}
        for evidence in fill_project_ocr_table(project, results, loaded_ocr):
            row = labels[evidence.row_id]
            if row.link is None:
                continue
            original = by_target.get((row.link.target_row_id, evidence.lane_index))
            if original is None:
                continue
            named = replace(original, figure=row.figure, protein=row.protein, ocr_row_id=row.row_id)
            if evidence.status != "valid":
                named = replace(
                    named,
                    target=None,
                    reference=None,
                    ratio=None,
                    relative=None,
                    control_mean=None,
                    ratio_status=evidence.status,
                    ratio_reason=evidence.reason,
                    relative_status=evidence.status,
                    relative_reason=evidence.reason,
                )
            ocr_cells.append(named)
    return NormalizationSnapshot(tuple(values), tuple(ocr_cells))
