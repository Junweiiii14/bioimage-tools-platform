"""Analytical geometry expectations, fixed before implementation."""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st
from wb_tool.api import BandBounds, Baseline, QuantificationError, integrate_profile


@pytest.mark.parametrize(
    ("profile", "baseline", "expected"),
    [
        ([10.0, 20.0, 10.0], None, 10.0),
        ([10.0, 20.0, 20.0, 10.0], None, 20.0),
        ([10.0, 15.0, 20.0], None, 0.0),
        ([10.0, 0.0, 20.0], None, 0.0),
        ([4.0, 8.0, 4.0], Baseline(0, 0), 12.0),
        ([8.0, 8.0], Baseline(0, 0), 8.0),
    ],
)
def test_analytic_areas(profile: list[float], baseline: Baseline | None, expected: float) -> None:
    before = profile.copy()
    result = integrate_profile(profile, BandBounds(0, len(profile) - 1), baseline)
    assert result.signal == expected
    assert result.algorithm_id == "profile_integral@1"
    assert result.unit == "intensity*pixel"
    assert result.baseline_source == ("endpoints" if baseline is None else "manual")
    assert profile == before


def test_inclusive_subwindow() -> None:
    bounds = BandBounds(1, 3)
    profile = [200.0, 10.0, 20.0, 10.0, 200.0]
    assert profile[bounds.image_slice] == [10.0, 20.0, 10.0]
    assert integrate_profile(profile, bounds).signal == 10


@pytest.mark.parametrize(("left", "right"), [(0, 0), (-1, 2), (3, 2), (True, 2)])
def test_invalid_bounds(left: int, right: int) -> None:
    with pytest.raises(QuantificationError):
        BandBounds(left, right)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, -1.0, True])
def test_invalid_profile(value: float) -> None:
    with pytest.raises(QuantificationError):
        integrate_profile([10.0, value, 10.0], BandBounds(0, 2))


@pytest.mark.parametrize("value", [math.nan, math.inf, -1.0, True])
def test_invalid_baseline(value: float) -> None:
    with pytest.raises(QuantificationError):
        Baseline(value, 0.0)


def test_out_of_bounds() -> None:
    with pytest.raises(QuantificationError):
        integrate_profile([10.0, 20.0], BandBounds(0, 2))


def test_finite_inputs_can_overflow_integral() -> None:
    with pytest.raises(QuantificationError, match="浮点范围"):
        integrate_profile([1e308] * 4, BandBounds(0, 3), Baseline(0, 0))


@given(
    height=st.integers(0, 65535),
    background=st.integers(0, 65535),
    factor=st.integers(1, 100),
)
def test_triangle_scale_and_background_invariance(
    height: int, background: int, factor: int
) -> None:
    bounds = BandBounds(0, 2)
    result = integrate_profile(
        [float(background), float(background + height), float(background)], bounds
    )
    scaled = integrate_profile([0.0, float(height * factor), 0.0], bounds)
    assert result.signal == height
    assert scaled.signal == height * factor
