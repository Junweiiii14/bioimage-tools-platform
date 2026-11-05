"""Explicit real-model engineering regression; does not download or tune anything.

Run with the fixed research Python, --host-python pointing at the desktop env.
All output roots must be new. P014 data are already seen engineering fixtures.
"""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import psutil
from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, name, source, model, timeout=300):
    command = [
        args.host_python,
        "-I",
        "-m",
        "bioimage_app.nuclei_cli",
        "--source",
        str(source),
        "--workspace",
        str(args.output / name),
        "--worker-python",
        args.worker_python,
        "--model-directory",
        str(model),
        "--timeout-seconds",
        str(timeout),
    ]
    before = sha(source)
    started = time.perf_counter()
    observed = {}
    peak = 0
    with (
        (args.output / (name + ".stdout")).open("wb") as stdout,
        (args.output / (name + ".stderr")).open("wb") as stderr,
    ):
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        parent = psutil.Process(process.pid)
        while process.poll() is None:
            total = 0
            try:
                children = parent.children(recursive=True)
            except psutil.NoSuchProcess:
                children = []
            for child in children:
                try:
                    observed[child.pid] = child.create_time()
                    total += child.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
            peak = max(peak, total)
            if time.perf_counter() - started > timeout + 60:
                raise RuntimeError(
                    "Host did not finish after deadline/grace; inspect owned process"
                )
            time.sleep(0.05)
        code = process.wait()
    elapsed = time.perf_counter() - started
    alive = []
    for pid, created in observed.items():
        try:
            if psutil.Process(pid).create_time() == created:
                alive.append(pid)
        except psutil.NoSuchProcess:
            pass
    assert not alive, alive
    assert sha(source) == before
    text = (args.output / (name + ".stdout")).read_text(encoding="utf-8")
    events = [json.loads(line) for line in text.splitlines() if line.startswith("{")]
    final = next((event for event in reversed(events) if event.get("phase") == "finished"), None)
    return {
        "case": name,
        "returncode": code,
        "seconds": elapsed,
        "sampled_descendant_peak_rss": peak,
        "observed_descendants": len(observed),
        "live_descendants_after_exit": alive,
        "original_sha256_unchanged": before,
        "final": final,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-python", required=True)
    parser.add_argument("--worker-python", required=True)
    parser.add_argument("--p014", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    model = args.p014 / "models/2D_versatile_fluo"
    rows = []
    for reference in sorted((args.p014 / "sd-evaluation").glob("*_labels.npy")):
        name = reference.stem.removesuffix("_labels")
        source = args.p014 / "dataset/rawimages" / (name + ".tif")
        with Image.open(source) as image:
            if image.mode != "L":
                continue  # RGB is deliberately outside this interface; no implicit conversion.
        row = run(args, name, source, model)
        assert row["returncode"] == 0, row
        result = np.load(row["final"]["outputs"]["labels"], allow_pickle=False)
        frozen = np.load(reference, allow_pickle=False)
        assert np.array_equal(result, frozen), name
        # Every labeled coordinate and instance ID must match, not only shape/count.
        row.update(
            all_original_coordinate_labels_equal=True,
            shape=list(result.shape),
            count=int(np.count_nonzero(np.unique(result))),
            dtype=str(result.dtype),
            reference_sha256=sha(reference),
        )
        provenance = json.loads(Path(row["final"]["outputs"]["provenance"]).read_text())
        assert provenance["nuclei_count"] == row["count"]
        rows.append(row)
        print(json.dumps({"case": name, "state": "passed", "count": row["count"]}), flush=True)

    blank = args.output / "blank.tif"
    Image.fromarray(np.zeros((128, 192), dtype=np.uint8)).save(blank)
    row = run(args, "valid-empty", blank, model)
    assert row["returncode"] == 0
    labels = np.load(row["final"]["outputs"]["labels"], allow_pickle=False)
    assert not np.any(labels)
    assert json.loads(Path(row["final"]["outputs"]["provenance"]).read_text())["nuclei_count"] == 0
    rows.append(row)

    bad = args.output / "bad-model"
    bad.mkdir()
    (bad / "config.json").write_text("{}")
    for name, chosen, deadline in (
        ("missing-model", args.output / "missing-model-files", 300),
        ("bad-model-digest", bad, 300),
        ("cancel-during-load", model, 1),
    ):
        row = run(args, name, blank, chosen, deadline)
        assert row["returncode"] != 0
        expected = "cancelled" if deadline == 1 else "failed"
        assert row["final"]["state"] == expected, row
        assert row["final"]["outputs"] == {}
        rows.append(row)

    unsupported = args.output / "uint16.tif"
    Image.fromarray(np.zeros((128, 192), dtype=np.uint16)).save(unsupported)
    row = run(args, "reject-uint16", unsupported, model)
    assert row["returncode"] != 0 and row["final"] is None
    assert not (args.output / "reject-uint16").exists()
    rows.append(row)
    report = {
        "scope": "already-seen P014 engineering regression, not scientific admission",
        "sample_interval_seconds": 0.05,
        "rows": rows,
    }
    (args.output / "regression.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps({"cases": len(rows), "report": str(args.output / "regression.json")}), flush=True
    )


if __name__ == "__main__":
    main()
