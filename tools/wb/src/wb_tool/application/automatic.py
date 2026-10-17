"""Versioned automatic proposals and persistent machine provenance, never human review."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from wb_tool.application.analysis import (
    AnalysisRequest,
    BandAnnotation,
    LaneAnnotation,
    QuantitativeImage,
)
from wb_tool.application.document import DocumentIO
from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.laboratory_layout import (
    DisplayFrame,
    WBLayoutProject,
    preserve_automatic_composition,
    with_figure_layout,
)
from wb_tool.application.project_analysis import ProjectRowAnalysis
from wb_tool.domain.automatic import AutoWBSettings, QuantPolicy, detect_automatic_geometry
from wb_tool.domain.crop_detection import (
    CropDetection,
    check_detection_cancelled,
    detection_noise,
    smooth_detection,
)
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI, Polarity, compute_lane_profiles
from wb_tool.domain.quantify import BandBounds


@dataclass(frozen=True)
class AutomaticWBResult:
    source_sha256: str
    source_revision: int
    row_id: str
    settings: AutoWBSettings
    detection: CropDetection
    requests: tuple[AnalysisRequest, ...]
    warnings: tuple[str, ...]
    algorithm_id: Literal["automatic_wb_proposals@1", "automatic_wb_proposals@2"] = (
        "automatic_wb_proposals@1"
    )

    @property
    def estimated_lane_count(self) -> int:
        return self.detection.settings.lane_count


def suggest_analysis_for_crop(
    image: QuantitativeImage,
    *,
    crop: LaneROI,
    lane_count: int,
    revision: int,
    polarity: Polarity = "dark",
    empty_lanes: tuple[int, ...] = (),
    min_snr: float = 4.0,
    quant_policy: QuantPolicy = "legacy_bounds@1",
    lane_rois: tuple[LaneROI, ...] = (),
    cancelled: Callable[[], bool] = lambda: False,
) -> AnalysisRequest:
    """Suggest closed bounds on detection copies; measurement uses untouched original pixels.

    Policy: smooth by radius 1, linear edge background, dominant connected peak,
    expand to 2% amplitude / adjacent-difference noise. Weak/flat lanes stay undetected.
    """
    AutoWBSettings(polarity=polarity, lane_count=lane_count, min_snr=min_snr)
    lanes: list[LaneAnnotation] = []
    geometry = (
        tuple(replace(roi, lane_id=f"{crop.lane_id}:{i:02d}") for i, roi in enumerate(lane_rois, 1))
        if lane_rois
        else fixed_lane_grid(crop, lane_count)
    )
    if len(geometry) != lane_count:
        raise ValueError("检测泳道数与请求不一致")
    if quant_policy == "wbquant_1_4_3@1":
        from wb_tool.domain.quant_supervision import propose_quant_lanes

        proposals = propose_quant_lanes(image.pixels, geometry, polarity)
        for index, proposal in enumerate(proposals, 1):
            check_detection_cancelled(cancelled)
            lanes.append(
                LaneAnnotation(
                    proposal.roi,
                    tuple(
                        BandAnnotation(
                            "target" if number == 1 else f"target-{number}",
                            band.bounds,
                            band.baseline,
                            index not in empty_lanes,
                            band.notes,
                        )
                        for number, band in enumerate(proposal.bands, 1)
                    ),
                )
            )
        return AnalysisRequest(
            image.sha256, revision, polarity, tuple(lanes), "independent_lanes@1", quant_policy
        )
    for index, roi in enumerate(geometry, 1):
        check_detection_cancelled(cancelled)
        profile = np.asarray(compute_lane_profiles(image.pixels, roi, polarity).quantitative)
        smooth = smooth_detection(profile, 1)
        baseline = np.linspace(float(smooth[0]), float(smooth[-1]), len(smooth))
        residual = smooth - baseline
        peak = int(np.argmax(residual))
        amplitude = float(residual[peak])
        sigma = detection_noise(profile)
        bounds = None
        if amplitude >= min_snr * sigma and 0 < peak < len(profile) - 1:
            floor = max(sigma, amplitude * 0.02)
            left = right = peak
            while left > 0 and residual[left] > floor:
                left -= 1
            while right < len(profile) - 1 and residual[right] > floor:
                right += 1
            if left < right:
                bounds = BandBounds(left, right)
        lanes.append(
            LaneAnnotation(
                roi, (BandAnnotation("target", bounds, included=index not in empty_lanes),)
            )
        )
    return AnalysisRequest(
        image.sha256,
        revision,
        polarity,
        tuple(lanes),
        "independent_lanes@1" if lane_rois else "fixed_grid@1",
        quant_policy,
    )


def suggest_automatic_wb(
    image: QuantitativeImage,
    *,
    row_id: str,
    revision: int,
    settings: AutoWBSettings | None = None,
    cancelled: Callable[[], bool] = lambda: False,
) -> AutomaticWBResult:
    settings = settings or AutoWBSettings()
    # Validate identity/revision before potentially expensive detection.
    AnalysisRequest(
        image.sha256,
        revision,
        settings.polarity,
        (LaneAnnotation(LaneROI(row_id, 0, 0, 1, 1), ()),),
    )
    detection = detect_automatic_geometry(image.pixels, settings, cancelled=cancelled)
    requests = tuple(
        suggest_analysis_for_crop(
            image,
            crop=replace(c.roi, lane_id=row_id),
            lane_count=detection.settings.lane_count,
            revision=revision,
            polarity=settings.polarity,
            min_snr=settings.min_snr,
            quant_policy=settings.quant_policy,
            lane_rois=c.lane_rois,
            cancelled=cancelled,
        )
        for c in detection.candidates
    )
    return AutomaticWBResult(
        image.sha256,
        revision,
        row_id,
        settings,
        detection,
        requests,
        (*detection.flags, "automatic_bounds_unreviewed"),
        "automatic_wb_proposals@2"
        if settings.crop_policy == "source_geometry@2"
        else "automatic_wb_proposals@1",
    )


class AutomaticRowEvidence(DocumentIO):
    row_id: str = Field(min_length=1, max_length=80)
    source_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    source_revision: int = Field(ge=0)
    crop: LaneROI
    lane_count: int = Field(ge=1, le=96)
    empty_lanes: tuple[int, ...] = ()
    settings: AutoWBSettings
    request: AnalysisRequest
    warnings: tuple[str, ...] = Field(default=(), max_length=64)
    algorithm_id: Literal["automatic_wb_proposals@1", "automatic_wb_proposals@2"] = (
        "automatic_wb_proposals@1"
    )
    human_reviewed: Literal[False] = False

    @model_validator(mode="after")
    def coherent(self) -> "AutomaticRowEvidence":
        if self.crop.lane_id != self.row_id or self.request.source_sha256 != self.source_sha256:
            raise ValueError("自动建议的来源/行身份不一致")
        ProjectRowAnalysis(
            row_id=self.row_id, crop=self.crop, empty_lanes=self.empty_lanes, request=self.request
        )
        if len(self.request.lanes) != self.lane_count:
            raise ValueError("自动建议的泳道数不一致")
        return self


class WBAutomaticProject(WBLayoutProject):
    schema_version: int = Field(default=8, ge=8, le=8)
    automatic_rows: tuple[AutomaticRowEvidence, ...] = Field(default=(), max_length=512)

    @model_validator(mode="after")
    def automatic_identity(self) -> "WBAutomaticProject":
        if len({e.row_id for e in self.automatic_rows}) != len(self.automatic_rows):
            raise ValueError("自动建议身份重复")
        rows = {r.row_id: r for r in self.rows}
        for evidence in self.automatic_rows:
            row = rows.get(evidence.row_id)
            if row is None or row.source is None or row.source.sha256 != evidence.source_sha256:
                raise ValueError("自动建议来源不属于项目")
            if evidence.source_revision > self.revision:
                raise ValueError("自动建议不能来自未来修订")
        return self


def row_is_ready(project: WBFigureProject, row: FigureRow) -> bool:
    """Human confirmation OR exact machine provenance; stale geometry is never authorized."""
    if row.reviewed:
        return True
    if not isinstance(project, WBAutomaticProject) or row.source is None:
        return False
    for evidence in project.automatic_rows:
        if evidence.row_id != row.row_id:
            continue
        plan = next((p for p in project.analyses if p.row_id == row.row_id), None)
        return bool(
            row.roi == evidence.crop
            and row.source.sha256 == evidence.source_sha256
            and row.lane_count == evidence.lane_count
            and row.empty_lanes == evidence.empty_lanes
            and plan is not None
            and plan.crop == row.roi
            and replace(plan.request, revision=0) == replace(evidence.request, revision=0)
        )
    return False


def install_automatic_result(
    project: WBFigureProject,
    row_id: str,
    result: AutomaticWBResult,
    candidate_index: int = 0,
) -> WBAutomaticProject:
    if result.row_id != row_id or result.source_revision != project.revision:
        raise ValueError("自动建议已过期或行身份不一致")
    if not 0 <= candidate_index < len(result.requests):
        raise ValueError("未检测到可应用的样本条带")
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or row.source is None or row.source.sha256 != result.source_sha256:
        raise ValueError("自动建议来源已改变")
    crop = replace(result.detection.candidates[candidate_index].roi, lane_id=row_id)
    request = result.requests[candidate_index]
    count = len(request.lanes)
    if any(n > count for n in row.empty_lanes):
        raise ValueError("自动泳道数与已标记空位不一致，请保留泳道数后重试")
    empty = row.empty_lanes
    request = replace(
        request,
        lanes=tuple(
            replace(lane, bands=(replace(lane.bands[0], included=i not in empty),))
            for i, lane in enumerate(request.lanes, 1)
        ),
    )
    installed = install_automatic_request(
        project, row_id, crop, request, result.settings, result.warnings, empty
    )
    frame = result.detection.candidates[candidate_index].display_frame
    if frame is not None:
        display = DisplayFrame(
            center_x=frame.center_x,
            center_y=frame.center_y,
            width=frame.width,
            height=frame.height,
            angle_degrees=frame.angle_degrees,
        )
        composition = installed.composition.model_copy(
            update={
                "slices": tuple(
                    s.model_copy(update={"display_frame": display}) if s.row_id == row_id else s
                    for s in installed.composition.slices
                )
            }
        )
        style = installed.layout_style.model_copy(
            update={"display_policy": "standard_lane_ratio@1"}
        )
        updated = with_figure_layout(installed, composition, style)
        return WBAutomaticProject.model_validate(
            {name: getattr(updated, name) for name in type(updated).model_fields}
        )
    return installed


def install_automatic_request(
    project: WBFigureProject,
    row_id: str,
    crop: LaneROI,
    request: AnalysisRequest,
    settings: AutoWBSettings,
    warnings: tuple[str, ...] = ("manually_adjusted_geometry_automatic_bounds",),
    empty_lanes: tuple[int, ...] | None = None,
) -> WBAutomaticProject:
    """Record a regenerated request after direct image manipulation, preserving its geometry."""
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if (
        row is None
        or row.source is None
        or request.source_sha256 != row.source.sha256
        or request.revision != project.revision
    ):
        raise ValueError("自动请求已过期或来源不一致")
    empty = row.empty_lanes if empty_lanes is None else empty_lanes
    count = len(request.lanes)
    changed = row.model_copy(
        update={"roi": crop, "lane_count": count, "empty_lanes": empty, "reviewed": False}
    )
    evidence = AutomaticRowEvidence(
        row_id=row_id,
        source_sha256=row.source.sha256,
        source_revision=project.revision,
        crop=crop,
        lane_count=count,
        empty_lanes=empty,
        settings=settings,
        request=request,
        warnings=warnings,
        algorithm_id="automatic_wb_proposals@2"
        if settings.crop_policy == "source_geometry@2"
        else "automatic_wb_proposals@1",
    )
    plan = ProjectRowAnalysis(row_id=row_id, crop=crop, empty_lanes=empty, request=request)
    fields = {name: getattr(project, name) for name in type(project).model_fields}
    previous = getattr(project, "automatic_rows", ())
    plans = getattr(project, "analyses", ())
    fields.update(
        schema_version=8,
        rows=tuple(changed if r.row_id == row_id else r for r in project.rows),
        automatic_rows=tuple(e for e in previous if e.row_id != row_id) + (evidence,),
        analyses=tuple(p for p in plans if p.row_id != row_id) + (plan,),
    )
    upgraded = WBAutomaticProject.model_validate(fields)
    composition = preserve_automatic_composition(upgraded, row_id)
    if (
        isinstance(project, WBLayoutProject)
        and project.composition.slices
        and composition != project.composition
    ):
        evidence = evidence.model_copy(
            update={
                "warnings": (
                    *evidence.warnings,
                    "layout_target_row_lane_count_updated_other_rows_preserved",
                )
            }
        )
        upgraded = upgraded.model_copy(
            update={
                "automatic_rows": tuple(
                    evidence if item.row_id == row_id else item for item in upgraded.automatic_rows
                )
            }
        )
    return upgraded.model_copy(update={"composition": composition})


def with_automatic_rows(
    project: WBFigureProject, automatic_rows: tuple[AutomaticRowEvidence, ...]
) -> WBAutomaticProject:
    fields = {name: getattr(project, name) for name in type(project).model_fields}
    fields.update(schema_version=8, automatic_rows=automatic_rows)
    return WBAutomaticProject.model_validate(fields)
