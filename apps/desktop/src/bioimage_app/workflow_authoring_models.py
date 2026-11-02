"""Versioned editor drafts and bounded fixed host messages; no Qt or tool imports."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from tool_contracts.api import (
    AssetRef,
    ExecutionPlan,
    ScientificAsset,
    WorkflowBatch,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowInput,
    WorkflowIssue,
    WorkflowLayout,
    WorkflowModule,
    WorkflowNode,
    WorkflowOutput,
)


class AuthoringGraph(WorkflowDefinition):
    # Incomplete graphs are honest saved drafts, never executable plans.
    nodes: Annotated[tuple[WorkflowNode, ...], Field(max_length=64)] = ()
    edges: Annotated[tuple[WorkflowEdge, ...], Field(max_length=256)] = ()
    inputs: Annotated[tuple[WorkflowInput, ...], Field(max_length=128)] = ()
    outputs: Annotated[tuple[WorkflowOutput, ...], Field(max_length=64)] = ()


class AuthoringSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    sample_id: Annotated[str, Field(min_length=1, max_length=80)]
    label: Annotated[str, Field(min_length=1, max_length=256)]
    asset: ScientificAsset | None = None
    reason: Annotated[str, Field(max_length=1024)] = ""

    @model_validator(mode="after")
    def source_facts(self) -> Self:
        if self.asset is None and not self.reason:
            raise ValueError("A failed input requires its actual reason")
        if self.asset is not None and self.asset.sample_id != self.sample_id:
            raise ValueError("Input identity differs from the scientific source")
        return self


class AuthoringProject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    schema_version: Literal[1] = 1
    document_id: Annotated[str, Field(min_length=1, max_length=80)]
    revision: Annotated[int, Field(ge=0)] = 0
    graph: AuthoringGraph
    layout: WorkflowLayout
    sources: Annotated[tuple[AuthoringSource, ...], Field(min_length=1, max_length=16)]
    seed: WorkflowDefinition
    last_batch_id: Annotated[str, Field(max_length=80)] = ""

    @model_validator(mode="after")
    def identities(self) -> Self:
        if len({item.sample_id for item in self.sources}) != len(self.sources):
            raise ValueError("Duplicate editor input identity")
        if not any(item.sample_id == self.graph.sample_id and item.asset for item in self.sources):
            raise ValueError("The draft needs one admitted primary source")
        return self


class AuthoringCommand(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    operation: Literal["initialize", "load", "save", "freeze", "bind", "export", "results", "open"]
    document_id: Annotated[str, Field(min_length=1, max_length=80)]
    previous_revision: Annotated[int, Field(ge=0)] | None = None
    graph: AuthoringGraph | None = None
    layout: WorkflowLayout | None = None
    source_paths: Annotated[tuple[str, ...], Field(max_length=16)] = ()
    validation_cases: Annotated[
        tuple[
            Literal["triangle_u8", "triangle_u16", "flat_zero", "invalid_roi", "dtype_limits"], ...
        ],
        Field(max_length=16),
    ] = ()
    lane_count: Annotated[int, Field(ge=1, le=96)] | None = None
    polarity: Literal["dark", "light"] = "dark"
    template_path: Annotated[str, Field(max_length=4096)] = ""
    destination: Annotated[str, Field(max_length=4096)] = ""
    batch_id: Annotated[str, Field(max_length=80)] = ""
    sample_id: Annotated[str, Field(max_length=80)] = ""
    node_id: Annotated[str, Field(max_length=80)] = ""
    port: Annotated[str, Field(max_length=80)] = ""

    @model_validator(mode="after")
    def required_fields(self) -> Self:
        if self.operation in ("save", "freeze", "bind") and self.previous_revision is None:
            raise ValueError("Editing requires the saved CAS revision")
        if self.operation in ("save", "freeze") and (self.graph is None or self.layout is None):
            raise ValueError("Save/run requires the current graph and separate layout")
        if self.operation in ("initialize", "bind"):
            if bool(self.source_paths) == bool(self.validation_cases):
                raise ValueError("Choose original files or explicitly labelled validation inputs")
            if self.operation == "initialize" and not self.template_path:
                if len(self.source_paths or self.validation_cases) != 1:
                    raise ValueError("Create the first template from one input, then bind a batch")
                if self.source_paths and self.lane_count is None:
                    raise ValueError("Declare the lane count for the original WB suggestion")
        if self.operation == "export" and not self.destination:
            raise ValueError("Choose a new template file")
        if self.operation == "open" and not all(
            (self.batch_id, self.sample_id, self.node_id, self.port)
        ):
            raise ValueError("Opening a result requires its frozen output identity")
        return self


class AuthoringModule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    title: str
    interface: WorkflowModule
    parameters_json: str
    limits: str


class AuthoringOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    batch_id: str
    sample_id: str
    node_id: str
    port: str
    kind: str
    asset: AssetRef
    text: str = ""
    preview: str = ""
    table: tuple[tuple[str, ...], ...] = ()
    table_rows: int = 0


class AuthoringRunNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    node_id: str
    module_id: str
    title: str


class AuthoringSampleState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    sample_id: str
    label: str
    state: str
    reason: str


class AuthoringProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    operation: str = ""
    project: AuthoringProject
    catalogue: tuple[AuthoringModule, ...]
    issues: tuple[WorkflowIssue, ...]
    plan: ExecutionPlan | None = None
    batch: WorkflowBatch | None = None
    outputs: tuple[AuthoringOutput, ...] = ()
    opened_path: str = ""
    execution_nodes: tuple[AuthoringRunNode, ...] = ()
    samples: tuple[AuthoringSampleState, ...] = ()
    matches_run: bool = False
