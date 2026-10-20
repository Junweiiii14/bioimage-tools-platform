"""Read originals only; report per-lane evidence without modifying or injecting results."""

import argparse
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import numpy as np
from wb_tool.api import AutoWBSettings, analyze_annotations, load_tiff, suggest_automatic_wb


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--policy",
        choices=("background_support@1", "anchored_background@1"),
        default="background_support@1",
    )
    args = parser.parse_args()
    if args.destination.exists():
        raise FileExistsError("Keep earlier diagnostic evidence")
    sources = json.loads(args.sources.read_text(encoding="utf-8"))
    assert len(sources) == 8 and all(set(item) == {"path", "sha256"} for item in sources)
    records = []
    for index, item in enumerate(sources, 1):
        path = Path(item["path"])
        assert sha256(path.read_bytes()).hexdigest() == item["sha256"]
        image = load_tiff(path)
        suggestion = suggest_automatic_wb(
            image,
            row_id=f"source-{index}",
            revision=0,
            settings=AutoWBSettings(crop_policy="source_geometry@2", quant_policy=args.policy),
        )
        for request in suggestion.requests:
            result = analyze_annotations(image, request)
            for number, lane in enumerate(result.lanes, 1):
                annotation = request.lanes[number - 1]
                assert lane.profiles is not None
                profile = np.asarray(lane.profiles.quantitative)
                for band in lane.bands:
                    bounds = band.annotation.bounds
                    roi = lane.roi
                    region = image.pixels[
                        roi.y0 + (bounds.left if bounds else 0) : roi.y0
                        + (bounds.right + 1 if bounds else len(profile)),
                        roi.x0 : roi.x1,
                    ]
                    records.append(
                        {
                            "source": index,
                            "file": path.name,
                            "lane": number,
                            "roi": {key: getattr(roi, key) for key in ("x0", "y0", "x1", "y1")},
                            "target_roi": {
                                key: getattr(annotation.target_roi, key)
                                for key in ("x0", "y0", "x1", "y1")
                            }
                            if annotation.target_roi
                            else None,
                            "context_expansion_percent": annotation.context_expansion_percent,
                            "bounds": {"left": bounds.left, "right": bounds.right}
                            if bounds
                            else None,
                            "status": band.status,
                            "flags": list(band.quality_flags),
                            "raw_integral": band.measurement.signal if band.measurement else None,
                            "profile": profile.tolist(),
                            "baseline": {
                                "left": band.annotation.baseline.left_value,
                                "right": band.annotation.baseline.right_value,
                            }
                            if band.annotation.baseline
                            else None,
                            "region_pixels": int(region.size),
                            "zero_pixels": int(np.count_nonzero(region == 0)),
                            "maximum_pixels": int(
                                np.count_nonzero(region == lane.profiles.dtype_max)
                            ),
                        }
                    )
        assert sha256(path.read_bytes()).hexdigest() == item["sha256"]
    counts = Counter(record["status"] for record in records)
    flags = Counter(flag for record in records for flag in record["flags"])
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(
        json.dumps(
            {
                "records": records,
                "statuses": counts,
                "flags": flags,
                "source_hashes_unchanged": True,
                "reference_reads": False,
                "quant_policy": args.policy,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps({"lanes": len(records), "statuses": counts, "flags": flags}, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
