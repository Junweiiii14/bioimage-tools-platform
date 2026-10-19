"""Publish an intake snapshot into a new root; verify bytes before declaring completeness."""

import json
import os
import shutil
from collections.abc import Callable
from dataclasses import asdict, replace
from hashlib import file_digest, sha256
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from tool_contracts.api import AssetRef

from wb_tool.application.figure_project import FigureRender, FigureSourcePath
from wb_tool.application.instrument_intake import intake_digest
from wb_tool.application.intake_execution import build_intake_execution_plan
from wb_tool.application.intake_figure import intake_figure_projection
from wb_tool.application.intake_output import (
    IntakeOutputPreparation,
    WBIntakeOutputProject,
    fill_intake_table,
    intake_output_digest,
)
from wb_tool.application.intake_workflow import (
    IntakeWorkflowTicket,
    validate_intake_workflow_ticket,
)
from wb_tool.application.laboratory_layout import plan_laboratory_layout
from wb_tool.application.project_archive import ArchiveRunEvidence, project_runs
from wb_tool.application.project_restore import project_assets


def _copy(source: str, target: Path, asset: AssetRef, cancelled: Callable[[], bool]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    digest, count = sha256(), 0
    created = False
    try:
        with Path(source).open("rb") as incoming, target.open("xb") as outgoing:
            created = True
            while chunk := incoming.read(1024 * 1024):
                if cancelled():
                    raise ValueError("结果输出已取消")
                count += len(chunk)
                if count > asset.size_bytes:
                    raise ValueError("来源文件字节数改变")
                digest.update(chunk)
                outgoing.write(chunk)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        if (count, digest.hexdigest()) != (asset.size_bytes, asset.sha256):
            raise ValueError("来源文件字节数或SHA256改变")
        with target.open("rb") as stored:
            if file_digest(stored, "sha256").hexdigest() != asset.sha256:
                raise ValueError("复制资产写后核验失败")
    except (OSError, ValueError):
        # Only the caller's new staging target can be removed here.
        if created:
            target.unlink(missing_ok=True)
        raise


def _publish(stage: Path, target: Path, check: Callable[[], None]) -> None:
    if os.name == "nt":
        os.rename(stage, target)
        return
    # POSIX rename can replace an existing empty directory. Reserve exclusively instead.
    target.mkdir()
    marker = target / ".incomplete-output"
    marker.write_text("输出发布未完成；请保留原项目并重新导出到新目录。", encoding="utf-8")
    try:
        for source in stage.iterdir():
            check()
            os.rename(source, target / source.name)
        marker.unlink()
    except (OSError, ValueError) as error:
        raise ValueError(f"输出发布未完成：{target}；未完成标记保留。{error}") from error


def _freeze_runs(
    project: WBIntakeOutputProject,
    supplied: tuple[ArchiveRunEvidence, ...],
    stage: Path,
    cancelled: Callable[[], bool],
) -> tuple[ArchiveRunEvidence, ...]:
    entries = {entry.run.run_id: entry for entry in supplied}
    expected = project_runs(project)
    if len(entries) != len(supplied) or set(entries) - {run.run_id for run in expected}:
        raise ValueError("输出运行证据重复或不属于当前项目")
    frozen: list[ArchiveRunEvidence] = []
    result_bytes = 0
    for index, run in enumerate(expected, 1):
        directory = stage / "runs" / f"{index:04d}"
        directory.mkdir(parents=True)
        (directory / "run.json").write_bytes(run.model_dump_json().encode())
        entry = entries.get(run.run_id)
        try:
            if entry is None or entry.run != run or entry.error or not entry.request_path:
                raise ValueError(entry.error if entry and entry.error else "未提供匹配的运行证据")
            if run.request.size_bytes > 16 * 1024 * 1024:
                raise ValueError("冻结请求超过16MiB预算")
            request = directory / "request.json"
            _copy(entry.request_path, request, run.request, cancelled)
            result = directory / "result.json"
            if run.result is not None:
                if not entry.result_path or run.result.size_bytes > 8 * 1024 * 1024:
                    raise ValueError("结果路径缺失或超过8MiB预算")
                result_bytes += run.result.size_bytes
                if result_bytes > 64 * 1024 * 1024:
                    raise ValueError("累计结果超过64MiB预算")
                _copy(entry.result_path, result, run.result, cancelled)
            frozen.append(ArchiveRunEvidence(run, str(request), str(result) if run.result else ""))
        except (OSError, ValueError) as error:
            if cancelled():
                raise ValueError("结果输出已取消") from error
            frozen.append(ArchiveRunEvidence(run, error=str(error)))
    return tuple(frozen)


def export_intake_outputs(
    project: WBIntakeOutputProject,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    runs: tuple[ArchiveRunEvidence, ...] = (),
    ticket: IntakeWorkflowTicket | None = None,
    cancelled: Callable[[], bool] = lambda: False,
) -> IntakeOutputPreparation:
    from wb_tool.adapters.figure_export import export_figure_bundle, render_figure
    from wb_tool.adapters.figure_image_export import publish_rendered_image
    from wb_tool.adapters.laboratory_figure import render_display_segment
    from wb_tool.adapters.project_evidence import verify_project_evidence
    from wb_tool.adapters.project_export import project_csv_bytes, project_xlsx_bytes
    from wb_tool.adapters.tiff_input import load_tiff
    from wb_tool.adapters.worksheet_export import publish_table_bytes

    project = type(project).model_validate(dict(project))
    if ticket is not None:
        validate_intake_workflow_ticket(project, ticket)
        if ticket.stage != "export":
            raise ValueError("输出需要当前export票据")
    elif any(step.status == "running" for step in project.workflow.steps):
        raise ValueError("活动阶段不能发布其他快照")

    def check() -> None:
        if (ticket is not None and project.workflow.cancel_requested) or cancelled():
            raise ValueError("结果输出已取消，未发布目录")

    check()
    target = Path(destination).absolute()
    if target.exists() or target.is_symlink() or target.is_junction():
        raise FileExistsError("结果目录已存在，请选择新目录")
    parent = target.parent
    if not parent.is_dir() or any(
        p.is_symlink() or p.is_junction() for p in (parent, *parent.parents)
    ):
        raise ValueError("结果父目录无效或经过链接")
    paths = {item.sha256: item.path for item in sources}
    if len(paths) != len(sources):
        raise ValueError("输出来源摘要路径重复")
    plan = build_intake_execution_plan(project, expected_digest=intake_digest(project))
    if sum(asset.size_bytes for asset in project_assets(project)) > 2 * 1024**3:
        raise ValueError("复制资产超过2GiB预算，请分批或保留原归档")
    output_id = uuid4().hex
    stage = parent / (".wb-intake-output-" + output_id)
    stage.mkdir()
    errors: list[str] = []
    frozen_paths: dict[str, str] = {}
    try:
        # Freeze verified copies once; later rendering never races the external paths.
        for asset in project_assets(project):
            check()
            try:
                if asset.sha256 not in paths:
                    raise ValueError("缺少资产路径")
                _copy(paths[asset.sha256], stage / "assets" / asset.sha256, asset, cancelled)
                copied = stage / "assets" / asset.sha256
                with copied.open("rb") as stream:
                    header = stream.read(8)
                # Reader extensions describe verified container bytes, never experiment identity.
                suffix = (
                    ".tiff"
                    if header[:4] in {b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"}
                    else ".png"
                    if header == b"\x89PNG\r\n\x1a\n"
                    else ".bin"
                )
                typed_path = copied.with_suffix(suffix)
                copied.rename(typed_path)
                frozen_paths[asset.sha256] = str(typed_path)
            except (OSError, ValueError) as error:
                check()
                errors.append(f"资产{asset.sha256}：{error}")
        frozen_sources = tuple(
            FigureSourcePath(digest, path) for digest, path in frozen_paths.items()
        )
        frozen_runs = _freeze_runs(project, runs, stage, cancelled)
        verified = verify_project_evidence(project, frozen_runs, cancelled=cancelled)
        errors.extend(
            f"运行{record['run_id']}：{record['reason']}"
            for record in verified.records
            if record["verification"] == "unavailable"
        )
        for suffix, data in (
            (".csv", project_csv_bytes(project, verified.results)),
            (".xlsx", project_xlsx_bytes(project, verified.results)),
        ):
            path = publish_table_bytes(
                data, stage / ("measurements" + suffix), suffix, cancelled=cancelled
            )
            if path.read_bytes() != data:
                raise ValueError("结果表写后核验失败")
        crops = {item.row_id: item for item in project.intake_crops}
        figures = {item.figure_id: item for item in project.intake_figures}
        for figure in plan.figures:
            check()
            evidence = figures.get(figure.figure_id)
            if evidence is not None:
                try:
                    image = stage / figure.image_path
                    image.parent.mkdir(parents=True, exist_ok=True)
                    _copy(
                        frozen_paths[evidence.image.sha256],
                        image.with_suffix(".png"),
                        evidence.image,
                        cancelled,
                    )
                    projection = intake_figure_projection(project, figure.figure_id)
                    rendered = render_figure(projection, frozen_sources, cancelled=cancelled)
                    publish_rendered_image(
                        rendered, project.template.dpi, str(image), cancelled=cancelled
                    )
                except (KeyError, OSError, ValueError) as error:
                    check()
                    errors.append(f"Fig {figure.figure_id}：{error}")
            for row in figure.rows:
                check()
                crop = crops.get(row.row_id)
                if crop is None or crop.raw_crop is None:
                    continue
                try:
                    _copy(
                        frozen_paths[crop.raw_crop.sha256],
                        stage / row.raw_crop_path,
                        crop.raw_crop,
                        cancelled,
                    )
                    # Preserve each manual segment and its original-coordinate provenance.
                    projection = intake_figure_projection(project, figure.figure_id)
                    layout = plan_laboratory_layout(projection)
                    original = load_tiff(frozen_paths[row.source.asset.sha256])
                    segments = [
                        s
                        for line in layout.lines
                        for s in line.segments
                        if s.row.row_id == row.row_id
                    ]
                    for index, segment in enumerate(segments, 1):
                        x0, y0, x1, y1 = segment.output_box
                        width, height = x1 - x0, y1 - y0
                        record: dict[str, object] = {
                            "operation": "intake_display_crop@1",
                            "purpose": "display_only_not_quantitative",
                            "project_id": project.project_id,
                            "revision": project.revision,
                            "figure_id": figure.figure_id,
                            "row_id": row.row_id,
                            "source_sha256": row.source.asset.sha256,
                            "first_lane": segment.segment.first_lane,
                            "last_lane": segment.segment.last_lane,
                        }
                        pixels = render_display_segment(
                            original,
                            replace(segment, output_box=(0, 0, width, height)),
                            record,
                            resample=projection.layout_style.display_policy
                            == "standard_lane_ratio@1",
                        )
                        name = Path(row.display_crop_path)
                        if len(segments) > 1:
                            name = name.with_stem(name.stem + f"-{index:02d}")
                        publish_rendered_image(
                            FigureRender(width, height, pixels.tobytes(), json.dumps(record)),
                            project.template.dpi,
                            str(stage / name),
                            cancelled=cancelled,
                        )
                except (KeyError, OSError, ValueError) as error:
                    check()
                    errors.append(f"蛋白行{row.row_id}：{error}")
        if all(asset.sha256 in frozen_paths for asset in project_assets(project)):
            try:
                export_figure_bundle(
                    project,
                    frozen_sources,
                    str(stage / "project.zip"),
                    runs=frozen_runs,
                    cancelled=cancelled,
                )
                with (
                    ZipFile(stage / "project.zip") as archive,
                    archive.open("archive.json") as stream,
                ):
                    data = stream.read(16 * 1024 * 1024 + 1)
                if len(data) > 16 * 1024 * 1024:
                    raise ValueError("归档索引超过16MiB预算")
                if json.loads(data).get("runs") != list(verified.records):
                    raise ValueError("归档运行证据在发布前改变，不能宣布完整输出")
            except (OSError, ValueError) as error:
                check()
                state = (
                    "归档未通过完整核验"
                    if (stage / "project.zip").is_file()
                    else "可恢复归档未生成"
                )
                errors.append(f"{state}：{error}")
        else:
            errors.append("原资产缺项，可恢复归档未生成；已有工作区与结果保持")
        unfinished = [
            s for s in project.workflow.steps if s.stage != "export" and s.status != "done"
        ]
        if unfinished:
            errors.append(f"尚有{len(unfinished)}个阶段未完成；本目录为部分输出")
        (stage / "project.json").write_bytes(project.model_dump_json().encode())
        (stage / "intake.json").write_bytes(project.intake.model_dump_json().encode())
        status = {
            "policy": "intake_table@1",
            "cells": [asdict(item) for item in fill_intake_table(project, verified.results)],
            "stages": project.workflow.model_dump(mode="json"),
            "errors": errors,
            "evidence": verified.records,
        }
        (stage / "status.json").write_text(
            json.dumps(status, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
        (stage / "README.txt").write_text(
            "仪器清单结果快照\nCSV/XLSX按稳定Fig/蛋白行/槽位身份填表；空值不是零。\n"
            "assets保留原资产字节；显示PNG/TIFF不作为定量输入。\n"
            "完整恢复使用project.zip；如该文件缺失，请查看status.json，不代表完整输出成功。\n"
            "运行、科学质量与实验对应分别核对；未自动推断归一化。\n",
            encoding="utf-8",
        )
        members: list[dict[str, object]] = []
        for path in sorted(stage.rglob("*")):
            check()
            if path.is_file():
                with path.open("rb") as stream:
                    digest = file_digest(stream, "sha256").hexdigest()
                members.append(
                    {
                        "path": path.relative_to(stage).as_posix(),
                        "sha256": digest,
                        "size_bytes": path.stat().st_size,
                    }
                )
        index = {
            "policy": "intake_output@1",
            "output_id": output_id,
            "project_id": project.project_id,
            "revision": project.revision,
            "input_digest": intake_output_digest(project),
            "complete": not errors,
            "errors": errors,
            "members": members,
        }
        data = json.dumps(index, ensure_ascii=False, allow_nan=False).encode()
        if len(data) > 16 * 1024 * 1024:
            raise ValueError("输出索引超过16MiB预算")
        with (stage / "index.json").open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        prepared = IntakeOutputPreparation(
            output_id=output_id,
            project_id=project.project_id,
            revision=project.revision,
            input_digest=intake_output_digest(project),
            destination=str(target),
            path=str(target / "index.json"),
            sha256=sha256(data).hexdigest(),
            size_bytes=len(data),
            complete=not errors,
            errors=tuple(errors),
        )
        check()
        if target.exists():
            raise FileExistsError("结果目录已存在")
        _publish(stage, target, check)
        return prepared
    finally:
        if stage.is_dir() and not stage.is_symlink() and stage.resolve().parent == parent.resolve():
            shutil.rmtree(stage)
