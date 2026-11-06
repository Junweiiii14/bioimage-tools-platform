"""Explicit fixed BCA assembly; shared execution/storage stays experiment-free."""

import json
import sys
from pathlib import Path

from bca_tool.api import (
    BcaConversation,
    BcaStart,
    bca_module_spec,
    encode_frame,
    execution_identity,
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


class BcaProcessCodec:
    def __init__(self, start: BcaStart) -> None:
        self.conversation = BcaConversation(start)

    def accept(self, data: bytes) -> ProcessEvent:
        event = self.conversation.accept(data)
        return ProcessEvent(
            event.kind,
            event.manifest.model_dump_json().encode() if event.manifest else b"",
            event.reason,
            "module_manifest",
            event,
        )

    def cancellation(self) -> bytes:
        return self.conversation.cancellation()


def validate_parameters(raw: str) -> None:
    if json.loads(raw) != {}:
        raise ValueError("BCA fixed method has no adjustable parameters")


class BcaHost:
    def launch(
        self,
        request: ExecutionRequest,
        run: RunRecord,
        files: tuple[HostInputFile, ...],
        directory: str,
    ) -> WorkflowLaunch:
        paths = {f.binding.port: f.path for f in files}
        output = str(Path(directory) / "outputs")
        start = BcaStart(
            identity=execution_identity(run.run_id, request),
            request=request,
            source_path=paths["source"],
            record_path=paths["record"],
            output_directory=output,
        )
        return WorkflowLaunch(
            request,
            run,
            (sys.executable, "-I", "-m", "bca_tool.worker"),
            directory,
            encode_frame(start),
            output,
            BcaProcessCodec(start),
        )

    def registry(self, _plan: ExecutionPlan) -> tuple[WorkflowHostModule, ...]:
        return self.registry_definition()

    def build(self, source: ScientificAsset, record: ScientificAsset) -> ExecutionPlan:
        spec = bca_module_spec()
        definition = WorkflowDefinition(
            workflow_id="bca-research",
            workflow_version="1.0",
            revision=0,
            title="Fixed Pierce25 BCA research",
            sample_id=source.sample_id,
            nodes=(WorkflowNode(node_id="quantify", module=spec, parameters_json="{}"),),
            inputs=(
                WorkflowInput(node_id="quantify", port="source", asset=source),
                WorkflowInput(node_id="quantify", port="record", asset=record),
            ),
            outputs=tuple(
                WorkflowOutput(name=p.name, node_id="quantify", port=p.name)
                for p in spec.output_ports
            ),
        )
        modules = self.registry_definition()
        return compile_workflow(
            definition, tuple(m.registration for m in modules), modules[0].environment
        )

    def registry_definition(self) -> tuple[WorkflowHostModule, ...]:
        # Registration is independent of input bytes; restore recompiles the frozen plan.
        spec = bca_module_spec()
        interface = WorkflowModule(
            module=spec,
            input_ports=(
                ScientificPort(name="source", kind="analysis_result", unit="A562"),
                ScientificPort(name="record", kind="run_manifest", unit=None),
            ),
            output_ports=tuple(
                PortTypeBinding(port=p.name, description=ScientificType(kind=p.kind, unit=None))
                for p in spec.output_ports
            ),
        )
        return (
            WorkflowHostModule(
                ModuleRegistration(
                    interface=interface,
                    parameters_schema=spec.parameters_schema,
                    validate_parameters=validate_parameters,
                ),
                workflow_runtime_environment(research_environment()),
                self.launch,
            ),
        )
