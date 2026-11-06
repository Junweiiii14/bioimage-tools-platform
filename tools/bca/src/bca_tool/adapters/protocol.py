"""Bounded research worker transport using the existing shared execution envelope."""

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from tool_contracts.api import (
    ExecutionEvent,
    ExecutionIdentity,
    ExecutionRequest,
    canonical_module_json,
)

MAX_FRAME = 1024 * 1024


def execution_identity(run_id: str, request: ExecutionRequest) -> ExecutionIdentity:
    return ExecutionIdentity(
        run_id=run_id,
        request_id=request.request_id,
        execution_id=request.execution_id,
        node_id=request.node_id,
        attempt_id=request.attempt_id,
        document_id=request.document_id,
        revision=request.revision,
    )


class BcaStart(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    protocol_version: Literal[1] = 1
    kind: Literal["start"] = "start"
    sequence: Literal[0] = 0
    identity: ExecutionIdentity
    request: ExecutionRequest
    source_path: Annotated[str, Field(min_length=1, max_length=32768)]
    record_path: Annotated[str, Field(min_length=1, max_length=32768)]
    output_directory: Annotated[str, Field(min_length=1, max_length=32768)]

    @field_validator("source_path", "record_path", "output_directory")
    @classmethod
    def absolute_path(cls, value: str) -> str:
        if not Path(value).is_absolute() or "\x00" in value:
            raise ValueError("Worker paths must be explicit absolute paths")
        return value

    @model_validator(mode="after")
    def same_attempt(self) -> Self:
        if self.identity != execution_identity(self.identity.run_id, self.request):
            raise ValueError("Start differs from frozen execution identity")
        return self


class BcaCancel(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    protocol_version: Literal[1] = 1
    kind: Literal["cancel"] = "cancel"
    sequence: Literal[1] = 1
    identity: ExecutionIdentity


def frame_json(data: bytes) -> str:
    if len(data) > MAX_FRAME:
        raise ValueError("Protocol frame exceeds budget")
    return canonical_module_json(data.decode("utf-8"))


def encode_frame(frame: BcaStart | BcaCancel | ExecutionEvent) -> bytes:
    data = canonical_module_json(frame.model_dump_json()).encode("utf-8")
    frame_json(data)
    type(frame).model_validate_json(data)
    return data + b"\n"


class BcaConversation:
    def __init__(self, start: BcaStart) -> None:
        self.start = BcaStart.model_validate_json(start.model_dump_json())
        self.sequence = 0
        self.cancelled = False

    def accept(self, data: bytes) -> ExecutionEvent:
        event = ExecutionEvent.model_validate_json(frame_json(data))
        if event.sequence != self.sequence:
            raise ValueError("Unexpected worker sequence")
        if self.sequence == 0:
            if event.kind != "hello":
                raise ValueError("Missing worker hello")
        elif event.identity != self.start.identity:
            raise ValueError("Worker event belongs to another attempt")
        if event.manifest is not None and event.manifest.request != self.start.request:
            raise ValueError("Worker result changed the frozen request")
        self.sequence += 1
        return event

    def cancellation(self) -> bytes:
        if self.sequence != 2 or self.cancelled:
            raise ValueError("Cancellation requires an accepted active attempt")
        self.cancelled = True
        return encode_frame(BcaCancel(identity=self.start.identity))
