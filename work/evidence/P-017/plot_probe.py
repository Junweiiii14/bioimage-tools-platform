"""Visualize the P017 probe without implying scientific admission."""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

source, output = map(Path, sys.argv[1:])
std = pd.read_csv(source / "standards.csv")
samples = pd.read_csv(source / "sample-wells.csv")
r = json.loads((source / "result.json").read_text())
with plt.rc_context({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    ax = axes[0]
    ax.scatter(
        std.std_conc, std.corrected_A562, c="#0072B2", marker="o", label="All 21 standard wells"
    )
    xx = np.array([0, 0.8])
    ax.plot(
        xx,
        r["forward_intercept"] + r["forward_slope"] * xx,
        color="#333333",
        linestyle="--",
        label="Forward OLS (diagnostic)",
    )
    ax.set(
        xlabel="BSA standard (mg/mL)",
        ylabel="Blank-corrected A562",
        title="A. Published BCA plate: software reproduction",
        xlim=(-0.03, 0.83),
        ylim=(0, 0.65),
    )
    ax.legend(fontsize=8)
    ax = axes[1]
    for i, (_name, group) in enumerate(samples.groupby("sample_ID")):
        values = group.forward_mg_ml / group.reference_dilution_factor
        ax.scatter(i + np.array([-0.08, 0, 0.08]), values, marker="x", color="#A33D00", s=38)
        ax.plot([i - 0.18, i + 0.18], [values.mean()] * 2, color="#333333")
    ax.axhline(
        r["calculated_loq_mg_ml"],
        linestyle="--",
        color="#333333",
        label="Upstream calculated LoQ (not validated)",
    )
    ax.set(
        xticks=range(6),
        xticklabels=sorted(samples.sample_ID.unique()),
        ylabel="Forward inverse estimate (mg/mL)\nbefore upstream volume/dilution factor",
        title="B. All 18 sample wells fall below calculated LoQ",
        ylim=(0, 0.42),
    )
    ax.legend(fontsize=8, loc="lower right")
    fig.suptitle(
        "Research only • 3 technical wells per sample • biological independence unknown",
        fontsize=11,
    )
    fig.savefig(
        output,
        dpi=180,
        metadata={
            "Description": (
                "No exclusions. Blank A562=0.034; individual technical wells shown. "
                "No confidence interval or biological inference."
            )
        },
    )
    plt.close(fig)
