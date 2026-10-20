"""Complete support, shared valleys, ROI limits and old-reference compatibility."""

import numpy as np
import pytest
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.peak_envelope import close_peak_envelopes
from wb_tool.domain.quant_supervision import propose_quant_lanes


def test_shoulder_minimum_does_not_cut_off_half_the_peak() -> None:
    # A shallow local dip near the apex must not become the closing endpoint.
    values = np.array([10, 10, 20, 40, 70, 90, 89, 100, 90, 70, 40, 20, 10, 10.0])
    peak = close_peak_envelopes(values, (7,))[0]
    assert (peak.bounds.left, peak.bounds.right) == (1, 12)
    assert peak.baseline.left_value == peak.baseline.right_value == 10
    assert not any(n.startswith("boundary_review:") for n in peak.notes)


def test_distinct_peaks_share_one_valley_without_double_area() -> None:
    values = np.array([10, 10, 30, 60, 30, 10, 10, 20, 50, 20, 10, 10.0])
    first, second = close_peak_envelopes(values, (3, 8))
    assert first.bounds.right == second.bounds.left == 5
    assert first.bounds.left == 1 and second.bounds.right == 10


def test_cropped_peak_retains_review_flag_and_never_looks_outside_roi() -> None:
    values = np.array([90, 92, 100, 90, 50, 20, 10.0])
    peak = close_peak_envelopes(values, (2,))[0]
    assert (peak.bounds.left, peak.bounds.right) == (0, 6)
    assert "boundary_review:background_at_roi_edge" in peak.notes
    assert "boundary_review:unequal_or_overlapping_peak_support" in peak.notes


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16])
def test_cropped_reference_preserves_original_coordinates_and_values(
    dtype: type[np.uint8] | type[np.uint16],
) -> None:
    maximum = np.iinfo(dtype).max
    values = 20 + np.maximum(0, 100 - 10 * np.abs(np.arange(80) - 40))
    crop = np.repeat((maximum - values).astype(dtype)[:, None], 30, axis=1)
    sheet = np.full((140, 160), maximum, dtype=dtype)
    sheet[30:110, 65:95] = crop
    local = propose_quant_lanes(crop, (LaneROI("a", 0, 0, 30, 80),))[0]
    actual = propose_quant_lanes(sheet, (LaneROI("a", 65, 30, 95, 110),))[0]
    assert actual.roi == LaneROI(
        "a", local.roi.x0 + 65, local.roi.y0 + 30, local.roi.x1 + 65, local.roi.y1 + 30
    )
    assert [(b.bounds, b.baseline) for b in actual.bands] == [
        (b.bounds, b.baseline) for b in local.bands
    ]


def test_invalid_profile_is_rejected() -> None:
    with pytest.raises(ValueError):
        close_peak_envelopes(np.array([0, np.nan, 0]), (1,))
