"""Reference profile_integral@1; discrete intensity times pixel, no width multiplier."""

from collections.abc import Sequence
from dataclasses import dataclass
from math import fsum, isfinite
from typing import Literal


class QuantificationError(ValueError):
    """Invalid quantitative input; never represented as a valid zero measurement."""


@dataclass(frozen=True, slots=True)
class BandBounds:
    """Inclusive endpoints relative to the original, unsmoothed lane profile."""

    left: int
    right: int

    def __post_init__(self) -> None:
        if (
            type(self.left) is not int
            or type(self.right) is not int
            or not 0 <= self.left < self.right
        ):
            raise QuantificationError("条带边界须为非负整数，且至少包含两个采样点")

    @property
    def image_slice(self) -> slice:
        """Half-open image row slice, before adding the lane's y origin."""
        return slice(self.left, self.right + 1)


@dataclass(frozen=True, slots=True)
class Baseline:
    """Endpoint intensities in the same polarity and units as the profile."""

    left_value: float
    right_value: float

    def __post_init__(self) -> None:
        for value in (self.left_value, self.right_value):
            if isinstance(value, bool) or not isfinite(value) or value < 0:
                raise QuantificationError("基线端点须为非负有限强度")


@dataclass(frozen=True, slots=True)
class ProfileMeasurement:
    signal: float
    bounds: BandBounds
    baseline: Baseline
    baseline_source: Literal["endpoints", "manual"]
    algorithm_id: Literal["profile_integral@1"] = "profile_integral@1"
    unit: Literal["intensity*pixel"] = "intensity*pixel"


def integrate_profile(
    profile: Sequence[float], bounds: BandBounds, baseline: Baseline | None = None
) -> ProfileMeasurement:
    """Integrate positive sampled excess over a linear baseline, with unit y spacing.

    The caller supplies original quantitative values in declared polarity, never a
    display or smoothed detection profile. Valid flat regions return zero; absent
    bands are represented by the calling use case, not by calling this function.
    """
    if bounds.right >= len(profile):
        raise QuantificationError("条带边界超出泳道剖面")
    values = tuple(float(value) for value in profile)
    if any(isinstance(value, bool) for value in profile) or any(
        not isfinite(value) or value < 0 for value in values
    ):
        raise QuantificationError("剖面须仅包含非负有限强度")
    selected = baseline or Baseline(values[bounds.left], values[bounds.right])
    span = bounds.right - bounds.left
    excess: list[float] = []
    for offset, value in enumerate(values[bounds.left : bounds.right + 1]):
        fraction = offset / span
        background = (1 - fraction) * selected.left_value + fraction * selected.right_value
        excess.append(max(value - background, 0.0))
    try:
        signal = fsum(a / 2 + b / 2 for a, b in zip(excess[:-1], excess[1:], strict=True))
    except OverflowError as exc:
        raise QuantificationError("积分超出有限浮点范围") from exc
    if not isfinite(signal):
        raise QuantificationError("积分超出有限浮点范围")
    return ProfileMeasurement(
        signal, bounds, selected, "endpoints" if baseline is None else "manual"
    )
