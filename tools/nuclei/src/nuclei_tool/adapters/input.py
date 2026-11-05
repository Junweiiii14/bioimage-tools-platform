"""Bounded original TIFF loading; never converts modes or image depth."""

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image, TiffImagePlugin

from nuclei_tool.domain.labels import validate_pixels
from nuclei_tool.domain.method import MAX_INPUT_BYTES, MAX_PIXELS


@dataclass(frozen=True)
class NucleiInput:
    pixels: NDArray[np.uint8]
    sha256: str
    size_bytes: int


def read_nuclei_input(path: str) -> NucleiInput:
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("invalid_input_path: expected a regular TIFF file")
    with source.open("rb") as stream:
        data = stream.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("input_budget: TIFF exceeds 16 MiB")
    with Image.open(io.BytesIO(data)) as image:
        if not isinstance(image, TiffImagePlugin.TiffImageFile):
            raise ValueError("unsupported_input: expected TIFF")
        if image.mode != "L" or image.n_frames != 1:
            raise ValueError("unsupported_input: expected one uint8 grayscale TIFF page")
        if (
            image.tag_v2.get(258) != (8,)
            or image.tag_v2.get(339, (1,)) != (1,)
            or image.tag_v2.get(277, 1) != 1
            or image.tag_v2.get(274, 1) != 1
            or image.tag_v2.get(262) != 1
        ):
            raise ValueError("unsupported_input: require uint8 black-is-zero, top-left TIFF")
        if not 1 <= image.width * image.height <= MAX_PIXELS:
            raise ValueError("input_budget: TIFF dimensions exceed admission budget")
        pixels = np.array(image, copy=True)
    validate_pixels(pixels)
    pixels.flags.writeable = False
    return NucleiInput(pixels, hashlib.sha256(data).hexdigest(), len(data))
