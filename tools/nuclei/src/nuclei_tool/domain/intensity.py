"""Per-instance raw detector values in the original pixel frame."""

from collections.abc import Iterator
from typing import cast

import numpy as np
from numpy.typing import NDArray

from nuclei_tool.domain.labels import validate_labels, validate_pixels


def measure_intensity(
    labels: NDArray[np.generic], pixels: NDArray[np.generic]
) -> Iterator[tuple[int, int, float, int]]:
    """Yield original instance ID, area (px²), mean (DN) and integral (DN·px)."""
    validate_pixels(pixels)
    instances, _ = validate_labels(labels, pixels.shape)
    # Compact indices keep memory bounded even for sparse uint32 instance IDs.
    ids, indices, areas = np.unique(instances.ravel(), return_inverse=True, return_counts=True)
    totals = np.bincount(indices, weights=cast(NDArray[np.uint8], pixels).ravel())
    for index, instance_id in enumerate(ids):
        if instance_id:
            total, area = int(totals[index]), int(areas[index])
            yield int(instance_id), area, total / area, total
