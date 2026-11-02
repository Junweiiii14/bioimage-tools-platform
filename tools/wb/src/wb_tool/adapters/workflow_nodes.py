"""Three real, fixed original-value nodes. No Workspace, GUI or new WB formula."""

import csv
import hashlib
import io
import json
import os
import platform
from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import TypeAdapter
from tool_contracts.api import (
    AssetRef,
    BoundAsset,
    ExecutionRequest,
    ModulePort,
    ModuleSpec,
    OutputManifest,
    RuntimeVersion,
    canonical_module_json,
)

from wb_tool.adapters.tiff_input import LoadedTiff, load_tiff
from wb_tool.adapters.workflow_protocol import WBWorkflowStart
from wb_tool.application.analysis import (
    AnalysisCancelled,
    AnalysisRequest,
    AnalysisResult,
    analyze_annotations,
)
from wb_tool.application.worker_protocol import ResultFrame
from wb_tool.application.workflow_parameters import (
    OriginalValidation,
    VerifyOriginalParameters,
    WBReportParameters,
    validate_wb_workflow_parameters,
)

_IDS = ("wb-verify-original", "wb-analyze-original", "wb-publish-original")
_FILES = (
    "api.py",
    "adapters/workflow_nodes.py",
    "adapters/workflow_protocol.py",
    "adapters/workflow_worker.py",
    "adapters/worker.py",
    "adapters/module_protocol.py",
    "application/workflow_parameters.py",
    "adapters/tiff_input.py",
    "application/analysis.py",
    "application/worker_protocol.py",
    "domain/lanes.py",
    "domain/quantify.py",
)
_BUDGET = 16 * 1024 * 1024
_UNIT = "mean_pixel_intensity_times_pixel"


def wb_workflow_spec(module_id: str) -> ModuleSpec:
    if module_id not in _IDS:
        raise ValueError("Unregistered WB workflow module")
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256(b"wb-original-workflow-source-lf@1\0")
    for relative in _FILES:
        digest.update(relative.encode() + b"\0")
        digest.update((root / relative).read_bytes().replace(b"\r\n", b"\n") + b"\0")
    if module_id == _IDS[0]:
        inputs = (ModulePort(name="source", kind="raw_image"),)
        outputs = (ModulePort(name="validation", kind="run_manifest", filename="validation.json"),)
        schema = VerifyOriginalParameters.model_json_schema()
        method = "original_tiff_validation@1"
    elif module_id == _IDS[1]:
        inputs = (
            ModulePort(name="source", kind="raw_image"),
            ModulePort(name="validation", kind="run_manifest"),
        )
        outputs = (ModulePort(name="analysis", kind="analysis_result", filename="analysis.json"),)
        schema = TypeAdapter(AnalysisRequest).json_schema()
        method = "profile_integral@1"
    else:
        inputs = (ModulePort(name="analysis", kind="analysis_result"),)
        outputs = (
            ModulePort(name="measurements", kind="typed_table", filename="measurements.csv"),
            ModulePort(name="curves", kind="analysis_result", filename="curves.json"),
            ModulePort(name="report", kind="display_image", filename="report.png"),
            ModulePort(name="provenance", kind="run_manifest", filename="report-manifest.json"),
        )
        schema = WBReportParameters.model_json_schema()
        method = "wb_original_report@1"
    return ModuleSpec(
        module_id=module_id,
        module_version="1.0",
        method_version=method,
        implementation_digest=digest.hexdigest(),
        input_ports=inputs,
        output_ports=outputs,
        parameters_schema=canonical_module_json(json.dumps(schema)),
    )


def wb_workflow_environment() -> tuple[RuntimeVersion, ...]:
    values = {
        "python": platform.python_version(),
        "os": platform.platform(),
        "machine": platform.machine() or "unknown",
        "processor": platform.processor() or "unknown",
    }
    values.update(
        {
            name: version(name)
            for name in ("wb-tool", "tool-contracts", "numpy", "tifffile", "pydantic", "pillow")
        }
    )
    try:
        values["imagecodecs"] = version("imagecodecs")
    except PackageNotFoundError:
        values["imagecodecs"] = "not-installed"
    for name in (
        "BIOIMAGE_TIFF_MAX_PIXELS",
        "BIOIMAGE_TIFF_MAX_PEAK_BYTES",
        "BIOIMAGE_TIFF_LZMA_MAX_MEMORY_BYTES",
    ):
        values[name] = os.environ.get(name, "not-set")
    return tuple(RuntimeVersion(name=name, version=value) for name, value in sorted(values.items()))


def wb_report_shape(parameters: WBReportParameters) -> tuple[int, int]:
    shape = (140 + parameters.expected_rows * (20 if parameters.layout == "compact" else 28), 1200)
    if shape[0] > 100000 or shape[0] * shape[1] > 32_000_000:
        raise ValueError("Report exceeds the existing 32-million-pixel image budget")
    return shape


