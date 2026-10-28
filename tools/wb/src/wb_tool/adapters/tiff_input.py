"""Read quantitative TIFF pixels without changing the source or its bit depth."""

import json
import os
from dataclasses import dataclass
from hashlib import file_digest
from pathlib import Path
from typing import cast

import numpy as np
import tifffile
from numpy.typing import NDArray

DISPLAY_TIFF_SOFTWARE = "bioimage-wb figure_display@1"
TIFF_DECODE_BUFFER_BYTES = 16 * 1024 * 1024


def _display_only(page: tifffile.TiffPage) -> bool:
    if page.software == DISPLAY_TIFF_SOFTWARE:
        return True
    description = page.description
    operations = (
        "figure_original_geometry@1",
        "figure_segmented_geometry@1",
        "figure_segmented_geometry@2",
        "figure_segmented_geometry@3",
    )
    if len(description) > 16 * 1024 * 1024 or not any(op in description for op in operations):
        return False
    try:
        value: object = json.loads(description)
    except (ValueError, RecursionError):
        return False
    if not isinstance(value, dict):
        return False
    record = cast(dict[str, object], value)
    return (
        record.get("operation") in operations
        and record.get("purpose") == "display_only_not_quantitative"
    )


class ImageInputError(ValueError):
    """Unsupported or unreadable quantitative source."""


