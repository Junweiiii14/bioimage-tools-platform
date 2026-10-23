"""Common, prominent WB rows; detection copies never become measurements.

Components select a row, not biological identities or sample counts. The explicit
sample count survives weak internal lanes. Missing terminal phase evidence remains
an adjustment case rather than silently shifting the sample identities.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from math import atan, ceil, cos, degrees, exp, floor, sin, tan

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.automatic import AutoWBSettings
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
from wb_tool.domain.scipy_geometry import peaks as peak_functions
from wb_tool.domain.source_geometry import DetectionPlane, filled_membrane, source_detection_plane

FloatArray = NDArray[np.float64]
PixelArray = NDArray[np.uint8 | np.uint16]


@dataclass(frozen=True)
class _Core:
    label: int
    x: float
    y: float
    x0: int
    y0: int
    x1: int
    y1: int
    score: float

    @property
    def height(self) -> int:
        return self.y1 - self.y0


def _closing(values: FloatArray, size: int) -> FloatArray:
    return -ndi.maximum_filter1d(-ndi.maximum_filter1d(values, size, axis=0), size, axis=0)


def _sample(pixels: PixelArray, plane: DetectionPlane) -> FloatArray:
    yy, xx = np.mgrid[: plane.values.shape[0], : plane.values.shape[1]]
    c, s = cos(plane.angle), sin(plane.angle)
    rx = plane.origin_x + c * xx - s * yy
    ry = plane.origin_y + s * xx + c * yy
    return ndi.map_coordinates(pixels.astype(np.float64), [ry, rx], order=1, mode="nearest")


def _marker_end(plane: DetectionPlane, valid: NDArray[np.bool_], scale: float) -> int:
    """A multi-ridge guide hypothesis, used only to exclude detection seeds."""
    residual = np.maximum(_closing(plane.values, max(7, round(scale))) - plane.values, 0)
    residual[~valid] = 0
    horizontal = ndi.gaussian_filter1d(residual.sum(axis=0), max(1.0, scale * 0.04))
    positions, _ = peak_functions.find_peaks(
        horizontal,
        prominence=max(1.0, float(horizontal.max()) * 0.15),
        distance=max(2, round(scale * 0.5)),
    )
    end = 0
    for position in positions:
        if position > plane.values.shape[1] * 0.28:
            continue
        half = max(1, round(scale * 0.18))
        vertical = ndi.gaussian_filter1d(
            residual[:, max(0, int(position) - half) : int(position) + half + 1].mean(axis=1),
            max(1.0, scale * 0.04),
        )
        ridges, _ = peak_functions.find_peaks(
            vertical,
            prominence=max(1.0, float(vertical.max()) * 0.22),
            distance=max(2, round(scale * 0.35)),
        )
        if len(ridges) >= 2:
            # The old .45-scale expansion cut into an adjacent genuine band.
            # Follow the marker's own horizontal extent, with only a small cap.
            right = int(position)
            while (
                right + 1 < len(horizontal) and horizontal[right + 1] > horizontal[position] * 0.25
            ):
                right += 1
            end = max(end, min(right + 2, round(float(position) + scale * 0.25)))
    return end


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
                if abs(q.y - slope * q.x - intercept) <= max(2.0, min(q.height * 0.8, scale * 0.22))
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


def _fit_row(signal: FloatArray, support: NDArray[np.bool_]) -> tuple[float, float]:
    weights: FloatArray = signal * support
    mass = weights.sum(axis=0)
    ys: FloatArray = (weights * np.arange(signal.shape[0], dtype=np.float64)[:, None]).sum(
        axis=0
    ) / np.maximum(mass, 1)
    keep = mass > max(1.0, float(mass.max()) * 0.08)
    xs: FloatArray = np.arange(signal.shape[1], dtype=np.float64)
    if np.count_nonzero(keep) < 3:
        raise ValueError("common_signal_direction_insufficient")
    fit: FloatArray = np.polyfit(xs[keep], ys[keep], 1)
    for _ in range(3):
        residual = np.abs(ys - np.polyval(fit, xs))
        good = keep & (residual < max(1.0, 3 * float(np.median(residual[keep]))))
        if np.count_nonzero(good) >= 3:
            fit = np.polyfit(xs[good], ys[good], 1)
    return float(fit[0]), float(fit[1])


def _basin_centers(profile: FloatArray, scale: float, n: int) -> FloatArray:
    peaks, _ = peak_functions.find_peaks(
        profile,
        prominence=max(1.0, float(profile.max()) * 0.065),
        distance=max(3, round(scale * 0.3)),
    )
    # Basin endpoints and peaks use the same retained signal span. A faint
    # fringe peak outside that span must not create an empty weighted slice.
    peaks = peaks[profile[peaks] > float(profile.max()) * 0.12]
    if not len(peaks):
        raise ValueError("common_row_profile_empty")
    boundaries = [
        int(a + np.argmin(profile[a : b + 1])) for a, b in zip(peaks, peaks[1:], strict=False)
    ]
    while len(boundaries) >= n:
        index = max(
            range(len(boundaries)),
            key=lambda j: (
                float(profile[boundaries[j]])
                / max(1.0, min(float(profile[peaks[j]]), float(profile[peaks[j + 1]])))
            ),
        )
        boundaries.pop(index)
        peaks = np.delete(
            peaks, index if profile[peaks[index]] < profile[peaks[index + 1]] else index + 1
        )
    span = np.flatnonzero(profile > float(profile.max()) * 0.12)
    edges = [int(span[0]), *boundaries, int(span[-1]) + 1]
    return np.array(
        [
            float(np.average(np.arange(a, b), weights=profile[a:b]))
            for a, b in zip(edges, edges[1:], strict=False)
        ],
        dtype=np.float64,
    )


def _slots(
    members: list[_Core], profile: FloatArray, scale: float, n: int
) -> tuple[FloatArray, tuple[int, ...]]:
    groups: list[list[_Core]] = []
    for core in members:
        if len(members) > n and groups and core.x - groups[-1][-1].x < scale * 0.55:
            groups[-1].append(core)
        else:
            groups.append([core])
    centers: FloatArray = np.array(
        [sum(q.x * q.score for q in group) / sum(q.score for q in group) for group in groups],
        dtype=np.float64,
    )
    if len(centers) < n:
        centers = _basin_centers(profile, scale, n)
    if len(centers) > n:
        # Do not silently drop a terminal sample because fragments consumed N.
        raise ValueError("common_slot_scale_ambiguous")
    if len(centers) == n:
        return centers, ()
    if len(centers) < 3:
        raise ValueError("common_terminal_slot_phase_unresolved")
    # A skipped internal lane is recoverable from repeated spacings with both
    # terminal anchors. Missing outer lanes have no equivalent phase evidence.
    gaps = np.diff(centers)
    pitch = float(np.min(gaps))
    indices = np.rint((centers - centers[0]) / pitch).astype(np.int64)
    if (
        indices[-1] != n - 1
        or len(np.unique(indices)) != len(indices)
        or np.max(np.abs(centers - centers[0] - indices * pitch)) > pitch * 0.2
    ):
        raise ValueError("common_terminal_slot_phase_unresolved")
    missing = tuple(i + 1 for i in range(n) if i not in indices)
    return np.linspace(float(centers[0]), float(centers[-1]), n), missing


def _sampling_rectangles(
    lanes: tuple[LaneROI, ...],
    plane: DetectionPlane,
    support: NDArray[np.bool_],
    center_x: float,
    center_y: float,
    width: float,
    angle: float,
) -> tuple[LaneROI, ...]:
    """Keep all N source slots, with a common original-coordinate row envelope.

    The broad display frame is not the quantitative Y extent. Bounding its
    sloping corners can include membrane exterior at large angles. This shared
    envelope contains the selected raw support plus background, and is retained
    through negative slots rather than fitted separately to their intensity.
    """
    sy, sx = np.nonzero(support)
    pc, ps = cos(plane.angle), sin(plane.angle)
    source_x = plane.origin_x + sx * pc - sy * ps
    source_y = plane.origin_y + sx * ps + sy * pc
    slope = tan(angle)
    half_y = float(np.abs(source_y - center_y - (source_x - center_x) * slope).max()) + 3
    left = max(lanes[0].x0, floor(min(center_x - width * cos(angle) / 2, float(source_x.min()))))
    right = min(
        lanes[-1].x1, ceil(max(center_x + width * cos(angle) / 2, float(source_x.max()) + 1))
    )
    valid = plane.valid.astype(np.float64)
    result: list[LaneROI] = []
    for index, lane in enumerate(lanes):
        x0 = left if index == 0 else lane.x0
        x1 = right if index == len(lanes) - 1 else lane.x1
        line_ends = [center_y + (x - center_x) * slope for x in (x0, x1 - 1)]
        y0 = max(lane.y0, floor(min(line_ends) - half_y))
        y1 = min(lane.y1, ceil(max(line_ends) + half_y) + 1)
        selected = (source_x >= x0) & (source_x < x1)
        if np.any((source_y[selected] < y0) | (source_y[selected] >= y1)):
            raise ValueError("common_sampling_cannot_cover_support")
        yy, xx = np.mgrid[y0:y1, x0:x1]
        px = (xx - plane.origin_x) * pc + (yy - plane.origin_y) * ps
        py = -(xx - plane.origin_x) * ps + (yy - plane.origin_y) * pc
        inside = ndi.map_coordinates(valid, [py, px], order=0, mode="constant") > 0
        if not np.all(inside) and np.any(selected) and index in {0, len(lanes) - 1}:
            # Only the first/last slot's outward blank padding may recede.
            # Keep three complete source columns beyond the enclosing selected
            # core, and keep every internal X boundary and the common Y extent.
            # A contour hole in the retained part still fails all(valid).
            invalid_columns = np.flatnonzero(~inside.all(axis=0))
            first, last = 0, inside.shape[1]
            if index == 0:
                maximum_left = floor(float(source_x[selected].min())) - 3
                blank_left = invalid_columns[invalid_columns + x0 < maximum_left]
                if len(blank_left):
                    first = int(blank_left[-1]) + 1
            if index == len(lanes) - 1:
                minimum_right = ceil(float(source_x[selected].max())) + 4
                blank_right = invalid_columns[invalid_columns + x0 >= minimum_right]
                if len(blank_right):
                    last = int(blank_right[0])
            if first < last and np.all(inside[:, first:last]):
                x0, x1 = x0 + first, x0 + last
                inside = inside[:, first:last]
        if not np.all(inside):
            raise ValueError("common_sampling_outside_membrane")
        result.append(LaneROI(lane.lane_id, x0, y0, x1, y1))
    return tuple(result)


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
