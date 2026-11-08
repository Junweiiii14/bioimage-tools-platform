import numpy as np
import pytest
from nuclei_tool.api import measure_intensity


def test_sparse_ids_and_raw_values() -> None:
    labels = np.array([[2**32 - 1, 0], [4, 4]], dtype=np.uint32)
    pixels = np.array([[0, 255], [1, 254]], dtype=np.uint8)
    assert list(measure_intensity(labels, pixels)) == [(4, 2, 127.5, 255), (2**32 - 1, 1, 0.0, 0)]
    assert list(measure_intensity(np.zeros_like(labels), pixels)) == []
    with pytest.raises(ValueError, match="shape"):
        list(measure_intensity(labels, pixels[:, :1]))
    with pytest.raises(ValueError, match="uint8"):
        list(measure_intensity(labels, pixels.astype(np.uint16)))
