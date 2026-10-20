"""E6 disposable baseline probe. Engineering fixtures, never scientific acceptance."""

import argparse
import json
import platform
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ParamSpec, TypeVar
from unittest.mock import patch

import numpy as np
import tifffile
from pydantic import TypeAdapter
from tool_contracts.api import AssetRef
from wb_tool.adapters import crop_export, figure_export, laboratory_figure, tiff_input
from wb_tool.adapters.automatic_export import export_automatic_results
from wb_tool.adapters.intake_output import export_intake_outputs
from wb_tool.api import (
    FigureRow,
    FigureSourcePath,
    FigureTemplate,
    LaneROI,
    WBFigureProject,
    plan_figure_layout,
)
from wb_tool.application.intake_output import WBIntakeOutputProject

from tooling.p0.metrics import peak_memory, summary
from tools.wb.tests.test_intake_output import full_files

P = ParamSpec("P")
R = TypeVar("R")


def one(mode: str) -> dict[str, int | float]:
    with TemporaryDirectory(prefix="wb-e6-perf-") as folder:
        root = Path(folder)
        project: WBFigureProject
        if mode == "intake":
            project, paths, runs = full_files(root)
        else:
            source_paths: list[FigureSourcePath] = []
            rows: list[FigureRow] = []
            for i in range(2):
                path = root / f"synthetic-{i}.tif"
                pixels = np.full((1024, 2048), 50000 + i, dtype=np.uint16)
                pixels[300:400, 100:1900:2] = 12000 + i
                tifffile.imwrite(path, pixels)
                image = tiff_input.load_tiff(path)
                source_paths.append(FigureSourcePath(image.sha256, str(path)))
                rows.append(
                    FigureRow(
                        row_id=f"r{i}",
                        source=AssetRef(
                            asset_id=f"s{i}",
                            relative_path=f"assets/{i}.tif",
                            sha256=image.sha256,
                            size_bytes=path.stat().st_size,
                        ),
                        filename=path.name,
                        width=2048,
                        height=1024,
                        bit_depth=16,
                        figure="Fig1",
                        protein="AKT",
                        lane_count=8,
                        roi=LaneROI(f"r{i}", 0, 100, 2048, 800),
                        reviewed=True,
                    )
                )
            project = WBFigureProject(
                project_id="engineering",
                rows=tuple(rows),
                figure_order=("Fig1",),
                template=FigureTemplate(crop_height=700, font_size=14),
            )
            paths, runs = tuple(source_paths), ()
        counts = {"original_decode": 0, "layout_render": 0}

        def counted(fn: Callable[P, R], key: str) -> Callable[P, R]:
            def call(*args: P.args, **kwargs: P.kwargs) -> R:
                counts[key] += 1
                return fn(*args, **kwargs)

            return call

        # Each alias is an actual call site; no decoding is bypassed or cached here.
        patches = [
            patch.object(module, "load_tiff", counted(module.load_tiff, "original_decode"))
            for module in (crop_export, figure_export, laboratory_figure, tiff_input)
        ]
        patches += [
            patch.object(
                laboratory_figure,
                "render_laboratory_figure",
                counted(laboratory_figure.render_laboratory_figure, "layout_render"),
            ),
            patch.object(
                figure_export,
                "plan_figure_layout",
                counted(plan_figure_layout, "layout_render"),
            ),
        ]
        for item in patches:
            item.start()
        started = time.perf_counter()
        try:
            if mode == "intake":
                assert isinstance(project, WBIntakeOutputProject)
                prepared = export_intake_outputs(project, paths, str(root / "output"), runs=runs)
                assert prepared.complete
            else:
                export_automatic_results(project, paths, str(root / "output"))
        finally:
            elapsed = time.perf_counter() - started
            for item in reversed(patches):
                item.stop()
        return {
            "seconds": elapsed,
            "peak_rss_bytes": peak_memory(),
            "output_bytes": sum(
                p.stat().st_size for p in (root / "output").rglob("*") if p.is_file()
            ),
            **counts,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", choices=("legacy", "intake"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--n", type=int, default=20)
    args = parser.parse_args()
    if args.sample:
        print(json.dumps(one(args.sample)))
    else:
        modes: dict[str, object] = {}
        data: dict[str, object] = {
            "environment": platform.platform(),
            "python": sys.version,
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "limitations": (
                "Synthetic engineering corpus; fixture setup outside export timing; "
                "fresh process per sample; OS caches not flushed; not GUI/scientific acceptance"
            ),
            "modes": modes,
        }
        for mode in ("legacy", "intake"):
            samples: list[dict[str, int | float]] = []
            for i in range(args.n):
                result = subprocess.run(
                    [sys.executable, "-m", "tools.wb.tests.benchmark_exports", "--sample", mode],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                samples.append(TypeAdapter(dict[str, int | float]).validate_json(result.stdout))
                print(mode, i + 1, flush=True)
            modes[mode] = {
                "samples": samples,
                "seconds": summary([s["seconds"] for s in samples]),
                "peak_rss_bytes": summary([s["peak_rss_bytes"] for s in samples]),
            }
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
