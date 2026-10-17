"""Second-pass weak-peak suggestions without changing primary detection."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks, peak_prominences, peak_widths

from .border_peak_filter import classify_black_border_peaks


def _local_noise(profile: np.ndarray, peak: int, radius: int = 14) -> float:
    window = profile[max(0, peak - radius) : min(profile.size, peak + radius + 1)]
    differences = np.diff(window)
    if differences.size < 2:
        return 0.0
    center = float(np.median(differences))
    return float(1.4826 * np.median(np.abs(differences - center)) / np.sqrt(2.0))


def detect_weak_peak_candidates(
    raw_roi: np.ndarray,
    profile: np.ndarray,
    primary_peaks: np.ndarray,
    *,
    dtype_max: int,
    global_range: float,
) -> list[dict[str, object]]:
    """Return conservative, review-only candidates missed by the primary pass."""
    signal = np.asarray(profile, dtype=np.float64)
    if signal.size < 7 or global_range <= 0:
        return []
    global_noise = _local_noise(signal, signal.size // 2, max(12, signal.size // 4))
    minimum_prominence = max(2.6 * global_noise, 0.0125 * global_range, 1e-9)
    per_scale: list[np.ndarray] = []
    for sigma in (0.8, 1.4):
        smoothed = gaussian_filter1d(signal, sigma, mode="nearest")
        peaks, _ = find_peaks(smoothed, prominence=minimum_prominence, width=1.25, distance=3)
        per_scale.append(peaks.astype(int))
    union = sorted({int(value) for values in per_scale for value in values})
    candidates: list[dict[str, object]] = []
    primary = np.asarray(primary_peaks, dtype=int)
    for peak in union:
        if primary.size and int(np.min(np.abs(primary - peak))) <= 2:
            continue
        prominence = float(peak_prominences(signal, np.array([peak]))[0][0])
        width = float(peak_widths(signal, np.array([peak]), rel_height=0.5)[0][0])
        noise = max(_local_noise(signal, peak), global_noise * 0.35, 1e-9)
        local_snr = prominence / noise
        present_scales = sum(bool(np.any(np.abs(values - peak) <= 2)) for values in per_scale)
        stability = present_scales / len(per_scale)
        radius = max(3, int(round(max(width, 1.5) * 2.0)))
        left = signal[max(0, peak - radius) : peak]
        right = signal[peak + 1 : min(signal.size, peak + radius + 1)]
        left_rise = signal[peak] - float(np.min(left)) if left.size else 0.0
        right_drop = signal[peak] - float(np.min(right)) if right.size else 0.0
        two_sided = float(np.clip(min(left_rise, right_drop) / max(prominence, 1e-9), 0.0, 1.0))
        decisions = classify_black_border_peaks(
            raw_roi, signal, np.array([peak]), np.array([prominence]), dtype_max=dtype_max
        )
        border = decisions[0].as_dict()
        border_likelihood = float(border.get("border_likelihood", border.get("confidence", 0.0)))
        score = float(np.clip(
            0.34 * np.clip((local_snr - 2.5) / 4.5, 0.0, 1.0)
            + 0.22 * stability
            + 0.20 * two_sided
            + 0.14 * np.clip(width / 4.0, 0.0, 1.0)
            + 0.10 * np.clip(prominence / max(0.035 * global_range, 1e-9), 0.0, 1.0)
            - 0.34 * border_likelihood,
            0.0, 1.0,
        ))
        if local_snr < 2.5 or score < 0.32:
            continue
        candidates.append({
            "candidate_id": f"W{peak}", "peak_y_relative": peak,
            "prominence": prominence, "width": width, "local_snr": float(local_snr),
            "scale_stability": float(stability), "two_sided_support": two_sided,
            "real_peak_score": score, "border_likelihood": border_likelihood,
            "status": "suggested-weak", "included": False, "edge_artifact": border,
        })
    candidates.sort(key=lambda item: int(item["peak_y_relative"]))
    return candidates
