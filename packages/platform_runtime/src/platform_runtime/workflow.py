"""Pure finite-DAG compiler. Trusted host registration supplies parameter validation."""

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from tool_contracts.api import (
    ExecutionPlan,
    PlannedInput,
    PlannedNode,
    RuntimeVersion,
    ScientificPort,
    ScientificType,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowInput,
    WorkflowIssue,
    WorkflowModule,
    WorkflowNode,
    canonical_module_json,
)


@dataclass(frozen=True)
class ModuleRegistration:
    interface: WorkflowModule
    parameters_schema: str
    validate_parameters: Callable[[str], None]

    def __post_init__(self) -> None:
        WorkflowModule.model_validate(self.interface.model_dump(mode="python"))
        if canonical_module_json(self.parameters_schema) != canonical_module_json(
            self.interface.module.parameters_schema
        ):
            raise ValueError("Registered parameter validator schema differs from the module")


class WorkflowValidationError(ValueError):
    def __init__(self, issues: Sequence[WorkflowIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(f"{x.code}: {x.message}" for x in issues))


def load_workflow_definition(raw: str) -> WorkflowDefinition:
    """Bounded JSON rejects duplicate keys, nonfinite values and unknown schema/fields."""
    return WorkflowDefinition.model_validate_json(canonical_module_json(raw), strict=True)


def workflow_definition_json(definition: WorkflowDefinition) -> str:
    valid = WorkflowDefinition.model_validate(definition.model_dump(mode="python"))
    return canonical_module_json(valid.model_dump_json())


def _port_issues(description: ScientificType, required: ScientificPort) -> tuple[str, ...]:
    reasons: list[str] = []
    if description.kind != required.kind:
        reasons.append("scientific_role")
    if required.quantitative and description.kind == "display_image":
        reasons.append("display_into_quantitation")
    if required.unit is not None and description.unit != required.unit:
        reasons.append("unit")
    if required.quantitative and description.unit is None:
        reasons.append("unknown_measurement_unit")
    image = description.image
    frame = (
        image.frame
        if image is not None
        else (description.series.coordinate_frame if description.series is not None else None)
    )
    if required.accepted_dtypes and (image is None or image.dtype not in required.accepted_dtypes):
        reasons.append("dtype")
    if required.frame_id is not None and (frame is None or frame.frame_id != required.frame_id):
        reasons.append("coordinate_frame")
    if required.frame_origin_sha256 is not None and (
        frame is None or frame.origin_asset_sha256 != required.frame_origin_sha256
    ):
        reasons.append("frame_origin")
    if required.table is not None and description.table != required.table:
        reasons.append("table_schema")
    return tuple(reasons)


def compile_workflow(
    definition: WorkflowDefinition,
    registrations: Sequence[ModuleRegistration],
    environment: tuple[RuntimeVersion, ...],
) -> ExecutionPlan:
    """The compiler owns no I/O; host validators are explicitly registered trusted code."""
    definition = load_workflow_definition(workflow_definition_json(definition))
    environment = tuple(
        RuntimeVersion.model_validate(x.model_dump(mode="python")) for x in environment
    )
    if (
        not environment
        or len(environment) > 32
        or len({x.name for x in environment}) != len(environment)
    ):
        raise ValueError("A unique, nonempty frozen runtime environment is required")
    environment = tuple(sorted(environment, key=lambda x: x.name))
    registry: dict[tuple[str, str], ModuleRegistration] = {}
    for entry in registrations:
        key = (entry.interface.module.module_id, entry.interface.module.module_version)
        if key in registry:
            raise ValueError("Duplicate trusted module registration")
        registry[key] = entry
    issues: list[WorkflowIssue] = []

    def issue(code: str, message: str, node: str | None = None, port: str | None = None) -> None:
        issues.append(WorkflowIssue(code=code, message=message, node_id=node, port=port))

    nodes = {x.node_id: x for x in definition.nodes}
    if len(nodes) != len(definition.nodes):
        issue("duplicate_node", "Node identities must be unique")
    entries: dict[str, ModuleRegistration] = {}
    for node in definition.nodes:
        key = (node.module.module_id, node.module.module_version)
        entry = registry.get(key)
        if entry is None:
            issue(
                "unknown_module", "Module/version is absent from the trusted registry", node.node_id
            )
        elif entry.interface.module != node.module:
            issue(
                "module_mismatch",
                "Frozen method, implementation or schema differs from registration",
                node.node_id,
            )
        else:
            entries[node.node_id] = entry
            try:
                entry.validate_parameters(node.parameters_json)
            except (ValueError, TypeError) as error:
                issue("parameters", str(error)[:1024] or "Invalid parameters", node.node_id)

    bindings: dict[tuple[str, str], WorkflowInput | WorkflowEdge] = {}
    assets: dict[str, str] = {}
    for item in definition.inputs:
        if item.asset.sample_id != definition.sample_id:
            issue("sample_mismatch", "Input belongs to a different sample", item.node_id, item.port)
        identity = item.asset.payload.asset_id
        serialized = item.asset.model_dump_json()
        if identity in assets and assets[identity] != serialized:
            issue(
                "asset_identity",
                "One physical identity has conflicting scientific bindings",
                item.node_id,
                item.port,
            )
        assets[identity] = serialized
        key = (item.node_id, item.port)
        if key in bindings:
            issue("duplicate_binding", "Input has more than one source", *key)
        bindings[key] = item
    dependencies = {key: set[str]() for key in nodes}
    for edge in definition.edges:
        if edge.source_node not in nodes or edge.target_node not in nodes:
            issue("unknown_node", "Connection references an absent node")
        else:
            dependencies[edge.target_node].add(edge.source_node)
        key = (edge.target_node, edge.target_port)
        if key in bindings:
            issue("duplicate_binding", "Input has more than one source", *key)
        bindings[key] = edge
        source = entries.get(edge.source_node)
        if source is not None and edge.source_port not in {
            p.port for p in source.interface.output_ports
        }:
            issue(
                "unknown_output_port",
                "Connection source port is absent",
                edge.source_node,
                edge.source_port,
            )
    for node_id, entry in entries.items():
        for port in entry.interface.input_ports:
            if (node_id, port.name) not in bindings:
                issue("missing_input", "Required input has no source", node_id, port.name)
    for node_id, port in bindings:
        if node_id not in nodes:
            issue("unknown_node", "Input references an absent node", node_id, port)
        elif node_id in entries and port not in {
            x.name for x in entries[node_id].interface.input_ports
        }:
            issue("unknown_input_port", "Input port is absent", node_id, port)
    names: set[str] = set()
    for output in definition.outputs:
        if output.name in names:
            issue("duplicate_output", "Workflow result names must be unique")
        names.add(output.name)
        entry = entries.get(output.node_id)
        if output.node_id not in nodes:
            issue("unknown_node", "Workflow output references an absent node")
        elif entry is not None and output.port not in {
            p.port for p in entry.interface.output_ports
        }:
            issue(
                "unknown_output_port", "Workflow output port is absent", output.node_id, output.port
            )
    remaining = {node: set(parents) for node, parents in dependencies.items()}
    order: list[str] = []
    while remaining:
        ready = sorted(node for node, parents in remaining.items() if not parents)
        if not ready:
            issue("cycle", "Workflow connections contain a cycle")
            break
        order.extend(ready)
        for node in ready:
            del remaining[node]
        for parents in remaining.values():
            parents.difference_update(ready)
    if issues:
        raise WorkflowValidationError(issues)
    planned: dict[str, PlannedNode] = {}
    for node_id in order:
        entry, node = entries[node_id], nodes[node_id]
        inputs: list[PlannedInput] = []
        for required in sorted(entry.interface.input_ports, key=lambda p: p.name):
            bound = bindings[node_id, required.name]
            if isinstance(bound, WorkflowInput):
                description = bound.asset.description
                current = PlannedInput(
                    port=required.name, description=description, asset=bound.asset
                )
            else:
                upstream = planned[bound.source_node]
                description = next(
                    p.description
                    for p in upstream.interface.output_ports
                    if p.port == bound.source_port
                )
                current = PlannedInput(
                    port=required.name,
                    description=description,
                    source_node=bound.source_node,
                    source_port=bound.source_port,
                    source_key=upstream.computation_key,
                )
            for code in _port_issues(description, required):
                issue(
                    code,
                    "Input scientific type does not satisfy its registered port",
                    node_id,
                    required.name,
                )
            inputs.append(current)
        planned[node_id] = PlannedNode(
            node_id=node_id,
            interface=entry.interface,
            parameters_json=node.parameters_json,
            inputs=tuple(inputs),
            environment=environment,
        )
    if issues:
        raise WorkflowValidationError(issues)
    plan = ExecutionPlan(
        workflow_id=definition.workflow_id,
        workflow_version=definition.workflow_version,
        revision=definition.revision,
        sample_id=definition.sample_id,
        nodes=tuple(planned.values()),
        outputs=tuple(sorted(definition.outputs, key=lambda x: x.name)),
    )
    canonical_module_json(plan.model_dump_json())
    return plan


def verify_execution_plan(
    plan: ExecutionPlan, registrations: Sequence[ModuleRegistration]
) -> ExecutionPlan:
    """Recompile untrusted persisted plans; a digest alone is not admission or integrity."""
    plan = ExecutionPlan.model_validate(plan.model_dump(mode="python"))
    roots: list[WorkflowInput] = []
    edges: list[WorkflowEdge] = []
    for node in plan.nodes:
        for item in node.inputs:
            if item.asset is not None:
                roots.append(WorkflowInput(node_id=node.node_id, port=item.port, asset=item.asset))
            elif item.source_node is not None and item.source_port is not None:
                edges.append(
                    WorkflowEdge(
                        source_node=item.source_node,
                        source_port=item.source_port,
                        target_node=node.node_id,
                        target_port=item.port,
                    )
                )
    definition = WorkflowDefinition(
        workflow_id=plan.workflow_id,
        workflow_version=plan.workflow_version,
        revision=plan.revision,
        sample_id=plan.sample_id,
        title="Frozen plan",
        nodes=tuple(
            WorkflowNode(
                node_id=n.node_id, module=n.interface.module, parameters_json=n.parameters_json
            )
            for n in plan.nodes
        ),
        edges=tuple(edges),
        inputs=tuple(roots),
        outputs=plan.outputs,
    )
    rebuilt = compile_workflow(definition, registrations, plan.nodes[0].environment)
    if rebuilt != plan:
        raise ValueError("Execution plan differs from trusted recompilation")
    return rebuilt


def execution_plan_digest(plan: ExecutionPlan) -> str:
    valid = ExecutionPlan.model_validate(plan.model_dump(mode="python"))
    return hashlib.sha256(
        canonical_module_json(valid.model_dump_json()).encode("utf-8")
    ).hexdigest()


def load_execution_plan(raw: str, registrations: Sequence[ModuleRegistration]) -> ExecutionPlan:
    parsed = ExecutionPlan.model_validate_json(canonical_module_json(raw), strict=True)
    return verify_execution_plan(parsed, registrations)
