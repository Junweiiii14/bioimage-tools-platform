"""Prepare immutable candidate files; publication belongs to the existing host."""

import csv
import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

from tool_contracts.api import AssetRef, BoundAsset, OutputManifest, canonical_module_json

from bca_tool.adapters.input import read_plate
from bca_tool.adapters.protocol import BcaStart
from bca_tool.adapters.registration import bca_module_spec, research_environment
from bca_tool.domain.plate import METHOD, analyze_plate


class BcaCancelled(Exception):
    pass


def execute(start: BcaStart, cancelled: Callable[[], bool]) -> OutputManifest:
    request = start.request
    if request.module != bca_module_spec() or request.parameters_json != "{}":
        raise ValueError("implementation_mismatch: fixed method or parameters differ")
    environment = {v.name: v.version for v in request.environment}
    if any(environment.get(v.name) != v.version for v in research_environment()):
        raise ValueError("environment_mismatch: frozen runtime differs")
    plate = read_plate(start.source_path, start.record_path)
    supplied = {"source": plate.csv_bytes, "record": plate.record_bytes}
    if {b.port for b in request.inputs} != set(supplied):
        raise ValueError("input_mismatch: expected source and record")
    for binding in request.inputs:
        raw = supplied[binding.port]
        if (
            hashlib.sha256(raw).hexdigest() != binding.asset.sha256
            or len(raw) != binding.asset.size_bytes
        ):
            raise ValueError("input_mismatch: bytes differ from frozen input")
    output = Path(start.output_directory)
    if output.exists() or output.is_symlink():
        raise ValueError("output_exists: candidate directory must be new")
    if cancelled():
        raise BcaCancelled()
    result = analyze_plate(plate.wells)
    output.mkdir()
    rows: list[dict[str, object]] = []
    for well in result.wells:
        row: dict[str, object] = dict(asdict(well.source))
        row.update({k: v for k, v in asdict(well).items() if k != "source"})
        rows.append(row)
    for name, data in (("wells", rows), ("samples", [dict(asdict(s)) for s in result.samples])):
        for row in data:
            row.update(method_id=METHOD, api_version="0.1.0")
        with (output / f"{name}.csv").open("x", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    provenance = {
        "schema_version": 1,
        "method_id": METHOD,
        "api_version": "0.1.0",
        "readiness": "research_not_scientifically_admitted",
        "lod": None,
        "loq": None,
        "limitations": (
            "synthetic/software verification only; "
            "chemistry, real plate and user validation unknown"
        ),
        "record": json.loads(plate.record.model_dump_json()),
        "record_sha256": hashlib.sha256(plate.record_bytes).hexdigest(),
        "request": json.loads(request.model_dump_json()),
    }
    with (output / "provenance.json").open("x", encoding="utf-8") as stream:
        stream.write(canonical_module_json(json.dumps(provenance)))
    if cancelled():
        raise BcaCancelled()
    outputs: list[BoundAsset] = []
    for port in request.module.output_ports:
        assert port.filename is not None
        raw = (output / port.filename).read_bytes()
        outputs.append(
            BoundAsset(
                port=port.name,
                kind=port.kind,
                asset=AssetRef(
                    asset_id=port.name,
                    relative_path=port.filename,
                    sha256=hashlib.sha256(raw).hexdigest(),
                    size_bytes=len(raw),
                ),
            )
        )
    return OutputManifest(
        run_id=start.identity.run_id,
        request=request,
        publication="candidate",
        outputs=tuple(outputs),
        quality="issues" if any(s.status == "partial" for s in result.samples) else "complete",
        summary_json=canonical_module_json(
            json.dumps(
                {
                    "readiness": "research_not_scientifically_admitted",
                    "samples": len(result.samples),
                    "partial_samples": sum(s.status == "partial" for s in result.samples),
                }
            )
        ),
    )
