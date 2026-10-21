"""Conservative small-N geometry from independent original-pixel components.

This is a versioned detection fallback, not a measurement or a classifier of
protein identity. A component which cannot support a complete isolated row does
not become a guessed lane. The guide supplies a mask, never the signal angle.
"""

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from math import atan, ceil, cos, degrees, floor, radians, sin

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.automatic import AutoWBSettings
from wb_tool.domain.crop_detection import (
    CropCandidate,
    CropDetection,
    CropDetectionSettings,
    check_detection_cancelled,
    detection_membrane,
)
from wb_tool.domain.fixed_lane_frame import fixed_lane_frame
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.scipy_geometry import filters as ndi
from wb_tool.domain.scipy_geometry import peaks as peak_functions
from wb_tool.domain.source_geometry import filled_membrane, source_detection_plane


@dataclass(frozen=True)
class SignalComponent:
    x: float
    y: float
    box: LaneROI
    slope: float
    residual: float
    snr: float
    touches_boundary: bool
    footprint: NDArray[np.bool_] = field(compare=False, repr=False)
    support_id: int


@dataclass(frozen=True)
class ReliableDetection(CropDetection):
    """New detection-only evidence, explicitly copied into the v3 crop record."""

    sampling_limits: tuple[LaneROI, ...] = ()
    review_positions: tuple[int, ...] = ()


