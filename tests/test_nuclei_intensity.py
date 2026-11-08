from pathlib import Path

import numpy as np
import pytest
from bioimage_app.nuclei_intensity_cli import export
from nuclei_intensity.api import measure_intensity
from platform_runtime.api import Workspace


def test_sparse_ids_and_raw_values() -> None:
    labels = np.array([[2**32 - 1, 0], [4, 4]], dtype=np.uint32)
    pixels = np.array([[0, 255], [1, 254]], dtype=np.uint8)
    assert list(measure_intensity(labels, pixels)) == [(4, 2, 127.5, 255), (2**32 - 1, 1, 0.0, 0)]
    assert list(measure_intensity(np.zeros_like(labels), pixels)) == []
    with pytest.raises(ValueError, match="shape"):
        list(measure_intensity(labels, pixels[:, :1]))
    with pytest.raises(ValueError, match="uint8"):
        list(measure_intensity(labels, pixels.astype(np.uint16)))


def test_export_rejects_another_workspace_results(tmp_path: Path) -> None:
    other = tmp_path / "another-project"
    with Workspace.create(other):
        pass
    with pytest.raises(ValueError, match="outside all managed workspaces"):
        export(tmp_path / "source-project", tmp_path / "target.tif", other / "results")
    with Workspace.open(other) as reopened:
        assert not reopened.list_documents()
