"""Manual targets use existing free-height persistence, without automatic crops."""

from dataclasses import replace
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.api import (
    AutomaticRowEvidence,
    AutoWBSettings,
    Baseline,
    DisplayFrame,
    FigureColumn,
    FigureComposition,
    FigureLayoutStyle,
    FigureRow,
    FigureSlice,
    LaneROI,
    LoadedTiff,
    ManualQuantTarget,
    WBFigureProject,
    WBLayoutProject,
    analysis_is_current,
    analyze_annotations,
    configure_manual_quantification,
    load_tiff,
    read_figure_project,
    update_quant_lane,
    with_automatic_rows,
    with_figure_layout,
)


def original(tmp_path: Path, row_id: str, peak: int = 40) -> tuple[LoadedTiff, FigureRow]:
    profile = 3000 + np.arange(160) * 10
    profile[peak : peak + 20] += 1000
    values = np.repeat(profile.astype(np.uint16)[:, None], 8, axis=1)
    path = tmp_path / f"{row_id}.tiff"
    tifffile.imwrite(path, values)
    image = load_tiff(path)
    asset = AssetRef(
        asset_id=row_id,
        relative_path=f"inputs/{row_id}.tiff",
        sha256=image.sha256,
        size_bytes=path.stat().st_size,
    )
    return image, FigureRow(
        row_id=row_id, source=asset, filename=path.name, width=8, height=160, bit_depth=16
    )


def target(image: LoadedTiff, row: FigureRow, y0: int = 38, y1: int = 62) -> ManualQuantTarget:
    return ManualQuantTarget(image.sha256, 0, LaneROI(row.row_id, 0, y0, 8, y1), 2, "light")


def test_two_free_height_targets_measure_and_roundtrip_without_composition(tmp_path: Path) -> None:
    first, a = original(tmp_path, "a")
    second, b = original(tmp_path, "b", peak=60)
    before = [image.source.read_bytes() for image in (first, second)]
    initial = WBFigureProject(project_id="p", rows=(a, b), figure_order=("Fig1",))
    one = configure_manual_quantification(first, initial, target(first, a))
    two = configure_manual_quantification(second, one, target(second, b, 55, 105))
    assert isinstance(two, WBLayoutProject) and two.schema_version == 7
    assert two.template == initial.template and two.template.crop_height == 60
    assert not two.composition.slices
    assert [two.crop_height_for(row) for row in two.rows] == [24, 50]
    restored = read_figure_project(two.model_dump_json().encode())
    assert restored == two and isinstance(restored, WBLayoutProject)
    for image, plan in zip((first, second), restored.analyses, strict=True):
        assert analysis_is_current(restored, plan)
        result = analyze_annotations(image, plan.request)
        assert len(result.lanes) == 2
        assert all(lane.bands[0].status == "valid" for lane in result.lanes)
        assert [lane.bands[0].signal for lane in result.lanes] == pytest.approx([20000, 20000])
    assert [image.source.read_bytes() for image in (first, second)] == before
    assert initial.rows == (a, b) and all(row.roi is None for row in initial.rows)


@pytest.mark.parametrize("count", [True, 2.5, 0, 97])
def test_lane_count_is_an_explicit_bounded_integer(tmp_path: Path, count: object) -> None:
    image, row = original(tmp_path, "source")
    with pytest.raises(ValueError, match="泳道数"):
        replace(target(image, row), lane_count=cast(int, count))


def test_stale_source_revision_outside_target_and_cancel_are_rejected(tmp_path: Path) -> None:
    image, row = original(tmp_path, "source")
    project = WBFigureProject(project_id="p", rows=(row,), figure_order=("Fig1",))
    requested = target(image, row)
    for invalid in (
        replace(requested, source_sha256="f" * 64),
        replace(requested, revision=1),
        replace(requested, roi=LaneROI(row.row_id, 0, 140, 8, 170)),
    ):
        with pytest.raises(ValueError):
            configure_manual_quantification(image, project, invalid)
    with pytest.raises(ValueError, match="取消"):
        configure_manual_quantification(image, project, requested, cancelled=lambda: True)
    assert project.rows[0].roi is None


def test_unchanged_manual_target_keeps_user_baseline(tmp_path: Path) -> None:
    image, row = original(tmp_path, "source")
    requested = target(image, row)
    project = configure_manual_quantification(
        image, WBFigureProject(project_id="p", rows=(row,), figure_order=("Fig1",)), requested
    )
    lane = project.analyses[0].request.lanes[0]
    edited = update_quant_lane(project, row.row_id, lane.roi.lane_id, baseline=Baseline(1, 2))
    assert configure_manual_quantification(image, edited, requested) is edited
    reset = configure_manual_quantification(image, edited, replace(requested, reset_bounds=True))
    assert reset.analyses[0].request == project.analyses[0].request
    assert reset.rows == project.rows


