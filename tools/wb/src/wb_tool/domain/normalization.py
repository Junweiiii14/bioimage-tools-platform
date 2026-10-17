"""Explicit finite signal ratios; no matching, files, arrays or implicit reference selection."""

from math import fsum, isfinite

NORMALIZATION_ALGORITHM = "lane_reference_ratio@1"


def signal_ratio(target: float, reference: float) -> float:
    if isinstance(target, bool) or not isfinite(target) or target < 0:
        raise ValueError("目标信号必须为有限非负值")
    if isinstance(reference, bool) or not isfinite(reference) or reference <= 0:
        raise ValueError("参照信号必须为有限正值")
    value = target / reference
    if not isfinite(value) or (value == 0 and target > 0):
        raise ValueError("比值超出可表示的数值范围")
    return value


def control_mean(values: tuple[float, ...]) -> float:
    if not values or any(isinstance(v, bool) or not isfinite(v) or v < 0 for v in values):
        raise ValueError("对照比值必须全部有效，不能跳过缺失对照")
    # Scale by the largest value before summing to avoid overflow and tiny/n underflow.
    maximum = max(values)
    if maximum <= 0:
        raise ValueError("对照均值必须大于0")
    mean = maximum * (fsum(v / maximum for v in values) / len(values))
    if not isfinite(mean) or mean <= 0:
        raise ValueError("对照均值超出可表示的数值范围")
    return mean
