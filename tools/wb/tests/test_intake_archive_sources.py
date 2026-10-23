"""Portable intake archives retain typed source, crop, figure and metadata assets."""

import json
import struct
import zlib
from pathlib import Path

import numpy as np
import pytest
import tifffile
from PIL import Image
from wb_tool.api import (
    FigureSourcePath,
    IntakeManifest,
    IntakeSource,
    WBIntakeOutputProject,
    export_figure_bundle,
    export_intake_outputs,
    load_intake_figure_preview,
    load_tiff,
    record_intake_output,
    stage_project_archive,
)
from wb_tool.application.instrument_intake import intake_manifest_digest

from tools.wb.tests.test_intake_figure import asset
from tools.wb.tests.test_intake_output import partial_files


def with_unselected_source(
    project: WBIntakeOutputProject, path: Path, *, width: int = 120, height: int = 80
) -> WBIntakeOutputProject:
    source = IntakeSource(
        source_id="unselected",
        asset=asset(path),
        # The persisted name is not a file-format authority.
        original_name="auxiliary.json",
        relative_path="auxiliary.json",
        width=width,
        height=height,
        bit_depth=16,
    )
    manifest = IntakeManifest.model_validate(
        {
            **dict(project.intake),
            "sources": (*project.intake.sources, source),
            "confirmed_digest": "",
        }
    )
    digest = intake_manifest_digest(project.project_id, manifest)
    return WBIntakeOutputProject.model_validate(
        {
            **dict(project),
            "intake": manifest.model_copy(update={"confirmed_digest": digest}),
            "workflow": project.workflow.model_copy(update={"intake_digest": digest}),
        }
    )


def test_restore_all_typed_images_and_keep_output_metadata_json(tmp_path: Path) -> None:
    project, paths = partial_files(tmp_path)
    auxiliary = tmp_path / "auxiliary.tif"
    tifffile.imwrite(auxiliary, np.arange(80 * 120, dtype=np.uint16).reshape(80, 120))
    project = with_unselected_source(project, auxiliary)
    paths = (*paths, FigureSourcePath(asset(auxiliary).sha256, str(auxiliary)))
    prepared = export_intake_outputs(project, paths, str(tmp_path / "output"))
    # A metadata asset's misleading extension must not turn it into a TIFF.
    metadata = tmp_path / "metadata.tiff"
    metadata.write_bytes((tmp_path / "output" / "index.json").read_bytes())
    project = record_intake_output(project, prepared, asset(metadata))
    paths = (*paths, FigureSourcePath(asset(metadata).sha256, str(metadata)))
    archive = tmp_path / "all-assets.zip"
    export_figure_bundle(project, paths, str(archive))

    staged = stage_project_archive(str(archive), str(tmp_path / "restored"))
    restored = {entry.sha256: Path(entry.path) for entry in staged.assets}
    tiffs = [source.asset for source in project.intake.sources]
    tiffs.extend(crop.raw_crop for crop in project.intake_crops if crop.raw_crop is not None)
    expected_suffixes = {ref.sha256: ".tif" for ref in tiffs}
    expected_suffixes.update({figure.image.sha256: ".png" for figure in project.intake_figures})
    expected_suffixes[asset(metadata).sha256] = ".json"
    assert {digest: restored[digest].suffix for digest in expected_suffixes} == expected_suffixes
    originals = {source.sha256: Path(source.path) for source in paths}
    for ref in tiffs:
        actual, expected = load_tiff(restored[ref.sha256]), load_tiff(originals[ref.sha256])
        assert actual.sha256 == expected.sha256 == ref.sha256
        assert actual.pixels.dtype == expected.pixels.dtype
        np.testing.assert_array_equal(actual.pixels, expected.pixels)
    assert isinstance(staged.project, WBIntakeOutputProject)
    for figure in project.intake_figures:
        assert (
            restored[figure.image.sha256].read_bytes()
            == originals[figure.image.sha256].read_bytes()
        )
        preview = load_intake_figure_preview(
            staged.project, figure.figure_id, str(restored[figure.image.sha256])
        )
        assert preview.width > 0 and preview.height > 0
    assert json.loads(restored[asset(metadata).sha256].read_bytes()) == json.loads(
        metadata.read_bytes()
    )


@pytest.mark.parametrize("invalid", ("multiple_pages", "pixel_budget"))
def test_unselected_tiff_cannot_bypass_restore_budget(tmp_path: Path, invalid: str) -> None:
    project, paths = partial_files(tmp_path)
    auxiliary = tmp_path / "invalid.tif"
    if invalid == "multiple_pages":
        tifffile.imwrite(
            auxiliary, np.ones((2, 80, 120), dtype=np.uint16), photometric="minisblack"
        )
        expected_error = "单页"
    else:
        tifffile.imwrite(auxiliary, np.ones((80, 120), dtype=np.uint16))
        # Header-only oversize evidence; do not allocate a 36-million-pixel array.
        with tifffile.TiffFile(auxiliary, mode="r+") as image:
            page = image.pages[0]
            assert isinstance(page, tifffile.TiffPage)
            page.tags["ImageWidth"].overwrite(6000)
            page.tags["ImageLength"].overwrite(6000)
        expected_error = "3200万像素"
    project = with_unselected_source(project, auxiliary)
    paths = (*paths, FigureSourcePath(asset(auxiliary).sha256, str(auxiliary)))
    archive = tmp_path / "invalid-source.zip"
    export_figure_bundle(project, paths, str(archive))
    with pytest.raises(ValueError, match=expected_error):
        stage_project_archive(str(archive), str(tmp_path / "rejected"))


def test_saved_figure_png_cannot_bypass_restore_pixel_budget(tmp_path: Path) -> None:
    project, paths = partial_files(tmp_path)
    figure = project.intake_figures[0]
    original = next(Path(path.path) for path in paths if path.sha256 == figure.image.sha256)
    data = bytearray(original.read_bytes())
    struct.pack_into(">II", data, 16, 6000, 6000)
    struct.pack_into(">I", data, 29, zlib.crc32(data[12:29]))
    oversized = tmp_path / "oversized.png"
    oversized.write_bytes(data)
    with Image.open(oversized) as image:
        assert image.size == (6000, 6000)
    replacement = asset(oversized)
    project = WBIntakeOutputProject.model_validate(
        {
            **dict(project),
            "intake_figures": (figure.model_copy(update={"image": replacement}),),
        }
    )
    paths = tuple(path for path in paths if path.sha256 != figure.image.sha256)
    paths = (*paths, FigureSourcePath(replacement.sha256, str(oversized)))
    archive = tmp_path / "invalid-figure.zip"
    export_figure_bundle(project, paths, str(archive))
    with pytest.raises(ValueError, match="3200万像素"):
        stage_project_archive(str(archive), str(tmp_path / "rejected"))
