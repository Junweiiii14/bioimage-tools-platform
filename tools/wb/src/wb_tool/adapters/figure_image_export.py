"""Single display image publication with provenance, reread verification and no replacement."""

import os
from collections.abc import Callable
from pathlib import Path
from typing import cast
from uuid import uuid4

import numpy as np
import tifffile
from PIL import Image

from wb_tool.adapters.figure_export import encode_figure_png, render_figure
from wb_tool.adapters.tiff_input import DISPLAY_TIFF_SOFTWARE
from wb_tool.application.figure_project import FigureRender, FigureSourcePath, WBFigureProject


def _cancel(cancelled: Callable[[], bool]) -> None:
    if cancelled():
        raise ValueError("成图导出已取消，未发布输出")


def _verify(path: Path, rendered: FigureRender, dpi: int, *, png: bool) -> None:
    if path.stat().st_size > (64 if png else 128) * 1024 * 1024:
        raise ValueError("成图超过PNG64MiB/TIFF128MiB文件预算")
    if png:
        with Image.open(path, formats=("PNG",)) as image:
            if image.size != (rendered.width, rendered.height) or image.mode != "RGB":
                raise ValueError("PNG尺寸或颜色模式不一致")
            if image.info.get("wb_provenance") != rendered.manifest_json:
                raise ValueError("PNG来源记录不一致")
            resolution = cast(tuple[float, float], image.info.get("dpi", (0, 0)))
            # PNG stores integer pixels/metre: half a step is 0.0127 pixels/inch.
            if len(resolution) != 2 or any(abs(value - dpi) > 0.013 for value in resolution):
                raise ValueError("PNG分辨率标记不一致")
            image.verify()
        with Image.open(path, formats=("PNG",)) as image:
            if image.tobytes() != rendered.rgb:
                raise ValueError("PNG显示像素不一致")
        return
    with tifffile.TiffFile(path) as image:
        if len(image.pages) != 1:
            raise ValueError("TIFF成图须为单页")
        page = image.pages[0]
        if not isinstance(page, tifffile.TiffPage):
            raise ValueError("TIFF成图元数据不完整")
        if (
            page.shape != (rendered.height, rendered.width, 3)
            or page.dtype != np.dtype("uint8")
            or page.photometric != tifffile.PHOTOMETRIC.RGB
            or page.planarconfig != 1
            or page.compression != 1
            or page.description != rendered.manifest_json
            or page.software != DISPLAY_TIFF_SOFTWARE
            or page.resolutionunit != tifffile.RESUNIT.INCH
        ):
            raise ValueError("TIFF成图像素模式或来源标记不一致")
        for name in ("XResolution", "YResolution"):
            tag = page.tags.get(name)
            if tag is None or tag.value != (dpi, 1):
                raise ValueError("TIFF分辨率标记不一致")
        if page.asarray().tobytes() != rendered.rgb:
            raise ValueError("TIFF显示像素不一致")


def export_figure_image(
    project: WBFigureProject,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    target = Path(destination).absolute()
    if target.suffix.lower() not in (".png", ".tif", ".tiff"):
        raise ValueError("请选择新的TIFF或PNG成图文件")
    if target.exists() or target.is_symlink() or target.is_junction():
        raise FileExistsError("成图目标已存在，请选择新文件")
    if any(p.is_symlink() or p.is_junction() for p in (target.parent, *target.parent.parents)):
        raise ValueError("成图目录不能经过符号链接或junction")
    _cancel(cancelled)
    rendered = render_figure(project, sources, cancelled=cancelled)
    return publish_rendered_image(rendered, project.template.dpi, destination, cancelled=cancelled)


def publish_rendered_image(
    rendered: FigureRender,
    dpi: int,
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    """Publish a verified display render; used by montage and reviewed crop export."""
    target = Path(destination).absolute()
    if target.suffix.lower() not in (".png", ".tif", ".tiff"):
        raise ValueError("请选择新的TIFF或PNG成图文件")
    if target.exists() or target.is_symlink() or target.is_junction():
        raise FileExistsError("成图目标已存在，请选择新文件")
    if any(p.is_symlink() or p.is_junction() for p in (target.parent, *target.parent.parents)):
        raise ValueError("成图目录不能经过符号链接或junction")
    if len(rendered.manifest_json.encode("utf-8")) > 16 * 1024 * 1024:
        raise ValueError("成图来源记录超过16MiB，请拆分项目")
    _cancel(cancelled)
    png = target.suffix.lower() == ".png"
    stage = target.parent / (".wb-image-" + uuid4().hex + ".tmp")
    try:
        with stage.open("xb") as stream:
            if png:
                encoded = encode_figure_png(rendered, dpi)
                for start in range(0, len(encoded.data), 1024 * 1024):
                    _cancel(cancelled)
                    stream.write(encoded.data[start : start + 1024 * 1024])
            else:
                pixels = np.frombuffer(rendered.rgb, dtype=np.uint8).reshape(
                    rendered.height, rendered.width, 3
                )
                tifffile.imwrite(
                    stream,
                    pixels,
                    photometric="rgb",
                    planarconfig="contig",
                    compression=None,
                    metadata=None,
                    description=rendered.manifest_json,
                    resolution=(dpi, dpi),
                    resolutionunit="INCH",
                    software=DISPLAY_TIFF_SOFTWARE,
                )
            stream.flush()
            os.fsync(stream.fileno())
        _cancel(cancelled)
        _verify(stage, rendered, dpi, png=png)
        _cancel(cancelled)
        if os.name == "nt":
            os.rename(stage, target)
        else:
            os.link(stage, target)
    finally:
        if stage.exists():
            stage.unlink()
    return str(target)
