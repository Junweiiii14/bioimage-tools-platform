"""Original-pixel manual lanes, multi-peak recovery and whole-height smear."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.api import (
    BandBounds,
    Baseline,
    FigureRow,
    LaneROI,
    ManualQuantTarget,
    WBAnalysisProject,
    WBFigureProject,
    add_manual_group,
    analysis_is_current,
    analyze_annotations,
    configure_manual_quantification,
    edit_quant_band,
    load_tiff,
    read_figure_project,
    replan_quant_lanes,
    update_quant_lane,
)


def example(tmp_path: Path):
    y = np.arange(120)
    signal = 20 + np.maximum(0, 100 - 10 * np.abs(y - 30)) + np.maximum(0, 80 - 8 * np.abs(y - 80))
    raw = np.repeat((255 - signal).astype(np.uint8)[:, None], 100, axis=1)
    path = tmp_path / "manual.tif"
    tifffile.imwrite(path, raw)
    image = load_tiff(path)
    row = FigureRow(
        row_id="source",
        source=AssetRef(
            asset_id="a",
            relative_path="inputs/a.tif",
            sha256=image.sha256,
            size_bytes=path.stat().st_size,
        ),
        filename=path.name,
        width=100,
        height=120,
        bit_depth=8,
    )
    project = WBFigureProject(project_id="p", rows=(row,), figure_order=("Fig1",))
    lanes = (LaneROI("source:01", 5, 0, 25, 120), LaneROI("source:02", 60, 0, 80, 120))
    target = ManualQuantTarget(
        image.sha256, 0, LaneROI("source", 5, 0, 80, 120), 2, "dark", lane_rois=lanes
    )
    return image, project, target


def test_manual_full_lanes_preserve_gap_multiple_peaks_and_saved_groups(tmp_path: Path) -> None:
    image, project, target = example(tmp_path)
    before = image.source.read_bytes()
    configured = configure_manual_quantification(image, project, target)
    plan = configured.analyses[0]
    assert [lane.roi for lane in plan.request.lanes] == list(target.lane_rois)
    assert [len(lane.bands) for lane in plan.request.lanes] == [2, 2]
    # T046 versions the automatic boundary proposal; the analytic areas stay fixed.
    assert plan.request.quant_policy == "peak_envelope@1"
    result = analyze_annotations(image, plan.request)
    assert [[b.signal for b in lane.bands] for lane in result.lanes] == [[1000, 800], [1000, 800]]
    added = add_manual_group(configured, "source", "Fig2B")
    assert isinstance(added, WBAnalysisProject)
    assert added.analyses == configured.analyses and added.rows[0] == configured.rows[0]
    assert added.rows[-1].source == added.rows[0].source and added.rows[-1].roi is None
    assert read_figure_project(added.model_dump_json().encode()) == added
    assert image.source.read_bytes() == before
    assert analysis_is_current(added, plan)


def test_smear_whole_range_analytic_area_and_manual_adjustment(tmp_path: Path) -> None:
    image, project, target = example(tmp_path)
    target = replace(target, measurement_mode="smear")
    configured = configure_manual_quantification(image, project, target)
    plan = configured.analyses[0]
    assert all(
        len(lane.bands) == 1 and lane.bands[0].bounds == BandBounds(0, 119)
        for lane in plan.request.lanes
    )
    result = analyze_annotations(image, plan.request)
    # Independent triangles: bases20, heights100/80 -> 1000+800. Width is row
    # averaging, matching the established WBQuant signal units.
    assert [lane.bands[0].signal for lane in result.lanes] == pytest.approx([1800, 1800])
    changed = update_quant_lane(
        configured, "source", "source:01", bounds=BandBounds(20, 40), baseline=Baseline(20, 20)
    )
    assert analyze_annotations(image, changed.analyses[0].request).lanes[0].bands[
        0
    ].signal == pytest.approx(1000)
    assert configure_manual_quantification(image, changed, target) is changed


def test_manual_add_exclude_and_invalid_peak_are_atomic(tmp_path: Path) -> None:
    image, project, target = example(tmp_path)
    configured = configure_manual_quantification(image, project, target)
    plan = configured.analyses[0]
    with pytest.raises(ValueError, match="重叠"):
        edit_quant_band(configured, "source", "source:01", "add", bounds=BandBounds(27, 33))
    changed = edit_quant_band(configured, "source", "source:01", "add", bounds=BandBounds(100, 110))
    assert len(changed.analyses[0].request.lanes[0].bands) == 3
    excluded = edit_quant_band(changed, "source", "source:01", "exclude", "target")
    assert not excluded.analyses[0].request.lanes[0].bands[0].included
    assert configured.analyses[0] == plan


@pytest.mark.parametrize(
    "roi", [LaneROI("source:01", 6, 0, 26, 120), LaneROI("source:01", 5, 5, 28, 115)]
)
def test_smear_geometry_edit_and_reopen_keep_complete_integration(
    tmp_path: Path, roi: LaneROI
) -> None:
    image, project, target = example(tmp_path)
    configured = configure_manual_quantification(
        image, project, replace(target, measurement_mode="smear")
    )
    changed = update_quant_lane(configured, "source", "source:01", roi=roi)
    reopened = read_figure_project(changed.model_dump_json().encode())
    assert isinstance(reopened, WBAnalysisProject)
    replanned = replan_quant_lanes(image.source, reopened, "source")
    request = replanned.analyses[0].request
    lane = request.lanes[0]
    assert lane.roi == roi and len(lane.bands) == 1
    assert lane.bands[0].bounds == BandBounds(0, roi.y1 - roi.y0 - 1)
    assert "whole_lane_smear@1" in lane.bands[0].detection_notes
    assert request.lanes[1] == configured.analyses[0].request.lanes[1]
    assert analyze_annotations(image, request).lanes[0].bands[0].signal == pytest.approx(1800)


def test_switch_explicit_lanes_to_same_envelope_grid_changes_policy(tmp_path: Path) -> None:
    image, project, target = example(tmp_path)
    configured = configure_manual_quantification(image, project, target)
    grid = configure_manual_quantification(image, configured, replace(target, lane_rois=()))
    assert grid is not configured
    assert grid.analyses[0].request.geometry_policy == "anchored_context@1"
    assert grid.analyses[0].request.quant_policy == "anchored_background@1"
    assert configure_manual_quantification(image, grid, replace(target, lane_rois=())) is grid


def test_invalid_explicit_lanes_rejected(tmp_path: Path) -> None:
    _, _, target = example(tmp_path)
    with pytest.raises(ValueError, match="重叠"):
        replace(target, lane_rois=(target.lane_rois[0], LaneROI("source:02", 20, 0, 40, 120)))
    with pytest.raises(ValueError, match="数量"):
        replace(target, lane_rois=target.lane_rois[:1])


def test_whole_smear_excludes_confirmed_frame_without_selecting_one_peak(tmp_path: Path) -> None:
    image, project, target = example(tmp_path)
    raw = image.pixels.copy()
    raw[:2, :] = 0
    raw[-2:, :] = 0
    framed = tmp_path / "framed.tif"
    tifffile.imwrite(framed, raw)
    loaded = load_tiff(framed)
    old = project.rows[0]
    assert old.source is not None
    asset = old.source.model_copy(
        update={
            "sha256": loaded.sha256,
            "size_bytes": framed.stat().st_size,
            "relative_path": "inputs/framed.tif",
        }
    )
    row = old.model_copy(update={"source": asset, "filename": framed.name})
    project = project.model_copy(update={"rows": (row,)})
    target = replace(target, source_sha256=loaded.sha256, measurement_mode="smear")
    configured = configure_manual_quantification(loaded, project, target)
    request = configured.analyses[0].request
    assert all(lane.roi.y0 >= 2 and lane.roi.y1 <= 118 for lane in request.lanes)
    assert all(len(lane.bands) == 1 for lane in request.lanes)
    result = analyze_annotations(loaded, request)
    assert [
        lane.bands[0].measurement.signal for lane in result.lanes if lane.bands[0].measurement
    ] == pytest.approx([1800, 1800])
