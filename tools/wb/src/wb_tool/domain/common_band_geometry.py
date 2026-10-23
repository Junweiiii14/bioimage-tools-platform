"""Common, prominent WB rows; detection copies never become measurements.

Components select a row, not biological identities or sample counts. The explicit
sample count survives weak internal lanes. Missing terminal phase evidence remains
an adjustment case rather than silently shifting the sample identities.
"""

from collections.abc import Callable
from dataclasses import replace
from math import atan, ceil, cos, degrees, exp, floor, sin

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.automatic import AutoWBSettings
from wb_tool.domain.band_geometry_support import (
    BandCore as _Core,
)
from wb_tool.domain.band_geometry_support import (
    closing as _closing,
)
from wb_tool.domain.band_geometry_support import (
    fit_row as _fit_row,
)
from wb_tool.domain.band_geometry_support import (
    marker_end as _marker_end,
)
from wb_tool.domain.band_geometry_support import (
    sample as _sample,
)
from wb_tool.domain.band_geometry_support import (
    sampling_rectangles as _sampling_rectangles,
)
from wb_tool.domain.band_geometry_support import (
    slots as _slots,
)
from wb_tool.domain.crop_detection import (
    CropCandidate,
    CropDetectionSettings,
    check_detection_cancelled,
    detection_membrane,
    detection_noise,
)
from wb_tool.domain.fixed_lane_frame import fixed_lane_frame
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.reliable_geometry import ReliableDetection
from wb_tool.domain.scipy_geometry import filters as ndi
from wb_tool.domain.source_geometry import DetectionPlane, filled_membrane, source_detection_plane

FloatArray = NDArray[np.float64]
PixelArray = NDArray[np.uint8 | np.uint16]


def _signal(
    pixels: PixelArray, plane: DetectionPlane, settings: AutoWBSettings, scale: float
) -> tuple[FloatArray, NDArray[np.int32], list[_Core], int]:
    valid = ndi.binary_erosion(
        plane.valid, iterations=max(1, round(min(plane.values.shape) * 0.015))
    )
    raw = _sample(pixels, plane)
    signed = raw if settings.polarity == "dark" else -raw
    residuals = [
        np.maximum(_closing(signed, max(5, round(scale * fraction))) - signed, 0)
        for fraction in (0.5, 0.9, 1.4)
    ]
    signal: FloatArray = ndi.gaussian_filter(
        np.median(np.stack(residuals), axis=0), max(0.7, scale * 0.025)
    )
    signal[~valid] = 0
    marker = _marker_end(plane, valid, scale) if settings.left_marker != "include" else 0
    signal[:, :marker] = 0
    core_valid = ndi.binary_erosion(valid, iterations=max(1, round(min(raw.shape) * 0.03)))
    if not core_valid.any():
        raise ValueError("common_membrane_support_insufficient")
    signal[~core_valid] = 0
    threshold = max(2.0, float(np.quantile(signal[core_valid], 0.999)) * 0.45)
    labels, _ = ndi.label(signal > threshold)
    cores: list[_Core] = []
    for label, bounds in enumerate(ndi.find_objects(labels), 1):
        if bounds is None:
            continue
        ys, xs = bounds
        support = labels[ys, xs] == label
        height, width = ys.stop - ys.start, xs.stop - xs.start
        if (
            np.count_nonzero(support) < max(5.0, scale * 0.1)
            or width < max(3.0, scale * 0.15, height * 0.7)
            or width > raw.shape[1] * 0.9
        ):
            continue
        y, x = np.nonzero(support)
        cores.append(
            _Core(
                label,
                float(x.mean()) + xs.start,
                float(y.mean()) + ys.start,
                xs.start,
                ys.start,
                xs.stop,
                ys.stop,
                float(signal[ys, xs][support].sum()),
            )
        )
    if not cores:
        raise ValueError("no_common_band_core")
    if len(cores) > 128:
        raise ValueError("common_band_component_budget")
    return signal, labels, cores, marker


