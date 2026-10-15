"""Render explicit segments without resampling or changing any quantitative source."""

import json
from collections.abc import Callable
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.figure_project import FigureRender, FigureSourcePath
from wb_tool.application.laboratory_layout import WBLayoutProject, plan_laboratory_layout


def render_laboratory_figure(
    project: WBLayoutProject,
    sources: tuple[FigureSourcePath, ...],
    *,
    require_review: bool = True,
    cancelled: Callable[[], bool] = lambda: False,
) -> FigureRender:
    layout = plan_laboratory_layout(project, require_review=require_review)
    paths = {source.sha256: source.path for source in sources}
    if any(paths[source.sha256] != source.path for source in sources):
        raise ValueError("同一来源摘要对应多个路径")
    template, style = project.template, project.layout_style
    required = {row.source.sha256 for row in project.rows if row.source}
    if template.font:
        required.add(template.font.sha256)
    if not required.issubset(paths):
        raise ValueError("缺少拼图原图或字体来源路径")
    font_hash = "pillow-12.3.0-bundled-aileron"
    if template.font:
        path = Path(paths[template.font.sha256])
        if path.stat().st_size > 32 * 1024 * 1024:
            raise ValueError("字体文件超出32MiB预算")
        data = path.read_bytes()
        font_hash = sha256(data).hexdigest()
        if font_hash != template.font.sha256 or len(data) != template.font.size_bytes:
            raise ValueError("字体摘要或字节数不一致")
        label_font = ImageFont.truetype(BytesIO(data), template.font_size)
        heading_font = ImageFont.truetype(BytesIO(data), style.heading_size)
    else:
        if any(
            ord(c) > 255
            for text in (*project.figure_order, *(r.protein for r in project.rows))
            for c in text
        ):
            raise ValueError("这些标签需要导入支持相应文字的TTF/OTF/TTC字体")
        label_font = ImageFont.load_default(size=template.font_size)
        heading_font = ImageFont.load_default(size=style.heading_size)
    canvas = Image.new("RGB", (layout.width, layout.height), "white")
    draw = ImageDraw.Draw(canvas)
    for panel in layout.placements:
        bounds = heading_font.getbbox(panel.figure)
        if (
            draw.textlength(panel.figure, font=heading_font) > panel.width
            or bounds[3] - bounds[1] > style.heading_size
        ):
            raise ValueError("Fig标题超出留白，请调整字号或布局")
        draw.text((panel.x, panel.y), panel.figure, font=heading_font, fill="black", anchor="lt")
    records: list[dict[str, object]] = []
    for line in layout.lines:
        bounds = label_font.getbbox(line.label)
        if (
            draw.textlength(line.label, font=label_font) > template.label_width - 20
            or bounds[3] - bounds[1] > line.height
        ):
            raise ValueError(f"{line.label} 标签超出留白，请调整标签区/字号或原ROI高度")
        draw.text(
            (line.label_x, line.label_y),
            line.label,
            font=label_font,
            fill="black",
            anchor="rm" if style.label_alignment == "right" else "lm",
        )
        for placed in line.segments:
            if cancelled():
                raise ValueError("拼图任务已取消，未发布输出")
            row, segment, roi = placed.row, placed.segment, placed.roi
            x0, y0, x1, y1 = placed.output_box
            b = template.border
            draw.rectangle((x0 - b, y0 - b, x1 + b - 1, y1 + b - 1), outline="black", width=b)
            record: dict[str, object] = {
                "row_id": row.row_id,
                "figure": row.figure,
                "protein": row.protein,
                "display_line": segment.line,
                "segment_position": segment.position,
                "source_sha256": row.source.sha256 if row.source else None,
                "crop_file": f"crops/{project.rows.index(row) + 1:04d}.tif" if row.source else None,
                "crop_file_scope": "complete_original_row",
                "roi": None,
                "output_box": list(placed.output_box),
                "source_lane_range": [segment.first_lane, segment.last_lane],
                "lane_count": row.lane_count,
                "empty_lanes": row.empty_lanes,
                "reviewed": row.reviewed,
                "status": "present" if row.source else "missing",
            }
            if row.source and roi:
                original = load_tiff(paths[row.source.sha256])
                if (
                    original.sha256 != row.source.sha256
                    or original.source.stat().st_size != row.source.size_bytes
                    or original.pixels.shape != (row.height, row.width)
                    or original.bit_depth != row.bit_depth
                ):
                    raise ValueError("拼图原图摘要/字节数/尺寸/位深不一致")
                crop = original.pixels[roi.y0 : roi.y1, roi.x0 : roi.x1]
                display = (crop // 257).astype(np.uint8) if row.bit_depth == 16 else crop
                canvas.paste(Image.fromarray(display).convert("RGB"), (x0, y0))
                record.update(
                    roi={"x0": roi.x0, "y0": roi.y0, "x1": roi.x1, "y1": roi.y1},
                    source_photometric=original.photometric,
                    gray_conversion=original.conversion,
                    source_warnings=original.warnings,
                    display_pixel_sha256=sha256(display.tobytes()).hexdigest(),
                )
            else:
                draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill="#eeeeee")
                draw.line((x0, y0, x1 - 1, y1 - 1), fill="#666666")
                draw.line((x1 - 1, y0, x0, y1 - 1), fill="#666666")
            records.append(record)
    manifest = {
        "schema_version": 2,
        "operation": "figure_segmented_geometry@1",
        "project_id": project.project_id,
        "revision": project.revision,
        "purpose": "display_only_not_quantitative",
        "display_mapping": template.display_mapping,
        "source_coordinate_system": "original_top_left_xy_half_open",
        "font_sha256": font_hash,
        "size": [layout.width, layout.height],
        "rows": records,
        "project": project.model_dump(mode="json"),
    }
    return FigureRender(
        layout.width, layout.height, canvas.tobytes(), json.dumps(manifest, ensure_ascii=True)
    )
