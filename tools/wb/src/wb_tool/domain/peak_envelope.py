"""peak_envelope@1: close detected peaks across complete valley search intervals.

WBQuant detection/frame rejection stays separate. A small local minimum on a
peak shoulder must not truncate the search before the surrounding background.
The original profile is used for both endpoints and subsequent integration.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.quantify import BandBounds, Baseline


@dataclass(frozen=True)
class PeakEnvelope:
    bounds: BandBounds
    baseline: Baseline
    notes: tuple[str, ...]


def close_peak_envelopes(
    profile: NDArray[np.float64], peak_positions: tuple[int, ...]
) -> tuple[PeakEnvelope, ...]:
    """Use complete half-valleys, with shared boundaries between real peaks.

    Outer intervals extend to the chosen lane's edges, never outside its ROI.
    Interior intervals stop at neighbouring peaks; distinct bands cannot overlap.
    Flat outer minima use the point nearest the apex. Shared minima use their
    midpoint. Unsupported ROI edges/raised inter-peak valleys remain review data.
    """
    if (
        profile.ndim != 1
        or len(profile) < 3
        or not np.isfinite(profile).all()
        or np.any(profile < 0)
        or tuple(sorted(set(peak_positions))) != peak_positions
        or any(not 0 < p < len(profile) - 1 for p in peak_positions)
    ):
        raise ValueError("峰与原始剖面不匹配")
    shared: list[int] = []
    for left, right in zip(peak_positions[:-1], peak_positions[1:], strict=True):
        if right - left < 2:
            raise ValueError("相邻峰之间没有可用谷点")
        values = profile[left + 1 : right]
        indices = np.flatnonzero(values == values.min()) + left + 1
        shared.append(int(min(indices, key=lambda i: (abs(i - (left + right) / 2), i))))
    proposals: list[PeakEnvelope] = []
    for index, peak in enumerate(peak_positions):
        if index:
            left = shared[index - 1]
        else:
            values = profile[:peak]
            left = int(np.flatnonzero(values == values.min())[-1])
        if index < len(shared):
            right = shared[index]
        else:
            values = profile[peak + 1 :]
            right = int(peak + 1 + np.flatnonzero(values == values.min())[0])
        notes = ["peak_envelope@1", "complete_valley_search@1"]
        if left == 0 or right == len(profile) - 1:
            notes.append("boundary_review:background_at_roi_edge")
        amplitude = float(profile[peak] - min(profile[left], profile[right]))
        # Endpoints in a raised shoulder/overlapping valley are not automatically
        # certified as background merely because a local minimum exists there.
        if (
            amplitude <= 0
            or min(float(profile[peak] - profile[left]), float(profile[peak] - profile[right]))
            < 0.8 * amplitude
        ):
            notes.append("boundary_review:unequal_or_overlapping_peak_support")
        proposals.append(
            PeakEnvelope(
                BandBounds(left, right),
                Baseline(float(profile[left]), float(profile[right])),
                tuple(notes),
            )
        )
    return tuple(proposals)
