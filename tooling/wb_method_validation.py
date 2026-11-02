"""Run the frozen P001 analytical references through the real public WB use case."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Literal, cast

from platform_runtime.api import evaluate_method, method_plan_digest
from pydantic import TypeAdapter
from tool_contracts.api import (
    AssetRef,
    ExecutionRequest,
    MeasurementState,
    MethodEvaluationEvidence,
    MethodEvaluationPlan,
    MethodEvaluationReport,
    MethodObservation,
    MethodReadinessRecord,
    ValidationCase,
    ValidationDataRecord,
    canonical_module_json,
)
from wb_tool.api import (
    execute_wb_module,
    load_tiff,
    prepare_wb_execution,
    wb_module_environment,
    wb_module_spec,
    wb_validation_input,
)

ROOT = Path(__file__).resolve().parents[1]
UNIT = "mean_pixel_intensity_times_pixel"


def _json_object(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    if len(raw) > 1024 * 1024:
        raise ValueError("Validation reference exceeds 1MiB")
    return cast(dict[str, object], json.loads(canonical_module_json(raw.decode("utf-8-sig"))))


def catalog_evidence(path: Path) -> tuple[ValidationDataRecord, ...]:
    """Preserve each source's full statements without inventing downloaded files."""
    catalog = _json_object(path)
    records = TypeAdapter(list[dict[str, object]]).validate_python(catalog["records"])
    result: list[ValidationDataRecord] = []
    for index, row in enumerate(records):
        result.append(
            ValidationDataRecord(
                record_id=f"catalog_{index + 1}",
                dataset_id=str(row["dataset_id"]),
                partition="unassigned",
                evidence_kind="catalog_reference",
                file_status="not_verified",
                decode_status="not_verified",
                license_use_status="unknown",
                license_and_use=str(row.get("license", "unknown")),
                source_record_json=canonical_module_json(json.dumps(row, ensure_ascii=False)),
            )
        )
    return tuple(result)


