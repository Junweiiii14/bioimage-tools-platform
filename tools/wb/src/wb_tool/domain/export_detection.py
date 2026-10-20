"""Bounded image-only suggestions. Detection copies never become measurements."""

from dataclasses import dataclass
from math import atan, ceil, cos, degrees, floor, sin

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.crop_detection import CropDetectionSettings, detection_membrane
from wb_tool.domain.scipy_geometry import filters as ndi
from wb_tool.domain.scipy_geometry import peaks as peak_functions
from wb_tool.domain.source_geometry import source_detection_plane


@dataclass(frozen=True)
class ExportFeatures:
    bright_background: bool
    texture: float
    regions: tuple[tuple[int, int, int, int, tuple[int, ...], float], ...]


def inspect_export(pixels: NDArray[np.uint8 | np.uint16]) -> ExportFeatures:
    """Locate horizontal dark-signal groups, retaining ambiguity and original coordinates."""
    if pixels.ndim != 2 or pixels.dtype not in (np.dtype("uint8"), np.dtype("uint16")):
        raise ValueError("识别需要二维原始uint8/uint16像素")
    h, w = pixels.shape
    step = max(1, ceil(max(h, w) / 512))
    a = pixels[::step, ::step].astype(np.float64)
    border = np.concatenate((a[0], a[-1], a[:, 0], a[:, -1]))
    low, high = np.percentile(a, [0.1, 99.9])
    span = max(float(high - low), 1)
    bright = float(np.median(border)) > low + span * 0.6
    if not bright:
        mask = a > low + span * 0.35
        labels, _ = ndi.label(mask)
        sizes = np.bincount(labels.ravel())
        sizes[0] = 0
        if len(sizes) < 2 or sizes.max() < 8:
            return ExportFeatures(False, 0, ())
        foreground = labels == int(sizes.argmax())
        core = ndi.binary_erosion(ndi.binary_fill_holes(foreground), iterations=2)
        values = a[core] if np.count_nonzero(core) >= 8 else a[foreground]
        texture = float((np.percentile(values, 98) - np.percentile(values, 2)) / span)
        return ExportFeatures(False, texture, ())

    # Percentiles of the entire frame can miss a tiny membrane. Border noise and
    # dynamic range bound the threshold; connected components discard speckles.
    background = float(np.median(border))
    noise = float(np.median(np.abs(border - background)))
    signal = np.maximum(0, background - a)
    threshold = max(6 * noise, float(signal.max()) * 0.12, 2)
    mask = signal > threshold
    labels, count = ndi.label(mask)
    objects = ndi.find_objects(labels)
    boxes: list[tuple[int, int, int, int]] = []
    for i in range(min(count, len(objects))):
        item = objects[i]
        if item is None:
            continue
        ys, xs = item
        area = int(np.count_nonzero(labels[ys, xs] == i + 1))
        if area >= 3 and xs.stop - xs.start >= 2 and area < a.size * 0.2:
            boxes.append((xs.start, ys.start, xs.stop, ys.stop))
    # Cluster components whose vertical extents overlap: multiple rows remain
    # multiple targets, rather than silently selecting the strongest row.
    groups: list[list[tuple[int, int, int, int]]] = []
    for box in sorted(boxes, key=lambda b: b[1]):
        matched = [
            g
            for g in groups
            if box[1] <= max(b[3] for b in g) + 2 and box[3] >= min(b[1] for b in g) - 2
        ]
        if matched:
            group = matched[0]
            group.append(box)
            for other in matched[1:]:
                group.extend(other)
                groups.remove(other)
        else:
            groups.append([box])
    regions: list[tuple[int, int, int, int, tuple[int, ...], float]] = []
    for group in groups:
        x0, y0 = min(b[0] for b in group), min(b[1] for b in group)
        x1, y1 = max(b[2] for b in group), max(b[3] for b in group)
        width, height = x1 - x0, y1 - y0
        if width < 8 or width < height * 1.4:
            continue
        energy = signal[y0:y1, x0:x1].sum(axis=0)
        energy = ndi.gaussian_filter1d(energy, max(0.6, width / 150))
        peaks, _ = peak_functions.find_peaks(
            np.pad(energy, 1),
            prominence=max(float(energy.max()) * 0.1, 1),
            distance=max(2, round(height * 0.4)),
        )
        n = len(peaks)
        counts = tuple(v for v in (n, n + 1) if 1 <= v <= 96)
        yy, xx = np.nonzero(mask[y0:y1, x0:x1])
        angle = 0.0
        if len(xx) >= 8 and np.ptp(xx) > 3:
            angle = degrees(atan(float(np.polyfit(xx, yy, 1)[0])))
        pad = max(2, round(height * 0.35))
        regions.append(
            (
                max(0, (x0 - pad) * step),
                max(0, (y0 - pad) * step),
                min(w, (x1 + pad) * step),
                min(h, (y1 + pad) * step),
                counts,
                angle,
            )
        )
    regions.sort(key=lambda r: (r[1], r[0]))
    return ExportFeatures(True, 0, tuple(regions[:8]))


