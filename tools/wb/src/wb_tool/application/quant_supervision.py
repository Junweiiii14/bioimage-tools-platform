"""Explicit edits of independent original-pixel lanes, with stale-run invalidation."""

from dataclasses import replace

from wb_tool.application.analysis import AnalysisRequest, BandAnnotation, LaneAnnotation
from wb_tool.application.automatic import WBAutomaticProject
from wb_tool.application.project_analysis import (
    ProjectRowAnalysis,
    WBAnalysisProject,
    analysis_is_current,
    project_with_analyses,
)
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.quantify import BandBounds, Baseline


def install_quant_request(
    project: WBAnalysisProject, row_id: str, request: AnalysisRequest
) -> WBAnalysisProject:
    """Keep automatic geometry provenance aligned with an explicit supervised edit."""
    plan = next((p for p in project.analyses if p.row_id == row_id), None)
    if plan is None or not analysis_is_current(project, plan):
        raise ValueError("定量计划已过期，请先重新规划")
    if (
        request.source_sha256 != plan.request.source_sha256
        or request.revision != plan.request.revision
    ):
        raise ValueError("不能更换来源或运行修订")
    if request.geometry_policy not in (
        "independent_lanes@1",
        "anchored_context@1",
    ) or request.quant_policy not in (
        "wbquant_1_4_3@1",
        "background_support@1",
        "anchored_background@1",
    ):
        raise ValueError("此入口仅支持新版独立泳道策略")
    if tuple(item.roi.lane_id for item in request.lanes) != tuple(
        item.roi.lane_id for item in plan.request.lanes
    ):
        raise ValueError("不能改变泳道身份或数量")
    updated = ProjectRowAnalysis(
        row_id=row_id, crop=plan.crop, empty_lanes=plan.empty_lanes, request=request
    )
    result = project_with_analyses(
        project, tuple(updated if p.row_id == row_id else p for p in project.analyses)
    )
    if isinstance(result, WBAutomaticProject):
        fields = {name: getattr(result, name) for name in type(result).model_fields}
        fields["automatic_rows"] = tuple(
            e.model_copy(update={"request": request}) if e.row_id == row_id else e
            for e in result.automatic_rows
        )
        result = type(result).model_validate(fields)
    return result


def update_quant_lane(
    project: WBAnalysisProject,
    row_id: str,
    lane_id: str,
    *,
    roi: LaneROI | None = None,
    bounds: BandBounds | None = None,
    baseline: Baseline | None = None,
    band_id: str = "target",
    included: bool | None = None,
) -> WBAnalysisProject:
    """Geometry edits invalidate boundaries; background replan must precede measure.

    A baseline of None with explicit bounds resets endpoint baselines. Without bounds,
    a baseline edits only the selected band. No change marks a human review complete.
    """
    plan = next((p for p in project.analyses if p.row_id == row_id), None)
    if plan is None:
        raise ValueError("没有定量计划")
    lane = next((item for item in plan.request.lanes if item.roi.lane_id == lane_id), None)
    if lane is None or not any(b.band_id == band_id for b in lane.bands):
        raise ValueError("泳道或条带不存在")
    if roi is not None and roi.lane_id != lane_id:
        raise ValueError("不能更换泳道身份")
    geometry_changed = roi is not None and roi != (lane.target_roi or lane.roi)
    if not geometry_changed and bounds is None and baseline is None and included is None:
        return project
    if geometry_changed:
        bands = (
            BandAnnotation(
                "target",
                None,
                included=lane.bands[0].included,
                detection_notes=(
                    "geometry_changed:replan_required",
                    *(
                        ("whole_lane_smear@1",)
                        if any("whole_lane_smear@1" in b.detection_notes for b in lane.bands)
                        else ()
                    ),
                ),
            ),
        )
    else:
        bands = tuple(
            replace(
                b,
                bounds=bounds if bounds is not None else b.bounds,
                baseline=baseline if bounds is not None or baseline is not None else b.baseline,
                included=b.included if included is None else included,
                detection_notes=tuple(
                    dict.fromkeys(
                        (
                            *(
                                note
                                for note in b.detection_notes
                                if not (bounds is not None or baseline is not None)
                                or not note.startswith("boundary_review:")
                            ),
                            "manually_adjusted",
                        )
                    )
                ),
            )
            if b.band_id == band_id
            else b
            for b in lane.bands
        )
    changed = LaneAnnotation(
        roi if geometry_changed and roi is not None else lane.roi,
        bands,
        (roi if geometry_changed else lane.target_roi)
        if plan.request.geometry_policy == "anchored_context@1"
        else None,
        0 if geometry_changed else lane.context_expansion_percent,
    )
    request = replace(
        plan.request,
        lanes=tuple(
            changed if item.roi.lane_id == lane_id else item for item in plan.request.lanes
        ),
    )
    return install_quant_request(project, row_id, request)
