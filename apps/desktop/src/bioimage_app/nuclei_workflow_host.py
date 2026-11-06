"""Explicit opt-in research tool assembly on the existing workflow host."""

from functools import partial
from pathlib import Path

from nuclei_tool.api import (
    NucleiConversation,
    NucleiParameters,
    NucleiStart,
    encode_frame,
    execution_identity,
    nuclei_module_spec,
    research_environment,
)
from platform_runtime.api import ModuleRegistration, compile_workflow
from tool_contracts.api import (
    ExecutionPlan,
    ExecutionRequest,
    PortTypeBinding,
    RunRecord,
    ScientificAsset,
    ScientificPort,
    ScientificType,
    WorkflowDefinition,
    WorkflowInput,
    WorkflowModule,
    WorkflowNode,
    WorkflowOutput,
)

from bioimage_app.process import ProcessEvent
from bioimage_app.workflow_environment import workflow_runtime_environment
from bioimage_app.workflow_preparation import HostInputFile, WorkflowHostModule, WorkflowLaunch


class NucleiProcessCodec:
    def __init__(self, start: NucleiStart) -> None:
        self.conversation = NucleiConversation(start)

    def accept(self, data: bytes) -> ProcessEvent:
        event = self.conversation.accept(data)
        payload = event.manifest.model_dump_json().encode() if event.manifest else b""
        return ProcessEvent(event.kind, payload, event.reason, "module_manifest", event)

    def cancellation(self) -> bytes:
        return self.conversation.cancellation()


class NucleiHost:
    """Trusted launch paths are explicit host configuration, never workspace code."""

    def __init__(self, worker_python: str, model_directory: str) -> None:
        # Resolving a venv's Python symlink would silently launch its base interpreter.
        self.worker_python = str(Path(worker_python).absolute())
        self.model_directory = str(Path(model_directory).absolute())
        if not Path(self.worker_python).is_file():
            raise ValueError("Worker Python must be an explicitly prepared executable")

    def launch(
        self,
        request: ExecutionRequest,
        run: RunRecord,
        files: tuple[HostInputFile, ...],
        directory: str,
    ) -> WorkflowLaunch:
        if len(files) != 1 or files[0].binding.port != "source":
            raise ValueError("Nuclei worker requires exactly one source")
        output = str(Path(directory) / "outputs")
        start = NucleiStart(
            identity=execution_identity(run.run_id, request),
            request=request,
            source_path=files[0].path,
            model_directory=self.model_directory,
            output_directory=output,
        )
        return WorkflowLaunch(
            request,
            run,
            (self.worker_python, "-I", "-m", "nuclei_tool.worker"),
            directory,
            encode_frame(start),
            output,
            NucleiProcessCodec(start),
        )

    def modules(self, source: ScientificAsset) -> tuple[WorkflowHostModule, ...]:
        image = source.description.image
        if (
            source.description.kind != "raw_image"
            or image is None
            or image.dtype != "uint8"
            or source.description.unit != "pixel_intensity"
            or image.frame.frame_id != "original_pixels"
            or image.frame.origin_asset_sha256 != source.payload.sha256
        ):
            raise ValueError("Nuclei research requires an original uint8 image")
        spec = nuclei_module_spec()
        interface = WorkflowModule(
            module=spec,
            input_ports=(
                ScientificPort(
                    name="source",
                    kind="raw_image",
                    quantitative=True,
                    accepted_dtypes=("uint8",),
                    unit="pixel_intensity",
                    frame_id=image.frame.frame_id,
                    frame_origin_sha256=source.payload.sha256,
                ),
            ),
            output_ports=(
                PortTypeBinding(
                    port="labels",
                    description=ScientificType(kind="analysis_result", unit="instance_id"),
                ),
                PortTypeBinding(
                    port="provenance", description=ScientificType(kind="run_manifest", unit=None)
                ),
            ),
        )
        expected = NucleiParameters(source_sha256=source.payload.sha256, shape_yx=image.shape)
        registration = ModuleRegistration(
            interface=interface,
            parameters_schema=spec.parameters_schema,
            validate_parameters=partial(_validate_parameters, expected),
        )
        return (
            WorkflowHostModule(
                registration,
                workflow_runtime_environment(research_environment()),
                self.launch,
            ),
        )

    def registry(self, plan: ExecutionPlan) -> tuple[WorkflowHostModule, ...]:
        roots = tuple(
            item.asset for node in plan.nodes for item in node.inputs if item.asset is not None
        )
        if not roots:
            raise ValueError("Nuclei workflow requires an original image")
        return self.modules(roots[0])

    def build(self, source: ScientificAsset) -> ExecutionPlan:
        definition = self.definition(source)
        modules = self.modules(source)
        return compile_workflow(
            definition, tuple(m.registration for m in modules), modules[0].environment
        )

    def definition(self, source: ScientificAsset) -> WorkflowDefinition:
        modules = self.modules(source)
        image = source.description.image
        assert image is not None
        parameters = NucleiParameters(source_sha256=source.payload.sha256, shape_yx=image.shape)
        definition = WorkflowDefinition(
            workflow_id="nuclei-research",
            workflow_version="1.0",
            revision=0,
            title="Fixed StarDist nuclei research",
            sample_id=source.sample_id,
            nodes=(
                WorkflowNode(
                    node_id="segment",
                    module=modules[0].registration.interface.module,
                    parameters_json=parameters.model_dump_json(),
                ),
            ),
            inputs=(WorkflowInput(node_id="segment", port="source", asset=source),),
            outputs=tuple(
                WorkflowOutput(name=name, node_id="segment", port=name)
                for name in ("labels", "provenance")
            ),
        )
        return definition


def _validate_parameters(expected: NucleiParameters, raw: str) -> None:
    if NucleiParameters.model_validate_json(raw) != expected:
        raise ValueError("Nuclei parameters differ from frozen original metadata")
