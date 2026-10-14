"""Portable WB draft: source asset identity and quantitative annotations, never a preview."""

import json
from dataclasses import replace
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator
from tool_contracts.api import AssetRef

from wb_tool.application.analysis import AnalysisRequest, AnalysisResult
from wb_tool.application.ocr_protocol import OCRResultFrame
from wb_tool.application.worker_protocol import ResultFrame
from wb_tool.domain.worksheet import OCRRecognition, Worksheet


class _DocumentIO(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", allow_inf_nan=False)

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("WB 文档不能有重复 JSON 字段")
                result[key] = value
            return result

        if len(data) > 16 * 1024 * 1024:
            raise ValueError("WB 文档超出大小预算")
        json.loads(data, object_pairs_hook=unique)
        return cls.model_validate_json(data)


class WBDocument(_DocumentIO):
    schema_version: int = Field(default=1, ge=1, le=1)
    source: AssetRef
    request: AnalysisRequest

    @property
    def revision(self) -> int:
        return self.request.revision

    @model_validator(mode="after")
    def source_matches(self) -> "WBDocument":
        if self.source.sha256 != self.request.source_sha256:
            raise ValueError("文档来源与请求摘要不一致")
        return self


class WBWorksheetDocument(_DocumentIO):
    schema_version: int = Field(default=2, ge=2, le=2)
    source: AssetRef
    revision: int = Field(ge=0)
    polarity: Literal["dark", "light"] = "dark"
    request: AnalysisRequest | None = None
    recognition: OCRRecognition | None = None
    ocr_source: AssetRef | None = None
    worksheet: Worksheet | None = None
    measurement: AnalysisResult | None = None

    @model_validator(mode="after")
    def worksheet_sources(self) -> "WBWorksheetDocument":
        if self.request is not None and (
            self.request.source_sha256 != self.source.sha256
            or self.request.revision != self.revision
            or self.request.polarity != self.polarity
        ):
            raise ValueError("文档标注来源/修订/极性不一致")
        if self.recognition is not None:
            source = self.ocr_source or self.source
            if self.recognition.source_sha256 != source.sha256:
                raise ValueError("OCR 文档来源不一致")
            OCRResultFrame(
                protocol_version=1,
                kind="result",
                sequence=2,
                run_id="document",
                attempt_id="document",
                request_id="document",
                revision=self.revision,
                result=self.recognition,
            )
        if self.worksheet is not None and self.worksheet.source_sha256 != self.source.sha256:
            raise ValueError("工作表测量来源不一致")
        if (
            self.measurement is not None
            and replace(self.measurement.request, revision=self.revision) != self.request
        ):
            raise ValueError("保存的测量不对应当前标注")
        if self.measurement is not None:
            ResultFrame(
                protocol_version=1,
                kind="result",
                sequence=2,
                run_id="document",
                attempt_id="document",
                request_id="document",
                result=self.measurement,
            )
        return self


def read_wb_document(data: bytes) -> WBDocument | WBWorksheetDocument:
    if len(data) > 16 * 1024 * 1024:
        raise ValueError("WB 文档超出大小预算")
    raw: object = json.loads(data)
    if isinstance(raw, dict):
        version = cast(dict[str, object], raw).get("schema_version", 1)
        if type(version) is int and version == 2:
            return WBWorksheetDocument.from_bytes(data)
    return WBDocument.from_bytes(data)
