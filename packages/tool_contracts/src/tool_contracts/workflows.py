"""Versioned finite DAG declarations; view layout is deliberately a separate document."""

import hashlib
import json
from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from tool_contracts.contracts_v1 import (
    Digest,
    FrozenContract,
    Identifier,
    ModuleSpec,
    RuntimeVersion,
    ShortText,
    VersionOne,
    canonical_module_json,
)
from tool_contracts.scientific_assets import (
    ImageDtype,
    ScientificAsset,
    ScientificKind,
    ScientificType,
    TableMetadata,
)


class ScientificPort(FrozenContract):
    name: Identifier
    kind: ScientificKind
    quantitative: bool = False
    accepted_dtypes: tuple[ImageDtype, ...] = ()
    unit: ShortText | None = None
    frame_id: Identifier | None = None
    frame_origin_sha256: Digest | None = None
    table: TableMetadata | None = None

    @model_validator(mode="after")
    def measurement_role(self) -> Self:
        if self.quantitative and self.kind == "display_image":
            raise ValueError("Display data cannot enter quantitative ports")
        if self.quantitative and self.unit is None:
            raise ValueError("Quantitative ports must declare the expected unit")
        if (
            self.quantitative
            and self.kind in ("raw_image", "analysis_image")
            and not self.accepted_dtypes
        ):
            raise ValueError("Quantitative image ports must declare admitted dtypes")
        if self.quantitative and self.kind == "typed_table" and self.table is None:
            raise ValueError("Quantitative table ports must declare their columns and units")
        if self.accepted_dtypes and self.kind not in (
            "raw_image",
            "analysis_image",
            "display_image",
        ):
            raise ValueError("Only image ports declare image dtypes")
        if self.table is not None and self.kind != "typed_table":
            raise ValueError("Table schema belongs to a table port")
        return self


class PortTypeBinding(FrozenContract):
    port: Identifier
    description: ScientificType


class WorkflowModule(FrozenContract):
    """Registered interface projection; no import paths, code or execution callbacks."""

    schema_version: VersionOne = 1
    module: ModuleSpec
    input_ports: Annotated[tuple[ScientificPort, ...], Field(min_length=1, max_length=8)]
    output_ports: Annotated[tuple[PortTypeBinding, ...], Field(min_length=1, max_length=16)]

    @model_validator(mode="after")
    def envelope_ports(self) -> Self:
        for semantic, envelope in (
            (
                {p.name: p.kind for p in self.input_ports},
                {p.name: p.kind for p in self.module.input_ports},
            ),
            (
                {p.port: p.description.kind for p in self.output_ports},
                {p.name: p.kind for p in self.module.output_ports},
            ),
        ):
            # New series semantics compose an existing analysis_result payload envelope.
            mapped = {
                name: "analysis_result" if kind in ("series", "analysis_image") else kind
                for name, kind in semantic.items()
            }
            if mapped != envelope:
                raise ValueError("Scientific interface must match every v1 envelope port")
        if len({p.name for p in self.input_ports}) != len(self.input_ports) or len(
            {p.port for p in self.output_ports}
        ) != len(self.output_ports):
            raise ValueError("Duplicate semantic port")
        return self


class WorkflowNode(FrozenContract):
    node_id: Identifier
    module: ModuleSpec
    parameters_json: Annotated[str, Field(min_length=2, max_length=1048576)]

    @field_validator("parameters_json")
    @classmethod
    def canonical_parameters(cls, value: str) -> str:
        return canonical_module_json(value)


class WorkflowEdge(FrozenContract):
    source_node: Identifier
    source_port: Identifier
    target_node: Identifier
    target_port: Identifier


class WorkflowInput(FrozenContract):
    node_id: Identifier
    port: Identifier
    asset: ScientificAsset


class WorkflowOutput(FrozenContract):
    name: Identifier
    node_id: Identifier
    port: Identifier


class WorkflowDefinition(FrozenContract):
    schema_version: VersionOne = 1
    workflow_id: Identifier
    workflow_version: ShortText
    revision: Annotated[int, Field(ge=0)]
    title: ShortText
    sample_id: Identifier
    nodes: Annotated[tuple[WorkflowNode, ...], Field(min_length=1, max_length=64)]
    edges: Annotated[tuple[WorkflowEdge, ...], Field(max_length=256)] = ()
    inputs: Annotated[tuple[WorkflowInput, ...], Field(min_length=1, max_length=128)]
    outputs: Annotated[tuple[WorkflowOutput, ...], Field(min_length=1, max_length=64)]


class NodePosition(FrozenContract):
    node_id: Identifier
    x: Annotated[float, Field(ge=-100000, le=100000)]
    y: Annotated[float, Field(ge=-100000, le=100000)]


class WorkflowLayout(FrozenContract):
    schema_version: VersionOne = 1
    positions: Annotated[tuple[NodePosition, ...], Field(max_length=64)] = ()
    zoom: Annotated[float, Field(ge=0.1, le=4)] = 1.0

    @model_validator(mode="after")
    def unique_nodes(self) -> Self:
        if len({p.node_id for p in self.positions}) != len(self.positions):
            raise ValueError("Duplicate node position")
        return self


class PlannedInput(FrozenContract):
    port: Identifier
    description: ScientificType
    asset: ScientificAsset | None = None
    source_node: Identifier | None = None
    source_port: Identifier | None = None
    source_key: Digest | None = None

    @model_validator(mode="after")
    def one_source(self) -> Self:
        if self.asset is not None:
            if any(x is not None for x in (self.source_node, self.source_port, self.source_key)):
                raise ValueError("Root input cannot also reference a node")
            if self.asset.description != self.description:
                raise ValueError("Input metadata differs from the root scientific asset")
        elif any(x is None for x in (self.source_node, self.source_port, self.source_key)):
            raise ValueError("An edge input needs a complete frozen upstream identity")
        return self


class PlannedNode(FrozenContract):
    node_id: Identifier
    interface: WorkflowModule
    parameters_json: Annotated[str, Field(min_length=2, max_length=1048576)]
    inputs: Annotated[tuple[PlannedInput, ...], Field(min_length=1, max_length=8)]
    environment: Annotated[tuple[RuntimeVersion, ...], Field(min_length=1, max_length=32)]

    @field_validator("parameters_json")
    @classmethod
    def frozen_parameters(cls, value: str) -> str:
        if canonical_module_json(value) != value:
            raise ValueError("Planned parameters must be canonical")
        return value

    @property
    def computation_key(self) -> str:
        # Node labels/revisions/layout do not change numerical identity. Input identities,
        # semantic interface, upstream output port/key and exact dependencies do.
        valid = PlannedNode.model_validate(self.model_dump(mode="python"))
        data = valid.model_dump(mode="json", exclude={"node_id"})
        for item in data["inputs"]:
            item.pop("source_node", None)
        canonical = canonical_module_json(json.dumps(data, ensure_ascii=False))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ExecutionPlan(FrozenContract):
    schema_version: VersionOne = 1
    compiler_version: Literal["finite_dag@1"] = "finite_dag@1"
    workflow_id: Identifier
    workflow_version: ShortText
    revision: Annotated[int, Field(ge=0)]
    sample_id: Identifier
    nodes: Annotated[tuple[PlannedNode, ...], Field(min_length=1, max_length=64)]
    outputs: Annotated[tuple[WorkflowOutput, ...], Field(min_length=1, max_length=64)]


class WorkflowIssue(FrozenContract):
    code: ShortText
    message: Annotated[str, Field(min_length=1, max_length=1024)]
    node_id: Identifier | None = None
    port: Identifier | None = None
