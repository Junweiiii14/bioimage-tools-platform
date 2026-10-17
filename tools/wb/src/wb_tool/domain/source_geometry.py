"""Source-only, contour-oriented detection. Resampled arrays are never measurements."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from math import atan, ceil, cos, degrees, floor, sin
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.crop_detection import (
    CropCandidate,
    CropDetection,
    CropDetectionSettings,
    OrientedCrop,
    check_detection_cancelled,
    detection_membrane,
    detection_noise,
    detection_segments,
)
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.scipy_geometry import filters as ndi
from wb_tool.domain.scipy_geometry import peaks as peak_functions

if TYPE_CHECKING:
    from wb_tool.domain.automatic import AutoWBSettings


@dataclass(frozen=True)
class DetectionPlane:
    values: NDArray[np.float64]
    valid: NDArray[np.bool_]
    origin_x: float
    origin_y: float
    angle: float

    def source(self, x: float, y: float) -> tuple[float, float]:
        c, s = cos(self.angle), sin(self.angle)
        return self.origin_x + c * x - s * y, self.origin_y + s * x + c * y


def _edge_fit(xs: NDArray[np.int64], ys: NDArray[np.int64]) -> float:
    keep = np.ones(xs.size, dtype=np.bool_)
    slope = 0.0
    for _ in range(4):
        if np.count_nonzero(keep) < 3:
            raise ValueError("membrane_edge_insufficient")
        coefficients = np.polyfit(xs[keep], ys[keep], 1)
        slope = float(coefficients[0])
        residual = ys - np.polyval(coefficients, xs)
        keep = np.abs(residual) <= max(2.0, 3 * float(np.median(np.abs(residual))))
    return slope


def _plane(pixels: NDArray[np.uint8 | np.uint16], membrane: LaneROI) -> DetectionPlane:
    pad = max(20, round(membrane.width * 0.1))
    x0, y0 = max(0, membrane.x0 - pad), max(0, membrane.y0 - pad)
    raw = pixels[
        y0 : min(pixels.shape[0], membrane.y1 + pad),
        x0 : min(pixels.shape[1], membrane.x1 + pad),
    ].astype(np.float64)
    border = np.concatenate((raw[0], raw[-1], raw[:, 0], raw[:, -1]))
    distance = np.abs(raw - np.median(border))
    threshold = (float(np.quantile(distance, 0.1)) + float(np.quantile(distance, 0.9))) / 2
    labels, _ = ndi.label(ndi.binary_fill_holes(distance > threshold))
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    mask = labels == int(sizes.argmax())
    yy, xx = np.nonzero(mask)
    if xx.size < 16:
        raise ValueError("membrane_contour_insufficient")
    left, right = int(xx.min()), int(xx.max()) + 1
    inset = max(1, int((right - left) * 0.15))
    xs = np.arange(left + inset, right - inset, dtype=np.int64)
    top = np.argmax(mask[:, xs], axis=0).astype(np.int64)
    bottom = (mask.shape[0] - 1 - np.argmax(mask[::-1, xs], axis=0)).astype(np.int64)
    slopes = (_edge_fit(xs, top), _edge_fit(xs, bottom))
    angle = atan(sum(slopes) / 2)
    # Slight trapezoidal cutting is common: compare the edge divergence to the
    # measured membrane thickness, rather than a scale-independent angle cutoff.
    divergence = abs(slopes[0] - slopes[1]) * (right - left)
    if abs(degrees(angle)) > 30 or divergence > float(np.median(bottom - top)) * 0.25:
        raise ValueError("membrane_orientation_disagreement")
    c, s = cos(angle), sin(angle)
    cx, cy = float(xx.mean()), float(yy.mean())
    u, v = (xx - cx) * c + (yy - cy) * s, -(xx - cx) * s + (yy - cy) * c
    u0, v0 = floor(float(u.min())), floor(float(v.min()))
    width, height = ceil(float(u.max())) - u0 + 1, ceil(float(v.max())) - v0 + 1
    if width * height > 16_000_000 or min(width, height) < 8:
        raise ValueError("membrane_plane_budget")
    vv, uu = np.mgrid[:height, :width]
    rx, ry = c * (uu + u0) - s * (vv + v0) + cx, s * (uu + u0) + c * (vv + v0) + cy
    values = np.asarray(ndi.map_coordinates(raw, [ry, rx], order=1, mode="nearest"))
    valid = np.asarray(
        ndi.map_coordinates(mask.astype(float), [ry, rx], order=0, mode="constant") > 0.5
    )
    return DetectionPlane(
        values, valid, x0 + c * u0 - s * v0 + cx, y0 + s * u0 + c * v0 + cy, angle
    )


def _centers(energy: NDArray[np.float64], height: int) -> tuple[list[float], list[int], float]:
    """Track interval centres across global/local thresholds, rejecting one-off fragments."""
    observations: list[tuple[float, float]] = []
    local = ndi.maximum_filter1d(energy, size=max(3, height // 3))
    for level in (float(energy.max()), local):
        for fraction in np.arange(0.1, 0.96, 0.025):
            spans = detection_segments((energy > fraction * level) & (energy > energy.max() * 0.06))
            observations.extend(
                ((a + b) / 2, float(b - a))
                for a, b in spans
                if height * 0.12 < b - a < height * 0.8
            )
    if not observations:
        return [], [], 0.0
    width = float(np.median([item[1] for item in observations]))
    groups: list[list[float]] = []
    for position, span in sorted(observations):
        if not 0.55 * width < span < 1.6 * width:
            continue
        if groups and position - float(np.mean(groups[-1])) < width * 0.35:
            groups[-1].append(position)
        else:
            groups.append([position])
    stable = [group for group in groups if len(group) >= 3]
    return [float(np.median(g)) for g in stable], [len(g) for g in stable], width


def detect_source_geometry(
    pixels: NDArray[np.uint8 | np.uint16], settings: "AutoWBSettings", cancelled: Callable[[], bool]
) -> CropDetection:
    h, w = pixels.shape
    initial = CropDetectionSettings(
        settings.lane_count or 1, 2, settings.polarity, left_marker=False
    )
    membrane, old_flags = detection_membrane(pixels, initial, cancelled)
    flags = ["crop_policy:source_geometry@2", "automatic_geometry_unreviewed", *old_flags]

    def failure(reason: str) -> CropDetection:
        return CropDetection(
            initial, w, h, membrane, None, None, (), (*flags, reason), "source_geometry@2"
        )

    if "multiple_membranes" in old_flags:
        return failure("no_reliable_membrane")
    check_detection_cancelled(cancelled)
    if membrane is None:
        # Previously cropped fields have no membrane/background contour. Accept
        # only a uniform perimeter with sparse signal of the declared polarity.
        raw_field = pixels.astype(np.float64)
        perimeter = np.concatenate((raw_field[0], raw_field[-1], raw_field[:, 0], raw_field[:, -1]))
        base = float(np.median(perimeter))
        contrast = base - raw_field if settings.polarity == "dark" else raw_field - base
        amplitude = float(contrast.max())
        noise_field = detection_noise(raw_field)
        occupied = float(np.mean(contrast > max(settings.min_snr * noise_field, amplitude * 0.1)))
        if (
            amplitude < settings.min_snr * noise_field
            or not 0.005 <= occupied <= 0.35
            or float(np.quantile(np.abs(perimeter - base), 0.95))
            > max(3 * noise_field, amplitude * 0.01)
        ):
            return failure("no_reliable_membrane")
        membrane = LaneROI("pre_cropped_field", 0, 0, w, h)
        plane = DetectionPlane(raw_field, np.ones(pixels.shape, dtype=np.bool_), 0.0, 0.0, 0.0)
        flags.append("uniform_background_field_without_orientation_evidence")
    else:
        try:
            plane = _plane(pixels, membrane)
        except ValueError as exc:
            return failure(str(exc))
    raw, valid = plane.values, plane.valid
    height, width = raw.shape
    signed = raw if settings.polarity == "dark" else -raw
    background = ndi.maximum_filter1d(signed, size=max(5, height // 2), axis=0)
    signal = ndi.gaussian_filter(np.maximum(background - signed, 0), sigma=max(1, height / 100))
    signal[~ndi.binary_erosion(valid, iterations=max(2, height // 20))] = 0
    row = signal[:, int(width * 0.2) : int(width * 0.95)].mean(axis=1)
    noise = detection_noise(raw)
    if float(row.max()) < settings.min_snr * noise:
        return failure("no_sample_bands")
    peak = int(row.argmax())
    low = high = peak
    while low > 0 and row[low - 1] > row.max() * 0.2:
        low -= 1
    while high < height - 1 and row[high + 1] > row.max() * 0.2:
        high += 1
    energy = np.asarray(
        ndi.gaussian_filter1d(signal[low : high + 1].max(axis=0), max(1, height / 35))
    )
    centers, support, band_width = _centers(energy, height)
    check_detection_cancelled(cancelled)
    if not centers or len(centers) > 97:
        return failure("no_stable_lane_centers")
    marker_center: float | None = None
    if settings.left_marker != "include" and len(centers) >= 2:
        first = int(centers[0])
        half = max(1, int(band_width * 0.3))
        profile = ndi.gaussian_filter1d(
            signal[:, max(0, first - half) : first + half + 1].mean(axis=1), max(1, height / 80)
        )
        peaks, _ = peak_functions.find_peaks(
            profile, prominence=float(profile.max()) * 0.18, distance=max(3, height // 8)
        )
        outside = sum(not low <= int(y) <= high for y in peaks)
        marker = centers[0] < width * 0.28 and len(peaks) >= 2 and outside >= 1
        if marker:
            marker_center = centers.pop(0)
            support.pop(0)
            flags.append("left_marker_multiband_evidence")
    if len(centers) < 2:
        return failure("insufficient_sample_structure")
    # A ladder entirely outside the target row needs no deletion, but remains
    # explicitly recorded when its separate vertical peaks support that identity.
    search_end = max(0, int(centers[0] - band_width))
    if marker_center is None and settings.left_marker != "include" and search_end > 3:
        left_energy = signal[:, :search_end].sum(axis=0)
        if float(left_energy.max()) > settings.min_snr * noise * height * 0.1:
            selected = np.flatnonzero(left_energy > left_energy.max() * 0.5)
            position = int(round(float(np.average(selected, weights=left_energy[selected]))))
            half = max(1, int(band_width * 0.3))
            profile = ndi.gaussian_filter1d(
                signal[:, max(0, position - half) : min(search_end, position + half + 1)].mean(
                    axis=1
                ),
                max(1, height / 80),
            )
            peaks, _ = peak_functions.find_peaks(
                profile, prominence=float(profile.max()) * 0.18, distance=max(3, height // 8)
            )
            if len(peaks) >= 2 and any(not low <= int(y) <= high for y in peaks):
                marker_center = float(position)
                flags.append("separate_left_marker_multiband_evidence")
    gaps = np.diff(centers)
    pitch = float(np.median(gaps))
    # Fill only interior gaps with explicit weak/empty evidence, never extrapolate invisible ends.
    slots = np.rint((np.array(centers) - centers[0]) / pitch).astype(int)
    if (
        np.any(np.diff(slots) < 1)
        or np.max(np.abs(np.array(centers) - centers[0] - slots * pitch)) > pitch * 0.3
    ):
        return failure("lane_spacing_ambiguous")
    count = int(slots[-1]) + 1
    if settings.lane_count is not None and settings.lane_count != count:
        return failure("explicit_lane_count_conflicts_with_evidence")
    if count > 96:
        return failure("lane_count_exceeds_budget")
    located = {int(slot): center for slot, center in zip(slots, centers, strict=True)}
    points = [located.get(i, centers[0] + i * pitch) for i in range(count)]
    start, end = max(0.0, points[0] - pitch / 2), min(float(width - 1), points[-1] + pitch / 2)
    frame_width = end - start
    frame_height = max(frame_width * 4 / (5 * count), high - low + 1 + height * 0.08)
    mid_y = (low + high) / 2
    if mid_y - frame_height / 2 < 0 or mid_y + frame_height / 2 >= height:
        return failure("target_frame_exceeds_membrane")
    corners = [
        plane.source(x, y)
        for x in (start, end)
        for y in (mid_y - frame_height / 2, mid_y + frame_height / 2)
    ]
    if any(x < 0 or y < 0 or x >= w or y >= h for x, y in corners):
        return failure("target_frame_exceeds_source")
    crop = LaneROI(
        "candidate",
        floor(min(x for x, _ in corners)),
        floor(min(y for _, y in corners)),
        min(w, ceil(max(x for x, _ in corners)) + 1),
        min(h, ceil(max(y for _, y in corners)) + 1),
    )
    source_centers = [plane.source(x, mid_y)[0] for x in points]
    edges = [
        crop.x0,
        *(round((a + b) / 2) for a, b in zip(source_centers, source_centers[1:], strict=False)),
        crop.x1,
    ]
    lanes: list[LaneROI] = []
    for i, x in enumerate(points):
        left = start if i == 0 else (points[i - 1] + x) / 2
        right = end if i == count - 1 else (x + points[i + 1]) / 2
        ys = [
            plane.source(u, v)[1]
            for u in (left, right)
            for v in (mid_y - frame_height / 2, mid_y + frame_height / 2)
        ]
        lanes.append(
            LaneROI(
                f"lane-{i + 1}",
                edges[i],
                max(crop.y0, floor(min(ys))),
                edges[i + 1],
                min(crop.y1, ceil(max(ys)) + 1),
            )
        )
    center_x, center_y = plane.source((start + end) / 2, mid_y)
    strengths = tuple(float(energy[min(width - 1, round(x))]) / noise for x in points)
    flags.extend(
        (
            f"angle_degrees:{degrees(plane.angle):.6f}",
            "center_support:" + ",".join(map(str, support)),
            "automatic_lane_count" if settings.lane_count is None else "explicit_lane_count",
        )
    )
    missing = tuple(i + 1 for i in range(count) if i not in located)
    candidate = CropCandidate(
        crop,
        round(center_y),
        strengths,
        tuple(i + 1 for i in range(count) if i in located),
        (),
        missing,
        tuple(flags),
        tuple(lanes),
        OrientedCrop(center_x, center_y, frame_width, frame_height, degrees(plane.angle)),
    )
    marker_roi = None
    if marker_center is not None:
        marker_x, _ = plane.source(marker_center, mid_y)
        marker_roi = LaneROI(
            "marker",
            max(0, floor(marker_x - band_width / 2)),
            crop.y0,
            max(1, min(crop.x0, ceil(marker_x + band_width / 2))),
            crop.y1,
        )
    chosen = replace(initial, lane_count=count, crop_height=crop.y1 - crop.y0)
    return CropDetection(
        chosen, w, h, membrane, marker_roi, crop, (candidate,), tuple(flags), "source_geometry@2"
    )
