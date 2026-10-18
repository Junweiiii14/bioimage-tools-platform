"""Typed boundary around the frozen WBQuant 1.4.3 numerical reference."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.lanes import LaneROI, Polarity
from wb_tool.domain.quantify import BandBounds, Baseline
from wb_tool.domain.wbquant143.core import detect_border_insets, quantify_image
from wb_tool.domain.wbquant143.models import LaneROI as ReferenceROI
from wb_tool.domain.wbquant143.models import LoadedImage


@dataclass(frozen=True)
class QuantBandProposal:
    bounds: BandBounds | None
    baseline: Baseline | None
    notes: tuple[str, ...]


@dataclass(frozen=True)
class QuantLaneProposal:
    roi: LaneROI
    bands: tuple[QuantBandProposal, ...]


def exclude_smear_frame(
    pixels: NDArray[np.uint8 | np.uint16], roi: LaneROI, polarity: Polarity
) -> LaneROI:
    """Reuse WBQuant's conservative frame test, without narrowing to a peak."""
    raw = pixels[roi.y0 : roi.y1, roi.x0 : roi.x1]
    maximum = int(np.iinfo(raw.dtype).max)
    raw = raw if polarity == "dark" else maximum - raw
    image = LoadedImage(
        "original-crop",
        raw,
        raw.astype(np.float64),
        maximum,
        raw.dtype.itemsize * 8,
        0,
        0,
        0.0,
        0.0,
    )
    local = ReferenceROI(1, 0, 0, roi.width, roi.y1 - roi.y0)
    insets, _ = detect_border_insets(image, local)
    effective = insets.apply(local)
    return LaneROI(
        roi.lane_id,
        roi.x0 + effective.x0,
        roi.y0 + effective.y0,
        roi.x0 + effective.x1,
        roi.y0 + effective.y1,
    )


def propose_smear_lane(
    pixels: NDArray[np.uint8 | np.uint16], roi: LaneROI, polarity: Polarity
) -> QuantLaneProposal:
    """Keep the complete chosen lane, excluding only a confirmed thin frame."""
    effective = exclude_smear_frame(pixels, roi, polarity)
    return QuantLaneProposal(
        effective,
        (
            QuantBandProposal(
                BandBounds(0, effective.y1 - effective.y0 - 1),
                None,
                (
                    "whole_lane_smear@1",
                    "endpoint_baseline@1",
                    "manual_range_adjustable",
                    f"original_roi:{roi.x0},{roi.y0},{roi.x1},{roi.y1}; "
                    f"effective_roi:{effective.x0},{effective.y0},{effective.x1},{effective.y1}",
                ),
            ),
        ),
    )


def propose_quant_lanes(
    pixels: NDArray[np.uint8 | np.uint16], rois: tuple[LaneROI, ...], polarity: Polarity = "dark"
) -> tuple[QuantLaneProposal, ...]:
    """Return all included targets; retain multi-peak/weak/frame warnings.

    Reference auto-border changes are reflected in the returned original-pixel ROI.
    No display scaling or resampling is performed. Other candidates are not silently
    assigned biological identities; they retain vertical ordinal positions.
    """
    if pixels.ndim != 2 or pixels.dtype not in (np.dtype("uint8"), np.dtype("uint16")):
        raise ValueError("定量需要原始二维 uint8/uint16 像素")
    maximum = int(np.iinfo(pixels.dtype).max)
    raw = pixels if polarity == "dark" else maximum - pixels
    image = LoadedImage(
        "original",
        raw,
        raw.astype(np.float64),
        maximum,
        raw.dtype.itemsize * 8,
        0,
        0,
        0.0,
        0.0,
    )
    results = quantify_image(
        image, [ReferenceROI(i, r.x0, r.y0, r.x1, r.y1) for i, r in enumerate(rois, 1)]
    ).lanes
    proposals: list[QuantLaneProposal] = []
    for roi, result in zip(rois, results, strict=True):
        effective = result.effective_roi or result.roi
        effective_roi = LaneROI(roi.lane_id, effective.x0, effective.y0, effective.x1, effective.y1)
        candidates = [b for b in result.bands if b.included]
        notes = list(result.warnings)
        if effective_roi != roi:
            notes.append(
                f"original_roi:{roi.x0},{roi.y0},{roi.x1},{roi.y1}; "
                f"effective_roi:{effective.x0},{effective.y0},{effective.x1},{effective.y1}"
            )
        if result.weak_candidates:
            notes.append(f"weak_peak_candidates:{len(result.weak_candidates)}")
        excluded = sum(not b.included for b in result.bands)
        if excluded:
            notes.append(f"excluded_frame_peaks:{excluded}")
        if len(candidates) > 1:
            notes.append(f"multiple_peaks:{len(candidates)}")
        if not candidates:
            proposals.append(
                QuantLaneProposal(effective_roi, (QuantBandProposal(None, None, tuple(notes)),))
            )
            continue
        bands: list[QuantBandProposal] = []
        for candidate in sorted(candidates, key=lambda b: b.peak_y_relative):
            left = candidate.baseline_left_value
            right = candidate.baseline_right_value
            if candidate.signal is None or left is None or right is None:
                bands.append(
                    QuantBandProposal(
                        None,
                        None,
                        tuple(
                            [
                                *notes,
                                *candidate.warnings,
                                f"invalid_peak_at:{candidate.peak_y_absolute}; signal_unavailable",
                            ]
                        ),
                    )
                )
                continue
            bands.append(
                QuantBandProposal(
                    BandBounds(candidate.left, candidate.right),
                    Baseline(left, right),
                    tuple([*notes, *candidate.warnings]),
                )
            )
        proposals.append(QuantLaneProposal(effective_roi, tuple(bands)))
    return tuple(proposals)


def propose_quant_lane(
    pixels: NDArray[np.uint8 | np.uint16], roi: LaneROI, polarity: Polarity = "dark"
) -> QuantLaneProposal:
    return propose_quant_lanes(pixels, (roi,), polarity)[0]
