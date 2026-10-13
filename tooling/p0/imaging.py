"""Technical image semantics only. No WB measurements or preprocessing defaults."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import cast

import numpy as np
import numpy.typing as npt
import tifffile

Pixels = npt.NDArray[np.uint16] | npt.NDArray[np.uint8]


def load(path: Path) -> Pixels:
    with tifffile.TiffFile(path) as image:
        raw = cast(Pixels, image.asarray())
    if not (
        (raw.ndim == 2 and raw.dtype == np.uint16)
        or (raw.ndim == 3 and raw.shape[2] == 3 and raw.dtype == np.uint8)
    ):
        raise ValueError("P0 supports 2D uint16 or YXC RGB uint8 TIFF only")
    if max(raw.shape[:2]) > 4096 or min(raw.shape[:2]) < 1:
        raise ValueError("P0 limit is 4096 x 4096, not a product limit")
    raw.flags.writeable = False
    return raw


def digest(raw: Pixels) -> str:
    return hashlib.sha256(memoryview(raw)).hexdigest()


def preview(raw: Pixels) -> npt.NDArray[np.uint8]:
    # Fixed full-range display transform; NEVER used by profile or worker.
    if raw.dtype == np.uint16:
        return np.asarray(raw // 256, dtype=np.uint8)
    return np.array(raw, dtype=np.uint8, copy=True)


def profile(raw: Pixels, box: tuple[int, int, int, int]) -> npt.NDArray[np.float64]:
    x, y, width, height = box
    if min(x, y) < 0 or min(width, height) < 1:
        raise ValueError("Invalid half-open ROI")
    if x + width > raw.shape[1] or y + height > raw.shape[0]:
        raise ValueError("ROI outside image")
    # Y rows averaged for each X column. RGB probe uses channel 0 explicitly.
    plane = raw if raw.ndim == 2 else raw[:, :, 0]
    return np.mean(plane[y : y + height, x : x + width], axis=0, dtype=np.float64)
