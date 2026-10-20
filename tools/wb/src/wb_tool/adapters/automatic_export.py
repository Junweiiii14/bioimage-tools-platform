"""Publish one complete, explicitly provisional output directory without overwriting inputs."""

import json
import os
import shutil
from collections.abc import Callable
from hashlib import file_digest
from pathlib import Path
from uuid import uuid4

from wb_tool.adapters.tiff_input import is_generated_tiff
from wb_tool.application.figure_project import FigureSourcePath, WBFigureProject
from wb_tool.application.import_labels import FolderDiscoveryReport, preferred_acquisition_sources
from wb_tool.application.project_archive import ArchiveRunEvidence


def discover_tiffs(
    path: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
    with_report: bool = False,
) -> bytes:
    root = Path(path)
    if not root.is_dir() or root.is_symlink() or root.is_junction():
        raise ValueError("请选择实际原图文件夹")
    files: list[str] = []
    skipped: list[dict[str, str]] = []
    examined = 0

    def unreadable(error: OSError) -> None:
        raise ValueError(f"无法读取目录：{error.filename}") from error

    for visited, (parent, directories, names) in enumerate(
        os.walk(root, followlinks=False, onerror=unreadable), 1
    ):
        if cancelled():
            raise ValueError("文件夹读取已取消")
        if visited > 4096:
            raise ValueError("目录超过4096个，请选择具体原图文件夹")
        directories[:] = sorted(
            d
            for d in directories
            if not d.startswith(".")
            and not (Path(parent) / d).is_junction()
            and not (Path(parent) / d).is_symlink()
        )
        for name in sorted(names):
            if cancelled():
                raise ValueError("文件夹读取已取消")
            source = Path(parent) / name
            if (
                source.suffix.lower() in (".tif", ".tiff")
                and not source.is_symlink()
                and not source.is_junction()
            ):
                examined += 1
                if examined > 4096:
                    raise ValueError("超过4096个TIFF候选文件，请选择具体原图文件夹")
                if is_generated_tiff(source):
                    skipped.append({"path": str(source), "reason": "generated_display_or_crop"})
                    continue
                files.append(str(source))
                if len(files) > 512:
                    raise ValueError("超过512张TIFF，请分批选择文件夹")
    selected = preferred_acquisition_sources(tuple(files))
    selected_set = set(selected)
    skipped.extend(
        {"path": source, "reason": "numbered_acquisition_variant"}
        for source in files
        if source not in selected_set
    )
    payload = (
        {"policy": "folder_sources@1", "paths": selected, "skipped": skipped}
        if with_report
        else selected
    )
    return json.dumps(payload, ensure_ascii=False).encode()


