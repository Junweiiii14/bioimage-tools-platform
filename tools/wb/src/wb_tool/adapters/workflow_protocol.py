"""Bounded multi-input transport for three explicitly registered original-value nodes."""

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from tool_contracts.api import (
    ExecutionEvent,
    ExecutionIdentity,
    ExecutionRequest,
    canonical_module_json,
)

from wb_tool.adapters.module_protocol import WBModuleCancel, module_frame_json, module_identity


class WorkflowInputPath(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    port: str
    path: Annotated[str, Field(min_length=1, max_length=32768)]


class WBWorkflowStart(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    protocol_version: Annotated[int, Field(ge=1, le=1)] = 1
    kind: Literal["start"] = "start"
    sequence: Annotated[int, Field(ge=0, le=0)] = 0
    identity: ExecutionIdentity
    request: ExecutionRequest
    inputs: Annotated[tuple[WorkflowInputPath, ...], Field(min_length=1, max_length=8)]
    output_directory: Annotated[str, Field(min_length=1, max_length=32768)]

    @model_validator(mode="after")
    def bound_paths(self) -> Self:
        if self.identity != module_identity(self.identity.run_id, self.request):
            raise ValueError("Workflow start identity changed")
        if len({item.port for item in self.inputs}) != len(self.inputs) or {
            item.port for item in self.inputs
        } != {item.port for item in self.request.inputs}:
            raise ValueError("Workflow paths do not match frozen input ports")
        if any(
            not Path(path).is_absolute() or "\x00" in path
            for path in (
                self.output_directory,
                *(item.path for item in self.inputs),
            )
        ):
            raise ValueError("Workflow paths must be host-assigned absolute paths")
        return self


def encode_wb_workflow_frame(frame: WBWorkflowStart | WBModuleCancel | ExecutionEvent) -> bytes:
    raw = canonical_module_json(frame.model_dump_json())
    type(frame).model_validate_json(raw)
    return raw.encode() + b"\n"


class WBWorkflowConversation:
    def __init__(self, start: WBWorkflowStart) -> None:
        self.start = WBWorkflowStart.model_validate_json(start.model_dump_json())
        self.stage = 0
        self.cancel_pending = False

    def accept(self, payload: bytes) -> ExecutionEvent:
        event = ExecutionEvent.model_validate_json(module_frame_json(payload))
        if event.sequence != self.stage:
            raise ValueError("Unexpected workflow event order")
        if self.stage > 0:
            if event.identity != self.start.identity:
                raise ValueError("Workflow event belongs to another attempt")
            if event.manifest is not None and event.manifest.request != self.start.request:
                raise ValueError("Workflow result changed the frozen request")
        self.stage += 1
        return event

    def cancellation(self) -> WBModuleCancel:
        if self.stage != 2 or self.cancel_pending:
            raise ValueError("Cancellation requires one accepted attempt")
        self.cancel_pending = True
        return WBModuleCancel(identity=self.start.identity)
