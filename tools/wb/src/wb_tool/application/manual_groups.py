"""Manual groups share immutable source assets and retain other groups' plans."""

from dataclasses import replace
from uuid import uuid4

from wb_tool.application.analysis import BandAnnotation
from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.project_analysis import WBAnalysisProject
from wb_tool.application.quant_supervision import install_quant_request
from wb_tool.domain.quantify import BandBounds


def add_manual_group(project: WBFigureProject, source_row_id: str, name: str) -> WBFigureProject:
    name = name.strip()
    if not name or len(name) > 120 or "\n" in name or "\r" in name:
        raise ValueError("请输入单行分组名称，最多120字")
    row = next((row for row in project.rows if row.row_id == source_row_id), None)
    if row is None or row.source is None:
        raise ValueError("当前原图不可用")
    new = FigureRow(
        row_id="manual-" + uuid4().hex,
        source=row.source,
        filename=row.filename,
        width=row.width,
        height=row.height,
        bit_depth=row.bit_depth,
        figure=name,
        protein="条带",
        lane_count=1,
        notes="manual_group@1",
    )
    fields = {key: getattr(project, key) for key in type(project).model_fields}
    fields.update(
        rows=(*project.rows, new), figure_order=tuple(dict.fromkeys((*project.figure_order, name)))
    )
    return type(project).model_validate(fields)


def edit_quant_band(
    project: WBAnalysisProject,
    row_id: str,
    lane_id: str,
    action: str,
    band_id: str = "target",
    bounds: BandBounds | None = None,
) -> WBAnalysisProject:
    plan = next((p for p in project.analyses if p.row_id == row_id), None)
    if plan is None or plan.request.geometry_policy != "independent_lanes@1":
        raise ValueError("请先完成独立泳道定量")
    lane = next((lane for lane in plan.request.lanes if lane.roi.lane_id == lane_id), None)
    if lane is None:
        raise ValueError("泳道已改变")
    if action == "add":
        if bounds is None or bounds.right >= lane.roi.y1 - lane.roi.y0 or len(lane.bands) >= 64:
            raise ValueError("补峰范围无效或超过64条带预算")
        if any(
            b.bounds and not (bounds.right < b.bounds.left or b.bounds.right < bounds.left)
            for b in lane.bands
            if b.included
        ):
            raise ValueError("补峰范围与已有条带重叠；请调整已有边界")
        number = 2
        while f"manual-{number}" in {b.band_id for b in lane.bands}:
            number += 1
        bands = (
            *lane.bands,
            BandAnnotation(f"manual-{number}", bounds, detection_notes=("manually_added@1",)),
        )
        # target remains first for the historical document contract. Additional peaks
        # are ordered vertically at presentation/export, without changing stable IDs.
    elif action == "exclude":
        if not any(b.band_id == band_id for b in lane.bands):
            raise ValueError("条带已改变")
        bands = tuple(
            replace(b, included=not b.included) if b.band_id == band_id else b for b in lane.bands
        )
    else:
        raise ValueError("未知条带操作")
    changed = replace(lane, bands=bands)
    return install_quant_request(
        project,
        row_id,
        replace(
            plan.request,
            lanes=tuple(changed if x.roi.lane_id == lane_id else x for x in plan.request.lanes),
        ),
    )
