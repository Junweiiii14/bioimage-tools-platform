"""Analytic controls for target identity and original-pixel context proposals."""

import numpy as np
import pytest
from wb_tool.domain.anchored_context import context_padding, propose_anchored_lanes
from wb_tool.domain.background_bounds import propose_background_lanes
from wb_tool.domain.lanes import LaneROI, Polarity, compute_lane_profiles
from wb_tool.domain.quantify import integrate_profile


def pixels(profile: np.ndarray, polarity: str = "light") -> np.ndarray:
    values = profile if polarity == "light" else 65535 - profile
    return np.repeat(values.astype(np.uint16)[:, None], 4, axis=1)


@pytest.mark.parametrize("offset", [0, 19, 83])
@pytest.mark.parametrize("polarity", ["dark", "light"])
def test_context_recovers_known_sloping_area_without_moving_target(
    offset: int, polarity: Polarity
) -> None:
    profile = 3000.0 + np.arange(120 + offset) * 10
    profile[40 + offset : 60 + offset] += 1000
    source = pixels(profile, polarity)
    before = source.tobytes()
    target = LaneROI("lane", 0, 38 + offset, 4, 62 + offset)
    proposed = propose_anchored_lanes(source, (target,), polarity)[0]
    assert proposed.target == target
    assert 0 < proposed.expansion_percent <= 25
    roi = proposed.proposal.roi
    assert roi.x0 == target.x0 and roi.x1 == target.x1
    band = proposed.proposal.bands[0]
    assert band.bounds is not None and band.baseline is not None and not band.notes
    assert roi.y0 + band.bounds.left < 40 + offset
    assert roi.y0 + band.bounds.right >= 60 + offset
    measured = integrate_profile(
        compute_lane_profiles(source, roi, polarity).quantitative, band.bounds, band.baseline
    )
    assert measured.signal == pytest.approx(20000, abs=1e-8)
    assert source.tobytes() == before


def test_stronger_neighbour_cannot_replace_target() -> None:
    profile = np.full(120, 3000.0)
    profile[40:60] += 1000
    profile[65:75] += 10000
    source = pixels(profile)
    target = LaneROI("lane", 0, 38, 4, 62)
    original = propose_background_lanes(source, (target,), "light")[0]
    proposed = propose_anchored_lanes(source, (target,), "light")[0]
    assert proposed.expansion_percent == 0
    assert proposed.proposal == original
    assert "boundary_review:insufficient_background_support" in original.bands[0].notes


def test_no_target_does_not_borrow_signal_from_outside() -> None:
    profile = np.full(120, 3000.0)
    profile[65:75] += 10000
    target = LaneROI("lane", 0, 38, 4, 62)
    proposed = propose_anchored_lanes(pixels(profile), (target,), "light")[0]
    assert proposed.expansion_percent == 0
    assert proposed.proposal.roi == target
    assert proposed.proposal.bands[0].bounds is None


def test_truncated_peak_retains_original_diagnostic_area() -> None:
    profile = 3000 + 12000 * np.exp(-(((np.arange(60) - 30) / 30) ** 2))
    source = pixels(profile)
    target = LaneROI("lane", 0, 10, 4, 50)
    proposed = propose_anchored_lanes(source, (target,), "light")[0]
    assert proposed.expansion_percent == 0
    assert proposed.proposal == propose_background_lanes(source, (target,), "light")[0]
    assert "boundary_review:insufficient_background_support" in proposed.proposal.bands[0].notes


def test_supported_original_is_preserved_exactly() -> None:
    profile = np.full(100, 3000.0)
    profile[30:70] += 10000
    source = pixels(profile)
    target = LaneROI("lane", 0, 0, 4, 100)
    proposed = propose_anchored_lanes(source, (target,), "light")[0]
    assert proposed.expansion_percent == 0
    assert proposed.proposal == propose_background_lanes(source, (target,), "light")[0]


def test_rounding_is_integer_and_bounded() -> None:
    assert context_padding(30, 5) == 2
    assert context_padding(10, 5) == 1
    with pytest.raises(ValueError):
        context_padding(100, 30)


def test_detected_exclusion_blocks_background_expansion_even_for_a_weak_mark() -> None:
    profile = 3000.0 + np.arange(120) * 10
    profile[40:60] += 1000
    profile[64] += 25  # Below the dominant-peak heuristic, still a known exclusion.
    source = pixels(profile)
    target = LaneROI("lane", 0, 38, 4, 62)
    limited = propose_anchored_lanes(
        source, (target,), "light", limits=(LaneROI("limit", 0, 0, 4, 64),)
    )[0]
    assert limited.proposal.roi.y1 <= 64
    assert limited.proposal.bands[0].notes == ("boundary_review:insufficient_background_support",)
    assert limited.proposal.roi == target
