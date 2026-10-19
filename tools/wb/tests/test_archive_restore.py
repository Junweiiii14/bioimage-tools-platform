"""Portable restore checks retain raw samples and distinguish history from local runs."""

import json
import struct
from collections.abc import Mapping
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import numpy as np
import pytest
import tifffile
from pydantic import TypeAdapter
from wb_tool.adapters.archive_reader import preflight_zip
from wb_tool.adapters.archive_restore import inspect_project_archive, stage_project_archive
from wb_tool.adapters.project_evidence import verify_project_evidence
from wb_tool.api import (
    ArchiveRunEvidence,
    FigureSourcePath,
    OCRRecognition,
    WBFigureProject,
    WBProjectOCR,
    export_figure_bundle,
    fill_project_table,
    project_with_ocr,
    read_figure_project,
)
from wb_tool.application.project_restore import (
    WBRestoredProject,
    imported_run,
    project_assets,
    restore_staged_project,
)

from tools.wb.tests.test_project_analysis import asset
from tools.wb.tests.test_project_archive import bundle


def real_bundle(tmp_path: Path):
    project, sources, evidence, results, loaded = bundle(tmp_path)
    assert project.ocr and project.ocr.run
    composite = tmp_path / "composite.tif"
    tifffile.imwrite(composite, np.full((500, 1000), 255, dtype=np.uint8))
    source = asset(composite.read_bytes(), "real-composite")
    recognition = replace(loaded.recognition, source_sha256=source.sha256)
    raw = TypeAdapter(OCRRecognition).dump_json(recognition)
    frozen = read_figure_project(Path(evidence[-1].request_path).read_bytes())
    assert isinstance(frozen, WBProjectOCR) and frozen.ocr
    frozen = project_with_ocr(frozen, frozen.ocr.model_copy(update={"source": source}))
    request = frozen.model_dump_json().encode()
    run = project.ocr.run.model_copy(
        update={
            "request": asset(request, "real-ocr-request"),
            "result": asset(raw, "real-ocr-result"),
        }
    )
    Path(evidence[-1].request_path).write_bytes(request)
    Path(evidence[-1].result_path).write_bytes(raw)
    project = project_with_ocr(
        project,
        project.ocr.model_copy(update={"source": source, "run": run, "recognition": recognition}),
    )
    sources = sources[:-1] + (FigureSourcePath(source.sha256, str(composite)),)
    evidence = evidence[:-1] + (replace(evidence[-1], run=run),)
    return project, sources, evidence, results


def exported(tmp_path: Path):
    project, sources, evidence, results = real_bundle(tmp_path)
    archive = tmp_path / "project.zip"
    export_figure_bundle(project, sources, str(archive), runs=evidence)
    return archive, project, results


def rewritten(
    source: Path, destination: Path, changes: Mapping[str, bytes | None], *, hashes: bool = True
) -> None:
    with ZipFile(source) as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}
    for name, data in changes.items():
        if data is None:
            contents.pop(name, None)
        else:
            contents[name] = data
    if hashes and "archive.json" in contents:
        index = json.loads(contents["archive.json"])
        for member in index["members"]:
            if member["path"] in contents:
                data = contents[member["path"]]
                member.update(sha256=sha256(data).hexdigest(), size_bytes=len(data))
        contents["archive.json"] = json.dumps(index).encode()
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr(name, data)


def test_restore_retains_ocr_results_identity_and_original_zip(tmp_path: Path) -> None:
    source, project, _ = exported(tmp_path)
    original = source.read_bytes()
    staged = stage_project_archive(str(source), str(tmp_path / "stage"))
    assert staged.project == project and staged.format_version == 2
    assert Path(staged.archive_path).read_bytes() == original
    imported = tuple(
        asset(Path(item.path).read_bytes(), "copied-" + str(i))
        for i, item in enumerate(staged.assets)
    )
    restored = restore_staged_project(staged, imported, asset(original, "original-zip"))
    assert isinstance(restored, WBRestoredProject)
    assert read_figure_project(restored.model_dump_json().encode()) == restored
    assert len(restored.imported_runs) == 3 and len(restored.archive_sources) == 1
    assert restored.project_id == project.project_id and restored.revision == project.revision
    paths = {item.sha256: item.path for item in staged.assets}
    evidence = tuple(
        ArchiveRunEvidence(
            item.run,
            paths[item.request.sha256] if item.request else "",
            paths[item.result.sha256] if item.result else "",
            item.error,
        )
        for item in restored.imported_runs
    )
    verified = verify_project_evidence(restored, evidence)
    assert len(verified.results) == 2 and verified.ocr is not None
    assert [cell.value for cell in fill_project_table(restored, verified.results)] == [
        4000,
        None,
        0,
        8000,
        16000,
        0,
    ]
    assert all(imported_run(restored, item.run) == item for item in restored.imported_runs)
    assert {ref.sha256 for ref in project_assets(restored)} >= {
        item.sha256 for item in staged.assets
    }
    assert source.read_bytes() == original


