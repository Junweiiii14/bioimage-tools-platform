"""Original-coordinate limits, exclusions, and frozen historical evidence."""

import json

import numpy as np
import pytest
from wb_tool.application.intake_crop import IntakeFixedGrid
from wb_tool.domain.anchored_context import propose_anchored_lanes
from wb_tool.domain.band_geometry_support import bounded_background_limits
from wb_tool.domain.lanes import LaneROI, compute_lane_profiles
from wb_tool.domain.quantify import integrate_profile
from wb_tool.domain.source_geometry import DetectionPlane


def test_context_recovers_rectangular_area_without_changing_target() -> None:
    pixels = np.full((80, 12), 50000, dtype=np.uint16)
    pixels[34:47] = 20000
    before = pixels.tobytes()
    plane = DetectionPlane(pixels.astype(float), np.ones(pixels.shape, dtype=bool), 0, 0, 0)
    target = LaneROI("lane", 2, 31, 10, 50)
    limits = bounded_background_limits(
        (target,), LaneROI("crop", 0, 20, 12, 60), plane, np.zeros(pixels.shape, dtype=bool)
    )
    assert limits == (LaneROI("lane", 2, 26, 10, 55),)
    legacy = propose_anchored_lanes(pixels, (target,), limits=(target,))[0]
    assert legacy.proposal.bands[0].notes == ("boundary_review:insufficient_background_support",)
    current = propose_anchored_lanes(pixels, (target,), limits=limits)[0]
    assert current.target == target and current.expansion_percent > 0
    band = current.proposal.bands[0]
    assert band.bounds is not None and band.baseline is not None and not band.notes
    measured = integrate_profile(
        compute_lane_profiles(pixels, current.proposal.roi, "dark").quantitative,
        band.bounds,
        band.baseline,
    )
    assert measured.signal == pytest.approx(13 * 30000, abs=1e-8)
    assert pixels.tobytes() == before


@pytest.mark.parametrize("hazard", ["other_band", "membrane_hole", "crop_edge"])
def test_context_stops_at_nearest_forbidden_source_row(hazard: str) -> None:
    values = np.zeros((80, 12))
    valid = np.ones(values.shape, dtype=bool)
    excluded = np.zeros(values.shape, dtype=bool)
    crop = LaneROI("crop", 0, 20, 12, 60)
    if hazard == "other_band":
        excluded[29, 5] = True
        excluded[51, 5] = True
    elif hazard == "membrane_hole":
        valid[29, 5] = False
        valid[51, 5] = False
    else:
        crop = LaneROI("crop", 0, 30, 12, 51)
    target = LaneROI("lane", 2, 31, 10, 50)
    plane = DetectionPlane(values, valid, 0, 0, 0)
    assert bounded_background_limits((target,), crop, plane, excluded) == (
        LaneROI("lane", 2, 30, 10, 51),
    )


def test_legacy_grid_wire_does_not_acquire_context_policy() -> None:
    old: dict[str, object] = {
        "policy": "fixed_n_frame@2",
        "sampling_policy": "source_axis_partition@2",
        "lane_width_pixels": 48,
        "width_basis": "source_row_estimate",
        "calibration": None,
        "source_estimate": None,
        "sampling_limits": [],
        "review_positions": [],
    }
    grid = IntakeFixedGrid.model_validate_json(json.dumps(old))
    assert grid.model_dump(mode="json") == old
    new = IntakeFixedGrid.model_validate_json(
        json.dumps({**old, "context_policy": "bounded_background_context@1"})
    )
    assert new.model_dump()["context_policy"] == "bounded_background_context@1"
    with pytest.raises(ValueError):
        IntakeFixedGrid.model_validate_json(
            json.dumps({**old, "context_policy": "bounded_background_context@2"})
        )
