"""Batch edits preserve scientific requests and grid output preserves verified pixels."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import tifffile
from PIL import Image
from wb_tool.adapters.figure_image_export import publish_rendered_image
from wb_tool.adapters.intake_grid import render_intake_grid
from wb_tool.api import (
    BandBounds,
    Baseline,
    IntakeGrid,
    WBIntakeGridProject,
    WBIntakeOutputProject,
    analyze_annotations,
    intake_output_digest,
    load_tiff,
    read_figure_project,
    revise_intake_grid,
    revise_intake_quant,
    update_quant_lane,
)

from tools.wb.tests.test_intake_output import full_files, partial_files


def test_grid_roundtrip_keeps_single_fig_evidence_and_exact_pixels(tmp_path: Path) -> None:
    project, paths, _ = full_files(tmp_path)
    before = project.model_dump_json()
    updated = revise_intake_grid(project, IntakeGrid(columns=1, gap=17, order=("b", "a")))
    assert isinstance(read_figure_project(updated.model_dump_json().encode()), WBIntakeGridProject)
    assert read_figure_project(project.model_dump_json().encode()) == project
    assert project.model_dump_json() == before
    assert updated.intake_figures == project.intake_figures
    assert updated.analyses == project.analyses
    assert updated.figure_order == project.figure_order
    assert intake_output_digest(updated) != intake_output_digest(project)
    rendered = render_intake_grid(updated, paths)
    records = json.loads(rendered.manifest_json)["figures"]
    assert [r["figure_id"] for r in records] == ["b", "a"]
    assert records[0]["x"] == records[1]["x"] == 0
    assert records[1]["y"] == records[0]["height"] + 17
    pixels = np.frombuffer(rendered.rgb, dtype=np.uint8).reshape(rendered.height, rendered.width, 3)
    by_sha = {p.sha256: p.path for p in paths}
    for record in records:
        with Image.open(by_sha[record["sha256"]]) as image:
            expected = np.asarray(image.convert("RGB"))
        x, y = record["x"], record["y"]
        assert np.array_equal(pixels[y : y + record["height"], x : x + record["width"]], expected)
    assert np.all(pixels[records[0]["height"] : records[1]["y"]] == 255)
    for suffix in ("png", "tiff"):
        publish_rendered_image(rendered, 300, str(tmp_path / f"all.{suffix}"))
    with Image.open(tmp_path / "all.png") as image:
        assert np.array_equal(np.asarray(image), pixels)
    with tifffile.TiffFile(tmp_path / "all.tiff") as image:
        assert np.array_equal(image.asarray(), pixels)
    with pytest.raises(FileExistsError):
        publish_rendered_image(rendered, 300, str(tmp_path / "all.png"))
    with pytest.raises(ValueError):
        WBIntakeOutputProject.from_bytes(updated.model_dump_json().encode())


def test_partial_grid_rejects_false_complete_and_bad_order(tmp_path: Path) -> None:
    project, paths = partial_files(tmp_path)
    with pytest.raises(ValueError, match="尚未完成"):
        render_intake_grid(project, paths)
    with pytest.raises(ValueError, match="全部Fig"):
        revise_intake_grid(project, IntakeGrid(order=("a", "a")))


def test_batch_baseline_edit_matches_independent_request_without_touching_pixels(
    tmp_path: Path,
) -> None:
    project, paths, _ = full_files(tmp_path)
    plan = project.analyses[0]
    lane = plan.request.lanes[0]
    bounds, baseline = BandBounds(5, 25), Baseline(1.0, 2.0)
    changed = revise_intake_quant(
        project,
        plan.row_id,
        lane.roi.lane_id,
        band_id=lane.bands[0].band_id,
        bounds=bounds,
        baseline=baseline,
    )
    actual = next(p for p in changed.analyses if p.row_id == plan.row_id)
    # The existing independent public edit receives a plain analysis project.
    from wb_tool.api import WBLayoutProject

    independent = WBLayoutProject(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        rows=project.rows,
        figure_order=project.figure_order,
        template=project.template,
        analyses=project.analyses,
    )
    independent = update_quant_lane(
        independent,
        plan.row_id,
        lane.roi.lane_id,
        band_id=lane.bands[0].band_id,
        bounds=bounds,
        baseline=baseline,
    )
    request = next(p.request for p in independent.analyses if p.row_id == plan.row_id)
    assert actual.request == request
    assert actual.run is None and plan.run is not None
    assert changed.intake_figures == project.intake_figures
    assert (
        next(
            s for s in changed.workflow.steps if s.stage == "measure" and s.target_id == "a"
        ).status
        == "pending"
    )
    assert (
        next(
            s for s in changed.workflow.steps if s.stage == "measure" and s.target_id == "b"
        ).status
        == "done"
    )
    original = load_tiff(next(p.path for p in paths if p.sha256 == request.source_sha256))
    assert analyze_annotations(original, actual.request) == analyze_annotations(original, request)
    assert replace(actual.request, lanes=plan.request.lanes) == plan.request


def test_grid_order_survives_regrouping_with_changed_fig_ids(tmp_path: Path) -> None:
    from wb_tool.api import begin_intake_group_revision, intake_digest, revise_intake_grouping

    from tools.wb.tests.test_intake_group_revision import grouped_full

    project, _, _ = grouped_full(tmp_path)
    grid = revise_intake_grid(project, IntakeGrid(columns=1, order=("b", "a")))
    editing = begin_intake_group_revision(grid, expected_digest=intake_digest(grid))
    grouping = editing.intake.grouping
    assert grouping is not None
    changed = grouping.model_copy(
        update={
            "figures": tuple(
                f.model_copy(update={"figure_id": "c"}) if f.figure_id == "a" else f
                for f in grouping.figures
            ),
            "groups": tuple(
                g.model_copy(update={"figure_id": "c"}) if g.figure_id == "a" else g
                for g in grouping.groups
            ),
        }
    )
    result = revise_intake_grouping(editing, changed, expected_digest=intake_digest(editing))
    assert isinstance(result, WBIntakeGridProject)
    assert result.grid.order == ("b", "c")
    assert result.grid.columns == 1
    assert grid.grid.order == ("b", "a")


def test_aggregate_preview_bounds_gui_pixels_but_preserves_full_layout() -> None:
    from wb_tool.adapters.intake_grid import grid_preview
    from wb_tool.api import FigureRender

    manifest = {"aggregate": {"columns": 1}, "figures": [{"x": 0, "y": 0, "width": 3000}]}
    full = FigureRender(3000, 2, bytes([17, 28, 39]) * 6000, json.dumps(manifest))
    preview = grid_preview(full)
    assert max(preview.width, preview.height) == 2048
    actual = json.loads(preview.manifest_json)
    assert actual["figures"] == manifest["figures"]
    assert actual["preview_binding"]["full_width"] == 3000
    assert full.width == 3000 and len(full.rgb) == 18000
