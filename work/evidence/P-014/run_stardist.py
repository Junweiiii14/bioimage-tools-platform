"""Direct official StarDist inference; only explicit manifest group and scale."""

import argparse
import json
import os
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--group", choices=["development", "evaluation"], required=True)
    parser.add_argument("--scale", type=float, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["KERAS_HOME"] = str(root / "keras")
    os.environ["MPLCONFIGDIR"] = str(root / "matplotlib")
    import numpy as np
    import tensorflow as tf
    from csbdeep.utils import normalize
    from PIL import Image
    from stardist.models import StarDist2D

    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    start = time.perf_counter()
    model = StarDist2D(None, name="2D_versatile_fluo", basedir=str(root / "models"))
    load_seconds = time.perf_counter() - start
    plan = json.loads(Path(__file__).with_name("dataset-plan.json").read_text(encoding="utf-8"))
    rows = []
    for row in plan["images"]:
        if row["group"] != args.group:
            continue
        name = Path(row["Files"]).stem
        start = time.perf_counter()
        raw = np.asarray(Image.open(root / row["Files"]))
        source_shape = list(raw.shape)
        if raw.ndim == 3:
            if raw.shape[-1] != 3 or not all(
                np.array_equal(raw[..., 0], raw[..., i]) for i in (1, 2)
            ):
                raise ValueError(f"{name}: input is not replicated grayscale")
            raw = raw[..., 0]
        if raw.ndim != 2 or raw.dtype != np.uint8:
            raise ValueError(f"{name}: unexpected input format {raw.shape}, {raw.dtype}")
        labels, _ = model.predict_instances(
            normalize(raw, pmin=3, pmax=99.8, axis=None, clip=False),
            axes="YX",
            scale=args.scale,
            n_tiles=(2, 2),
            show_tile_progress=False,
        )
        if labels.shape != raw.shape:
            raise ValueError("Prediction changed coordinate space")
        seconds = time.perf_counter() - start
        np.save(args.output / f"{name}_labels.npy", labels)
        result = dict(
            image=name,
            source_shape=source_shape,
            count=int(labels.max()),
            read_normalize_predict_seconds=seconds,
            scale=args.scale,
        )
        rows.append(result)
        print(json.dumps(result), flush=True)
    report = dict(
        model_load_seconds=load_seconds,
        tensorflow=tf.__version__,
        cpu_only=True,
        intra_threads=4,
        inter_threads=1,
        normalization_percentiles=[3, 99.8],
        rows=rows,
    )
    (args.output / "execution.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
