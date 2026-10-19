"""Portable WB draft: source asset identity and quantitative annotations, never a preview."""

import json
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from tool_contracts.api import AssetRef

from wb_tool.application.analysis import AnalysisRequest


class WBDocument(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", allow_inf_nan=False)
    schema_version: int = Field(default=1, ge=1, le=1)
    source: AssetRef
    request: AnalysisRequest

    @model_validator(mode="after")
    def source_matches(self) -> "WBDocument":
        if self.source.sha256 != self.request.source_sha256:
            raise ValueError("文档来源与请求摘要不一致")
        return self

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
