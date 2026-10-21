"""Analytical fixed-grid oracles, independent of blob/peak detection."""

import numpy as np
import pytest
from wb_tool.domain.fixed_lane_frame import fixed_lane_frame


@pytest.mark.parametrize("count", [1, 2, 5])
@pytest.mark.parametrize("width", [50.0, 57.5, 115.0])
@pytest.mark.parametrize("angle", [-9.0, 0.0, 9.0])
def test_fixed_frame_ratio_pixel_partition_and_complete_band_support(
    count: int, width: float, angle: float
) -> None:
    frame, crop, lanes = fixed_lane_frame(count, width, 500, 250, angle, 1000, 500)
    assert frame.width == count * width and frame.height == 0.8 * width
    assert len(lanes) == count
    assert lanes[0].x0 == crop.x0 and lanes[-1].x1 == crop.x1
    assert all(a.x1 == b.x0 for a, b in zip(lanes, lanes[1:], strict=False))
    yy, xx = np.mgrid[:500, :1000]
    c, s = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
    u, v = (xx - 500) * c + (yy - 250) * s, -(xx - 500) * s + (yy - 250) * c
    for i, roi in enumerate(lanes):
        # Each analytic band belongs to exactly one axis partition;
        # no duplicated rotated bounding boxes.
        band = (abs(u - (i - (count - 1) / 2) * width) < width * 0.32) & (abs(v) < width * 0.1)
        assert np.count_nonzero(band[roi.y0 : roi.y1, roi.x0 : roi.x1]) == band.sum()
        assert crop.y0 <= roi.y0 < roi.y1 <= crop.y1
    if angle and count > 1:
        assert len({(r.y0, r.y1) for r in lanes}) > 1


def test_verified_slot_width_is_not_replaced_by_peak_spacing() -> None:
    frame, crop, lanes = fixed_lane_frame(2, 115, 300, 120, 0, 600, 240)
    assert (frame.width, frame.height) == (230, 92)
    assert (crop.x0, crop.y0, crop.x1, crop.y1) == (185, 74, 415, 166)
    # Peak spacing 108 still fits; it does not resize the declared 115px grid.
    assert lanes[0].x0 < 246 < lanes[0].x1 and lanes[1].x0 < 354 < lanes[1].x1


def test_rotated_outer_box_does_not_use_display_aspect_ratio() -> None:
    frame, crop, _ = fixed_lane_frame(5, 100, 500, 250, 9, 1000, 500)
    assert (frame.width, frame.height) == (500, 80)
    assert (crop.width, crop.y1 - crop.y0) == (508, 158)


@pytest.mark.parametrize("width,angle", [(0.0, 0), (float("nan"), 0), (50.0, 11)])
def test_invalid_scale_or_angle_is_not_clipped_into_success(width: float, angle: float) -> None:
    with pytest.raises(ValueError):
        fixed_lane_frame(2, width, 300, 120, angle, 600, 240)
    with pytest.raises(ValueError, match="超出"):
        fixed_lane_frame(5, 115, 20, 120, 0, 600, 240)
