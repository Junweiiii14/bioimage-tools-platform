"""Validate existing model output without implementing segmentation."""

from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from nuclei_tool.domain.method import MAX_PIXELS


def validate_pixels(pixels: NDArray[np.generic]) -> None:
    if pixels.ndim != 2 or pixels.dtype != np.uint8:
        raise ValueError("unsupported_input: expected two-dimensional single-channel uint8")
    if not 1 <= pixels.size <= MAX_PIXELS:
        raise ValueError("input_budget: image must contain 1..2000000 pixels")


def validate_labels(
    labels: NDArray[np.generic], shape: tuple[int, int]
) -> tuple[NDArray[np.uint32], int]:
    if labels.shape != shape or not np.issubdtype(labels.dtype, np.integer):
        raise ValueError("invalid_labels: integer labels must use the original image shape")
    # Runtime dtype check above narrows NumPy's generic array to integral scalars.
    integers = cast(NDArray[np.integer[Any]], labels)
    if int(integers.min()) < 0 or int(integers.max()) > np.iinfo(np.uint32).max:
        raise ValueError("invalid_labels: negative or overflowing instance IDs")
    count = int(np.count_nonzero(np.unique(labels)))
    return labels.astype(np.uint32, copy=True), count
