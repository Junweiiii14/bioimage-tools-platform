"""Independent synthetic regressions for reliable geometry: completeness."""

from pathlib import Path

import pytest
import tifffile
from wb_tool.api import (
    AutoWBSettings,
    WBIntakeCropProject,
    automatic_intake_crop_allowed,
    claim_intake_workflow_step,
    propose_intake_crop,
)
from wb_tool.domain.reliable_geometry import detect_reliable_geometry

from tools.wb.tests.common_policy_assertions import assert_prominent_row
from tools.wb.tests.test_intake_automatic_crop import prepared
from tools.wb.tests.test_reliable_geometry_exclusions import component_scene


@pytest.mark.parametrize(
    "name,bands",
    [
        (
            "weak_close_terminal",
            [(250, 120, 11, 5, 8000), (280, 120, 11, 5, 8000), (310, 120, 11, 5, 49000)],
        ),
        (
            "narrow_terminal",
            [(250, 120, 16, 5, 8000), (300, 120, 16, 5, 8000), (350, 120, 5, 2, 8000)],
        ),
    ],
)
def test_subset_cannot_reach_accepted_state(
    tmp_path: Path, name: str, bands: list[tuple[float, int, int, int, int]]
) -> None:
    signal, _ = component_scene(bands)
    path = tmp_path / f"{name}.tiff"
    tifffile.imwrite(path, signal)
    project, ticket = claim_intake_workflow_step(prepared(path, count=2), session_key="independent")
    assert isinstance(project, WBIntakeCropProject)
    assert ticket
    evidence = propose_intake_crop(str(path), project, "r")
    bounds = [(int(x - hw + 1), y - hh + 1, int(x + hw), y + hh) for x, y, hw, hh, _ in bands[:2]]
    assert_prominent_row(evidence, path, signal, bounds)
    # An explicit third sample cannot be converted to a two-slot result.
    three = propose_intake_crop(str(path), prepared(path, count=3), "r")
    assert three.lane_count == len(three.slots) == 3
    if automatic_intake_crop_allowed(three):
        roi = three.slots[2].roi
        x, y, hw, hh, _ = bands[2]
        assert roi and roi.x0 <= x - hw + 1 and roi.x1 >= x + hw
        assert roi.y0 <= y - hh + 1 and roi.y1 >= y + hh


@pytest.mark.parametrize("count", [4, 5])
@pytest.mark.parametrize("half_height", [2, 3, 5])
@pytest.mark.parametrize("weak_value", [8000, 47500, 49000])
def test_complete_n_does_not_miss_new_fallback(
    tmp_path: Path, count: int, half_height: int, weak_value: int
) -> None:
    bands = [
        (
            300 + (i - (count - 1) / 2) * 50,
            120,
            16,
            half_height,
            weak_value if i == count - 1 else 8000,
        )
        for i in range(count)
    ]
    signal, _ = component_scene(bands)
    direct = detect_reliable_geometry(signal, signal, AutoWBSettings(lane_count=count))
    assert direct.candidates, direct.flags
    path = tmp_path / "complete.tiff"
    tifffile.imwrite(path, signal)
    evidence = propose_intake_crop(str(path), prepared(path, count=count), "r")
    assert automatic_intake_crop_allowed(evidence), (
        count,
        half_height,
        weak_value,
        evidence.reason,
    )
