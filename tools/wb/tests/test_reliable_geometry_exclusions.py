"""Independent synthetic regressions for reliable geometry: exclusions."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from numpy.typing import NDArray
from wb_tool.api import AutoWBSettings, automatic_intake_crop_allowed, propose_intake_crop
from wb_tool.domain.reliable_geometry import detect_reliable_geometry

from tools.wb.tests.test_intake_automatic_crop import prepared


def component_scene(
    bands: list[tuple[float, int, int, int, int]],
) -> tuple[NDArray[np.uint16], NDArray[np.uint16]]:
    yy, xx = np.mgrid[:240, :600]
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[(abs(xx - 300) < 230) & (abs(yy - 120) < 65)] = 50000
    signal = guide.copy()
    for x, y, half_width, half_height, value in bands:
        signal[(abs(xx - x) < half_width) & (abs(yy - y) < half_height)] = value
    return signal, guide


@pytest.mark.parametrize(
    "name,bands",
    [
        (
            "weak_terminal",
            [(250, 120, 16, 5, 8000), (300, 120, 16, 5, 8000), (350, 120, 16, 5, 49000)],
        ),
        (
            "displaced_terminal",
            [(250, 120, 16, 5, 8000), (300, 120, 16, 5, 8000), (350, 129, 16, 5, 8000)],
        ),
        (
            "sample_doublet_as_marker",
            [
                (170, 120, 16, 5, 8000),
                (220, 120, 16, 5, 8000),
                (270, 120, 16, 5, 8000),
                (170, 95, 16, 5, 8000),
            ],
        ),
        (
            "tall_terminal",
            [(250, 120, 16, 5, 8000), (300, 120, 16, 5, 8000), (350, 120, 16, 12, 8000)],
        ),
    ],
)
def test_unselected_third_lane_must_not_be_discarded(
    tmp_path: Path, name: str, bands: list[tuple[float, int, int, int, int]]
) -> None:
    signal, guide = component_scene(bands)
    direct = detect_reliable_geometry(signal, guide, AutoWBSettings(lane_count=2))
    assert not direct.candidates, direct.flags
    path = tmp_path / f"{name}.tiff"
    tifffile.imwrite(path, signal)
    evidence = propose_intake_crop(str(path), prepared(path, count=2), "r")
    assert not automatic_intake_crop_allowed(evidence), f"Wrong 2-of-3 row accepted: {name}"
