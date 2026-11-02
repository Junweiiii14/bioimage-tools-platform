"""Finite batch index v1; each item references the existing workflow journal."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from tool_contracts.contracts_v1 import FrozenContract, Identifier, VersionOne
from tool_contracts.workflows import ExecutionPlan

BatchState = Literal[
    "running", "pausing", "paused", "cancelling", "cancelled", "completed", "completed_with_issues"
]
BatchItemState = Literal[
    "pending", "running", "paused", "succeeded", "issues", "failed", "cancelled"
]


class WorkflowBatchItem(FrozenContract):
    sample_id: Identifier
    execution_id: Identifier
    plan: ExecutionPlan | None
    cache_execution_id: Identifier | None = None
    state: BatchItemState = "pending"
    child_revision: Annotated[int, Field(ge=0)] | None = None
    completed_nodes: Annotated[int, Field(ge=0, le=64)] = 0
    reason: Annotated[str, Field(min_length=1, max_length=1024)] | None = None

    @model_validator(mode="after")
    def item_facts(self) -> Self:
        if self.plan is None:
            if self.state != "failed" or self.reason is None or self.completed_nodes:
                raise ValueError("An unprepared sample must retain its explicit failure")
        else:
            if self.sample_id != self.plan.sample_id:
                raise ValueError("Batch sample differs from the frozen plan")
            if self.completed_nodes > len(self.plan.nodes):
                raise ValueError("Completed node count exceeds the frozen graph")
            if self.state in ("succeeded", "issues") and (
                self.completed_nodes != len(self.plan.nodes) or self.child_revision is None
            ):
                raise ValueError("A completed sample needs a complete child checkpoint")
        if self.state == "failed" and self.reason is None:
            raise ValueError("Failed samples require a reason")
        return self


class WorkflowBatchControl(FrozenContract):
    command_id: Identifier
    action: Literal["pause", "resume", "cancel"]


class WorkflowBatch(FrozenContract):
    schema_version: VersionOne = 1
    batch_id: Identifier
    revision: Annotated[int, Field(ge=0)] = 0
    state: BatchState = "running"
    items: Annotated[tuple[WorkflowBatchItem, ...], Field(min_length=1, max_length=16)]
    controls: Annotated[tuple[WorkflowBatchControl, ...], Field(max_length=128)] = ()
    dispatches: Annotated[int, Field(ge=0, le=256)] = 0

    @model_validator(mode="after")
    def finite_batch(self) -> Self:
        if len({item.sample_id for item in self.items}) != len(self.items):
            raise ValueError("Duplicate batch sample")
        executions = {item.execution_id for item in self.items}
        if len(executions) != len(self.items) or self.batch_id in executions:
            raise ValueError("Batch and child document identities must be distinct")
        if len({control.command_id for control in self.controls}) != len(self.controls):
            raise ValueError("Duplicate batch control identity")
        plans = tuple(item.plan for item in self.items if item.plan is not None)
        if sum(len(plan.nodes) for plan in plans) > 64:
            raise ValueError("Batch exceeds 64 frozen nodes")
        edges = sum(
            port.source_node is not None
            for plan in plans
            for node in plan.nodes
            for port in node.inputs
        )
        if edges > 256 or sum(len(plan.model_dump_json().encode()) for plan in plans) > 1048576:
            raise ValueError("Batch exceeds the frozen edge/plan-byte budget")
        active = tuple(item for item in self.items if item.state in ("running", "paused"))
        if len(active) > 1:
            raise ValueError("A batch may own only one current child")
        complete = all(
            item.state in ("succeeded", "issues", "failed", "cancelled") for item in self.items
        )
        if self.state in ("completed", "completed_with_issues", "cancelled") and not complete:
            raise ValueError("Terminal batch retains unfinished samples")
        if self.state == "completed" and any(item.state != "succeeded" for item in self.items):
            raise ValueError("Successful batch contains a failed or incomplete sample")
        return self

    @property
    def current_index(self) -> int | None:
        active = next(
            (index for index, item in enumerate(self.items) if item.state in ("running", "paused")),
            None,
        )
        return (
            active
            if active is not None
            else next(
                (index for index, item in enumerate(self.items) if item.state == "pending"), None
            )
        )