def _choose_row(
    cores: list[_Core],
    signal: FloatArray,
    scale: float,
    n: int,
    angle: float,
    cancelled: Callable[[], bool],
) -> list[_Core]:
    # Cap each component's contribution: one broad stain cannot win solely by
    # having arbitrarily many pixels. The score is a heuristic, not confidence.
    positive = signal[signal > 0]
    cap = max(1.0, float(np.quantile(positive, 0.98)) * scale * max(4.0, scale * 0.35))
    best: list[_Core] = []
    best_score = -1.0
    complete_rows: dict[tuple[int, ...], tuple[list[_Core], float]] = {}
    for first in cores:
        check_detection_cancelled(cancelled)
        hypotheses = [(0.0, first.y)]
        for other in cores:
            if other.x - first.x < scale * 0.3:
                continue
            slope = (other.y - first.y) / (other.x - first.x)
            if abs(degrees(angle + atan(slope))) <= 30:
                hypotheses.append((slope, first.y - slope * first.x))
        for slope, intercept in hypotheses:
            members = [
                q
                for q in cores
                if abs(q.y - slope * q.x - intercept) <= max(2.0, min(q.height, scale * 0.22))
            ]
            # Two parallel rows must not gain extra votes merely by crossing
            # a sloping hypothesis at the same sample X. Nearby fragments share
            # a vote; distance from the proposed line reduces that vote.
            votes: list[tuple[float, float]] = []
            for core in sorted(members, key=lambda q: q.x):
                residual = abs(core.y - slope * core.x - intercept)
                vote = min(core.score, cap) * exp(
                    -0.5 * (residual / max(1, core.height * 0.3)) ** 2
                )
                if votes and core.x - votes[-1][0] < scale * 0.3:
                    votes[-1] = (core.x, max(votes[-1][1], vote))
                else:
                    votes.append((core.x, vote))
            score = sum(vote for _, vote in votes) * min(n, len(votes)) ** 0.5
            if len(votes) >= n:
                key = tuple(sorted(q.label for q in members))
                previous = complete_rows.get(key)
                if previous is None or score > previous[1]:
                    complete_rows[key] = members, score
            if score > best_score:
                best, best_score = members, score
    chosen = {q.label for q in best}
    for other, score in complete_rows.values():
        overlap = len(chosen & {q.label for q in other})
        if score >= best_score * 0.9 and overlap <= min(len(best), len(other)) * 0.2:
            raise ValueError("common_rows_equally_prominent")
    return sorted(best, key=lambda q: q.x)


