"""Immutable suggestion snapshots and explicit application to project rows."""

import json
from dataclasses import replace
from math import isfinite
from typing import cast

from pydantic import Field, model_validator

from wb_tool.application.document import DocumentIO
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.domain.crop_detection import CropDetection, CropDetectionSettings


class CropSuggestion(DocumentIO):
    row_id: str = Field(min_length=1, max_length=80)
    source_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    source_revision: int = Field(ge=0)
    settings: CropDetectionSettings
    result: CropDetection | None = None
    error: str = Field(default="", max_length=2000)
    selected_index: int | None = Field(default=None, ge=0, le=7)
    source_warnings: tuple[str, ...] = Field(default=(), max_length=32)

    @model_validator(mode="after")
    def coherent(self) -> "CropSuggestion":
        if (self.result is None) == (not self.error):
            raise ValueError("建议必须是检测结果或明确失败，不能伪装为空成功")
        if self.result is None:
            if self.selected_index is not None:
                raise ValueError("失败建议没有可选候选")
            return self
        result = self.result
        if result.width < 1 or result.height < 1 or result.width * result.height > 16_000_000:
            raise ValueError("建议原图尺寸无效")
        if result.settings != self.settings or len(result.candidates) > 8:
            raise ValueError("建议参数/候选容量不一致")
        if self.selected_index is not None and self.selected_index >= len(result.candidates):
            raise ValueError("候选下标越界")
        for roi in (
            result.membrane,
            result.marker,
            result.sample_region,
            *(c.roi for c in result.candidates),
        ):
            if roi is not None and (roi.x1 > result.width or roi.y1 > result.height):
                raise ValueError("建议范围超出源尺寸")
        for candidate in result.candidates:
            if result.sample_region is None or result.membrane is None:
                raise ValueError("行候选必须有膜和样本范围")
            if (
                candidate.roi.x0 != result.sample_region.x0
                or candidate.roi.x1 != result.sample_region.x1
                or candidate.roi.y0 < result.membrane.y0
                or candidate.roi.y1 > result.membrane.y1
            ):
                raise ValueError("行候选几何不在样本网格内")
            if (
                candidate.roi.y1 - candidate.roi.y0 != self.settings.crop_height
                or not candidate.roi.y0 <= candidate.peak_y < candidate.roi.y1
            ):
                raise ValueError("候选高度/峰位置不一致")
            strength = candidate.lane_snr
            if len(strength) != self.settings.lane_count or any(
                not isfinite(v) or v < 0 for v in strength
            ):
                raise ValueError("候选泳道评分无效")
            if (
                candidate.detected_lanes
                != tuple(i + 1 for i, v in enumerate(strength) if v >= self.settings.min_snr)
                or candidate.weak_lanes
                != tuple(i + 1 for i, v in enumerate(strength) if 2 <= v < self.settings.min_snr)
                or candidate.possible_empty_lanes
                != tuple(i + 1 for i, v in enumerate(strength) if v < 2)
            ):
                raise ValueError("候选强弱/缺信号状态不一致")
        if result.sample_region is not None:
            region, membrane = result.sample_region, result.membrane
            if membrane is None or not (
                membrane.x0 <= region.x0 < region.x1 <= membrane.x1
                and region.y0 == membrane.y0
                and region.y1 == membrane.y1
            ):
                raise ValueError("样本范围必须在膜范围内")
            if region.width < self.settings.lane_count:
                raise ValueError("样本范围不足以保留固定泳道数")
            if self.settings.left_marker:
                marker = result.marker
                if marker is None or (marker.x0, marker.x1, marker.y0, marker.y1) != (
                    membrane.x0,
                    region.x0,
                    membrane.y0,
                    membrane.y1,
                ):
                    raise ValueError("左 Marker 与样本范围不一致")
            elif result.marker is not None:
                raise ValueError("未声明左 Marker，不能带有排除区域")
        elif result.marker is not None:
            raise ValueError("Marker 建议缺少样本范围")
        return self


