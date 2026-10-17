"""Background-only re-planning of explicitly moved quantitative lanes."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.analysis import BandAnnotation, LaneAnnotation
from wb_tool.application.project_analysis import WBAnalysisProject
from wb_tool.application.quant_supervision import install_quant_request
from wb_tool.domain.quant_supervision import propose_quant_lanes


def replan_quant_lanes(
    path: str | Path,
    project: WBAnalysisProject,
    row_id: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> WBAnalysisProject:
    plan = next((p for p in project.analyses if p.row_id == row_id), None)
    if plan is None or plan.request.quant_policy != "wbquant_1_4_3@1":
        raise ValueError("没有新版定量计划")
    image = load_tiff(path)
    if image.sha256 != plan.request.source_sha256:
        raise ValueError("原图来源不一致")
    if cancelled():
        raise ValueError("重新规划已取消")
    proposals = propose_quant_lanes(
        image.pixels, tuple(lane.roi for lane in plan.request.lanes), plan.request.polarity
    )
    lanes: list[LaneAnnotation] = []
    for lane, proposal in zip(plan.request.lanes, proposals, strict=True):
        if cancelled():
            raise ValueError("重新规划已取消")
        if not any("geometry_changed:replan_required" in b.detection_notes for b in lane.bands):
            lanes.append(lane)
            continue
        lanes.append(
            LaneAnnotation(
                proposal.roi,
                tuple(
                    BandAnnotation(
                        "target" if n == 1 else f"target-{n}",
                        b.bounds,
                        b.baseline,
                        lane.bands[0].included,
                        b.notes,
                    )
                    for n, b in enumerate(proposal.bands, 1)
                ),
            )
        )
    return install_quant_request(project, row_id, replace(plan.request, lanes=tuple(lanes)))
