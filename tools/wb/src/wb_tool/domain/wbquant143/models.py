from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .errors import ROIValidationError


@dataclass(frozen=True, slots=True)
class LaneROI:
    lane_id: int
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0

    @property
    def area(self) -> int:
        return self.width * self.height

    def validate(self, image_width: int, image_height: int) -> None:
        values = (self.lane_id, self.x0, self.y0, self.x1, self.y1)
        if any(isinstance(v, bool) or not isinstance(v, int) for v in values):
            raise ROIValidationError("ROI lane_id and coordinates must be integers")
        if self.lane_id < 1:
            raise ROIValidationError("lane_id must be a positive integer")
        if not (0 <= self.x0 < self.x1 <= image_width):
            raise ROIValidationError(
                f"lane {self.lane_id} x coordinates are out of bounds: [{self.x0}:{self.x1}]"
            )
        if not (0 <= self.y0 < self.y1 <= image_height):
            raise ROIValidationError(
                f"lane {self.lane_id} y coordinates are out of bounds: [{self.y0}:{self.y1}]"
            )
        if self.area < 25:
            raise ROIValidationError(f"lane {self.lane_id} area must be at least 25 px²")

    def moved(self, dx: int, dy: int, image_width: int, image_height: int) -> "LaneROI":
        moved = LaneROI(self.lane_id, self.x0 + dx, self.y0 + dy, self.x1 + dx, self.y1 + dy)
        moved.validate(image_width, image_height)
        return moved

    def as_dict(self) -> dict[str, int]:
        return {
            "lane_id": self.lane_id,
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
        }


@dataclass(frozen=True, slots=True)
class ROIInsets:
    top: int = 0
    right: int = 0
    bottom: int = 0
    left: int = 0
    source: str = "none"

    def validate(self, roi: LaneROI) -> None:
        values = (self.top, self.right, self.bottom, self.left)
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
            raise ROIValidationError("ROI insets must be non-negative integers")
        if self.left + self.right >= roi.width or self.top + self.bottom >= roi.height:
            raise ROIValidationError("ROI insets leave no usable analysis area")

    def apply(self, roi: LaneROI) -> LaneROI:
        self.validate(roi)
        return LaneROI(
            roi.lane_id,
            roi.x0 + self.left,
            roi.y0 + self.top,
            roi.x1 - self.right,
            roi.y1 - self.bottom,
        )

    def as_dict(self) -> dict[str, int | str]:
        return {
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "left": self.left,
            "source": self.source,
        }


@dataclass(slots=True)
class LoadedImage:
    path: Path
    raw: np.ndarray
    raw_float: np.ndarray
    dtype_max: int
    bit_depth: int
    min_count: int
    max_count: int
    min_fraction: float
    max_fraction: float
    source_shape: tuple[int, ...] | None = None
    conversion: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def shape(self) -> tuple[int, int]:
        return int(self.raw.shape[0]), int(self.raw.shape[1])


@dataclass(slots=True)
class BandResult:
    band_index: int
    peak_y_relative: int
    peak_y_absolute: int
    height: float
    prominence: float
    width: float
    left: int
    right: int
    left_absolute: int
    right_absolute: int
    boundary_source: str
    status: str
    area_px: int | None
    background: float | None
    signal: float | None
    band_id: str = ""
    auto_left: int | None = None
    auto_right: int | None = None
    auto_baseline_left_value: float | None = None
    auto_baseline_right_value: float | None = None
    baseline_left_value: float | None = None
    baseline_right_value: float | None = None
    baseline_source: str = "auto"
    detection_source: str = "auto"
    included: bool = True
    review_status: str = "draft"
    excluded_background_signal: float = 0.0
    boundary_method: str = "unknown"
    boundary_confidence: float | None = None
    background_slope: float | None = None
    edge_artifact: dict[str, Any] = field(default_factory=dict)
    manual_reason: str | None = None
    signal_normalized: float | None = None
    normalization: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "band_index": self.band_index,
            "peak_y_relative": self.peak_y_relative,
            "peak_y_absolute": self.peak_y_absolute,
            "height": self.height,
            "prominence": self.prominence,
            "width": self.width,
            "left": self.left,
            "right": self.right,
            "left_absolute": self.left_absolute,
            "right_absolute": self.right_absolute,
            "boundary_source": self.boundary_source,
            "status": self.status,
            "area_px": self.area_px,
            "background": self.background,
            "signal": self.signal,
            "band_id": self.band_id,
            "auto_left": self.auto_left,
            "auto_right": self.auto_right,
            "auto_baseline_left_value": self.auto_baseline_left_value,
            "auto_baseline_right_value": self.auto_baseline_right_value,
            "baseline_left_value": self.baseline_left_value,
            "baseline_right_value": self.baseline_right_value,
            "baseline_source": self.baseline_source,
            "detection_source": self.detection_source,
            "included": self.included,
            "review_status": self.review_status,
            "excluded_background_signal": self.excluded_background_signal,
            "boundary_method": self.boundary_method,
            "boundary_confidence": self.boundary_confidence,
            "background_slope": self.background_slope,
            "edge_artifact": self.edge_artifact,
            "manual_reason": self.manual_reason,
            "signal_normalized": self.signal_normalized,
            "normalization": self.normalization,
            "warnings": self.warnings,
        }


@dataclass(slots=True)
class LaneResult:
    roi: LaneROI
    raw_profile: np.ndarray
    profile: np.ndarray
    robust_range: float
    prominence_threshold: float
    bands: list[BandResult]
    status: str
    warnings: list[str] = field(default_factory=list)
    effective_roi: LaneROI | None = None
    insets: ROIInsets = field(default_factory=ROIInsets)
    border_detection: dict[str, Any] = field(default_factory=dict)
    detection_profile: np.ndarray | None = None
    weak_candidates: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ImageResult:
    image: LoadedImage
    identifier: str
    lanes: list[LaneResult]
    config: dict[str, float | int]
    reference_lane_id: int | None
    status: str
    warnings: list[str] = field(default_factory=list)
    review_status: str = "draft"
    revision_log: list[dict[str, Any]] = field(default_factory=list)

    @property
    def band_count(self) -> int:
        return sum(1 for lane in self.lanes for band in lane.bands if band.included)