def _read(start: WBWorkflowStart, port: str, *, raw: bool = False) -> tuple[AssetRef, Path, bytes]:
    ref = next(item.asset for item in start.request.inputs if item.port == port)
    path = Path(next(item.path for item in start.inputs if item.port == port))
    if path.stat().st_size != ref.size_bytes:
        raise ValueError("Workflow input size changed")
    if not raw and ref.size_bytes > _BUDGET:
        raise ValueError("Derived workflow input exceeds the result budget")
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != ref.sha256:
            raise ValueError("Workflow input bytes changed")
    data = b"" if raw else path.read_bytes()
    if not raw and (len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256):
        raise ValueError("Workflow input changed during reading")
    return ref, path, data


def _original(
    start: WBWorkflowStart, description: VerifyOriginalParameters
) -> tuple[AssetRef, LoadedTiff]:
    ref, path, _ = _read(start, "source", raw=True)
    image = load_tiff(path)
    expected = description.image
    if (image.sha256, image.pixels.dtype.name, image.pixels.shape) != (
        ref.sha256,
        expected.dtype,
        expected.shape,
    ):
        raise ValueError("Decoded original dtype/shape/source differs from the frozen description")
    if expected.frame.origin_asset_sha256 != ref.sha256:
        raise ValueError("Original coordinate frame belongs to different bytes")
    return ref, image


def _json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()


def _validated_result(result: AnalysisResult, start: WBWorkflowStart) -> AnalysisResult:
    # Validate before JSON serialization can replace a nonfinite value with null.
    return ResultFrame(
        protocol_version=1,
        kind="result",
        sequence=2,
        run_id=start.identity.run_id,
        attempt_id=start.request.attempt_id,
        request_id=start.request.request_id,
        result=result,
    ).result


def _report(
    result: AnalysisResult, parameters: WBReportParameters, request: ExecutionRequest
) -> tuple[dict[str, bytes], Literal["complete", "issues"]]:
    # Pillow is an existing optional figures dependency; importing the base WB API stays headless.
    from PIL import Image, ImageDraw, ImageFont

    rows: list[dict[str, object]] = []
    profiles: list[dict[str, object]] = []
    for lane in result.lanes:
        profiles.append(
            {
                "lane_id": lane.roi.lane_id,
                "roi": TypeAdapter(type(lane.roi)).dump_python(lane.roi, mode="json"),
                "raw": lane.profiles.raw if lane.profiles else None,
                "quantitative": lane.profiles.quantitative if lane.profiles else None,
                "polarity": result.request.polarity,
                "x_unit": "source_pixel_y",
                "x_origin": lane.roi.y0,
                "x_step": 1,
                "y_unit": "pixel_intensity",
                "dtype_max": lane.profiles.dtype_max if lane.profiles else None,
                "reason": lane.reason,
            }
        )
        for band in lane.bands:
            rows.append(
                {
                    "sample_id": lane.roi.lane_id,
                    "metric": band.annotation.band_id,
                    "value": band.signal,
                    "status": band.status,
                    "reason": band.reason or "",
                    "unit": _UNIT,
                    "source_sha256": result.request.source_sha256,
                    "raw_integral_for_review": band.measurement.signal
                    if band.measurement
                    else None,
                }
            )
    if len(rows) != parameters.expected_rows:
        raise ValueError("Report row count differs from the frozen output description")
    height, width = wb_report_shape(parameters)
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=16)
    draw.text((24, 16), "WB original-value report / profile_integral@1", font=font, fill=0)
    draw.text((24, 44), "Values: " + _UNIT + "; no normalization or smoothing", font=font, fill=0)
    draw.text(
        (24, 70),
        "Row numbers follow measurements.csv; null is not zero. Full profiles: curves.json",
        font=font,
        fill=0,
    )
    draw.text((24, 96), "Source SHA256: " + result.request.source_sha256, font=font, fill=0)
    spacing = 20 if parameters.layout == "compact" else 28
    for index, row in enumerate(rows):
        value = "null" if row["value"] is None else str(row["value"])
        draw.text(
            (24, 124 + index * spacing),
            f"Row {index + 1}    value={value}    status={row['status']}",
            font=font,
            fill=0,
        )
    png = io.BytesIO()
    image.save(png, format="PNG")
    image.close()
    csv_stream = io.StringIO(newline="")
    writer = csv.DictWriter(csv_stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: "text:" + value if isinstance(value, str) else value
                for key, value in row.items()
            }
        )
    quality = "complete" if all(row["status"] == "valid" for row in rows) else "issues"
    return {
        "measurements": csv_stream.getvalue().encode("utf-8-sig"),
        "curves": _json(
            {
                "schema_version": 1,
                "source_sha256": result.request.source_sha256,
                "bit_depth": result.bit_depth,
                "source_conversion": result.source_conversion,
                "profiles": profiles,
                "transforms": "unchanged raw and polarity-defined profiles",
            }
        ),
        "report": png.getvalue(),
        "provenance": _json(
            {
                "schema_version": 1,
                "request": request.model_dump(mode="json"),
                "source_sha256": result.request.source_sha256,
                "rows": len(rows),
                "report_shape_yx": (height, width),
                "report_role": "display_only",
                "quality": quality,
                "scientific_admission": "not_granted",
            }
        ),
    }, quality


