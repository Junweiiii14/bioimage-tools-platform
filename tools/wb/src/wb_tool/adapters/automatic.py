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
from wb_tool.domain.automatic import AutoWBSettings


def automatic_project_row(
    path: str | Path,
    project: WBFigureProject,
    row_id: str,
    *,
    lane_count: int | None = None,
    cancelled: Callable[[], bool] = lambda: False,
) -> WBAutomaticProject:
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or row.source is None:
        raise ValueError("此行没有原图")
    image = load_tiff(path)
    if image.sha256 != row.source.sha256:
        raise ValueError("原图摘要已改变")
    settings = AutoWBSettings(lane_count=lane_count, crop_height=project.template.crop_height)
    if row.roi is not None:
        previous = (
            next((e for e in project.automatic_rows if e.row_id == row_id), None)
            if isinstance(project, WBAutomaticProject)
            else None
        )
        polarity = previous.settings.polarity if previous else "dark"
        count = lane_count or row.lane_count
        settings = AutoWBSettings(
            lane_count=count, crop_height=row.roi.y1 - row.roi.y0, polarity=polarity
        )
        request = suggest_analysis_for_crop(
            image,
            crop=row.roi,
            lane_count=count,
            revision=project.revision,
            polarity=polarity,
            empty_lanes=row.empty_lanes,
            cancelled=cancelled,
        )
        return install_automatic_request(project, row_id, row.roi, request, settings)
    result = suggest_automatic_wb(
        image, row_id=row_id, revision=project.revision, settings=settings, cancelled=cancelled
    )
    return install_automatic_result(project, row_id, result)
