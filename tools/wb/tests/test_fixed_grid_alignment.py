"""Known-N/known-width rows need not separate into N connected components."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from wb_tool.api import (
    AutoWBSettings,
    LaneROI,
    WBIntakeCropProject,
    claim_intake_workflow_step,
    intake_workflow_digest,
    propose_intake_crop,
    record_intake_crop_proposal,
    review_intake_crop,
)
from wb_tool.domain.reliable_geometry import detect_reliable_geometry

from tools.wb.tests.test_intake_automatic_crop import prepared


def test_reproposing_reviewed_grid_keeps_asymmetric_signal_ownership(tmp_path: Path) -> None:
    raw = np.full((240, 600), 100, dtype=np.uint16)
    raw[45:195, 60:540] = 50000
    raw[116:125, 210:330] = 8000
    path = tmp_path / "reviewed-asymmetric.tiff"
    tifffile.imwrite(path, raw)
    project, ticket = claim_intake_workflow_step(prepared(path, count=2), session_key="manual-grid")
    assert isinstance(project, WBIntakeCropProject) and ticket
    project = record_intake_crop_proposal(
        project, ticket, propose_intake_crop(str(path), project, "r")
    )
    reviewed = review_intake_crop(
        project,
        "r",
        LaneROI("r", 200, 80, 400, 160),
        expected_digest=intake_workflow_digest(project),
    )
    prior = reviewed.intake_crops[0]
    frozen = reviewed.model_dump_json()
    new = propose_intake_crop(str(path), reviewed, "r")
    assert new == prior and new.reviewed
    assert new.slots[0].roi and new.slots[0].roi.x1 == 300
    assert new.slots[1].roi and new.slots[1].roi.x0 == 300
    assert reviewed.model_dump_json() == frozen


@pytest.mark.parametrize("count", [2, 5])
@pytest.mark.parametrize("angle", [-9.0, 0.0, 9.0])
@pytest.mark.parametrize("bridge_value", [8000, 45000])
def test_connected_support_uses_fixed_template_without_counting_blobs(
    count: int, angle: float, bridge_value: int
) -> None:
    yy, xx = np.mgrid[:300, :700]
    c, s = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
    u, v = (xx - 350) * c + (yy - 150) * s, -(xx - 350) * s + (yy - 150) * c
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[(abs(xx - 350) < 230) & (abs(yy - 150) < 100)] = 50000
    raw = guide.copy()
    connected = (abs(u) < count * 25 - 9) & (abs(v) < 3)
    raw[connected] = bridge_value
    support = connected.copy()
    for center in (np.arange(count) - (count - 1) / 2) * 50:
        band = (abs(u - center) < 16) & (abs(v) < 5)
        raw[band] = 8000
        support |= band
    before = raw.copy()
    result = detect_reliable_geometry(raw, guide, AutoWBSettings(lane_count=count), lane_width=50)
    assert len(result.candidates) == 1, result.flags
    crop = result.candidates[0]
    assert crop.display_frame and crop.display_frame.width == count * 50
    assert crop.display_frame.height == 40
    assert abs(crop.display_frame.angle_degrees - angle) < 1
    assert len(crop.lane_rois) == count
    ownership = np.zeros(raw.shape, dtype=np.uint8)
    for r in crop.lane_rois:
        ownership[r.y0 : r.y1, r.x0 : r.x1] += 1
    assert np.all(ownership[support] == 1)
    assert ownership.max() == 1
    assert np.array_equal(raw, before)


def test_same_merged_strip_without_width_does_not_invent_two_lanes() -> None:
    raw = np.full((240, 600), 100, dtype=np.uint16)
    raw[55:185, 70:530] = 50000
    raw[116:125, 260:341] = 8000
    result = detect_reliable_geometry(raw, raw, AutoWBSettings(lane_count=2))
    assert not result.candidates


def test_verified_width_not_replaced_by_108_pixel_peak_spacing() -> None:
    raw = np.full((240, 600), 100, dtype=np.uint16)
    raw[55:185, 70:530] = 50000
    for x in (246, 354):
        raw[116:125, x - 16 : x + 16] = 8000
    result = detect_reliable_geometry(raw, raw, AutoWBSettings(lane_count=2), lane_width=115)
    assert result.candidates, result.flags
    frame = result.candidates[0].display_frame
    assert frame and (frame.width, frame.height) == (230, 92)


@pytest.mark.parametrize("count", [2, 4, 5])
@pytest.mark.parametrize("band_width", [25, 32])
def test_width_estimate_cannot_absorb_an_extra_complete_weak_sample(
    count: int, band_width: int
) -> None:
    raw = np.full((240, 600), 100, dtype=np.uint16)
    raw[55:185, 70:530] = 50000
    for i in range(count + 1):
        x = 200 + 50 * i
        raw[116:125, x - band_width // 2 : x - band_width // 2 + band_width] = (
            49000 if i == count else 8000
        )
    result = detect_reliable_geometry(
        raw, raw, AutoWBSettings(lane_count=count), lane_width=50, width_is_estimate=True
    )
    assert not result.candidates


def test_known_frame_checks_local_extent_not_axis_aligned_width() -> None:
    yy, xx = np.mgrid[:300, :600]
    angle = np.deg2rad(9)
    u = (xx - 300) * np.cos(angle) + (yy - 150) * np.sin(angle)
    v = -(xx - 300) * np.sin(angle) + (yy - 150) * np.cos(angle)
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[50:250, 70:530] = 50000
    raw = guide.copy()
    support = (abs(u) < 99) & (abs(v) < 20)
    raw[support] = 8000
    # Half-open raster width includes both endpoint pixels.
    assert np.ptp(np.nonzero(support)[1]) + 1 > 200
    detection = detect_reliable_geometry(raw, guide, AutoWBSettings(lane_count=2), lane_width=100)
    assert detection.candidates, detection.flags
    frame = detection.candidates[0].display_frame
    assert frame and frame.width == 200 and frame.height == 80


def test_connector_between_two_complete_rows_does_not_prove_one_target() -> None:
    guide = np.full((240, 600), 100, dtype=np.uint16)
    guide[45:195, 60:540] = 50000
    raw = guide.copy()
    raw[108:113, 210:390] = 8000
    raw[128:133, 210:390] = 8000
    raw[113:128, 299:301] = 8000
    detection = detect_reliable_geometry(raw, guide, AutoWBSettings(lane_count=2), lane_width=100)
    assert not detection.candidates
    assert "signal_rows_ambiguous" in detection.flags


def test_bbox_fragment_keeps_local_quality_review_in_measurement(tmp_path: Path) -> None:
    from dataclasses import replace

    from wb_tool.api import analyze_annotations, load_tiff, suggest_analysis_for_crop
    from wb_tool.application.intake_crop import make_intake_crop_evidence
    from wb_tool.application.intake_figure import (
        apply_intake_sampling_review,
        intake_sampling_current,
    )

    guide = np.full((300, 600), 100, dtype=np.uint16)
    guide[50:250, 80:520] = 50000
    raw = guide.copy()
    for x in (225, 275, 325, 375):
        raw[146:154, x - 16 : x + 16] = 8000
    raw[132:147, 210:212] = 8000
    raw[134:137, 217:229] = 49000
    detection = detect_reliable_geometry(raw, guide, AutoWBSettings(lane_count=4), lane_width=50)
    assert detection.candidates, detection.flags
    assert 1 in detection.review_positions
    path = tmp_path / "local-second-target.tiff"
    tifffile.imwrite(path, raw)
    image = load_tiff(path)
    evidence = make_intake_crop_evidence(
        prepared(path, count=4),
        "r",
        detection,
        sampling_limits=detection.sampling_limits,
        review_positions=detection.review_positions,
    )
    assert evidence.crop
    request = suggest_analysis_for_crop(
        image,
        crop=evidence.crop,
        lane_count=4,
        revision=0,
        lane_rois=detection.candidates[0].lane_rois,
        context_limits=detection.sampling_limits,
        quant_policy="anchored_background@1",
    )
    checked = apply_intake_sampling_review(evidence, request)
    assert intake_sampling_current(evidence, checked)
    assert not intake_sampling_current(evidence, request)
    result = analyze_annotations(image, checked)
    band = result.lanes[0].bands[0]
    assert band.status == "quality_review" and band.measurement is not None
    assert "boundary_review:local_signal_ambiguity" in band.quality_flags
    assert evidence.fixed_grid
    tighter = evidence.model_copy(
        update={
            "fixed_grid": evidence.fixed_grid.model_copy(
                update={"sampling_limits": tuple(lane.roi for lane in checked.lanes)}
            )
        }
    )
    first = checked.lanes[0]
    widened = replace(
        first, roi=replace(first.roi, y0=first.roi.y0 - 1), context_expansion_percent=25
    )
    assert not intake_sampling_current(
        tighter, replace(checked, lanes=(widened, *checked.lanes[1:]))
    )
