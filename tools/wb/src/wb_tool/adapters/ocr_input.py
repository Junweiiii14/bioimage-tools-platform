"""OCR-only display rasters; never accepted by quantitative TIFF/profile APIs."""

from dataclasses import dataclass
from hashlib import file_digest
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.domain.ocr_manifest import PNG_PREPROCESS_ID, PREPROCESS_ID


@dataclass(frozen=True)
class OCRImage:
    sha256: str
    pixels: NDArray[np.uint8]
    bit_depth: int
    preprocess_id: str
    warnings: tuple[str, ...] = ()


def load_ocr_image(path: str | Path) -> OCRImage:
    source = Path(path).resolve()
    if source.suffix.lower() in (".tif", ".tiff"):
        image = load_tiff(source)
        display = (image.pixels // 257).astype(np.uint8) if image.bit_depth == 16 else image.pixels
        pixels = np.frombuffer(display.tobytes(), dtype=np.uint8).reshape(display.shape)
        return OCRImage(image.sha256, pixels, image.bit_depth, PREPROCESS_ID, image.warnings)
    if source.suffix.lower() != ".png":
        raise ValueError("OCR仅支持TIFF或PNG拼图")
    from PIL import Image

    try:
        return _load_png(source)
    except (OSError, SyntaxError, EOFError, Image.DecompressionBombError) as error:
        raise ValueError("PNG无法读取：" + str(error)) from error


def _load_png(source: Path) -> OCRImage:
    from PIL import Image

    with source.open("rb") as stream:
        if source.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("PNG超出64MiB文件预算")
        digest = file_digest(stream, "sha256").hexdigest()
        stream.seek(0)
        header = stream.read(29)
        if len(header) != 29 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            raise ValueError("文件不是PNG图像")
        depth, color = header[24], header[25]
        if depth == 16 and color != 0:
            raise ValueError("暂不支持16位彩色PNG；请提供8位显示副本或TIFF拼图")
        stream.seek(0)
        with Image.open(stream, formats=("PNG",)) as png:
            if png.width * png.height > 32_000_000 or max(png.size) > 32768:
                raise ValueError("PNG超出3200万像素/32768边长预算，请拆分Fig")
            if getattr(png, "n_frames", 1) != 1 or "loop" in png.info:
                raise ValueError("OCR不支持动画PNG，请提供单帧拼图")
            png.verify()
        stream.seek(0)
        with Image.open(stream, formats=("PNG",)) as png:
            png.load()
            if png.getexif().get(274, 1) != 1:
                raise ValueError("PNG须为左上原点，请先确认方向")
            if depth == 16:
                raw = np.asarray(png, dtype=np.uint16)
                display = (raw // 257).astype(np.uint8)
                transparent = png.info.get("transparency")
                if isinstance(transparent, int):
                    display[raw == transparent] = 255
            else:
                rgba = png.convert("RGBA")
                opaque = Image.alpha_composite(Image.new("RGBA", png.size, "white"), rgba)
                rgb = np.asarray(opaque.convert("RGB"), dtype=np.uint32)
                display = (
                    (rgb[..., 0] * 299 + rgb[..., 1] * 587 + rgb[..., 2] * 114 + 500) // 1000
                ).astype(np.uint8)
        stream.seek(0)
        if file_digest(stream, "sha256").hexdigest() != digest:
            raise ValueError("读取期间PNG改变，请重新导入")
    pixels = np.frombuffer(display.tobytes(), dtype=np.uint8).reshape(display.shape)
    return OCRImage(
        digest, pixels, depth, PNG_PREPROCESS_ID, ("PNG仅用于OCR；透明合成白底，不应用ICC/gamma",)
    )
