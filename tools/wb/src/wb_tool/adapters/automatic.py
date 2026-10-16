"""Load originals and produce persisted automatic row plans in a background caller."""

from collections.abc import Callable
from pathlib import Path

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.automatic import (
    WBAutomaticProject,
    install_automatic_request,
    install_automatic_result,
    suggest_analysis_for_crop,
    suggest_automatic_wb,
)
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_analysis import WBAnalysisProject
from wb_tool.domain.automatic import AutoWBSettings, CropPolicy, QuantPolicy


def automatic_project_row(
    path: str | Path,
    project: WBFigureProject,
    row_id: str,
    *,
    lane_count: int | None = None,
    crop_policy: CropPolicy = "legacy_fixed_height@1",
    quant_policy: QuantPolicy = "legacy_bounds@1",
    cancelled: Callable[[], bool] = lambda: False,
) -> WBAutomaticProject:
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or row.source is None:
        raise ValueError("此行没有原图")
    image = load_tiff(path)
    if image.sha256 != row.source.sha256:
        raise ValueError("原图摘要已改变")
    settings = AutoWBSettings(
        lane_count=lane_count,
        crop_height=project.template.crop_height,
        crop_policy=crop_policy,
        quant_policy=quant_policy,
    )
    if row.roi is not None:
        previous = (
            next((e for e in project.automatic_rows if e.row_id == row_id), None)
            if isinstance(project, WBAutomaticProject)
            else None
        )
        current_plan = (
            next(
                (
                    p
                    for p in project.analyses
                    if p.row_id == row_id and p.request.source_sha256 == image.sha256
                ),
                None,
            )
            if isinstance(project, WBAnalysisProject)
            else None
        )
        # A saved same-source plan is the latest explicit polarity choice, even
        # after geometry edits have made its measurement or automatic evidence stale.
        polarity = (
            current_plan.request.polarity
            if current_plan is not None
            else previous.settings.polarity
            if previous is not None and previous.source_sha256 == image.sha256
            else "dark"
        )
        count = lane_count or row.lane_count
        settings = AutoWBSettings(
            lane_count=count,
            crop_height=row.roi.y1 - row.roi.y0,
            polarity=polarity,
            crop_policy=previous.settings.crop_policy if previous else crop_policy,
            quant_policy=quant_policy,
        )
        request = suggest_analysis_for_crop(
            image,
            crop=row.roi,
            lane_count=count,
            revision=project.revision,
            polarity=polarity,
            empty_lanes=row.empty_lanes,
            quant_policy=quant_policy,
            cancelled=cancelled,
        )
        return install_automatic_request(project, row_id, row.roi, request, settings)
    result = suggest_automatic_wb(
        image, row_id=row_id, revision=project.revision, settings=settings, cancelled=cancelled
    )
    return install_automatic_result(project, row_id, result)