def export_automatic_results(
    project: WBFigureProject,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    runs: tuple[ArchiveRunEvidence, ...] = (),
    processing_errors: tuple[str, ...] = (),
    discovery_report: bytes = b"",
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    from wb_tool.adapters.figure_export import export_figure_bundle
    from wb_tool.adapters.figure_image_export import export_figure_image
    from wb_tool.adapters.project_evidence import verify_project_evidence
    from wb_tool.adapters.project_export import export_project_table
    from wb_tool.adapters.quant_export import export_wbquant_table
    from wb_tool.application.automatic import row_is_ready
    from wb_tool.application.project_analysis import fill_project_table

    target = Path(destination).absolute()
    if target.exists() or target.is_symlink() or target.is_junction():
        raise FileExistsError("结果目录已存在，请选择新目录")
    if not target.parent.is_dir() or any(
        p.is_symlink() or p.is_junction() for p in (target.parent, *target.parent.parents)
    ):
        raise ValueError("结果父目录无效或经过链接")
    if cancelled():
        raise ValueError("自动输出已取消")
    evidence = verify_project_evidence(project, runs, cancelled=cancelled)
    cells = fill_project_table(project, evidence.results)
    stage = target.parent / (".wb-output-" + uuid4().hex)
    stage.mkdir()
    try:
        export_project_table(
            project, evidence.results, str(stage / "measurements.xlsx"), cancelled=cancelled
        )
        export_project_table(
            project, evidence.results, str(stage / "measurements.csv"), cancelled=cancelled
        )
        if any(
            p.request.quant_policy
            in ("wbquant_1_4_3@1", "background_support@1", "anchored_background@1")
            for p in getattr(project, "analyses", ())
        ):
            export_wbquant_table(
                project, evidence.results, stage / "gray_analysis.xlsx", cancelled=cancelled
            )
            export_wbquant_table(
                project, evidence.results, stage / "gray_analysis.csv", cancelled=cancelled
            )
        ready = [r for r in project.rows if r.roi and row_is_ready(project, r)]
        if ready:
            export_figure_image(project, sources, str(stage / "figure.png"), cancelled=cancelled)
            export_figure_image(project, sources, str(stage / "figure.tif"), cancelled=cancelled)
            export_figure_bundle(
                project, sources, str(stage / "project.zip"), runs=runs, cancelled=cancelled
            )
        (stage / "project.json").write_text(project.model_dump_json(), encoding="utf-8")
        report = {
            "schema_version": 1,
            "purpose": "automatic_results_pending_review",
            "project_id": project.project_id,
            "revision": project.revision,
            "source_count": len(project.rows),
            "rendered_source_count": len(ready),
            "human_reviewed_count": sum(r.reviewed for r in project.rows),
            "processing_errors": list(processing_errors),
            "source_discovery": FolderDiscoveryReport.model_validate_json(
                discovery_report
            ).model_dump(mode="json")
            if discovery_report
            else None,
            "rows": [
                {
                    "row_id": r.row_id,
                    "filename": r.filename,
                    "source_sha256": r.source.sha256 if r.source else None,
                    "lane_count": r.lane_count,
                    "has_crop": r.roi is not None,
                    "human_reviewed": r.reviewed,
                    "notes": r.notes,
                    "lanes": [
                        {
                            "index": c.lane_index,
                            "value": c.value,
                            "raw_integral_pending_review": c.raw_integral,
                            "status": c.status,
                            "reason": c.reason,
                        }
                        for c in cells
                        if c.row_id == r.row_id
                    ],
                }
                for r in project.rows
            ],
            "evidence": evidence.records,
            "limitations": [
                "自动定位与边界尚需复核",
                "未推断蛋白身份或归一化配对",
                "未生成裁剪的原图不会伪装为拼图或零信号",
            ],
        }
        (stage / "status.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (stage / "README.txt").write_text(
            "WB 自动结果（待复核）\n\n"
            "measurements.xlsx / csv：定量与来源状态；空值不是零。\n"
            "figure.png / tif：自动裁剪拼图，仅供展示，不作为定量输入。\n"
            "project.zip：原图、原值裁剪、运行证据与项目，可恢复。\n"
            "status.json：每张原图的处理状态、失败原因与来源。\n"
            "未能识别条带的原图保留在项目中，不进入拼图。全批无有效裁剪时不生成拼图及ZIP。\n"
            "自动估计的泳道、裁剪、边界需图上复核；未自动推断蛋白名、样本或内参。\n",
            encoding="utf-8",
        )
        checksums: dict[str, str] = {}
        for file in sorted(stage.iterdir()):
            if cancelled():
                raise ValueError("自动输出已取消，未发布目录")
            with file.open("rb") as stream:
                checksums[file.name] = file_digest(stream, "sha256").hexdigest()
        (stage / "checksums.json").write_text(json.dumps(checksums, indent=2), encoding="utf-8")
        if cancelled():
            raise ValueError("自动输出已取消，未发布目录")
        if target.exists():
            raise FileExistsError("结果目录已存在")
        os.rename(stage, target)
    finally:
        if stage.is_dir() and stage.resolve().parent == target.parent.resolve():
            shutil.rmtree(stage)
    return str(target)
