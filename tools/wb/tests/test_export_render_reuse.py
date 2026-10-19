"""Frozen display reuse preserves pixels, raw crops, provenance and cancellation guards."""

import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from PIL import Image
from wb_tool.adapters import figure_export, laboratory_figure
from wb_tool.adapters.automatic_export import export_automatic_results
from wb_tool.adapters.figure_export import publish_rendered_bundle
from wb_tool.api import (
    build_intake_execution_plan,
    export_intake_outputs,
    intake_digest,
    render_figure,
)

from tools.wb.tests.test_figure_project import sample
from tools.wb.tests.test_intake_output import full_files


def test_legacy_multiformat_has_one_render_and_same_full_pixels_and_provenance(
    tmp_path: Path,
) -> None:
    project, sources = sample(tmp_path)
    frozen = project.model_dump_json()
    expected = render_figure(project, sources)
    original = figure_export.render_figure

    # Count the real adapter without replacing its semantics or numerical checks.
    from unittest.mock import patch

    with patch.object(figure_export, "render_figure", wraps=original) as counted:
        export_automatic_results(project, sources, str(tmp_path / "result"))
        calls = counted.call_count
    assert calls == 1
    output = tmp_path / "result"
    with Image.open(output / "figure.png") as png:
        assert png.tobytes() == expected.rgb
        assert png.info["wb_provenance"] == expected.manifest_json
    with tifffile.TiffFile(output / "figure.tif") as tiff:
        assert tiff.asarray().tobytes() == expected.rgb
        assert tiff.pages[0].description == expected.manifest_json
    with ZipFile(output / "project.zip") as archive:
        assert archive.read("figure.png") == (output / "figure.png").read_bytes()
        assert archive.read("manifest.json").decode() == expected.manifest_json
        assert archive.read("tables/source.csv") == (output / "measurements.csv").read_bytes()
    assert project.model_dump_json() == frozen
    with pytest.raises(FileExistsError):
        export_automatic_results(project, sources, str(output))
    stale = project.model_copy(update={"revision": project.revision + 1})
    with pytest.raises(ValueError, match="冻结拼图"):
        publish_rendered_bundle(stale, sources, str(tmp_path / "stale.zip"), expected)
    assert not (tmp_path / "stale.zip").exists()


def test_intake_tiff_reuses_exact_saved_fig_pixels_and_keeps_one_combined_layout(
    tmp_path: Path,
) -> None:
    from unittest.mock import patch

    project, sources, runs = full_files(tmp_path)
    paths = {item.sha256: item.path for item in sources}
    output = tmp_path / "result"
    with patch.object(
        laboratory_figure,
        "render_laboratory_figure",
        wraps=laboratory_figure.render_laboratory_figure,
    ) as counted:
        result = export_intake_outputs(project, sources, str(output), runs=runs)
    assert result.complete and counted.call_count == 1
    plan = build_intake_execution_plan(project, expected_digest=intake_digest(project))
    for figure in plan.figures:
        saved = next(e for e in project.intake_figures if e.figure_id == figure.figure_id)
        destination = output / figure.image_path
        assert (
            destination.with_suffix(".png").read_bytes()
            == Path(paths[saved.image.sha256]).read_bytes()
        )
        with Image.open(paths[saved.image.sha256]) as png:
            expected = png.tobytes()
            old_provenance = json.loads(png.info["wb_provenance"])
        with tifffile.TiffFile(destination) as tiff:
            assert tiff.asarray().tobytes() == expected
            provenance = json.loads(tiff.pages[0].description)
        binding = provenance.pop("export_binding")
        assert provenance == old_provenance
        assert binding == {
            "policy": "intake_saved_figure@1",
            "revision": project.revision,
            "figure_id": figure.figure_id,
            "input_digest": saved.input_digest,
            "asset_sha256": saved.image.sha256,
        }
        for row in figure.rows:
            crop = next(e for e in project.intake_crops if e.row_id == row.row_id)
            assert crop.raw_crop is not None
            np.testing.assert_array_equal(
                tifffile.imread(output / row.raw_crop_path),
                tifffile.imread(paths[crop.raw_crop.sha256]),
            )
