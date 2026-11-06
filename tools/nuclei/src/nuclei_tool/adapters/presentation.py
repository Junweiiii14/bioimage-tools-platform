"""Display-only original-coordinate outlines from verified, committed result bytes."""

import hashlib
import io
import json
from dataclasses import dataclass
from typing import cast

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from tool_contracts.api import ExecutionRequest

from nuclei_tool.adapters.input import NucleiInput
from nuclei_tool.application.contracts import NucleiParameters
from nuclei_tool.domain.labels import validate_labels


@dataclass(frozen=True)
class NucleiDisplay:
    count: int
    original_png: bytes
    overlay_png: bytes


def original_png(source: NucleiInput) -> bytes:
    output = io.BytesIO()
    Image.fromarray(source.pixels).save(output, format="PNG")
    return output.getvalue()


def present_nuclei_result(
    source: NucleiInput, labels_bytes: bytes, provenance_bytes: bytes, request: ExecutionRequest
) -> NucleiDisplay:
    """Does not run a model or alter analysis pixels; caller verifies storage publication."""
    parameters = NucleiParameters.model_validate_json(request.parameters_json)
    if (
        request.module.module_id != "nuclei-stardist-research"
        or source.sha256 != parameters.source_sha256
        or source.pixels.shape != parameters.shape_yx
        or len(request.inputs) != 1
        or request.inputs[0].asset.sha256 != source.sha256
        or request.inputs[0].asset.size_bytes != source.size_bytes
    ):
        raise ValueError("Result does not belong to this original image")
    loaded: object = np.load(io.BytesIO(labels_bytes), allow_pickle=False)
    if not isinstance(loaded, np.ndarray):
        raise ValueError("Expected the original uint32 instance labels")
    array = cast(NDArray[np.generic], loaded)
    if array.dtype != np.uint32:
        raise ValueError("Expected the original uint32 instance labels")
    labels, count = validate_labels(array, parameters.shape_yx)
    raw: object = json.loads(provenance_bytes)
    if not isinstance(raw, dict):
        raise ValueError("Invalid nuclei provenance")
    provenance = cast(dict[str, object], raw)
    expected: dict[str, object] = {
        "schema_version": 1,
        "state": "valid",
        "nuclei_count": count,
        "input_sha256": source.sha256,
        "input_size_bytes": source.size_bytes,
        "shape_yx": list(parameters.shape_yx),
        "label_dtype": "uint32",
        "background_label": 0,
        "coordinates": "original_pixels",
        "label_sha256": hashlib.sha256(labels_bytes).hexdigest(),
        "request": json.loads(request.model_dump_json()),
    }
    if any(provenance.get(key) != value for key, value in expected.items()):
        raise ValueError("Nuclei provenance differs from the committed labels or request")
    # Outline pixels belong to their original instance. This RGB raster is display only.
    edge = np.zeros(labels.shape, dtype=np.bool_)
    edge[1:, :] |= labels[1:, :] != labels[:-1, :]
    edge[:-1, :] |= labels[:-1, :] != labels[1:, :]
    edge[:, 1:] |= labels[:, 1:] != labels[:, :-1]
    edge[:, :-1] |= labels[:, :-1] != labels[:, 1:]
    edge[0, :] = edge[-1, :] = True
    edge[:, 0] = edge[:, -1] = True
    edge &= labels != 0
    rgb = np.repeat(source.pixels[:, :, None], 3, axis=2)
    rgb[edge] = (215, 237, 130)
    output = io.BytesIO()
    Image.fromarray(rgb).save(output, format="PNG")
    return NucleiDisplay(count, original_png(source), output.getvalue())
