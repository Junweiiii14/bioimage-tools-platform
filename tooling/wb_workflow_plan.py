"""Freeze a real P002 public-module consumer; this command does not execute a graph."""

import argparse
import hashlib
import json
from pathlib import Path

from platform_runtime.api import (
    ModuleRegistration,
    compile_workflow,
    execution_plan_digest,
    load_execution_plan,
    load_workflow_definition,
    verify_execution_plan,
    workflow_definition_json,
)
from pydantic import TypeAdapter
from tool_contracts.api import (
    AssetRef,
    CoordinateFrame,
    ImageMetadata,
    PortTypeBinding,
    ScientificAsset,
    ScientificPort,
    ScientificType,
    TableColumn,
    TableMetadata,
    WorkflowDefinition,
    WorkflowInput,
    WorkflowModule,
    WorkflowNode,
    WorkflowOutput,
)
from wb_tool.api import (
    AnalysisRequest,
    load_tiff,
    prepare_wb_execution,
    wb_module_environment,
    wb_module_spec,
    wb_validation_input,
)

UNIT = "mean_pixel_intensity_times_pixel"


def legacy_table_metadata(*, differences: bool) -> TableMetadata:
    common = [
        TableColumn(name=name, dtype="string", unit=None, nullable=False)
        for name in (
            "sample_id",
            "metric",
            "method",
            "source_asset_id",
            "source_sha256",
            "run_id",
            "request_id",
        )
    ]
    if differences:
        extra = [
            TableColumn(
                name="baseline_value",
                dtype="float64",
                unit=UNIT,
                nullable=True,
                state_column="baseline_status",
            ),
            TableColumn(
                name="module_value",
                dtype="float64",
                unit=UNIT,
                nullable=True,
                state_column="module_status",
            ),
            *(
                TableColumn(name=name, dtype="string", unit=None, nullable=False)
                for name in ("baseline_status", "module_status", "baseline_reason", "module_reason")
            ),
            TableColumn(name="difference", dtype="float64", unit=UNIT, nullable=True),
            TableColumn(name="numerically_comparable", dtype="bool", unit=None, nullable=False),
            TableColumn(name="exact_match", dtype="bool", unit=None, nullable=False),
            TableColumn(name="absolute_tolerance", dtype="float64", unit=UNIT, nullable=False),
        ]
    else:
        extra = [
            TableColumn(
                name="value", dtype="float64", unit=UNIT, nullable=True, state_column="status"
            ),
            *(
                TableColumn(name=name, dtype="string", unit=None, nullable=False)
                for name in ("status", "reason", "unit")
            ),
            TableColumn(name="raw_integral_for_review", dtype="float64", unit=UNIT, nullable=True),
        ]
    return TableMetadata(
        row_entity="legacy_lane_band",
        columns=tuple(common + extra),
        state_vocabulary="wb_legacy_band_status@1",
        states=("valid", "quality_review", "invalid", "excluded", "not_detected"),
    )


def wb_plan_registration(source: ScientificAsset) -> ModuleRegistration:
    """Host-owned sample binding uses the real public P002 validator, not a mock schema."""
    spec = wb_module_spec()
    image = source.description.image
    if image is None or source.description.kind != "raw_image":
        raise ValueError("Legacy WB plan requires an original integer scientific image")
    interface = WorkflowModule(
        module=spec,
        input_ports=(
            ScientificPort(
                name="source",
                kind="raw_image",
                quantitative=True,
                accepted_dtypes=("uint8", "uint16"),
                unit="detector_count",
                frame_id=image.frame.frame_id,
                frame_origin_sha256=source.payload.sha256,
            ),
        ),
        output_ports=tuple(
            PortTypeBinding(
                port=p.name,
                description=ScientificType(
                    kind=p.kind,
                    unit=UNIT if p.kind == "typed_table" else None,
                    table=legacy_table_metadata(differences=p.name == "differences")
                    if p.kind == "typed_table"
                    else None,
                ),
            )
            for p in spec.output_ports
        ),
    )

    def validate(raw: str) -> None:
        planned = TypeAdapter(AnalysisRequest).validate_json(raw, strict=True, extra="forbid")
        prepare_wb_execution(source.payload, planned, "workflow-contract")

    return ModuleRegistration(
        interface=interface, parameters_schema=spec.parameters_schema, validate_parameters=validate
    )


def freeze_wb_plan(output: Path) -> dict[str, object]:
    fixture = wb_validation_input("triangle_u16")
    output.mkdir(parents=True, exist_ok=False)
    path = output / "source.tif"
    path.write_bytes(fixture.source_bytes)
    image = load_tiff(path)
    dtype = "uint8" if str(image.pixels.dtype) == "uint8" else "uint16"
    source = ScientificAsset(
        payload=AssetRef(
            asset_id="triangle_source",
            relative_path="source.tif",
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            size_bytes=path.stat().st_size,
        ),
        sample_id="synthetic_triangle",
        producing_method=None,
        parameters_sha256=None,
        description=ScientificType(
            kind="raw_image",
            unit="detector_count",
            image=ImageMetadata(
                dtype=dtype,
                axes=("y", "x"),
                shape=(int(image.pixels.shape[0]), int(image.pixels.shape[1])),
                acquisition_bit_depth=None,
                acquisition_range=None,
                acquisition_range_source=None,
                frame=CoordinateFrame(
                    frame_id="triangle_pixels",
                    origin_asset_sha256=image.sha256,
                    physical_pixel_size_yx=None,
                    physical_unit=None,
                ),
            ),
        ),
    )
    request = prepare_wb_execution(source.payload, fixture.request, "workflow-contract")
    registration = wb_plan_registration(source)
    definition = WorkflowDefinition(
        workflow_id="legacy_wb_contract",
        workflow_version="1.0",
        revision=0,
        title="旧WB工程契约示例",
        sample_id=source.sample_id,
        nodes=(
            WorkflowNode(
                node_id="analysis", module=request.module, parameters_json=request.parameters_json
            ),
        ),
        inputs=(WorkflowInput(node_id="analysis", port="source", asset=source),),
        outputs=tuple(
            WorkflowOutput(name=p.name, node_id="analysis", port=p.name)
            for p in request.module.output_ports
        ),
    )
    raw = workflow_definition_json(definition)
    (output / "workflow.json").write_text(raw, encoding="utf-8", newline="\n")
    restored = load_workflow_definition((output / "workflow.json").read_text(encoding="utf-8"))
    plan = compile_workflow(restored, (registration,), wb_module_environment())
    verify_execution_plan(plan, (registration,))
    (output / "execution-plan.json").write_text(
        plan.model_dump_json(), encoding="utf-8", newline="\n"
    )
    if (
        load_execution_plan(
            (output / "execution-plan.json").read_text(encoding="utf-8"), (registration,)
        )
        != plan
    ):
        raise ValueError("Saved execution plan did not reopen identically")
    report: dict[str, object] = {
        "schema_version": 1,
        "scope": "P007 contract/preflight only; execution and UI not implemented here",
        "source_sha256": source.payload.sha256,
        "module": request.module.model_dump(mode="json"),
        "plan_sha256": execution_plan_digest(plan),
        "node_key": plan.nodes[0].computation_key,
        "definition_roundtrip_equal": restored == definition,
        "scientific_admission": "not_granted",
        "acquisition_bit_depth": None,
        "physical_calibration": None,
    }
    (output / "receipt.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = freeze_wb_plan(args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "scope": report["scope"],
                "plan_sha256": report["plan_sha256"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
