"""Display standardization is explicit and retains original quantitative evidence."""

import json
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.api import (
    FigureComposition,
    FigureLayoutStyle,
    ImageInputError,
    LaneROI,
    compute_lane_profiles,
    export_figure_bundle,
    export_figure_image,
    initial_composition,
    load_tiff,
    make_row_analysis,
    plan_laboratory_layout,
    read_figure_project,
    render_figure,
    with_figure_layout,
)

from tools.wb.tests.test_figure_project import sample


def mixed_resolution(tmp_path: Path):
    base, paths = sample(tmp_path)
    pixels = np.arange(80 * 72, dtype=np.uint8).reshape(80, 72)
    path = Path(paths[1].path)
    tifffile.imwrite(path, pixels)
    data = path.read_bytes()
    digest = sha256(data).hexdigest()
    old = base.rows[1]
    assert old.source is not None
    row = old.model_copy(
        update={
            "width": 72,
            "height": 80,
            "bit_depth": 8,
            "roi": LaneROI("r1", 0, 10, 72, 50),
            "source": AssetRef(
                asset_id=old.source.asset_id,
                relative_path=old.source.relative_path,
                sha256=digest,
                size_bytes=len(data),
            ),
        }
    )
    base = base.model_copy(update={"rows": (base.rows[0], row, *base.rows[2:])})
    paths = (paths[0], type(paths[1])(digest, str(path)), *paths[2:])
    return with_figure_layout(
        base,
        initial_composition(base),
        FigureLayoutStyle(heading_size=12, display_policy="standard_lane_ratio@1"),
    ), paths


def test_mixed_resolution_standard_rows_preserve_measurement_and_provenance(tmp_path: Path) -> None:
    project, paths = mixed_resolution(tmp_path)
    before = {p.path: Path(p.path).read_bytes() for p in paths}
    originals = {p.sha256: load_tiff(p.path) for p in paths}
    row = project.rows[1]
    assert row.source is not None and row.roi is not None
    profile = compute_lane_profiles(originals[row.source.sha256].pixels, row.roi, "dark")
    analysis = make_row_analysis(project, row.row_id, "dark")
    rendered = render_figure(project, paths)
    manifest = json.loads(rendered.manifest_json)
    assert manifest["operation"] == "figure_segmented_geometry@2"
    assert manifest["display_policy"] == "standard_lane_ratio@1"
    assert manifest["resampling"] == "pillow_rgb8_lanczos@1"
    assert manifest["row_height"] == 96
    fig1 = [r for r in manifest["rows"] if r["figure"] == "Fig1"]
    assert all(
        [r["output_box"][2] - r["output_box"][0], r["output_box"][3] - r["output_box"][1]]
        == [360, 96]
        for r in fig1
    )
    rgb = np.frombuffer(rendered.rgb, np.uint8).reshape(rendered.height, rendered.width, 3)
    for record in manifest["rows"]:
        if record["source_sha256"] is None:
            assert record["status"] == "missing" and record["roi"] is None
            continue
        roi = record["roi"]
        original = originals[record["source_sha256"]]
        crop = original.pixels[roi["y0"] : roi["y1"], roi["x0"] : roi["x1"]]
        assert record["original_roi_size"] == [crop.shape[1], crop.shape[0]]
        x0, y0, x1, y1 = record["output_box"]
        assert record["display_rgb_sha256"] == sha256(rgb[y0:y1, x0:x1].tobytes()).hexdigest()
    assert fig1[0]["original_roi_size"] == [36, 20]
    assert fig1[1]["original_roi_size"] == [72, 40]
    assert make_row_analysis(project, row.row_id, "dark") == analysis
    assert compute_lane_profiles(originals[row.source.sha256].pixels, row.roi, "dark") == profile
    assert all(Path(path).read_bytes() == data for path, data in before.items())
    assert read_figure_project(project.model_dump_json().encode()) == project
    target = tmp_path / "standard.tiff"
    export_figure_image(project, paths, str(target))
    with pytest.raises(ImageInputError, match="显示拼图"):
        load_tiff(target)
    archive_path = tmp_path / "standard.zip"
    export_figure_bundle(project, paths, str(archive_path))
    with ZipFile(archive_path) as archive:
        for index, source_row in enumerate(project.rows):
            if source_row.source is None or source_row.roi is None:
                continue
            roi = source_row.roi
            raw = originals[source_row.source.sha256].pixels
            with tifffile.TiffFile(BytesIO(archive.read(f"crops/{index + 1:04d}.tif"))) as image:
                np.testing.assert_array_equal(
                    image.asarray(), raw[roi.y0 : roi.y1, roi.x0 : roi.x1]
                )
    # Provenance alone must protect quantitative admission even if Software is stripped.
    stripped = tmp_path / "description-only.tiff"
    tifffile.imwrite(
        stripped, rgb, photometric="rgb", description=rendered.manifest_json, software="external"
    )
    with pytest.raises(ImageInputError, match="显示拼图"):
        load_tiff(stripped)