class WBReviewProject(WBFigureProject):
    schema_version: int = Field(default=2, ge=2, le=2)
    suggestions: tuple[CropSuggestion, ...] = Field(default=(), max_length=512)

    @model_validator(mode="after")
    def sources_match(self) -> "WBReviewProject":
        rows = {row.row_id: row for row in self.rows}
        if len({s.row_id for s in self.suggestions}) != len(self.suggestions):
            raise ValueError("同一行不能保存重复当前建议")
        for suggestion in self.suggestions:
            row = rows.get(suggestion.row_id)
            if row is None or row.source is None or row.source.sha256 != suggestion.source_sha256:
                raise ValueError("建议与项目原图身份不一致")
            if suggestion.source_revision > self.revision:
                raise ValueError("建议不能来自未来修订")
            if suggestion.result is not None and (
                suggestion.result.width != row.width or suggestion.result.height != row.height
            ):
                raise ValueError("建议与原图尺寸不一致")
        return self


def read_figure_project(data: bytes) -> WBFigureProject:
    if len(data) > 16 * 1024 * 1024:
        raise ValueError("项目超出大小预算")
    raw: object = json.loads(data)
    if isinstance(raw, dict):
        version = cast(dict[str, object], raw).get("schema_version")
        if type(version) is int and version == 7:
            from wb_tool.application.laboratory_layout import WBLayoutProject

            return WBLayoutProject.from_bytes(data)
        if type(version) is int and version == 6:
            from wb_tool.application.project_restore import WBRestoredProject

            return WBRestoredProject.from_bytes(data)
        if type(version) is int and version == 5:
            from wb_tool.application.project_normalization import WBNormalizedProject

            return WBNormalizedProject.from_bytes(data)
        if type(version) is int and version == 4:
            from wb_tool.application.project_ocr import WBProjectOCR

            return WBProjectOCR.from_bytes(data)
        if type(version) is int and version == 3:
            from wb_tool.application.project_analysis import WBAnalysisProject

            return WBAnalysisProject.from_bytes(data)
        if type(version) is int and version == 2:
            return WBReviewProject.from_bytes(data)
    return WBFigureProject.from_bytes(data)


def project_with_suggestions(
    project: WBFigureProject, suggestions: tuple[CropSuggestion, ...]
) -> WBReviewProject:
    if isinstance(project, WBReviewProject):
        fields = {name: getattr(project, name) for name in type(project).model_fields}
        fields["suggestions"] = suggestions
        return type(project).model_validate(fields)
    return WBReviewProject(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        rows=project.rows,
        figure_order=project.figure_order,
        template=project.template,
        suggestions=suggestions,
    )


def record_crop_suggestion(project: WBFigureProject, suggestion: CropSuggestion) -> WBReviewProject:
    previous = project.suggestions if isinstance(project, WBReviewProject) else ()
    return project_with_suggestions(
        project, (*(s for s in previous if s.row_id != suggestion.row_id), suggestion)
    )


def apply_crop_suggestion(project: WBFigureProject, row_id: str, index: int) -> WBReviewProject:
    if not isinstance(project, WBReviewProject):
        raise ValueError("项目尚无自动建议")
    suggestion = next((s for s in project.suggestions if s.row_id == row_id), None)
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or suggestion is None or suggestion.result is None:
        raise ValueError("此行没有可应用的检测结果")
    if type(index) is not int or not 0 <= index < len(suggestion.result.candidates):
        raise ValueError("请选择已有候选")
    if (
        row.lane_count != suggestion.settings.lane_count
        or project.crop_height_for(row) != suggestion.settings.crop_height
    ):
        raise ValueError("泳道数或裁剪高度已改变，请重新检测")
    roi = replace(suggestion.result.candidates[index].roi, lane_id=row.row_id)
    rows = tuple(
        r.model_copy(update={"roi": roi, "reviewed": False}) if r.row_id == row_id else r
        for r in project.rows
    )
    updated = project.model_copy(update={"rows": rows})
    return record_crop_suggestion(updated, suggestion.model_copy(update={"selected_index": index}))
