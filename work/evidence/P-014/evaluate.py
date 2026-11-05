"""Instance metric copied unchanged from audited P013 probe; contiguous IDs required."""

import numpy as np


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


def main():
    import argparse
    import csv
    import json
    from pathlib import Path

    from PIL import Image

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--group", choices=["development", "evaluation"], required=True)
    parser.add_argument("--prediction", action="append", required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    plan = json.loads(Path(__file__).with_name("dataset-plan.json").read_text(encoding="utf-8"))
    rows = []
    for specification in args.prediction:
        method, directory = specification.split("=", 1)
        for item in plan["images"]:
            if item["group"] != args.group:
                continue
            name = Path(item["Files"]).stem
            reference = np.asarray(Image.open(args.root / item["mask"]))
            prediction = np.load(Path(directory) / f"{name}_labels.npy", allow_pickle=False)
            if reference.ndim != 2 or reference.shape != prediction.shape:
                raise ValueError("Shape mismatch")
            dense = []
            for labels in (reference, prediction):
                if not np.issubdtype(labels.dtype, np.integer) or np.any(labels < 0):
                    raise ValueError("Invalid instance labels")
                # Relabel IDs only: retain each object's exact pixels, never join touching IDs.
                ids = np.unique(labels)
                if ids[0] != 0:
                    ids = np.r_[0, ids]
                dense.append(np.searchsorted(ids, labels).astype(np.int64))
            result = metrics(*dense)
            denominator = 2 * result["tp"] + result["fp"] + result["fn"]
            result["f1"] = 2 * result["tp"] / denominator if denominator else None
            rows.append(dict(method=method, image=name, **result))
    with (args.output / "metrics.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summaries = {}
    for method in dict.fromkeys(row["method"] for row in rows):
        group = [row for row in rows if row["method"] == method]
        summaries[method] = dict(
            images=len(group),
            mean_f1=float(np.mean([row["f1"] for row in group])),
            mean_relative_count_error=float(
                np.mean([row["relative_count_error"] for row in group])
            ),
            tp=sum(row["tp"] for row in group),
            fp=sum(row["fp"] for row in group),
            fn=sum(row["fn"] for row in group),
        )
    (args.output / "summary.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