def test_incompatible_existing_segments_fail_without_partial_changes(tmp_path: Path) -> None:
    image, row = original(tmp_path, "source")
    requested = replace(target(image, row), lane_count=4)
    initial = WBFigureProject(project_id="p", rows=(row,), figure_order=("Fig1",))
    configured = configure_manual_quantification(image, initial, requested)
    composition = FigureComposition(
        columns=(FigureColumn(figure="Fig1", column=1),),
        slices=(
            FigureSlice(
                row_id=row.row_id, figure="Fig1", line=1, position=1, first_lane=1, last_lane=2
            ),
            FigureSlice(
                row_id=row.row_id, figure="Fig1", line=2, position=1, first_lane=3, last_lane=4
            ),
        ),
    )
    segmented = with_figure_layout(configured, composition)
    before = segmented.model_dump_json()
    with pytest.raises(ValueError, match="不兼容"):
        configure_manual_quantification(image, segmented, replace(requested, lane_count=3))
    assert segmented.model_dump_json() == before


def test_excluded_lanes_remain_slots_and_never_become_valid_zero(tmp_path: Path) -> None:
    image, row = original(tmp_path, "source")
    requested = replace(target(image, row), empty_lanes=(2,))
    project = configure_manual_quantification(
        image, WBFigureProject(project_id="p", rows=(row,), figure_order=("Fig1",)), requested
    )
    result = analyze_annotations(image, project.analyses[0].request)
    assert len(result.lanes) == 2
    assert result.lanes[0].bands[0].signal == pytest.approx(20000)
    assert result.lanes[1].bands[0].status == "excluded"
    assert result.lanes[1].bands[0].signal is None


def test_manual_geometry_removes_only_its_machine_evidence_and_display_frame(
    tmp_path: Path,
) -> None:
    first, a = original(tmp_path, "a")
    second, b = original(tmp_path, "b", peak=60)
    initial = WBFigureProject(project_id="p", rows=(a, b), figure_order=("Fig1",))
    one = configure_manual_quantification(first, initial, target(first, a))
    two = configure_manual_quantification(second, one, target(second, b, 55, 105))
    frame = DisplayFrame(center_x=4.0, center_y=50.0, width=8.0, height=20.0, angle_degrees=0.0)
    composition = FigureComposition(
        columns=(FigureColumn(figure="Fig1", column=1),),
        slices=(
            FigureSlice(
                row_id="a",
                figure="Fig1",
                line=1,
                position=1,
                first_lane=1,
                last_lane=2,
                display_frame=frame,
            ),
            FigureSlice(row_id="b", figure="Fig1", line=2, position=1, first_lane=1, last_lane=2),
        ),
    )
    layout = with_figure_layout(
        two, composition, FigureLayoutStyle(display_policy="standard_lane_ratio@1")
    )
    evidence = tuple(
        AutomaticRowEvidence(
            row_id=plan.row_id,
            source_sha256=plan.request.source_sha256,
            source_revision=0,
            crop=plan.crop,
            lane_count=2,
            request=plan.request,
            settings=AutoWBSettings(
                polarity="light", lane_count=2, quant_policy="anchored_background@1"
            ),
        )
        for plan in two.analyses
    )
    machine = with_automatic_rows(layout, evidence)
    changed = configure_manual_quantification(first, machine, target(first, a, 30, 70))
    assert changed.schema_version == 8 and isinstance(changed, type(machine))
    assert changed.automatic_rows == (evidence[1],)
    assert changed.rows[1] == machine.rows[1]
    assert changed.analyses[0] == machine.analyses[1]
    assert changed.composition.slices[0].display_frame is None
    assert changed.composition.slices[1] == machine.composition.slices[1]
    assert changed.template == machine.template
    polarity_only = configure_manual_quantification(
        first, machine, replace(target(first, a), polarity="dark")
    )
    assert isinstance(polarity_only, WBLayoutProject)
    assert polarity_only.composition == machine.composition


def test_cancellation_after_planning_begins_does_not_mutate_project(tmp_path: Path) -> None:
    image, row = original(tmp_path, "source")
    project = WBFigureProject(project_id="p", rows=(row,), figure_order=("Fig1",))
    observations: list[bool] = []

    def cancelled() -> bool:
        observations.append(True)
        return len(observations) >= 3

    with pytest.raises(ValueError, match="取消"):
        configure_manual_quantification(image, project, target(image, row), cancelled=cancelled)
    assert len(observations) >= 3 and project.rows == (row,)