def run_wb_validation(
    output: Path,
    *,
    catalog_path: Path = ROOT / "work/evidence/B-007/public-development-data.json",
    design_path: Path = ROOT / "work/evidence/P-001/frozen-case-design.json",
    intended_use: Literal["engineering", "scientific"] = "engineering",
) -> MethodEvaluationReport:
    """Write the plan before computing; create a fresh diagnostic folder only."""
    design = _json_object(design_path)
    cases = TypeAdapter(list[dict[str, object]]).validate_python(design["cases"])
    if not 1 <= len(cases) <= 128:
        raise ValueError("Validation requires 1–128 frozen cases")
    if float(cast(float, design["absolute_tolerance"])) != 0:
        raise ValueError("This analytical reference runner only admits frozen exact tolerance")
    references = catalog_evidence(catalog_path)
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / "inputs"
    inputs.mkdir()
    (output / "source-catalog.json").write_text(
        json.dumps(
            {
                "source_sha256": sha256(catalog_path.read_bytes()).hexdigest(),
                "scope": "Catalog citations only; local source payloads not inspected here",
                "records": [x.model_dump(mode="json") for x in references],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    records: list[ValidationDataRecord] = []
    validation_cases: list[ValidationCase] = []
    requests: list[tuple[str, Path, ExecutionRequest]] = []
    spec, environment = wb_module_spec(), wb_module_environment()
    if design["method"] != spec.method_version or design["geometry_policy"] != "fixed_grid@1":
        raise ValueError("Frozen method identity does not match the analytical runner")
    for row in cases:
        name = str(row["name"])
        fixture = wb_validation_input(name)
        if not fixture.source_bytes:
            raise ValueError("Analytical fixture has no original bytes")
        data = fixture.source_bytes
        path = inputs / f"{name}.tif"
        path.write_bytes(data)
        source_digest = sha256(data).hexdigest()
        decoded = load_tiff(path)
        profile = TypeAdapter(list[int]).validate_python(row["profile"])
        width = TypeAdapter(int).validate_python(design["pixel_width"])
        roi = fixture.request.lanes[0].roi
        if (
            decoded.pixels.tolist() != [[value] * width for value in profile]
            or str(decoded.pixels.dtype) != row["dtype"]
            or [roi.x0, roi.y0, roi.x1, roi.y1] != row["roi"]
        ):
            raise ValueError("Generated fixture differs from the frozen source definition")
        asset = AssetRef(
            asset_id=name,
            relative_path=f"inputs/{name}.tif",
            sha256=source_digest,
            size_bytes=len(data),
        )
        request = prepare_wb_execution(asset, fixture.request, "method-validation")
        if request.module != spec or request.environment != environment:
            raise ValueError("Method or environment changed while freezing the evaluation")
        requests.append((name, path, request))
        records.append(
            ValidationDataRecord(
                record_id=name,
                dataset_id="P001-analytical-reference@1",
                source_groups=("synthetic_flat" if name == "flat_zero" else "synthetic_triangles",),
                partition="development",
                evidence_kind="synthetic_analytic",
                payload_sha256=source_digest,
                file_status="verified_local",
                decode_status="decoded",
                license_use_status="allowed",
                license_and_use="Self-generated arithmetic fixture; no external image",
                sample_relation="synthetic; no biological replicate inference",
                unit=UNIT,
                source_record_json=canonical_module_json(json.dumps(row, ensure_ascii=False)),
            )
        )
        validation_cases.append(
            ValidationCase(
                case_id=name,
                record_id=name,
                metric_id="signal",
                unit=UNIT,
                parameters_sha256=request.parameters_sha256,
                expected_status=TypeAdapter(MeasurementState).validate_python(
                    row["expected_status"]
                ),
                expected_value=TypeAdapter(float | None).validate_python(row["expected_signal"]),
                absolute_tolerance=0.0,
                reference_source=str(design["expectation_source"]),
            )
        )
    plan = MethodEvaluationPlan(
        evaluation_id="legacy_analytic_v1",
        intended_use=intended_use,
        module=spec,
        environment=environment,
        records=tuple(records),
        cases=tuple(validation_cases),
    )
    (output / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    observations: list[MethodObservation] = []
    for name, path, request in requests:
        image = load_tiff(path)
        result = execute_wb_module(image, request)
        band = result.lanes[0].bands[0]
        observations.append(
            MethodObservation(
                case_id=name,
                payload_sha256=image.sha256,
                parameters_sha256=request.parameters_sha256,
                unit=UNIT,
                status=band.status,
                value=band.signal if band.status == "valid" else None,
            )
        )
        (output / f"{name}-actual.json").write_text(
            TypeAdapter(type(result)).dump_json(result, indent=2).decode("utf-8"), encoding="utf-8"
        )
        if sha256(path.read_bytes()).hexdigest() != image.sha256:
            raise ValueError("Original fixture changed during evaluation")
    evidence = MethodEvaluationEvidence(
        plan_sha256=method_plan_digest(plan),
        module=wb_module_spec(),
        environment=wb_module_environment(),
        observations=tuple(observations),
    )
    report = evaluate_method(plan, evidence)
    (output / "observations.json").write_text(evidence.model_dump_json(indent=2), encoding="utf-8")
    (output / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    readiness = (
        MethodReadinessRecord(
            record_id="legacy_wb_reference",
            method_id=spec.module_id,
            method_version=spec.method_version,
            module_id=spec.module_id,
            implementation_digest=spec.implementation_digest,
            supported_inputs=(
                "uint8/uint16 TIFF; explicit original-frame ROI; light/dark polarity",
            ),
            responsible_role="independent method owner",
            design_readiness="ready" if report.engineering_passed else "pending",
            engineering_report_sha256=sha256((output / "report.json").read_bytes()).hexdigest(),
            remaining_evidence=("independent heldout data", "owner-approved scientific criteria"),
        ),
        MethodReadinessRecord(
            record_id="wb_geometry_candidate",
            method_id="WB automatic geometry candidate",
            method_version=None,
            module_id=None,
            implementation_digest=None,
            supported_inputs=("analysis-image/valid-mask contract pending P004",),
            responsible_role="independent method owner",
            design_readiness="pending",
            engineering_report_sha256=None,
            remaining_evidence=(
                "versioned angle/resampling method implementation",
                "independent geometric and intensity reference",
                "owner-approved tolerances and representative heldout data",
            ),
        ),
    )
    (output / "method-register.json").write_text(
        json.dumps([x.model_dump(mode="json") for x in readiness], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scientific", action="store_true")
    args = parser.parse_args()
    report = run_wb_validation(
        args.output, intended_use="scientific" if args.scientific else "engineering"
    )
    print(report.model_dump_json(indent=2))
    return 0 if report.requested_use_allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
