"""Appearance counterexamples for v1; not independent laboratory accuracy."""

import numpy as np
import pytest
from numpy.typing import NDArray
from wb_tool.domain.automatic import AutoWBSettings
from wb_tool.domain.prominent_band_geometry import detect_prominent_band_geometry


def scene(
    *, angle: float = 0.0, background: int = 50000
) -> tuple[NDArray[np.uint16], NDArray[np.uint16], NDArray[np.float64], NDArray[np.float64]]:
    yy, xx = np.mgrid[:320, :640]
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[30:290, 35:605] = background
    image = guide.copy()
    c, s = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
    u, v = (xx - 320) * c + (yy - 175) * s, -(xx - 320) * s + (yy - 175) * c
    return image, guide, u, v


def add_row(
    image: NDArray[np.uint16],
    u: NDArray[np.float64],
    v: NDArray[np.float64],
    *,
    y: float = 0,
    value: int = 8000,
    missing: int | None = None,
) -> None:
    for i, center in enumerate((-110, -55, 0, 55, 110)):
        if i != missing:
            image[(abs(u - center) < 17) & (abs(v - y) < 5)] = value


@pytest.mark.parametrize(
    "upper_value,lower_value,expected_y", [(8000, 9500, 150), (9500, 8000, 175), (8000, 8000, None)]
)
def test_close_or_equal_rows_still_choose_one_complete_row(
    upper_value: int, lower_value: int, expected_y: float | None
) -> None:
    image, guide, u, v = scene()
    add_row(image, u, v, y=-25, value=upper_value)
    add_row(image, u, v, value=lower_value)
    before = image.copy()
    result = detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=5))
    assert len(result.candidates) == 1, result.flags
    frame = result.candidates[0].display_frame
    assert frame is not None
    assert min(abs(frame.center_y - 150), abs(frame.center_y - 175)) < 1
    if expected_y is not None:
        assert abs(frame.center_y - expected_y) < 1
    assert len(result.candidates[0].lane_rois) == 5
    assert np.array_equal(image, before)


@pytest.mark.parametrize("interference", ["broad_shadow", "strong_stain"])
def test_clear_but_weaker_row_survives_stronger_non_band_interference(interference: str) -> None:
    image, guide, u, v = scene()
    add_row(image, u, v, value=44000)
    yy, xx = np.mgrid[:320, :640]
    if interference == "broad_shadow":
        image[(abs(xx - 320) < 170) & (abs(yy - 90) < 18)] = 1000
    else:
        image[(xx - 520) ** 2 + (yy - 80) ** 2 < 25**2] = 1000
    result = detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=5))
    assert len(result.candidates) == 1, result.flags
    candidate = result.candidates[0]
    assert candidate.display_frame is not None
    assert abs(candidate.display_frame.center_y - 175) < 1
    assert candidate.roi.y0 > 130


@pytest.mark.parametrize("n", [2, 4, 6])
def test_explicit_wrong_n_cannot_be_satisfied_by_dropping_or_inventing_samples(n: int) -> None:
    image, guide, u, v = scene()
    add_row(image, u, v)
    result = detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=n))
    assert not result.candidates, result.flags


def test_wrong_n_does_not_switch_from_prominent_row_to_weaker_matching_row() -> None:
    image, guide, u, v = scene()
    add_row(image, u, v)
    for center in (-82, -27, 28, 83):
        image[(abs(u - center) < 17) & (abs(v + 70) < 5)] = 20000
    result = detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=4))
    assert not result.candidates, result.flags


def test_connected_strong_row_outvotes_separated_weaker_row() -> None:
    image, guide, u, v = scene()
    add_row(image, u, v)
    image[(abs(u) < 127) & (abs(v) < 2)] = 10000
    add_row(image, u, v, y=60, value=22000)
    result = detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=5))
    assert len(result.candidates) == 1, result.flags
    frame = result.candidates[0].display_frame
    assert frame is not None and abs(frame.center_y - 175) < 1


def test_internal_missing_lane_keeps_full_original_region_and_slot_identity() -> None:
    image, guide, u, v = scene()
    add_row(image, u, v, missing=2)
    result = detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=5))
    assert len(result.candidates) == 1, result.flags
    candidate = result.candidates[0]
    assert candidate.weak_lanes == (3,)
    assert len(candidate.lane_rois) == len(result.sampling_limits) == 5
    assert candidate.lane_rois[2].x0 < 320 < candidate.lane_rois[2].x1
    assert all(
        a.x1 == b.x0 for a, b in zip(candidate.lane_rois, candidate.lane_rois[1:], strict=False)
    )


@pytest.mark.parametrize("n,pitch,half_width,half_height", [(3, 40, 17, 23), (5, 80, 36, 49)])
def test_complete_tall_support_changes_height_without_expanding_n_pitch(
    n: int, pitch: int, half_width: int, half_height: int
) -> None:
    image, guide, u, v = scene()
    for i in range(n):
        center = (i - (n - 1) / 2) * pitch
        image[(abs(u - center) < half_width) & (abs(v) < half_height)] = 8000
    result = detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=n))
    assert len(result.candidates) == 1, result.flags
    frame = result.candidates[0].display_frame
    assert frame is not None
    assert abs(frame.width - n * pitch) < 2
    assert frame.height > frame.width / n
    covered = np.zeros_like(image, dtype=bool)
    for roi in result.candidates[0].lane_rois:
        covered[roi.y0 : roi.y1, roi.x0 : roi.x1] = True
    assert np.all(covered[image == 8000])


@pytest.mark.parametrize("angle", [-22.0, 21.0])
def test_signal_angle_and_original_samples_survive_without_using_guide_angle(angle: float) -> None:
    image, guide, u, v = scene(angle=angle)
    add_row(image, u, v)
    original = image.copy()
    result = detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=5))
    assert len(result.candidates) == 1, result.flags
    candidate = result.candidates[0]
    assert candidate.display_frame is not None
    assert abs(candidate.display_frame.angle_degrees - angle) < 1
    covered = np.zeros(image.shape, dtype=bool)
    for roi in candidate.lane_rois:
        covered[roi.y0 : roi.y1, roi.x0 : roi.x1] = True
    assert np.all(covered[image == 8000])
    assert np.array_equal(image, original)


def test_uniform_signal_export_does_not_require_a_visible_membrane_edge() -> None:
    image, _, u, v = scene()
    image[:] = 50000
    add_row(image, u, v)
    result = detect_prominent_band_geometry(image, None, AutoWBSettings(lane_count=5))
    assert len(result.candidates) == 1, result.flags
    assert "uniform_signal_field@1" in result.flags
    assert len(result.candidates[0].lane_rois) == 5


def test_blank_and_one_continuous_shadow_do_not_invent_five_lanes() -> None:
    image, guide, _, _ = scene()
    assert not detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=5)).candidates
    image[100:130, 180:460] = 1000
    assert not detect_prominent_band_geometry(image, guide, AutoWBSettings(lane_count=5)).candidates
    with pytest.raises(ValueError, match="取消"):
        detect_prominent_band_geometry(
            image, guide, AutoWBSettings(lane_count=5), cancelled=lambda: True
        )
