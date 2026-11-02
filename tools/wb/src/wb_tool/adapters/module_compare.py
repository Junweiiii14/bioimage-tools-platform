"""Actually execute both WB paths and write a fresh, attributable comparison bundle."""

import csv
import hashlib
import io
import json
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from pydantic import TypeAdapter
from tool_contracts.api import AssetRef, BoundAsset, OutputManifest, canonical_module_json

from wb_tool.adapters.module_execution import execute_wb_module
from wb_tool.adapters.module_protocol import WBModuleStart
from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.analysis import (
    AnalysisCancelled,
    AnalysisError,
    AnalysisResult,
    analyze_annotations,
)
from wb_tool.application.module_execution import read_legacy_module_parameters
from wb_tool.application.worker_protocol import ResultFrame

MAX_BUNDLE_BYTES = 16 * 1024 * 1024


def _csv(rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        # Versioned, reversible literal text encoding; formulas never enter spreadsheets.
        writer.writerow(
            {key: "text:" + item if isinstance(item, str) else item for key, item in row.items()}
        )
    return stream.getvalue().encode("utf-8-sig")


def _result_bytes(result: AnalysisResult, start: WBModuleStart) -> bytes:
    validated = ResultFrame.model_validate_json(
        ResultFrame(
            protocol_version=1,
            kind="result",
            sequence=2,
            run_id=start.identity.run_id,
            attempt_id=start.request.attempt_id,
            request_id=start.request.request_id,
            result=result,
        ).model_dump_json()
    )
    return TypeAdapter(AnalysisResult).dump_json(validated.result)


def compare_wb_module(
    start: WBModuleStart, *, cancelled: Callable[[], bool] | None = None
) -> OutputManifest:
    """Return uncommitted file references only; Workspace publication is host-owned."""
    start = WBModuleStart.model_validate_json(start.model_dump_json())

    def check_cancel() -> None:
        if cancelled is not None and cancelled():
            raise AnalysisCancelled("对照已取消")

    check_cancel()
    source = Path(start.source_path)
    if source.stat().st_size != start.request.inputs[0].asset.size_bytes:
        raise AnalysisError("输入文件大小与冻结资产不一致")
    image = load_tiff(source)
    planned = read_legacy_module_parameters(start.request)
    # Two actual calls. Never populate the new result by copying the baseline table.
    baseline = analyze_annotations(image, planned, cancelled=cancelled)
    actual = execute_wb_module(image, start.request, cancelled=cancelled)
    baseline_bytes = _result_bytes(baseline, start)
    actual_bytes = _result_bytes(actual, start)
    measurements: list[dict[str, object]] = []
    differences: list[dict[str, object]] = []
    for old_lane, new_lane in zip(baseline.lanes, actual.lanes, strict=True):
        for old, new in zip(old_lane.bands, new_lane.bands, strict=True):
            check_cancel()
            common: dict[str, object] = {
                "sample_id": new_lane.roi.lane_id,
                "metric": new.annotation.band_id,
                "method": actual.algorithm_id,
                "source_asset_id": start.request.inputs[0].asset.asset_id,
                "source_sha256": image.sha256,
                "run_id": start.identity.run_id,
                "request_id": start.request.request_id,
            }
            measurements.append(
                {
                    **common,
                    "value": new.signal,
                    "status": new.status,
                    "reason": new.reason or "",
                    "unit": "mean_pixel_intensity_times_pixel",
                    "raw_integral_for_review": new.measurement.signal if new.measurement else None,
                }
            )
            comparable = old.signal is not None and new.signal is not None
            differences.append(
                {
                    **common,
                    "baseline_value": old.signal,
                    "module_value": new.signal,
                    "baseline_status": old.status,
                    "module_status": new.status,
                    "baseline_reason": old.reason or "",
                    "module_reason": new.reason or "",
                    "difference": new.signal - old.signal
                    if new.signal is not None and old.signal is not None
                    else None,
                    "numerically_comparable": comparable,
                    "exact_match": old == new and old_lane.roi == new_lane.roi,
                    "absolute_tolerance": 0,
                }
            )
    if not measurements:
        raise AnalysisError("对照至少需要一个条带，不能生成空差异表")
    matched = baseline_bytes == actual_bytes
    summary = {
        "comparison_policy": "legacy_exact@1",
        "csv_text_encoding": "text_prefix@1",
        "rows": len(measurements),
        "exact_match": matched,
        "valid_rows": sum(row["status"] == "valid" for row in measurements),
        "absolute_tolerance": 0,
    }
    payloads = {
        "measurements": _csv(measurements),
        "differences": _csv(differences),
        "analysis": actual_bytes,
        "baseline": baseline_bytes,
    }
    provenance = {
        "schema_version": 1,
        "kind": "wb_v0_comparison@1",
        "run_id": start.identity.run_id,
        "request": start.request.model_dump(mode="json"),
        "summary": summary,
        "output_sha256": {
            key: hashlib.sha256(value).hexdigest() for key, value in payloads.items()
        },
        "interpretation": "工程等价对照；旧方法不构成独立科学真值。状态非valid的value为空。",
    }
    payloads["provenance"] = json.dumps(
        provenance, ensure_ascii=False, allow_nan=False, indent=2
    ).encode("utf-8")
    if sum(map(len, payloads.values())) > MAX_BUNDLE_BYTES:
        raise AnalysisError("对照产物超过16MiB预算")
    check_cancel()
    destination = Path(start.output_directory)
    # The host supplies a fresh private staging path. Existing directories/files survive.
    destination.mkdir(parents=False, exist_ok=False)
    outputs: list[BoundAsset] = []
    for port in start.request.module.output_ports:
        check_cancel()
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
    check_cancel()
    return OutputManifest(
        run_id=start.identity.run_id,
        request=start.request,
        publication="candidate",
        outputs=tuple(outputs),
        quality="complete" if matched and summary["valid_rows"] == len(measurements) else "issues",
        summary_json=canonical_module_json(json.dumps(summary)),
    )
