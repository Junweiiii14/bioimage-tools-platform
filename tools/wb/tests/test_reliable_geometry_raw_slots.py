"""Independent synthetic regressions for reliable geometry: raw slots."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from numpy.typing import NDArray
from PIL import Image
from tool_contracts.api import AssetRef
from wb_tool.api import (
    AutoWBSettings,
    FigureSourcePath,
    WBIntakeCropProject,
    WBIntakeFigureProject,
    accept_automatic_intake_crop,
    analyze_annotations,
    automatic_intake_crop_allowed,
    claim_intake_workflow_step,
    complete_intake_crop,
    export_intake_crop,
    load_tiff,
    prepare_intake_figure,
    propose_intake_crop,
)
from wb_tool.domain.reliable_geometry import detect_reliable_geometry

from tools.wb.tests.test_intake_automatic_crop import prepared


def analytic_bands(
    n: int, angle: float, *, vertical_offset: int = 0
) -> tuple[NDArray[np.uint16], NDArray[np.uint16], list[NDArray[np.bool_]], NDArray[np.bool_]]:
    yy, xx = np.mgrid[:300, :700]
    ca, sa = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
    u = (xx - 350) * ca + (yy - 150) * sa
    v = -(xx - 350) * sa + (yy - 150) * ca
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    inside = (abs(u) < n * 24 + 32) & (abs(v) < 50)
    guide[inside] = 50000
    raw = guide.copy()
    masks: list[NDArray[np.bool_]] = []
    for i, center in enumerate((np.arange(n) - (n - 1) / 2) * 48):
        # Different complete band heights test independent y extents.
        mask = (abs(u - center) < 17) & (abs(v - vertical_offset) < 5 + i % 3)
        masks.append(mask)
        raw[mask] = 8000 + 1000 * i
    return raw, guide, masks, inside


@pytest.mark.parametrize("n", [1, 2, 5])
@pytest.mark.parametrize("angle", [-9, 0, 9])
def test_each_slot_contains_every_known_original_band_pixel(n: int, angle: float) -> None:
    raw, guide, masks, inside = analytic_bands(n, angle)
    before = raw.copy()
    detection = detect_reliable_geometry(raw, guide, AutoWBSettings(lane_count=n))
    assert len(detection.candidates) == 1, detection.flags
    c = detection.candidates[0]
    for mask, roi in zip(masks, c.lane_rois, strict=True):
        y, x = np.nonzero(mask)
        assert roi.x0 <= x.min() <= x.max() < roi.x1
        assert roi.y0 <= y.min() <= y.max() < roi.y1
        assert inside[roi.y0 : roi.y1, roi.x0 : roi.x1].all()
        assert np.count_nonzero(mask[roi.y0 : roi.y1, roi.x0 : roi.x1]) == mask.sum()
        assert c.roi.x0 <= roi.x0 < roi.x1 <= c.roi.x1
        assert c.roi.y0 <= roi.y0 < roi.y1 <= c.roi.y1
    if n > 1 and angle:
        assert len({(r.y0, r.y1) for r in c.lane_rois}) > 1
    assert np.array_equal(raw, before)


@pytest.mark.parametrize("angle", [-9, 9])
@pytest.mark.parametrize("offset", [-43, 43])
def test_known_band_near_guide_edge_never_silently_loses_pixels(angle: float, offset: int) -> None:
    raw, guide, masks, inside = analytic_bands(5, angle, vertical_offset=offset)
    detection = detect_reliable_geometry(raw, guide, AutoWBSettings(lane_count=5))
    # At the boundary either pause or retain ALL known pixels. An accepted
    # clipped fragment is never a valid way to satisfy the requested N.
    for c in detection.candidates:
        for mask, roi in zip(masks, c.lane_rois, strict=True):
            assert np.count_nonzero(mask[roi.y0 : roi.y1, roi.x0 : roi.x1]) == mask.sum()
            assert inside[roi.y0 : roi.y1, roi.x0 : roi.x1].all()


@pytest.mark.parametrize("angle", [-9, 9])
def test_per_slot_raw_profiles_survive_export_render_and_display_rotation(
    tmp_path: Path, angle: float
) -> None:
    raw, _, masks, _ = analytic_bands(5, angle)
    path = tmp_path / "synthetic_raw.tiff"
    tifffile.imwrite(path, raw)
    original_bytes = path.read_bytes()
    p, ticket = claim_intake_workflow_step(prepared(path), session_key="independent-detect")
    assert isinstance(p, WBIntakeCropProject)
    assert ticket
    proposal = propose_intake_crop(str(path), p, "r")
    assert proposal.detection
    assert automatic_intake_crop_allowed(proposal), proposal.detection.flags
    accepted = accept_automatic_intake_crop(p, ticket, proposal)
    evidence = accepted.intake_crops[0]
    assert evidence.crop and evidence.policy == "intake_crop@3"
    for mask, slot in zip(masks, evidence.slots, strict=True):
        r = slot.roi
        assert r and np.count_nonzero(mask[r.y0 : r.y1, r.x0 : r.x1]) == mask.sum()
    active, export_ticket = claim_intake_workflow_step(accepted, session_key="independent-export")
    assert isinstance(active, WBIntakeCropProject)
    assert export_ticket
    dest = tmp_path / "raw_crop.tiff"
    result = export_intake_crop(str(path), active, "r", str(dest), ticket=export_ticket)
    crop = evidence.crop
    assert np.array_equal(load_tiff(dest).pixels, raw[crop.y0 : crop.y1, crop.x0 : crop.x1])
    done = complete_intake_crop(
        active,
        export_ticket,
        AssetRef(
            asset_id="independent-crop",
            relative_path="assets/crop.tiff",
            sha256=result.sha256,
            size_bytes=result.size_bytes,
        ),
    )
    compose, compose_ticket = claim_intake_workflow_step(done, session_key="independent-compose")
    assert isinstance(compose, WBIntakeFigureProject)
    assert compose_ticket and compose_ticket.stage == "compose"
    original = load_tiff(path)
    sources = (FigureSourcePath(original.sha256, str(path)),)
    displayed = prepare_intake_figure(
        compose, compose_ticket, sources, str(tmp_path / "rotated.png")
    )
    changed = type(done).model_validate(
        {
            **dict(done),
            "composition": done.composition.model_copy(
                update={
                    "slices": tuple(
                        s.model_copy(
                            update={
                                "display_frame": s.display_frame.model_copy(
                                    update={"angle_degrees": 0}
                                )
                                if s.display_frame
                                else None
                            }
                        )
                        for s in done.composition.slices
                    )
                }
            ),
            "layout_style": done.layout_style.model_copy(update={"lane_unit": 60}),
        }
    )
    changed, changed_ticket = claim_intake_workflow_step(
        changed, session_key="independent-display-change"
    )
    assert isinstance(changed, WBIntakeFigureProject)
    assert changed_ticket and changed_ticket.stage == "compose"
    unrotated = prepare_intake_figure(
        changed, changed_ticket, sources, str(tmp_path / "unrotated.png")
    )
    with (
        Image.open(tmp_path / "rotated.png") as rotated,
        Image.open(tmp_path / "unrotated.png") as unrotated_image,
    ):
        assert (
            rotated.size != unrotated_image.size or rotated.tobytes() != unrotated_image.tobytes()
        )
    assert displayed.analyses == unrotated.analyses
    request = displayed.analyses[0].request
    measured = analyze_annotations(original, request)
    for slot, lane, result in zip(evidence.slots, request.lanes, measured.lanes, strict=True):
        assert slot.roi and lane.target_roi
        assert (lane.target_roi.x0, lane.target_roi.y0, lane.target_roi.x1, lane.target_roi.y1) == (
            slot.roi.x0,
            slot.roi.y0,
            slot.roi.x1,
            slot.roi.y1,
        )
        roi = lane.roi
        expected = raw[roi.y0 : roi.y1, roi.x0 : roi.x1].astype(float).mean(axis=1)
        assert result.profiles
        np.testing.assert_array_equal(result.profiles.raw, expected)
        np.testing.assert_array_equal(result.profiles.quantitative, 65535 - expected)
    assert path.read_bytes() == original_bytes
