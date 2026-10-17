"""Read source-only manifest; exercise public product APIs, freeze outputs before scoring.

Usage: uv run --locked --no-sync python work/evidence/T-042/run_source_regression.py
    SOURCE_MANIFEST NEW_OUTPUT_DIRECTORY
Manifest entries use path/sha256; references and expected geometry are not accepted.
"""

import json
import sys
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from PIL import Image
from tool_contracts.api import AssetRef
from wb_tool.api import (
    AutoWBSettings,
    FigureRow,
    FigureSourcePath,
    WBFigureProject,
    install_automatic_result,
    load_tiff,
    read_figure_project,
    render_figure,
    suggest_automatic_wb,
)


def main() -> None:
    manifest, output = Path(sys.argv[1]), Path(sys.argv[2])
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    assert isinstance(entries, list) and entries
    assert all(set(entry) == {"path", "sha256"} for entry in entries)
    output.mkdir(parents=True, exist_ok=False)
    predictions = []
    projects = []
    for i, entry in enumerate(entries, 1):
        source = Path(entry["path"])
        image = load_tiff(source)
        assert image.sha256 == entry["sha256"]
        row_id = f"source-{i:02d}"
        result = suggest_automatic_wb(
            image,
            row_id=row_id,
            revision=0,
            settings=AutoWBSettings(
                crop_policy="source_geometry@2",
                quant_policy=sys.argv[3] if len(sys.argv) > 3 else "wbquant_1_4_3@1",
            ),
        )
        predictions.append(
            {"source": str(source), "sha256": image.sha256, "proposal": asdict(result)}
        )
        if not result.requests:
            print(i, "FAILED", result.warnings)
            continue
        project = WBFigureProject(
            project_id=row_id,
            figure_order=("Fig1",),
            rows=(
                FigureRow(
                    row_id=row_id,
                    source=AssetRef(
                        asset_id=row_id,
                        relative_path=f"inputs/{i}.tiff",
                        sha256=image.sha256,
                        size_bytes=source.stat().st_size,
                    ),
                    filename=source.name,
                    width=image.pixels.shape[1],
                    height=image.pixels.shape[0],
                    bit_depth=image.pixels.dtype.itemsize * 8,
                    protein="Unassigned",
                ),
            ),
        )
        installed = install_automatic_result(project, row_id, result)
        encoded = installed.model_dump_json().encode("utf-8")
        restored = read_figure_project(encoded)
        assert restored == installed
        (output / f"{i:02d}-project.json").write_bytes(encoded)
        rendered = render_figure(restored, (FigureSourcePath(image.sha256, str(source)),))
        Image.frombytes("RGB", (rendered.width, rendered.height), rendered.rgb).save(
            output / f"{i:02d}-display.png"
        )
        projects.append(str(output / f"{i:02d}-project.json"))
        print(i, result.estimated_lane_count, "installed, reopened, rendered")
        assert sha256(source.read_bytes()).hexdigest() == image.sha256
    data = json.dumps(predictions, ensure_ascii=False, indent=2).encode("utf-8")
    (output / "predictions.json").write_bytes(data)
    (output / "freeze.json").write_text(
        json.dumps(
            {
                "predictions_sha256": sha256(data).hexdigest(),
                "projects": projects,
                "references_read": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
