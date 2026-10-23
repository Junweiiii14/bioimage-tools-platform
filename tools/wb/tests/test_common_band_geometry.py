"""Small independent pixel scenes for the common-row policy, not a coverage claim."""

import numpy as np
import pytest
from wb_tool.api import AutoWBSettings
from wb_tool.domain.common_band_geometry import detect_common_band_geometry
from wb_tool.domain.fixed_lane_frame import fixed_lane_frame


def _scene(
    *,
    angle: float = 0,
    missing: int | None = None,
    connected: bool = False,
    shadow: bool = False,
    membrane_half_height: int = 110,
    membrane_half_width: int = 250,
):
    yy, xx = np.mgrid[:300, :600]
    c, s = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
    u, v = (xx - 300) * c + (yy - 150) * s, -(xx - 300) * s + (yy - 150) * c
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[(abs(xx - 300) < membrane_half_width) & (abs(yy - 150) < membrane_half_height)] = 50000
    signal = guide.copy()
    centers = np.arange(-100, 101, 50)
    for index, center in enumerate(centers):
        if index != missing:
            signal[(abs(u - center) < 17) & (abs(v) < 6)] = 8000
    if connected:
        signal[(abs(u) < 117) & (abs(v) < 2)] = 14000
    if shadow:
        signal[(abs(xx - 300) < 110) & (abs(yy - 75) < 6)] = 16000
    return signal, guide, centers


@pytest.mark.parametrize("angle", [-17.4, 0, 22])
def test_source_coordinates_follow_signal_not_membrane(angle: float) -> None:
    signal, guide, centers = _scene(angle=angle)
    before, guide_before = signal.copy(), guide.copy()
    result = detect_common_band_geometry(
        signal, guide, AutoWBSettings(lane_count=5, left_marker="include")
    )
    assert len(result.candidates) == 1, result.flags
    candidate = result.candidates[0]
    assert candidate.display_frame is not None
    assert abs(candidate.display_frame.angle_degrees - angle) < 1
    assert len(candidate.lane_rois) == len(result.sampling_limits) == 5
    for roi, limit, pos in zip(candidate.lane_rois, result.sampling_limits, centers, strict=True):
        x, y = 300 + pos * np.cos(np.deg2rad(angle)), 150 + pos * np.sin(np.deg2rad(angle))
        assert roi.x0 <= x < roi.x1 and roi.y0 <= y < roi.y1
        assert limit.x0 <= roi.x0 < roi.x1 <= limit.x1
        assert limit.y0 <= roi.y0 < roi.y1 <= limit.y1
    assert all(
        a.x1 == b.x0 for a, b in zip(candidate.lane_rois, candidate.lane_rois[1:], strict=False)
    )
    assert np.array_equal(signal, before) and np.array_equal(guide, guide_before)


def test_contiguous_connected_band_still_has_five_samples() -> None:
    signal, guide, _ = _scene(connected=True)
    result = detect_common_band_geometry(
        signal, guide, AutoWBSettings(lane_count=5, left_marker="include")
    )
    assert len(result.candidates) == 1, result.flags
    lanes = result.candidates[0].lane_rois
    assert len(lanes) == 5
    assert all(r.x0 < x < r.x1 for r, x in zip(lanes, (200, 250, 300, 350, 400), strict=True))


def test_internal_negative_slot_retains_its_original_position() -> None:
    signal, guide, _ = _scene(missing=2)
    result = detect_common_band_geometry(
        signal, guide, AutoWBSettings(lane_count=5, left_marker="include")
    )
    assert len(result.candidates) == 1, result.flags
    candidate = result.candidates[0]
    assert len(candidate.lane_rois) == 5
    assert candidate.weak_lanes == (3,)
    assert candidate.lane_rois[2].x0 < 300 < candidate.lane_rois[2].x1
    assert candidate.lane_snr[2] == 0  # Detection score, never a measured zero result.


