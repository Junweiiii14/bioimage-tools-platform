"""P013 frozen CPU research probe; reads public archives, never extracts them."""

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import platform
import time
import zipfile
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.filters import threshold_otsu
from skimage.measure import label
from skimage.segmentation import watershed


def metrics(reference, prediction):
    """Strict IoU > .5 ensures unique matches for disjoint instance masks."""
    ng, npred = int(reference.max()), int(prediction.max())
    pairs = np.bincount(
        (reference.ravel() * (npred + 1) + prediction.ravel()),
        minlength=(ng + 1) * (npred + 1),
    ).reshape(ng + 1, npred + 1)
    intersection = pairs[1:, 1:]
    union = pairs.sum(1)[1:, None] + pairs.sum(0)[None, 1:] - intersection
    assert np.all(union > 0)
    matched = (intersection / union) > 0.5
    assert np.all(matched.sum(0) <= 1) and np.all(matched.sum(1) <= 1)
    tp = int(matched.sum())
    return dict(
        gt_count=ng,
        pred_count=npred,
        absolute_count_error=abs(npred - ng),
        relative_count_error=abs(npred - ng) / ng if ng else None,
        tp=tp,
        fp=npred - tp,
        fn=ng - tp,
    )


def segment(raw):
    smoothed = ndimage.gaussian_filter(raw.astype(np.float64), sigma=1)
    binary = smoothed > threshold_otsu(smoothed)
    components = label(binary, connectivity=2)
    sizes = np.bincount(components.ravel())
    binary = binary & (sizes[components] >= 30)
    binary = ndimage.binary_fill_holes(binary)
    baseline = label(binary, connectivity=2)
    distance = ndimage.distance_transform_edt(binary)
    peaks = peak_local_max(distance, min_distance=8, exclude_border=False, labels=binary)
    seeds = np.zeros(raw.shape, dtype=np.int32)
    seeds[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    prediction = watershed(-distance, seeds, mask=binary)
    return baseline, prediction


def write_csv(path, rows):
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    archives = {}
    for name in ("images", "masks", "metadata"):
        path = args.data / f"{name}.zip"
        archives[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    rows, intensities, selected = [], [], []
    with (
        zipfile.ZipFile(args.data / "images.zip") as images,
        zipfile.ZipFile(args.data / "masks.zip") as masks,
        zipfile.ZipFile(args.data / "metadata.zip") as meta,
    ):
        image_names = {
            Path(n).stem: n
            for n in images.namelist()
            if n.startswith("images/") and n.endswith(".tif")
        }
        mask_names = {
            Path(n).stem: n
            for n in masks.namelist()
            if n.startswith("masks/") and n.endswith(".png")
        }
        split_names = {
            split: sorted(meta.read(f"metadata/{split}.txt").decode().splitlines())[:count]
            for split, count in (("validation", 3), ("test", 12))
        }
        assert not set(split_names["validation"]) & set(split_names["test"])
        for split, names in split_names.items():
            for name in names:
                stem = Path(name).stem
                image_bytes, mask_bytes = (
                    images.read(image_names[stem]),
                    masks.read(mask_names[stem]),
                )
                raw = tifffile.imread(io.BytesIO(image_bytes))
                annotation = np.asarray(Image.open(io.BytesIO(mask_bytes)))
                assert raw.dtype == np.uint16 and raw.shape == (520, 696)
                assert annotation.shape[:2] == raw.shape and annotation.shape[2] in (3, 4)
                if annotation.shape[2] == 4:
                    assert np.all(annotation[:, :, 3] == 255)
                reference = label(annotation[:, :, 0], connectivity=2, background=0)
                start = time.perf_counter()
                baseline, prediction = segment(raw)
                elapsed = time.perf_counter() - start
                selected.append(
                    dict(
                        split=split,
                        image=name,
                        image_sha256=hashlib.sha256(image_bytes).hexdigest(),
                        mask_sha256=hashlib.sha256(mask_bytes).hexdigest(),
                        red_values=np.unique(annotation[:, :, 0]).tolist(),
                        saturated_pixels=int(np.count_nonzero(raw == 65535)),
                        segmentation_seconds=elapsed,
                    )
                )
                for method, result in (("connected", baseline), ("watershed", prediction)):
                    rows.append(
                        dict(split=split, image=name, method=method, **metrics(reference, result))
                    )
                for region in range(1, int(prediction.max()) + 1):
                    values = raw[prediction == region].astype(np.float64)
                    intensities.append(
                        dict(
                            split=split,
                            image=name,
                            nucleus=region,
                            area_px=len(values),
                            mean_adu=float(values.mean()),
                            sum_adu=float(values.sum()),
                        )
                    )
    write_csv(args.output / "metrics.csv", rows)
    write_csv(args.output / "intensities.csv", intensities)
    summary = []
    for split in ("validation", "test"):
        for method in ("connected", "watershed"):
            subset = [r for r in rows if r["split"] == split and r["method"] == method]
            tp, fp, fn = (sum(r[k] for r in subset) for k in ("tp", "fp", "fn"))
            summary.append(
                dict(
                    split=split,
                    method=method,
                    images=len(subset),
                    tp=tp,
                    fp=fp,
                    fn=fn,
                    micro_f1=2 * tp / (2 * tp + fp + fn),
                    mean_absolute_count_error=float(
                        np.mean([r["absolute_count_error"] for r in subset])
                    ),
                    mean_relative_count_error=float(
                        np.mean([r["relative_count_error"] for r in subset])
                    ),
                )
            )
    report = dict(
        method_version="p013-nuclei-v1",
        python=platform.python_version(),
        platform=platform.platform(),
        dependencies={d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        archives=archives,
        selected=selected,
        summary=summary,
    )
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
