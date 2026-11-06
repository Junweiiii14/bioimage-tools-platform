"""Explicit research-tool bindings for the existing editor, not a plugin loader."""

import sys

from platform_runtime.api import compile_workflow
from tool_contracts.api import (
    ExecutionPlan,
    WorkflowDefinition,
    WorkflowInput,
    WorkflowNode,
    canonical_module_json,
)

from bioimage_app.workflow_authoring_models import AuthoringSource
from bioimage_app.workflow_preparation import WorkflowHostModule


def research_definition(tool: str, sample: AuthoringSource) -> WorkflowDefinition:
    assert sample.asset is not None
    if tool == "bca":
        from bioimage_app.bca_workflow_host import BcaHost

        assert sample.record is not None
        return BcaHost().definition(sample.asset, sample.record)
    from bioimage_app.nuclei_workflow_host import NucleiHost

    return NucleiHost(sys.executable, "").definition(sample.asset)


def research_modules(tool: str, sample: AuthoringSource) -> tuple[WorkflowHostModule, ...]:
    assert sample.asset is not None
    if tool == "bca":
        from bioimage_app.bca_workflow_host import BcaHost

        return BcaHost().registry_definition()
    # Metadata assembly only. Execution uses the explicitly configured research host.
    from bioimage_app.nuclei_workflow_host import NucleiHost

    return NucleiHost(sys.executable, "").modules(sample.asset)


def bind_research_template(
    definition: WorkflowDefinition, sample: AuthoringSource, tool: str
) -> tuple[WorkflowDefinition, ExecutionPlan]:
    assert sample.asset is not None
    expected = research_definition(tool, sample)
    module_id = expected.nodes[0].module.module_id
    if any(n.module.module_id != module_id for n in definition.nodes):
        raise ValueError("模板包含与所选研究输入不兼容的模块")
    nodes: list[WorkflowNode] = []
    for node in definition.nodes:
        raw = node.parameters_json
        if tool == "nuclei":
            from nuclei_tool.api import NucleiParameters

            # Validate the frozen method before replacing only source metadata.
            old = NucleiParameters.model_validate_json(raw)
            image = sample.asset.description.image
            assert image is not None
            raw = old.model_copy(
                update={"source_sha256": sample.asset.payload.sha256, "shape_yx": image.shape}
            ).model_dump_json()
        nodes.append(node.model_copy(update={"parameters_json": canonical_module_json(raw)}))
    roots = {"source": sample.asset, "record": sample.record}
    inputs: list[WorkflowInput] = []
    for binding in definition.inputs:
        asset = roots.get(binding.port)
        if asset is None:
            raise ValueError(f"{binding.node_id}/{binding.port}: 没有兼容的研究输入")
        inputs.append(binding.model_copy(update={"asset": asset}))
    bound = definition.model_copy(
        update={
            "sample_id": sample.sample_id,
            "revision": definition.revision + 1,
            "nodes": tuple(nodes),
            "inputs": tuple(inputs),
        }
    )
    modules = research_modules(tool, sample)
    return bound, compile_workflow(
        bound, tuple(m.registration for m in modules), modules[0].environment
    )