def guided_signal_regions(
    signal: NDArray[np.uint8 | np.uint16], guide: NDArray[np.uint8 | np.uint16]
) -> tuple[tuple[int, int, int, int, tuple[int, ...], float], ...]:
    """White-light contour constrains suggestions only, using signal-frame intensities."""
    if signal.shape != guide.shape:
        return ()
    membrane, _ = detection_membrane(guide, CropDetectionSettings(1, 2, "dark"), lambda: False)
    if membrane is None:
        return ()
    plane = source_detection_plane(guide, membrane)
    height, width = plane.values.shape
    vv, uu = np.mgrid[:height, :width]
    c, s = cos(plane.angle), sin(plane.angle)
    rx = plane.origin_x + c * uu - s * vv
    ry = plane.origin_y + s * uu + c * vv
    values = ndi.map_coordinates(signal.astype(float), [ry, rx], order=1, mode="nearest")
    background = ndi.maximum_filter1d(values, size=max(7, height // 2), axis=0)
    dark = np.maximum(0, background - values)
    # Exclude the white-light contour itself from both axes of the evidence.
    valid = ndi.binary_erosion(plane.valid, iterations=max(1, height // 15))
    dark[~valid] = 0
    profile = ndi.gaussian_filter1d(dark.sum(axis=1), max(1.0, height / 70))
    if float(profile.max()) <= 0:
        return ()
    peaks, _ = peak_functions.find_peaks(
        profile, prominence=float(profile.max()) * 0.18, distance=max(3, height // 8)
    )
    result: list[tuple[int, int, int, int, tuple[int, ...], float]] = []
    for peak in peaks:
        low = high = int(peak)
        while low > 0 and profile[low - 1] >= profile[peak] * 0.4:
            low -= 1
        while high + 1 < height and profile[high + 1] >= profile[peak] * 0.4:
            high += 1
        energy = ndi.gaussian_filter1d(dark[low : high + 1].sum(axis=0), max(1.0, width / 180))
        support = np.flatnonzero(energy > float(energy.max()) * 0.08)
        if len(support) < 8:
            continue
        left, right = int(support[0]), int(support[-1]) + 1
        band_height = high - low + 1
        if right - left < band_height * 1.4:
            continue
        centers, _ = peak_functions.find_peaks(
            np.pad(energy[left:right], 1),
            prominence=float(energy.max()) * 0.12,
            distance=max(3, round(band_height * 0.5)),
        )
        n = len(centers)
        counts = tuple(v for v in (n, n - 1, n + 1) if 1 <= v <= 96)
        pad = max(3, round(band_height * 0.3))
        corners = [
            plane.source(x, y)
            for x in (max(0, left - pad), min(width - 1, right + pad))
            for y in (max(0, low - pad), min(height - 1, high + pad))
        ]
        x0, y0 = (
            max(0, floor(min(p[0] for p in corners))),
            max(0, floor(min(p[1] for p in corners))),
        )
        x1 = min(signal.shape[1], ceil(max(p[0] for p in corners)) + 1)
        y1 = min(signal.shape[0], ceil(max(p[1] for p in corners)) + 1)
        if x1 > x0 and y1 > y0:
            result.append((x0, y0, x1, y1, counts, degrees(plane.angle)))
    return tuple(result[:8])
