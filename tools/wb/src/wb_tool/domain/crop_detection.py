"""Deterministic, review-only geometry suggestions from original quantitative pixels.

All filtering happens on private float copies. These arrays and scores are never measurements.
"""

from collections.abc import Callable
from dataclasses import dataclass
from math import ceil, isfinite, sqrt
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI, Polarity

ALGORITHM = "membrane_periodic_profile_candidates@1"


@dataclass(frozen=True)
class CropDetectionSettings:
    lane_count: int
    crop_height: int
    polarity: Polarity
    left_marker: bool = True
    min_snr: float = 4.0
    membrane_hint: LaneROI | None = None
    include_membrane_edges: bool = False

    def __post_init__(self) -> None:
        if type(self.lane_count) is not int or not 1 <= self.lane_count <= 96:
            raise ValueError("候选检测泳道数须为1–96")
        if type(self.crop_height) is not int or not 2 <= self.crop_height <= 4096:
            raise ValueError("候选裁剪高度须为2–4096")
        if self.polarity not in ("dark", "light") or type(self.left_marker) is not bool:
            raise ValueError("须声明条带极性和是否包含左侧Marker")
        if type(self.include_membrane_edges) is not bool:
            raise ValueError("膜边缘候选选项必须为布尔值")
        if not isfinite(self.min_snr) or not 2 <= self.min_snr <= 12:
            raise ValueError("候选信噪阈值须为2–12")


@dataclass(frozen=True)
class CropCandidate:
    roi: LaneROI
    peak_y: int
    lane_snr: tuple[float, ...]
    detected_lanes: tuple[int, ...]
    weak_lanes: tuple[int, ...]
    possible_empty_lanes: tuple[int, ...]
    flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CropDetection:
    settings: CropDetectionSettings
    width: int
    height: int
    membrane: LaneROI | None
    marker: LaneROI | None
    sample_region: LaneROI | None
    candidates: tuple[CropCandidate, ...]
    flags: tuple[str, ...]
    algorithm_id: Literal["membrane_periodic_profile_candidates@1"] = ALGORITHM


def _check(cancelled: Callable[[], bool]) -> None:
    if cancelled():
        raise ValueError("候选检测已取消")


def _segments(mask: NDArray[np.bool_]) -> list[tuple[int, int]]:
    changes = np.diff(np.concatenate(([False], mask, [False])).astype(np.int8))
    return [
        (int(a), int(b))
        for a, b in zip(np.flatnonzero(changes == 1), np.flatnonzero(changes == -1), strict=True)
    ]


def _smooth(values: NDArray[np.float64], radius: int) -> NDArray[np.float64]:
    """Vertical box filter with edge replication, private arrays only, O(HW) memory/time."""
    padding = ((radius, radius),) + ((0, 0),) * (values.ndim - 1)
    padded = np.pad(values, padding, mode="edge")
    total = np.concatenate((np.zeros_like(padded[:1]), np.cumsum(padded, axis=0)), axis=0)
    span = 2 * radius + 1
    return (total[span:] - total[:-span]) / span


def _noise(profile: NDArray[np.float64]) -> float:
    differences = np.diff(profile, axis=0)
    if not differences.size:
        return 1.0
    median = np.median(differences)
    # Median absolute deviation of adjacent Gaussian differences / (sqrt(2)*Phi^-1(.75)).
    return max(1.0, float(np.median(np.abs(differences - median))) / 0.9538725524)


