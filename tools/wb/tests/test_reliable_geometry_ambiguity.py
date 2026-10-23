"""Independent synthetic regressions for reliable geometry: ambiguity."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from numpy.typing import NDArray
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


def _base() -> tuple[NDArray[np.int64], NDArray[np.int64], NDArray[np.uint16]]:
    yy, xx = np.mgrid[:240, :600]
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[(abs(xx - 300) < 230) & (abs(yy - 120) < 65)] = 50000
    return yy, xx, guide


@pytest.mark.parametrize("lower_count", [1, 3])
def test_unselected_partial_second_row_does_not_prove_target_identity(
    tmp_path: Path, lower_count: int
) -> None:
    yy, xx, signal = _base()
    for x in (275, 325):
        signal[(abs(xx - x) < 16) & (abs(yy - 102) < 5)] = 8000
    for x in [250 + i * 50 for i in range(lower_count)]:
        signal[(abs(xx - x) < 16) & (abs(yy - 138) < 5)] = 8000
    path = tmp_path / "two_targets.tiff"
    tifffile.imwrite(path, signal)
    p, ticket = claim_intake_workflow_step(prepared(path, count=2), session_key="ambiguous")
    assert isinstance(p, WBIntakeCropProject)
    assert ticket
    evidence = propose_intake_crop(str(path), p, "r")
    allowed = automatic_intake_crop_allowed(evidence)
    if allowed:
        # A complete main row may win over isolated off-row clutter, never a diagonal subset.
        assert_prominent_row(evidence, path, signal, [(260, 98, 291, 107), (310, 98, 341, 107)])
    else:
        assert lower_count == 3


def test_unrotated_frame_can_retain_all_observed_original_pixels() -> None:
    yy, xx, guide = _base()
    signal = guide.copy()
    masks: list[NDArray[np.bool_]] = []
    for x, angle in [(275, 6), (325, -6)]:
        slope = np.tan(np.deg2rad(angle))
        mask = (abs(xx - x) < 16) & (abs(yy - 120 - (xx - x) * slope) < 5)
        masks.append(mask)
        signal[mask] = 8000
    before = signal.copy()
    detection = detect_reliable_geometry(signal, guide, AutoWBSettings(lane_count=2))
    assert len(detection.candidates) == 1, detection.flags
    candidate = detection.candidates[0]
    assert "unrotated_complete_geometry@1" in detection.flags
    assert candidate.display_frame and candidate.display_frame.angle_degrees == 0
    for mask, roi in zip(masks, candidate.lane_rois, strict=True):
        y, x = np.nonzero(mask)
        assert roi.x0 <= x.min() <= x.max() < roi.x1
        assert roi.y0 <= y.min() <= y.max() < roi.y1
    assert np.array_equal(before, signal)


@pytest.mark.parametrize(
    "kind", ["narrow_tall", "narrow_tilted", "fragmented_weak", "horizontal_weak"]
)
def test_proposed_extra_slot_filter_does_not_erase_unknown_third_target(
    tmp_path: Path, kind: str
) -> None:
    """The proposed rule reached the shared working tree during review.

    This now tests that implementation directly, through original synthetic
    TIFF input and the public proposal/acceptance API. No monkeypatch is used.
    """

    yy, xx = np.mgrid[:400, :1000]
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[(abs(xx - 500) < 400) & (abs(yy - 200) < 100)] = 50000
    signal = guide.copy()
    for x in (350, 500):
        signal[(abs(xx - x) < 51) & (abs(yy - 200) < 22)] = 8000
    if kind == "narrow_tall":
        signal[(abs(xx - 650) < 16) & (abs(yy - 200) < 26)] = 49000
    elif kind == "narrow_tilted":
        angle = np.deg2rad(25)
        u = (xx - 650) * np.cos(angle) + (yy - 200) * np.sin(angle)
        v = -(xx - 650) * np.sin(angle) + (yy - 200) * np.cos(angle)
        signal[(abs(u) < 16) & (abs(v) < 8)] = 49000
    elif kind == "fragmented_weak":
        for x in (630, 650, 670):
            signal[(abs(xx - x) < 9) & (abs(yy - 200) < 7)] = 49000
    else:
        signal[(abs(xx - 650) < 16) & (abs(yy - 200) < 5)] = 49000

    settings = AutoWBSettings(lane_count=2)
    actual = detect_reliable_geometry(signal, guide, settings)
    assert not actual.candidates, actual.flags
    path = tmp_path / f"{kind}.tiff"
    tifffile.imwrite(path, signal)
    project, ticket = claim_intake_workflow_step(
        prepared(path, count=2), session_key="shape-review"
    )
    assert isinstance(project, WBIntakeCropProject)
    assert ticket
    evidence = propose_intake_crop(str(path), project, "r")
    assert_prominent_row(evidence, path, signal, [(300, 179, 401, 222), (450, 179, 551, 222)])
