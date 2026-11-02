"""Workflow journal v1: process facts are references, never invented process receipts."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from tool_contracts.contracts_v1 import (
    BoundAsset,
    Digest,
    FrozenContract,
    Identifier,
    RunRecord,
    VersionOne,
)
from tool_contracts.workflows import ExecutionPlan

WorkflowState = Literal[
    "running", "pausing", "paused", "cancelling", "succeeded", "failed", "cancelled", "interrupted"
]
WorkflowEventKind = Literal[
    "created",
    "intent",
    "prepared",
    "started",
    "worker_hello",
    "worker_accepted",
    "worker_terminal",
    "committed",
    "recovered",
    "reused",
    "pausing",
    "paused",
    "resumed",
    "cancelling",
    "cancelled",
    "failed",
    "interrupted",
    "abandoned",
]


class WorkflowAttempt(FrozenContract):
    node_id: Identifier
    attempt_id: Identifier
    request_id: Identifier
    document_id: Identifier
    revision: Annotated[int, Field(ge=0)]
    request_sha256: Digest
    computation_key: Digest
    run: RunRecord | None = None
    worker_sequence: Annotated[int, Field(ge=-1, le=2)] = -1
    worker_terminal: Literal["result", "failure", "cancelled"] | None = None
    abandoned_reason: Annotated[str, Field(min_length=1, max_length=1024)] | None = None

    @model_validator(mode="after")
    def facts_agree(self) -> Self:
        if self.run is not None:
            if (self.run.document_id, self.run.revision, self.run.request.sha256) != (
                self.document_id,
                self.revision,
                self.request_sha256,
            ):
                raise ValueError("Run differs from its persisted attempt intent")
            if self.abandoned_reason is not None:
                raise ValueError("An actual run cannot be abandoned without a terminal record")
        if (self.worker_sequence == 2) != (self.worker_terminal is not None):
            raise ValueError("Only the observed terminal worker sequence has a terminal kind")
        return self

    @property
    def active(self) -> bool:
        return self.abandoned_reason is None and (
            self.run is None
            or self.run.state in ("prepared", "running", "committing", "cancelling")
        )


class WorkflowNodeResult(FrozenContract):
    """A selected committed result; reuse points to the original real run/attempt."""

    node_id: Identifier
    computation_key: Digest
    run: RunRecord
    outputs: Annotated[tuple[BoundAsset, ...], Field(min_length=1, max_length=16)]
    source_execution_id: Identifier
    source_node_id: Identifier
    source_attempt_id: Identifier
    reused: bool
    quality: Literal["complete", "issues"]

    @model_validator(mode="after")
    def committed_only(self) -> Self:
        if self.run.state != "succeeded" or self.run.result is None:
            raise ValueError("Selected workflow results require a real committed RunRecord")
        if len({item.port for item in self.outputs}) != len(self.outputs):
            raise ValueError("Duplicate selected output port")
        if len({item.asset.asset_id for item in self.outputs}) != len(self.outputs):
            raise ValueError("Selected output physical identities must be distinct")
        return self


class WorkflowJournalEvent(FrozenContract):
    sequence: Annotated[int, Field(ge=1, le=4096)]
    kind: WorkflowEventKind
    state: WorkflowState
    node_id: Identifier | None = None
    attempt_id: Identifier | None = None
    run_id: Identifier | None = None
    command_id: Identifier | None = None
    message: Annotated[str, Field(max_length=256)] = ""


class WorkflowLedger(FrozenContract):
    schema_version: VersionOne = 1
    execution_id: Identifier
    plan: ExecutionPlan
    revision: Annotated[int, Field(ge=0)]
    state: WorkflowState
    attempts: Annotated[tuple[WorkflowAttempt, ...], Field(max_length=256)] = ()
    results: Annotated[tuple[WorkflowNodeResult, ...], Field(max_length=64)] = ()
    events: Annotated[tuple[WorkflowJournalEvent, ...], Field(min_length=1, max_length=4096)]
    control_count: Annotated[int, Field(ge=0, le=128)] = 0
    reason: Annotated[str, Field(min_length=1, max_length=1024)] | None = None

    @model_validator(mode="after")
    def consistent_journal(self) -> Self:
        if self.events[0].kind != "created" or any(
            event.kind == "created" for event in self.events[1:]
        ):
            raise ValueError("A workflow has exactly one initial created event")
        if self.events[-1].state != self.state:
            raise ValueError("Last persisted event must expose the actual workflow state")
        if self.revision != len(self.events) - 1 or any(
            event.sequence != index for index, event in enumerate(self.events, start=1)
        ):
            raise ValueError("Journal revision/global event sequence must be contiguous")
        commands = [event.command_id for event in self.events if event.command_id is not None]
        if len(commands) != len(set(commands)) or len(commands) != self.control_count:
            raise ValueError("Control receipts must be unique and counted")
        nodes = {node.node_id: node for node in self.plan.nodes}
        if len(nodes) != len(self.plan.nodes):
            raise ValueError("Frozen plan has duplicate node identities")
        for field in ("attempt_id", "request_id", "document_id"):
            values = [getattr(attempt, field) for attempt in self.attempts]
            if len(values) != len(set(values)):
                raise ValueError("Attempt/request/document identities cannot be reused")
        selected = tuple(result.node_id for result in self.results)
        if selected != tuple(node.node_id for node in self.plan.nodes[: len(selected)]):
            raise ValueError("Committed results must follow the frozen serial plan")
        for item in (*self.attempts, *self.results):
            node = nodes.get(item.node_id)
            if node is None or item.computation_key != node.computation_key:
                raise ValueError("Journal node/key differs from its frozen plan")
        active = [attempt for attempt in self.attempts if attempt.active]
        if len(active) > 1:
            raise ValueError("Only one attempt may be active")
        if active:
            if self.state not in ("running", "pausing", "cancelling"):
                raise ValueError("A paused/terminal workflow cannot retain an active attempt")
            if (
                len(selected) == len(nodes)
                or active[0].node_id != self.plan.nodes[len(selected)].node_id
            ):
                raise ValueError("Active attempt is not the next frozen node")
        complete = len(self.results) == len(self.plan.nodes)
        if (self.state == "succeeded") != complete:
            raise ValueError("Workflow success requires every committed node result")
        if self.state in ("failed", "interrupted") and self.reason is None:
            raise ValueError("Failed/interrupted workflows require a reason")
        return self

    @property
    def active_attempt(self) -> WorkflowAttempt | None:
        return next((attempt for attempt in self.attempts if attempt.active), None)
