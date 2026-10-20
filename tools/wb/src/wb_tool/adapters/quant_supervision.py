"""Background-only re-planning of explicitly moved quantitative lanes."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.analysis import BandAnnotation, LaneAnnotation
from wb_tool.application.figure_project import FigureSourcePath
from wb_tool.application.project_analysis import WBAnalysisProject
from wb_tool.application.quant_supervision import install_quant_request
from wb_tool.application.standalone_quant import ManualQuantTarget, configure_manual_quantification
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.quant_supervision import propose_quant_lane, propose_smear_lane


def reset_group_boundaries(
    project: WBAnalysisProject,
    row_id: str,
    sources: tuple[FigureSourcePath, ...],
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> WBAnalysisProject:
    """Explicitly reset a group's integration; never silently migrate old runs."""
    selected = next((r for r in project.rows if r.row_id == row_id), None)
    if selected is None:
        raise ValueError("当前分组不存在")
    paths = {s.sha256: s.path for s in sources}
    result = project
    # Load each immutable source once, releasing it before the next source.
    hashes = dict.fromkeys(
        r.source.sha256 for r in project.rows if r.figure == selected.figure and r.source
    )
    for source_hash in hashes:
        if cancelled():
            raise ValueError("重新封底已取消")
        if source_hash not in paths:
            raise ValueError("本组原图资产不可用")
        image = load_tiff(paths[source_hash])
        if image.sha256 != source_hash:
            raise ValueError("原图来源不一致")
        for row in project.rows:
            if row.figure != selected.figure or not row.source or row.source.sha256 != source_hash:
                continue
            plan = next((p for p in project.analyses if p.row_id == row.row_id), None)
            if plan is None:
                raise ValueError("请先为本组所有蛋白配置泳道")
            lanes = tuple(lane.roi for lane in plan.request.lanes)
            roi = LaneROI(
                row.row_id,
                min(r.x0 for r in lanes),
                min(r.y0 for r in lanes),
                max(r.x1 for r in lanes),
                max(r.y1 for r in lanes),
            )
            smear = any(
                "whole_lane_smear@1" in b.detection_notes
                for lane in plan.request.lanes
                for b in lane.bands
            )
            result = configure_manual_quantification(
                image,
                result,
                ManualQuantTarget(
                    source_hash,
                    project.revision,
                    roi,
                    len(lanes),
                    plan.request.polarity,
                    plan.empty_lanes,
                    True,
                    lanes,
                    "smear" if smear else "peaks",
                ),
                cancelled=cancelled,
            )
    return result


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
        "peak_envelope@1",
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
            proposal = propose_quant_lane(
                image.pixels,
                lane.roi,
                plan.request.polarity,
                complete_peaks=plan.request.quant_policy == "peak_envelope@1",
            )
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
