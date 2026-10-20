"""Versioned, unconfirmed export observations; never quantitative truth."""

from typing import Literal

from pydantic import Field, model_validator

from wb_tool.application.document import DocumentIO


class SignalRegion(DocumentIO):
    x0: int = Field(ge=0)
    y0: int = Field(ge=0)
    x1: int = Field(gt=0)
    y1: int = Field(gt=0)
    lane_counts: tuple[int, ...] = Field(default=(), max_length=4)
    angle_degrees: float = Field(default=0, ge=-90, le=90)

    @model_validator(mode="after")
    def geometry(self) -> "SignalRegion":
        if self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError("信号区域必须为有效的原图半开矩形")
        if any(type(n) is not int or not 1 <= n <= 96 for n in self.lane_counts):
            raise ValueError("泳道数候选必须为1–96")
        return self


class ExportObservation(DocumentIO):
    source_id: str = Field(min_length=1, max_length=80)
    sha256: str = Field(pattern="^[0-9a-f]{64}$")
    group_id: str = Field(pattern="^[0-9a-f]{24}$")
    role: Literal["signal", "merge", "white", "reference", "unknown"]
    reasons: tuple[str, ...] = Field(default=(), max_length=16)
    regions: tuple[SignalRegion, ...] = Field(default=(), max_length=8)
    error: str = Field(default="", max_length=4096)


class ExportSelection(DocumentIO):
    source_id: str = Field(min_length=1, max_length=80)
    figure_label: str = Field(min_length=1, max_length=120)
    protein_label: str = Field(min_length=1, max_length=120)
    lane_count: int = Field(ge=1, le=96)
    region_index: int | None = Field(default=None, ge=0, le=7)


class ExportDiscovery(DocumentIO):
    schema_version: Literal[1] = 1
    algorithm: Literal["export_signal_regions@1"] = "export_signal_regions@1"
    observations: tuple[ExportObservation, ...] = Field(default=(), max_length=512)
    selections: tuple[ExportSelection, ...] = Field(default=(), max_length=512)

    @model_validator(mode="after")
    def unique_sources(self) -> "ExportDiscovery":
        if len({item.source_id for item in self.observations}) != len(self.observations):
            raise ValueError("识别建议包含重复来源")
        observations = {item.source_id: item for item in self.observations}
        if len({item.source_id for item in self.selections}) != len(self.selections):
            raise ValueError("请勿重复确认同一原图")
        for item in self.selections:
            observation = observations.get(item.source_id)
            if observation is None or observation.error or observation.role == "reference":
                raise ValueError("确认来源必须属于有效的原图识别记录")
            if item.region_index is not None and item.region_index >= len(observation.regions):
                raise ValueError("目标区域不属于当前识别建议")
        return self
