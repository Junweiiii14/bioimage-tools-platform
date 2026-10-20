"""Automatic geometry policy v1; private detection arrays never enter integration."""

from collections.abc import Callable
from dataclasses import dataclass
from math import ceil
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.crop_detection import (
    CropCandidate,
    CropDetection,
    CropDetectionSettings,
    check_detection_cancelled,
    detection_membrane,
    detection_noise,
    detection_segments,
    smooth_detection,
)
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI, Polarity

QuantPolicy = Literal[
    "legacy_bounds@1", "wbquant_1_4_3@1", "background_support@1", "anchored_background@1"
]

CropPolicy = Literal["legacy_fixed_height@1", "lane_ratio@1", "source_geometry@2"]


def resize_crop_for_lane_count(
    crop: LaneROI, lane_count: int, image_width: int, image_height: int
) -> LaneROI:
    """Keep original-pixel height and centre; reject clipping, round half pixels up."""
    if type(lane_count) is not int or not 1 <= lane_count <= 96:
        raise ValueError("泳道数须为1–96")
    if any(type(v) is not int or v < 1 for v in (image_width, image_height)):
        raise ValueError("原图尺寸须为正整数")
    if crop.x1 > image_width or crop.y1 > image_height:
        raise ValueError("裁剪框超出原图")
    height = crop.y1 - crop.y0
    width = (5 * lane_count * height + 2) // 4
    if width < lane_count:
        raise ValueError("裁剪框宽度不足")
    x0 = (crop.x0 + crop.x1 - width + 1) // 2
    if x0 < 0 or x0 + width > image_width:
        raise ValueError("保持当前高度和中心无法容纳新的泳道数，请先移动或缩小裁剪框")
    return LaneROI(crop.lane_id, x0, crop.y0, x0 + width, crop.y1)


@dataclass(frozen=True)
class AutoWBSettings:
    polarity: Polarity = "dark"
    lane_count: int | None = None
    crop_height: int = 60
    left_marker: Literal["auto", "exclude", "include"] = "auto"
    min_snr: float = 4.0
    crop_policy: CropPolicy = "legacy_fixed_height@1"
    quant_policy: QuantPolicy = "legacy_bounds@1"

    def __post_init__(self) -> None:
        if self.quant_policy not in (
            "legacy_bounds@1",
            "wbquant_1_4_3@1",
            "background_support@1",
            "anchored_background@1",
        ):
            raise ValueError("未知定量策略")
        if self.crop_policy not in ("legacy_fixed_height@1", "lane_ratio@1", "source_geometry@2"):
            raise ValueError("裁剪比例策略无效")
        CropDetectionSettings(
            self.lane_count or 1, self.crop_height, self.polarity, min_snr=self.min_snr
        )
        if self.lane_count is not None and (
            type(self.lane_count) is not int or self.lane_count < 1
        ):
            raise ValueError("泳道数覆盖值须为1–96")
        if self.left_marker not in ("auto", "exclude", "include"):
            raise ValueError("Marker 策略无效")


