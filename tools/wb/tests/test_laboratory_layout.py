"""Original-coordinate segment layouts, independent pixel expectations and portable evidence."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from platform_runtime.api import Workspace
from wb_tool.api import (
    FigureColumn,
    FigureLayoutStyle,
    FigureSlice,
    FigureSourcePath,
    ImageInputError,
    LaneROI,
    WBLayoutProject,
    analysis_is_current,
    export_figure_bundle,
    export_figure_image,
    initial_composition,
    inspect_project_archive,
    load_ocr_image,
    load_tiff,
    make_row_analysis,
    plan_laboratory_layout,
    project_with_analyses,
    read_figure_project,
    render_figure,
    restore_staged_project,
    stage_project_archive,
    with_figure_layout,
)

from tools.wb.tests.test_figure_project import sample


def laboratory(tmp_path: Path):
    base, paths = sample(tmp_path)
    first = base.rows[0].model_copy(update={"roi": LaneROI("r0", 0, 5, 36, 35)})
    base = base.model_copy(update={"rows": (first, *base.rows[1:])})
    composition = initial_composition(base)
    parts: list[FigureSlice] = []
    for part in composition.slices:
        if part.figure == "Fig1":
            parts.extend(
                (
                    part.model_copy(update={"last_lane": 1}),
                    part.model_copy(update={"position": 2, "first_lane": 2}),
                )
            )
        else:
            parts.append(part)
    return with_figure_layout(
        base,
        composition.model_copy(update={"slices": tuple(parts)}),
        FigureLayoutStyle(heading_size=12),
    ), paths


def test_segment_geometry_original_pixels_labels_and_missing(tmp_path: Path) -> None:
    project, paths = laboratory(tmp_path)
    before = {path.path: Path(path.path).read_bytes() for path in paths}
    layout = plan_laboratory_layout(project)
    assert (layout.width, layout.height) == (366, 176)
    lines = [line for line in layout.lines if line.figure == "Fig1"]
    assert [line.line for line in lines] == [1, 2, 3]
    assert lines[0].segments[0].output_box == (295, 47, 307, 77)
    assert lines[0].segments[1].output_box == (317, 47, 341, 77)
    assert lines[1].segments[0].output_box == (295, 89, 307, 109)
    assert lines[2].segments[0].roi is None
    rendered = render_figure(project, paths)
    rgb = np.frombuffer(rendered.rgb, np.uint8).reshape(rendered.height, rendered.width, 3)
    metadata = json.loads(rendered.manifest_json)
    assert metadata["operation"] == "figure_segmented_geometry@1"
    assert len(metadata["rows"]) == 7
    for record in metadata["rows"]:
        x0, y0, x1, y1 = record["output_box"]
        assert np.all(rgb[y0:y1, x0 - 1] == 0)  # border is outside original samples
        if record["source_sha256"]:
            number = int(record["row_id"][1:])
            roi = record["roi"]
            expected = np.full((y1 - y0, x1 - x0), 100 + number, np.uint8)
            for y in range(8, 13):
                for x in range(12, 18):
                    if roi["x0"] <= x < roi["x1"] and roi["y0"] <= y < roi["y1"]:
                        expected[y - roi["y0"], x - roi["x0"]] = 20 + number
            for channel in range(3):
                np.testing.assert_array_equal(rgb[y0:y1, x0:x1, channel], expected)
        else:
            assert record["status"] == "missing" and record["roi"] is None
    assert np.all(rgb[47:77, 308:316] == 255)  # eight-pixel explicit split boundary
    assert all(Path(path).read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize(
    "fault",
    [
        "omitted",
        "duplicate",
        "reversed",
        "position",
        "figure",
        "name",
        "width",
        "column",
        "review",
        "source",
        "too_tall",
    ],
)
def test_bad_mapping_cannot_render_or_drop_original_lanes(tmp_path: Path, fault: str) -> None:
    project, paths = laboratory(tmp_path)
    parts = list(project.composition.slices)
    rows = list(project.rows)
    if fault == "omitted":
        parts.pop(0)
    elif fault == "duplicate":
        parts.append(parts[0])
    elif fault == "reversed":
        parts[0] = parts[0].model_copy(update={"first_lane": 3, "last_lane": 3})
        parts[1] = parts[1].model_copy(update={"first_lane": 1, "last_lane": 2})
    elif fault == "position":
        parts[0] = parts[0].model_copy(update={"position": 3})
    elif fault == "figure":
        parts[0] = parts[0].model_copy(update={"figure": "Fig99"})
    elif fault == "name":
        # Explicit horizontal merge of different proteins must be rejected.
        rows[1] = rows[1].model_copy(update={"protein": "ERK"})
        parts = [
            part.model_copy(update={"line": 1, "position": part.position + 2})
            if part.row_id == "r1"
            else part
            for part in parts
        ]
    elif fault == "width":
        rows[1] = rows[1].model_copy(update={"roi": LaneROI("r1", 0, 5, 35, 25)})
    elif fault == "column":
        project = project.model_copy(
            update={
                "composition": project.composition.model_copy(
                    update={
                        "columns": (
                            FigureColumn(figure="Fig2", column=3),
                            FigureColumn(figure="Fig1", column=1),
                        )
                    }
                )
            }
        )
    elif fault == "review":
        rows[0] = rows[0].model_copy(update={"reviewed": False})
    elif fault == "source":
        paths = paths[1:]
    elif fault == "too_tall":
        rows[0] = rows[0].model_copy(update={"roi": LaneROI("r0", 0, 0, 36, 5000)})
    project = project.model_copy(
        update={
            "rows": tuple(rows),
            "composition": project.composition.model_copy(update={"slices": tuple(parts)}),
        }
    )
    target = tmp_path / "bad.png"
    with pytest.raises(ValueError):
        export_figure_image(project, paths, str(target))
    assert not target.exists()


def test_variable_height_analysis_and_helper_roundtrip_keep_layout(tmp_path: Path) -> None:
    project, _ = laboratory(tmp_path)
    plan = make_row_analysis(project, "r0", "dark")
    assert plan.crop == LaneROI("r0", 0, 5, 36, 35)
    changed = project_with_analyses(project, (plan,))
    assert isinstance(changed, WBLayoutProject) and changed.composition == project.composition
    assert analysis_is_current(changed, plan)
    # Layout style/unused common height changes do not change the original measurement ROI.
    changed = changed.model_copy(
        update={"template": changed.template.model_copy(update={"crop_height": 55})}
    )
    assert analysis_is_current(changed, plan)
    assert read_figure_project(changed.model_dump_json().encode()) == changed
    changed = changed.model_copy(
        update={
            "rows": (
                changed.rows[0].model_copy(update={"roi": LaneROI("r0", 0, 4, 36, 34)}),
                *changed.rows[1:],
            )
        }
    )
    assert not analysis_is_current(changed, plan)


def test_cross_source_line_and_independent_columns_do_not_stretch(tmp_path: Path) -> None:
    project, _ = laboratory(tmp_path)
    base, _ = sample(tmp_path)
    # Two original rows are explicitly placed side by side; same-name rows are otherwise separate.
    rows = base.rows[:2]
    base = base.model_copy(update={"rows": rows, "figure_order": ("Fig1",)})
    comp = initial_composition(base)
    comp = comp.model_copy(
        update={
            "slices": (comp.slices[0], comp.slices[1].model_copy(update={"line": 1, "position": 2}))
        }
    )
    combined = with_figure_layout(base, comp, FigureLayoutStyle(heading_size=12))
    lines = plan_laboratory_layout(combined).lines
    assert len(lines) == 1 and [p.row.row_id for p in lines[0].segments] == ["r0", "r1"]
    assert [p.roi for p in lines[0].segments] == [row.roi for row in rows]
    # Three panels in two columns: third panel follows the first column's own bottom.
    third_roi = project.rows[2].roi
    assert third_roi is not None
    third = project.rows[2].model_copy(
        update={
            "row_id": "third",
            "figure": "Fig3",
            "roi": replace(third_roi, lane_id="third"),
        }
    )
    project = project.model_copy(
        update={"rows": (*project.rows, third), "figure_order": (*project.figure_order, "Fig3")}
    )
    project = with_figure_layout(
        project, initial_composition(project), FigureLayoutStyle(heading_size=12)
    )
    layout = plan_laboratory_layout(project)
    assert [(p.x, p.y) for p in layout.placements] == [(24, 24), (204, 24), (24, 118)]


def test_direct_tiff_ocr_and_archive_restore_keep_segment_plan(tmp_path: Path) -> None:
    project, paths = laboratory(tmp_path)
    tiff = tmp_path / "display.tiff"
    export_figure_image(project, paths, str(tiff))
    assert load_ocr_image(tiff).pixels.shape == (176, 366)
    with pytest.raises(ImageInputError, match="显示拼图"):
        load_tiff(tiff)
    archive = tmp_path / "project.zip"
    export_figure_bundle(project, paths, str(archive))
    assert inspect_project_archive(str(archive)) == project
    staged = stage_project_archive(str(archive), str(tmp_path / "stage"))
    with Workspace.create(tmp_path / "workspace") as store:
        original = store.import_asset(staged.archive_path, staged.archive_sha256)
        imported = tuple(store.import_asset(item.path, item.sha256) for item in staged.assets)
        restored = restore_staged_project(staged, imported, original)
        assert isinstance(restored, WBLayoutProject)
        assert restored.composition == project.composition and len(restored.archive_sources) == 1
        assert read_figure_project(restored.model_dump_json().encode()) == restored
        sources = tuple(
            FigureSourcePath(asset.sha256, str(store.asset_path(asset))) for asset in imported
        )
        # Display pixels survive local asset reference remapping and history addition.
        assert render_figure(restored, sources).rgb == render_figure(project, paths).rgb