def _signal_field(
    pixels: NDArray[np.uint8 | np.uint16],
    valid: NDArray[np.bool_],
    membrane: LaneROI,
    settings: AutoWBSettings,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    raw = pixels[membrane.y0 : membrane.y1, membrane.x0 : membrane.x1].astype(float)
    signed = raw if settings.polarity == "dark" else -raw
    # Vertical closing follows slow illumination gradients. A maximum filter
    # alone turns those gradients into bridges between unrelated bands.
    span = max(7, 2 * (raw.shape[0] // 6) + 1)
    dilated = ndi.maximum_filter1d(signed, span, axis=0)
    background = -ndi.maximum_filter1d(-dilated, span, axis=0)
    residual = background - signed
    # Closing is an upper envelope: even symmetric background noise has a
    # positive residual. Centre that background before applying the stated SNR
    # threshold, otherwise a 4-sigma threshold becomes roughly 1–2 sigma.
    # This changes detection only; neither source pixels nor quantitative ROIs
    # are background-subtracted.
    # Estimate each source column locally. Texture elsewhere on the membrane
    # must not raise the threshold of a clean, weak terminal sample.
    residual_masked = np.ma.array(residual, mask=~valid)
    offset = np.ma.median(residual_masked, axis=0).filled(0)
    strength = np.maximum(residual - offset, 0)
    # Adjacent-pixel differences underestimate correlated detector/background
    # texture. Use the larger robust scale of the original differences and the
    # background residual; both are independent of the strongest sample band.
    dispersion = np.ma.median(np.ma.abs(residual_masked - offset), axis=0).filled(0) / 0.6744897502
    differences = np.ma.array(np.diff(raw, axis=0), mask=~(valid[1:] & valid[:-1]))
    center = np.ma.median(differences, axis=0)
    adjacent = np.ma.median(np.ma.abs(differences - center), axis=0).filled(0) / 0.9538725524
    noise = np.maximum(1, np.maximum(adjacent, dispersion))
    strength[~valid] = 0
    return strength, noise


def _components(
    pixels: NDArray[np.uint8 | np.uint16],
    valid: NDArray[np.bool_],
    membrane: LaneROI,
    settings: AutoWBSettings,
) -> list[SignalComponent]:
    strength, noise = _signal_field(pixels, valid, membrane, settings)
    # Retain all noise-supported pixels. Connected halos do not prove that two
    # separated profile peaks are one lane; conversely a bright core must not
    # replace the full extent of its weak supporting band.
    support_labels, _ = ndi.label(strength > settings.min_snr * noise)
    support_boxes = ndi.find_objects(support_labels)
    boundary = valid & ~ndi.binary_erosion(valid, iterations=1)
    result: list[SignalComponent] = []
    regions: list[tuple[slice, slice, NDArray[np.bool_], int]] = []
    for index, bounds in enumerate(support_boxes, 1):
        if bounds is None:
            continue
        ys, xs = bounds
        mask = support_labels[ys, xs] == index
        if np.count_nonzero(mask) < 6:
            continue
        height = ys.stop - ys.start
        profile = (strength[ys, xs] * mask).sum(axis=0)
        profile = ndi.gaussian_filter1d(profile, max(1.0, height * 0.08))
        peaks, properties = peak_functions.find_peaks(
            profile,
            prominence=settings.min_snr * height**0.5 * float(np.median(noise[xs])),
            distance=max(3, round(height * 0.7)),
        )
        peaks = peaks[properties["prominences"] >= profile[peaks] * 0.4]
        cuts = [
            int(a + np.argmin(profile[a : b + 1])) + 1
            for a, b in zip(peaks, peaks[1:], strict=False)
            if float(profile[a : b + 1].min()) < min(profile[a], profile[b]) * 0.8
        ]
        edges = [0, *cuts, xs.stop - xs.start]
        for left, right in zip(edges, edges[1:], strict=False):
            part = mask[:, left:right]
            if not part.any():
                continue
            py, px = np.nonzero(part)
            sub_y = slice(ys.start + int(py.min()), ys.start + int(py.max()) + 1)
            sub_x = slice(xs.start + left + int(px.min()), xs.start + left + int(px.max()) + 1)
            regions.append((sub_y, sub_x, support_labels[sub_y, sub_x] == index, index))
    if len(regions) > 200:
        return []
    for ys, xs, mask, support_id in regions:
        if np.count_nonzero(mask) < 6:
            continue
        weight = strength[ys, xs] * mask
        yy, xx = np.mgrid[ys, xs]
        column_weight = weight.sum(axis=0)
        supported = column_weight > column_weight.max() * 0.2
        inset = max(1, round((xs.stop - xs.start) * 0.15))
        supported[:inset] = False
        supported[-inset:] = False
        positions: NDArray[np.float64] = np.arange(xs.start, xs.stop, dtype=np.float64)[supported]
        slope, fit_residual = 0.0, float("inf")
        if len(positions) >= 3:
            centers: NDArray[np.float64] = (yy * weight).sum(axis=0)[supported] / column_weight[
                supported
            ]
            fit: NDArray[np.float64] = np.polyfit(positions, centers, 1)
            slope = float(fit[0])
            fit_residual = float(np.max(np.abs(centers - np.polyval(fit, positions))))
        # A narrow bright core may leave too few columns to estimate direction.
        # Retain the entire observed component as an exclusion: an unfit signal
        # is not an absent sample and cannot justify accepting the strongest N.
        result.append(
            SignalComponent(
                float(np.average(xx, weights=weight)) + membrane.x0,
                float(np.average(yy, weights=weight)) + membrane.y0,
                LaneROI(
                    "component",
                    xs.start + membrane.x0,
                    ys.start + membrane.y0,
                    xs.stop + membrane.x0,
                    ys.stop + membrane.y0,
                ),
                slope,
                fit_residual,
                float(np.max(weight / noise[xs])),
                bool(np.any(mask & boundary[ys, xs])),
                mask.copy(),
                support_id,
            )
        )
    return result


def _intersects(a: LaneROI, b: LaneROI) -> bool:
    return a.x0 < b.x1 and b.x0 < a.x1 and a.y0 < b.y1 and b.y0 < a.y1


def component_intersects(roi: LaneROI, component: SignalComponent) -> bool:
    """Bounding-box contact alone is not a signal in a quantitative rectangle."""
    b = component.box
    if not _intersects(roi, b):
        return False
    return bool(
        component.footprint[
            max(roi.y0, b.y0) - b.y0 : min(roi.y1, b.y1) - b.y0,
            max(roi.x0, b.x0) - b.x0 : min(roi.x1, b.x1) - b.x0,
        ].any()
    )


def _edge_marks(
    components: list[SignalComponent],
    chosen: list[SignalComponent],
    membrane: LaneROI,
) -> list[SignalComponent]:
    """A location-and-shape hypothesis, never permission to erase raw pixels.

    Whole horizontal bands remain evidence even at the edge. Short, non-band
    strokes can form one annotation near an edge; a stroke inside a quantitative
    slot still fails the later overlap check. No file names or brightness ranks
    participate in this rule.
    """
    scale = float(np.median([b.box.width for b in chosen]))
    height = membrane.y1 - membrane.y0
    possible = [
        b
        for b in components
        if b not in chosen
        and b.box.width < scale * 0.65
        and (
            b.box.width < (b.box.y1 - b.box.y0) * 1.2
            or abs(degrees(atan(b.slope))) > 30
            or not np.isfinite(b.residual)
            or b.touches_boundary
        )
    ]
    marks = [
        b
        for b in possible
        if b.touches_boundary
        or b.box.x1 <= membrane.x0 + membrane.width * 0.2
        or b.box.x0 >= membrane.x1 - membrane.width * 0.2
        or b.box.y1 <= membrane.y0 + height * 0.2
        or b.box.y0 >= membrane.y1 - height * 0.2
    ]
    # Follow nearby pen strokes from an edge anchor, without crossing a sample.
    # Each member retains its own original bbox for quantitative exclusion.
    for _ in possible:
        added = [
            b
            for b in possible
            if b not in marks
            and any(
                max(0, b.box.x0 - m.box.x1, m.box.x0 - b.box.x1) ** 2
                + max(0, b.box.y0 - m.box.y1, m.box.y0 - b.box.y1) ** 2
                <= (height * 0.25) ** 2
                for m in (*marks, *(c for c in components if c.touches_boundary))
            )
        ]
        if not added:
            break
        marks.extend(added)
    return marks


def _shared_guide_marks(
    components: list[SignalComponent],
    guide_components: list[SignalComponent],
    membrane: LaneROI,
) -> list[SignalComponent]:
    """Only a same-position mark in a separately verified white-light image.

    An extra band in the selected source alone is not evidence of a marker.
    Right-hand horizontal guide bands are never removed by this rule.
    """
    marks: list[SignalComponent] = []
    for guide in guide_components:
        ladder = guide.x < membrane.x0 + membrane.width * 0.28 and any(
            other != guide
            and abs(other.x - guide.x) < min(other.box.width, guide.box.width) * 0.5
            and not (other.box.y0 < guide.box.y1 and guide.box.y0 < other.box.y1)
            for other in guide_components
        )
        non_band = (
            guide.box.width < (guide.box.y1 - guide.box.y0) * 1.5
            or abs(degrees(atan(guide.slope))) > 30
        )
        if not ladder and not non_band:
            continue
        for signal in components:
            intersection = max(
                0, min(signal.box.x1, guide.box.x1) - max(signal.box.x0, guide.box.x0)
            ) * max(0, min(signal.box.y1, guide.box.y1) - max(signal.box.y0, guide.box.y0))
            area = signal.box.width * (signal.box.y1 - signal.box.y0)
            if intersection >= area * 0.6 and signal not in marks:
                marks.append(signal)
    return marks


def _fixed_rows(bands: list[SignalComponent], width: float) -> list[list[SignalComponent]]:
    """Find whole-row hypotheses without assigning one component to one slot.

    Pairwise local band slopes are not row directions: diffuse lobes can have
    different intensity centroids. Hypotheses use a common line and retain all
    compatible components, including weak ones. No intensity rank selects N.
    """
    hypotheses: set[frozenset[int]] = set()
    for i, a in enumerate(bands):
        slopes = [a.slope]
        slopes.extend(
            (b.y - a.y) / (b.x - a.x)
            for b in bands[i + 1 :]
            if abs(b.x - a.x) >= width * 0.5 and abs(degrees(atan((b.y - a.y) / (b.x - a.x)))) <= 10
        )
        for slope in slopes:
            if abs(degrees(atan(slope))) > 10:
                continue
            members = frozenset(
                j
                for j, b in enumerate(bands)
                if abs(b.y - a.y - (b.x - a.x) * slope) <= width * 0.18
            )
            if members:
                hypotheses.add(members)
    # Subsets are not alternative complete targets. Disjoint/overlapping
    # maximal hypotheses remain alternatives and are rejected by the caller.
    maximal = [h for h in hypotheses if not any(h < other for other in hypotheses)]
    return [[bands[i] for i in sorted(h)] for h in sorted(maximal, key=lambda h: sorted(h))]


def _row_line(
    row: list[SignalComponent], strength: NDArray[np.float64], membrane: LaneROI
) -> tuple[float, float, float, float]:
    """Fit observed signal column centres with equal weight per source column."""
    x0, x1 = min(b.box.x0 for b in row), max(b.box.x1 for b in row)
    weights = np.zeros(x1 - x0)
    vertical = np.zeros(x1 - x0)
    for b in row:
        values = (
            strength[
                b.box.y0 - membrane.y0 : b.box.y1 - membrane.y0,
                b.box.x0 - membrane.x0 : b.box.x1 - membrane.x0,
            ]
            * b.footprint
        )
        yy = np.arange(b.box.y0, b.box.y1)[:, None]
        left, right = b.box.x0 - x0, b.box.x1 - x0
        weights[left:right] += values.sum(axis=0)
        vertical[left:right] += (values * yy).sum(axis=0)
    supported = weights > 0
    xs = np.arange(x0, x1, dtype=float)[supported]
    ys = vertical[supported] / weights[supported]
    fit = np.polyfit(xs, ys, 1)
    center = (x0 + x1) / 2
    return (
        center,
        float(np.polyval(fit, center)),
        float(fit[0]),
        float(np.max(np.abs(ys - np.polyval(fit, xs)))),
    )


def _seed_grid_conflict(
    chosen: list[SignalComponent],
    components: list[SignalComponent],
    shared_marks: list[SignalComponent],
    width: float,
    count: int,
    strength: NDArray[np.float64],
    membrane: LaneROI,
) -> bool:
    """Reject contradictory independent support before refining an estimated grid.

    Peak splits of one connected strip cannot establish independent anchors.
    This is only a rejection check; connected/fragmented rows need no anchors
    to proceed through the existing whole-row geometry checks.
    """
    support_counts: dict[int, int] = {}
    for component in components:
        support_counts[component.support_id] = support_counts.get(component.support_id, 0) + 1
    independent = [b for b in chosen if support_counts[b.support_id] == 1]
    anchors = sorted(
        (b for b in independent if width * 0.5 <= b.box.width <= width), key=lambda b: b.x
    )
    if count < 2 or len(anchors) < count:
        return False
    _, _, slope, _ = _row_line(anchors, strength, membrane)
    if abs(degrees(atan(slope))) > 10:
        return False
    ca, sa = cos(atan(slope)), sin(atan(slope))
    positions = np.array([b.x * ca + b.y * sa for b in anchors])
    # Test the whole set against one grid, not just consecutive gaps. No
    # strongest/first subset is selected when the anchor set is ambiguous.
    offsets = positions - np.arange(len(anchors)) * width
    origin = float(np.median(offsets))
    if np.any(abs(offsets - origin) > width * 0.2):
        return False
    if len(anchors) > count:
        return True
    phase = origin + (count - 1) * width / 2
    reach = (count / 2 + 0.25) * width
    for b in independent:
        if b in anchors or b in shared_marks:
            continue
        yy, xx = np.nonzero(b.footprint)
        local = (xx + b.box.x0) * ca + (yy + b.box.y0) * sa - phase
        if local.min() > reach or local.max() < -reach:
            return True
    return False


def _ridge_columns(row: list[SignalComponent], width: float) -> tuple[set[int], int]:
    """Retain local second ridges even when they occupy only one lane."""
    columns: dict[int, set[int]] = {}
    for b in row:
        yy, xx = np.nonzero(b.footprint)
        for x, y in zip(xx + b.box.x0, yy + b.box.y0, strict=True):
            columns.setdefault(int(x), set()).add(int(y))
    repeated: set[int] = set()
    for x, values in columns.items():
        ys = np.array(sorted(values))
        runs = np.split(ys, np.flatnonzero(np.diff(ys) > max(2, width * 0.06)) + 1)
        if sum(len(run) >= 2 for run in runs) > 1:
            repeated.add(x)
    return repeated, len(columns)


def _sampling_limits(
    lanes: tuple[LaneROI, ...],
    excluded: list[SignalComponent],
    valid: NDArray[np.bool_],
    membrane: LaneROI,
) -> tuple[LaneROI, ...]:
    """Maximal contiguous source Y intervals without contour gaps or exclusions."""
    result: list[LaneROI] = []
    for lane in lanes:
        unsafe = ~valid[:, lane.x0 - membrane.x0 : lane.x1 - membrane.x0].all(axis=1)
        for b in excluded:
            left, right = max(lane.x0, b.box.x0), min(lane.x1, b.box.x1)
            if left < right:
                rows = b.footprint[:, left - b.box.x0 : right - b.box.x0].any(axis=1)
                unsafe[np.flatnonzero(rows) + b.box.y0 - membrane.y0] = True
        above = np.flatnonzero(unsafe[: lane.y0 - membrane.y0])
        below = np.flatnonzero(unsafe[lane.y1 - membrane.y0 :])
        result.append(
            replace(
                lane,
                y0=membrane.y0 + int(above[-1]) + 1 if len(above) else membrane.y0,
                y1=lane.y1 + int(below[0]) if len(below) else membrane.y1,
            )
        )
    return tuple(result)


def detect_reliable_geometry(
    signal: NDArray[np.uint8 | np.uint16],
    guide: NDArray[np.uint8 | np.uint16],
    settings: AutoWBSettings,
    *,
    target: LaneROI | None = None,
    lane_width: float | None = None,
    width_is_estimate: bool = False,
    registration_target: bool = False,
    exclude_guide_marks: bool = False,
    cancelled: Callable[[], bool] = lambda: False,
) -> ReliableDetection:
    """Align known-N geometry; a supplied original-pixel width fixes the grid."""
    if signal.ndim != 2 or signal.shape != guide.shape:
        raise ValueError("辅助定位与信号原图须为相同原像素尺寸")
    check_detection_cancelled(cancelled)
    if lane_width is not None and (not np.isfinite(lane_width) or lane_width < 2):
        raise ValueError("固定网格须提供有效的原像素槽宽")
    initial = CropDetectionSettings(
        settings.lane_count or 1, 2, settings.polarity, left_marker=False
    )
    membrane, flags = detection_membrane(guide, initial, cancelled)
    if membrane is None:
        membrane, multiple = filled_membrane(guide)
        flags = ("filled_guide_contour@1", *(("multiple_membranes",) if multiple else ()))

    def failure(reason: str) -> ReliableDetection:
        return ReliableDetection(
            initial,
            signal.shape[1],
            signal.shape[0],
            membrane,
            None,
            None,
            (),
            (*flags, reason),
            "instrument_guided_geometry@2",
        )

    if membrane is None:
        return failure("guide_membrane_unlocated")
    if "multiple_membranes" in flags:
        return failure("guide_multiple_membranes")
    try:
        plane = source_detection_plane(guide, membrane)
    except ValueError as exc:
        return failure(str(exc))
    c, s = cos(plane.angle), sin(plane.angle)
    py, px = np.nonzero(plane.valid)
    source_x = plane.origin_x + px * c - py * s
    source_y = plane.origin_y + px * s + py * c
    # The discovery bbox uses 50% row/column occupancy and cuts tilted corners.
    # Reconstruct the actual contour extent before sampling its validity mask.
    membrane = LaneROI(
        "membrane",
        max(0, floor(float(source_x.min()))),
        max(0, floor(float(source_y.min()))),
        min(signal.shape[1], ceil(float(source_x.max())) + 1),
        min(signal.shape[0], ceil(float(source_y.max())) + 1),
    )
    flags = (*flags, "source_contour_extent@1")
    yy, xx = np.mgrid[membrane.y0 : membrane.y1, membrane.x0 : membrane.x1]
    uu = (xx - plane.origin_x) * c + (yy - plane.origin_y) * s
    vv = -(xx - plane.origin_x) * s + (yy - plane.origin_y) * c
    valid = ndi.map_coordinates(plane.valid.astype(float), [vv, uu], order=0, mode="constant") > 0.5
    valid = ndi.binary_erosion(valid, iterations=2)
    components = _components(signal, valid, membrane, settings)
    if not components:
        return failure("no_sample_bands")
    shared_marks = (
        _shared_guide_marks(components, _components(guide, valid, membrane, settings), membrane)
        if exclude_guide_marks
        else []
    )
    # Horizontal shape supports a band hypothesis; narrow marks remain in the
    # overlap checks and can never be included just to meet the requested N.
    bands = [
        b
        for b in components
        if not b.touches_boundary
        and (
            b.box.width >= lane_width * 0.22
            and (b.box.y1 - b.box.y0) - abs(b.slope) * b.box.width <= lane_width * 0.8
            if lane_width is not None
            else b.box.width >= max((b.box.y1 - b.box.y0) * 0.9, (membrane.y1 - membrane.y0) * 0.08)
        )
        and abs(degrees(atan(b.slope))) <= 30
        and b.residual <= max(1.5, (b.box.y1 - b.box.y0) * 0.2)
    ]
    # Multiple bands in a left column alone cannot distinguish a ladder from a
    # sample with multiple targets. Retain it in the N and ambiguity checks.
    rows: list[list[SignalComponent]] = []
    for band in sorted(bands, key=lambda b: (b.y, b.x)) if lane_width is None else []:
        matches = [
            row
            for row in rows
            if all(
                abs((band.y - other.y) - (band.x - other.x) * (band.slope + other.slope) / 2)
                <= max(2, min(band.box.y1 - band.box.y0, other.box.y1 - other.box.y0) * 0.6)
                for other in row
            )
        ]
        if len(matches) > 1:
            return failure("signal_rows_ambiguous")
        if matches:
            matches[0].append(band)
        else:
            rows.append([band])

    if lane_width is not None:
        rows = _fixed_rows(bands, lane_width)
        # Preserve the original hypotheses, and also evaluate the row without
        # small marks independently corroborated by white light. Full-width
        # bands are never removed to force N. Exclusions still face the final
        # quantitative-rectangle overlap check.
        clean_rows = [
            [b for b in row if not (b in shared_marks and b.box.width < lane_width * 0.4)]
            for row in rows
        ]
        rows.extend(row for row in clean_rows if row and row not in rows)

    def fits_width(row: list[SignalComponent]) -> bool:
        if lane_width is None:
            return len(row) == settings.lane_count
        span = max(b.box.x1 for b in row) - min(b.box.x0 for b in row)
        if width_is_estimate:
            occupied: set[int] = set()
            for b in row:
                occupied.update((np.flatnonzero(b.footprint.any(axis=0)) + b.box.x0).tolist())
            # Preserve the existing estimated-pitch plausibility limit (a
            # sample supports at least 1/2.5 of its pitch) at whole-row level.
            # A user-calibrated grid is not inferred from this intensity support.
            if len(occupied) < (settings.lane_count or 1) * lane_width / 2.5:
                return False
        # Whole-row support locates the fixed template. An unobserved terminal
        # slot cannot be guessed from a short fragment merely because N is known.
        return (
            max(0.4, (settings.lane_count or 1) - 0.9) * lane_width
            <= span
            <= ((settings.lane_count or 1) + (0.5 if width_is_estimate else 0)) * lane_width
            + 0.8 * lane_width * sin(radians(10))
        )

    candidates = [sorted(row, key=lambda b: b.x) for row in rows if fits_width(row)]
    if target is not None:
        candidates = [
            row
            for row in candidates
            if all(target.x0 <= b.x < target.x1 and target.y0 <= b.y < target.y1 for b in row)
        ]
    if not candidates:
        return failure("explicit_lane_count_conflicts_with_evidence")

    def evaluate(
        chosen: list[SignalComponent], lane_width: float | None = lane_width
    ) -> ReliableDetection:
        uncertain: list[SignalComponent] = []
        if lane_width is not None:
            strength, _ = _signal_field(signal, valid, membrane, settings)
            if width_is_estimate and _seed_grid_conflict(
                chosen,
                components,
                shared_marks,
                lane_width,
                settings.lane_count or 1,
                strength,
                membrane,
            ):
                return failure("explicit_lane_count_conflicts_with_evidence")
            cx, cy, fitted_slope, _ = _row_line(chosen, strength, membrane)
            ca, sa = cos(atan(fitted_slope)), sin(atan(fitted_slope))
            # The fixed row may contain weak disconnected lobes or a connected
            # band split by peak finding. Retain such support inside the grid;
            # neither shape nor component count makes it an additional lane.
            original_chosen = chosen
            chosen = sorted(
                (
                    b
                    for b in components
                    if b in chosen
                    or (
                        not b.touches_boundary
                        and abs((b.x - cx) * ca + (b.y - cy) * sa)
                        < (settings.lane_count or 1) * lane_width / 2
                        and (
                            abs(-(b.x - cx) * sa + (b.y - cy) * ca) < lane_width * 0.18
                            or (
                                abs(-(b.x - cx) * sa + (b.y - cy) * ca) < lane_width * 0.4
                                and any(_intersects(b.box, member.box) for member in chosen)
                            )
                        )
                    )
                ),
                key=lambda b: b.x,
            )
            uncertain = [
                b
                for b in chosen
                if b not in original_chosen
                and abs(-(b.x - cx) * sa + (b.y - cy) * ca) >= lane_width * 0.18
            ]
        if lane_width is None and any(
            a.box.x1 > b.box.x0 for a, b in zip(chosen, chosen[1:], strict=False)
        ):
            return failure("signal_rows_ambiguous")
        widths = np.array([b.box.width for b in chosen], dtype=float)
        if lane_width is None and widths.max() > widths.min() * 2:
            return failure("lane_shape_ambiguous")
        xs, ys = np.array([b.x for b in chosen]), np.array([b.y for b in chosen])
        if len(chosen) > 1:
            gaps = np.diff(xs)
            pitch = float(np.median(gaps))
            if lane_width is None and (
                np.any(np.abs(gaps - pitch) > pitch * 0.2) or pitch > float(widths.max()) * 2.5
            ):
                return failure("lane_spacing_ambiguous")
            fit = np.polyfit(xs, ys, 1)
            residual = float(np.max(np.abs(ys - np.polyval(fit, xs))))
            slope = float(fit[0])
            if lane_width is None and residual > max(
                1.5, float(np.median([b.box.y1 - b.box.y0 for b in chosen])) * 0.2
            ):
                return failure("signal_orientation_ambiguous")
        else:
            pitch = float(widths[0]) * 1.4
            slope = chosen[0].slope
        center_x, center_y = float(np.mean(xs)), float(np.mean(ys))
        if lane_width is not None:
            strength, _ = _signal_field(signal, valid, membrane, settings)
            center_x, center_y, slope, residual = _row_line(chosen, strength, membrane)
            ridges, supported_columns = _ridge_columns(chosen, lane_width)
            if len(ridges) >= max(3, supported_columns * 0.25):
                return failure("signal_rows_ambiguous")
            if residual > lane_width * 0.18:
                return failure("signal_orientation_ambiguous")
        target_height = float(np.median([b.box.y1 - b.box.y0 for b in chosen]))
        edge_marks = _edge_marks(components, chosen, membrane)

        def separated_guide_mark(b: SignalComponent) -> bool:
            # Exclusion explains a separate observed mark, never deletes a chosen
            # sample; original-pixel slot overlap remains checked below.
            return b in shared_marks and b not in chosen

        if (target is None or registration_target) and any(
            b not in chosen and b not in edge_marks and not separated_guide_mark(b) for b in bands
        ):
            return failure("guided_target_ambiguous")
        if any(
            abs(b.y - (center_y + (b.x - center_x) * slope))
            <= max(target_height, b.box.y1 - b.box.y0) * 0.6
            for b in components
            if b not in chosen and b not in edge_marks and not separated_guide_mark(b)
        ):
            return failure("additional_signal_at_target_row")
        angle = degrees(atan(slope))
        orientation_agrees = abs(angle) <= 10 and (
            lane_width is not None or all(abs(degrees(atan(b.slope)) - angle) <= 3 for b in chosen)
        )
        # When direction lacks independent support, keep an unrotated frame only if
        # all original component boxes and exclusions pass the same containment test.
        angle = angle if orientation_agrees and abs(angle) >= 0.2 else 0.0
        # Local frame dimensions follow the laboratory's fixed 5N:4 contract.
        # Peak spacing is only an uncalibrated width estimate; a verified width,
        # when supplied, must remain independent of intensity or blob boundaries.
        calibrated = lane_width is not None
        lane_width = lane_width if lane_width is not None else pitch / cos(radians(angle))
        width_refined = False
        if calibrated and width_is_estimate:
            ca, sa = cos(radians(angle)), sin(radians(angle))
            extent = 0.0
            for b in chosen:
                by, bx = np.nonzero(b.footprint)
                u = (bx + b.box.x0 - center_x) * ca + (by + b.box.y0 - center_y) * sa
                extent = max(extent, float(np.max(np.abs(u))) + (abs(ca) + abs(sa)) / 2)
            required = 2 * extent / (settings.lane_count or 1)
            # An estimate may absorb sub-slot edge localization uncertainty;
            # it cannot acquire more than half an additional slot. A declared
            # calibration never reaches this refinement branch.
            if required > lane_width * (1 + 0.5 / (settings.lane_count or 1)):
                return failure("source_width_estimate_conflicts_with_support")
            width_refined = required > lane_width
            lane_width = max(lane_width, required)
        try:
            frame, crop, grid = fixed_lane_frame(
                settings.lane_count or 1,
                lane_width,
                center_x,
                center_y,
                angle,
                signal.shape[1],
                signal.shape[0],
            )
        except ValueError:
            return failure("target_frame_exceeds_membrane")
        cx, cy = frame.center_x, frame.center_y
        ca, sa = cos(radians(angle)), sin(radians(angle))
        corners = [
            (cx + ca * x - sa * y, cy + sa * x + ca * y)
            for x in (-frame.width / 2, frame.width / 2)
            for y in (-frame.height / 2, frame.height / 2)
        ]
        if any(
            x < membrane.x0 or x >= membrane.x1 or y < membrane.y0 or y >= membrane.y1
            for x, y in corners
        ):
            return failure("target_frame_exceeds_membrane")
        if calibrated:
            # C encloses the rotated display rectangle. Q need not consume its
            # unused side corners: keep the projected fixed grid plus every
            # actual target pixel, without drawing border fragments into Q.
            left = max(
                crop.x0, min(floor(cx - frame.width * ca / 2), min(b.box.x0 for b in chosen))
            )
            right = min(
                crop.x1, max(ceil(cx + frame.width * ca / 2), max(b.box.x1 for b in chosen))
            )
            grid = tuple(
                replace(r, x0=left if i == 0 else r.x0, x1=right if i == len(grid) - 1 else r.x1)
                for i, r in enumerate(grid)
            )
            rectangles: list[LaneROI] = []
            for r in grid:
                ys_in_slot: list[int] = []
                for b in chosen:
                    if not component_intersects(r, b):
                        continue
                    y, x = np.nonzero(b.footprint)
                    x, y = x + b.box.x0, y + b.box.y0
                    selected = (x >= r.x0) & (x < r.x1)
                    ys_in_slot.extend((int(y[selected].min()), int(y[selected].max()) + 1))
                if not ys_in_slot:
                    rectangles.append(r)
                else:
                    tight = replace(r, y0=max(r.y0, min(ys_in_slot)), y1=min(r.y1, max(ys_in_slot)))
                    padded = replace(r, y0=max(r.y0, tight.y0 - 2), y1=min(r.y1, tight.y1 + 2))
                    # Optional display/background margin must not pull an
                    # unrelated edge mark into an otherwise complete sample.
                    # Real support is retained; interference inside tight still
                    # fails below. No source pixel is edited.
                    margin_conflict = any(
                        component_intersects(padded, b) and not component_intersects(tight, b)
                        for b in components
                        if b not in chosen
                    )
                    rectangles.append(tight if margin_conflict else padded)
            lanes = tuple(rectangles)
            # Check actual support in the union of non-overlapping raw rectangles.
            # Connected support is allowed to cross a shared slot boundary.
            for b in chosen:
                y, x = np.nonzero(b.footprint)
                x, y = x + b.box.x0, y + b.box.y0
                covered = np.zeros(x.shape, dtype=bool)
                for r in lanes:
                    covered |= (x >= r.x0) & (x < r.x1) & (y >= r.y0) & (y < r.y1)
                if not covered.all():
                    return failure("fixed_grid_clips_target_support")
        else:
            lanes = tuple(
                replace(r, y0=max(r.y0, b.box.y0 - 2), y1=min(r.y1, b.box.y1 + 2))
                for r, b in zip(grid, chosen, strict=True)
            )
        # Quantitative slots follow each complete band in original coordinates.
        # The outer bounding crop may include unused corners around a tilted frame;
        # those corners must not enlarge every lane's measurement rectangle.
        if not all(
            valid[
                r.y0 - membrane.y0 : r.y1 - membrane.y0, r.x0 - membrane.x0 : r.x1 - membrane.x0
            ].all()
            for r in lanes
        ) or not all(valid[int(y) - membrane.y0, int(x) - membrane.x0] for x, y in corners):
            return failure("target_frame_exceeds_membrane")
        if not calibrated and any(
            not (r.x0 <= b.box.x0 < b.box.x1 <= r.x1) for r, b in zip(lanes, chosen, strict=True)
        ):
            return failure("lane_spacing_ambiguous")
        if any(component_intersects(r, b) for b in components if b not in chosen for r in lanes):
            return failure("signal_target_overlap")
        check_detection_cancelled(cancelled)
        resolved = tuple(
            i + 1
            for i, r in enumerate(lanes)
            if sum(r.x0 <= b.box.x0 < b.box.x1 <= r.x1 for b in chosen) == 1
        )
        strength, noise = _signal_field(signal, valid, membrane, settings)
        snrs = tuple(
            float(
                np.max(
                    strength[
                        r.y0 - membrane.y0 : r.y1 - membrane.y0,
                        r.x0 - membrane.x0 : r.x1 - membrane.x0,
                    ]
                    / noise[r.x0 - membrane.x0 : r.x1 - membrane.x0]
                )
            )
            for r in lanes
        )
        evidence_flags = (
            *flags,
            "fixed_width_grid@1" if calibrated else "complete_signal_components@1",
            *(("source_width_refined@1",) if width_refined else ()),
            *(f"grid_signal_unresolved:{i}" for i in range(1, len(lanes) + 1) if i not in resolved),
            "fixed_n_frame@1",
            "source_axis_partition@2" if calibrated else "source_axis_partition@1",
            "signal_orientation_fit@2" if orientation_agrees else "unrotated_complete_geometry@1",
            f"excluded_components:{len(components) - len(chosen)}",
            f"verified_guide_marks:{len(shared_marks)}",
            f"edge_shape_exclusions@1:{len(edge_marks)}",
        )
        candidate = CropCandidate(
            crop,
            round(cy),
            snrs,
            resolved,
            (),
            (),
            evidence_flags,
            lanes,
            frame,
        )
        ridges, _ = _ridge_columns(chosen, lane_width)
        review_positions = tuple(
            i
            for i, r in enumerate(lanes, 1)
            if any(component_intersects(r, b) for b in uncertain)
            or sum(r.x0 <= x < r.x1 for x in ridges) >= max(3, r.width * 0.15)
        )
        return ReliableDetection(
            replace(initial, crop_height=crop.y1 - crop.y0),
            signal.shape[1],
            signal.shape[0],
            membrane,
            None,
            crop,
            (candidate,),
            evidence_flags,
            "instrument_guided_geometry@2",
            _sampling_limits(lanes, [b for b in components if b not in chosen], valid, membrane),
            review_positions,
        )

    evaluated = [evaluate(chosen) for chosen in candidates]
    accepted: list[ReliableDetection] = []
    for result in evaluated:
        if result.candidates and not any(result.candidates == old.candidates for old in accepted):
            accepted.append(result)
    if len(accepted) > 1:
        return failure("guided_target_ambiguous")
    return (
        accepted[0]
        if accepted
        else replace(
            evaluated[0],
            flags=tuple(dict.fromkeys(flag for result in evaluated for flag in result.flags)),
        )
    )