def _membrane(
    pixels: NDArray[np.uint8 | np.uint16],
    settings: CropDetectionSettings,
    cancelled: Callable[[], bool],
) -> tuple[LaneROI | None, tuple[str, ...]]:
    height, width = pixels.shape
    if settings.membrane_hint is not None:
        hint = settings.membrane_hint
        if hint.x1 > width or hint.y1 > height:
            raise ValueError("指定膜区域超出原图")
        return LaneROI("membrane", hint.x0, hint.y0, hint.x1, hint.y1), ("manual_membrane",)
    step = max(1, ceil(max(pixels.shape) / 256))
    sample = pixels[::step, ::step].astype(np.float64)
    border = np.concatenate((sample[0], sample[-1], sample[:, 0], sample[:, -1]))
    distance = np.abs(sample - np.median(border))
    maximum = float(distance.max())
    if maximum <= max(2.0, 6 * _noise(border)):
        return None, ("membrane_not_found",)
    histogram, edges = np.histogram(distance, bins=256, range=(0, maximum))
    weights = histogram.astype(np.float64) / distance.size
    centres = (edges[1:] + edges[:-1]) / 2
    fraction = np.cumsum(weights)
    mean = np.cumsum(weights * centres)
    between = np.zeros(256, dtype=np.float64)
    valid = (fraction > 0) & (fraction < 1)
    between[valid] = (mean[-1] * fraction[valid] - mean[valid]) ** 2 / (
        fraction[valid] * (1 - fraction[valid])
    )
    threshold = max(float(edges[int(np.argmax(between)) + 1]), 6 * _noise(border))
    mask = distance > threshold
    visited = np.zeros(mask.shape, dtype=np.bool_)
    components: list[tuple[int, int, int, int, int]] = []
    sh, sw = mask.shape
    # At most 256*256 nodes; no native CV/Qt dependency or unbounded full-image flood fill.
    for sy, sx in zip(*np.nonzero(mask), strict=True):
        y, x = int(sy), int(sx)
        if visited[y, x]:
            continue
        _check(cancelled)
        stack = [(y, x)]
        visited[y, x] = True
        area = 0
        x0 = x1 = x
        y0 = y1 = y
        while stack:
            cy, cx = stack.pop()
            area += 1
            if area % 512 == 0:
                _check(cancelled)
            x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < sh and 0 <= nx < sw and mask[ny, nx] and not visited[ny, nx]:
                    visited[ny, nx] = True
                    stack.append((ny, nx))
        if area >= distance.size * 0.01 and area >= (x1 - x0 + 1) * (y1 - y0 + 1) * 0.55:
            components.append((area, x0, y0, x1 + 1, y1 + 1))
    components.sort(reverse=True)
    if not components:
        return None, ("membrane_not_found",)
    area, x0, y0, x1, y1 = components[0]
    if area > distance.size * 0.95:
        return None, ("membrane_boundary_unclear",)
    # Refine the coarse rectangle against the same threshold in original coordinates.
    ax, ay = max(0, (x0 - 1) * step), max(0, (y0 - 1) * step)
    bx, by = min(width, (x1 + 1) * step), min(height, (y1 + 1) * step)
    local = np.abs(pixels[ay:by, ax:bx].astype(np.float64) - np.median(border)) > threshold
    rows, columns = local.mean(axis=1), local.mean(axis=0)
    ys, xs = (
        np.flatnonzero(rows >= rows.max() * 0.5),
        np.flatnonzero(columns >= columns.max() * 0.5),
    )
    membrane = LaneROI(
        "membrane", ax + int(xs[0]), ay + int(ys[0]), ax + int(xs[-1]) + 1, ay + int(ys[-1]) + 1
    )
    if (
        membrane.y1 - membrane.y0 < settings.crop_height * 2
        or membrane.width < settings.lane_count * 4
    ):
        return None, ("membrane_boundary_unclear",)
    flags = ["membrane_geometry_candidate"]
    if len(components) > 1 and components[1][0] >= area * 0.25:
        flags.append("multiple_membranes")
    if membrane.x0 == 0 or membrane.y0 == 0 or membrane.x1 == width or membrane.y1 == height:
        flags.append("membrane_at_image_edge")
    return membrane, tuple(flags)


def _sample_grid(
    signal: NDArray[np.float64], membrane: LaneROI, settings: CropDetectionSettings, noise: float
) -> tuple[LaneROI, LaneROI | None, tuple[str, ...]]:
    total = settings.lane_count + int(settings.left_marker)
    width = membrane.width
    # Short bands can occupy <5% of the membrane height; 97th percentile resists isolated dust.
    energy = np.quantile(np.maximum(signal, 0), 0.97, axis=0)
    threshold = max(noise * settings.min_snr, float(energy.max()) * 0.1)
    intervals = _segments(energy >= threshold)
    peaks = [
        float(np.average(np.arange(a, b) + 0.5, weights=energy[a:b]))
        for a, b in intervals
        if b - a >= max(2, width / total * 0.12)
    ]
    best: tuple[float, float, float] | None = None
    # Candidate fit to known equal-spacing slots. A missing peak never removes a slot.
    if 1 < total <= 24 and 2 <= len(peaks) <= 24:
        for i, left in enumerate(peaks):
            for right in peaks[i + 1 :]:
                for distance in range(1, total):
                    pitch = (right - left) / distance
                    if not width / (total + 1) * 0.65 <= pitch <= width / (total - 0.5):
                        continue
                    for slot in range(total - distance):
                        first = left - slot * pitch
                        allowed_left = -pitch / 2 if settings.left_marker else 0.0
                        if (
                            first - pitch / 2 < allowed_left
                            or first + (total - 0.5) * pitch > width
                        ):
                            continue
                        residuals = [
                            min(abs(p - (first + k * pitch)) for p in peaks) / pitch
                            for k in range(total)
                        ]
                        support = sum(r < 0.22 for r in residuals)
                        if support < max(2, ceil(total / 2)):
                            continue
                        score = (
                            support
                            - sum(min(r, 0.22) for r in residuals)
                            + 0.1 * pitch * total / width
                        )
                        if best is None or score > best[0]:
                            best = (score, first, pitch)
    flags: list[str] = []
    if best is None:
        first, pitch = width / total / 2, width / total
        flags.append("uniform_grid_fallback")
    else:
        _, first, pitch = best
        flags.append("periodic_grid_candidate")
        if first - pitch / 2 < 0:
            flags.append("marker_at_membrane_edge")
    start = max(0, int(round(first + (0.5 if settings.left_marker else -0.5) * pitch)))
    end = min(width, int(round(first + (total - 0.5) * pitch)))
    region = LaneROI("samples", membrane.x0 + start, membrane.y0, membrane.x0 + end, membrane.y1)
    marker = None
    if settings.left_marker:
        marker = LaneROI("marker", membrane.x0, membrane.y0, region.x0, membrane.y1)
        flags.append("left_marker_identity_unconfirmed")
    fixed_lane_grid(region, settings.lane_count)
    return region, marker, tuple(flags)


