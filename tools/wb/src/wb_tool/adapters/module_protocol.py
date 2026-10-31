"""Bounded one-attempt transport for the explicitly registered WB comparison worker."""

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from tool_contracts.api import (
    ExecutionEvent,
    ExecutionIdentity,
    ExecutionRequest,
    canonical_module_json,
)

MAX_MODULE_FRAME = 1024 * 1024


def module_identity(run_id: str, request: ExecutionRequest) -> ExecutionIdentity:
    return ExecutionIdentity(
        run_id=run_id,
        request_id=request.request_id,
        execution_id=request.execution_id,
        node_id=request.node_id,
        attempt_id=request.attempt_id,
        document_id=request.document_id,
        revision=request.revision,
    )


class WBModuleStart(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    protocol_version: Annotated[int, Field(ge=1, le=1)] = 1
    kind: Literal["start"] = "start"
    sequence: Annotated[int, Field(ge=0, le=0)] = 0
    identity: ExecutionIdentity
    request: ExecutionRequest
    source_path: Annotated[str, Field(min_length=1, max_length=32768)]
    output_directory: Annotated[str, Field(min_length=1, max_length=32768)]

    @field_validator("source_path", "output_directory")
    @classmethod
    def absolute_path(cls, value: str) -> str:
        if not Path(value).is_absolute() or "\x00" in value:
            raise ValueError("Worker paths must be host-assigned absolute paths")
        return value

    @model_validator(mode="after")
    def same_attempt(self) -> Self:
        if self.identity != module_identity(self.identity.run_id, self.request):
            raise ValueError("Start identity differs from the frozen request")
        return self


class WBModuleCancel(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    protocol_version: Annotated[int, Field(ge=1, le=1)] = 1
    kind: Literal["cancel"] = "cancel"
    sequence: Annotated[int, Field(ge=1, le=1)] = 1
    identity: ExecutionIdentity


def encode_module_frame(frame: WBModuleStart | WBModuleCancel | ExecutionEvent) -> bytes:
    payload = canonical_module_json(frame.model_dump_json())
    # Revalidate nested objects, including model_copy(update=...) values.
    type(frame).model_validate_json(payload)
    return payload.encode("utf-8") + b"\n"


def module_frame_json(payload: bytes) -> str:
    if len(payload) > MAX_MODULE_FRAME:
        raise ValueError("Module frame exceeds byte budget")
    return canonical_module_json(payload.decode("utf-8"))


class WBModuleConversation:
    """Host-side identity/order checks; an event is never proof of OS success."""

    def __init__(self, start: WBModuleStart) -> None:
        self.start = WBModuleStart.model_validate_json(start.model_dump_json())
        self.stage = 0
        self.cancel_pending = False

    def accept(self, payload: bytes) -> ExecutionEvent:
        event = ExecutionEvent.model_validate_json(module_frame_json(payload))
        if event.sequence != self.stage:
            raise ValueError("Unexpected module event order")
        if self.stage == 0:
            if event.kind != "hello":
                raise ValueError("Missing module hello")
        else:
            if event.identity != self.start.identity:
                raise ValueError("Module event belongs to another attempt")
            if self.stage == 1 and event.kind != "accepted":
                raise ValueError("Missing module acceptance")
            if event.manifest is not None and event.manifest.request != self.start.request:
                raise ValueError("Module result changed the frozen request")
        self.stage += 1
        return event

    def cancellation(self) -> WBModuleCancel:
        if self.stage != 2 or self.cancel_pending:
            raise ValueError("Cancellation requires one accepted active attempt")
        self.cancel_pending = True
        return WBModuleCancel(identity=self.start.identity)
