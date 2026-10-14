"""Analyze immutable manual annotations without GUI or concrete file adapters."""

from collections.abc import Callable
from dataclasses import dataclass
from string import hexdigits
from typing import Literal, Protocol

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.lanes import LaneProfiles, LaneROI, Polarity, compute_lane_profiles
from wb_tool.domain.quantify import (
    BandBounds,
    Baseline,
    ProfileMeasurement,
    QuantificationError,
    integrate_profile,
)


class AnalysisError(ValueError):
    """Request or source cannot be analyzed as specified."""


class AnalysisCancelled(Exception):
    """No completed result is returned after cancellation."""


class QuantitativeImage(Protocol):
    @property
    def sha256(self) -> str: ...

    @property
    def pixels(self) -> NDArray[np.uint8 | np.uint16]: ...

    @property
    def conversion(self) -> str | None: ...


@dataclass(frozen=True, slots=True)
class BandAnnotation:
    band_id: str
    bounds: BandBounds | None
    baseline: Baseline | None = None
    included: bool = True

    def __post_init__(self) -> None:
        if not self.band_id.strip() or type(self.included) is not bool:
            raise AnalysisError("条带须有稳定身份和明确包含状态")
        if self.bounds is None and self.baseline is not None:
            raise AnalysisError("没有条带边界时不能指定基线")


@dataclass(frozen=True, slots=True)
class LaneAnnotation:
    roi: LaneROI
    bands: tuple[BandAnnotation, ...]

    def __post_init__(self) -> None:
        if type(self.bands) is not tuple:
            raise AnalysisError("条带标注须为不可变元组")
        if len({band.band_id for band in self.bands}) != len(self.bands):
            raise AnalysisError("同一泳道的条带身份不能重复")


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    source_sha256: str
    revision: int
    polarity: Polarity
    lanes: tuple[LaneAnnotation, ...]

    def __post_init__(self) -> None:
        if len(self.source_sha256) != 64 or any(c not in hexdigits for c in self.source_sha256):
            raise AnalysisError("输入来源摘要须为 SHA256")
        if type(self.revision) is not int or self.revision < 0:
            raise AnalysisError("草稿修订须为非负整数")
        if self.polarity not in ("dark", "light"):
            raise AnalysisError("须显式声明 dark/light 极性")
        if type(self.lanes) is not tuple or not self.lanes:
            raise AnalysisError("至少提供一个泳道，且使用不可变元组")
        if len({lane.roi.lane_id for lane in self.lanes}) != len(self.lanes):
            raise AnalysisError("泳道身份不能重复")


BandStatus = Literal["valid", "quality_review", "invalid", "excluded", "not_detected"]


@dataclass(frozen=True, slots=True)
class BandAnalysis:
    annotation: BandAnnotation
    status: BandStatus
    measurement: ProfileMeasurement | None = None
    reason: str | None = None
    quality_flags: tuple[str, ...] = ()

    @property
    def signal(self) -> float | None:
        """Only measurements with valid status may enter ratios or result columns."""
        return self.measurement.signal if self.status == "valid" and self.measurement else None


@dataclass(frozen=True, slots=True)
class LaneAnalysis:
    roi: LaneROI
    profiles: LaneProfiles | None
    bands: tuple[BandAnalysis, ...]
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    request: AnalysisRequest
    bit_depth: int
    source_conversion: str | None
    lanes: tuple[LaneAnalysis, ...]
    algorithm_id: Literal["profile_integral@1"] = "profile_integral@1"
    quality_policy: Literal["dtype_limits_review@1"] = "dtype_limits_review@1"
    schema_version: Literal[1] = 1


def _check_cancel(cancelled: Callable[[], bool] | None) -> None:
    if cancelled is not None and cancelled():
        raise AnalysisCancelled("分析已取消，不返回完成结果")


def analyze_annotations(
    image: QuantitativeImage,
    request: AnalysisRequest,
    *,
    cancelled: Callable[[], bool] | None = None,
) -> AnalysisResult:
    """Evaluate each lane independently; source mismatch and cancellation abort all.

    Rail pixels are a review prompt, not proof of biological saturation. Raw
    integration remains available for inspection, but is not a valid signal.
    """
    _check_cancel(cancelled)
    if image.sha256.lower() != request.source_sha256.lower():
        raise AnalysisError("当前图像与标注来源摘要不一致")
    lanes: list[LaneAnalysis] = []
    for annotation in request.lanes:
        _check_cancel(cancelled)
        try:
            profiles = compute_lane_profiles(image.pixels, annotation.roi, request.polarity)
        except QuantificationError as exc:
            bands = tuple(
                BandAnalysis(band, "invalid" if band.included else "excluded", reason=str(exc))
                for band in annotation.bands
            )
            lanes.append(LaneAnalysis(annotation.roi, None, bands, str(exc)))
            continue
        results: list[BandAnalysis] = []
        for band in annotation.bands:
            _check_cancel(cancelled)
            if not band.included:
                results.append(BandAnalysis(band, "excluded", reason="该条带已排除"))
                continue
            if band.bounds is None:
                results.append(BandAnalysis(band, "not_detected", reason="尚未建立条带边界"))
                continue
            try:
                if (
                    band.baseline is not None
                    and max(band.baseline.left_value, band.baseline.right_value)
                    > profiles.dtype_max
                ):
                    raise QuantificationError("人工基线超出原始图像位深范围")
                measurement = integrate_profile(profiles.quantitative, band.bounds, band.baseline)
            except QuantificationError as exc:
                results.append(BandAnalysis(band, "invalid", reason=str(exc)))
                continue
            roi = annotation.roi
            region = image.pixels[
                roi.y0 + band.bounds.left : roi.y0 + band.bounds.right + 1, roi.x0 : roi.x1
            ]
            flags: list[str] = []
            if np.any(region == 0):
                flags.append("dtype_min_present")
            if np.any(region == profiles.dtype_max):
                flags.append("dtype_max_present")
            results.append(
                BandAnalysis(
                    band,
                    "quality_review" if flags else "valid",
                    measurement,
                    "条带区域含位深上下限像素，须核对曝光和饱和" if flags else None,
                    tuple(flags),
                )
            )
        lanes.append(LaneAnalysis(annotation.roi, profiles, tuple(results)))
    _check_cancel(cancelled)
    return AnalysisResult(request, image.pixels.dtype.itemsize * 8, image.conversion, tuple(lanes))
