"""Replay one frozen ExampleHuman field. All output goes into a new directory."""

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage

HERE = Path(__file__).resolve().parent
FIELD = "AS_09125_050116030001_D03f00"
CHANNELS = {"DNA": "d0", "PH3": "d1"}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("p014", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--cp", type=Path, default=Path("C:/Program Files/CellProfiler/CellProfiler.exe")
    )
    args = parser.parse_args()
    source = args.p014.resolve()
    out = args.output.resolve()
    example = source / "official-human/ExampleHuman"
    reference = source / "cp-official-human-01"
    official = json.loads((HERE.parent / "P-014/official-smoke.json").read_text())
    archive = source / "ExampleHuman.zip"
    for path, key in [(archive, "archive_sha256"), (args.cp, "exe_sha256")]:
        if hashlib.sha256(path.read_bytes()).hexdigest() != official[key]:
            raise ValueError(f"Unexpected source: {path}")
    with zipfile.ZipFile(archive) as bundle:
        for path in [example / "ExampleHuman.cppipe", *sorted((example / "images").glob("*.tif"))]:
            if path.read_bytes() != bundle.read(
                "ExampleHuman/" + path.relative_to(example).as_posix()
            ):
                raise ValueError(f"Changed input: {path}")
    out.mkdir(parents=True, exist_ok=False)
    pipe = (example / "ExampleHuman.cppipe").read_text(encoding="utf-8")
    frozen = (HERE.parent / "P-014/cellprofiler-frozen.cppipe").read_text(encoding="utf-8")
    export = frozen[frozen.index("ConvertObjectsToImage:[") : frozen.index("ExportToSpreadsheet:[")]
    export = export.replace("module_num:6|", "module_num:15|").replace(
        "module_num:7|", "module_num:16|"
    )
    pipeline = out / "export.cppipe"
    pipeline.write_text(
        pipe.rstrip().replace("ModuleCount:14", "ModuleCount:16") + "\n\n" + export,
        encoding="utf-8",
    )
    done = out / "done.txt"
    env = os.environ.copy()
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        directory = out / key.lower()
        directory.mkdir()
        env[key] = str(directory)
    env["PROCESSOR_ARCHITECTURE"] = platform.machine()
    subprocess.run(
        [
            str(args.cp),
            "-c",
            "-r",
            "-p",
            str(pipeline),
            "-i",
            str(example / "images"),
            "-o",
            str(out),
            "-d",
            str(done),
        ],
        check=True,
        env=env,
    )
    if done.read_text().strip() != "Complete":
        raise ValueError("Incomplete label export")
    label_path = out / f"{FIELD}d0_labels.npy"
    labels = np.load(label_path, allow_pickle=False)
    (image,) = read_csv(reference / "Image.csv")
    rows = sorted(read_csv(reference / "Nuclei.csv"), key=lambda row: int(row["ObjectNumber"]))
    ids = np.array([int(row["ObjectNumber"]) for row in rows])
    np.testing.assert_array_equal(ids, np.arange(1, 290))
    np.testing.assert_array_equal(np.unique(labels), np.arange(290))
    if (
        labels.dtype != np.int32
        or labels.shape != (512, 512)
        or image["ImageNumber"] != "1"
        or float(image["Count_Nuclei"]) != len(ids)
        or any(row["ImageNumber"] != "1" for row in rows)
    ):
        raise ValueError("Unexpected label or reference identity")
    foreground = labels > 0
    area = ndimage.sum_labels(foreground, labels, ids).astype(int)
    np.testing.assert_array_equal(area, [float(row["AreaShape_Area"]) for row in rows])
    centers = ndimage.center_of_mass(foreground, labels, ids)
    np.testing.assert_allclose(
        centers,
        [[float(row["Location_Center_Y"]), float(row["Location_Center_X"])] for row in rows],
        rtol=0,
        atol=1e-10,
    )
    records = []
    summary = {}
    for channel, suffix in CHANNELS.items():
        name = image[f"FileName_{channel}"]
        scale = float(image[f"Scaling_{channel}"])
        if name != FIELD + suffix + ".tif" or scale != 255:
            raise ValueError("Unexpected channel or metadata scaling")
        pixels = tifffile.imread(example / "images" / name)
        if pixels.dtype != np.uint8 or pixels.shape != labels.shape:
            raise ValueError("Unexpected raw image")
        sums = ndimage.sum_labels(pixels, labels, ids)
        means = ndimage.mean(pixels, labels, ids)
        ceiling = ndimage.sum_labels(pixels == 255, labels, ids)
        errors = {}
        for column, values in [("MeanIntensity", means), ("IntegratedIntensity", sums)]:
            cp = np.array([float(row[f"Intensity_{column}_{channel}"]) for row in rows])
            # Float32 conversion of individual CP normalized pixels; allow one relative epsilon.
            np.testing.assert_allclose(cp, values / scale, rtol=np.finfo(np.float32).eps, atol=0)
            errors[column] = float(np.max(np.abs(cp - values / scale)))
        summary[channel] = dict(
            file=name,
            scale=scale,
            max_raw=int(pixels.max()),
            ceiling_field_px=int((pixels == 255).sum()),
            ceiling_nuclear_px=int(ceiling.sum()),
            nuclei_at_ceiling=int((ceiling > 0).sum()),
            median_nuclear_mean=float(np.median(means)),
            max_abs_error_cp_units=errors,
        )
        for idx, obj in enumerate(ids):
            y, x = centers[idx]
            records.append(
                dict(
                    field=FIELD,
                    sample="UNKNOWN",
                    object_id=obj,
                    channel=channel,
                    x_px=x,
                    y_px=y,
                    area_px2=area[idx],
                    mean_dn=means[idx],
                    integrated_dn_px=int(sums[idx]),
                    ceiling_px=int(ceiling[idx]),
                    cp_mean=rows[idx][f"Intensity_MeanIntensity_{channel}"],
                    cp_integrated=rows[idx][f"Intensity_IntegratedIntensity_{channel}"],
                )
            )
    with (out / "per-nucleus.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    summary["labels_npy_sha256"] = hashlib.sha256(label_path.read_bytes()).hexdigest()
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    tifffile.imwrite(out / "nuclei-labels.tif", labels, compression="deflate", metadata=None)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