@pytest.mark.parametrize(
    "kind", ["csv", "xlsx", "result", "crop", "figure", "manifest", "index", "missing", "extra"]
)
def test_rejects_inconsistent_archives_even_with_rehashed_members(
    tmp_path: Path, kind: str
) -> None:
    source, _, _ = exported(tmp_path)
    with ZipFile(source) as archive:
        if kind == "csv":
            changes = {
                "tables/source.csv": archive.read("tables/source.csv").replace(b"4000.0", b"9000.0")
            }
        elif kind == "xlsx":
            stream = BytesIO()
            with (
                ZipFile(BytesIO(archive.read("tables/source.xlsx"))) as old,
                ZipFile(stream, "w") as new,
            ):
                for name in old.namelist():
                    new.writestr(name, old.read(name).replace(b"4000.0", b"9000.0"))
            changes = {"tables/source.xlsx": stream.getvalue()}
        elif kind == "result":
            changes = {"runs/0001/result.json": archive.read("runs/0001/result.json") + b" "}
        elif kind == "crop":
            stream = BytesIO()
            tifffile.imwrite(stream, np.zeros((10, 30), dtype=np.uint16))
            changes = {"crops/0001.tif": stream.getvalue()}
        elif kind == "figure":
            changes = {"figure.png": b"not a png"}
        elif kind == "manifest":
            manifest = json.loads(archive.read("manifest.json"))
            manifest["revision"] += 1
            changes = {"manifest.json": json.dumps(manifest).encode()}
        elif kind == "index":
            index = json.loads(archive.read("archive.json"))
            index["schema_version"] = 999
            changes = {"archive.json": json.dumps(index).encode()}
        elif kind == "missing":
            changes = {"runs/0001/result.json": None}
        else:
            changes = {"../../outside": b"data"}
    target = tmp_path / "changed.zip"
    rewritten(source, target, changes)
    with pytest.raises((ValueError, OSError)):
        inspect_project_archive(str(target))


def test_missing_evidence_and_legacy_are_explicit(tmp_path: Path) -> None:
    project, sources, evidence, _ = real_bundle(tmp_path)
    target = tmp_path / "partial.zip"
    export_figure_bundle(project, sources, str(target), runs=evidence[1:])
    staged = stage_project_archive(str(target), str(tmp_path / "partial"))
    assert staged.runs[0].error and staged.runs[1].result_sha256
    with ZipFile(target) as archive:
        removed = {
            name: None
            for name in archive.namelist()
            if name.startswith(("runs/", "tables/")) or name in ("archive.json", "README.txt")
        }
    legacy = tmp_path / "legacy.zip"
    rewritten(target, legacy, removed)
    old = stage_project_archive(str(legacy), str(tmp_path / "old"))
    assert old.format_version == 1
    assert all(record.error == "旧归档未携带结果证据" for record in old.runs)


def test_duplicate_link_cancel_and_destination_protection(tmp_path: Path) -> None:
    source, _, _ = exported(tmp_path)
    target = tmp_path / "duplicate.zip"
    target.write_bytes(source.read_bytes())
    with pytest.warns(UserWarning), ZipFile(target, "a") as archive:
        archive.writestr("project.json", b"{}")
    with pytest.raises(ValueError, match="重复"):
        inspect_project_archive(str(target))
    link = tmp_path / "link.zip"
    with ZipFile(link, "w") as archive:
        info = ZipInfo("project.json")
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        archive.writestr(info, "target")
    with pytest.raises(ValueError, match="链接"):
        inspect_project_archive(str(link))
    with pytest.raises(ValueError, match="取消"):
        inspect_project_archive(str(source), cancelled=lambda: True)
    with pytest.raises(FileExistsError):
        stage_project_archive(str(source), str(tmp_path))
    assert source.exists()


def test_central_directory_budget_is_checked_before_zipfile() -> None:
    data = b"PK\x03\x04" + struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, 5000, 5000, 0, 4, 0)
    with pytest.raises(ValueError, match="中央目录"):
        preflight_zip(BytesIO(data), len(data))


