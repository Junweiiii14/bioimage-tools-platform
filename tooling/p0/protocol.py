"""Versioned, bounded UTF-8 NDJSON; no Qt or numerical dependencies."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LIMIT = 1024 * 1024
BUILD = "p0-v1"


class Frame(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    protocol: Literal[1] = 1
    build: Literal["p0-v1"] = BUILD
    run_id: str = Field(min_length=1, max_length=80)
    attempt: Literal[1] = 1
    seq: int = Field(ge=0)
    kind: Literal["hello", "run", "cancel", "ack", "progress", "result", "cancelled", "error"]
    paths: list[str] = Field(default_factory=list, max_length=20)
    mode: Literal["normal", "crash", "stubborn"] = "normal"
    passes: int = Field(default=3, ge=1, le=200)
    completed: int = Field(default=0, ge=0, le=20)
    seconds: list[float] = Field(default_factory=list[float], max_length=20)
    checksums: list[str] = Field(default_factory=list, max_length=20)
    peak_bytes: int = Field(default=0, ge=0)
    detail: str = Field(default="", max_length=4096)


def encode(frame: Frame) -> bytes:
    data = frame.model_dump_json().encode("utf-8")
    if len(data) > LIMIT:
        raise ValueError("Frame exceeds 1 MiB")
    return data + b"\n"


class Decoder:
    def __init__(self) -> None:
        self.pending = bytearray()

    def feed(self, data: bytes) -> list[Frame]:
        result: list[Frame] = []
        # Bound each unfinished line before appending, even for a large input chunk.
        for part in data.splitlines(keepends=True):
            if len(self.pending) + len(part.rstrip(b"\n")) > LIMIT:
                raise ValueError("Frame exceeds 1 MiB")
            self.pending.extend(part)
            if self.pending.endswith(b"\n"):
                result.append(Frame.model_validate_json(self.pending.decode("utf-8")))
                self.pending.clear()
        return result

    def finish(self) -> None:
        if self.pending:
            raise ValueError("Truncated frame")


class Sequence:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.last = -1

    def accept(self, frame: Frame) -> bool:
        if frame.run_id != self.run_id or frame.seq <= self.last:
            return False
        self.last = frame.seq
        return True
