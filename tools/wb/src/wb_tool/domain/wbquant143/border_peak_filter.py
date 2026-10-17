"""Conservative post-detection filter for crop-frame peaks.

Peak finding remains unchanged.  This module classifies existing candidates as
keep/review/exclude. Besides edge proximity it recognizes the position-independent
rectangular-line morphology made by borders between vertically stacked panels:
a thin, uniform row-spanning run with abrupt transitions on both sides. Every
decision is serializable so an automatic exclusion remains visible and reversible
during review.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from typing import Literal

import numpy as np


Action = Literal["keep", "review", "exclude"]


@dataclass(frozen=True, slots=True)
class BorderPeakFilterConfig:
    edge_zone_fraction: float = 0.12
    edge_zone_min_px: int = 6
    extreme_prominence_ratio: float = 0.72
    extreme_level_ratio: float = 0.78
    line_coverage_threshold: float = 0.70
    line_uniformity_threshold: float = 0.78
    sharp_step_ratio: float = 0.28
    rectangular_step_ratio: float = 0.55
    two_sided_drop_ratio: float = 0.22
    thin_line_max_px: int = 8
    high_confidence: float = 0.74
    review_confidence: float = 0.54


@dataclass(frozen=True, slots=True)
class BorderPeakDecision:
    peak_index: int
    action: Action
    confidence: float
    matched_edge: Literal["top", "bottom"] | None
    prominence_ratio: float
    peak_level_ratio: float
    line_coverage: float
    line_uniformity: float
    local_step_ratio: float
    vertical_thickness: int
    two_sided_drop_ratio: float
    edge_proximity: float
    edge_contact_ratio: float
    row_run_continuity: float
    thickness_cv: float
    boundary_straightness: float
    plateau_flatness: float
    border_likelihood: float
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _robust_sigma(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size < 2:
        return 0.0
    center = float(np.median(finite))
    return float(1.4826 * np.median(np.abs(finite - center)))


def _clip_score(value: float, low: float, high: float) -> float:
    if high <= low:
        return float(value >= high)
    return float(np.clip((value - low) / (high - low), 0.0, 1.0))


def _validate_inputs(
    raw_roi: np.ndarray,
    profile: np.ndarray,
    peaks: np.ndarray,
    prominences: np.ndarray,
    dtype_max: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    raw = np.asarray(raw_roi)
    signal = np.asarray(profile, dtype=np.float64)
    peak_indices = np.asarray(peaks, dtype=int)
    peak_prominences = np.asarray(prominences, dtype=np.float64)
    if raw.ndim != 2 or signal.ndim != 1 or raw.shape[0] != signal.size:
        raise ValueError("raw_roi must be 2-D and profile must match its row count")
    if peak_indices.ndim != 1 or peak_prominences.shape != peak_indices.shape:
        raise ValueError("peaks and prominences must be equally sized 1-D arrays")
    if dtype_max <= 0 or np.any(~np.isfinite(signal)) or np.any(~np.isfinite(peak_prominences)):
        raise ValueError("dtype_max and all profile/prominence values must be finite and valid")
    if np.any((peak_indices < 0) | (peak_indices >= signal.size)):
        raise ValueError("all peak indices must be inside the profile")
    return raw.astype(np.float64, copy=False), signal, peak_indices, peak_prominences


def classify_black_border_peaks(
    raw_roi: np.ndarray,
    profile: np.ndarray,
    peaks: np.ndarray,
    prominences: np.ndarray,
    *,
    dtype_max: int,
    config: BorderPeakFilterConfig | None = None,
) -> list[BorderPeakDecision]:
    """Classify already-detected peaks without changing peak detection.

    Automatic exclusion requires the full thin rectangular-line morphology.
    A large prominence, saturation, or edge position alone is never enough to
    remove a candidate.
    """

    cfg = config or BorderPeakFilterConfig()
    raw, signal, peak_indices, peak_prominences = _validate_inputs(
        raw_roi, profile, peaks, prominences, dtype_max
    )
    height = signal.size
    edge_limit = min(
        max(1, height // 2),
        max(cfg.edge_zone_min_px, int(ceil(height * cfg.edge_zone_fraction))),
    )
    robust_range = float(np.percentile(signal, 99) - np.percentile(signal, 1))
    if robust_range <= 0:
        robust_range = max(float(np.ptp(signal)), 1.0)

    decisions: list[BorderPeakDecision] = []

    for peak, prominence in zip(peak_indices, peak_prominences, strict=True):
        peak = int(peak)
        top_distance = peak
        bottom_distance = height - 1 - peak
        distance = min(top_distance, bottom_distance)
        matched_edge = "top" if top_distance <= bottom_distance else "bottom"
        edge_proximity = max(0.0, 1.0 - distance / max(1, edge_limit))

        prominence_ratio = float(max(0.0, prominence) / robust_range)
        peak_level_ratio = float(np.clip(signal[peak] / dtype_max, 0.0, 1.0))
        # Compare the apex rows with the darker of the two local side
        # backgrounds, column by column. This remains valid when one side of a
        # frame opens onto a white inter-panel gap. The previous global
        # ``background + 4*MAD`` gate could exceed the frame peak itself on a
        # bimodal panel and report zero coverage for a perfectly uniform line.
        local_radius = max(6, min(16, height // 12 if height >= 72 else 6))
        shoulder_gap = 2
        left_start = max(0, peak - local_radius)
        left_stop = max(left_start, peak - shoulder_gap)
        right_start = min(height, peak + shoulder_gap + 1)
        right_stop = min(height, peak + local_radius + 1)
        left_values = signal[left_start:left_stop]
        right_values = signal[right_start:right_stop]
        left_background = (
            float(np.min(left_values)) if left_values.size else float(signal[max(0, peak - 1)])
        )
        right_background = (
            float(np.min(right_values)) if right_values.size else float(signal[min(height - 1, peak + 1)])
        )
        local_background = max(left_background, right_background)
        peak_excess = max(float(signal[peak]) - local_background, 1.0)

        darkness = dtype_max - raw
        row_start = max(0, peak - 1)
        row_stop = min(height, peak + 2)
        darkness_rows = darkness[row_start:row_stop]

        def side_floor(start: int, stop: int) -> np.ndarray:
            rows = darkness[start:stop]
            if rows.size:
                return np.min(rows, axis=0)
            return np.zeros(raw.shape[1], dtype=np.float64)

        local_reference = np.maximum(
            side_floor(left_start, left_stop),
            side_floor(right_start, right_stop),
        )
        line_contrast_gate = max(0.12 * robust_range, 0.035 * dtype_max, 1.0)
        row_coverages = np.mean(
            darkness_rows - local_reference >= line_contrast_gate,
            axis=1,
        )
        best_row = darkness_rows[int(np.argmax(row_coverages))]
        line_coverage = float(np.max(row_coverages))
        row_mask = best_row - local_reference >= line_contrast_gate
        true_columns = np.flatnonzero(row_mask)
        if true_columns.size:
            gaps = np.flatnonzero(np.diff(true_columns) > 1)
            run_starts = np.r_[true_columns[0], true_columns[gaps + 1]]
            run_ends = np.r_[true_columns[gaps], true_columns[-1]]
            row_run_continuity = float(np.max(run_ends - run_starts + 1) / raw.shape[1])
        else:
            row_run_continuity = 0.0
        edge_span = max(1, int(ceil(raw.shape[1] * 0.08)))
        edge_contact_ratio = float(
            (np.mean(row_mask[:edge_span]) + np.mean(row_mask[-edge_span:])) / 2.0
        )
        row_median = float(np.median(best_row))
        row_mad = float(np.median(np.abs(best_row - row_median)))
        line_uniformity = float(1.0 / (1.0 + row_mad / max(0.12 * peak_excess, 1.0)))

        local_start = max(0, peak - local_radius)
        local_stop = min(height, peak + local_radius + 1)
        local_step_ratio = (
            float(np.max(np.abs(np.diff(signal[local_start:local_stop]))) / robust_range)
            if local_stop - local_start >= 2
            else 0.0
        )
        two_sided_drop_ratio = float(
            max(
                0.0,
                min(signal[peak] - left_background, signal[peak] - right_background)
                / robust_range,
            )
        )
        thickness_gate_level = local_background + 0.65 * peak_excess
        thickness_left = peak
        while thickness_left > 0 and signal[thickness_left - 1] >= thickness_gate_level:
            thickness_left -= 1
        thickness_right = peak
        while thickness_right < height - 1 and signal[thickness_right + 1] >= thickness_gate_level:
            thickness_right += 1
        vertical_thickness = thickness_right - thickness_left + 1
        # Estimate thickness independently in each supported column. A frame
        # line has nearly parallel upper/lower edges; a biological band is
        # usually curved, feathered, or laterally incomplete.
        column_thicknesses: list[int] = []
        upper_edges: list[int] = []
        lower_edges: list[int] = []
        column_gate = 0.55 * line_contrast_gate
        for column in true_columns:
            column_signal = darkness[local_start:local_stop, column] - local_reference[column]
            local_peak = peak - local_start
            if local_peak < 0 or local_peak >= column_signal.size or column_signal[local_peak] < column_gate:
                continue
            upper = local_peak
            while upper > 0 and column_signal[upper - 1] >= column_gate:
                upper -= 1
            lower = local_peak
            while lower < column_signal.size - 1 and column_signal[lower + 1] >= column_gate:
                lower += 1
            column_thicknesses.append(lower - upper + 1)
            upper_edges.append(local_start + upper)
            lower_edges.append(local_start + lower)
        if column_thicknesses:
            mean_thickness = float(np.mean(column_thicknesses))
            thickness_cv = float(np.std(column_thicknesses) / max(mean_thickness, 1.0))
            edge_spread = float(np.std(upper_edges) + np.std(lower_edges)) / 2.0
            boundary_straightness = float(1.0 / (1.0 + edge_spread))
        else:
            thickness_cv = 1.0
            boundary_straightness = 0.0
        plateau_values = signal[thickness_left : thickness_right + 1]
        plateau_flatness = float(
            1.0 / (1.0 + np.std(plateau_values) / max(0.12 * peak_excess, 1.0))
        )

        prominence_score = _clip_score(
            prominence_ratio, cfg.extreme_prominence_ratio, 1.02
        )
        level_score = _clip_score(peak_level_ratio, cfg.extreme_level_ratio, 0.98)
        contrast_score = max(prominence_score, level_score)
        geometry_score = 0.60 * _clip_score(
            line_coverage, cfg.line_coverage_threshold, 0.98
        ) + 0.40 * _clip_score(
            line_uniformity, cfg.line_uniformity_threshold, 0.99
        )
        step_score = _clip_score(local_step_ratio, cfg.rectangular_step_ratio, 0.95)
        thinness_score = float(
            np.clip(
                (cfg.thin_line_max_px + 1 - vertical_thickness)
                / max(1, cfg.thin_line_max_px - 2),
                0.0,
                1.0,
            )
        )
        drop_score = _clip_score(
            two_sided_drop_ratio, cfg.two_sided_drop_ratio, 0.45
        )
        morphology_score = float(
            0.23 * line_coverage
            + 0.17 * row_run_continuity
            + 0.10 * edge_contact_ratio
            + 0.14 * line_uniformity
            + 0.14 * boundary_straightness
            + 0.08 * plateau_flatness
            + 0.07 * (1.0 - min(thickness_cv, 1.0))
            + 0.07 * thinness_score
        )
        border_likelihood = float(
            np.clip(
                0.54 * morphology_score
                + 0.16 * step_score
                + 0.14 * drop_score
                + 0.09 * contrast_score
                + 0.07 * edge_proximity,
                0.0,
                1.0,
            )
        )
        confidence = border_likelihood

        edge_gate = distance <= edge_limit and edge_proximity >= 0.35
        contrast_gate = prominence_ratio >= cfg.extreme_prominence_ratio or (
            peak_level_ratio >= cfg.extreme_level_ratio
            and local_step_ratio >= cfg.sharp_step_ratio
        )
        line_gate = (
            line_coverage >= cfg.line_coverage_threshold
            and (row_run_continuity >= 0.62 or line_coverage >= 0.86)
            and line_uniformity >= cfg.line_uniformity_threshold
        )
        step_gate = local_step_ratio >= cfg.rectangular_step_ratio
        thin_gate = vertical_thickness <= cfg.thin_line_max_px
        drop_gate = two_sided_drop_ratio >= cfg.two_sided_drop_ratio

        reasons: list[str] = []
        if edge_gate:
            reasons.append(f"peak is within the {matched_edge} edge zone")
        if contrast_gate:
            reasons.append("global prominence or absolute/local contrast is extreme")
        if line_gate:
            reasons.append("apex row is a straight high-coverage dark line")
        if step_gate:
            reasons.append("local profile contains a sharp intensity step")
        if thin_gate:
            reasons.append("high-intensity vertical run is thin")
        if drop_gate:
            reasons.append("profile drops sharply on both sides of the run")

        straight_gate = boundary_straightness >= 0.68 and thickness_cv <= 0.45
        morphology_gate = line_gate and straight_gate and (edge_contact_ratio >= 0.45 or line_coverage >= 0.90)
        if morphology_gate and thin_gate and (step_gate or drop_gate) and border_likelihood >= cfg.high_confidence:
            action: Action = "exclude"
        elif (
            confidence >= cfg.review_confidence
            and sum((edge_gate, contrast_gate, line_gate, step_gate, thin_gate, drop_gate)) >= 4
        ):
            action = "review"
        else:
            action = "keep"
        decisions.append(
            BorderPeakDecision(
                peak_index=peak,
                action=action,
                confidence=confidence,
                matched_edge=matched_edge if edge_gate else None,
                prominence_ratio=prominence_ratio,
                peak_level_ratio=peak_level_ratio,
                line_coverage=line_coverage,
                line_uniformity=line_uniformity,
                local_step_ratio=local_step_ratio,
                vertical_thickness=vertical_thickness,
                two_sided_drop_ratio=two_sided_drop_ratio,
                edge_proximity=edge_proximity,
                edge_contact_ratio=edge_contact_ratio,
                row_run_continuity=row_run_continuity,
                thickness_cv=thickness_cv,
                boundary_straightness=boundary_straightness,
                plateau_flatness=plateau_flatness,
                border_likelihood=border_likelihood,
                reasons=tuple(reasons),
            )
        )
    return decisions
