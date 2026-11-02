"""Explicit parameters for the original-image workflow; no new numerical method."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from tool_contracts.api import AssetRef, ImageMetadata, canonical_module_json

from wb_tool.application.analysis import AnalysisRequest


class VerifyOriginalParameters(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    schema_version: Annotated[int, Field(ge=1, le=1)] = 1
    image: ImageMetadata


class WBReportParameters(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    schema_version: Annotated[int, Field(ge=1, le=1)] = 1
    layout: Literal["compact", "comfortable"] = "comfortable"
    expected_rows: Annotated[int, Field(ge=1)]


class OriginalValidation(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    schema_version: Annotated[int, Field(ge=1, le=1)] = 1
    method: Literal["original_tiff_validation@1"] = "original_tiff_validation@1"
    source: AssetRef
    image: ImageMetadata
    conversion: str | None


def validate_wb_workflow_parameters(module_id: str, raw: str) -> None:
    raw = canonical_module_json(raw)
    if module_id == "wb-verify-original":
        VerifyOriginalParameters.model_validate_json(raw)
    elif module_id == "wb-analyze-original":
        planned = TypeAdapter(AnalysisRequest).validate_json(raw, strict=True, extra="forbid")
        if (planned.revision, planned.geometry_policy, planned.quant_policy) != (
            0,
            "fixed_grid@1",
            "legacy_bounds@1",
        ) or not any(lane.bands for lane in planned.lanes):
            raise ValueError("Workflow accepts the unchanged fixed-grid method and fresh document0")
    elif module_id == "wb-publish-original":
        WBReportParameters.model_validate_json(raw)
    else:
        raise ValueError("Unregistered WB workflow module")
