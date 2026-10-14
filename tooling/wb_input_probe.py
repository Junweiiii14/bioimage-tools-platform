"""Read-only local TIFF acceptance probe; private paths and hashes stay in .local."""

import argparse
import json
from pathlib import Path

from wb_tool.api import LaneROI, compute_lane_profiles, load_tiff


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, default=Path(".local/wb-real-input.json"))
    args = parser.parse_args()
    paths = sorted(
        path for path in args.folder.iterdir() if path.suffix.lower() in (".tif", ".tiff")
    )
    if not paths:
        raise ValueError("No TIFF inputs found")
    results: list[dict[str, object]] = []
    for path in paths:
        image = load_tiff(path)
        height, width = image.pixels.shape
        lane = compute_lane_profiles(
            image.pixels, LaneROI("input-probe", 0, 0, min(width, 10), min(height, 10)), "dark"
        )
        results.append(
            {
                "file": path.name,
                "sha256": image.sha256,
                "shape": [height, width],
                "bit_depth": image.bit_depth,
                "conversion": image.conversion,
                "profile_rows": len(lane.raw),
            }
        )
        del image
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(f"Read-only TIFF input: {len(results)} files passed; private metadata: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