def _resource_limit(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    if not value.isascii() or not value.isdecimal() or len(value) > 19:
        raise ImageInputError(f"{name} 须为正整数；未解码输入")
    limit = int(value)
    if not 0 < limit <= 2**63 - 1:
        raise ImageInputError(f"{name} 须为正整数且不超过64位范围；未解码输入")
    return limit


def read_admitted_tiff_page(page: tifffile.TiffPage) -> NDArray[np.generic]:
    """Apply tiff_resource_admission@1 before decoding, including crop re-reads.

    Limits are per read, not an OS memory cap. The conservative estimate includes
    raw pixels, conversion temporaries, immutable copies, OCR conversion and a
    single decoded strip/tile with scratch space plus compressed read buffering.
    See docs/contracts/wb-tiff-resource-admission-v1.md for the policy/limits.
    """
    max_pixels = _resource_limit("BIOIMAGE_TIFF_MAX_PIXELS", 32_000_000)
    max_peak = _resource_limit("BIOIMAGE_TIFF_MAX_PEAK_BYTES", 2 * 1024**3)
    width, height = page.imagewidth, page.imagelength
    pixels = width * height
    if width <= 0 or height <= 0 or page.imagedepth != 1:
        raise ImageInputError("定量图像须为非空二维平面")
    if pixels > max_pixels:
        raise ImageInputError(f"TIFF 超出像素预算（{pixels} > {max_pixels}）；未解码输入")
    dtype = page.dtype
    if dtype is None or dtype.kind != "u" or dtype.itemsize not in (1, 2):
        raise ImageInputError("仅支持 uint8 和 uint16 TIFF")
    sample_bytes = dtype.itemsize
    channels = page.samplesperpixel
    rgb = page.photometric == tifffile.PHOTOMETRIC.RGB
    if page.photometric not in (
        tifffile.PHOTOMETRIC.MINISBLACK,
        tifffile.PHOTOMETRIC.MINISWHITE,
        tifffile.PHOTOMETRIC.RGB,
    ):
        raise ImageInputError("不支持该 TIFF 色度定义")
    if page.planarconfig not in (1, 2):
        raise ImageInputError("不支持该 TIFF 通道排列")
    if rgb:
        shape = (channels, height, width) if page.planarconfig == 2 else (height, width, channels)
        if channels not in (3, 4) or page.shape != shape:
            raise ImageInputError("RGB 输入须为三个颜色通道或不透明 RGBA")
    elif channels != 1 or page.shape != (height, width):
        raise ImageInputError("定量图像须为非空二维平面")
    orientation = page.tags.get("Orientation")
    if orientation is not None and orientation.value != 1:
        raise ImageInputError("当前仅支持左上原点 TIFF，请先确认方向")
    raw_bytes = pixels * channels * sample_bytes
    if page.nbytes != raw_bytes:
        raise ImageInputError("TIFF 解码尺寸与元数据不一致")
    # A padded tile can be much larger than the visible image. Include it even
    # for a tiny page; bounding visible pixels alone does not bound decoding.
    segment_width = page.tilewidth if page.is_tiled else width
    segment_height = page.tilelength if page.is_tiled else min(height, page.rowsperstrip)
    if segment_width <= 0 or segment_height <= 0 or page.tiledepth != 1:
        raise ImageInputError("不支持该 TIFF 解码块尺寸")
    segment_channels = 1 if page.planarconfig == 2 else channels
    segment_bytes = segment_width * segment_height * segment_channels * sample_bytes
    # tifffile reads until a group exceeds buffersize, then slices that group.
    # Include one overshoot segment and old/new group overlap, not just the
    # nominal buffer size. Tiny files need no fictional full-sized buffer.
    encoded_group = min(
        sum(page.databytecounts),
        TIFF_DECODE_BUFFER_BYTES + max(page.databytecounts, default=0),
    )
    encoded_buffer = 3 * encoded_group
    peak_bytes = (
        raw_bytes
        + pixels * (2 * sample_bytes + 7 + (24 if rgb else 0))
        + 3 * segment_bytes
        + encoded_buffer
    )
    if peak_bytes > max_peak:
        raise ImageInputError(f"TIFF 超出估算峰值内存预算（{peak_bytes} > {max_peak}）；未解码输入")
    return cast(
        NDArray[np.generic], page.asarray(maxworkers=1, buffersize=TIFF_DECODE_BUFFER_BYTES)
    )


def is_generated_tiff(path: str | Path) -> bool:
    """Inspect provenance tags only, without decoding image pixels.

    Broken/unrecognized files stay in discovery so the importer reports their
    actual error instead of silently hiding a damaged original.
    """
    try:
        with tifffile.TiffFile(path) as image:
            page = image.pages[0]
            return isinstance(page, tifffile.TiffPage) and (
                _display_only(page) or page.software == "bioimage-wb original_sample_crop@1"
            )
    except (OSError, ValueError, IndexError):
        return False


@dataclass(frozen=True, slots=True)
class LoadedTiff:
    source: Path
    sha256: str
    pixels: NDArray[np.uint8 | np.uint16]
    source_shape: tuple[int, ...]
    photometric: str
    conversion: str | None
    warnings: tuple[str, ...]

    @property
    def bit_depth(self) -> int:
        return self.pixels.dtype.itemsize * 8


def load_tiff(path: str | Path) -> LoadedTiff:
    """Accept one top-left page: 8/16-bit grayscale or explicit RGB/opaque RGBA.

    MINISWHITE intensities remain numerically unchanged. The caller must select
    polarity using metadata; no silent inversion or default polarity is applied.
    """
    return _read_tiff(path, allow_display=False)


def load_ocr_tiff(path: str | Path) -> LoadedTiff:
    """OCR may read known display composites without offering quantitative admission."""
    return _read_tiff(path, allow_display=True)


def _read_tiff(path: str | Path, *, allow_display: bool) -> LoadedTiff:
    source = Path(path).resolve()
    if source.suffix.lower() not in (".tif", ".tiff"):
        raise ImageInputError("仅支持 TIFF 定量输入")
    try:
        with source.open("rb") as stream:
            digest = file_digest(stream, "sha256").hexdigest()
            stream.seek(0)
            with tifffile.TiffFile(stream) as image:
                if len(image.pages) != 1:
                    raise ImageInputError("定量输入须为单页 TIFF")
                page = image.pages[0]
                if not isinstance(page, tifffile.TiffPage):
                    raise ImageInputError("无法确认 TIFF 页的完整元数据")
                display_only = _display_only(page)
                if display_only and not allow_display:
                    raise ImageInputError("这是显示拼图；可用于拼图OCR，定量请使用未改强度的原图")
                photometric = tifffile.PHOTOMETRIC(page.photometric).name
                raw = read_admitted_tiff_page(page)
                planar = page.planarconfig
            stream.seek(0)
            if file_digest(stream, "sha256").hexdigest() != digest:
                raise ImageInputError("读取期间输入文件改变，请重新导入")
    except ImageInputError:
        raise
    except (OSError, ValueError) as exc:
        raise ImageInputError("无法读取 TIFF 输入：文件损坏或所需解码器不可用") from exc
    if raw.dtype.kind != "u" or raw.dtype.itemsize not in (1, 2):
        raise ImageInputError("仅支持 uint8 和 uint16 TIFF")
    original_shape = tuple(int(value) for value in raw.shape)
    warnings: list[str] = []
    if display_only:
        warnings.append("本软件生成的显示拼图，仅用于OCR/排版；定量须回到原图")
    conversion: str | None = None
    if photometric == "RGB":
        if planar == 2:
            raw = np.moveaxis(raw, 0, -1)
        if raw.ndim != 3 or raw.shape[-1] not in (3, 4):
            raise ImageInputError("RGB 输入须为三个颜色通道或不透明 RGBA")
        maximum = (1 << (raw.dtype.itemsize * 8)) - 1
        if raw.shape[-1] == 4 and np.any(raw[..., 3] != maximum):
            raise ImageInputError("含透明像素的 TIFF 不能直接定量")
        work = raw[..., :3].astype(np.uint32)
        grayscale = (work[..., 0] * 299 + work[..., 1] * 587 + work[..., 2] * 114 + 500) // 1000
        raw = grayscale.astype(raw.dtype)
        conversion = "rgb-bt601-integer@1"
        warnings.append("RGB 已按整数 BT.601 转换为灰度，原始文件未修改")
    if raw.ndim != 2 or raw.size == 0:
        raise ImageInputError("定量图像须为非空二维平面")
    # bytes backing prevents callers from re-enabling writes to this array.
    pixels = cast(
        NDArray[np.uint8 | np.uint16],
        np.frombuffer(raw.tobytes(), dtype=raw.dtype).reshape(raw.shape),
    )
    if np.any(pixels == 0) or np.any(pixels == (1 << (pixels.dtype.itemsize * 8)) - 1):
        warnings.append("存在位深上下限像素，请检查曝光及饱和；不能据此自动认定信号有效")
    if photometric == "MINISWHITE":
        warnings.append("MINISWHITE：零值表示白色；已保留原始强度，须核对条带极性")
    return LoadedTiff(
        source, digest, pixels, original_shape, photometric, conversion, tuple(warnings)
    )
