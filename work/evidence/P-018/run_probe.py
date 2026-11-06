"""Analytic API probe only: no external CSV parser or chemical validation."""

import csv
import json
import platform
import sys
from pathlib import Path

import numpy as np


def inverse(readings, concentration, response):
    """Validate the numerical boundary once; interpolate with the public API."""
    if not all(np.isfinite(a).all() for a in (readings, concentration, response)):
        raise ValueError("nonfinite_input")
    if not (np.all(np.diff(concentration) > 0) and np.all(np.diff(response) > 0)):
        raise ValueError("nonmonotonic_calibration")
    return np.interp(readings, response, concentration, left=np.nan, right=np.nan)


out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=False)
# Deliberately invented numbers, not digitized manufacturer data.
concentration = np.array([0, 25, 125, 250, 500, 750, 1000, 1500, 2000.0])
response = np.array([0, 0.02, 0.10, 0.20, 0.38, 0.54, 0.68, 0.90, 1.08])
blank = np.array([0.049, 0.051])
blank_mean = float(np.mean(blank))
standard_raw = response[:, None] + blank[None, :]
corrected = standard_raw.mean(axis=1) - blank_mean
np.testing.assert_allclose(corrected, response, atol=1e-10, rtol=1e-10)
# S1 straddles a slope change: inverse(mean A) differs from mean(inverse A).
raw = np.array([0.42, 0.44, 0.06, 1.14, 0.04])
sample_ids = ["S1", "S1", "LOW", "HIGH", "NEGATIVE"]
dilutions = np.array([10, 10, 1, 1, 1])
estimates = inverse(raw - blank_mean, concentration, corrected)
expected = [486.1111111111111, 515.625, 12.5, np.nan, np.nan]
np.testing.assert_allclose(estimates, expected, atol=1e-10, rtol=1e-10)
assert abs(float(np.mean(estimates[:2] * 10)) - 5008.680555555556) < 1e-10
assert abs(float(inverse([0.38], concentration, corrected)[0]) - 500) < 1e-10
np.testing.assert_allclose(
    inverse([0, 0.02, 1.08], concentration, response), [0, 25, 2000], atol=1e-10
)
failures = {}
for name, readings, curve in [
    ("nonfinite", [np.nan], response),
    ("flat", [0.1], np.zeros(9)),
    ("descending", [0.1], response[::-1]),
]:
    try:
        inverse(readings, concentration, curve)
    except ValueError as error:
        failures[name] = str(error)
    else:
        raise AssertionError(name)

rows = []
for i, (level, values) in enumerate(zip(concentration, standard_raw, strict=True)):
    for rep, value in enumerate(values, 1):
        rows.append(
            [
                "synthetic",
                f"{'AB'[rep - 1]}{i + 1}",
                "blank" if level == 0 else "standard",
                f"BSA_{level:g}",
                rep,
                float(value),
                float(level),
                1,
            ]
        )
for i, (name, value, factor) in enumerate(zip(sample_ids, raw, dilutions, strict=True)):
    rows.append(
        [
            "synthetic",
            f"C{i + 1}",
            "sample",
            name,
            i + 1 if name == "S1" else 1,
            float(value),
            "",
            int(factor),
        ]
    )
with (out / "synthetic-input.csv").open("w", newline="", encoding="utf-8") as stream:
    writer = csv.writer(stream)
    writer.writerow(
        [
            "plate_id",
            "well",
            "role",
            "sample_id",
            "technical_replicate",
            "a562",
            "standard_ug_ml",
            "dilution_factor",
        ]
    )
    writer.writerows(rows)
with (out / "sample-wells.csv").open("w", newline="", encoding="utf-8") as stream:
    writer = csv.writer(stream)
    writer.writerow(
        [
            "sample_id",
            "a562",
            "corrected_a562",
            "dilution_factor",
            "assayed_ug_ml",
            "original_ug_ml",
            "status",
        ]
    )
    for name, value, estimate, factor in zip(sample_ids, raw, estimates, dilutions, strict=True):
        status = (
            "outside_calibration"
            if not np.isfinite(estimate)
            else ("below_supported_range" if estimate < 25 else "research_estimate")
        )
        usable = status == "research_estimate"
        writer.writerow(
            [
                name,
                value,
                value - blank_mean,
                factor,
                float(estimate) if usable else "",
                float(estimate * factor) if usable else "",
                status,
            ]
        )
result = {
    "evidence": "analytic_synthetic_only",
    "method": "pierce25-point-v0-research",
    "python": platform.python_version(),
    "numpy": np.__version__,
    "blank_mean": blank_mean,
    "atol": 1e-10,
    "rtol": 1e-10,
    "S1_technical_n": 2,
    "S1_original_mean_ug_ml": float(np.mean(estimates[:2] * 10)),
    "S1_original_sd_ug_ml": float(np.std(estimates[:2] * 10, ddof=1)),
    "inverse_of_mean_assayed_ug_ml": 500,
    "boundary_rejections": failures,
    "LoQ": None,
    "chemical_validation": False,
}
(out / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
print(json.dumps(result, indent=2))
