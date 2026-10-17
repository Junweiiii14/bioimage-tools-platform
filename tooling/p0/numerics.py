"""Narrow typed adapter for SciPy's untyped API, tested against analytic constants."""

from __future__ import annotations

import importlib
from typing import Protocol, cast

import numpy as np
import numpy.typing as npt

FloatImage = npt.NDArray[np.float32]


class Filters(Protocol):
    def gaussian_filter(
        self, input: FloatImage, sigma: float, *, mode: str, output: FloatImage
    ) -> FloatImage: ...


def smooth(source: FloatImage, destination: FloatImage) -> None:
    filters = cast(Filters, importlib.import_module("scipy.ndimage"))
    filters.gaussian_filter(source, sigma=1.0, mode="reflect", output=destination)
