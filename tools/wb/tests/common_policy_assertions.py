"""Geometry assertions for the explicitly approved prominent-row policy."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from wb_tool.api import IntakeCropEvidence, automatic_intake_crop_allowed, load_tiff


def assert_prominent_row(
    evidence: IntakeCropEvidence,
    path: Path,
    pixels: NDArray[np.uint16],
    bounds: list[tuple[int, int, int, int]],
) -> None:
    assert automatic_intake_crop_allowed(evidence), evidence.reason
    assert evidence.geometry_policy == "source_common_band_geometry@1"
    assert not evidence.reviewed
    assert evidence.lane_count == len(evidence.slots) == len(bounds)
    for slot, (x0, y0, x1, y1) in zip(evidence.slots, bounds, strict=True):
        assert slot.roi is not None
        assert slot.roi.x0 <= x0 < x1 <= slot.roi.x1
        assert slot.roi.y0 <= y0 < y1 <= slot.roi.y1
    assert np.array_equal(load_tiff(path).pixels, pixels)
