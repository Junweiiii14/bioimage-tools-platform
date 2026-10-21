"""Paired signal/guide oracles; the signal image has no membrane contour."""

from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.api import (
    AutoWBSettings,
    FigureSourcePath,
    IntakeDraftFigure,
    IntakeGrouping,
    IntakeSource,
    WBFigureProject,
    WBIntakeCropProject,
    accept_automatic_intake_crop,
    approve_intake_workflow,
    automatic_intake_crop_allowed,
    claim_intake_workflow_step,
    confirm_intake,
    create_intake,
    intake_crop_companion_assets,
    intake_digest,
    intake_grouping,
    intake_workflow_digest,
    load_tiff,
    prepare_intake_crops,
    prepare_intake_figures,
    prepare_intake_workflow,
    propose_intake_crop,
    register_intake_source,
    save_intake_grouping,
)
from wb_tool.domain.instrument_geometry import detect_instrument_geometry


def paired(
    angle: float = 3, *, two_rows: bool = False
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    yy, xx = np.mgrid[:300, :700]
    c, s = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
    u, v = (xx - 350) * c + (yy - 150) * s, -(xx - 350) * s + (yy - 150) * c
    guide = np.full(xx.shape, 15, dtype=np.uint16)
    guide[(np.abs(u) < 145) & (np.abs(v) < 55)] = 50000
    signal = np.full(xx.shape, 50000, dtype=np.uint16)
    merge = guide.copy()
    for pos in (-96, -48, 0, 48, 96):
        for row in (-20, 20) if two_rows else (0,):
            mask = (np.abs(u - pos) < 17) & (np.abs(v - row) < 6)
            signal[mask] = 8000
            merge[mask] = 8000
    return signal, guide, merge


def grouped(tmp_path: Path) -> tuple[WBIntakeCropProject, tuple[FigureSourcePath, ...], str]:
    p = create_intake(WBFigureProject(project_id="guided"))
    paths: list[FigureSourcePath] = []
    for index, pixels in enumerate(paired(), 1):
        field = np.full((1200, 1800), 50000 if index == 1 else 15, dtype=np.uint16)
        field[450:750, 550:1250] = pixels
        pixels = field
        path = tmp_path / f"AKT_123456 ({index}).tiff"
        tifffile.imwrite(path, pixels)
        digest = sha256(path.read_bytes()).hexdigest()
        paths.append(FigureSourcePath(digest, str(path)))
        p = register_intake_source(
            p,
            IntakeSource(
                source_id=f"s{index}",
                asset=AssetRef(
                    asset_id=f"a{index}",
                    relative_path=f"assets/{index}.tiff",
                    sha256=digest,
                    size_bytes=path.stat().st_size,
                ),
                original_name=path.name,
                relative_path=path.name,
                width=pixels.shape[1],
                height=pixels.shape[0],
                bit_depth=16,
            ),
            expected_digest=intake_digest(p),
        )
    grouping = intake_grouping(p)
    p = save_intake_grouping(
        p,
        IntakeGrouping(
            figures=(IntakeDraftFigure(figure_id="f", label="Fig", lane_count=5),),
            groups=tuple(
                g.model_copy(
                    update={"figure_id": "f", "protein_label": "AKT", "selected_source_id": "s1"}
                )
                for g in grouping.groups
            ),
        ),
        expected_digest=intake_digest(p),
    )
    p = confirm_intake(p, expected_digest=intake_digest(p))
    prepared = prepare_intake_figures(
        prepare_intake_crops(
            prepare_intake_workflow(p, expected_digest=intake_digest(p), batch_stages=True)
        )
    )
    return (
        type(prepared).model_validate(
            dict(
                approve_intake_workflow(prepared, expected_digest=intake_workflow_digest(prepared))
            )
        ),
        tuple(paths),
        prepared.rows[0].row_id,
    )


@pytest.mark.parametrize("angle", [-8, 0, 8])
def test_known_guided_bands_keep_original_geometry_and_direction(angle: float) -> None:
    signal, guide, _ = paired(angle)
    before = signal.copy()
    result = detect_instrument_geometry(
        signal, guide, AutoWBSettings(lane_count=5, crop_policy="source_geometry@2")
    )
    assert len(result.candidates) == 1, result.flags
    frame = result.candidates[0].display_frame
    assert frame and abs(frame.angle_degrees - angle) < 1
    assert len(result.candidates[0].lane_rois) == 5
    for roi, pos in zip(result.candidates[0].lane_rois, (-96, -48, 0, 48, 96), strict=True):
        x, y = 350 + pos * np.cos(np.deg2rad(angle)), 150 + pos * np.sin(np.deg2rad(angle))
        assert roi.x0 < x < roi.x1 and roi.y0 < y < roi.y1
    assert np.array_equal(signal, before)


def test_multiple_rows_wrong_n_and_cancel_do_not_become_ready() -> None:
    signal, guide, _ = paired(two_rows=True)
    result = detect_instrument_geometry(signal, guide, AutoWBSettings(lane_count=5))
    assert not result.candidates and "guided_target_ambiguous" in result.flags
    signal, guide, _ = paired()
    result = detect_instrument_geometry(signal, guide, AutoWBSettings(lane_count=6))
    assert not result.candidates
    with pytest.raises(ValueError, match="取消"):
        detect_instrument_geometry(
            signal, guide, AutoWBSettings(lane_count=5), cancelled=lambda: True
        )


@pytest.mark.parametrize("signal_angle,guide_angle", [(0, 9), (-3, 6), (3, 0)])
def test_signal_direction_is_independent_of_guide(signal_angle: float, guide_angle: float) -> None:
    signal, _, _ = paired(signal_angle)
    _, guide, _ = paired(guide_angle)
    result = detect_instrument_geometry(signal, guide, AutoWBSettings(lane_count=5))
    assert len(result.candidates) == 1, result.flags
    frame = result.candidates[0].display_frame
    assert frame and abs(frame.angle_degrees - signal_angle) < 0.25


@pytest.mark.parametrize("separation", [10, 12, 14, 20])
def test_close_double_rows_are_not_accepted(separation: int) -> None:
    yy, xx = np.mgrid[:300, :700]
    _, guide, _ = paired(0)
    signal = np.tile(np.linspace(43000, 63000, 700).astype(np.uint16), (300, 1))
    for x in (254, 302, 350, 398, 446):
        for y in (150 - separation / 2, 150 + separation / 2):
            signal[(abs(xx - x) < 17) & (abs(yy - y) < 3)] = 10000
    result = detect_instrument_geometry(signal, guide, AutoWBSettings(lane_count=5))
    assert not result.candidates


def test_multiple_membranes_and_explicit_target_overlap_pause() -> None:
    from wb_tool.domain.export_detection import guided_signal_regions
    from wb_tool.domain.lanes import LaneROI

    yy, xx = np.mgrid[:400, :700]
    guide = np.full(xx.shape, 15, dtype=np.uint16)
    signal = np.tile(np.linspace(43000, 63000, 700).astype(np.uint16), (400, 1))
    for y in (100, 290):
        guide[(abs(xx - 350) < 170) & (abs(yy - y) < 55)] = 50000
        for x in (254, 302, 350, 398, 446):
            signal[(abs(xx - x) < 17) & (abs(yy - y) < 7)] = 10000
    result = detect_instrument_geometry(signal, guide, AutoWBSettings(lane_count=5))
    assert not result.candidates and "guide_multiple_membranes" in result.flags
    yy, xx = np.mgrid[:300, :700]
    _, guide, _ = paired(0)
    signal = np.tile(np.linspace(43000, 63000, 700).astype(np.uint16), (300, 1))
    for x in (254, 302, 350, 398, 446):
        for y in (140, 160):
            signal[(abs(xx - x) < 17) & (abs(yy - y) < 4)] = 10000
    regions = guided_signal_regions(signal, guide)
    assert len(regions) == 2
    result = detect_instrument_geometry(
        signal, guide, AutoWBSettings(lane_count=5), target=LaneROI("chosen", *regions[0][:4])
    )
    assert not result.candidates and "signal_target_overlap" in result.flags


def test_guided_adapter_requires_same_group_verified_assets_and_keeps_human_flag_false(
    tmp_path: Path,
) -> None:
    p, paths, row_id = grouped(tmp_path)
    assert len(intake_crop_companion_assets(p, row_id)) == 2
    assert intake_crop_companion_assets(p, "missing") == ()
    assert not automatic_intake_crop_allowed(propose_intake_crop(paths[0].path, p, row_id))
    active, ticket = claim_intake_workflow_step(p, session_key="guided")
    assert isinstance(active, WBIntakeCropProject) and ticket
    evidence = propose_intake_crop(paths[0].path, active, row_id, sources=paths[1:])
    assert automatic_intake_crop_allowed(evidence), evidence.reason
    accepted = accept_automatic_intake_crop(active, ticket, evidence)
    assert accepted.intake_crops[0].geometry_ready and not accepted.rows[0].reviewed
    assert accepted.intake_crops[0].detection
    flags = accepted.intake_crops[0].detection.flags
    assert any(f == "guide_sha256:" + paths[1].sha256 for f in flags)
    assert (
        accepted.rows[0].source
        and load_tiff(paths[0].path).sha256 == accepted.rows[0].source.sha256
    )
    with pytest.raises(ValueError, match="资产缺失"):
        propose_intake_crop(paths[0].path, active, row_id, sources=paths[1:2])
