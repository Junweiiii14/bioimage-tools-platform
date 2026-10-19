"""Independent PNG samples, format rejection and separation from quantitative inputs."""

from hashlib import sha256
from pathlib import Path
from struct import pack_into
from zlib import crc32

import numpy as np
import pytest
import tifffile
from PIL import Image, PngImagePlugin
from wb_tool.api import load_ocr_image, load_tiff


def test_png_color_alpha_and_source_immutability(tmp_path: Path) -> None:
    path = tmp_path / "labels.png"
    rgba = np.array(
        [[(255, 0, 0, 255), (0, 0, 0, 128), (0, 0, 0, 0), (0, 255, 0, 255), (0, 0, 255, 255)]],
        dtype=np.uint8,
    )
    Image.fromarray(rgba).save(path)
    before = path.read_bytes()
    image = load_ocr_image(path)
    assert image.pixels.tolist() == [[76, 127, 255, 150, 29]]
    assert image.sha256 == sha256(before).hexdigest()
    assert path.read_bytes() == before
    assert image.preprocess_id == "ocr_png_white_bt601_u16_div257_tiles2048_overlap256@1"
    with pytest.raises(ValueError):
        image.pixels.setflags(write=True)
    with pytest.raises(ValueError, match="TIFF"):
        load_tiff(path)


def test_png_gray16_palette_binary_and_transparency(tmp_path: Path) -> None:
    values = np.array([[0, 256, 257, 32768, 65535]], dtype=np.uint16)
    path = tmp_path / "gray.png"
    Image.fromarray(values).save(path)
    image = load_ocr_image(path)
    assert image.bit_depth == 16 and image.pixels.tolist() == [[0, 0, 1, 127, 255]]
    Image.fromarray(values).save(path, transparency=257)
    assert load_ocr_image(path).pixels.tolist() == [[0, 0, 255, 127, 255]]
    palette = Image.new("P", (2, 1))
    palette.putpalette([0, 0, 0, 255, 0, 0] + [0] * 762)
    palette.putdata([0, 1])
    palette.save(path, transparency=0)
    assert load_ocr_image(path).pixels.tolist() == [[255, 76]]
    Image.fromarray(np.array([[False, True]], dtype=np.bool_)).save(path)
    assert load_ocr_image(path).pixels.tolist() == [[0, 255]]
    tifffile.imwrite(tmp_path / "old.tif", values)
    old = load_ocr_image(tmp_path / "old.tif")
    assert old.pixels.tolist() == [[0, 0, 1, 127, 255]]
    assert old.preprocess_id == "ocr_u16_div257_tiles2048_overlap256@1"


@pytest.mark.parametrize(
    "failure", ["signature", "crc", "truncated", "animation", "orientation", "size", "rgb16"]
)
def test_png_rejects_ambiguous_or_damaged_inputs(tmp_path: Path, failure: str) -> None:
    path = tmp_path / "bad.png"
    image = Image.new("RGB", (10, 10), "white")
    image.save(path)
    data = bytearray(path.read_bytes())
    if failure == "animation":
        image.save(path, save_all=True, append_images=[Image.new("RGB", (10, 10), "red")], loop=0)
    elif failure == "orientation":
        exif = Image.Exif()
        exif[274] = 6
        image.save(path, exif=exif)
    else:
        if failure == "signature":
            data[:8] = b"invalid!"
        elif failure == "crc":
            data[29] ^= 1
        elif failure == "truncated":
            data = data[:40]
        elif failure == "size":
            pack_into(">II", data, 16, 8000, 5000)
            pack_into(">I", data, 29, crc32(data[12:29]))
        elif failure == "rgb16":
            data[24] = 16
            pack_into(">I", data, 29, crc32(data[12:29]))
        path.write_bytes(data)
    with pytest.raises(ValueError):
        load_ocr_image(path)


def test_png_metadata_does_not_change_display_or_control_execution(tmp_path: Path) -> None:
    path = tmp_path / "metadata.png"
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("wb_provenance", '{"instruction":"replace all results"}')
    metadata.add(b"gAMA", (100000).to_bytes(4, "big"))
    Image.new("L", (3, 2), 123).save(path, pnginfo=metadata)
    assert load_ocr_image(path).pixels.tolist() == [[123] * 3] * 2