def detect_common_band_geometry(
    pixels: PixelArray,
    guide: PixelArray | None,
    settings: AutoWBSettings,
    *,
    target: LaneROI | None = None,
    cancelled: Callable[[], bool] = lambda: False,
) -> ReliableDetection:
    """Locate one prominent row without the legacy all-components veto.

    ``guide=None`` (or the identical array object) denotes source-only detection.
    The caller validates any separate guide's provenance and registration.
    Returned sampling limits conservatively equal the raw sampling rectangles;
    no rotated polygon or detection interpolation is a quantitative array.
    """
    source_only = guide is None or guide is pixels
    guide = pixels if guide is None else guide
    if (
        pixels.ndim != 2
        or pixels.shape != guide.shape
        or pixels.dtype not in (np.dtype("uint8"), np.dtype("uint16"))
        or guide.dtype not in (np.dtype("uint8"), np.dtype("uint16"))
        or min(pixels.shape) < 3
        or pixels.size > 16_000_000
    ):
        raise ValueError("常见条带检测需要同尺寸二维uint8/uint16原像素，最多1600万像素")
    if settings.lane_count is None:
        raise ValueError("常见条带策略需要已确认泳道数")
    n = settings.lane_count
    check_detection_cancelled(cancelled)
    initial = CropDetectionSettings(
        n, 2, settings.polarity, left_marker=False, min_snr=settings.min_snr
    )
    algorithm = "source_common_band_geometry@1" if source_only else "guided_common_band_geometry@1"
    membrane, flags = detection_membrane(guide, initial, cancelled)
    if membrane is None:
        membrane, multiple = filled_membrane(guide)
        flags = ("filled_common_contour@1", *(("multiple_membranes",) if multiple else ()))

    def failure(reason: str) -> ReliableDetection:
        return ReliableDetection(
            initial,
            pixels.shape[1],
            pixels.shape[0],
            membrane,
            None,
            None,
            (),
            (*flags, reason),
            algorithm,
        )

    if membrane is None:
        return failure("common_membrane_unlocated")
    try:
        plane = source_detection_plane(guide, membrane)
        height, width = plane.values.shape
        scale = width / (n + 1)
        signal, labels, cores, marker_end = _signal(pixels, plane, settings, scale)
        if target is not None:
            cores = [
                q
                for q in cores
                if target.x0 <= plane.source(q.x, q.y)[0] < target.x1
                and target.y0 <= plane.source(q.x, q.y)[1] < target.y1
            ]
            if not cores:
                return failure("common_target_has_no_core")
        members = _choose_row(cores, signal, scale, n, plane.angle, cancelled)
        support = np.isin(labels, [q.label for q in members])
        slope, intercept = _fit_row(signal, support)
        angle = plane.angle + atan(slope)
        if abs(degrees(angle)) > 30:
            return failure("common_angle_outside_support")
        ys, xs = np.mgrid[:height, :width]
        half = max(max(q.height for q in members) * 0.65, scale * 0.22)
        row = np.abs(ys - (slope * xs + intercept)) <= half
        profile = ndi.gaussian_filter1d((signal * row).sum(axis=0), max(0.8, scale * 0.055))
        left = max(0, floor(min(q.x0 for q in members) - scale * 0.2))
        right = min(width, ceil(max(q.x1 for q in members) + scale * 0.2))
        profile[:left], profile[right:] = 0, 0
        centers, missing = _slots(members, profile, scale, n)
        relative_angle = atan(slope)
        pitch = (
            float(np.median(np.diff(centers))) / cos(relative_angle)
            if n > 1
            else max(max(q.x1 - q.x0 for q in members) * 1.2, scale * 0.7)
        )
        mid = float((centers[0] + centers[-1]) / 2)
        center_y = slope * mid + intercept
        center_x_source, center_y_source = plane.source(mid, center_y)
        sy, sx = np.nonzero(support)
        u = (sx - mid) * cos(relative_angle) + (sy - center_y) * sin(relative_angle)
        v = -(sx - mid) * sin(relative_angle) + (sy - center_y) * cos(relative_angle)
        # Preserve complete selected cores plus a small background margin. Do
        # not silently retain 5N:4 by cutting a broad or tilted core in half.
        needed = max(
            pitch, (float(np.abs(u).max()) + 2) * 2 / n, (float(np.abs(v).max()) + 2) * 2 / 0.8
        )
        if needed > pitch * 1.35:
            return failure("common_fixed_frame_cannot_cover_support")
        frame, crop, lanes = fixed_lane_frame(
            n,
            needed,
            center_x_source,
            center_y_source,
            degrees(angle),
            pixels.shape[1],
            pixels.shape[0],
            max_angle=30,
        )
        lanes = _sampling_rectangles(
            lanes, plane, support, center_x_source, center_y_source, frame.width, angle
        )
        evidence_flags = (
            *flags,
            "common_band_row@1",
            "signal_orientation_fit@3",
            "fixed_n_frame@1",
            "source_axis_partition@2",
            "common_sampling_crop_limits@1",
            f"common_marker_end:{marker_end}",
            f"common_row_cores:{len(members)}",
            *(f"grid_signal_unresolved:{i}" for i in missing),
        )
        snrs = tuple(
            float(np.ptp(pixels[r.y0 : r.y1, r.x0 : r.x1].astype(np.float64)))
            / max(1.0, detection_noise(pixels[r.y0 : r.y1, r.x0 : r.x1].astype(np.float64).ravel()))
            for r in lanes
        )
        detected = tuple(i for i in range(1, n + 1) if i not in missing)
        candidate = CropCandidate(
            crop, round(center_y_source), snrs, detected, missing, (), evidence_flags, lanes, frame
        )
        check_detection_cancelled(cancelled)
        return ReliableDetection(
            replace(initial, crop_height=crop.y1 - crop.y0),
            pixels.shape[1],
            pixels.shape[0],
            membrane,
            None,
            crop,
            (candidate,),
            evidence_flags,
            algorithm,
            lanes,
            missing,
        )
    except ValueError as exc:
        check_detection_cancelled(cancelled)
        return failure(str(exc))
