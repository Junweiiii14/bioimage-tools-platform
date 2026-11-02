"""Original-image workspace setup shared by CLI and background desktop preparation."""

from pathlib import Path
from tempfile import TemporaryDirectory

from platform_runtime.api import Workspace, load_workflow_ledger
from pydantic import TypeAdapter
from tool_contracts.api import (
    CoordinateFrame,
    ExecutionPlan,
    ImageMetadata,
    ScientificAsset,
    ScientificType,
)
from wb_tool.api import (
    AnalysisRequest,
    WBReportParameters,
    load_tiff,
    read_wb_module_input,
    wb_validation_input,
)

from bioimage_app.wb_workflow_host import build_wb_workflow


def prepare_wb_workspace(
    workspace: Path,
    *,
    source_path: str = "",
    parameters: str = "",
    validation: str = "",
    rerun: str = "",
    layout: str = "",
) -> ExecutionPlan:
    if rerun:
        with Workspace.open(workspace) as store:
            previous = load_workflow_ledger(
                store.read_asset(store.load_draft(rerun).asset).decode()
            )
            source = next(
                item.asset
                for node in previous.plan.nodes
                for item in node.inputs
                if item.asset is not None
            )
            analysis_node = next(
                node
                for node in previous.plan.nodes
                if node.interface.module.module_id == "wb-analyze-original"
            )
            report_node = next(
                node
                for node in previous.plan.nodes
                if node.interface.module.module_id == "wb-publish-original"
            )
            planned = (
                read_wb_module_input(str(store.asset_path(source.payload)), parameters).request
                if parameters
                else TypeAdapter(AnalysisRequest).validate_json(
                    analysis_node.parameters_json, strict=True
                )
            )
            layout = (
                layout or WBReportParameters.model_validate_json(report_node.parameters_json).layout
            )
            _, plan = build_wb_workflow(
                source,
                planned,
                workflow_id=previous.plan.workflow_id,
                revision=previous.plan.revision + 1,
                layout=layout,
            )
    else:
        supplied = (
            read_wb_module_input(source_path, parameters)
            if source_path
            else wb_validation_input(validation)
        )
        with (
            Workspace.create(workspace) as store,
            TemporaryDirectory(prefix="bioimage-workflow-input-") as temporary,
        ):
            if supplied.source_bytes:
                input_path = Path(temporary) / "original.tif"
                input_path.write_bytes(supplied.source_bytes)
            else:
                input_path = Path(supplied.source_path)
            ref = store.import_asset(input_path, supplied.request.source_sha256)
            image = load_tiff(store.asset_path(ref))
            metadata = ImageMetadata(
                dtype="uint16" if image.pixels.dtype.itemsize == 2 else "uint8",
                axes=("y", "x"),
                shape=image.pixels.shape,
                acquisition_bit_depth=None,
                acquisition_range=None,
                acquisition_range_source=None,
                frame=CoordinateFrame(
                    frame_id="original_pixels",
                    origin_asset_sha256=ref.sha256,
                    physical_pixel_size_yx=None,
                    physical_unit=None,
                ),
            )
            source = ScientificAsset(
                payload=ref,
                sample_id="sample",
                producing_method=None,
                parameters_sha256=None,
                description=ScientificType(
                    kind="raw_image", unit="pixel_intensity", image=metadata
                ),
            )
            _, plan = build_wb_workflow(source, supplied.request, layout=layout or "comfortable")
    return plan
