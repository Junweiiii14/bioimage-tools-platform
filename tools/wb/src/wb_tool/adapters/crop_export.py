"""Export a new TIFF with unchanged source samples and embedded coordinate provenance."""

import json
import os
from collections.abc import Callable
from dataclasses import asdict
from fractions import Fraction
from hashlib import file_digest, sha256
from pathlib import Path
from uuid import uuid4

import numpy as np
import tifffile

from wb_tool.adapters.tiff_input import load_tiff, read_admitted_tiff_page
from wb_tool.application.crop import CropRequest


def export_crop(
    source: str,
    request: CropRequest,
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    def check_cancel() -> None:
        if cancelled():
            raise ValueError("原值裁剪已取消，未发布当前文件")

    check_cancel()
    target = Path(destination).absolute()
    if target.suffix.lower() not in (".tif", ".tiff"):
        raise ValueError("请选择新的 TIFF 文件")
    for parent in (target.parent, *target.parent.parents):
        if parent.is_symlink() or parent.is_junction():
            raise ValueError("导出目录不能经过符号链接或 junction")
    if target.exists() or target.is_symlink():
        raise FileExistsError("裁剪目标已存在，请选择新文件")
    # Reuse quantitative input validation, but never export its RGB-to-gray array.
    validated = load_tiff(source)
    if validated.sha256 != request.source_sha256:
        raise ValueError("裁剪来源与当前原图不一致")
    height, width = validated.pixels.shape
    roi = request.roi
    if roi.x1 > width or roi.y1 > height:
        raise ValueError("裁剪矩形超出原图")
    del validated
    with Path(source).open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != request.source_sha256:
            raise ValueError("裁剪读取前原图已改变")
        stream.seek(0)
        with tifffile.TiffFile(stream) as image:
            page = image.pages[0]
            if len(image.pages) != 1 or not isinstance(page, tifffile.TiffPage):
                raise ValueError("无法读取原始 TIFF 页")
            original = read_admitted_tiff_page(page)
            if page.planarconfig == 2:
                original = np.moveaxis(original, 0, -1)
            photometric = tifffile.PHOTOMETRIC(page.photometric)
            extras = tuple(page.extrasamples)
            xres, yres = page.tags.get("XResolution"), page.tags.get("YResolution")
            resolution = (xres.value, yres.value) if xres is not None and yres is not None else None
            unit = page.resolutionunit
        stream.seek(0)
        if file_digest(stream, "sha256").hexdigest() != request.source_sha256:
            raise ValueError("裁剪读取期间原图已改变")
    check_cancel()
    cropped = np.ascontiguousarray(original[roi.y0 : roi.y1, roi.x0 : roi.x1])
    manifest = {
        "schema_version": 1,
        "operation": "original_sample_crop@1",
        "source_sha256": request.source_sha256,
        "source_revision": request.revision,
        "source_shape_yxc": list(original.shape),
        "roi": asdict(roi),
        "coordinate_system": "original_top_left_xy_half_open",
        "shape": list(cropped.shape),
        "dtype": cropped.dtype.str,
        "pixel_sha256": sha256(cropped.tobytes()).hexdigest(),
        "photometric": photometric.name,
        "transforms": [],
    }
    stage = target.parent / (".wb-crop-" + uuid4().hex + ".tmp")
    try:
        with stage.open("xb") as file:
            tifffile.imwrite(
                file,
                cropped,
                photometric=photometric,
                extrasamples=extras or None,
                resolution=resolution,
                resolutionunit=unit,
                metadata=None,
                description=json.dumps(manifest, ensure_ascii=True),
                software="bioimage-wb original_sample_crop@1",
            )
            file.flush()
            os.fsync(file.fileno())
        check_cancel()
        with tifffile.TiffFile(stage) as image:
            page = image.pages[0]
            if (
                len(image.pages) != 1
                or not isinstance(page, tifffile.TiffPage)
                or page.dtype != cropped.dtype
                or page.shape != cropped.shape
                or page.photometric != photometric
                or page.resolutionunit != unit
                or tuple(page.extrasamples) != extras
                or page.software != "bioimage-wb original_sample_crop@1"
                or json.loads(page.description) != manifest
                or not np.array_equal(read_admitted_tiff_page(page), cropped)
            ):
                raise ValueError("原值裁剪写后核验失败，未发布当前文件")
            if resolution is not None:
                for name, expected in zip(("XResolution", "YResolution"), resolution, strict=True):
                    tag = page.tags.get(name)
                    if (
                        tag is None
                        or not tag.value[1]
                        or not expected[1]
                        or Fraction(*tag.value) != Fraction(*expected)
                    ):
                        raise ValueError("原值裁剪分辨率写后核验失败，未发布当前文件")
        check_cancel()
        if os.name == "nt":
            os.rename(stage, target)
        else:
            os.link(stage, target)
    finally:
        if stage.exists():
            stage.unlink()
    return str(target)
