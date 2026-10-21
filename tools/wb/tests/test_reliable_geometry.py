"""Analytical small-N and ambiguous-row oracles, independent of detector output."""

import numpy as np
import pytest
from wb_tool.api import AutoWBSettings
from wb_tool.domain.reliable_geometry import detect_reliable_geometry


def scene(n: int, angle: float = 0, *, double: bool = False, weak: bool = False):
    yy, xx = np.mgrid[:240, :600]
    ca, sa = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
    u, v = (xx - 300) * ca + (yy - 120) * sa, -(xx - 300) * sa + (yy - 120) * ca
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[(abs(xx - 300) < 230) & (abs(yy - 120) < 65)] = 50000
    signal = guide.copy()
    centers = (np.arange(n) - (n - 1) / 2) * 50
    for i, pos in enumerate(centers):
        for row in (-18, 18) if double else (0,):
            mask = (abs(u - pos) < 16) & (abs(v - row) < 5)
            signal[mask] = 47500 if weak and i == n - 1 else 8000
    return signal, guide, centers


@pytest.mark.parametrize("n", [1, 2, 4, 5])
@pytest.mark.parametrize("angle", [-8, 0, 8])
def test_complete_original_slots_and_independent_angle(n: int, angle: float) -> None:
    signal, guide, centers = scene(n, angle)
    before = signal.copy()
    result = detect_reliable_geometry(signal, guide, AutoWBSettings(lane_count=n))
    assert len(result.candidates) == 1, result.flags
    candidate = result.candidates[0]
    assert candidate.display_frame and abs(candidate.display_frame.angle_degrees - angle) < 1
    assert len(candidate.lane_rois) == n
    for roi, pos in zip(candidate.lane_rois, centers, strict=True):
        x, y = 300 + pos * np.cos(np.deg2rad(angle)), 120 + pos * np.sin(np.deg2rad(angle))
        assert roi.x0 < x < roi.x1 and roi.y0 < y < roi.y1
    assert np.array_equal(signal, before)


@pytest.mark.parametrize("n", [1, 2, 4, 5])
def test_double_rows_and_wrong_n_pause(n: int) -> None:
    signal, guide, _ = scene(n, double=True)
    assert not detect_reliable_geometry(signal, guide, AutoWBSettings(lane_count=n)).candidates
    signal, guide, _ = scene(n + 1, weak=True)
    assert not detect_reliable_geometry(signal, guide, AutoWBSettings(lane_count=n)).candidates
    result = detect_reliable_geometry(signal, guide, AutoWBSettings(lane_count=n + 1))
    assert len(result.candidates) == 1, result.flags


def test_cancel_does_not_produce_geometry() -> None:
    signal, guide, _ = scene(2)
    with pytest.raises(ValueError, match="取消"):
        detect_reliable_geometry(
            signal, guide, AutoWBSettings(lane_count=2), cancelled=lambda: True
        )