def test_native_default_remains_strict_and_standard_budget_applies(tmp_path: Path) -> None:
    project, paths = mixed_resolution(tmp_path)
    native = project.model_copy(update={"layout_style": FigureLayoutStyle(heading_size=12)})
    assert native.layout_style.display_policy == "native_samples@1"
    with pytest.raises(ValueError, match="宽度/N一致"):
        render_figure(native, paths)
    # Changing N remains an error, even when native widths no longer need to agree.
    bad = project.model_copy(
        update={
            "rows": (
                project.rows[0],
                project.rows[1].model_copy(update={"lane_count": 4}),
                *project.rows[2:],
            )
        }
    )
    bad = with_figure_layout(bad, initial_composition(bad))
    with pytest.raises(ValueError, match="宽度/N一致"):
        plan_laboratory_layout(bad)
    # One Fig can use unit1200 for a 960 x 1200N display row.
    single = project.model_copy(update={"rows": project.rows[:2], "figure_order": ("Fig1",)})
    single = with_figure_layout(
        single,
        initial_composition(single),
        FigureLayoutStyle(heading_size=12, display_policy="standard_lane_ratio@1", lane_unit=1200),
    )
    assert plan_laboratory_layout(single).lines[0].segments[0].output_box[2:] == (3715, 1007)
    # Larger combined projects must still fit the same output budget.
    huge = project.model_copy(
        update={
            "layout_style": FigureLayoutStyle(
                heading_size=12, display_policy="standard_lane_ratio@1", lane_unit=1200
            )
        }
    )
    huge = huge.model_copy(
        update={
            "rows": (
                *huge.rows,
                *(huge.rows[-1].model_copy(update={"row_id": f"missing-{i}"}) for i in range(4)),
            )
        }
    )
    huge = with_figure_layout(huge, initial_composition(huge))
    with pytest.raises(ValueError, match="3200万"):
        plan_laboratory_layout(huge)
    old = {
        "schema_version": 1,
        "heading_size": 12,
        "segment_gap": 8,
        "label_alignment": "right",
        "flow": "columns",
    }
    assert FigureLayoutStyle.model_validate(old).display_policy == "native_samples@1"
    with pytest.raises(ValueError):
        FigureLayoutStyle(display_policy="standard_lane_ratio@1", lane_unit=121)


def test_style_schema_is_current() -> None:
    schema = Path(__file__).resolve().parents[3] / "docs/contracts/wb-layout-style-v1.schema.json"
    assert json.loads(schema.read_text(encoding="utf-8")) == FigureLayoutStyle.model_json_schema()
    schema = schema.with_name("wb-figure-composition-v1.schema.json")
    assert json.loads(schema.read_text(encoding="utf-8")) == FigureComposition.model_json_schema()