def detect_crop_candidates(
    pixels: NDArray[np.uint8 | np.uint16],
    settings: CropDetectionSettings,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> CropDetection:
    if (
        pixels.ndim != 2
        or pixels.dtype.kind != "u"
        or pixels.dtype.itemsize not in (1, 2)
        or not pixels.size
    ):
        raise ValueError("候选检测需要原始二维uint8/uint16灰度")
    if pixels.size > 16_000_000:
        raise ValueError("候选检测超过1600万像素预算，请拆分原图")
    _check(cancelled)
    height, width = pixels.shape
    membrane, membrane_flags = _membrane(pixels, settings, cancelled)
    if membrane is None:
        return CropDetection(settings, width, height, None, None, None, (), membrane_flags)
    if membrane.y1 - membrane.y0 < settings.crop_height:
        return CropDetection(
            settings,
            width,
            height,
            membrane,
            None,
            None,
            (),
            (*membrane_flags, "crop_height_exceeds_membrane"),
        )
    original = pixels[membrane.y0 : membrane.y1, membrane.x0 : membrane.x1].astype(np.float64)
    noise = _noise(original)
    background = _smooth(original, max(2, settings.crop_height))
    signal = background - original if settings.polarity == "dark" else original - background
    signal = _smooth(signal, 1)
    _check(cancelled)
    guard = (
        0
        if settings.include_membrane_edges
        else min(settings.crop_height // 2, original.shape[0] // 8)
    )
    interior = signal[guard : len(signal) - guard] if guard else signal
    region, marker, grid_flags = _sample_grid(interior, membrane, settings, noise)
    lanes = fixed_lane_grid(region, settings.lane_count)
    profiles: list[NDArray[np.float64]] = []
    for lane in lanes:
        profile = signal[:, lane.x0 - membrane.x0 : lane.x1 - membrane.x0].mean(axis=1)
        sigma = max(_noise(profile), noise / sqrt(lane.width))
        profiles.append(np.maximum(profile, 0) / sigma)
    snr = np.stack(profiles, axis=1)
    active = np.max(snr, axis=1) >= settings.min_snr
    edge_signal = bool(guard and (np.any(active[:guard]) or np.any(active[-guard:])))
    if guard:
        active[:guard] = False
        active[-guard:] = False
    groups = _segments(active)
    merged: list[tuple[int, int]] = []
    for start, end in groups:
        if merged and start - merged[-1][1] <= max(1, settings.crop_height // 6):
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    candidates: list[CropCandidate] = []
    for start, end in merged:
        _check(cancelled)
        if end - start < 2:
            continue
        score = np.minimum(snr[start:end], 20).sum(axis=1)
        peak = start + int(round(float(np.average(np.arange(end - start), weights=score))))
        y0 = max(0, min(peak - settings.crop_height // 2, original.shape[0] - settings.crop_height))
        strength = tuple(float(v) for v in snr[start:end].max(axis=0))
        candidate_flags: list[str] = []
        if end - start > settings.crop_height:
            candidate_flags.append("band_wider_than_crop")
        crop = pixels[
            membrane.y0 + y0 : membrane.y0 + y0 + settings.crop_height, region.x0 : region.x1
        ]
        if np.any(crop == 0) or np.any(crop == np.iinfo(pixels.dtype).max):
            candidate_flags.append("dtype_limits_review")
        candidates.append(
            CropCandidate(
                LaneROI(
                    "candidate",
                    region.x0,
                    membrane.y0 + y0,
                    region.x1,
                    membrane.y0 + y0 + settings.crop_height,
                ),
                membrane.y0 + peak,
                strength,
                tuple(i + 1 for i, v in enumerate(strength) if v >= settings.min_snr),
                tuple(i + 1 for i, v in enumerate(strength) if 2 <= v < settings.min_snr),
                tuple(i + 1 for i, v in enumerate(strength) if v < 2),
                tuple(candidate_flags),
            )
        )
    candidates.sort(
        key=lambda c: (-len(c.detected_lanes), -sum(min(v, 20) for v in c.lane_snr), c.peak_y)
    )
    flags = [*membrane_flags, *grid_flags]
    if edge_signal:
        flags.append("membrane_edge_signal_ignored")
    if len(candidates) > 1:
        flags.append("multiple_candidate_rows")
    if not candidates:
        flags.append("no_candidate_rows")
    if len(candidates) > 8:
        flags.append("candidate_limit")
    return CropDetection(
        settings, width, height, membrane, marker, region, tuple(candidates[:8]), tuple(flags)
    )
