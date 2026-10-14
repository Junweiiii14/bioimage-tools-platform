"""Separate OCR job protocol v1; common envelopes/order remain the same as quantitative jobs."""

import json
from typing import Annotated, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from wb_tool.application.worker_protocol import (
    MAX_FRAME_BYTES,
    AcceptedFrame,
    CancelFrame,
    CancelledFrame,
    FailureFrame,
    FrameSizeError,
    HelloFrame,
    IdentifiedFrame,
    ProtocolErrorFrame,
    WireConversation,
    WireModel,
    unique_json_object,
)
from wb_tool.domain.ocr_manifest import ENGINE_ID, MODEL_HASHES, PREPROCESS_ID
from wb_tool.domain.worksheet import OCRRecognition


class OCRRequest(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    source_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    revision: Annotated[int, Field(ge=0)]


class OCRStartFrame(IdentifiedFrame):
    kind: Literal["start"]
    sequence: Literal[0]
    source_path: Annotated[str, Field(min_length=1, max_length=32768)]
    request: OCRRequest


class OCRResultFrame(IdentifiedFrame):
    kind: Literal["result"]
    sequence: Literal[2]
    revision: Annotated[int, Field(ge=0)]
    result: OCRRecognition

    @model_validator(mode="after")
    def versions(self) -> "OCRResultFrame":
        if type(self.result.schema_version) is not int or self.result.schema_version != 1:
            raise ValueError("OCR schema 无效")
        if (
            self.result.engine_id != ENGINE_ID
            or self.result.model_hashes != MODEL_HASHES
            or self.result.preprocess_id != PREPROCESS_ID
        ):
            raise ValueError("OCR 引擎/模型/预处理版本未知")
        return self


OCRFrame = Annotated[
    HelloFrame
    | OCRStartFrame
    | CancelFrame
    | AcceptedFrame
    | OCRResultFrame
    | FailureFrame
    | CancelledFrame
    | ProtocolErrorFrame,
    Field(discriminator="kind"),
]
_FRAMES = TypeAdapter(OCRFrame)


def parse_ocr_frame(data: bytes) -> OCRFrame:
    if len(data) > MAX_FRAME_BYTES:
        raise FrameSizeError("OCR 消息超过上限")
    json.loads(data, object_pairs_hook=unique_json_object)
    return _FRAMES.validate_json(data, strict=True, extra="forbid")


def encode_ocr_frame(frame: WireModel) -> bytes:
    data = frame.model_dump_json().encode("utf-8")
    parse_ocr_frame(data)
    return data + b"\n"


class OCRConversation(WireConversation):
    def __init__(self, start: OCRStartFrame) -> None:
        def matches(frame: WireModel) -> bool:
            return (
                isinstance(frame, OCRResultFrame)
                and frame.revision == start.request.revision
                and frame.result.source_sha256 == start.request.source_sha256
            )

        super().__init__(start, parse_ocr_frame, matches)

    def accept(self, data: bytes) -> OCRFrame:
        return cast(OCRFrame, super().accept(data))


def ocr_protocol_schema() -> dict[str, object]:
    return _FRAMES.json_schema()
