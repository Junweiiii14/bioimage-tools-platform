"""Background-only figure rendering and atomic, traceable export bundles."""

import json
import os
from collections.abc import Callable
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

from wb_tool.adapters.archive_io import ArchiveWriter
from wb_tool.adapters.crop_export import export_crop
from wb_tool.adapters.project_archive import archive_index_bytes, write_project_results
from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.crop import CropRequest
from wb_tool.application.figure_project import (
    FigurePNG,
    FigureRender,
    FigureSourcePath,
    WBFigureProject,
    plan_figure_layout,
)
from wb_tool.application.project_archive import ArchiveRunEvidence
from wb_tool.application.project_restore import WBRestoredProject, project_assets


def _paths(sources: tuple[FigureSourcePath, ...]) -> dict[str, str]:
    paths = {source.sha256: source.path for source in sources}
    if len(paths) != len(sources):
        raise ValueError("来源路径重复")
    return paths


def render_figure(
    project: WBFigureProject,
    sources: tuple[FigureSourcePath, ...],
    *,
    require_review: bool = True,
    cancelled: Callable[[], bool] = lambda: False,
) -> FigureRender:
    layout = plan_figure_layout(project, require_review=require_review)
    paths = _paths(sources)
    template = project.template
    required = {row.source.sha256 for row in project.rows if row.source is not None}
    if template.font is not None:
        required.add(template.font.sha256)
    if not required.issubset(paths):
        raise ValueError("缺少项目原图或字体来源路径")
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    font_hash = "pillow-12.3.0-bundled-aileron"
    if template.font is None:
        # Bundled font is portable. Non-Latin labels require an explicitly imported font.
        if any(
            any(ord(c) > 255 for c in text)
            for text in (*project.figure_order, *(r.protein for r in project.rows))
        ):
            raise ValueError("这些标签需要导入支持相应文字的 TTF/OTF/TTC 字体")
        font = ImageFont.load_default(size=template.font_size)
    else:
        font_path = Path(paths[template.font.sha256])
        if font_path.stat().st_size > 32 * 1024 * 1024:
            raise ValueError("字体文件超出 32 MiB 预算")
        data = font_path.read_bytes()
        font_hash = sha256(data).hexdigest()
        if font_hash != template.font.sha256 or len(data) != template.font.size_bytes:
            raise ValueError("模板字体摘要或字节数不一致")
        font = ImageFont.truetype(BytesIO(data), template.font_size)
    canvas = Image.new("RGB", (layout.width, layout.height), "white")
    draw = ImageDraw.Draw(canvas)
    provenance: list[dict[str, object]] = []
    for panel in layout.placements:
        if draw.textlength(panel.figure, font=font) > template.label_width + panel.width:
            raise ValueError("Fig 标题过长，请增大版式宽度或减小字号")
        draw.text((panel.x, panel.y), panel.figure, fill="black", font=font, anchor="lt")
        y = panel.y + template.font_size + template.row_gap
        for row in panel.rows:
            if cancelled():
                raise ValueError("拼图任务已取消，未发布输出")
            x = panel.x + (template.label_width if template.label_side == "left" else 0)
            label_x = (
                panel.x
                if template.label_side == "left"
                else x + panel.width + 2 * template.border + 8
            )
            bounds = font.getbbox(row.protein)
            if (
                draw.textlength(row.protein, font=font) > template.label_width - 12
                or bounds[3] - bounds[1] > template.crop_height
            ):
                raise ValueError(f"{row.protein} 标签超出留白，请增大标签区/行高或减小字号")
            draw.text(
                (label_x, y + template.crop_height / 2),
                row.protein,
                fill="black",
                font=font,
                anchor="lm",
            )
            # Border lies outside the crop; source pixels are never painted over.
            draw.rectangle(
                (
                    x,
                    y,
                    x + panel.width + 2 * template.border - 1,
                    y + template.crop_height + 2 * template.border - 1,
                ),
                outline="black",
                width=template.border,
            )
            x0, y0 = x + template.border, y + template.border
            record: dict[str, object] = {
                "row_id": row.row_id,
                "figure": row.figure,
                "protein": row.protein,
                "source_sha256": row.source.sha256 if row.source else None,
                "crop_file": f"crops/{project.rows.index(row) + 1:04d}.tif" if row.source else None,
                "roi": None,
                "output_box": [x0, y0, x0 + panel.width, y0 + template.crop_height],
                "lane_count": row.lane_count,
                "empty_lanes": row.empty_lanes,
                "reviewed": row.reviewed,
                "status": "missing" if row.source is None else "present",
            }
            if row.source is not None and row.roi is not None:
                original = load_tiff(paths[row.source.sha256])
                if (
                    original.sha256 != row.source.sha256
                    or original.source.stat().st_size != row.source.size_bytes
                    or original.pixels.shape != (row.height, row.width)
                    or original.bit_depth != row.bit_depth
                ):
                    raise ValueError("拼图原图摘要/尺寸/位深不一致")
                roi = row.roi
                record["source_photometric"] = original.photometric
                record["gray_conversion"] = original.conversion
                record["source_warnings"] = original.warnings
                cropped = original.pixels[roi.y0 : roi.y1, roi.x0 : roi.x1]
                display = (cropped // 257).astype(np.uint8) if row.bit_depth == 16 else cropped
                canvas.paste(Image.fromarray(display).convert("RGB"), (x0, y0))
                record["roi"] = {"x0": roi.x0, "y0": roi.y0, "x1": roi.x1, "y1": roi.y1}
                record["display_pixel_sha256"] = sha256(display.tobytes()).hexdigest()
            else:
                draw.rectangle(
                    (x0, y0, x0 + panel.width - 1, y0 + template.crop_height - 1), fill="#eeeeee"
                )
                draw.line(
                    (x0, y0, x0 + panel.width - 1, y0 + template.crop_height - 1), fill="#666666"
                )
                draw.line(
                    (x0 + panel.width - 1, y0, x0, y0 + template.crop_height - 1), fill="#666666"
                )
            provenance.append(record)
            y += template.crop_height + template.row_gap + 2 * template.border
    manifest = {
        "schema_version": 1,
        "operation": "figure_original_geometry@1",
        "project_id": project.project_id,
        "revision": project.revision,
        "purpose": "display_only_not_quantitative",
        "display_mapping": template.display_mapping,
        "source_coordinate_system": "original_top_left_xy_half_open",
        "font_sha256": font_hash,
        "size": [layout.width, layout.height],
        "rows": provenance,
        "project": project.model_dump(mode="json"),
    }
    return FigureRender(
        layout.width, layout.height, canvas.tobytes(), json.dumps(manifest, ensure_ascii=True)
    )


def encode_figure_png(rendered: FigureRender, dpi: int) -> FigurePNG:
    png = BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text("wb_provenance", rendered.manifest_json)
    Image.frombytes("RGB", (rendered.width, rendered.height), rendered.rgb).save(
        png, format="PNG", pnginfo=info, dpi=(dpi, dpi)
    )
    data = png.getvalue()
    if len(data) > 64 * 1024 * 1024:
        raise ValueError("生成PNG超出64MiB资产预算，请拆分Fig")
    return FigurePNG(rendered.width, rendered.height, sha256(data).hexdigest(), data)


def export_figure_bundle(
    project: WBFigureProject,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
    runs: tuple[ArchiveRunEvidence, ...] = (),
) -> str:
    target = Path(destination).absolute()
    if target.suffix.lower() != ".zip":
        raise ValueError("请选择新的 ZIP 拼图归档")
    if target.exists() or target.is_symlink():
        raise FileExistsError("目标已存在，请选择新文件")
    if any(p.is_symlink() or p.is_junction() for p in (target.parent, *target.parent.parents)):
        raise ValueError("导出目录不能经过符号链接或 junction")
    rendered = render_figure(project, sources, cancelled=cancelled)
    paths = _paths(sources)
    stage = target.parent / (".wb-figure-" + uuid4().hex + ".tmp")
    try:
        with TemporaryDirectory(prefix="wb-figure-") as temporary, stage.open("xb") as output:
            with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
                writer = ArchiveWriter(archive, cancelled)
                png = encode_figure_png(rendered, project.template.dpi)
                writer.data("figure.png", png.data, "display_figure")
                writer.data("manifest.json", rendered.manifest_json.encode(), "figure_provenance")
                writer.data("project.json", project.model_dump_json().encode(), "saved_project")
                for index, row in enumerate(project.rows):
                    if cancelled():
                        raise ValueError("拼图导出已取消，未发布输出")
                    if row.source is None or row.roi is None:
                        continue
                    crop = Path(temporary) / f"{index + 1:04d}.tif"
                    export_crop(
                        paths[row.source.sha256],
                        CropRequest(row.source.sha256, project.revision, row.roi),
                        str(crop),
                    )
                    writer.file(f"crops/{index + 1:04d}.tif", crop, "original_sample_crop")
                # The bundle is independently traceable, including originals and custom font.
                refs = project_assets(project)
                historical: set[str] = (
                    {source.archive.sha256 for source in project.archive_sources}
                    if isinstance(project, WBRestoredProject)
                    else set()
                )
                assets = {ref.sha256: ref.size_bytes for ref in refs}
                if any(assets[ref.sha256] != ref.size_bytes for ref in refs):
                    raise ValueError("同一来源SHA对应不一致的字节数")
                for digest in sorted(assets):
                    if cancelled():
                        raise ValueError("拼图导出已取消，未发布输出")
                    if digest not in paths:
                        raise ValueError("缺少项目原图/OCR/字体资产路径")
                    writer.file(
                        f"assets/{digest}",
                        paths[digest],
                        "historical_archive" if digest in historical else "source_asset",
                        digest,
                        assets[digest],
                    )
                index = write_project_results(project, runs, writer)
                writer.check_cancel()
                writer.data("archive.json", archive_index_bytes(index), "archive_index")
            output.flush()
            os.fsync(output.fileno())
        if cancelled():
            raise ValueError("拼图导出已取消，未发布输出")
        if os.name == "nt":
            os.rename(stage, target)
        else:
            os.link(stage, target)
    finally:
        if stage.exists():
            stage.unlink()
    return str(target)
