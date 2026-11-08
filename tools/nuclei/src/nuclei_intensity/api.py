"""Per-instance raw detector values in the original pixel frame."""

from collections.abc import Iterator
from typing import cast

import numpy as np
from numpy.typing import NDArray


def measure_intensity(
    labels: NDArray[np.generic], pixels: NDArray[np.generic]
) -> Iterator[tuple[int, int, float, int]]:
    """Yield original instance ID, area (px²), mean (DN) and integral (DN·px)."""
    if pixels.ndim != 2 or pixels.dtype != np.uint8:
        raise ValueError("Expected original 2D uint8 target pixels")
    if labels.shape != pixels.shape or labels.dtype != np.uint32:
        raise ValueError("Expected committed uint32 labels with the target image shape")
    # Compact indices keep memory bounded even for sparse uint32 instance IDs.
    ids, indices, areas = np.unique(labels.ravel(), return_inverse=True, return_counts=True)
    totals = np.bincount(indices, weights=cast(NDArray[np.uint8], pixels).ravel())
    for index, instance_id in enumerate(ids):
        if instance_id:
            total, area = int(totals[index]), int(areas[index])
            yield int(instance_id), area, total / area, total
