"""Shared numeric row geometry, extracted unchanged from common-band v1.

These helpers do not choose a detection policy or read/write image files.
"""

from dataclasses import dataclass
from math import ceil, cos, floor, sin, tan

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.scipy_geometry import filters as ndi
from wb_tool.domain.scipy_geometry import peaks as peak_functions
from wb_tool.domain.source_geometry import DetectionPlane

FloatArray = NDArray[np.float64]
PixelArray = NDArray[np.uint8 | np.uint16]


@dataclass(frozen=True)
class BandCore:
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


def closing(values: FloatArray, size: int) -> FloatArray:
    return -ndi.maximum_filter1d(-ndi.maximum_filter1d(values, size, axis=0), size, axis=0)


def sample(pixels: PixelArray, plane: DetectionPlane) -> FloatArray:
    yy, xx = np.mgrid[: plane.values.shape[0], : plane.values.shape[1]]
    c, s = cos(plane.angle), sin(plane.angle)
    rx = plane.origin_x + c * xx - s * yy
    ry = plane.origin_y + s * xx + c * yy
    return ndi.map_coordinates(pixels.astype(np.float64), [ry, rx], order=1, mode="nearest")


def marker_end(plane: DetectionPlane, valid: NDArray[np.bool_], scale: float) -> int:
    """A multi-ridge guide hypothesis, used only to exclude detection seeds."""
    residual = np.maximum(closing(plane.values, max(7, round(scale))) - plane.values, 0)
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
        # A sample doublet is insufficient evidence for a marker column.
        if len(ridges) >= 3:
            # The old .45-scale expansion cut into an adjacent genuine band.
            # Follow the marker's own horizontal extent, with only a small cap.
            right = int(position)
            while (
                right + 1 < len(horizontal) and horizontal[right + 1] > horizontal[position] * 0.25
            ):
                right += 1
            end = max(end, min(right + 2, round(float(position) + scale * 0.25)))
    return end


def fit_row(signal: FloatArray, support: NDArray[np.bool_]) -> tuple[float, float]:
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


def basin_centers(profile: FloatArray, scale: float, n: int) -> FloatArray:
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
        valley_ratio = float(profile[boundaries[index]]) / max(
            1.0, min(float(profile[peaks[index]]), float(profile[peaks[index + 1]]))
        )
        if valley_ratio < 0.5:
            # Separate prominent basins are not fragments to merge merely to
            # reach the requested N. Keep this as an explicit count conflict.
            raise ValueError("common_prominent_slot_count_conflict")
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


def slots(
    members: list[BandCore], profile: FloatArray, scale: float, n: int
) -> tuple[FloatArray, tuple[int, ...]]:
    groups: list[list[BandCore]] = []
    gaps = np.diff([q.x for q in members])
    positive_gaps = gaps[gaps > 1]
    # Membrane width can overestimate pitch for a short row. Repeated observed
    # separations must not be collapsed just because the membrane is broad.
    fragment_distance = min(
        scale * 0.55,
        float(np.median(positive_gaps)) * 0.75 if len(positive_gaps) else scale * 0.55,
    )
    for core in members:
        if len(members) > n and groups and core.x - groups[-1][-1].x < fragment_distance:
            groups[-1].append(core)
        else:
            groups.append([core])
    centers: FloatArray = np.array(
        [sum(q.x * q.score for q in group) / sum(q.score for q in group) for group in groups],
        dtype=np.float64,
    )
    if len(centers) < n:
        centers = basin_centers(profile, scale, n)
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


def sampling_rectangles(
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
