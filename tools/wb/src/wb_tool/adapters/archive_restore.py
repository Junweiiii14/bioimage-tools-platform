"""Validate a portable project before exposing a plan for host-owned asset import."""

import json
import os
import struct
import zlib
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile

import numpy as np
import tifffile
from PIL import Image
from pydantic import Field
from tool_contracts.api import RunRecord

from wb_tool.adapters.archive_reader import (
    MAX_MEMBER,
    ArchiveEntry,
    check_cancel,
    preflight_zip,
    read_archive,
    snapshot_archive,
)
from wb_tool.adapters.crop_export import export_crop
from wb_tool.adapters.csv_export import CSV_ENCODING
from wb_tool.adapters.figure_export import render_figure
from wb_tool.adapters.normalization_export import normalization_csv_bytes, normalization_table_rows
from wb_tool.adapters.ocr_input import load_ocr_image
from wb_tool.adapters.project_evidence import VerifiedProjectEvidence, verify_project_evidence
from wb_tool.adapters.project_export import project_csv_bytes, project_xlsx_bytes
from wb_tool.adapters.project_ocr_export import project_ocr_csv_bytes, project_ocr_table_rows
from wb_tool.adapters.worksheet_export import two_sheet_xlsx_bytes
from wb_tool.application.crop import CropRequest
from wb_tool.application.crop_suggestions import read_figure_project
from wb_tool.application.document import DocumentIO, check_document_json
from wb_tool.application.figure_project import FigureSourcePath, WBFigureProject
from wb_tool.application.project_archive import ArchiveRunEvidence, project_runs
from wb_tool.application.project_normalization import WBNormalizedProject
from wb_tool.application.project_ocr import WBProjectOCR
from wb_tool.application.project_restore import (
    StagedArchiveAsset,
    StagedArchiveRun,
    StagedProjectArchive,
    WBRestoredProject,
    project_assets,
)


class MemberIndex(DocumentIO):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    role: str


class RunIndex(DocumentIO):
    run_id: str
    state: str
    record: str
    request: str | None
    result: str | None
    verification: Literal["unavailable", "verified_result", "terminal_without_result"]
    reason: str = Field(max_length=4000)


class ProjectArchiveIndex(DocumentIO):
    format: Literal["wb_project_archive"]
    schema_version: Literal[2]
    project_id: str
    revision: int = Field(ge=0)
    csv_encoding: Literal["wb_csv_text_prefix@1"]
    runs: tuple[RunIndex, ...] = Field(max_length=4096)
    ocr: Literal["present", "not_configured"]
    normalization: Literal["configured", "not_configured"]
    trust: Literal["portable_evidence_not_local_execution_receipt"]
    members: tuple[MemberIndex, ...] = Field(max_length=4095)


def _json(path: Path) -> object:
    data = path.read_bytes()
    check_document_json(data)
    return json.loads(data)


def _role(name: str, project: WBFigureProject) -> str:
    fixed = {
        "figure.png": "display_figure",
        "manifest.json": "figure_provenance",
        "project.json": "saved_project",
        "README.txt": "archive_instructions",
    }
    if name in fixed:
        return fixed[name]
    if name.startswith("assets/"):
        history = isinstance(project, WBRestoredProject) and any(
            s.archive.sha256 == name.removeprefix("assets/") for s in project.archive_sources
        )
        return "historical_archive" if history else "source_asset"
    if name.startswith("crops/"):
        return "original_sample_crop"
    if name.startswith("runs/"):
        return {
            "run.json": "declared_run_record",
            "request.json": "frozen_project_request",
            "result.json": "original_result_asset",
        }.get(name.rsplit("/", 1)[-1], "")
    if name.startswith("tables/"):
        kind = name.rsplit(".", 1)[-1]
        if name.startswith("tables/normalization"):
            return "normalization_" + kind
        return ("source_result_" if name.startswith("tables/source") else "ocr_result_") + kind
    return ""


def _rename(entry: ArchiveEntry, suffix: str) -> Path:
    target = entry.path.with_suffix(suffix)
    # Only our generated file in our staging directory; never an archive path.
    if target.exists():
        raise ValueError("恢复暂存路径冲突")
    os.rename(entry.path, target)
    return target


