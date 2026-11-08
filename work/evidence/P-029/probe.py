"""Read only the fixed Müller & Tiret S2 workbook; run from the research venv."""

import hashlib
import math
import sys
from pathlib import Path
from statistics import mean

import openpyxl
import pandas as pd
import qpcr

source = Path(sys.argv[1])
assert hashlib.sha256(source.read_bytes()).hexdigest() == (
    "392883b5337f65c5099f04143bb160fa294492d438d1ebab49c7318ab6b18be3"
)
book = openpyxl.load_workbook(source, data_only=True)
cq = book["TARGET"]
eff = book["Efficiencies"]
rows = range(6, 42, 3)
samples = [cq.cell(row, 3).value for row in rows]
assert samples == [f"{group} {i}" for group in ("Control", "Treatment") for i in range(1, 7)]
analyser = qpcr.Analyser()
analyser.anchor(0.0)
for label, columns in [("workbook", [5, 3, 4]), ("heading", [3, 4, 5])]:
    quantities = []
    for offset, efficiency_col in enumerate(columns):
        factor = mean(eff.cell(row, efficiency_col).value for row in range(4, 40))
        means = []
        for row in rows:
            # In S2 only G30 uses the REF1 Cq range E30:E32 for TARGET.
            col = 5 if label == "workbook" and row == 30 and offset == 0 else 4 + offset
            means.append(mean(cq.cell(row + j, col).value for j in range(3)))
        assay = qpcr.Assay(pd.DataFrame({"id": samples, "Ct": means}), replicates=1)
        assay.efficiency(factor / 2)  # qpcr 4.1.4 internally uses 2 * argument
        quantities.append(analyser.pipe(assay).get()["dCt"].tolist())
    normalized = [t / math.sqrt(a * b) for t, a, b in zip(*quantities, strict=True)]
    calibrator = mean(normalized[:6])
    fold = [v / calibrator for v in normalized]
    displayed = [round(v, 2) for v in fold]
    if label == "workbook":
        assert displayed == [cq.cell(row, 12).value for row in rows]
    print(label, list(zip(samples, displayed, strict=True)))
    print("treatment mean (unrounded / from displayed):", mean(fold[6:]), mean(displayed[6:]))
