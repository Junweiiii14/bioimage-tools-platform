"""P017 frozen BCA software-reference probe, not a production assay tool."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import time
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
from scipy.stats import linregress
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
manifest = json.loads(Path(__file__).with_name("source-manifest.json").read_text())
for entry in manifest["files"]:
    assert hashlib.sha256((args.source / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
args.output.mkdir(parents=True, exist_ok=False)
start = time.perf_counter()
base = args.source / "examples/example_run/experimental_data"
wb = openpyxl.load_workbook(
    base / "raw_data/2026.06.15_BCA_assay_data.xlsx", read_only=True, data_only=True
)
sheet = wb.active
assert sheet["B18"].value == "Wavelengths:  562"
raw = []
for row in sheet.iter_rows(min_row=25, max_row=32, values_only=True):
    for col, value in enumerate(row[2:14], 1):
        raw.append({"well": f"{row[1]}{col}", "raw_A562": value})
wb.close()
layout = pd.read_csv(base / "raw_data/2026.06.15_BCA_exp_metadata.csv")
assert len(layout) == 42 and not layout.well.duplicated().any()
wells = layout.merge(pd.DataFrame(raw), on="well", validate="one_to_one")
assert len(wells) == 42 and np.isfinite(wells.raw_A562).all()
assert not wells.suppress.any()
blank = wells.loc[wells.type == "blank", "raw_A562"].mean()
wells["corrected_A562"] = wells.raw_A562 - blank
std = wells[wells.type == "std"].copy()
x, y = std.std_conc.to_numpy(), std.corrected_A562.to_numpy()
reverse = linregress(y, x, nan_policy="raise")
forward = linregress(x, y, nan_policy="raise")
ols_reverse = OLS(x, add_constant(y), missing="raise").fit()
ols_forward = OLS(y, add_constant(x), missing="raise").fit()
np.testing.assert_allclose(
    ols_reverse.params, [reverse.intercept, reverse.slope], atol=1e-10, rtol=1e-10
)
np.testing.assert_allclose(
    ols_forward.params, [forward.intercept, forward.slope], atol=1e-10, rtol=1e-10
)
reference_performance = pd.read_csv(
    base / "processed_data/Protein/2026.06.15_PTN_analytical_performance.csv"
).iloc[0]
residual_sd = np.sqrt(ols_forward.mse_resid)
lod, loq = 3 * residual_sd / forward.slope, 10 * residual_sd / forward.slope
observed = [lod, loq, forward.slope, forward.intercept, ols_forward.rsquared_adj]
expected = reference_performance[
    ["LOD_conc", "LOQ_conc", "regression_slope", "regression_intercept", "r_squared_adj"]
].to_numpy(dtype=float)
np.testing.assert_allclose(observed, expected, atol=1e-10, rtol=1e-10)
std["forward_residual"] = y - ols_forward.predict(add_constant(x))
std.to_csv(args.output / "standards.csv", index=False)
samples = wells[wells.type == "sample"].copy()
# Reproduce upstream volume convention only; chemical validity remains unverified.
samples["reference_dilution_factor"] = samples.sample_dil * std.volume.iloc[0] / samples.volume
samples["reverse_mg_ml"] = (
    reverse.intercept + reverse.slope * samples.corrected_A562
) * samples.reference_dilution_factor
samples["forward_mg_ml"] = (
    (samples.corrected_A562 - forward.intercept) / forward.slope * samples.reference_dilution_factor
)
samples["below_upstream_calculated_loq"] = (
    (samples.corrected_A562 - forward.intercept) / forward.slope
) < loq
samples["negative_corrected_signal"] = samples.corrected_A562 < 0
samples["outside_observed_standard_signal"] = (samples.corrected_A562 < y.min()) | (
    samples.corrected_A562 > y.max()
)
samples.to_csv(args.output / "sample-wells.csv", index=False)
wells.to_csv(args.output / "all-defined-wells.csv", index=False)
summary = samples.groupby("sample_ID").agg(
    n_technical=("well", "size"),
    mean_corrected_A562=("corrected_A562", "mean"),
    sd_corrected_A562=("corrected_A562", "std"),
    reverse_mg_ml=("reverse_mg_ml", "mean"),
    forward_mg_ml=("forward_mg_ml", "mean"),
    below_loq_wells=("below_upstream_calculated_loq", "sum"),
)
reference = pd.read_csv(base / "processed_data/Protein/2026.06.15_PTN_levels.csv").set_index(
    "sample_ID"
)
summary = summary.join(
    reference[["value", "extrapolated"]].rename(
        columns={"value": "upstream_mg_ml", "extrapolated": "upstream_extrapolated"}
    ),
    validate="one_to_one",
)
summary["reference_error"] = summary.reverse_mg_ml - summary.upstream_mg_ml
summary["direction_difference_pct"] = 100 * (summary.forward_mg_ml / summary.reverse_mg_ml - 1)
np.testing.assert_allclose(summary.reverse_mg_ml, summary.upstream_mg_ml, atol=1e-10, rtol=1e-10)
summary.to_csv(args.output / "samples.csv")
# Direct library failure probes use synthetic arrays solely for engineering behavior.
failures = {}
for name, xx, yy in [("nan", [0, 1, 2], [0, np.nan, 2]), ("constant_x", [1, 1, 1], [0, 1, 2])]:
    try:
        probe = linregress(xx, yy, nan_policy="raise")
        failures[name] = {
            "returned_finite_slope": bool(np.isfinite(probe.slope)),
            "slope": str(probe.slope),
        }
    except ValueError as exc:
        failures[name] = str(exc)
assert isinstance(failures["nan"], str)
assert failures["constant_x"]["returned_finite_slope"] is False
result = {
    "python": platform.python_version(),
    "platform": platform.platform(),
    "versions": {
        p: importlib.metadata.version(p)
        for p in ["numpy", "scipy", "statsmodels", "pandas", "openpyxl"]
    },
    "seconds_excluding_imports": time.perf_counter() - start,
    "defined_wells": len(wells),
    "blank_A562": float(blank),
    "forward_slope": float(forward.slope),
    "forward_intercept": float(forward.intercept),
    "reverse_slope": float(reverse.slope),
    "reverse_intercept": float(reverse.intercept),
    "calculated_lod_mg_ml": float(lod),
    "calculated_loq_mg_ml": float(loq),
    "adjusted_r2": float(ols_forward.rsquared_adj),
    "max_reference_error": float(summary.reference_error.abs().max()),
    "synthetic_library_errors": failures,
    "scope": "software-reference reproduction; no chemical truth or student validation",
}
(args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(summary.to_string())
print(json.dumps(result, indent=2))
