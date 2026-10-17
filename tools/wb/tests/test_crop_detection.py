"""Synthetic geometry ground truth; suggestions never alter original samples or define identity."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import TypedDict
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.api import (
    CropDetectionSettings,
    CropSuggestion,
    FigureRow,
    FigureSourcePath,
    FigureTemplate,
    LaneROI,
    WBFigureProject,
    WBReviewProject,
    apply_crop_suggestion,
    detect_crop_candidates,
    export_figure_bundle,
    read_figure_project,
    record_crop_suggestion,
    suggest_crops,
)


def blot(
    *, blank: bool = False, light: bool = False, noise: bool = False
) -> np.ndarray[tuple[int, int], np.dtype[np.uint16]]:
    image = np.full((220, 300), 1000, dtype=np.uint16)
    image[20:200, 20:260] = 50000
    # Marker centre50; samples110,170,230. Known pitch60, sample region80..260.
    image[45:53, 40:60] = 22000
    image[130:138, 40:60] = 22000
    for centre in (110, 170, 230):
        if not (blank and centre == 170):
            image[77:87, centre - 15 : centre + 15] = 20000
        image[145:153, centre - 15 : centre + 15] = 34000
    if noise:
        rng = np.random.default_rng(734)
        image = np.clip(
            image.astype(np.float64) + rng.normal(0, 180, image.shape), 0, 65535
        ).astype(np.uint16)
    return 65535 - image if light else image


@pytest.mark.parametrize(
    "blank,light,noise", [(False, False, False), (True, False, False), (True, True, True)]
)
def test_membrane_marker_grid_and_two_rows(blank: bool, light: bool, noise: bool) -> None:
    image = blot(blank=blank, light=light, noise=noise)
    original = image.copy()
    result = detect_crop_candidates(
        image, CropDetectionSettings(3, 30, "light" if light else "dark")
    )
    assert result.membrane == LaneROI("membrane", 20, 20, 260, 200)
    assert result.sample_region is not None and result.marker is not None
    assert abs(result.sample_region.x0 - 80) <= 2
    assert abs(result.sample_region.x1 - 260) <= 2
    assert result.marker.x1 == result.sample_region.x0
    assert len(result.candidates) == 2, result
    assert sorted(c.peak_y for c in result.candidates) == pytest.approx([81, 148], abs=2)
    assert all(c.roi.y1 - c.roi.y0 == 30 for c in result.candidates)
    top = min(result.candidates, key=lambda c: c.peak_y)
    assert top.possible_empty_lanes == ((2,) if blank else ())
    assert len(top.lane_snr) == 3
    assert "left_marker_identity_unconfirmed" in result.flags
    np.testing.assert_array_equal(image, original)


def test_flat_noise_and_manual_region_without_marker() -> None:
    for image in (
        np.full((220, 300), 40000, dtype=np.uint16),
        np.random.default_rng(12).integers(39500, 40500, (220, 300), dtype=np.uint16),
    ):
        result = detect_crop_candidates(image, CropDetectionSettings(3, 30, "dark"))
        assert result.membrane is None and not result.candidates
    pixels = blot()[20:200, 80:260]
    settings = CropDetectionSettings(
        3, 30, "dark", left_marker=False, membrane_hint=LaneROI("manual", 0, 0, 180, 180)
    )
    result = detect_crop_candidates(pixels, settings)
    assert result.marker is None
    assert result.sample_region == LaneROI("samples", 0, 0, 180, 180)
    assert len(result.candidates) == 2
    with pytest.raises(ValueError, match="超出"):
        detect_crop_candidates(
            pixels, replace(settings, membrane_hint=LaneROI("bad", 0, 0, 181, 180))
        )


def test_cancellation_and_invalid_parameters() -> None:
    with pytest.raises(ValueError, match="取消"):
        detect_crop_candidates(blot(), CropDetectionSettings(3, 30, "dark"), cancelled=lambda: True)
    with pytest.raises(ValueError):
        CropDetectionSettings(True, 30, "dark")
    with pytest.raises(ValueError):
        CropDetectionSettings(3, 30, "dark", min_snr=float("nan"))


def test_edge_artifact_is_explicit_and_weak_saturated_slots_preserve_n() -> None:
    image = blot()
    image[20:23, 80:260] = 25000
    image[77:87, 155:185] = 49994
    image[77:87, 95:125] = 0
    settings = CropDetectionSettings(3, 30, "dark", membrane_hint=LaneROI("mem", 20, 20, 260, 200))
    result = detect_crop_candidates(image, settings)
    assert "membrane_edge_signal_ignored" in result.flags
    assert len(result.candidates) == 2
    top = min(result.candidates, key=lambda c: c.peak_y)
    assert top.weak_lanes == (2,)
    assert "dtype_limits_review" in top.flags
    assert len(top.lane_snr) == 3
    included = detect_crop_candidates(image, replace(settings, include_membrane_edges=True))
    assert any(c.peak_y < 30 for c in included.candidates)
    assert "membrane_edge_signal_ignored" not in included.flags


def test_multiple_membranes_and_cooperative_cancel_inside_algorithm() -> None:
    image = np.concatenate((blot(), blot()), axis=1)
    result = detect_crop_candidates(image, CropDetectionSettings(3, 30, "dark"))
    assert "multiple_membranes" in result.flags
    calls = 0

    def cancelled() -> bool:
        nonlocal calls
        calls += 1
        return calls >= 4

    with pytest.raises(ValueError, match="取消"):
        detect_crop_candidates(image, CropDetectionSettings(3, 30, "dark"), cancelled=cancelled)
    assert calls == 4


def test_suggestion_source_roundtrip_apply_restore_and_export(tmp_path: Path) -> None:
    source = tmp_path / "source.tif"
    tifffile.imwrite(source, blot(blank=True))
    original = source.read_bytes()
    sha = sha256(original).hexdigest()
    row = FigureRow(
        row_id="r1",
        source=AssetRef(
            asset_id="a1", relative_path="inputs/a1.tif", sha256=sha, size_bytes=len(original)
        ),
        width=300,
        height=220,
        bit_depth=16,
        lane_count=3,
        protein="AKT",
        empty_lanes=(3,),
    )
    project = WBFigureProject(
        project_id="p1",
        rows=(row,),
        figure_order=("Fig1",),
        template=FigureTemplate(crop_height=30),
    )
    legacy = project.model_dump_json().encode()
    assert read_figure_project(legacy) == project
    settings = CropDetectionSettings(3, 30, "dark")
    with pytest.raises(ValueError, match="摘要"):
        suggest_crops(str(source), "f" * 64, "r1", 0, settings)
    suggestion = suggest_crops(str(source), sha, "r1", 0, settings)
    reviewed = record_crop_suggestion(project, suggestion)
    assert reviewed.schema_version == 2 and reviewed.rows[0].roi is None
    with pytest.raises(ValueError):
        WBFigureProject.from_bytes(reviewed.model_dump_json().encode())
    restored = read_figure_project(reviewed.model_dump_json().encode())
    assert restored == reviewed
    applied = apply_crop_suggestion(restored, "r1", 1)
    assert applied.rows[0].roi is not None and not applied.rows[0].reviewed
    assert applied.rows[0].empty_lanes == (3,)  # Suggestions never rewrite explicit metadata.
    with pytest.raises(ValueError, match="已审核"):
        applied.rows[0].quantitative_lanes()
    assert applied.suggestions[0].selected_index == 1
    reapplied = apply_crop_suggestion(applied, "r1", 0)
    assert reapplied.rows[0].roi != applied.rows[0].roi
    # Reject stale parameters without losing old evidence.
    changed = reapplied.model_copy(update={"template": FigureTemplate(crop_height=40)})
    assert read_figure_project(changed.model_dump_json().encode()) == changed
    with pytest.raises(ValueError, match="重新检测"):
        apply_crop_suggestion(changed, "r1", 0)
    accepted = reapplied.model_copy(
        update={"rows": (reapplied.rows[0].model_copy(update={"reviewed": True}),)}
    )
    target = tmp_path / "figure.zip"
    export_figure_bundle(accepted, (FigureSourcePath(sha, str(source)),), str(target))
    with ZipFile(target) as archive:
        assert read_figure_project(archive.read("project.json")) == accepted
    assert source.read_bytes() == original


class SuggestionArguments(TypedDict):
    row_id: str
    source_sha256: str
    source_revision: int
    settings: CropDetectionSettings


def test_suggestion_validation_rejects_forged_identity_geometry_and_status() -> None:
    settings = CropDetectionSettings(3, 30, "dark")
    detection = detect_crop_candidates(blot(), settings)
    data: SuggestionArguments = {
        "row_id": "r1",
        "source_sha256": "1" * 64,
        "source_revision": 0,
        "settings": settings,
    }
    candidate = detection.candidates[0]
    for result in (
        replace(detection, width=0),
        replace(detection, settings=replace(settings, lane_count=2)),
        replace(detection, candidates=(replace(candidate, lane_snr=(1.0, 2.0, 3.0)),)),
        replace(detection, candidates=(replace(candidate, roi=LaneROI("bad", 0, 1, 100, 31)),)),
        replace(detection, candidates=(replace(candidate, possible_empty_lanes=(1,)),)),
    ):
        with pytest.raises(ValueError):
            CropSuggestion(**data, result=result)
    with pytest.raises(ValueError):
        CropSuggestion(**data)
    with pytest.raises(ValueError):
        CropSuggestion(**data, error="bad source", selected_index=0)
    with pytest.raises(ValueError, match="身份"):
        WBReviewProject(project_id="p", suggestions=(CropSuggestion(**data, error="bad"),))
    valid = CropSuggestion(**data, result=detection)
    raw = valid.model_dump_json().encode()
    with pytest.raises(ValueError, match="重复"):
        CropSuggestion.from_bytes(raw.replace(b'"row_id":"r1"', b'"row_id":"r1","row_id":"r1"'))
