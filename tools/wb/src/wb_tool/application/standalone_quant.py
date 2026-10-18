"""Explicit manual measurement targets, independent of crop detection and rendering."""

from collections.abc import Callable
from dataclasses import dataclass

from wb_tool.application.analysis import QuantitativeImage
from wb_tool.application.automatic import WBAutomaticProject, suggest_analysis_for_crop
from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.laboratory_layout import (
    FigureComposition,
    WBLayoutProject,
    preserve_automatic_composition,
    with_figure_layout,
)
from wb_tool.application.project_analysis import (
    ProjectRowAnalysis,
    WBAnalysisProject,
    analysis_is_current,
    set_row_analysis,
)
from wb_tool.domain.lanes import LaneROI, Polarity


@dataclass(frozen=True, slots=True)
class ManualQuantTarget:
    source_sha256: str
    revision: int
    roi: LaneROI
    lane_count: int
    polarity: Polarity
    empty_lanes: tuple[int, ...] = ()
    reset_bounds: bool = False

    def __post_init__(self) -> None:
        if type(self.reset_bounds) is not bool:
            raise ValueError("重置边界须为明确布尔值")
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("测量目标须绑定非负整数修订")
        if type(self.lane_count) is not int or not 1 <= self.lane_count <= 96:
            raise ValueError("泳道数须为1–96的整数")
        if self.polarity not in ("dark", "light"):
            raise ValueError("请选择暗条带或亮条带")
        if any(
            type(value) is not int for value in (self.roi.x0, self.roi.y0, self.roi.x1, self.roi.y1)
        ):
            raise ValueError("测量区域须使用原图整数像素")
        if self.roi.width < self.lane_count or not 2 <= self.roi.y1 - self.roi.y0 <= 4096:
            raise ValueError("测量区域须容纳全部泳道，高度须为2–4096原图像素")
        if (
            type(self.empty_lanes) is not tuple
            or any(type(n) is not int or not 1 <= n <= self.lane_count for n in self.empty_lanes)
            or len(set(self.empty_lanes)) != len(self.empty_lanes)
        ):
            raise ValueError("排除泳道须为不重复的1–N整数编号")


def configure_manual_quantification(
    image: QuantitativeImage,
    project: WBFigureProject,
    target: ManualQuantTarget,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> WBAnalysisProject:
    """Install a user-confirmed target without detecting a membrane or composing.

    Existing schema7 already stores each row's own target height. Only that row's
    current run/proposal is superseded; immutable storage history is not touched.
    """
    if cancelled():
        raise ValueError("独立灰度配置已取消")
    row = next((row for row in project.rows if row.row_id == target.roi.lane_id), None)
    if (
        row is None
        or row.source is None
        or target.revision != project.revision
        or target.source_sha256 != row.source.sha256
        or image.sha256 != row.source.sha256
        or image.pixels.shape != (row.height, row.width)
        or image.pixels.dtype.itemsize * 8 != row.bit_depth
    ):
        raise ValueError("测量目标的原图、尺寸、位深或项目修订已改变")
    fields = row.model_dump()
    fields.update(
        roi=target.roi,
        lane_count=target.lane_count,
        empty_lanes=target.empty_lanes,
        reviewed=True,
    )
    changed = FigureRow.model_validate(fields)
    previous = project.analyses if isinstance(project, WBAnalysisProject) else ()
    old_plan = next((plan for plan in previous if plan.row_id == row.row_id), None)
    if (
        isinstance(project, WBAnalysisProject)
        and not target.reset_bounds
        and old_plan is not None
        and analysis_is_current(project, old_plan)
        and row.roi == target.roi
        and row.lane_count == target.lane_count
        and row.empty_lanes == target.empty_lanes
        and old_plan.request.polarity == target.polarity
    ):
        # Re-measuring an unchanged target must retain manually adjusted bounds.
        return project
    request = suggest_analysis_for_crop(
        image,
        crop=target.roi,
        lane_count=target.lane_count,
        revision=target.revision,
        polarity=target.polarity,
        empty_lanes=target.empty_lanes,
        quant_policy="anchored_background@1",
        cancelled=cancelled,
    )
    composition = (
        project.composition if isinstance(project, WBLayoutProject) else FigureComposition()
    )
    upgraded = with_figure_layout(project, composition)
    values = {name: getattr(upgraded, name) for name in type(upgraded).model_fields}
    values.update(
        rows=tuple(changed if item.row_id == row.row_id else item for item in project.rows),
        analyses=tuple(plan for plan in previous if plan.row_id != row.row_id),
    )
    if isinstance(upgraded, WBAutomaticProject):
        # This target is explicitly chosen by a person, not an automatic detection.
        values["automatic_rows"] = tuple(
            evidence for evidence in upgraded.automatic_rows if evidence.row_id != row.row_id
        )
    updated = type(upgraded).model_validate(values)
    geometry_changed = row.roi != target.roi or row.lane_count != target.lane_count
    if composition.slices:
        composition = preserve_automatic_composition(
            updated, row.row_id, geometry_changed=geometry_changed
        )
        updated = with_figure_layout(updated, composition)
    if cancelled():
        raise ValueError("独立灰度配置已取消")
    return set_row_analysis(
        updated,
        ProjectRowAnalysis(
            row_id=row.row_id,
            crop=target.roi,
            empty_lanes=target.empty_lanes,
            request=request,
        ),
    )
