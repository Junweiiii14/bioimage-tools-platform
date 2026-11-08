"""Check one normal CLI export and P032's fixed labels against independent measurements."""

import csv
import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import tifffile
from bioimage_app.nuclei_results import read_result
from nuclei_intensity.api import measure_intensity
from nuclei_tool.api import read_nuclei_input


def verify(workspace: Path, target: Path, table: Path) -> None:
    result = read_result(str(workspace))
    with table.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    provenance = json.loads((table.parent / "provenance.json").read_bytes())
    assert provenance["source_sha256"] == result.source_sha256
    assert provenance["label_sha256"] == hashlib.sha256(result.labels).hexdigest()
    assert provenance["execution_id"] == result.execution_id
    pixels = tifffile.imread(target)

    labels = np.load(BytesIO(result.labels), allow_pickle=False)
    ids = [int(i) for i in np.unique(labels) if i]
    assert [int(r["nucleus_id"]) for r in rows] == ids
    assert len(rows) == result.display.count == provenance["nuclei_count"]
    target_sha = hashlib.sha256(target.read_bytes()).hexdigest()
    assert provenance["target_sha256"] == target_sha
    for row, label in zip(rows, ids, strict=True):
        values = pixels[labels == label]
        assert int(row["area_px2"]) == values.size
        assert int(row["integrated_dn_px"]) == int(values.sum())
        assert float(row["mean_dn"]) == float(values.mean())
        assert row["target_sha256"] == target_sha and row["run_id"] == result.run_id

    reference = Path(__file__).resolve().parents[1] / "P-032"
    with (reference / "per-nucleus.csv").open(encoding="utf-8") as stream:
        expected = [
            (
                int(r["object_id"]),
                int(r["area_px2"]),
                float(r["mean_dn"]),
                int(r["integrated_dn_px"]),
            )
            for r in csv.DictReader(stream)
            if r["channel"] == "PH3"
        ]
    fixed = tifffile.imread(reference / "nuclei-labels.tif")
    assert fixed.dtype == np.int32 and fixed.min() >= 0
    assert (
        list(measure_intensity(fixed.astype(np.uint32), read_nuclei_input(str(target)).pixels))
        == expected
    )
    print(f"Verified {len(rows)} committed StarDist objects and {len(expected)} fixed PH3 objects")


if __name__ == "__main__":
    verify(*(Path(p) for p in sys.argv[1:]))
