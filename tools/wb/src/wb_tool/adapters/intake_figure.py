"""Render a complete Fig, then plan existing quantitative requests on original TIFFs."""

import json
from collections.abc import Callable, Generator
from contextlib import contextmanager
from hashlib import file_digest, sha256
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.automatic import suggest_analysis_for_crop
from wb_tool.application.figure_project import FigureRender, FigureSourcePath
from wb_tool.application.intake_figure import (
    IntakeFigureEvidence,
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

if TYPE_CHECKING:
    from PIL import Image


def prepare_intake_figure(
    project: WBIntakeFigureProject,
    ticket: IntakeWorkflowTicket,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> IntakeFigurePreparation:
    from wb_tool.adapters.figure_export import render_figure
    from wb_tool.adapters.figure_image_export import publish_rendered_image

    validate_intake_workflow_ticket(project, ticket)
    if ticket.stage != "compose" or project.workflow.cancel_requested or cancelled():
        raise ValueError("完整Fig成图需要当前未取消的compose票据")
    if Path(destination).suffix.lower() != ".png":
        raise ValueError("当前Fig阶段资产须为带来源的显示PNG")
    paths = {s.sha256: s.path for s in sources}
    if len(paths) != len(sources):
        raise ValueError("Fig来源路径重复")
    projection = intake_figure_projection(project, ticket.target_id)
    # The projection has already checked every member's v1 review or v2 machine
    # provenance. Keep row.reviewed false for automatically accepted geometry.
    rendered = render_figure(projection, sources, require_review=False, cancelled=cancelled)
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


@contextmanager
def open_intake_figure_image(
    project: WBIntakeFigureProject,
    figure_id: str,
    path: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> Generator[tuple["Image.Image", IntakeFigureEvidence, dict[str, object]], None, None]:
    """Own one bounded, verified saved display image for preview or full encoding."""
    from PIL import Image

    evidence = next((e for e in project.intake_figures if e.figure_id == figure_id), None)
    if evidence is None or evidence.input_digest != intake_figure_digest(project, figure_id):
        raise ValueError("当前Fig成图尚未就绪或已过期")
    target = Path(path)
    if (
        cancelled()
        or target.stat().st_size != evidence.image.size_bytes
        or target.stat().st_size > 64 * 1024 * 1024
    ):
        raise ValueError("Fig显示资产已取消或字节数不一致")
    data = target.read_bytes()
    if sha256(data).hexdigest() != evidence.image.sha256:
        raise ValueError("Fig显示资产摘要改变")
    with Image.open(BytesIO(data), formats=("PNG",)) as image:
        if image.mode != "RGB" or image.size != (evidence.width, evidence.height):
            raise ValueError("Fig显示资产尺寸或模式不一致")
        provenance = image.info.get("wb_provenance")
        if not isinstance(provenance, str):
            raise ValueError("Fig显示资产缺少来源记录")
        manifest = TypeAdapter(dict[str, object]).validate_json(provenance)
        if manifest.get("project_id") != project.project_id:
            raise ValueError("Fig显示资产来源记录无效")
        yield image, evidence, manifest
    if cancelled():
        raise ValueError("Fig显示已取消")


def load_intake_figure_render(
    project: WBIntakeFigureProject,
    figure_id: str,
    path: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> FigureRender:
    """Reuse exact saved full pixels; the display asset never becomes quantitative."""
    with open_intake_figure_image(project, figure_id, path, cancelled=cancelled) as (
        image,
        evidence,
        manifest,
    ):
        manifest["export_binding"] = {
            "policy": "intake_saved_figure@1",
            "revision": project.revision,
            "figure_id": figure_id,
            "input_digest": evidence.input_digest,
            "asset_sha256": evidence.image.sha256,
        }
        return FigureRender(
            image.width, image.height, image.tobytes(), json.dumps(manifest, ensure_ascii=True)
        )


def load_intake_figure_preview(
    project: WBIntakeFigureProject,
    figure_id: str,
    path: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> FigureRender:
    """Read the immutable completed PNG, retaining source provenance and scaled hit boxes."""
    from PIL import Image

    with open_intake_figure_image(project, figure_id, path, cancelled=cancelled) as (
        image,
        evidence,
        manifest,
    ):
        rows = TypeAdapter(tuple[dict[str, object], ...]).validate_python(manifest.get("rows"))
        image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
        width, height = image.size
        rgb = image.tobytes()
    sx, sy = width / evidence.width, height / evidence.height
    for row in rows:
        box = TypeAdapter(tuple[float, float, float, float] | None).validate_python(
            row.get("output_box")
        )
        if box:
            row["preview_output_box"] = [box[0] * sx, box[1] * sy, box[2] * sx, box[3] * sy]
        matrix = TypeAdapter(
            tuple[tuple[float, float, float], tuple[float, float, float]] | None
        ).validate_python(row.get("source_to_output"))
        if matrix:
            row["preview_source_to_output"] = [
                [value * sx for value in matrix[0]],
                [value * sy for value in matrix[1]],
            ]
    manifest["rows"] = rows
    manifest["preview_binding"] = {
        "revision": project.revision,
        "figure_id": figure_id,
        "input_digest": evidence.input_digest,
        "asset_sha256": evidence.image.sha256,
        "scale_x": sx,
        "scale_y": sy,
    }
    if cancelled():
        raise ValueError("Fig显示已取消")
    return FigureRender(width, height, rgb, json.dumps(manifest, ensure_ascii=False))