def test_broad_shadow_does_not_outvote_coherent_sample_row() -> None:
    signal, guide, _ = _scene(shadow=True)
    result = detect_common_band_geometry(
        signal, guide, AutoWBSettings(lane_count=5, left_marker="include")
    )
    assert len(result.candidates) == 1, result.flags
    candidate = result.candidates[0]
    assert candidate.display_frame is not None
    assert abs(candidate.display_frame.center_y - 150) < 2
    assert candidate.roi.y0 > 100


@pytest.mark.parametrize("secondary_intensity", [8000, 24000])
def test_complete_rows_require_a_prominent_winner(secondary_intensity: int) -> None:
    signal, guide, _ = _scene()
    yy, xx = np.mgrid[:300, :600]
    signal[:] = guide
    for x in (200, 250, 300, 350, 400):
        signal[(abs(xx - x) < 17) & (abs(yy - 144) < 4)] = 8000
        signal[(abs(xx - x) < 17) & (abs(yy - 156) < 4)] = secondary_intensity
    result = detect_common_band_geometry(
        signal, guide, AutoWBSettings(lane_count=5, left_marker="include")
    )
    if secondary_intensity == 8000:
        assert not result.candidates
        assert "common_rows_equally_prominent" in result.flags
    else:
        assert len(result.candidates) == 1, result.flags
        frame = result.candidates[0].display_frame
        assert frame is not None and abs(frame.center_y - 144) < 2


def test_tilted_raw_sampling_avoids_membrane_exterior() -> None:
    signal, guide, _ = _scene(angle=-24, membrane_half_height=65)
    result = detect_common_band_geometry(
        signal, guide, AutoWBSettings(lane_count=5, left_marker="include")
    )
    assert len(result.candidates) == 1, result.flags
    lanes = result.candidates[0].lane_rois
    assert len(lanes) == 5
    assert all(np.all(guide[r.y0 : r.y1, r.x0 : r.x1] == 50000) for r in lanes)
    selected = signal == 8000
    covered = np.zeros_like(selected)
    for roi in lanes:
        covered[roi.y0 : roi.y1, roi.x0 : roi.x1] = True
    assert np.all(covered[selected])


def test_only_outer_blank_padding_recedes_at_a_nearby_membrane_edge() -> None:
    signal, guide, _ = _scene(membrane_half_width=124)
    before, guide_before = signal.copy(), guide.copy()
    result = detect_common_band_geometry(
        signal, guide, AutoWBSettings(lane_count=5, left_marker="include")
    )
    assert len(result.candidates) == 1, result.flags
    frame = result.candidates[0].display_frame
    assert frame is not None
    _, _, original = fixed_lane_frame(
        5, frame.width / 5, frame.center_x, frame.center_y, frame.angle_degrees, 600, 300
    )
    selected = signal == 8000
    lanes = result.candidates[0].lane_rois
    assert len(lanes) == 5
    assert original[0].x0 < lanes[0].x0
    assert original[-1].x1 >= lanes[-1].x1
    assert [r.x1 for r in lanes[:-1]] == [r.x1 for r in original[:-1]]
    assert all(a.x1 == b.x0 for a, b in zip(lanes, lanes[1:], strict=False))
    assert all(np.all(guide[r.y0 : r.y1, r.x0 : r.x1] == 50000) for r in lanes)
    yy, xx = np.nonzero(selected)
    assert lanes[0].x0 + 3 <= xx.min() and lanes[-1].x1 - 4 >= xx.max()
    covered = np.zeros_like(selected)
    for roi in lanes:
        covered[roi.y0 : roi.y1, roi.x0 : roi.x1] = True
    assert np.all(covered[yy, xx])
    assert np.array_equal(signal, before) and np.array_equal(guide, guide_before)


def test_unknown_terminal_phase_and_cancel_do_not_fake_complete_geometry() -> None:
    signal, guide, _ = _scene(missing=0)
    result = detect_common_band_geometry(
        signal, guide, AutoWBSettings(lane_count=5, left_marker="include")
    )
    assert not result.candidates
    assert "common_terminal_slot_phase_unresolved" in result.flags
    with pytest.raises(ValueError, match="取消"):
        detect_common_band_geometry(
            signal, guide, AutoWBSettings(lane_count=5), cancelled=lambda: True
        )
