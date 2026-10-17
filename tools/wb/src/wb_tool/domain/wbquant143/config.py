from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite

from .errors import QuantificationError


@dataclass(frozen=True, slots=True)
class AlgorithmConfig:
    prominence_fraction: float = 0.05
    min_width_px: float = 3.0
    min_distance_px: int = 5
    smoothing_sigma: float = 0.0

    def __post_init__(self) -> None:
        if not isfinite(self.prominence_fraction) or self.prominence_fraction < 0:
            raise QuantificationError("prominence_fraction must be finite and non-negative")
        if not isfinite(self.min_width_px) or self.min_width_px <= 0:
            raise QuantificationError("min_width_px must be finite and positive")
        if self.min_distance_px < 1:
            raise QuantificationError("min_distance_px must be at least 1")
        if not isfinite(self.smoothing_sigma) or self.smoothing_sigma < 0:
            raise QuantificationError("smoothing_sigma must be finite and non-negative")

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)

