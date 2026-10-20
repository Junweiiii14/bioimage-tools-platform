"""Bounded original-pixel background context, anchored_context@1.

This is a proposal mechanism, not a change to integration or clipping policy.
The target never moves; unsuccessful trials retain the original diagnostic area.
"""

from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.background_bounds import propose_background_lanes
from wb_tool.domain.lanes import LaneROI, Polarity, compute_lane_profiles
from wb_tool.domain.quant_supervision import QuantLaneProposal
from wb_tool.domain.scipy_geometry import filters


@dataclass(frozen=True, slots=True)
class AnchoredLaneProposal:
    target: LaneROI
    proposal: QuantLaneProposal
    expansion_percent: int = 0


def context_padding(height: int, percent: int) -> int:
    """Integer nearest rounding (ties upward), minimum one original pixel."""
    if type(height) is not int or height < 1 or percent not in (5, 10, 15, 20, 25):
        raise ValueError("上下文仅支持正整数高度和5–25%的有界扩展")
    return max(1, (height * percent + 50) // 100)


def _dominant_peak_in_target(
    pixels: NDArray[np.uint8 | np.uint16],
    context: LaneROI,
    target: LaneROI,
    polarity: Polarity,
) -> bool:
    # Match background_support@1's detection-only trend. A stronger outside peak
    # invalidates the trial instead of becoming the selected biological target.
    profile = np.asarray(compute_lane_profiles(pixels, context, polarity).quantitative)
    size = len(profile)
    support_size = max(3, min(10, size // 10))
    mid = (support_size - 1) / 2
    left = float(np.median(profile[:support_size]))
    right = float(np.median(profile[-support_size:]))
    background = left + (right - left) / (size - 1 - 2 * mid) * (np.arange(size) - mid)
    peak = int((filters.gaussian_filter1d(profile, sigma=1.0) - background).argmax())
    return target.y0 <= context.y0 + peak < target.y1


def propose_anchored_lanes(
    pixels: NDArray[np.uint8 | np.uint16],
    targets: tuple[LaneROI, ...],
    polarity: Polarity = "dark",
) -> tuple[AnchoredLaneProposal, ...]:
    """Try the first fully supported context, never rank trials by larger area.

    Only an original single-target insufficient-background proposal is eligible.
    No x expansion, display transform, source mutation or weak-target borrowing.
    Bounds remain local to proposal.roi, which may differ from target in y only.
    """
    originals = propose_background_lanes(pixels, targets, polarity)
    results: list[AnchoredLaneProposal] = []
    for target, original in zip(targets, originals, strict=True):
        chosen = AnchoredLaneProposal(target, original)
        band = original.bands[0]
        if band.bounds is None or band.notes != (
            "boundary_review:insufficient_background_support",
        ):
            results.append(chosen)
            continue
        previous = target
        for percent in (5, 10, 15, 20, 25):
            pad = context_padding(target.y1 - target.y0, percent)
            context = replace(
                target, y0=max(0, target.y0 - pad), y1=min(pixels.shape[0], target.y1 + pad)
            )
            if context == previous:
                continue
            previous = context
            candidate = propose_background_lanes(pixels, (context,), polarity)[0]
            candidate_band = candidate.bands[0]
            if (
                candidate_band.bounds is not None
                and not candidate_band.notes
                and _dominant_peak_in_target(pixels, context, target, polarity)
            ):
                chosen = AnchoredLaneProposal(target, candidate, percent)
                break
        results.append(chosen)
    return tuple(results)
