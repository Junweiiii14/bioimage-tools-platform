"""Export raw target-channel intensity for a committed single-field nuclei result."""

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import numpy as np
from nuclei_tool.api import read_nuclei_input
from platform_runtime.api import WorkspaceError

from bioimage_app.nuclei_intensity import measure_intensity
from bioimage_app.nuclei_results import read_result


def export(workspace: Path, target: Path, parent: Path) -> Path:
    parent = parent.resolve()
    if any((p / "workspace.json").is_file() for p in (parent, *parent.parents)):
        raise ValueError("Choose an export directory outside all managed workspaces")
    result = read_result(str(workspace))
    channel = read_nuclei_input(str(target))
    labels = np.load(io.BytesIO(result.labels), allow_pickle=False)
    columns = ("nucleus_id", "area_px2", "mean_dn", "integrated_dn_px")
    method = "nuclear-raw-intensity@1"
    destination = parent / ("nuclear-intensity-" + uuid4().hex)
    with TemporaryDirectory(dir=parent) as scratch:
        staging = Path(scratch) / "result"
        staging.mkdir()
        with (staging / "per-nucleus.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow((*columns, "run_id", "target_sha256"))
            for row in measure_intensity(labels, channel.pixels):
                writer.writerow((*row, result.run_id, channel.sha256))
        provenance = {
            "method": method,
            "nuclei_count": result.display.count,
            "workspace": str(workspace.resolve()),
            "execution_id": result.execution_id,
            "run_id": result.run_id,
            "source_sha256": result.source_sha256,
            "label_sha256": hashlib.sha256(result.labels).hexdigest(),
            "target_file": target.name,
            "target_sha256": channel.sha256,
            "shape_yx": channel.pixels.shape,
            "pairing": "user_confirmed_same_field_and_pixel_coordinates",
        }
        (staging / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
        staging.rename(destination)
    return destination


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path, help="Committed nuclei project")
    parser.add_argument("--target", required=True, type=Path, help="Original 2D uint8 target TIFF")
    parser.add_argument("--output-dir", required=True, type=Path, help="Existing export parent")
    parser.add_argument(
        "--confirm-same-frame",
        required=True,
        action="store_true",
        help="I verified both channels show the same field in matching pixel coordinates",
    )
    args = parser.parse_args(arguments)
    try:
        print(export(args.workspace, args.target, args.output_dir) / "per-nucleus.csv")
    except (ValueError, OSError, WorkspaceError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