def detect_automatic_geometry(
    pixels: NDArray[np.uint8 | np.uint16],
    settings: AutoWBSettings,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> CropDetection:
    """Estimate equal-spacing sample slots, retaining inferred internal empty slots.

    No biological identity is inferred. Isolated left-edge signal is withheld;
    this avoids promoting a lone marker into a complete sample result.
    """
    if pixels.ndim != 2 or pixels.dtype not in (np.dtype("uint8"), np.dtype("uint16")):
        raise ValueError("自动检测需要原始二维 uint8/uint16 灰度")
    h, w = pixels.shape
    if h < 3 or w < 3 or h * w > 16_000_000:
        raise ValueError("自动检测尺寸超出预算")
    check_detection_cancelled(cancelled)
    if settings.crop_policy == "source_geometry@2":
        from wb_tool.domain.source_geometry import detect_source_geometry

        return detect_source_geometry(pixels, settings, cancelled)
    crop_height = min(settings.crop_height, h)
    initial = CropDetectionSettings(
        settings.lane_count or 1,
        crop_height,
        settings.polarity,
        left_marker=False,
        min_snr=settings.min_snr,
    )
    membrane, membrane_flags = detection_membrane(pixels, initial, cancelled)
    flags = list(membrane_flags)
    if membrane is None:
        membrane = LaneROI("membrane", 0, 0, w, h)
        flags.append("full_image_detection_fallback")
    height = membrane.y1 - membrane.y0
    crop_height = min(crop_height, height)
    raw = pixels[membrane.y0 : membrane.y1, membrane.x0 : membrane.x1].astype(np.float64)
    background = smooth_detection(raw, max(2, crop_height))
    signal = background - raw if settings.polarity == "dark" else raw - background
    signal = smooth_detection(signal, 1)
    noise = detection_noise(raw)
    guard = min(max(2, crop_height // 4), height // 8) if membrane_flags else 0
    interior = signal[guard : height - guard] if guard else signal
    energy = np.quantile(np.maximum(interior, 0), 0.95, axis=0)
    energy = smooth_detection(energy, max(1, membrane.width // 200))
    edge = max(1, membrane.width // 100)
    energy[:edge] = 0
    energy[-edge:] = 0
    choices: list[tuple[list[tuple[int, int]], list[float]]] = []
    for fraction in (0.35, 0.5, 0.65, 0.8, 0.9):
        threshold = max(settings.min_snr * noise, float(energy.max()) * fraction)
        spans = [
            (a, b)
            for a, b in detection_segments(energy > threshold)
            if b - a >= max(2, membrane.width // 40)
        ]
        points = [float(np.average(np.arange(a, b), weights=energy[a:b])) for a, b in spans]
        if len(points) >= 3:
            gaps = np.diff(points)
            regular = float(np.std(gaps) / np.mean(gaps)) < 0.15
            substantial = min(b - a for a, b in spans) >= float(np.median(gaps)) * 0.4
            if regular and substantial:
                choices.append((spans, points))
    if choices:
        intervals, centers = max(choices, key=lambda pair: len(pair[1]))
    else:
        threshold = max(settings.min_snr * noise, float(energy.max()) * 0.5)
        intervals = [
            (a, b)
            for a, b in detection_segments(energy > threshold)
            if b - a >= max(2, membrane.width // 40)
        ]
        centers = [float(np.average(np.arange(a, b), weights=energy[a:b])) for a, b in intervals]
    peaks_y = [int(np.argmax(interior[:, a:b].mean(axis=1))) + guard for a, b in intervals]
    marker_end: int | None = None
    if centers:
        marker = settings.left_marker == "exclude"
        if settings.left_marker == "auto" and len(centers) >= 3:
            other_y = float(np.median(peaks_y[1:]))
            marker = centers[0] < membrane.width * 0.28 and abs(peaks_y[0] - other_y) > max(
                4, crop_height * 0.15
            )
        if marker:
            marker_end = (
                int(round((centers[0] + centers[1]) / 2)) if len(centers) > 1 else intervals[0][1]
            )
            centers, intervals, peaks_y = centers[1:], intervals[1:], peaks_y[1:]
            flags.append("left_marker_geometry_candidate")
    if centers and max(centers) < membrane.width * 0.3 and settings.left_marker != "include":
        centers = []
        flags.append("isolated_left_signal_not_sample")
    if not centers:
        return CropDetection(
            initial, w, h, membrane, None, None, (), tuple([*flags, "no_sample_bands"])
        )
    if len(centers) > 1:
        pitch = float(np.median(np.diff(centers)))
        inferred = int(round((centers[-1] - centers[0]) / pitch)) + 1
    else:
        pitch = max(float(intervals[0][1] - intervals[0][0]) * 1.5, 4.0)
        inferred = 1
    count = settings.lane_count or min(96, inferred)
    if settings.lane_count and len(centers) > 1:
        pitch = (centers[-1] - centers[0]) / max(1, count - 1)
    x0 = max(marker_end or 0, int(round(centers[0] - pitch / 2)))
    x1 = min(membrane.width, int(round(centers[-1] + pitch / 2)))
    if x1 - x0 < count:
        return CropDetection(
            initial, w, h, membrane, None, None, (), tuple([*flags, "insufficient_lane_width"])
        )
    region = LaneROI("samples", membrane.x0 + x0, membrane.y0, membrane.x0 + x1, membrane.y1)
    marker_roi = (
        LaneROI("marker", membrane.x0, membrane.y0, region.x0, membrane.y1) if marker_end else None
    )
    chosen = CropDetectionSettings(
        count,
        crop_height,
        settings.polarity,
        left_marker=bool(marker_end),
        min_snr=settings.min_snr,
        membrane_hint=membrane,
    )
    profiles: list[NDArray[np.float64]] = []
    for lane in fixed_lane_grid(region, count):
        p = signal[:, lane.x0 - membrane.x0 : lane.x1 - membrane.x0].mean(axis=1)
        profiles.append(np.maximum(p, 0) / max(detection_noise(p), noise / np.sqrt(lane.width)))
    snr = np.stack(profiles, axis=1)
    active = (snr >= settings.min_snr).sum(axis=1) >= max(1, int(np.ceil(count * 0.4)))
    if guard:
        active[:guard] = False
        active[-guard:] = False
    groups = detection_segments(active)
    merged: list[tuple[int, int]] = []
    for a, b in groups:
        if merged and a - merged[-1][1] <= max(1, crop_height // 12):
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    candidates: list[CropCandidate] = []
    for a, b in merged:
        check_detection_cancelled(cancelled)
        if b - a < 2:
            continue
        score = np.minimum(snr[a:b], 20).sum(axis=1)
        peak = a + int(round(float(np.average(np.arange(b - a), weights=score))))
        y0 = max(0, min(peak - crop_height // 2, height - crop_height))
        strengths = tuple(float(v) for v in snr[a:b].max(axis=0))
        roi = LaneROI(
            "candidate", region.x0, membrane.y0 + y0, region.x1, membrane.y0 + y0 + crop_height
        )
        if settings.crop_policy == "lane_ratio@1":
            # Preserve detected horizontal coverage and the full active band height.
            # This changes coordinates only; source pixels are never resampled.
            ratio_height = max(2, ceil(region.width * 4 / (5 * count)), b - a + 4)
            ratio_width = (5 * count * ratio_height + 2) // 4
            if ratio_width > w or ratio_height > h:
                flags.append("ratio_crop_exceeds_source")
                continue
            ratio_x0 = max(0, min((region.x0 + region.x1 - ratio_width + 1) // 2, w - ratio_width))
            ratio_y0 = max(0, min(membrane.y0 + peak - ratio_height // 2, h - ratio_height))
            if ratio_y0 > membrane.y0 + a or ratio_y0 + ratio_height < membrane.y0 + b:
                flags.append("ratio_crop_cannot_cover_band")
                continue
            roi = LaneROI(
                "candidate", ratio_x0, ratio_y0, ratio_x0 + ratio_width, ratio_y0 + ratio_height
            )
        candidates.append(
            CropCandidate(
                roi,
                membrane.y0 + peak,
                strengths,
                tuple(i + 1 for i, v in enumerate(strengths) if v >= settings.min_snr),
                tuple(i + 1 for i, v in enumerate(strengths) if 2 <= v < settings.min_snr),
                tuple(i + 1 for i, v in enumerate(strengths) if v < 2),
                ("automatic_geometry_unreviewed",),
            )
        )
    candidates.sort(
        key=lambda c: (-len(c.detected_lanes), -sum(min(v, 20) for v in c.lane_snr), c.peak_y)
    )
    if settings.crop_policy == "lane_ratio@1":
        flags.append("crop_policy:lane_ratio@1")
    flags.extend(
        (
            "automatic_lane_count" if settings.lane_count is None else "explicit_lane_count",
            "automatic_geometry_unreviewed",
        )
    )
    if len(candidates) > 1:
        flags.append("multiple_candidate_rows")
    if inferred != len(centers):
        flags.append("inferred_internal_empty_slots")
    if not candidates:
        flags.append("no_sample_bands")
    return CropDetection(
        chosen, w, h, membrane, marker_roi, region, tuple(candidates[:8]), tuple(flags)
    )
