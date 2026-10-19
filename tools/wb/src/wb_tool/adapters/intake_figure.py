"""Render a complete Fig, then plan existing quantitative requests on original TIFFs."""

from collections.abc import Callable
from hashlib import file_digest
from pathlib import Path

from wb_tool.adapters.figure_export import render_figure
from wb_tool.adapters.figure_image_export import publish_rendered_image
from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.automatic import suggest_analysis_for_crop
from wb_tool.application.figure_project import FigureSourcePath
from wb_tool.application.intake_figure import (
    IntakeFigurePreparation,
    WBIntakeFigureProject,
    intake_figure_digest,
    intake_figure_projection,
    intake_figure_rows,
)
from wb_tool.application.intake_workflow import (
    IntakeWorkflowTicket,
    validate_intake_workflow_ticket,
)
from wb_tool.application.project_analysis import ProjectRowAnalysis


def prepare_intake_figure(
    project: WBIntakeFigureProject,
    ticket: IntakeWorkflowTicket,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> IntakeFigurePreparation:
    validate_intake_workflow_ticket(project, ticket)
    if ticket.stage != "compose" or project.workflow.cancel_requested or cancelled():
        raise ValueError("完整Fig成图需要当前未取消的compose票据")
    if Path(destination).suffix.lower() != ".png":
        raise ValueError("当前Fig阶段资产须为带来源的显示PNG")
    paths = {s.sha256: s.path for s in sources}
    if len(paths) != len(sources):
        raise ValueError("Fig来源路径重复")
    projection = intake_figure_projection(project, ticket.target_id)
    rendered = render_figure(projection, sources, cancelled=cancelled)
    plans: list[ProjectRowAnalysis] = []
    crops = {e.row_id: e for e in project.intake_crops}
    for row in intake_figure_rows(project, ticket.target_id):
        if cancelled():
            raise ValueError("Fig成图已取消")
        if row.source is None or row.roi is None or row.source.sha256 not in paths:
            raise ValueError("Fig缺少当前行原图")
        original = load_tiff(paths[row.source.sha256])
        if (original.sha256, original.pixels.shape, original.bit_depth) != (
            row.source.sha256,
            (row.height, row.width),
            row.bit_depth,
        ):
            raise ValueError("Fig原图身份、尺寸或位深改变")
        evidence = crops[row.row_id]
        geometry = tuple(s.roi for s in evidence.slots if s.roi is not None)
        if len(geometry) != row.lane_count:
            raise ValueError("Fig不能从未定位槽位发起测量")
        request = suggest_analysis_for_crop(
            original,
            crop=row.roi,
            lane_count=row.lane_count,
            revision=project.revision,
            polarity=evidence.detection.settings.polarity if evidence.detection else "dark",
            empty_lanes=row.empty_lanes,
            lane_rois=geometry,
            quant_policy="anchored_background@1",
            cancelled=cancelled,
        )
        plans.append(
            ProjectRowAnalysis(
                row_id=row.row_id, crop=row.roi, empty_lanes=row.empty_lanes, request=request
            )
        )
    output = publish_rendered_image(
        rendered, project.template.dpi, destination, cancelled=cancelled
    )
    path = Path(output)
    with path.open("rb") as stream:
        digest = file_digest(stream, "sha256").hexdigest()
    if cancelled():
        raise ValueError("Fig成图已取消，临时产物不安装")
    return IntakeFigurePreparation(
        path=output,
        sha256=digest,
        size_bytes=path.stat().st_size,
        figure_id=ticket.target_id,
        input_digest=intake_figure_digest(project, ticket.target_id),
        width=rendered.width,
        height=rendered.height,
        analyses=tuple(plans),
    )
