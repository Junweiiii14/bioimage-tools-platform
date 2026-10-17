"""Narrow typed surface for the locked SciPy functions used by geometry detection.

SciPy 1.18.1 does not ship typing metadata. Only its module imports suppress the
missing-stub diagnostic; call sites use explicit signatures instead of Any.
"""

from typing import Protocol, cast

import numpy as np
from numpy.typing import NDArray
from scipy import ndimage as _ndimage  # pyright: ignore[reportMissingTypeStubs]
from scipy import signal as _signal  # pyright: ignore[reportMissingTypeStubs]


class GeometryFilters(Protocol):
    def label(self, input: NDArray[np.bool_]) -> tuple[NDArray[np.int32], int]: ...
    def binary_fill_holes(self, input: NDArray[np.bool_]) -> NDArray[np.bool_]: ...
    def binary_erosion(self, input: NDArray[np.bool_], *, iterations: int) -> NDArray[np.bool_]: ...
    def map_coordinates(
        self,
        input: NDArray[np.float64],
        coordinates: list[NDArray[np.float64]],
        *,
        order: int,
        mode: str,
    ) -> NDArray[np.float64]: ...
    def maximum_filter1d(
        self, input: NDArray[np.float64], size: int, axis: int = -1
    ) -> NDArray[np.float64]: ...
    def gaussian_filter(self, input: NDArray[np.float64], sigma: float) -> NDArray[np.float64]: ...
    def gaussian_filter1d(
        self, input: NDArray[np.float64], sigma: float
    ) -> NDArray[np.float64]: ...


class SignalPeaks(Protocol):
    def find_peaks(
        self, x: NDArray[np.float64], *, prominence: float, distance: int
    ) -> tuple[NDArray[np.int64], dict[str, NDArray[np.float64]]]: ...


filters = cast(GeometryFilters, _ndimage)
peaks = cast(SignalPeaks, _signal)
