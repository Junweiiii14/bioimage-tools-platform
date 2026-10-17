"""background_support@1: sustained background, never nearest peak-internal minima.

Only detection is smoothed. Integration still consumes the untouched original
mean profile and profile_integral@1. Missing support is retained as review data.
"""

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.lanes import LaneROI, Polarity, compute_lane_profiles
from wb_tool.domain.quant_supervision import QuantBandProposal, QuantLaneProposal
from wb_tool.domain.quantify import BandBounds, Baseline
from wb_tool.domain.scipy_geometry import filters, peaks


def propose_background_lanes(
    pixels: NDArray[np.uint8 | np.uint16], rois: tuple[LaneROI, ...], polarity: Polarity = "dark"
) -> tuple[QuantLaneProposal, ...]:
    proposals: list[QuantLaneProposal] = []
    for roi in rois:
        profile = np.asarray(compute_lane_profiles(pixels, roi, polarity).quantitative)
        size = len(profile)
        if size < 9:
            proposals.append(
                QuantLaneProposal(roi, (QuantBandProposal(None, None, ("profile_too_short",)),))
            )
            continue
        support_size = max(3, min(10, size // 10))
        edge_left = float(np.median(profile[:support_size]))
        edge_right = float(np.median(profile[-support_size:]))
        mid = (support_size - 1) / 2
        slope = (edge_right - edge_left) / (size - 1 - 2 * mid)
        background = edge_left + slope * (np.arange(size) - mid)
        smooth = filters.gaussian_filter1d(profile, sigma=1.0)
        residual = smooth - background
        noise = max(0.1, float(np.median(np.abs(np.diff(profile, n=2)))) / 1.65)
        peak = int(residual.argmax())
        amplitude = float(residual[peak])
        if amplitude < 4 * noise or peak in (0, size - 1):
            proposals.append(
                QuantLaneProposal(roi, (QuantBandProposal(None, None, ("weak_or_edge_peak",)),))
            )
            continue
        floor = max(3 * noise, amplitude * 0.025)
        support = residual <= floor
        left = next(
            (
                y
                for y in range(peak - 1, support_size - 2, -1)
                if bool(support[y - support_size + 1 : y + 1].all())
            ),
            None,
        )
        right = next(
            (
                y
                for y in range(peak + 1, size - support_size + 1)
                if bool(support[y : y + support_size].all())
            ),
            None,
        )
        notes: list[str] = []
        if left is None or right is None:
            notes.append("boundary_review:insufficient_background_support")
        start, end = left if left is not None else 0, right if right is not None else size - 1
        # A second strong region is not silently assigned to the same target.
        outside = np.concatenate((residual[:start], residual[end + 1 :]))
        if outside.size and float(outside.max()) > max(4 * noise, amplitude * 0.2):
            notes.append("boundary_review:multiple_signal_regions")
        maxima, _ = peaks.find_peaks(
            residual, prominence=max(4 * noise, amplitude * 0.2), distance=3
        )
        for a, b in zip(maxima[:-1], maxima[1:], strict=True):
            valley = float(residual[int(a) : int(b) + 1].min())
            smaller = min(float(residual[int(a)]), float(residual[int(b)]))
            if valley < smaller * 0.25:
                notes.append("boundary_review:multiple_signal_regions")
                break
        baseline = Baseline(max(0.0, float(background[start])), max(0.0, float(background[end])))
        proposals.append(
            QuantLaneProposal(
                roi,
                (QuantBandProposal(BandBounds(start, end), baseline, tuple(dict.fromkeys(notes))),),
            )
        )
    return tuple(proposals)