def execute_wb_workflow_node(
    start: WBWorkflowStart, *, cancelled: Callable[[], bool] | None = None
) -> OutputManifest:
    start = WBWorkflowStart.model_validate_json(start.model_dump_json())
    req = start.request
    if req.module != wb_workflow_spec(req.module.module_id):
        raise ValueError("Installed workflow module differs from frozen implementation")
    expected = {item.name: item.version for item in wb_workflow_environment()}
    actual = {item.name: item.version for item in req.environment}
    host_names = {"host_runtime_source", "platform-runtime", "bioimage-app", "PySide6", "shiboken6"}
    if (
        any(actual.get(name) != value for name, value in expected.items())
        or set(actual) - set(expected) != host_names
    ):
        raise ValueError("Workflow environment differs from installed dependencies/OS/CPU")
    host_digest = actual["host_runtime_source"]
    if len(host_digest) != 64 or set(host_digest) - set("0123456789abcdef"):
        raise ValueError("Host runtime source identity is not a SHA256 digest")
    validate_wb_workflow_parameters(req.module.module_id, req.parameters_json)

    def check() -> None:
        if cancelled is not None and cancelled():
            raise AnalysisCancelled("Workflow node cancelled")

    check()
    quality = "complete"
    if req.module.module_id == _IDS[0]:
        parameters = VerifyOriginalParameters.model_validate_json(req.parameters_json)
        ref, image = _original(start, parameters)
        attestation = OriginalValidation(
            source=ref, image=parameters.image, conversion=image.conversion
        )
        payloads = {"validation": attestation.model_dump_json().encode()}
    elif req.module.module_id == _IDS[1]:
        _, _, raw = _read(start, "validation")
        attestation = OriginalValidation.model_validate_json(raw)
        ref, image = _original(start, VerifyOriginalParameters(image=attestation.image))
        if attestation.source != ref or attestation.conversion != image.conversion:
            raise ValueError("Validation attestation does not bind the actual original")
        planned = TypeAdapter(AnalysisRequest).validate_json(
            req.parameters_json, strict=True, extra="forbid"
        )
        if (planned.source_sha256, planned.revision) != (ref.sha256, req.revision):
            raise ValueError("Analysis parameters do not bind the original/request document")
        result = analyze_annotations(image, planned, cancelled=cancelled)
        result = _validated_result(result, start)
        payloads = {"analysis": TypeAdapter(AnalysisResult).dump_json(result)}
        quality = (
            "complete"
            if all(band.status == "valid" for lane in result.lanes for band in lane.bands)
            else "issues"
        )
    else:
        _, _, raw = _read(start, "analysis")
        result = TypeAdapter(AnalysisResult).validate_json(raw, strict=True, extra="forbid")
        result = _validated_result(result, start)
        if (
            result.request.revision,
            result.request.geometry_policy,
            result.request.quant_policy,
        ) != (
            0,
            "fixed_grid@1",
            "legacy_bounds@1",
        ):
            raise ValueError("Original-value report rejects a different analysis policy")
        payloads, quality = _report(
            result, WBReportParameters.model_validate_json(req.parameters_json), req
        )
    check()
    if sum(map(len, payloads.values())) > _BUDGET:
        raise ValueError("Workflow node outputs exceed the unchanged 16MiB result budget")
    destination = Path(start.output_directory)
    destination.mkdir(parents=False, exist_ok=False)
    outputs: list[BoundAsset] = []
    for port in req.module.output_ports:
        check()
        data = payloads[port.name]
        with (destination / port.filename).open("xb") as stream:
            stream.write(data)
        outputs.append(
            BoundAsset(
                port=port.name,
                kind=port.kind,
                asset=AssetRef(
                    asset_id=uuid4().hex,
                    relative_path=port.filename,
                    sha256=hashlib.sha256(data).hexdigest(),
                    size_bytes=len(data),
                ),
            )
        )
    check()
    return OutputManifest(
        run_id=start.identity.run_id,
        request=req,
        publication="candidate",
        outputs=tuple(outputs),
        quality=quality,
        summary_json=canonical_module_json(
            json.dumps(
                {
                    "module": req.module.module_id,
                    "quality": quality,
                    "scientific_admission": "not_granted",
                }
            )
        ),
    )
