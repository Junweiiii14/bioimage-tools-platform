"""Select an installed font in a background caller; persist it through normal asset import."""

import os
from collections.abc import Callable, Sequence
from io import BytesIO
from pathlib import Path
from typing import cast

from PIL import ImageFont


def _glyph(
    font: ImageFont.FreeTypeFont, character: str
) -> tuple[tuple[float, float, float, float], bytes]:
    # Pillow's ImagingCore stub omits its runtime byte-sequence protocol.
    mask = cast(Sequence[int], font.getmask(character, mode="L"))
    return font.getbbox(character), bytes(mask)


def find_label_font(labels: tuple[str, ...], *, cancelled: Callable[[], bool]) -> str:
    characters = {char for label in labels for char in label if not char.isspace()}
    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    candidates = (
        windows / "arial.ttf",
        windows / "msyh.ttc",
        windows / "simsun.ttc",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    )
    for path in candidates:
        if cancelled():
            raise ValueError("字体选择已取消")
        try:
            if not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
                continue
            font = ImageFont.truetype(BytesIO(path.read_bytes()), 18)
            missing = _glyph(font, "\U0010ffff")
            supported = True
            for char in characters:
                if cancelled():
                    supported = False
                    break
                if _glyph(font, char) == missing:
                    supported = False
                    break
            if supported:
                return str(path)
        except (OSError, ValueError):
            continue
    if cancelled():
        raise ValueError("字体选择已取消")
    raise ValueError("未找到支持标签文字的系统字体；请在项目工具中导入TTF/OTF/TTC字体")
