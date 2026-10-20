"""Necessary oracles for source roles, original geometry and durable confirmation."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.api import (
    ExportSelection,
    FigureSourcePath,
    IntakeSource,
    WBFigureProject,
    WBIntakeProject,
    accept_export_selections,
    confirm_intake,
    create_intake,
    discover_exports,
    install_export_discovery,
    intake_digest,
    load_tiff,
    prepare_intake_crops,
    prepare_intake_workflow,
    propose_intake_crop,
    read_figure_project,
    register_intake_source,
)


def sources(tmp_path: Path, bits: int = 16) -> tuple[WBIntakeProject, tuple[FigureSourcePath, ...]]:
    dtype = np.uint16 if bits == 16 else np.uint8
    top = 60000 if bits == 16 else 240
    signal = np.full((180, 360), top, dtype=dtype)
    white = np.zeros_like(signal)
    white[55:125, 50:310] = top
    merged = white.copy()
    for x in (80, 135, 190, 245):
        signal[80:94, x : x + 28] = top // 8
        merged[80:94, x : x + 28] = top // 8
    project = create_intake(WBFigureProject(project_id="export-test"))
    paths: list[FigureSourcePath] = []
    # Deliberately permute variant numbering; numbered suffix is not role truth.
    for index, raw in enumerate((signal, white, merged), 1):
        path = tmp_path / f"P_123456_0_1_0_0 ({index}).tiff"
        tifffile.imwrite(path, raw)
        image = load_tiff(path)
        asset = AssetRef(
            asset_id=f"s{index}",
            relative_path=f"assets/s{index}.tiff",
            sha256=image.sha256,
            size_bytes=path.stat().st_size,
        )
        project = register_intake_source(
            project,
            IntakeSource(
                source_id=f"s{index}",
                asset=asset,
                original_name=path.name,
                relative_path=f"Fig/{path.name}",
                width=360,
                height=180,
                bit_depth=16 if bits == 16 else 8,
            ),
            expected_digest=intake_digest(project),
        )
        paths.append(FigureSourcePath(image.sha256, str(path)))
    return project, tuple(paths)


@pytest.mark.parametrize("bits", [8, 16])
def test_roles_geometry_and_roundtrip_keep_original_samples(tmp_path: Path, bits: int) -> None:
    project, paths = sources(tmp_path, bits)
    before = [Path(p.path).read_bytes() for p in paths]
    old = project.model_dump_json()
    assert '"discovery"' not in old  # unchanged v1 wire shape and digest inputs
    report = discover_exports(project, paths)
    assert [o.role for o in report.observations] == ["signal", "white", "merge"]
    assert len({o.group_id for o in report.observations}) == 1
    assert report.observations[0].regions
    region = report.observations[0].regions[0]
    assert region.x0 <= 80 and region.x1 >= 273 and region.y0 <= 80 and region.y1 >= 94
    project = install_export_discovery(project, report, expected_digest=intake_digest(project))
    assert not project.intake.assignments and not project.intake.figures
    project = accept_export_selections(
        project,
        (
            ExportSelection(
                source_id="s1", figure_label="Fig", protein_label="P", lane_count=4, region_index=0
            ),
        ),
        expected_digest=intake_digest(project),
    )
    loaded = read_figure_project(project.model_dump_json().encode())
    assert isinstance(loaded, WBIntakeProject) and loaded.intake == project.intake
    project = confirm_intake(project, expected_digest=intake_digest(project))
    crops = prepare_intake_crops(
        prepare_intake_workflow(project, expected_digest=intake_digest(project))
    )
    evidence = propose_intake_crop(paths[0].path, crops, crops.rows[0].row_id)
    assert not evidence.reviewed and len(evidence.slots) == 4
    assert evidence.crop is not None and evidence.crop.x0 == region.x0
    assert [Path(p.path).read_bytes() for p in paths] == before


def test_cancel_and_stale_suggestions_never_install(tmp_path: Path) -> None:
    project, paths = sources(tmp_path)
    with pytest.raises(ValueError, match="取消"):
        discover_exports(project, paths, cancelled=lambda: True)
    report = discover_exports(project, paths)
    with pytest.raises(ValueError, match="修改"):
        install_export_discovery(project, report, expected_digest="old")
    assert project.intake.schema_version == 1 and not project.intake.discovery


def test_rgb_source_is_preserved_and_reported_as_candidate(tmp_path: Path) -> None:
    _, paths = sources(tmp_path, 8)
    raw = load_tiff(paths[0].path).pixels
    path = tmp_path / "RGB_123456 (1).tiff"
    tifffile.imwrite(path, np.stack([raw, raw, raw], axis=2), photometric="rgb")
    image = load_tiff(path)
    assert image.conversion is not None and image.source_shape == (180, 360, 3)
    assert np.array_equal(image.pixels, raw)
