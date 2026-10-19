"""Original-coordinate ratio policy and compatibility checks."""

from dataclasses import asdict

import numpy as np
import pytest
from pydantic import TypeAdapter
from wb_tool.api import (
    AutoWBSettings,
    LaneROI,
    detect_automatic_geometry,
    resize_crop_for_lane_count,
)


def test_ratio_detection_covers_known_bands_without_changing_original() -> None:
    pixels = np.full((180, 360), 50000, dtype=np.uint16)
    for x in (60, 120, 180, 240, 300):
        pixels[70:85, x - 17 : x + 17] = 15000
    before = pixels.copy()
    result = detect_automatic_geometry(pixels, AutoWBSettings(crop_policy="lane_ratio@1"))
    assert result.settings.lane_count == 5
    assert len(result.candidates) == 1
    crop = result.candidates[0].roi
    assert crop.x0 <= 43 and crop.x1 >= 317
    assert crop.y0 <= 70 and crop.y1 >= 85
    assert abs(crop.width - 6.25 * (crop.y1 - crop.y0)) <= 0.5
    assert np.array_equal(pixels, before)
    assert "crop_policy:lane_ratio@1" in result.flags


def test_old_settings_omit_policy_and_still_use_fixed_height() -> None:
    old = asdict(AutoWBSettings())
    del old["crop_policy"]
    settings = TypeAdapter(AutoWBSettings).validate_python(old)
    assert settings.crop_policy == "legacy_fixed_height@1"
    pixels = np.full((180, 360), 50000, dtype=np.uint16)
    for x in (60, 120, 180, 240, 300):
        pixels[70:85, x - 17 : x + 17] = 15000
    result = detect_automatic_geometry(pixels, settings)
    assert result.candidates[0].roi.y1 - result.candidates[0].roi.y0 == 60


def test_change_n_keeps_height_and_centre() -> None:
    original = LaneROI("r", 300, 100, 600, 180)
    resized = resize_crop_for_lane_count(original, 5, 1000, 800)
    assert resized == LaneROI("r", 200, 100, 700, 180)
    assert original == LaneROI("r", 300, 100, 600, 180)


@pytest.mark.parametrize("count", [0, 97, True, 1.5])
def test_change_n_rejects_invalid_count(count: int) -> None:
    with pytest.raises(ValueError):
        resize_crop_for_lane_count(LaneROI("r", 100, 100, 400, 180), count, 1000, 800)


def test_change_n_never_clips_or_moves_centre_to_hide_boundary() -> None:
    with pytest.raises(ValueError, match="无法容纳"):
        resize_crop_for_lane_count(LaneROI("r", 0, 100, 300, 180), 5, 1000, 800)


def test_ratio_resize_rounding_is_at_most_half_pixel() -> None:
    for height in range(2, 90):
        for count in range(1, 12):
            crop = LaneROI("r", 2000, 10, 2301, 10 + height)
            resized = resize_crop_for_lane_count(crop, count, 5000, 1000)
            assert abs(resized.width - 1.25 * count * height) <= 0.5
            assert abs(resized.x0 + resized.x1 - crop.x0 - crop.x1) <= 1


def test_ratio_empty_image_stays_explicitly_unlocated() -> None:
    result = detect_automatic_geometry(
        np.full((180, 360), 100, dtype=np.uint8),
        AutoWBSettings(crop_policy="lane_ratio@1"),
    )
    assert not result.candidates
    assert "no_sample_bands" in result.flags
