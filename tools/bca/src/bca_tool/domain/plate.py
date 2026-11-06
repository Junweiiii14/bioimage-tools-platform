"""Validated single-plate data and fixed P018 numerical semantics; no I/O."""

from dataclasses import dataclass
from statistics import mean, stdev
from typing import Literal

import numpy as np

METHOD = "pierce25-point-v0-research"
LEVELS = (0.0, 25.0, 125.0, 250.0, 500.0, 750.0, 1000.0, 1500.0, 2000.0)


@dataclass(frozen=True)
class Well:
    plate_id: str
    well: str
    role: Literal["blank", "standard", "sample"]
    sample_id: str
    technical_replicate: str
    a562: float
    standard_ug_ml: float | None
    dilution_factor: float


@dataclass(frozen=True)
class WellResult:
    source: Well
    blank_mean: float
    corrected_a562: float
    standard_mean: float | None
    standard_residual: float | None
    assayed_ug_ml: float | None
    original_ug_ml: float | None
    status: str
    reason: str


@dataclass(frozen=True)
class SampleResult:
    sample_id: str
    dilution_factor: float
    n_total: int
    n_valid: int
    mean_original_ug_ml: float | None
    sd_original_ug_ml: float | None
    status: str
    reason: str


@dataclass(frozen=True)
class PlateResult:
    wells: tuple[WellResult, ...]
    samples: tuple[SampleResult, ...]


def analyze_plate(wells: tuple[Well, ...]) -> PlateResult:
    """Consume input validated by read_plate; invert each well before summarizing."""
    blank = mean(w.a562 for w in wells if w.role == "blank")
    standards = {
        c: mean(w.a562 - blank for w in wells if w.role != "sample" and w.standard_ug_ml == c)
        for c in LEVELS
    }
    curve = tuple(standards.values())
    if not all(np.isfinite(curve)) or any(a >= b for a, b in zip(curve, curve[1:], strict=False)):
        raise ValueError("invalid_curve: corrected standard means must strictly increase")
    results: list[WellResult] = []
    for w in wells:
        corrected = w.a562 - blank
        standard = standards[w.standard_ug_ml] if w.standard_ug_ml is not None else None
        assayed = original = None
        status, reason = "not_applicable", "calibration well"
        if w.role == "sample":
            if corrected < curve[1]:
                status, reason = (
                    "below_supported_range",
                    "below lowest nonzero standard (25 ug/mL); LoQ unknown",
                )
            elif corrected > curve[-1]:
                status, reason = "above_supported_range", "above calibration; no extrapolation"
            else:
                assayed = float(np.interp(corrected, curve, LEVELS, left=np.nan, right=np.nan))
                original = assayed * w.dilution_factor
                if not np.isfinite(original):
                    raise ValueError("numerical_overflow: original concentration is not finite")
                status, reason = "research_estimate", "LoQ and chemical accuracy unknown"
        results.append(
            WellResult(
                w,
                blank,
                corrected,
                standard,
                corrected - standard if standard is not None else None,
                assayed,
                original,
                status,
                reason,
            )
        )
    samples: list[SampleResult] = []
    for identity in dict.fromkeys(w.sample_id for w in wells if w.role == "sample"):
        group = [r for r in results if r.source.role == "sample" and r.source.sample_id == identity]
        values = [r.original_ug_ml for r in group if r.original_ug_ml is not None]
        complete = len(values) == len(group)
        samples.append(
            SampleResult(
                identity,
                group[0].source.dilution_factor,
                len(group),
                len(values),
                mean(values) if complete else None,
                stdev(values) if complete else None,
                "research_estimate" if complete else "partial",
                "technical replicates only; LoQ unknown"
                if complete
                else "one or more wells outside supported range; no complete summary",
            )
        )
    return PlateResult(tuple(results), tuple(samples))
