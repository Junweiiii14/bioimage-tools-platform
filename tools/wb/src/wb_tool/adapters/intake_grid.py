"""Aggregate verified saved Fig pixels; no quantitative resampling or source decoding."""

import json
from collections.abc import Callable

from PIL import Image

from wb_tool.adapters.intake_figure import open_intake_figure_image
from wb_tool.application.figure_project import FigureRender, FigureSourcePath
from wb_tool.application.intake_output import WBIntakeOutputProject
from wb_tool.application.intake_supervision import IntakeGrid, WBIntakeGridProject


def render_intake_grid(
    project: WBIntakeOutputProject,
    sources: tuple[FigureSourcePath, ...],
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> FigureRender:
    grid = project.grid if isinstance(project, WBIntakeGridProject) else IntakeGrid()
    order = grid.order or tuple(f.figure_id for f in project.intake.figures)
    evidence = {e.figure_id: e for e in project.intake_figures}
    done = {
        s.target_id for s in project.workflow.steps if s.stage == "compose" and s.status == "done"
    }
    if not order or any(key not in done or key not in evidence for key in order):
        raise ValueError("全部Fig尚未完成；请查看缺项，不生成缺图的完整总图")
    paths = {s.sha256: s.path for s in sources}
    columns = min(grid.columns, len(order))
    widths = [
        max(evidence[key].width for i, key in enumerate(order) if i % columns == col)
        for col in range(columns)
    ]
    heights = [
        max(evidence[key].height for key in order[i : i + columns])
        for i in range(0, len(order), columns)
    ]
    width, height = (
        sum(widths) + grid.gap * (columns - 1),
        sum(heights) + grid.gap * (len(heights) - 1),
    )
    if width * height > 32_000_000 or max(width, height) > 32768:
        raise ValueError("总图超出3200万像素/32768边长预算，请减少间距或调整每行数量")
    records: list[dict[str, object]] = []
    with Image.new("RGB", (width, height), "white") as canvas:
        for i, key in enumerate(order):
            if cancelled():
                raise ValueError("总图生成已取消")
            item = evidence[key]
            path = paths.get(item.image.sha256)
            if path is None:
                raise ValueError("Fig图像资产缺失，请重新打开项目核对")
            x = sum(widths[: i % columns]) + grid.gap * (i % columns)
            y = sum(heights[: i // columns]) + grid.gap * (i // columns)
            with open_intake_figure_image(project, key, path, cancelled=cancelled) as (image, _, _):
                canvas.paste(image, (x, y))
            records.append(
                {
                    "figure_id": key,
                    "sha256": item.image.sha256,
                    "x": x,
                    "y": y,
                    "width": item.width,
                    "height": item.height,
                }
            )
        rgb = canvas.tobytes()
    manifest = {
        "project_id": project.project_id,
        "revision": project.revision,
        "purpose": "display_only_not_quantitative",
        "aggregate": grid.model_dump(mode="json"),
        "figures": records,
        "rows": [],
    }
    return FigureRender(width, height, rgb, json.dumps(manifest))


def grid_preview(rendered: FigureRender) -> FigureRender:
    """Bound GUI encoding work while retaining the exact full layout and scale."""
    with Image.frombytes("RGB", (rendered.width, rendered.height), rendered.rgb) as image:
        image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
        width, height = image.size
        rgb = image.tobytes()
    manifest = json.loads(rendered.manifest_json)
    manifest["preview_binding"] = {
        "full_width": rendered.width,
        "full_height": rendered.height,
        "scale_x": width / rendered.width,
        "scale_y": height / rendered.height,
    }
    return FigureRender(width, height, rgb, json.dumps(manifest))
