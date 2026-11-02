"""Explicit WB host assembly. Numerical code remains behind wb_tool.api."""

import sys
from dataclasses import replace
from functools import partial
from pathlib import Path

from platform_runtime.api import ModuleRegistration, compile_workflow
from pydantic import TypeAdapter
from tool_contracts.api import (
    CoordinateFrame,
    ExecutionPlan,
    ExecutionRequest,
    ImageMetadata,
    PortTypeBinding,
    RunRecord,
    ScientificAsset,
    ScientificPort,
    ScientificType,
    TableColumn,
    TableMetadata,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowInput,
    WorkflowModule,
    WorkflowNode,
    WorkflowOutput,
    canonical_module_json,
)
from wb_tool.api import (
    AnalysisRequest,
    VerifyOriginalParameters,
    WBReportParameters,
    WBWorkflowStart,
    WorkflowInputPath,
    encode_wb_workflow_frame,
    module_identity,
    validate_wb_workflow_parameters,
    wb_report_shape,
    wb_workflow_environment,
    wb_workflow_spec,
)

from bioimage_app.wb_registration import WBWorkflowProcessCodec
from bioimage_app.workflow_environment import workflow_runtime_environment
from bioimage_app.workflow_preparation import HostInputFile, WorkflowHostModule, WorkflowLaunch

_UNIT = "mean_pixel_intensity_times_pixel"


def _environment():
    return workflow_runtime_environment(wb_workflow_environment())


def _launch(
    req: ExecutionRequest, run: RunRecord, files: tuple[HostInputFile, ...], directory: str
) -> WorkflowLaunch:
    output = str(Path(directory) / "outputs")
    start = WBWorkflowStart(
        identity=module_identity(run.run_id, req),
        request=req,
        inputs=tuple(WorkflowInputPath(port=item.binding.port, path=item.path) for item in files),
        output_directory=output,
    )
    return WorkflowLaunch(
        req,
        run,
        (sys.executable, "-I", "-m", "bioimage_app", "--worker", "wb_workflow"),
        directory,
        encode_wb_workflow_frame(start),
        output,
        WBWorkflowProcessCodec(start),
    )


def _parameters(
    module_id: str, source: ScientificAsset, report: WBReportParameters, raw: str
) -> None:
    validate_wb_workflow_parameters(module_id, raw)
    if module_id == "wb-verify-original":
        if VerifyOriginalParameters.model_validate_json(raw).image != source.description.image:
            raise ValueError("Validation parameters differ from scientific original metadata")
    elif module_id == "wb-analyze-original":
        planned = TypeAdapter(AnalysisRequest).validate_json(raw, strict=True, extra="forbid")
        if planned.source_sha256 != source.payload.sha256:
            raise ValueError("Analysis parameters belong to another source")
    elif wb_report_shape(WBReportParameters.model_validate_json(raw)) != wb_report_shape(report):
        raise ValueError("Report parameters differ from its frozen display dimensions")


def _modules(source: ScientificAsset, report: WBReportParameters) -> tuple[WorkflowHostModule, ...]:
    environment = _environment()
    image = source.description.image
    if (
        source.description.kind != "raw_image"
        or image is None
        or source.description.unit != "pixel_intensity"
    ):
        raise ValueError(
            "Original WB workflow requires an explicit integer original and intensity unit"
        )
    source_port = ScientificPort(
        name="source",
        kind="raw_image",
        quantitative=True,
        accepted_dtypes=("uint8", "uint16"),
        unit="pixel_intensity",
        frame_id=image.frame.frame_id,
        frame_origin_sha256=source.payload.sha256,
    )
    table = TableMetadata(
        row_entity="legacy_lane_band",
        columns=(
            TableColumn(name="sample_id", dtype="string", unit=None, nullable=False),
            TableColumn(name="metric", dtype="string", unit=None, nullable=False),
            TableColumn(
                name="value", dtype="float64", unit=_UNIT, nullable=True, state_column="status"
            ),
            *(
                TableColumn(name=name, dtype="string", unit=None, nullable=False)
                for name in ("status", "reason", "unit", "source_sha256")
            ),
            TableColumn(name="raw_integral_for_review", dtype="float64", unit=_UNIT, nullable=True),
        ),
        state_vocabulary="wb_legacy_band_status@1",
        states=("valid", "quality_review", "invalid", "excluded", "not_detected"),
    )
    report_image = ImageMetadata(
        dtype="uint8",
        axes=("y", "x"),
        shape=wb_report_shape(report),
        acquisition_bit_depth=None,
        acquisition_range=None,
        acquisition_range_source=None,
        frame=CoordinateFrame(
            frame_id="wb_report_canvas",
            origin_asset_sha256=source.payload.sha256,
            physical_pixel_size_yx=None,
            physical_unit=None,
        ),
    )
    manifest = ScientificType(kind="run_manifest", unit=None)
    analysis = ScientificType(kind="analysis_result", unit=_UNIT)
    declarations = (
        (
            "wb-verify-original",
            (source_port,),
            (PortTypeBinding(port="validation", description=manifest),),
        ),
        (
            "wb-analyze-original",
            (source_port, ScientificPort(name="validation", kind="run_manifest")),
            (PortTypeBinding(port="analysis", description=analysis),),
        ),
        (
            "wb-publish-original",
            (
                ScientificPort(
                    name="analysis", kind="analysis_result", quantitative=True, unit=_UNIT
                ),
            ),
            (
                PortTypeBinding(
                    port="measurements",
                    description=ScientificType(kind="typed_table", unit=_UNIT, table=table),
                ),
                PortTypeBinding(
                    port="curves",
                    description=ScientificType(kind="analysis_result", unit="pixel_intensity"),
                ),
                PortTypeBinding(
                    port="report",
                    description=ScientificType(kind="display_image", unit=None, image=report_image),
                ),
                PortTypeBinding(port="provenance", description=manifest),
            ),
        ),
    )
    modules: list[WorkflowHostModule] = []
    for module_id, inputs, outputs in declarations:
        spec = wb_workflow_spec(module_id)
        interface = WorkflowModule(module=spec, input_ports=inputs, output_ports=outputs)
        registration = ModuleRegistration(
            interface=interface,
            parameters_schema=spec.parameters_schema,
            validate_parameters=partial(_parameters, module_id, source, report),
        )
        modules.append(WorkflowHostModule(registration, environment, _launch))
    return tuple(modules)


