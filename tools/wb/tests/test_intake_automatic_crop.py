"""Source geometry can proceed without human approval while retaining its provenance."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.api import (
    FigureSourcePath,
    IntakeAssignment,
    IntakeFigure,
    IntakeProtein,
    IntakeSource,
    WBFigureProject,
    WBIntakeCropProject,
    accept_automatic_intake_crop,
    approve_intake_workflow,
    assign_intake_sources,
    automatic_intake_crop_allowed,
    claim_intake_workflow_step,
    complete_intake_crop,
    confirm_intake,
    create_intake,
    export_intake_crop,
    intake_digest,
    intake_workflow_digest,
    load_tiff,
    prepare_intake_crops,
    prepare_intake_figure,
    prepare_intake_figures,
    prepare_intake_workflow,
    propose_intake_crop,
    read_figure_project,
    record_intake_crop_proposal,
    register_intake_source,
    replace_intake_plan,
    request_intake_workflow_cancel,
    review_intake_crop,
)

from tools.wb.tests.test_source_geometry import membrane


def prepared(path: Path, count: int = 5) -> WBIntakeCropProject:
    image = load_tiff(path)
    p = create_intake(WBFigureProject(project_id="automatic-crop"))
    p = replace_intake_plan(
        p,
        (IntakeFigure(figure_id="f", label="Fig", lane_count=count),),
        (IntakeProtein(protein_id="r", figure_id="f", label="AKT"),),
        expected_digest=intake_digest(p),
    )
    ref = AssetRef(
        asset_id="raw",
        relative_path="assets/raw.tiff",
        sha256=image.sha256,
        size_bytes=path.stat().st_size,
    )
    p = register_intake_source(
        p,
        IntakeSource(
            source_id="s",
            asset=ref,
            original_name=path.name,
            relative_path=path.name,
            width=image.pixels.shape[1],
            height=image.pixels.shape[0],
            bit_depth=16,
        ),
        expected_digest=intake_digest(p),
    )
    p = assign_intake_sources(
        p, (IntakeAssignment(protein_id="r", source_id="s"),), expected_digest=intake_digest(p)
    )
    p = confirm_intake(p, expected_digest=intake_digest(p))
    p = prepare_intake_figures(
        prepare_intake_crops(
            prepare_intake_workflow(p, expected_digest=intake_digest(p), batch_stages=True)
        )
    )
    return type(p).model_validate(
        dict(approve_intake_workflow(p, expected_digest=intake_workflow_digest(p)))
    )


@pytest.mark.parametrize("angle", [-9, -3, 0, 3, 9])
def test_reliable_geometry_auto_exports_exact_pixels_and_straightens_display(
    tmp_path: Path, angle: float
) -> None:
    path = tmp_path / "raw.tiff"
    pixels = membrane(angle=angle)
    tifffile.imwrite(path, pixels)
    original = path.read_bytes()
    p, ticket = claim_intake_workflow_step(prepared(path), session_key="detection")
    assert isinstance(p, WBIntakeCropProject) and ticket
    proposal = propose_intake_crop(str(path), p, "r")
    assert automatic_intake_crop_allowed(proposal)
    accepted = accept_automatic_intake_crop(p, ticket, proposal)
    e = accepted.intake_crops[0]
    assert e.policy == "intake_crop@2" and e.geometry_ready and not e.reviewed
    assert not accepted.rows[0].reviewed and accepted.rows[0].roi == e.crop
    frame = accepted.composition.slices[0].display_frame
    assert frame and abs(frame.angle_degrees - angle) < 1
    assert read_figure_project(accepted.model_dump_json().encode()) == accepted
    active, export_ticket = claim_intake_workflow_step(accepted, session_key="export")
    assert isinstance(active, WBIntakeCropProject) and export_ticket
    crop_path = tmp_path / "crop.tiff"
    result = export_intake_crop(str(path), active, "r", str(crop_path), ticket=export_ticket)
    assert e.crop
    with tifffile.TiffFile(crop_path) as exported:
        page = exported.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        assert np.array_equal(page.asarray(), pixels[e.crop.y0 : e.crop.y1, e.crop.x0 : e.crop.x1])
    done = complete_intake_crop(
        active,
        export_ticket,
        AssetRef(
            asset_id="crop",
            relative_path="assets/crop.tiff",
            sha256=result.sha256,
            size_bytes=result.size_bytes,
        ),
    )
    compose, compose_ticket = claim_intake_workflow_step(done, session_key="compose")
    assert compose_ticket and compose_ticket.stage == "compose"
    from wb_tool.api import WBIntakeFigureProject

    assert isinstance(compose, WBIntakeFigureProject)
    output = prepare_intake_figure(
        compose,
        compose_ticket,
        (FigureSourcePath(sha256(original).hexdigest(), str(path)),),
        str(tmp_path / "fig.png"),
    )
    assert len(output.analyses) == 1
    assert tuple(lane.target_roi for lane in output.analyses[0].request.lanes) == tuple(
        replace(s.roi, lane_id=f"r:{s.position:02d}") for s in e.slots if s.roi
    )
    assert path.read_bytes() == original


@pytest.mark.parametrize("kind", ["blank", "wrong-n", "large-angle"])
def test_uncertain_geometry_still_pauses(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "raw.tiff"
    pixels = (
        np.full((300, 700), 50000, dtype=np.uint16)
        if kind == "blank"
        else membrane(angle=15 if kind == "large-angle" else 0)
    )
    tifffile.imwrite(path, pixels)
    p, ticket = claim_intake_workflow_step(
        prepared(path, 6 if kind == "wrong-n" else 5), session_key="d"
    )
    assert isinstance(p, WBIntakeCropProject) and ticket
    e = propose_intake_crop(str(path), p, "r")
    assert not automatic_intake_crop_allowed(e)
    with pytest.raises(ValueError, match="明确范围"):
        accept_automatic_intake_crop(p, ticket, e)
    result = record_intake_crop_proposal(p, ticket, e)
    assert result.workflow.steps[0].status == "needs_review"
    assert not result.intake_crops[0].geometry_ready and not result.analyses


def test_cancel_and_forged_machine_evidence_cannot_become_ready(tmp_path: Path) -> None:
    path = tmp_path / "raw.tiff"
    tifffile.imwrite(path, membrane(angle=3))
    p, ticket = claim_intake_workflow_step(prepared(path), session_key="d")
    assert isinstance(p, WBIntakeCropProject) and ticket
    e = propose_intake_crop(str(path), p, "r")
    cancelled = request_intake_workflow_cancel(p)
    assert isinstance(cancelled, WBIntakeCropProject)
    result = accept_automatic_intake_crop(cancelled, ticket, e)
    assert not result.intake_crops and result.workflow.steps[0].status == "cancelled"
    with pytest.raises(ValueError):
        type(e).model_validate({**dict(e), "policy": "intake_crop@2", "selected_index": None})


@pytest.mark.parametrize("angle", [-10, 0, 10])
def test_manual_display_rotation_fits_original_roi_and_preserves_quantitative_geometry(
    tmp_path: Path, angle: float
) -> None:
    path = tmp_path / "raw.tiff"
    tifffile.imwrite(path, membrane(angle=3))
    p, ticket = claim_intake_workflow_step(prepared(path), session_key="d")
    assert isinstance(p, WBIntakeCropProject) and ticket
    e = propose_intake_crop(str(path), p, "r")
    p = record_intake_crop_proposal(p, ticket, e)
    assert e.crop
    reviewed = review_intake_crop(
        p, "r", e.crop, expected_digest=intake_workflow_digest(p), display_angle=angle
    )
    assert reviewed.rows[0].roi == e.crop and reviewed.rows[0].reviewed
    frame = reviewed.composition.slices[0].display_frame
    if angle:
        assert frame and frame.angle_degrees == angle
        assert all(
            e.crop.x0 - 1e-7 <= x <= e.crop.x1 + 1e-7 and e.crop.y0 - 1e-7 <= y <= e.crop.y1 + 1e-7
            for x, y in frame.corners()
        )
    else:
        assert frame is None
