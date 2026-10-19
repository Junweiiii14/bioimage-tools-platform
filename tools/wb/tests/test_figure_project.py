"""Independent pixel/geometry assertions for multi-source composition and provenance."""

import json
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from PIL import Image
from tool_contracts.api import AssetRef
from wb_tool.api import (
    FigureRow,
    FigureSourcePath,
    FigureTemplate,
    LaneROI,
    WBFigureProject,
    export_figure_bundle,
    plan_figure_layout,
    render_figure,
)


def sample(tmp_path: Path) -> tuple[WBFigureProject, tuple[FigureSourcePath, ...]]:
    paths: list[FigureSourcePath] = []
    rows: list[FigureRow] = []
    # Two proteins with the SAME label are independent rows/sources; a third Fig differs in width/N.
    for index, width in enumerate((36, 36, 48)):
        pixels = np.full((40, width), 25700 + 257 * index, dtype=np.uint16)
        pixels[8:13, 12:18] = 5140 + 257 * index
        source = tmp_path / f"{index}.tif"
        tifffile.imwrite(source, pixels)
        data = source.read_bytes()
        digest = sha256(data).hexdigest()
        asset = AssetRef(
            asset_id=f"a{index}",
            relative_path=f"inputs/{index}.tif",
            sha256=digest,
            size_bytes=len(data),
        )
        paths.append(FigureSourcePath(digest, str(source)))
        rows.append(
            FigureRow(
                row_id=f"r{index}",
                source=asset,
                filename=source.name,
                width=width,
                height=40,
                bit_depth=16,
                figure="Fig1" if index < 2 else "Fig2",
                protein="AKT",
                lane_count=3 if index < 2 else 4,
                empty_lanes=(2,),
                roi=LaneROI(f"r{index}", 0, 5, width, 25),
                reviewed=True,
            )
        )
    rows.append(
        FigureRow(row_id="missing", figure="Fig1", protein="GAPDH", lane_count=3, reviewed=True)
    )
    return WBFigureProject(
        project_id="project",
        name="experiment",
        revision=4,
        rows=tuple(rows),
        figure_order=("Fig2", "Fig1"),
        template=FigureTemplate(crop_height=20, font_size=12, label_width=90, columns=2),
    ), tuple(paths)


def test_figure_pixels_raw_crops_and_reordered_provenance(tmp_path: Path) -> None:
    project, paths = sample(tmp_path)
    render = render_figure(project, paths)
    metadata = json.loads(render.manifest_json)
    rgb = np.frombuffer(render.rgb, dtype=np.uint8).reshape(render.height, render.width, 3)
    assert [row["row_id"] for row in metadata["rows"]] == ["r2", "r0", "r1", "missing"]
    assert [p.width for p in plan_figure_layout(project).placements] == [48, 36]
    for record in metadata["rows"][:3]:
        x0, y0, x1, y1 = record["output_box"]
        index = int(record["row_id"][1:])
        actual = rgb[y0:y1, x0:x1, 0]
        # Analytic expected gray: background 100+i, band 20+i. No resizing or auto contrast.
        assert actual.shape == (20, 48 if index == 2 else 36)
        assert actual[0, 0] == 100 + index
        assert np.all(actual[3:8, 12:18] == 20 + index)
        assert np.all(rgb[y0:y1, x0:x1, 1] == actual)
    target = tmp_path / "figure.zip"
    export_figure_bundle(project, paths, str(target))
    with ZipFile(target) as archive:
        assert WBFigureProject.from_bytes(archive.read("project.json")) == project
        assert json.loads(archive.read("manifest.json")) == metadata
        with Image.open(BytesIO(archive.read("figure.png"))) as png:
            assert json.loads(png.info["wb_provenance"]) == metadata
        for index, path in enumerate(paths):
            assert archive.read("assets/" + path.sha256) == Path(path.path).read_bytes()
            with tifffile.TiffFile(BytesIO(archive.read(f"crops/{index + 1:04d}.tif"))) as image:
                page = image.pages[0]
                assert isinstance(page, tifffile.TiffPage)
                crop = page.asarray()
            assert crop.dtype == np.uint16 and crop[0, 0] == 25700 + 257 * index
            assert np.all(crop[3:8, 12:18] == 5140 + 257 * index)
        assert not any("0004" in name for name in archive.namelist())
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        export_figure_bundle(project, paths, str(target))
    assert target.read_bytes() == before


def test_project_roundtrip_and_strict_document(tmp_path: Path) -> None:
    project, _ = sample(tmp_path)
    assert WBFigureProject.from_bytes(project.model_dump_json().encode()) == project
    raw = project.model_dump(mode="json")
    for updates in (
        {"schema_version": True},
        {"schema_version": 2},
        {"revision": False},
        {"unknown": 1},
        {"figure_order": ["Fig1", "Fig1"]},
    ):
        with pytest.raises(ValueError):
            WBFigureProject.from_bytes(json.dumps({**raw, **updates}).encode())
    with pytest.raises(ValueError, match="重复"):
        WBFigureProject.from_bytes(
            project.model_dump_json().replace('"revision":4', '"revision":4,"revision":5').encode()
        )


def test_review_and_blank_lane_identity_gates(tmp_path: Path) -> None:
    project, paths = sample(tmp_path)
    row = project.rows[0]
    assert [(r.x0, r.x1) for r in row.quantitative_lanes()] == [(0, 12), (12, 24), (24, 36)]
    pending = row.model_copy(update={"reviewed": False})
    with pytest.raises(ValueError, match="审核"):
        pending.quantitative_lanes()
    with pytest.raises(ValueError, match="缺图"):
        project.rows[-1].quantitative_lanes()
    project = project.model_copy(update={"rows": (pending, *project.rows[1:])})
    render_figure(project, paths, require_review=False)
    with pytest.raises(ValueError, match="未审核"):
        export_figure_bundle(project, paths, str(tmp_path / "no.zip"))
    assert not (tmp_path / "no.zip").exists()


def test_cancel_during_archive_removes_stage(tmp_path: Path) -> None:
    project, paths = sample(tmp_path)
    with pytest.raises(ValueError, match="取消"):
        export_figure_bundle(
            project,
            paths,
            str(tmp_path / "cancelled.zip"),
            cancelled=lambda: bool(list(tmp_path.glob(".wb-figure-*"))),
        )
    assert not (tmp_path / "cancelled.zip").exists()
    assert not list(tmp_path.glob(".wb-figure-*"))


@pytest.mark.parametrize("change", ["width", "height", "lanes", "missing_path", "hash", "cancel"])
def test_figure_refuses_silent_alignment_or_bad_sources(tmp_path: Path, change: str) -> None:
    project, paths = sample(tmp_path)
    row = project.rows[0]
    if change == "width":
        row = row.model_copy(update={"roi": LaneROI(row.row_id, 0, 5, 35, 25)})
    if change == "height":
        row = row.model_copy(update={"roi": LaneROI(row.row_id, 0, 5, 36, 24)})
    if change == "lanes":
        row = row.model_copy(update={"lane_count": 4})
    project = project.model_copy(update={"rows": (row, *project.rows[1:])})
    if change == "missing_path":
        paths = paths[1:]
    if change == "hash":
        tifffile.imwrite(paths[0].path, np.zeros((40, 36), dtype=np.uint16))
    with pytest.raises(ValueError):
        export_figure_bundle(
            project, paths, str(tmp_path / "no.zip"), cancelled=lambda: change == "cancel"
        )
    assert not (tmp_path / "no.zip").exists()
    assert not list(tmp_path.glob(".wb-figure-*"))
