"""Local-only review atlas: python -m wb_tool.discovery --root ... --output NEW_DIR."""

import argparse
import html
import json
import re
from hashlib import sha256
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image, ImageDraw
from tool_contracts.api import AssetRef

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.api import (
    AutoWBSettings,
    FigureSourcePath,
    IntakeSource,
    WBFigureProject,
    create_intake,
    detect_automatic_geometry,
    discover_exports,
    install_export_discovery,
    intake_digest,
    register_intake_source,
)
from wb_tool.application.intake_grouping import acquisition_key as export_group


def build_atlas(
    roots: list[Path], destination: Path, *, include_baseline: bool = False
) -> dict[str, object]:
    """Write a unique private review report. No automatic labels, no overwrites."""
    paths = sorted(
        {
            p.resolve()
            for root in roots
            for p in root.rglob("*")
            if p.is_file() and p.suffix.casefold() in {".tif", ".tiff"}
        }
    )
    if not paths or len(paths) > 512:
        raise ValueError("请选择包含1–512张TIFF的目录")
    target = destination.resolve()
    if any(target == r.resolve() or target.is_relative_to(r.resolve()) for r in roots):
        raise ValueError("报告目录必须位于原始输入目录之外")
    target.mkdir(parents=True, exist_ok=False)
    project = create_intake(WBFigureProject(project_id="local-export-review"))
    mappings: list[FigureSourcePath] = []
    originals: dict[str, str] = {}
    for i, path in enumerate(paths):
        image = load_tiff(path)
        root = next(r.resolve() for r in roots if path.is_relative_to(r.resolve()))
        root_index = next(i for i, r in enumerate(roots) if r.resolve() == root)
        relative = f"batch-{root_index + 1}/{path.relative_to(root).as_posix()}"
        source = IntakeSource(
            source_id=f"image-{i:03}",
            asset=AssetRef(
                asset_id=f"image-{i:03}",
                relative_path=f"assets/{i}.tiff",
                sha256=image.sha256,
                size_bytes=path.stat().st_size,
            ),
            original_name=path.name,
            relative_path=relative,
            width=image.pixels.shape[1],
            height=image.pixels.shape[0],
            bit_depth=16 if image.bit_depth == 16 else 8,
        )
        project = register_intake_source(project, source, expected_digest=intake_digest(project))
        mappings.append(FigureSourcePath(image.sha256, str(path)))
        originals[source.source_id] = str(path)
    started = perf_counter()
    report = discover_exports(project, tuple(mappings))
    seconds = perf_counter() - started
    project = install_export_discovery(project, report, expected_digest=intake_digest(project))
    # Freeze whole acquisition groups and corresponding reference into one split.
    # All labels are currently unverified; this is a prospective split, not accuracy.
    cohorts: dict[str, str] = {}
    for source in project.intake.sources:
        stem = re.split(r"_\d{6}", Path(source.original_name).stem)[0]
        key = str(Path(source.relative_path).parent / stem)
        cohorts[source.source_id] = key
    # Exact duplicate content cannot straddle the split, including renamed copies.
    leaders = {key: key for key in cohorts.values()}

    def leader(key: str) -> str:
        while leaders[key] != key:
            key = leaders[key]
        return key

    seen: dict[str, str] = {}
    for source in project.intake.sources:
        key = leader(cohorts[source.source_id])
        if source.asset.sha256 in seen:
            leaders[key] = leader(seen[source.asset.sha256])
        else:
            seen[source.asset.sha256] = key
    groups = sorted(
        {leader(key) for key in cohorts.values()}, key=lambda k: sha256(k.encode()).hexdigest()
    )
    holdout = set(groups[: max(1, len(groups) // 3)])
    cards: list[str] = []
    baseline: list[dict[str, object]] = []
    dataset: list[dict[str, object]] = []
    baseline_located = 0
    roles = {
        "signal": "信号图候选",
        "white": "白光图候选",
        "merge": "合并图候选",
        "reference": "人工结果候选·未核验",
        "unknown": "角色待确认",
    }
    for observation, source in zip(report.observations, project.intake.sources, strict=True):
        path = Path(originals[source.source_id])
        image = load_tiff(path)
        raw = image.pixels
        if image.sha256 != source.asset.sha256:
            raise ValueError("报告期间来源发生变化")
        split = "holdout" if leader(cohorts[source.source_id]) in holdout else "development"
        dataset.append(
            {
                "source_id": source.source_id,
                "path": str(path),
                "sha256": image.sha256,
                "group": export_group(source.relative_path),
                "cohort": leader(cohorts[source.source_id]),
                "split": split,
                "label_status": "unverified",
                "n": None,
                "target": None,
                "source_shape": image.source_shape,
                "conversion": image.conversion,
            }
        )
        lo, hi = np.percentile(raw, [0.1, 99.9])
        preview = np.clip((raw.astype(float) - lo) * 255 / max(float(hi - lo), 1), 0, 255).astype(
            "uint8"
        )
        raster = Image.fromarray(preview).convert("RGB")
        raster.thumbnail((540, 360))
        sx, sy = raster.width / source.width, raster.height / source.height
        draw = ImageDraw.Draw(raster)
        for j, region in enumerate(observation.regions):
            draw.rectangle(
                (region.x0 * sx, region.y0 * sy, region.x1 * sx, region.y1 * sy),
                outline="#c73519",
                width=2,
            )
            draw.text((region.x0 * sx, max(0, region.y0 * sy - 12)), str(j + 1), fill="#c73519")
        filename = f"{source.source_id}.png"
        raster.save(target / filename)
        details: list[str] = []
        for j, region in enumerate(observation.regions):
            crop = Image.fromarray(preview[region.y0 : region.y1, region.x0 : region.x1]).convert(
                "RGB"
            )
            crop.thumbnail((540, 180))
            cropfile = f"{source.source_id}-region-{j}.png"
            crop.save(target / cropfile)
            details.append(
                f'<figure><img src="{cropfile}" alt="候选条带放大"><figcaption>候选{j + 1}'
                f" · N建议 {region.lane_counts} · 倾斜 {region.angle_degrees:.1f}°"
                " · 未确认</figcaption></figure>"
            )
        if observation.role == "signal" and include_baseline:
            before = perf_counter()
            old = detect_automatic_geometry(raw, AutoWBSettings(crop_policy="source_geometry@2"))
            baseline_located += bool(old.candidates)
            baseline.append(
                {
                    "source_id": source.source_id,
                    "seconds": perf_counter() - before,
                    "candidates": len(old.candidates),
                    "flags": old.flags,
                    "n_candidate": old.settings.lane_count if old.candidates else None,
                }
            )
        cards.append(
            f"<article><h2>{source.source_id} · {html.escape(source.relative_path)}</h2>"
            f"<p>{roles[observation.role]} · {source.width}×{source.height}"
            f" · {source.bit_depth}bit · {split}</p>"
            f'<img src="{filename}" alt="原图显示预览与候选框">'
            f"<p>{html.escape('；'.join(observation.reasons))}</p>"
            f"{''.join(details)}<p>确认项：来源角色 / 目标候选编号 / N / 参考是否有效</p></article>"
        )
    result: dict[str, object] = {
        "schema_version": 1,
        "algorithm": report.algorithm,
        "seconds": seconds,
        "images": len(paths),
        "observations": report.model_dump(mode="json"),
        "dataset": dataset,
        "baseline": baseline,
        "baseline_ran": include_baseline,
        "accuracy": None,
        "note": (
            "全部科学标签未确认；划分仅作后续冻结，不声称独立留出准确率。当前图册已显示所有图。"
        ),
    }
    (target / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (target / "intake-project.json").write_text(project.model_dump_json(indent=2), encoding="utf-8")
    (target / "index.html").write_text(
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>仪器原图集中核对</title>'
        "<style>body{font:16px system-ui;background:#f4f3ef;color:#242925;margin:28px}"
        "main{display:grid;grid-template-columns:repeat(auto-fit,minmax(540px,1fr));gap:20px}"
        "article{background:white;padding:20px;border:1px solid #ccc}h1{font-size:28px}"
        "h2{font-size:16px;overflow-wrap:anywhere}img{max-width:100%;height:auto}"
        "figure{margin:12px 0}p,figcaption{line-height:1.5}</style>"
        "<h1>仪器原图与裁剪候选 · 集中核对</h1><p>红框仅为机器建议；N和目标尚未确认。"
        "图片仅作显示，定量仍取原始像素。请按编号集中反馈，不将人工成品直接作为真值。</p>"
        f"<p>{len(paths)}张图片 · 尚无可靠科学标签，准确率未评估。</p>"
        f"<main>{''.join(cards)}</main></html>",
        encoding="utf-8",
    )
    return {
        "images": len(paths),
        "signal_candidates": sum(r.role == "signal" for r in report.observations),
        "regions": sum(len(r.regions) for r in report.observations),
        "seconds": seconds,
        "baseline_located": baseline_located if include_baseline else None,
        "output": str(target),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", action="store_true", help="首次记录旧算法基线，后续不重复")
    args = parser.parse_args()
    print(
        json.dumps(
            build_atlas(args.root, args.output, include_baseline=args.baseline), ensure_ascii=True
        )
    )


if __name__ == "__main__":
    main()