def test_rotated_frame_affine_and_bounds_leave_original_uint16_unchanged(tmp_path: Path) -> None:
    from wb_tool.api import DisplayFrame, FigureSlice

    project, paths = mixed_resolution(tmp_path)
    frame = DisplayFrame(center_x=18, center_y=15, width=20, height=8, angle_degrees=15)
    parts = list(project.composition.slices)
    parts[0] = parts[0].model_copy(update={"display_frame": frame})
    project = project.model_copy(
        update={"composition": project.composition.model_copy(update={"slices": tuple(parts)})}
    )
    before = Path(paths[0].path).read_bytes()
    original = load_tiff(paths[0].path)
    pixels_before = original.pixels.tobytes()
    output = render_figure(project, paths)
    record = next(r for r in json.loads(output.manifest_json)["rows"] if r["row_id"] == "r0")
    assert record["display_frame"] == frame.model_dump(mode="json")
    assert record["resampling"] == "pillow_rgb8_affine_bilinear@1"
    affine = np.asarray(record["source_to_output"])
    x0, y0, x1, y1 = record["output_box"]
    np.testing.assert_allclose(
        affine @ [frame.center_x, frame.center_y, 1], [(x0 + x1) / 2, (y0 + y1) / 2], atol=1e-10
    )
    for source_corner, target in zip(
        frame.corners(), ((x0, y0), (x1, y0), (x1, y1), (x0, y1)), strict=True
    ):
        np.testing.assert_allclose(affine @ [*source_corner, 1], target, atol=1e-10)
    rgb = np.frombuffer(output.rgb, np.uint8).reshape(output.height, output.width, 3)
    assert np.all(rgb[y0:y1, x0:x1] > 0)  # no outside-image black fill
    assert original.pixels.dtype == np.uint16 and original.pixels.tobytes() == pixels_before
    assert Path(paths[0].path).read_bytes() == before
    native = project.model_copy(update={"layout_style": FigureLayoutStyle(heading_size=12)})
    with pytest.raises(ValueError, match="仅支持"):
        plan_laboratory_layout(native)
    parts[0] = parts[0].model_copy(
        update={"display_frame": frame.model_copy(update={"center_x": -1.0})}
    )
    invalid = project.model_copy(
        update={"composition": project.composition.model_copy(update={"slices": tuple(parts)})}
    )
    with pytest.raises(ValueError, match="超出原图ROI"):
        render_figure(invalid, paths)
    old = {
        "row_id": "r0",
        "figure": "Fig1",
        "line": 1,
        "position": 1,
        "first_lane": 1,
        "last_lane": 3,
    }
    assert FigureSlice.model_validate(old).display_frame is None
    for values in (
        {"width": 0},
        {"angle_degrees": 31},
        {"center_x": float("nan")},
        {"center_y": float("inf")},
    ):
        with pytest.raises(ValueError):
            DisplayFrame.model_validate({**frame.model_dump(), **values})


def test_rotated_frame_cannot_repeat_whole_row_under_segment_lane_claims(tmp_path: Path) -> None:
    from wb_tool.api import DisplayFrame, FigureSlice

    project, paths = mixed_resolution(tmp_path)
    frame = DisplayFrame(center_x=18, center_y=15, width=36, height=20, angle_degrees=0)
    slices: list[FigureSlice] = []
    for segment in project.composition.slices:
        if segment.figure == "Fig1":
            slices.extend(
                (
                    segment.model_copy(
                        update={
                            "last_lane": 1,
                            "display_frame": frame if segment.row_id == "r0" else None,
                        }
                    ),
                    segment.model_copy(
                        update={
                            "first_lane": 2,
                            "position": 2,
                            "display_frame": frame if segment.row_id == "r0" else None,
                        }
                    ),
                )
            )
        else:
            slices.append(segment)
    bad = project.model_copy(
        update={"composition": project.composition.model_copy(update={"slices": tuple(slices)})}
    )
    with pytest.raises(ValueError, match="仅允许完整原图行"):
        render_figure(bad, paths)
