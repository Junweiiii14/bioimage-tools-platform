"""Background-only re-planning of explicitly moved quantitative lanes."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.analysis import BandAnnotation, LaneAnnotation
from wb_tool.application.project_analysis import WBAnalysisProject
from wb_tool.application.quant_supervision import install_quant_request
from wb_tool.domain.quant_supervision import propose_quant_lane, propose_smear_lane


def replan_quant_lanes(
    path: str | Path,
    project: WBAnalysisProject,
    row_id: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> WBAnalysisProject:
    plan = next((p for p in project.analyses if p.row_id == row_id), None)
    if plan is None or plan.request.quant_policy not in (
        "wbquant_1_4_3@1",
        "background_support@1",
        "anchored_background@1",
    ):
        raise ValueError("没有新版定量计划")
    image = load_tiff(path)
    if image.sha256 != plan.request.source_sha256:
        raise ValueError("原图来源不一致")
    if cancelled():
        raise ValueError("重新规划已取消")
    if plan.request.quant_policy == "anchored_background@1":
        from wb_tool.application.automatic import suggest_analysis_for_crop

        generated = suggest_analysis_for_crop(
            image,
            crop=plan.crop,
            lane_count=len(plan.request.lanes),
            revision=plan.request.revision,
            polarity=plan.request.polarity,
            empty_lanes=plan.empty_lanes,
            quant_policy=plan.request.quant_policy,
            lane_rois=tuple(lane.target_roi or lane.roi for lane in plan.request.lanes),
            cancelled=cancelled,
        )
        request = replace(
            plan.request,
            lanes=tuple(
                replace(new, bands=(replace(new.bands[0], included=old.bands[0].included),))
                if any("geometry_changed:replan_required" in b.detection_notes for b in old.bands)
                else old
                for old, new in zip(plan.request.lanes, generated.lanes, strict=True)
            ),
        )
        return install_quant_request(project, row_id, request)
    from wb_tool.domain.background_bounds import propose_background_lanes

    lanes: list[LaneAnnotation] = []
    for lane in plan.request.lanes:
        if cancelled():
            raise ValueError("重新规划已取消")
        if not any("geometry_changed:replan_required" in b.detection_notes for b in lane.bands):
            lanes.append(lane)
            continue
        if any("whole_lane_smear@1" in b.detection_notes for b in lane.bands):
            proposal = propose_smear_lane(image.pixels, lane.roi, plan.request.polarity)
        elif plan.request.quant_policy == "background_support@1":
            proposal = propose_background_lanes(image.pixels, (lane.roi,), plan.request.polarity)[0]
        else:
            proposal = propose_quant_lane(image.pixels, lane.roi, plan.request.polarity)
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