@pytest.mark.parametrize("mode", ["u8", "u16", "rgb16", "miniswhite"])
def test_restores_v1_pixels_without_depth_channel_or_polarity_changes(
    tmp_path: Path, mode: str
) -> None:
    from tools.wb.tests.test_project_analysis import configured

    configured_project, _ = configured(tmp_path)
    pixels = np.arange(600, dtype=np.uint16).reshape(20, 30)
    if mode == "u8":
        pixels = (pixels % 256).astype(np.uint8)
    elif mode == "rgb16":
        pixels = np.stack((pixels, pixels + 100, pixels + 200), axis=-1)
    original = tmp_path / "native.tiff"
    tifffile.imwrite(
        original,
        pixels,
        photometric="rgb"
        if mode == "rgb16"
        else "miniswhite"
        if mode == "miniswhite"
        else "minisblack",
    )
    ref = asset(original.read_bytes(), "native")
    row = configured_project.rows[0].model_copy(
        update={"source": ref, "bit_depth": 8 if mode == "u8" else 16}
    )
    project = WBFigureProject(
        project_id="native",
        rows=(row,),
        figure_order=(row.figure,),
        template=configured_project.template.model_copy(update={"font_size": 8}),
    )
    output = tmp_path / "native.zip"
    export_figure_bundle(project, (FigureSourcePath(ref.sha256, str(original)),), str(output))
    staged = stage_project_archive(str(output), str(tmp_path / "stage"))
    assert staged.project == project
    assert Path(staged.assets[0].path).read_bytes() == original.read_bytes()
    with (
        ZipFile(output) as archive,
        tifffile.TiffFile(BytesIO(archive.read("crops/0001.tif"))) as crop,
    ):
        page = crop.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        cropped = page.asarray()
    assert row.roi and cropped.dtype == pixels.dtype
    np.testing.assert_array_equal(cropped, pixels[row.roi.y0 : row.roi.y1, row.roi.x0 : row.roi.x1])


@pytest.mark.parametrize(
    "attack",
    [
        "encrypted",
        "strong_encryption",
        "dos_directory",
        "compression",
        "expanded",
        "role",
        "hash",
        "json_duplicates",
    ],
)
def test_rejects_container_budgets_roles_and_inconsistent_metadata(
    tmp_path: Path, attack: str
) -> None:
    source, _, _ = exported(tmp_path)
    target = tmp_path / "attack.zip"
    if attack in ("encrypted", "strong_encryption", "dos_directory", "compression", "expanded"):
        data = bytearray(source.read_bytes())
        start = data.index(b"PK\x01\x02")
        if attack == "encrypted":
            struct.pack_into("<H", data, start + 8, 1)
        elif attack == "strong_encryption":
            struct.pack_into("<H", data, start + 8, 64)
        elif attack == "dos_directory":
            struct.pack_into("<L", data, start + 38, 0x10)
        elif attack == "compression":
            struct.pack_into("<H", data, start + 10, 99)
        else:
            struct.pack_into("<L", data, start + 24, 3 * 1024**3)
        target.write_bytes(data)
    else:
        with ZipFile(source) as archive:
            index = json.loads(archive.read("archive.json"))
        if attack == "role":
            index["members"][0]["role"] = "not_a_display"
        elif attack == "hash":
            index["members"][0]["sha256"] = "f" * 64
        encoded = json.dumps(index).encode()
        if attack == "json_duplicates":
            encoded = b'{"format":"wb_project_archive",' + encoded[1:]
        rewritten(source, target, {"archive.json": encoded}, hashes=False)
    with pytest.raises(ValueError):
        inspect_project_archive(str(target))


def test_valid_zip64_directory_and_crc_corruption(tmp_path: Path) -> None:
    source, project, _ = exported(tmp_path)
    raw = source.read_bytes()
    end = len(raw) - 22
    _, _, _, _, count, size, position, _ = struct.unpack("<4s4H2LH", raw[end:])
    directory = struct.pack(
        "<4sQ2H2L4Q", b"PK\x06\x06", 44, 45, 45, 0, 0, count, count, size, position
    )
    locator = struct.pack("<4sLQL", b"PK\x06\x07", 0, end, 1)
    extended = tmp_path / "zip64.zip"
    extended.write_bytes(raw[:end] + directory + locator + raw[end:])
    assert inspect_project_archive(str(extended)) == project
    damaged = bytearray(raw)
    central = damaged.index(b"PK\x01\x02")
    struct.pack_into("<L", damaged, central + 16, 1)
    extended.write_bytes(damaged)
    with pytest.raises(ValueError, match="损坏"):
        inspect_project_archive(str(extended))