def wb_workflow_registry(plan: ExecutionPlan) -> tuple[WorkflowHostModule, ...]:
    roots = tuple(
        item.asset for node in plan.nodes for item in node.inputs if item.asset is not None
    )
    originals = tuple(item for item in roots if item.description.kind == "raw_image")
    if not originals or any(item != originals[0] for item in originals):
        raise ValueError("This WB workflow registration requires one unambiguous original")
    reports = tuple(
        WBReportParameters.model_validate_json(node.parameters_json)
        for node in plan.nodes
        if node.interface.module.module_id == "wb-publish-original"
    )
    if not reports or any(wb_report_shape(item) != wb_report_shape(reports[0]) for item in reports):
        raise ValueError("WB report nodes need a single consistent frozen canvas declaration")
    return _modules(originals[0], reports[0])


def build_wb_workflow(
    source: ScientificAsset,
    planned: AnalysisRequest,
    *,
    workflow_id: str = "wb-original",
    revision: int = 0,
    layout: str = "comfortable",
) -> tuple[WorkflowDefinition, ExecutionPlan]:
    """Call in background: actual module/environment inspection reads installed files."""
    # Node documents are new; workflow generation never becomes their first draft revision.
    planned = replace(planned, revision=0)
    report = WBReportParameters.model_validate(
        {"layout": layout, "expected_rows": sum(len(lane.bands) for lane in planned.lanes)}
    )
    modules = _modules(source, report)
    interfaces = {
        item.registration.interface.module.module_id: item.registration.interface
        for item in modules
    }
    verify = VerifyOriginalParameters.model_validate({"image": source.description.image})
    parameters = (
        verify.model_dump_json(),
        TypeAdapter(AnalysisRequest).dump_json(planned).decode(),
        report.model_dump_json(),
    )
    definition = WorkflowDefinition(
        workflow_id=workflow_id,
        workflow_version="1.0",
        revision=revision,
        title="Original WB workflow",
        sample_id=source.sample_id,
        nodes=tuple(
            WorkflowNode(
                node_id=node_id,
                module=interfaces[module_id].module,
                parameters_json=canonical_module_json(raw),
            )
            for node_id, module_id, raw in zip(
                ("verify", "analyze", "publish"),
                ("wb-verify-original", "wb-analyze-original", "wb-publish-original"),
                parameters,
                strict=True,
            )
        ),
        inputs=(
            WorkflowInput(node_id="verify", port="source", asset=source),
            WorkflowInput(node_id="analyze", port="source", asset=source),
        ),
        edges=(
            WorkflowEdge(
                source_node="verify",
                source_port="validation",
                target_node="analyze",
                target_port="validation",
            ),
            WorkflowEdge(
                source_node="analyze",
                source_port="analysis",
                target_node="publish",
                target_port="analysis",
            ),
        ),
        outputs=tuple(
            WorkflowOutput(name=name, node_id="publish", port=name)
            for name in ("measurements", "curves", "report", "provenance")
        ),
    )
    return definition, compile_workflow(
        definition, tuple(item.registration for item in modules), modules[0].environment
    )
