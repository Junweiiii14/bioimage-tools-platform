from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import ceil

import numpy as np
from scipy.integrate import trapezoid
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

from .border_peak_filter import classify_black_border_peaks
from .config import AlgorithmConfig
from .errors import QuantificationError
from .lane_validation import validate_lanes
from .models import BandResult, ImageResult, LaneROI, LaneResult, LoadedImage, ROIInsets
from .peak_candidates import detect_weak_peak_candidates


def _robust_sigma(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size < 2:
        return 0.0
    median = float(np.median(finite))
    return float(1.4826 * np.median(np.abs(finite - median)))


def _merge_short_gaps(mask: np.ndarray, maximum_gap: int = 2) -> np.ndarray:
    merged = np.asarray(mask, dtype=bool).copy()
    true_indices = np.flatnonzero(merged)
    for first, second in zip(true_indices[:-1], true_indices[1:], strict=False):
        if 0 < second - first - 1 <= maximum_gap:
            merged[first : second + 1] = True
    return merged


def _true_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    indices = np.flatnonzero(mask)
    if not indices.size:
        return []
    breaks = np.flatnonzero(np.diff(indices) > 1)
    starts = np.r_[indices[0], indices[breaks + 1]]
    ends = np.r_[indices[breaks], indices[-1]]
    return [(int(start), int(end)) for start, end in zip(starts, ends, strict=True)]


def _axis_border_candidates(
    darkness: np.ndarray,
    *,
    axis: int,
    dtype_max: int,
) -> tuple[list[dict[str, object]], float]:
    """Return straight, high-coverage dark-line candidates near both axis edges."""
    length = darkness.shape[axis]
    orthogonal = darkness.shape[1 - axis]
    belt = min(length, max(6, min(64, int(ceil(length * 0.08)))))
    central_start = min(length - 1, belt)
    central_stop = max(central_start + 1, length - belt)
    central = np.take(darkness, np.arange(central_start, central_stop), axis=axis)
    central_values = central.ravel()
    background_pool = central_values[
        central_values <= np.percentile(central_values, 60)
    ]
    center = float(np.median(background_pool))
    sigma = _robust_sigma(background_pool)
    robust_range = float(np.percentile(darkness, 99.5) - np.percentile(darkness, 5))
    pixel_threshold = center + max(4.0 * sigma, 0.18 * robust_range, dtype_max * 0.025, 1.0)
    pixel_threshold = min(pixel_threshold, center + 0.72 * (dtype_max - center))
    coverage = np.mean(darkness >= pixel_threshold, axis=1 - axis)
    scores = np.median(darkness, axis=1 - axis)
    spreads = np.median(np.abs(darkness - np.expand_dims(scores, axis=1 - axis)), axis=1 - axis)
    line_mask = _merge_short_gaps((coverage >= 0.72) & (scores >= pixel_threshold), 2)
    candidates: list[dict[str, object]] = []
    for side, indices in (
        ("start", np.arange(0, belt)),
        ("end", np.arange(length - belt, length)),
    ):
        local_mask = line_mask[indices]
        runs = _true_runs(local_mask)
        for local_start, local_end in runs:
            start = int(indices[local_start])
            end = int(indices[local_end])
            thickness = end - start + 1
            if thickness > max(20, belt // 2 + 1):
                continue
            outer_slice = slice(0, start) if side == "start" else slice(end + 1, length)
            outer_scores = scores[outer_slice]
            if outer_scores.size:
                padding_score = float(np.mean(outer_scores < pixel_threshold))
                padding_uniformity = 1.0 / (1.0 + _robust_sigma(outer_scores) / max(dtype_max * 0.002, 1.0))
                padding_score = 0.65 * padding_score + 0.35 * padding_uniformity
            else:
                padding_score = 0.82
            mean_coverage = float(np.mean(coverage[start : end + 1]))
            contrast = float(np.median(scores[start : end + 1]) - center)
            contrast_score = min(1.0, contrast / max(dtype_max * 0.12, robust_range * 0.55, 1.0))
            uniformity = 1.0 / (
                1.0 + float(np.median(spreads[start : end + 1])) / max(contrast * 0.12, 1.0)
            )
            distance = start if side == "start" else length - 1 - end
            proximity = max(0.0, 1.0 - distance / max(1.0, belt))
            thinness = max(0.0, 1.0 - (thickness - 1) / max(3.0, belt * 0.65))
            confidence = (
                0.32 * mean_coverage
                + 0.24 * contrast_score
                + 0.16 * uniformity
                + 0.12 * padding_score
                + 0.10 * proximity
                + 0.06 * thinness
            )
            candidates.append(
                {
                    "side": side,
                    "start": start,
                    "end": end,
                    "thickness": thickness,
                    "distance_from_edge": distance,
                    "coverage": mean_coverage,
                    "contrast": contrast,
                    "uniformity": uniformity,
                    "padding_score": padding_score,
                    "confidence": min(1.0, max(0.0, confidence)),
                    "orthogonal_pixels": orthogonal,
                }
            )
    return candidates, pixel_threshold


def detect_border_insets(image: LoadedImage, roi: LaneROI) -> tuple[ROIInsets, dict[str, object]]:
    """Detect near-edge frame lines, including lines separated by light padding.

    Detection is deliberately conservative: automatic trimming requires a thin,
    straight, high-coverage line with high contrast. Medium-confidence evidence is
    retained for review but does not change the quantitative ROI.
    """
    roi.validate(image.shape[1], image.shape[0])
    crop = image.dtype_max - image.raw_float[roi.y0 : roi.y1, roi.x0 : roi.x1]
    row_candidates, row_threshold = _axis_border_candidates(
        crop, axis=0, dtype_max=image.dtype_max
    )
    col_candidates, col_threshold = _axis_border_candidates(
        crop, axis=1, dtype_max=image.dtype_max
    )

    def best(candidates: list[dict[str, object]], side: str) -> dict[str, object] | None:
        matches = [item for item in candidates if item["side"] == side]
        if not matches:
            return None
        return max(matches, key=lambda item: (float(item["confidence"]), -int(item["distance_from_edge"])))

    selected = {
        "top": best(row_candidates, "start"),
        "bottom": best(row_candidates, "end"),
        "left": best(col_candidates, "start"),
        "right": best(col_candidates, "end"),
    }
    horizontal_present = selected["top"] is not None or selected["bottom"] is not None
    vertical_present = selected["left"] is not None or selected["right"] is not None
    evidence: dict[str, object] = {}
    insets: dict[str, int] = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    for side, item in selected.items():
        if item is None:
            evidence[side] = {"detected": False, "confidence": 0.0, "action": "none"}
            continue
        confidence = float(item["confidence"])
        if (side in {"top", "bottom"} and vertical_present) or (
            side in {"left", "right"} and horizontal_present
        ):
            confidence = min(1.0, confidence + 0.06)
        action = "exclude" if confidence >= 0.78 else "review" if confidence >= 0.62 else "none"
        if action == "exclude":
            safety = 1
            if side in {"top", "left"}:
                insets[side] = int(item["end"]) + 1 + safety
            else:
                axis_length = roi.height if side == "bottom" else roi.width
                insets[side] = axis_length - int(item["start"]) + safety
        evidence[side] = {
            **item,
            "detected": action != "none",
            "confidence": confidence,
            "action": action,
        }

    detected = ROIInsets(**insets, source="auto-border-v2")
    try:
        detected.validate(roi)
    except Exception:
        detected = ROIInsets()
        for item in evidence.values():
            if isinstance(item, dict) and item.get("action") == "exclude":
                item["action"] = "review"
                item["reason"] = "automatic insets would leave no usable analysis area"
    info: dict[str, object] = {
        "mode": "near-edge-frame-evidence-v2",
        "search_belt": {
            "rows": min(roi.height, max(6, min(64, int(ceil(roi.height * 0.08))))),
            "columns": min(roi.width, max(6, min(64, int(ceil(roi.width * 0.08))))),
        },
        "row_pixel_threshold": row_threshold,
        "column_pixel_threshold": col_threshold,
        "sides": evidence,
        "insets": detected.as_dict(),
    }
    return detected, info


def compute_profiles(image: LoadedImage, roi: LaneROI) -> tuple[np.ndarray, np.ndarray]:
    height, width = image.shape
    roi.validate(width, height)
    raw_profile = image.raw_float[roi.y0 : roi.y1, roi.x0 : roi.x1].mean(
        axis=1, dtype=np.float64
    )
    profile = image.dtype_max - raw_profile
    raw_profile = np.asarray(raw_profile, dtype=np.float64)
    profile = np.asarray(profile, dtype=np.float64)
    raw_profile.setflags(write=False)
    profile.setflags(write=False)
    return raw_profile, profile


def _robust_dynamic_range(profile: np.ndarray) -> float:
    robust = float(np.percentile(profile, 99) - np.percentile(profile, 1))
    if robust > 0:
        return robust
    return float(profile.max() - profile.min()) if profile.size else 0.0


def _valley_between(profile: np.ndarray, left_peak: int, right_peak: int) -> int:
    values = profile[left_peak : right_peak + 1]
    minimum = float(values.min())
    candidates = np.flatnonzero(values == minimum) + left_peak
    midpoint = (left_peak + right_peak) / 2.0
    return int(min(candidates, key=lambda index: (abs(index - midpoint), index)))


def _strict_local_minimum(profile: np.ndarray, index: int) -> bool:
    return 0 < index < profile.size - 1 and profile[index] < profile[index - 1] and profile[index] < profile[index + 1]


def _outer_boundary(profile: np.ndarray, peak: int, width: float, side: str) -> tuple[int, bool, str]:
    radius = max(6, int(ceil(2.0 * width)))
    if side == "left":
        window_start, window_end = max(0, peak - radius), peak - 1
        strict = [i for i in range(window_end, window_start - 1, -1) if _strict_local_minimum(profile, i)]
        if strict:
            selected = strict[0]
            method = "nearest-local-minimum"
        else:
            window = profile[window_start : window_end + 1]
            minimum = float(window.min())
            selected = int(np.flatnonzero(window == minimum)[-1] + window_start)
            method = "window-global-minimum"
        review = selected == window_start or selected == 0
    elif side == "right":
        window_start, window_end = peak + 1, min(profile.size - 1, peak + radius)
        strict = [i for i in range(window_start, window_end + 1) if _strict_local_minimum(profile, i)]
        if strict:
            selected = strict[0]
            method = "nearest-local-minimum"
        else:
            window = profile[window_start : window_end + 1]
            minimum = float(window.min())
            selected = int(np.flatnonzero(window == minimum)[0] + window_start)
            method = "window-global-minimum"
        review = selected == window_end or selected == profile.size - 1
    else:
        raise ValueError("side must be left or right")
    return selected, review, method


def _integrate_band(
    raw_profile: np.ndarray,
    profile: np.ndarray,
    roi: LaneROI,
    left: int,
    right: int,
    *,
    baseline_left_value: float | None = None,
    baseline_right_value: float | None = None,
) -> tuple[int, float, float]:
    x = np.arange(left, right + 1, dtype=np.float64)
    left_value = float(profile[left]) if baseline_left_value is None else float(baseline_left_value)
    right_value = float(profile[right]) if baseline_right_value is None else float(baseline_right_value)
    baseline = np.linspace(left_value, right_value, right - left + 1)
    excess = np.maximum(profile[left : right + 1] - baseline, 0.0)
    signal = float(trapezoid(excess, x=x))
    area_px = int((right - left + 1) * roi.width)
    background = float((raw_profile[left] + raw_profile[right]) / 2.0)
    return area_px, background, signal


def _peak_connected_bounds(
    profile: np.ndarray,
    peak: int,
    left: int,
    right: int,
    prominence: float,
) -> dict[str, object]:
    """Close one peak at the nearest raw-profile minima on its two sides.

    ``left`` and ``right`` delimit the candidate search window established by
    neighbouring detected peaks (or the outer-boundary search). Within each
    half, the lowest *unsmoothed* profile sample is selected. If a minimum is a
    plateau, the sample nearest the apex wins. This is deterministic and keeps
    the closing line attached to the actual curve at both endpoints.
    """
    if not (0 <= left < peak < right < profile.size):
        raise ValueError("candidate boundaries must strictly contain the peak")

    left_values = np.asarray(profile[left:peak], dtype=np.float64)
    right_values = np.asarray(profile[peak + 1 : right + 1], dtype=np.float64)
    left_minimum = float(np.min(left_values))
    right_minimum = float(np.min(right_values))
    # On a flat valley use the point closest to the peak, avoiding arbitrary
    # expansion across long white/background plateaus.
    tightened_left = int(left + np.flatnonzero(left_values == left_minimum)[-1])
    tightened_right = int(peak + 1 + np.flatnonzero(right_values == right_minimum)[0])
    baseline_left = float(profile[tightened_left])
    baseline_right = float(profile[tightened_right])
    background_slope = float(baseline_right - baseline_left) / max(
        1, tightened_right - tightened_left
    )
    scale = max(float(prominence), 1e-12)
    left_drop = max(0.0, float(profile[peak]) - baseline_left) / scale
    right_drop = max(0.0, float(profile[peak]) - baseline_right) / scale
    boundary_confidence = float(np.clip(min(left_drop, right_drop), 0.0, 1.0))

    synthetic_roi = LaneROI(1, 0, 0, 1, profile.size)
    _, _, initial_signal = _integrate_band(
        np.zeros_like(profile),
        profile,
        synthetic_roi,
        left,
        right,
        baseline_left_value=float(profile[left]),
        baseline_right_value=float(profile[right]),
    )
    _, _, connected_signal = _integrate_band(
        np.zeros_like(profile),
        profile,
        synthetic_roi,
        tightened_left,
        tightened_right,
        baseline_left_value=baseline_left,
        baseline_right_value=baseline_right,
    )
    return {
        "left": tightened_left,
        "right": tightened_right,
        "baseline_left": baseline_left,
        "baseline_right": baseline_right,
        "low_gate": 0.0,
        "high_gate": 0.0,
        "excluded_signal": max(0.0, initial_signal - connected_signal),
        "left_returned": tightened_left > 0,
        "right_returned": tightened_right < profile.size - 1,
        "method": "valley-minimum",
        "confidence": boundary_confidence,
        "background_slope": background_slope,
    }


def quantify_lane(
    image: LoadedImage,
    roi: LaneROI,
    config: AlgorithmConfig | None = None,
    *,
    boundary_overrides: Mapping[int, tuple[int, int]] | None = None,
    insets: ROIInsets | None = None,
    auto_border: bool = True,
) -> LaneResult:
    config = config or AlgorithmConfig()
    border_info: dict[str, object] = {"mode": "disabled", "insets": ROIInsets().as_dict()}
    if insets is None:
        if auto_border:
            insets, border_info = detect_border_insets(image, roi)
        else:
            insets = ROIInsets()
    else:
        insets.validate(roi)
        border_info = {"mode": "manual", "insets": insets.as_dict()}
    effective_roi = insets.apply(roi)
    effective_roi.validate(image.shape[1], image.shape[0])
    raw_profile, profile = compute_profiles(image, effective_roi)
    warnings: list[str] = []
    if any((insets.top, insets.right, insets.bottom, insets.left)):
        warnings.append(
            "high-confidence near-edge frame evidence was excluded from the effective ROI; review both ROI outlines"
        )
    medium_sides = [
        side
        for side, item in (border_info.get("sides", {}) if isinstance(border_info, dict) else {}).items()
        if isinstance(item, dict) and item.get("action") == "review"
    ]
    if medium_sides:
        warnings.append(
            "possible frame evidence needs review on: " + ", ".join(medium_sides)
        )

    def make_result(
        robust_range: float,
        prominence_threshold: float,
        bands: list[BandResult],
        status: str,
        extra_warnings: list[str] | None = None,
        detection: np.ndarray | None = None,
        weak_candidates: list[dict[str, object]] | None = None,
    ) -> LaneResult:
        return LaneResult(
            roi=roi,
            raw_profile=raw_profile,
            profile=profile,
            robust_range=robust_range,
            prominence_threshold=prominence_threshold,
            bands=bands,
            status=status,
            warnings=warnings + ([] if extra_warnings is None else extra_warnings),
            effective_roi=effective_roi,
            insets=insets,
            border_detection=border_info,
            detection_profile=np.asarray(detection if detection is not None else profile, dtype=np.float64),
            weak_candidates=[] if weak_candidates is None else weak_candidates,
        )

    if profile.size < 3:
        return make_result(0.0, 0.0, [], "needs-review", ["profile is too short"])
    dynamic_range = _robust_dynamic_range(profile)
    prominence_threshold = config.prominence_fraction * dynamic_range
    if not np.isfinite(dynamic_range) or dynamic_range <= 0:
        return make_result(
            dynamic_range,
            0.0,
            [],
            "needs-review",
            ["profile has zero dynamic range; no peaks were detected"],
        )
    detection_profile = profile
    if config.smoothing_sigma > 0:
        detection_profile = gaussian_filter1d(profile, config.smoothing_sigma, mode="nearest")
    peaks, properties = find_peaks(
        detection_profile,
        prominence=prominence_threshold,
        width=config.min_width_px,
        distance=config.min_distance_px,
    )
    raw_roi = image.raw_float[
        effective_roi.y0 : effective_roi.y1,
        effective_roi.x0 : effective_roi.x1,
    ]
    weak_candidates = detect_weak_peak_candidates(
        raw_roi,
        profile,
        peaks,
        dtype_max=image.dtype_max,
        global_range=dynamic_range,
    )
    if peaks.size == 0:
        return make_result(
            dynamic_range,
            prominence_threshold,
            [],
            "needs-review",
            ["no peaks met the current detection parameters"],
            detection_profile,
            weak_candidates,
        )
    order = np.argsort(peaks)
    peaks = peaks[order]
    widths = np.asarray(properties["widths"])[order]
    prominences = np.asarray(properties["prominences"])[order]
    border_peak_decisions = {
        decision.peak_index: decision
        for decision in classify_black_border_peaks(
            raw_roi,
            profile,
            peaks,
            prominences,
            dtype_max=image.dtype_max,
        )
    }
    shared = [_valley_between(profile, int(peaks[i]), int(peaks[i + 1])) for i in range(len(peaks) - 1)]
    bands: list[BandResult] = []
    overrides = boundary_overrides or {}
    for index, (peak_value, width_value, prominence_value) in enumerate(
        zip(peaks, widths, prominences, strict=True), start=1
    ):
        peak = int(peak_value)
        width = float(width_value)
        band_warnings: list[str] = []
        boundary_source = "auto"
        needs_review = False
        excluded_background_signal = 0.0
        if index in overrides:
            left, right = overrides[index]
            if any(isinstance(v, bool) or not isinstance(v, int) for v in (left, right)):
                raise QuantificationError(f"manual boundaries for band {index} must be integers")
            if not (0 <= left < peak < right < profile.size):
                raise QuantificationError(
                    f"manual boundaries for band {index} must satisfy 0 <= left < peak < right < {profile.size}"
                )
            boundary_source = "manual"
        else:
            if index == 1:
                left, review, method = _outer_boundary(profile, peak, width, "left")
                needs_review |= review
                if review:
                    band_warnings.append(f"left boundary from {method} touches its search-window or ROI edge")
            else:
                left = shared[index - 2]
            if index == len(peaks):
                right, review, method = _outer_boundary(profile, peak, width, "right")
                needs_review |= review
                if review:
                    band_warnings.append(f"right boundary from {method} touches its search-window or ROI edge")
            else:
                right = shared[index - 1]
        valid = 0 <= left < peak < right < profile.size
        auto_left, auto_right = int(left), int(right)
        support: dict[str, object] | None = None
        if valid and boundary_source == "auto":
            support = _peak_connected_bounds(
                profile, peak, int(left), int(right), float(prominence_value)
            )
            left = int(support["left"])
            right = int(support["right"])
            auto_left, auto_right = left, right
            excluded_background_signal = float(support["excluded_signal"])
            if excluded_background_signal > max(1e-9, float(prominence_value) * 0.02):
                band_warnings.append(
                    "near-linear background outside the apex-connected peak support was not integrated"
                )
            if not bool(support["left_returned"]):
                needs_review = True
                band_warnings.append("left side did not return to stable background inside the search interval")
            if not bool(support["right_returned"]):
                needs_review = True
                band_warnings.append("right side did not return to stable background inside the search interval")
            if support["method"] != "valley-minimum":
                needs_review = True
                band_warnings.append(
                    "one or both valley minima were weak; a candidate-boundary fallback was used"
                )
        valid = 0 <= left < peak < right < profile.size
        if not valid:
            needs_review = True
            band_warnings.append("boundaries do not strictly contain the peak; manual correction is required")
            area_px = None
            background = None
            signal = None
            baseline_left_value = None
            baseline_right_value = None
        else:
            if support is None:
                baseline_left_value = float(profile[left])
                baseline_right_value = float(profile[right])
            else:
                baseline_left_value = float(support["baseline_left"])
                baseline_right_value = float(support["baseline_right"])
            area_px, background, signal = _integrate_band(
                raw_profile,
                profile,
                effective_roi,
                left,
                right,
                baseline_left_value=baseline_left_value,
                baseline_right_value=baseline_right_value,
            )
        decision = border_peak_decisions[peak]
        edge_artifact: dict[str, object] = decision.as_dict()
        included = True
        detection_source = "auto"
        if decision.action == "exclude":
            # Boundary quality is irrelevant for a confidently excluded frame
            # peak and must not force the whole lane into review by itself.
            needs_review = False
            included = False
            detection_source = "auto-border-peak-filter"
            band_warnings.append(
                "extreme straight near-edge peak matched high-confidence black-border evidence and was excluded"
            )
        elif decision.action == "review":
            needs_review = True
            band_warnings.append(
                "possible black-border peak needs confirmation during review"
            )
        bands.append(
            BandResult(
                band_index=index,
                peak_y_relative=peak,
                peak_y_absolute=effective_roi.y0 + peak,
                height=float(profile[peak]),
                prominence=float(prominence_value),
                width=width,
                left=int(left),
                right=int(right),
                left_absolute=effective_roi.y0 + int(left),
                right_absolute=effective_roi.y0 + int(right),
                boundary_source=boundary_source,
                status="needs-review" if needs_review else "ok",
                area_px=area_px,
                background=background,
                signal=signal,
                band_id=f"L{roi.lane_id}-A{peak}",
                auto_left=auto_left,
                auto_right=auto_right,
                auto_baseline_left_value=baseline_left_value,
                auto_baseline_right_value=baseline_right_value,
                baseline_left_value=baseline_left_value,
                baseline_right_value=baseline_right_value,
                baseline_source="manual" if boundary_source == "manual" else "auto",
                detection_source=detection_source,
                included=included,
                review_status="draft",
                excluded_background_signal=excluded_background_signal,
                boundary_method=(
                    "manual" if boundary_source == "manual" else str(support["method"] if support else "candidate")
                ),
                boundary_confidence=(
                    None if support is None else float(support["confidence"])
                ),
                background_slope=(
                    None if support is None else float(support["background_slope"])
                ),
                edge_artifact=edge_artifact,
                warnings=band_warnings,
            )
        )
    status = "needs-review" if any(band.status != "ok" for band in bands) else "ok"
    return make_result(
        dynamic_range,
        prominence_threshold,
        bands,
        status,
        detection=detection_profile,
        weak_candidates=weak_candidates,
    )


def quantify_image(
    image: LoadedImage,
    lanes: Sequence[LaneROI],
    config: AlgorithmConfig | None = None,
    *,
    reference_lane_id: int | None = None,
    identifier: str | None = None,
    boundary_overrides: Mapping[int, Mapping[int, tuple[int, int]]] | None = None,
    lane_insets: Mapping[int, ROIInsets] | None = None,
) -> ImageResult:
    config = config or AlgorithmConfig()
    height, width = image.shape
    checked = validate_lanes(lanes, width, height)
    if reference_lane_id is not None and reference_lane_id not in {lane.lane_id for lane in checked}:
        raise QuantificationError(f"reference lane {reference_lane_id} does not exist")
    results = [
        quantify_lane(
            image,
            roi,
            config,
            boundary_overrides=(boundary_overrides or {}).get(roi.lane_id),
            insets=(lane_insets or {}).get(roi.lane_id),
        )
        for roi in checked
    ]
    # Cross-lane repetition is supporting evidence only. It can strengthen an
    # already line-shaped review candidate, but cannot turn an ordinary band
    # into a border by alignment alone.
    for lane in results:
        tolerance = max(2, int(round(lane.profile.size * 0.01)))
        for band in lane.bands:
            matches = sum(
                any(abs(other_band.peak_y_relative - band.peak_y_relative) <= tolerance for other_band in other.bands)
                for other in results if other is not lane
            )
            consensus = matches / max(1, len(results) - 1)
            evidence = band.edge_artifact
            evidence["cross_lane_consensus"] = float(consensus)
            old_likelihood = float(evidence.get("border_likelihood", evidence.get("confidence", 0.0)))
            line_shaped = float(evidence.get("line_coverage", 0.0)) >= 0.70 and float(evidence.get("boundary_straightness", 0.0)) >= 0.68
            new_likelihood = float(min(1.0, old_likelihood + (0.06 * consensus if line_shaped else 0.0)))
            evidence["border_likelihood"] = new_likelihood
            if band.included and evidence.get("action") == "review" and line_shaped and new_likelihood >= 0.80:
                band.included = False
                band.detection_source = "auto-border-peak-filter-v3-consensus"
                evidence["action"] = "exclude"
                band.warnings.append("repeated straight-line morphology across lanes strengthened black-border evidence")
        for candidate in lane.weak_candidates:
            matches = sum(
                any(abs(int(other_candidate["peak_y_relative"]) - int(candidate["peak_y_relative"])) <= tolerance for other_candidate in other.weak_candidates)
                for other in results if other is not lane
            )
            consensus = matches / max(1, len(results) - 1)
            candidate["cross_lane_consensus"] = float(consensus)
            if float(candidate.get("border_likelihood", 0.0)) < 0.45:
                candidate["real_peak_score"] = float(min(1.0, float(candidate["real_peak_score"]) + 0.05 * consensus))
    result = ImageResult(
        image=image,
        identifier=identifier or image.path.name,
        lanes=results,
        config=config.as_dict(),
        reference_lane_id=reference_lane_id,
        status="needs-review" if any(lane.status != "ok" for lane in results) else "ok",
        warnings=list(image.warnings),
    )
    if reference_lane_id is not None:
        raise QuantificationError("Normalization is outside this numerical adapter")
    return result

