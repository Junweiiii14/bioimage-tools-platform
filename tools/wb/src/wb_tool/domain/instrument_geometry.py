"""A white-light contour guides detection; quantitative slots stay on signal pixels."""

from collections.abc import Callable
from dataclasses import replace
from math import atan, ceil, cos, degrees, floor, radians, sin

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.automatic import AutoWBSettings
from wb_tool.domain.crop_detection import (
    CropDetection,
    CropDetectionSettings,
    check_detection_cancelled,
    detection_membrane,
    detection_noise,
)
from wb_tool.domain.export_detection import guided_signal_regions
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.scipy_geometry import filters as ndi
from wb_tool.domain.source_geometry import (
    DetectionPlane,
    detect_source_geometry,
    source_detection_plane,
)


def _signal_components(
    signal: NDArray[np.uint8 | np.uint16],
    plane: DetectionPlane,
    membrane: LaneROI,
    settings: AutoWBSettings,
) -> list[tuple[float, float, LaneROI]]:
    """Independent original-signal components; no guide angle enters the fit."""
    yy, xx = np.mgrid[membrane.y0 : membrane.y1, membrane.x0 : membrane.x1]
    c, s = cos(plane.angle), sin(plane.angle)
    u = (xx - plane.origin_x) * c + (yy - plane.origin_y) * s
    v = -(xx - plane.origin_x) * s + (yy - plane.origin_y) * c
    valid = ndi.map_coordinates(plane.valid.astype(float), [v, u], order=0, mode="constant") > 0.5
    valid = ndi.binary_erosion(valid, iterations=2)
    raw = signal[membrane.y0 : membrane.y1, membrane.x0 : membrane.x1].astype(float)
    signed = raw if settings.polarity == "dark" else -raw
    strength = np.maximum(
        ndi.maximum_filter1d(signed, max(7, (membrane.y1 - membrane.y0) // 2), axis=0) - signed, 0
    )
    strength[~valid] = 0
    threshold = max(float(strength.max()) * 0.12, settings.min_snr * detection_noise(raw))
    labels, count = ndi.label(strength > threshold)
    if count > 200:
        return []
    components: list[tuple[float, float, LaneROI]] = []
    for index, box in enumerate(ndi.find_objects(labels), 1):
        if box is None:
            continue
        ys, xs = box
        mask = labels[ys, xs] == index
        if np.count_nonzero(mask) < 6 or xs.stop - xs.start < 3:
            continue
        weights = strength[ys, xs] * mask
        cy, cx = np.mgrid[ys, xs]
        components.append(
            (
                float(np.average(cx, weights=weights)) + membrane.x0,
                float(np.average(cy, weights=weights)) + membrane.y0,
                LaneROI(
                    "signal",
                    xs.start + membrane.x0,
                    ys.start + membrane.y0,
                    xs.stop + membrane.x0,
                    ys.stop + membrane.y0,
                ),
            )
        )
    return components


def _signal_plane(
    signal: NDArray[np.uint8 | np.uint16], guide: DetectionPlane, angle: float
) -> DetectionPlane:
    """Rotate a private detection copy, retaining the guide's original-pixel mask."""
    height, width = guide.values.shape
    cx, cy = width / 2, height / 2
    delta = angle - guide.angle
    c, s = cos(delta), sin(delta)
    corners = [
        (c * (x - cx) + s * (y - cy), -s * (x - cx) + c * (y - cy))
        for x in (0, width - 1)
        for y in (0, height - 1)
    ]
    u0, v0 = floor(min(x for x, _ in corners)), floor(min(y for _, y in corners))
    w, h = ceil(max(x for x, _ in corners)) - u0 + 1, ceil(max(y for _, y in corners)) - v0 + 1
    if w * h > 16_000_000:
        raise ValueError("signal_plane_budget")
    vv, uu = np.mgrid[:h, :w]
    ox, oy = cx + c * (uu + u0) - s * (vv + v0), cy + s * (uu + u0) + c * (vv + v0)
    origin_x, origin_y = guide.source(cx + c * u0 - s * v0, cy + s * u0 + c * v0)
    ca, sa = cos(angle), sin(angle)
    rx, ry = origin_x + ca * uu - sa * vv, origin_y + sa * uu + ca * vv
    values = ndi.map_coordinates(signal.astype(float), [ry, rx], order=1, mode="nearest")
    valid = ndi.map_coordinates(guide.valid.astype(float), [oy, ox], order=0, mode="constant") > 0.5
    return DetectionPlane(values, valid, origin_x, origin_y, angle)


def detect_instrument_geometry(
    signal: NDArray[np.uint8 | np.uint16],
    guide: NDArray[np.uint8 | np.uint16],
    settings: AutoWBSettings,
    *,
    target: LaneROI | None = None,
    cancelled: Callable[[], bool] = lambda: False,
) -> CropDetection:
    if signal.shape != guide.shape or signal.ndim != 2:
        raise ValueError("辅助定位与信号原图须为相同原像素尺寸")
    initial = CropDetectionSettings(
        settings.lane_count or 1, 2, settings.polarity, left_marker=False
    )
    membrane, membrane_flags = detection_membrane(guide, initial, cancelled)

    def failure(reason: str) -> CropDetection:
        return CropDetection(
            initial,
            signal.shape[1],
            signal.shape[0],
            membrane,
            None,
            None,
            (),
            (reason,),
            "instrument_guided_geometry@1",
        )

    if membrane is None:
        return failure("guide_membrane_unlocated")
    if "multiple_membranes" in membrane_flags:
        return failure("guide_multiple_membranes")
    check_detection_cancelled(cancelled)
    regions = guided_signal_regions(signal, guide)
    if target is not None:
        regions = tuple(
            r
            for r in regions
            if (r[0], r[1], r[2], r[3]) == (target.x0, target.y0, target.x1, target.y1)
        )
    else:
        regions = tuple(r for r in regions if settings.lane_count in r[4])
    if len(regions) != 1:
        return failure("guided_target_ambiguous" if regions else "guided_target_not_supported")
    x0, y0, x1, y1, _, _ = regions[0]
    plane = source_detection_plane(guide, membrane)
    components = _signal_components(signal, plane, membrane, settings)
    selected = [(x, y, box) for x, y, box in components if x0 <= x < x1 and y0 <= y < y1]
    if len(selected) < 3:
        return failure("signal_orientation_insufficient")
    selected.sort(key=lambda item: item[0])
    # Two disconnected bands at the same lane position are two possible targets.
    if any(a[2].x1 > b[2].x0 for a, b in zip(selected, selected[1:], strict=False)):
        return failure("signal_rows_ambiguous")
    xs, ys = np.array([x for x, _, _ in selected]), np.array([y for _, y, _ in selected])
    fit = np.polyfit(xs, ys, 1)
    residual = float(np.max(np.abs(ys - np.polyval(fit, xs))))
    band_height = float(np.median([(box.y1 - box.y0) for _, _, box in selected]))
    angle = degrees(atan(float(fit[0])))
    if residual > max(1.5, band_height * 0.2) or abs(angle) > 10:
        return failure("signal_orientation_ambiguous")
    if abs(angle) < 0.2:
        angle = 0.0
    plane = _signal_plane(signal, plane, radians(angle))
    vv, uu = np.mgrid[: plane.values.shape[0], : plane.values.shape[1]]
    c, s = cos(plane.angle), sin(plane.angle)
    rx, ry = plane.origin_x + c * uu - s * vv, plane.origin_y + s * uu + c * vv
    values = np.asarray(
        ndi.map_coordinates(signal.astype(np.float64), [ry, rx], order=1, mode="nearest")
    )
    valid = plane.valid & (rx >= x0) & (rx < x1) & (ry >= y0) & (ry < y1)
    guided = replace(plane, values=values, valid=valid)
    result = detect_source_geometry(signal, settings, cancelled, guidance=(guided, membrane))
    # Standard presentation height must not expand quantitative slots into a
    # different signal row, including a target the caller explicitly did not pick.
    for candidate in result.candidates:
        for x, y, box in components:
            if (x, y, box) in selected:
                continue
            if any(
                r.x0 < box.x1 and box.x0 < r.x1 and r.y0 < box.y1 and box.y0 < r.y1
                for r in candidate.lane_rois
            ):
                return failure("signal_target_overlap")
    return replace(
        result,
        flags=(*result.flags, "signal_orientation_fit@1", f"signal_fit_residual:{residual:.6f}"),
    )
