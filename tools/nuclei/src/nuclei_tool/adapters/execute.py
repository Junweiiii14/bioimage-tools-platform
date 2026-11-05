"""Create candidate artifacts; only the existing host may commit publication."""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import numpy as np
from tool_contracts.api import AssetRef, BoundAsset, OutputManifest, canonical_module_json

from nuclei_tool.adapters.inference import check_cancelled, predict
from nuclei_tool.adapters.input import read_nuclei_input
from nuclei_tool.adapters.protocol import NucleiStart
from nuclei_tool.adapters.registration import nuclei_module_spec, research_environment
from nuclei_tool.application.contracts import NucleiParameters
from nuclei_tool.domain.labels import validate_labels
from nuclei_tool.domain.method import method_description


def execute(start: NucleiStart, cancelled: Callable[[], bool]) -> OutputManifest:
    request = start.request
    if request.module != nuclei_module_spec():
        raise ValueError("implementation_mismatch: worker differs from frozen module")
    environment = {item.name: item.version for item in request.environment}
    if any(environment.get(item.name) != item.version for item in research_environment()):
        raise ValueError("environment_mismatch: request differs from fixed research runtime")
    parameters = NucleiParameters.model_validate_json(request.parameters_json)
    source = read_nuclei_input(start.source_path)
    binding = request.inputs[0]
    if (
        source.sha256 != parameters.source_sha256
        or source.sha256 != binding.asset.sha256
        or source.size_bytes != binding.asset.size_bytes
        or source.pixels.shape != parameters.shape_yx
    ):
        raise ValueError("input_mismatch: bytes or shape differ from frozen request")
    output = Path(start.output_directory)
    # A new directory is required even for failed attempts; never reuse old results.
    if output.exists() or output.is_symlink():
        raise ValueError("output_exists: candidate directory must be new")
    check_cancelled(cancelled)
    labels, count = validate_labels(
        predict(source.pixels, start.model_directory, cancelled, str(output.parent)),
        parameters.shape_yx,
    )
    check_cancelled(cancelled)
    output.mkdir()
    label_path = output / "labels.npy"
    with label_path.open("xb") as stream:
        np.save(stream, labels, allow_pickle=False)
    provenance = {
        "schema_version": 1,
        "state": "valid",
        "nuclei_count": count,
        "method": method_description(),
        "input_sha256": source.sha256,
        "input_size_bytes": source.size_bytes,
        "shape_yx": list(parameters.shape_yx),
        "label_dtype": "uint32",
        "background_label": 0,
        "coordinates": "original_pixels",
        "physical_calibration": None,
        "label_sha256": hashlib.sha256(label_path.read_bytes()).hexdigest(),
        "request": json.loads(request.model_dump_json()),
    }
    raw = canonical_module_json(json.dumps(provenance))
    with (output / "provenance.json").open("xb") as stream:
        stream.write(raw.encode("utf-8"))
    check_cancelled(cancelled)
    outputs: list[BoundAsset] = []
    for port in request.module.output_ports:
        assert port.filename is not None
        path = output / port.filename
        data = path.read_bytes()
        outputs.append(
            BoundAsset(
                port=port.name,
                kind=port.kind,
                asset=AssetRef(
                    asset_id=port.name,
                    relative_path=port.filename,
                    sha256=hashlib.sha256(data).hexdigest(),
                    size_bytes=len(data),
                ),
            )
        )
    return OutputManifest(
        run_id=start.identity.run_id,
        request=request,
        publication="candidate",
        outputs=tuple(outputs),
        quality="complete",
        summary_json=canonical_module_json(
            json.dumps(
                {
                    "state": "valid",
                    "nuclei_count": count,
                    "readiness": "research_not_scientifically_admitted",
                }
            )
        ),
    )
