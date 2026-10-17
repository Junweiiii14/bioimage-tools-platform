"""Source-only geometric oracles: angled rectangles, distinct marker, original samples."""

from math import cos, radians, sin
from pathlib import Path

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from wb_tool.api import AutoWBSettings, detect_automatic_geometry


def membrane(count: int = 5, angle: float = 0, marker: bool = True) -> np.ndarray:
    yy, xx = np.mgrid[:300, :700]
    c, s = cos(radians(angle)), sin(radians(angle))
    u, v = (xx - 350) * c + (yy - 150) * s, -(xx - 350) * s + (yy - 150) * c
    width = (count + int(marker)) * 48 + 20
    raw = np.full(xx.shape, 15, dtype=np.uint16)
    inside = (np.abs(u) < width / 2) & (np.abs(v) < 45)
    raw[inside] = 50000
    first = -width / 2 + 34
    for i in range(count):
        x = first + (i + int(marker)) * 48
        raw[(np.abs(u - x) < 17) & (np.abs(v) < 7)] = 8000 if i % 2 else 20000
    if marker:
        for y in (-22, 22):
            raw[(np.abs(u - first) < 17) & (np.abs(v - y) < 5)] = 17000
    return raw


@pytest.mark.parametrize("angle", [-9, -4, 0, 4, 9])
@pytest.mark.parametrize("marker", [False, True])
def test_tilted_short_membrane_and_marker(angle: float, marker: bool) -> None:
    raw = membrane(angle=angle, marker=marker)
    before = raw.copy()
    result = detect_automatic_geometry(raw, AutoWBSettings(crop_policy="source_geometry@2"))
    assert result.candidates, result.flags
    assert result.settings.lane_count == 5
    candidate = result.candidates[0]
    assert candidate.display_frame is not None
    assert abs(candidate.display_frame.angle_degrees - angle) < 1
    assert (result.marker is not None) == marker
    assert len(candidate.lane_rois) == 5
    for a, b in zip(candidate.lane_rois, candidate.lane_rois[1:], strict=False):
        assert a.x1 <= b.x0
    assert np.array_equal(raw, before)


@example(angle=7.0, count=8)
@settings(max_examples=12, deadline=None)
@given(angle=st.floats(min_value=-9, max_value=9, allow_nan=False), count=st.integers(3, 8))
def test_original_geometry_contains_each_known_band(angle: float, count: int) -> None:
    raw = membrane(count=count, angle=angle)
    result = detect_automatic_geometry(raw, AutoWBSettings(crop_policy="source_geometry@2"))
    assert result.settings.lane_count == count, result.flags
    lanes = result.candidates[0].lane_rois
    # Independent known generator centre, rather than recomputing detector output.
    first = -((count + 1) * 48 + 20) / 2 + 34
    for i, roi in enumerate(lanes):
        x = first + (i + 1) * 48
        cx, cy = 350 + x * cos(radians(angle)), 150 + x * sin(radians(angle))
        assert roi.x0 < cx < roi.x1 and roi.y0 < cy < roi.y1


def test_blank_and_cancel_are_not_success() -> None:
    raw = np.full((200, 400), 20000, dtype=np.uint16)
    assert not detect_automatic_geometry(
        raw, AutoWBSettings(crop_policy="source_geometry@2")
    ).candidates
    with pytest.raises(ValueError, match="取消"):
        detect_automatic_geometry(
            membrane(), AutoWBSettings(crop_policy="source_geometry@2"), cancelled=lambda: True
        )


def test_explicit_n_conflict_does_not_invent_slots() -> None:
    result = detect_automatic_geometry(
        membrane(), AutoWBSettings(crop_policy="source_geometry@2", lane_count=6)
    )
    assert not result.candidates
    assert "explicit_lane_count_conflicts_with_evidence" in result.flags


@pytest.mark.parametrize("marker", [False, True])
def test_explicit_marker_exclusion_preserves_sample_without_marker_in_target_row(
    marker: bool,
) -> None:
    result = detect_automatic_geometry(
        membrane(marker=marker),
        AutoWBSettings(crop_policy="source_geometry@2", left_marker="exclude"),
    )
    assert result.candidates and result.settings.lane_count == 5
    assert (result.marker is not None) == marker


def test_reanalysis_preserves_source_frame(tmp_path: Path) -> None:
    import tifffile
    from wb_tool.api import automatic_project_row

    from tools.wb.tests.test_automatic_wb import project_for

    path = tmp_path / "tilted.tif"
    tifffile.imwrite(path, membrane(angle=7))
    first = automatic_project_row(path, project_for(path), "r", crop_policy="source_geometry@2")
    frame = first.composition.slices[0].display_frame
    assert frame is not None
    again = automatic_project_row(path, first, "r", quant_policy="background_support@1")
    assert again.composition.slices[0].display_frame == frame
    assert tuple(lane.roi for lane in again.analyses[0].request.lanes) == tuple(
        lane.roi for lane in first.analyses[0].request.lanes
    )


@pytest.mark.parametrize("light", [False, True])
def test_pre_cropped_uniform_field_retains_supported_input(light: bool) -> None:
    raw = np.full((180, 360), 50000, dtype=np.uint16)
    for x in (60, 120, 180, 240, 300):
        raw[70:85, x - 17 : x + 17] = 15000
    if light:
        raw = 65535 - raw
    result = detect_automatic_geometry(
        raw, AutoWBSettings(crop_policy="source_geometry@2", polarity="light" if light else "dark")
    )
    assert result.candidates and result.settings.lane_count == 5
    assert "uniform_background_field_without_orientation_evidence" in result.flags
