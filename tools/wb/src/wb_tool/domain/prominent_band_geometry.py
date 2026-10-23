"""Prominence-ranked fixed-N rows; all filtering remains detection-only.

The score describes image appearance, never protein identity or calibrated
confidence. Existing common-band evidence remains frozen in its own module.
"""

from collections.abc import Callable
from dataclasses import replace
from math import atan, ceil, cos, degrees, exp, floor, log1p, sin

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.automatic import AutoWBSettings
from wb_tool.domain.band_geometry_support import (
    BandCore,
    closing,
    fit_row,
    marker_end,
    sample,
    sampling_rectangles,
    slots,
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
from wb_tool.domain.scipy_geometry import peaks as peak_functions
from wb_tool.domain.source_geometry import DetectionPlane, filled_membrane, source_detection_plane

FloatArray = NDArray[np.float64]
PixelArray = NDArray[np.uint8 | np.uint16]


def _field(
    pixels: PixelArray,
    plane: DetectionPlane,
    settings: AutoWBSettings,
    scale: float,
    *,
    local: bool,
) -> tuple[FloatArray, NDArray[np.int32], list[BandCore]]:
    raw = sample(pixels, plane)
    signed = raw if settings.polarity == "dark" else -raw
    responses = [
        np.maximum(closing(signed, max(7, round(scale * fraction))) - signed, 0)
        for fraction in (0.5, 0.9, 1.4)
    ]
    response = np.median(np.stack(responses), axis=0)
    # Membrane cut edges create thin high-response lines after background
    # subtraction. They locate the field, not sample-band detection seeds.
    valid = ndi.binary_erosion(
        plane.valid, iterations=max(2, round(min(plane.values.shape) * 0.045))
    )
    if not valid.any():
        raise ValueError("prominent_signal_support_insufficient")
    masked = np.ma.array(response, mask=~valid)
    offset = np.ma.median(masked, axis=0).filled(0)
    noise = np.maximum(
        1.0, np.ma.median(np.ma.abs(masked - offset), axis=0).filled(0) / 0.6744897502
    )
    signal: FloatArray = ndi.gaussian_filter(np.maximum(response - offset, 0), 0.8)
    signal[~valid] = 0
    if settings.left_marker != "include":
        signal[:, : marker_end(plane, valid, scale)] = 0
    # Compare local and image-wide hypotheses, rather than making the strongest
    # stain a mandatory threshold for every lane. Local per-column peaks retain
    # cleaner weaker lanes; the global hypothesis can separate their touching
    # halos. Both face the same appearance score and exact-N geometry checks.
    if local:
        level = ndi.maximum_filter1d(signal, max(7, round(scale * 0.8)), axis=0) * 0.35
    else:
        level = float(np.quantile(signal[valid], 0.999)) * 0.35
    labels, _ = ndi.label(signal > np.maximum(np.maximum(2.0, level), 2.5 * noise))
    cores: list[BandCore] = []
    for label, bounds in enumerate(ndi.find_objects(labels), 1):
        if bounds is None:
            continue
        ys, xs = bounds
        support = labels[ys, xs] == label
        height, width = ys.stop - ys.start, xs.stop - xs.start
        if (
            np.count_nonzero(support) < max(6, scale * 0.08)
            or width < max(3, scale * 0.10, height * 0.7)
            or width > raw.shape[1] * 0.95
        ):
            continue
        y, x = np.nonzero(support)
        cores.append(
            BandCore(
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
    # Bounded hypothesis generation. Rank by actual response, not scan order;
    # discarded texture is not declared an absent/zero quantitative sample.
    return signal, labels, sorted(cores, key=lambda q: q.score, reverse=True)[:128]


def _rank_rows(
    cores: list[BandCore],
    signal: FloatArray,
    labels: NDArray[np.int32],
    scale: float,
    n: int,
    angle: float,
    cancelled: Callable[[], bool],
) -> list[tuple[float, list[BandCore]]]:
    rows: dict[tuple[int, ...], tuple[float, list[BandCore]]] = {}
    appearances: dict[int, tuple[float, list[float]]] = {}
    for q in cores:
        area = (q.x1 - q.x0) * q.height
        contrast = q.score / area
        shape = min(1.0, (q.x1 - q.x0) / max(1.0, q.height * 1.5))
        thickness = min(1.0, scale * 0.45 / max(1.0, q.height))
        span = min(1.0, (q.x1 - q.x0) / max(1.0, scale * 0.4))
        # Saturated neighbouring bands may share one connected core. Count its
        # observed profile ridges, while a uniform stripe has one location only.
        local_signal = signal[q.y0 : q.y1, q.x0 : q.x1]
        support = labels[q.y0 : q.y1, q.x0 : q.x1] == q.label
        try:
            component_slope, _ = fit_row(local_signal, support)
        except ValueError:
            component_slope = 0.0
        theta = atan(component_slope)
        sy, sx = np.nonzero(support)
        u = (sx + q.x0 - q.x) * cos(theta) + (sy + q.y0 - q.y) * sin(theta)
        origin = float(u.min())
        bins = np.floor(u - origin).astype(np.int64)
        profile = ndi.gaussian_filter1d(
            np.bincount(bins, weights=local_signal[support]), max(0.8, scale * 0.055)
        )
        padded = np.pad(profile, (1, 1))
        peaks, properties = peak_functions.find_peaks(
            padded,
            prominence=max(1.0, float(profile.max()) * 0.065),
            distance=max(3, round(scale * 0.3)),
        )
        peaks = peaks[properties["prominences"] >= padded[peaks] * 0.3]
        positions = [q.x + (origin + int(p) - 1) * cos(theta) for p in peaks] or [q.x]
        appearances[q.label] = log1p(contrast) * shape * thickness * span, positions
    for first in cores:
        check_detection_cancelled(cancelled)
        hypotheses = [(0.0, first.y)]
        for other in cores:
            if other.x - first.x >= scale * 0.3:
                slope = (other.y - first.y) / (other.x - first.x)
                if abs(degrees(angle + atan(slope))) <= 30:
                    hypotheses.append((slope, first.y - slope * first.x))
        for slope, intercept in hypotheses:
            members = sorted(
                (
                    q
                    for q in cores
                    if abs(q.y - slope * q.x - intercept)
                    <= max(2.0, min(q.height * 0.6, scale * 0.18))
                ),
                key=lambda q: q.x,
            )
            votes: list[tuple[float, float]] = []
            for q in members:
                appearance, positions = appearances[q.label]
                residual = abs(q.y - slope * q.x - intercept)
                vote = appearance * exp(-0.5 * (residual / max(1, q.height * 0.3)) ** 2)
                for x in positions:
                    if votes and x - votes[-1][0] < scale * 0.3:
                        votes[-1] = (x, max(votes[-1][1], vote))
                    else:
                        votes.append((x, vote))
            # Extra lobes cannot buy more than the declared N sample votes.
            # This limits scoring only: geometry below still retains every
            # observed core and rejects an actual sample-count conflict.
            score = sum(sorted((v for _, v in votes), reverse=True)[:n]) * min(n, len(votes)) ** 0.5
            key = tuple(q.label for q in members)
            if key and (key not in rows or score > rows[key][0]):
                rows[key] = score, members
    # No vertical-location preference. Equal scores use signal mass as a
    # deterministic secondary appearance measure, then the stable labels.
    return sorted(
        rows.values(),
        key=lambda item: (item[0], sum(q.score for q in item[1])),
        reverse=True,
    )


def _complete_thin_support(
    pixels: PixelArray,
    plane: DetectionPlane,
    settings: AutoWBSettings,
    signal: FloatArray,
    support: NDArray[np.bool_],
    members: list[BandCore],
    scale: float,
) -> tuple[FloatArray, NDArray[np.bool_], bool]:
    """Complete a selected thin edge only where stronger-scale pixels connect.

    Broad-window responses never enter row ranking. They may recover a thick
    body's extent from its selected edge, but not jump a background valley to
    another row. The original fixed-N centres survive this bounded completion.
    """
    if max(q.height for q in members) > max(4, scale * 0.10):
        return signal, support, False
    raw = sample(pixels, plane)
    signed = raw if settings.polarity == "dark" else -raw
    response = np.maximum(closing(signed, max(7, round(scale * 1.4))) - signed, 0)
    response = ndi.gaussian_filter(response, 0.8)
    level = max(2.0, float(np.median(signal[support])) * 0.35)
    allowed = plane.valid.copy()
    # Limit the exploration around the already selected row in both axes. A
    # remote stain/row cannot become the target through this extent-only step.
    y0 = max(0, floor(min(q.y0 for q in members) - scale * 1.4))
    y1 = min(signal.shape[0], ceil(max(q.y1 for q in members) + scale * 1.4))
    x0 = max(0, floor(min(q.x0 for q in members) - scale * 0.2))
    x1 = min(signal.shape[1], ceil(max(q.x1 for q in members) + scale * 0.2))
    allowed[:y0] = False
    allowed[y1:] = False
    allowed[:, :x0] = False
    allowed[:, x1:] = False
    labels, _ = ndi.label((response > level) & allowed)
    touched = np.unique(labels[support])
    completed = np.isin(labels, touched[touched != 0])
    if not completed.any():
        return signal, support, False
    yy, _ = np.nonzero(completed)
    if int(yy.max() - yy.min() + 1) <= max(q.height for q in members) * 2:
        return signal, support, False
    result = signal.copy()
    result[completed] = response[completed]
    return result, support | completed, True


def _source_field(pixels: PixelArray, settings: AutoWBSettings) -> tuple[DetectionPlane, float]:
    """A uniform acquisition field need not contain a separately visible membrane."""
    values = pixels.astype(np.float64)
    border = np.concatenate((values[0], values[-1], values[:, 0], values[:, -1]))
    base = float(np.median(border))
    signed = base - values if settings.polarity == "dark" else values - base
    noise = detection_noise(border)
    amplitude = float(np.quantile(signed, 0.999))
    if amplitude < max(4.0, 4 * noise) or np.quantile(np.abs(border - base), 0.95) > max(
        4 * noise, amplitude * 0.03
    ):
        raise ValueError("prominent_source_field_unlocated")
    labels, _ = ndi.label(signed > max(4 * noise, amplitude * 0.03))
    widths: list[int] = []
    bounds_all: list[tuple[slice, slice]] = []
    for bounds in ndi.find_objects(labels):
        if bounds is None:
            continue
        ys, xs = bounds
        height, width = ys.stop - ys.start, xs.stop - xs.start
        if width >= max(6, height) and width * height >= 24:
            widths.append(width)
            bounds_all.append(bounds)
    if not widths:
        raise ValueError("prominent_source_field_no_bands")
    scale = float(np.median(widths)) * 1.5
    # Bound expensive filtering to observed contrast plus generous context. This
    # is not a biological membrane mask: all original pixels remain valid here.
    margin = max(12, round(scale))
    x0 = max(0, min(b[1].start for b in bounds_all) - margin)
    y0 = max(0, min(b[0].start for b in bounds_all) - margin)
    x1 = min(values.shape[1], max(b[1].stop for b in bounds_all) + margin)
    y1 = min(values.shape[0], max(b[0].stop for b in bounds_all) + margin)
    raw = values[y0:y1, x0:x1]
    return DetectionPlane(raw, np.ones(raw.shape, dtype=np.bool_), x0, y0, 0.0), scale


def detect_prominent_band_geometry(
    pixels: PixelArray,
    guide: PixelArray | None,
    settings: AutoWBSettings,
    *,
    target: LaneROI | None = None,
    cancelled: Callable[[], bool] = lambda: False,
) -> ReliableDetection:
    """Select the best supported complete fixed-N row, including close doublets."""
    source_only = guide is None or guide is pixels
    guide = pixels if guide is None else guide
    if (
        pixels.ndim != 2
        or pixels.shape != guide.shape
        or pixels.dtype not in (np.dtype("uint8"), np.dtype("uint16"))
        or guide.dtype not in (np.dtype("uint8"), np.dtype("uint16"))
        or min(pixels.shape) < 8
        or pixels.size > 16_000_000
    ):
        raise ValueError("明显条带检测需要同尺寸二维uint8/uint16原像素，最多1600万像素")
    if settings.lane_count is None:
        raise ValueError("明显条带策略需要已确认泳道数")
    n = settings.lane_count
    check_detection_cancelled(cancelled)
    initial = CropDetectionSettings(n, 2, settings.polarity, left_marker=False)
    algorithm = (
        "source_prominent_band_geometry@1" if source_only else "guided_prominent_band_geometry@1"
    )
    membrane, flags = detection_membrane(guide, initial, cancelled)
    if membrane is None:
        membrane, _ = filled_membrane(guide)

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

    try:
        if membrane is None:
            plane, scale = _source_field(pixels, settings)
            flags = (*flags, "uniform_signal_field@1")
        else:
            plane = source_detection_plane(guide, membrane)
            scale = plane.values.shape[1] / (n + 1)
        ranked: list[tuple[float, list[BandCore], FloatArray, NDArray[np.int32], bool]] = []
        for local in (True, False):
            signal, labels, cores = _field(pixels, plane, settings, scale, local=local)
            if target is not None:
                cores = [
                    q
                    for q in cores
                    if target.x0 <= plane.source(q.x, q.y)[0] < target.x1
                    and target.y0 <= plane.source(q.x, q.y)[1] < target.y1
                ]
            ranked.extend(
                (score, members, signal, labels, local)
                for score, members in _rank_rows(
                    cores, signal, labels, scale, n, plane.angle, cancelled
                )
            )
        ranked.sort(key=lambda item: item[0], reverse=True)
        if not ranked:
            return failure("no_prominent_band_row")
        _, anchor_members, anchor_signal, anchor_labels, _ = ranked[0]
        anchor_support = np.isin(anchor_labels, [q.label for q in anchor_members])
        anchor_slope, anchor_intercept = fit_row(anchor_signal, anchor_support)
        anchor_height = float(np.median([q.height for q in anchor_members]))
        failures: list[str] = []
        for score, members, signal, labels, local in ranked:
            check_detection_cancelled(cancelled)
            try:
                support = np.isin(labels, [q.label for q in members])
                slope, intercept = fit_row(signal, support)
                # Resolve appearance before testing N. Retry another threshold
                # for the same physical row, never a weaker distant row merely
                # because its component count happens to fit the declared N.
                compare_x = float(np.median([q.x for q in anchor_members]))
                if abs((slope - anchor_slope) * compare_x + intercept - anchor_intercept) > max(
                    3.0, min(anchor_height, float(np.median([q.height for q in members]))) * 0.6
                ):
                    continue
                signal, support, completed = _complete_thin_support(
                    pixels, plane, settings, signal, support, members, scale
                )
                if completed:
                    slope, intercept = fit_row(signal, support)
                angle = plane.angle + atan(slope)
                if abs(degrees(angle)) > 30:
                    raise ValueError("prominent_angle_outside_support")
                ys, xs = np.mgrid[: signal.shape[0], : signal.shape[1]]
                half = max(max(q.height for q in members) * 0.65, scale * 0.22)
                row = np.abs(ys - (slope * xs + intercept)) <= half
                profile = ndi.gaussian_filter1d((signal * row).sum(axis=0), max(0.8, scale * 0.055))
                left = max(0, floor(min(q.x0 for q in members) - scale * 0.2))
                right = min(signal.shape[1], ceil(max(q.x1 for q in members) + scale * 0.2))
                profile[:left], profile[right:] = 0, 0
                centers, missing = slots(members, profile, scale, n)
                relative_angle = atan(slope)
                pitch = (
                    float(np.median(np.diff(centers))) / cos(relative_angle)
                    if n > 1
                    else max(max(q.x1 - q.x0 for q in members) * 1.2, scale * 0.7)
                )
                mid = float((centers[0] + centers[-1]) / 2)
                center_y = slope * mid + intercept
                cx, cy = plane.source(mid, center_y)
                sy, sx = np.nonzero(support)
                u = (sx - mid) * cos(relative_angle) + (sy - center_y) * sin(relative_angle)
                v = -(sx - mid) * sin(relative_angle) + (sy - center_y) * cos(relative_angle)
                # Vertical signal thickness must not enlarge the horizontal
                # sample pitch. Preserve all N positions and the complete row;
                # only observed horizontal extent can refine the outer margin.
                needed = max(pitch, (float(np.abs(u).max()) + 2) * 2 / n)
                if needed > pitch * 1.35:
                    raise ValueError("prominent_slot_width_cannot_cover_support")
                frame_height = max(pitch * 0.8, (float(np.abs(v).max()) + 2) * 2)
                frame, crop, lanes = fixed_lane_frame(
                    n,
                    needed,
                    cx,
                    cy,
                    degrees(angle),
                    pixels.shape[1],
                    pixels.shape[0],
                    max_angle=30,
                    frame_height=frame_height,
                )
                lanes = sampling_rectangles(lanes, plane, support, cx, cy, frame.width, angle)
                evidence = (
                    *flags,
                    "prominent_band_row@1",
                    "signal_orientation_fit@3",
                    "fixed_n_frame@2",
                    "prominent_envelope_frame@1",
                    "source_axis_partition@2",
                    "common_sampling_crop_limits@1",
                    f"prominent_row_score:{score:.6f}",
                    f"prominent_row_cores:{len(members)}",
                    "column_local_threshold@1" if local else "global_core_threshold@1",
                    *(("multiscale_extent_completed@1",) if completed else ()),
                    *(f"grid_signal_unresolved:{i}" for i in missing),
                )
                snrs = tuple(
                    float(np.ptp(pixels[r.y0 : r.y1, r.x0 : r.x1].astype(float)))
                    / max(
                        1.0, detection_noise(pixels[r.y0 : r.y1, r.x0 : r.x1].astype(float).ravel())
                    )
                    for r in lanes
                )
                candidate = CropCandidate(
                    crop,
                    round(cy),
                    snrs,
                    tuple(i for i in range(1, n + 1) if i not in missing),
                    missing,
                    (),
                    evidence,
                    lanes,
                    frame,
                )
                return ReliableDetection(
                    replace(initial, crop_height=crop.y1 - crop.y0),
                    pixels.shape[1],
                    pixels.shape[0],
                    membrane,
                    None,
                    crop,
                    (candidate,),
                    evidence,
                    algorithm,
                    lanes,
                    missing,
                )
            except ValueError as error:
                failures.append(str(error))
        return failure("prominent_rows_failed:" + ",".join(dict.fromkeys(failures)))
    except ValueError as error:
        check_detection_cancelled(cancelled)
        return failure(str(error))