def _tiff_budget(path: Path) -> None:
    with tifffile.TiffFile(path) as image:
        if len(image.pages) != 1:
            raise ValueError("恢复TIFF须单页")
        page = image.pages[0]
        if not isinstance(page, tifffile.TiffPage) or page.nbytes > MAX_MEMBER:
            raise ValueError("恢复TIFF解码超出512MiB预算")
        if page.imagewidth * page.imagelength > 32_000_000:
            raise ValueError("恢复TIFF超出3200万像素预算")


def _assets(project: WBFigureProject, entries: dict[str, ArchiveEntry]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    originals = {row.source.sha256 for row in project.rows if row.source}
    historical: set[str] = (
        {s.archive.sha256 for s in project.archive_sources}
        if isinstance(project, WBRestoredProject)
        else set()
    )
    for asset in project_assets(project):
        name = "assets/" + asset.sha256
        entry = entries.get(name)
        if entry is None or (entry.sha256, entry.size_bytes) != (asset.sha256, asset.size_bytes):
            raise ValueError("项目资产缺失或大小/摘要不一致")
        if asset.sha256 not in historical and entry.size_bytes > MAX_MEMBER:
            raise ValueError("普通来源资产超出512MiB预算")
        suffix = ".json"
        if asset.sha256 in originals:
            suffix = ".tif"
        elif project.template.font and asset.sha256 == project.template.font.sha256:
            suffix = ".ttf"
        elif (
            isinstance(project, WBProjectOCR)
            and project.ocr
            and asset.sha256 == project.ocr.source.sha256
        ):
            with entry.path.open("rb") as file:
                suffix = ".png" if file.read(8) == b"\x89PNG\r\n\x1a\n" else ".tif"
        elif asset.sha256 in historical:
            suffix = ".zip"
        path = _rename(entry, suffix)
        paths[asset.sha256] = path
        if suffix == ".tif":
            _tiff_budget(path)
    if isinstance(project, WBProjectOCR) and project.ocr:
        image = load_ocr_image(paths[project.ocr.source.sha256])
        if image.pixels.shape != (project.ocr.height, project.ocr.width):
            raise ValueError("OCR原图尺寸与项目不同")
    return paths


def _verify_images(
    project: WBFigureProject,
    entries: dict[str, ArchiveEntry],
    paths: dict[str, Path],
    staging: Path,
    cancelled: Callable[[], bool],
) -> None:
    sources = tuple(FigureSourcePath(digest, str(path)) for digest, path in paths.items())
    rendered = render_figure(project, sources, cancelled=cancelled)
    expected = json.loads(rendered.manifest_json)
    if _json(entries["manifest.json"].path) != expected:
        raise ValueError("拼图来源记录与原项目/原图不一致")
    with Image.open(entries["figure.png"].path, formats=("PNG",)) as image:
        if image.size != (rendered.width, rendered.height) or image.mode != "RGB":
            raise ValueError("拼图图像尺寸或模式不一致")
        if (
            image.tobytes() != rendered.rgb
            or image.info.get("wb_provenance") != rendered.manifest_json
        ):
            raise ValueError("拼图显示像素或嵌入来源记录不一致")
    for index, row in enumerate(project.rows, 1):
        check_cancel(cancelled)
        if row.source is None or row.roi is None:
            continue
        saved = entries[f"crops/{index:04d}.tif"].path
        _tiff_budget(saved)
        expected_crop = staging / f"verified-crop-{index:04d}.tif"
        export_crop(
            str(paths[row.source.sha256]),
            CropRequest(row.source.sha256, project.revision, row.roi),
            str(expected_crop),
        )
        with tifffile.TiffFile(saved) as actual, tifffile.TiffFile(expected_crop) as verified:
            left, right = actual.pages[0], verified.pages[0]
            if not isinstance(left, tifffile.TiffPage) or not isinstance(right, tifffile.TiffPage):
                raise ValueError("裁剪缺少完整TIFF页")
            if (
                left.dtype != right.dtype
                or left.shape != right.shape
                or left.photometric != right.photometric
                or left.extrasamples != right.extrasamples
            ):
                raise ValueError("裁剪位深/通道/形状改变")
            if not np.array_equal(left.asarray(), right.asarray()) or json.loads(
                left.description
            ) != json.loads(right.description):
                raise ValueError("裁剪原值像素或来源坐标不一致")
        expected_crop.unlink()


def _verify_xlsx(path: Path, expected: bytes) -> None:
    with ZipFile(BytesIO(expected)) as generated:
        names = set(generated.namelist())
        with path.open("rb") as stream:
            count = preflight_zip(stream, path.stat().st_size, max_members=len(names))
            with ZipFile(stream) as actual:
                infos = actual.infolist()
                if (
                    count != len(names)
                    or len(infos) != len(names)
                    or {i.filename for i in infos} != names
                ):
                    raise ValueError("XLSX成员集合不一致")
                for info in infos:
                    if info.flag_bits & 1 or info.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
                        raise ValueError("XLSX压缩/加密格式无效")
                    data = generated.read(info.filename)
                    if info.file_size != len(data):
                        raise ValueError("XLSX内容大小不一致")
                    with actual.open(info) as member:
                        if member.read(len(data) + 1) != data:
                            raise ValueError("XLSX内容与核验结果不一致")


def _tables(project: WBFigureProject, verified: VerifiedProjectEvidence) -> dict[str, bytes]:
    results, ocr = verified.results, verified.ocr
    data = {
        "source.csv": project_csv_bytes(project, results),
        "source.xlsx": project_xlsx_bytes(project, results),
    }
    if isinstance(project, WBProjectOCR) and project.ocr:
        data["ocr.csv"] = project_ocr_csv_bytes(project, results, ocr)
        data["ocr.xlsx"] = two_sheet_xlsx_bytes(*project_ocr_table_rows(project, results, ocr))
    if isinstance(project, WBNormalizedProject):
        for labels in (False, True) if project.ocr else (False,):
            name = "normalization_ocr" if labels else "normalization"
            data[name + ".csv"] = normalization_csv_bytes(project, results, ocr, ocr_labels=labels)
            data[name + ".xlsx"] = two_sheet_xlsx_bytes(
                *normalization_table_rows(project, results, ocr, ocr_labels=labels)
            )
    return {"tables/" + name: value for name, value in data.items()}


def _run_evidence(
    project: WBFigureProject, index: ProjectArchiveIndex, entries: dict[str, ArchiveEntry]
) -> tuple[ArchiveRunEvidence, ...]:
    runs = project_runs(project)
    if len(runs) != len(index.runs):
        raise ValueError("归档运行数量与项目不同")
    evidence: list[ArchiveRunEvidence] = []
    for position, (run, record) in enumerate(zip(runs, index.runs, strict=True), 1):
        prefix = f"runs/{position:04d}"
        if (record.run_id, record.state, record.record) != (
            run.run_id,
            run.state,
            prefix + "/run.json",
        ):
            raise ValueError("归档运行身份或路径不一致")
        raw = entries[record.record].path.read_bytes()
        check_document_json(raw)
        if RunRecord.model_validate_json(raw) != run:
            raise ValueError("运行声明与项目不一致")
        if record.verification == "unavailable":
            if record.request or record.result or not record.reason:
                raise ValueError("缺失证据标记不一致")
        elif record.request != prefix + "/request.json" or record.result != (
            prefix + "/result.json" if run.result else None
        ):
            raise ValueError("运行资产路径不一致")
        evidence.append(
            ArchiveRunEvidence(
                run,
                str(entries[record.request].path) if record.request else "",
                str(entries[record.result].path) if record.result else "",
                record.reason if record.verification == "unavailable" else "",
            )
        )
    return tuple(evidence)


def _stage_project_archive(
    source: str, destination: str, *, cancelled: Callable[[], bool] = lambda: False
) -> StagedProjectArchive:
    """Destination must be new; caller owns cleanup and subsequent workspace import."""
    original = Path(source).absolute()
    if any(p.is_symlink() or p.is_junction() for p in (original, *original.parents)):
        raise ValueError("归档来源不能经过链接")
    staging = Path(destination).absolute()
    if any(p.is_symlink() or p.is_junction() for p in (staging, *staging.parents)):
        raise ValueError("恢复暂存目录不能经过链接")
    staging.mkdir()
    snapshot = staging / "original.zip"
    digest = snapshot_archive(Path(source), snapshot, cancelled)
    entries = read_archive(snapshot, staging, cancelled)
    required = {"project.json", "manifest.json", "figure.png"}
    if not required.issubset(entries):
        raise ValueError("归档缺少项目/拼图/来源记录")
    project = read_figure_project(entries["project.json"].path.read_bytes())
    required.update("assets/" + asset.sha256 for asset in project_assets(project))
    required.update(
        f"crops/{i:04d}.tif" for i, row in enumerate(project.rows, 1) if row.source and row.roi
    )
    index = (
        ProjectArchiveIndex.from_bytes(entries["archive.json"].path.read_bytes())
        if "archive.json" in entries
        else None
    )
    evidence: tuple[ArchiveRunEvidence, ...] = ()
    if index:
        if (index.project_id, index.revision, index.csv_encoding) != (
            project.project_id,
            project.revision,
            CSV_ENCODING,
        ):
            raise ValueError("归档索引与项目身份不同")
        if index.ocr != (
            "present" if isinstance(project, WBProjectOCR) and project.ocr else "not_configured"
        ) or index.normalization != (
            "configured"
            if isinstance(project, WBNormalizedProject) and project.normalizations
            else "not_configured"
        ):
            raise ValueError("归档OCR/归一化配置不一致")
        members = {m.path: m for m in index.members}
        if len(members) != len(index.members) or set(members) != set(entries) - {"archive.json"}:
            raise ValueError("索引成员集合不一致")
        for name, member in members.items():
            if member.role != _role(name, project):
                raise ValueError("归档成员角色不一致")
            if (member.sha256, member.size_bytes) != (
                entries[name].sha256,
                entries[name].size_bytes,
            ):
                raise ValueError("归档成员SHA或大小不一致")
        try:
            evidence = _run_evidence(project, index, entries)
        except KeyError as error:
            raise ValueError("归档声明的运行资产缺失") from error
        verified = verify_project_evidence(project, evidence, cancelled=cancelled)
        if tuple(r.model_dump() for r in index.runs) != verified.records:
            raise ValueError("归档结果未通过重新核验")
        for name, data in _tables(project, verified).items():
            required.add(name)
            if name not in entries:
                raise ValueError("归档结果表缺失")
            if name.endswith(".xlsx"):
                _verify_xlsx(entries[name].path, data)
            elif entries[name].path.read_bytes() != data:
                raise ValueError("CSV结果表与核验结果不一致")
        required.update(("archive.json", "README.txt"))
        for record in index.runs:
            required.update(name for name in (record.record, record.request, record.result) if name)
    if set(entries) != required:
        raise ValueError("归档成员缺失或包含未声明内容")
    paths = _assets(project, entries)
    _verify_images(project, entries, paths, staging, cancelled)
    records: list[StagedArchiveRun] = []
    for run in project_runs(project):
        entry = next((item for item in evidence if item.run == run), None)
        if entry is None or entry.error:
            records.append(
                StagedArchiveRun(run, error=entry.error if entry else "旧归档未携带结果证据")
            )
            continue
        for ref, path in ((run.request, entry.request_path), (run.result, entry.result_path)):
            if ref and path and ref.sha256 not in paths:
                saved = Path(path)
                target = saved.with_suffix(".json")
                os.rename(saved, target)
                paths[ref.sha256] = target
        records.append(
            StagedArchiveRun(run, run.request.sha256, run.result.sha256 if run.result else "")
        )
    check_cancel(cancelled)
    return StagedProjectArchive(
        project,
        str(snapshot),
        digest,
        tuple(StagedArchiveAsset(key, str(path)) for key, path in paths.items()),
        tuple(records),
        2 if index else 1,
    )


def inspect_project_archive(
    source: str, *, cancelled: Callable[[], bool] = lambda: False
) -> WBFigureProject:
    """Read-only validation for callers that do not need staging/import artifacts."""
    with TemporaryDirectory(prefix="wb-inspect-") as temporary:
        return stage_project_archive(
            source, str(Path(temporary) / "checked"), cancelled=cancelled
        ).project


def stage_project_archive(
    source: str, destination: str, *, cancelled: Callable[[], bool] = lambda: False
) -> StagedProjectArchive:
    try:
        return _stage_project_archive(source, destination, cancelled=cancelled)
    except (BadZipFile, EOFError, struct.error, zlib.error, RecursionError) as error:
        raise ValueError("归档结构或压缩内容损坏：" + str(error)) from error
