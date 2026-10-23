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
    WBIntakeFigureProject,
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
    revise_completed_intake_crop,
)

from tools.wb.tests.test_source_geometry import membrane


@pytest.mark.parametrize("double_row", [False, True])
def test_source_contour_cannot_prove_signal_direction_or_single_target(
    tmp_path: Path,
    double_row: bool,
) -> None:
    yy, xx = np.mgrid[:300, :700]
    angle = np.deg2rad(0 if double_row else 9)
    u = (xx - 350) * np.cos(angle) + (yy - 150) * np.sin(angle)
    v = -(xx - 350) * np.sin(angle) + (yy - 150) * np.cos(angle)
    pixels = np.full(xx.shape, 15, dtype=np.uint16)
    pixels[(abs(u) < 155) & (abs(v) < 55)] = 50000
    for x in (254, 302, 350, 398, 446):
        for y in (144, 156) if double_row else (150,):
            pixels[(abs(xx - x) < 17) & (abs(yy - y) < 4)] = 8000
    path = tmp_path / "source.tiff"
    tifffile.imwrite(path, pixels)
    proposal = propose_intake_crop(str(path), prepared(path), "r")
    if double_row:
        assert not automatic_intake_crop_allowed(proposal)
    else:
        assert automatic_intake_crop_allowed(proposal)
        assert proposal.detection and proposal.detection.candidates[0].display_frame
        assert proposal.detection.candidates[0].display_frame.angle_degrees == 0


def test_rotation_preserves_other_completed_fig_and_native_global_style(tmp_path: Path) -> None:
    from wb_tool.api import (
        FigureLayoutStyle,
        LaneROI,
        WBIntakeFigureProject,
        intake_figure_digest,
        intake_figure_projection,
        render_figure,
    )

    from tools.wb.tests.test_intake_figure import compose, ready_fig

    project, sources = ready_fig(tmp_path)
    project = type(project).model_validate(
        {
            **dict(project),
            "layout_style": FigureLayoutStyle(heading_size=28, display_policy="native_samples@1"),
        }
    )
    project = compose(project, sources, tmp_path / "a.png")
    previous_digest = intake_figure_digest(project, "a")
    previous_image = (tmp_path / "a.png").read_bytes()
    previous_render = render_figure(intake_figure_projection(project, "a"), sources).rgb
    active, ticket = claim_intake_workflow_step(
        approve_intake_workflow(project, expected_digest=intake_workflow_digest(project)),
        session_key="b",
        stage_filter="crop",
    )
    assert isinstance(active, WBIntakeFigureProject) and ticket and ticket.target_id == "b1"
    proposed = record_intake_crop_proposal(
        active, ticket, propose_intake_crop(sources[2].path, active, "b1")
    )
    changed = review_intake_crop(
        proposed,
        "b1",
        # Fixed-size rotation now requires actual source margin instead of
        # silently reducing the selected display frame to fit its old ROI.
        LaneROI("b1", 4, 10, 116, 60),
        expected_digest=intake_workflow_digest(proposed),
        display_angle=3,
    )
    assert isinstance(changed, WBIntakeFigureProject)
    assert changed.layout_style == project.layout_style
    assert changed.intake_figures == project.intake_figures and changed.analyses == project.analyses
    assert intake_figure_digest(changed, "a") == previous_digest
    assert (tmp_path / "a.png").read_bytes() == previous_image
    assert render_figure(intake_figure_projection(changed, "a"), sources).rgb == previous_render


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
    # These frozen T072-T080 cases verify historical geometry policies. New
    # batches use v5; preserve the old route here instead of rewriting its oracle.
    p = type(p).model_validate(
        {**dict(p), "workflow": {**dict(p.workflow), "policy": "intake_workflow@4"}}
    )
    return type(p).model_validate(
        dict(approve_intake_workflow(p, expected_digest=intake_workflow_digest(p)))
    )


@pytest.mark.parametrize("angle", [-9, -3, 0, 3, 9])
def test_reliable_geometry_auto_exports_exact_pixels_and_straightens_display(
    tmp_path: Path, angle: float
) -> None:
    path = tmp_path / "raw.tiff"
    # Automatic geometry no longer infers Marker identity from a source-only
    # doublet. Keep this pixel/rotation positive oracle unambiguous; the original
    # marker scene remains a separate mandatory-pause regression below.
    pixels = membrane(angle=angle, marker=False)
    tifffile.imwrite(path, pixels)
    original = path.read_bytes()
    p, ticket = claim_intake_workflow_step(prepared(path), session_key="detection")
    assert isinstance(p, WBIntakeCropProject) and ticket
    proposal = propose_intake_crop(str(path), p, "r")
    assert automatic_intake_crop_allowed(proposal)
    accepted = accept_automatic_intake_crop(p, ticket, proposal)
    e = accepted.intake_crops[0]
    assert e.policy == "intake_crop@3" and e.geometry_ready and not e.reviewed
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


@pytest.mark.parametrize("kind", ["blank", "wrong-n"])
def test_uncertain_geometry_still_pauses(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "raw.tiff"
    pixels = np.full((300, 700), 50000, dtype=np.uint16) if kind == "blank" else membrane()
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
    tifffile.imwrite(path, membrane(angle=3, marker=False))
    p, ticket = claim_intake_workflow_step(prepared(path), session_key="d")
    assert isinstance(p, WBIntakeCropProject) and ticket
    e = propose_intake_crop(str(path), p, "r")
    cancelled = request_intake_workflow_cancel(p)
    assert isinstance(cancelled, WBIntakeCropProject)
    result = accept_automatic_intake_crop(cancelled, ticket, e)
    assert not result.intake_crops and result.workflow.steps[0].status == "cancelled"
    with pytest.raises(ValueError):
        type(e).model_validate({**dict(e), "policy": "intake_crop@3", "selected_index": None})


@pytest.mark.parametrize("angle", [-17.5, 0, 30])
def test_manual_display_rotation_keeps_size_and_preserves_quantitative_geometry(
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
    assert frame and frame.angle_degrees == angle
    assert frame.sampling_policy == "within_source@2"
    assert (frame.width, frame.height) == (e.crop.width, e.crop.y1 - e.crop.y0)
    assert all(0 <= x <= 700 and 0 <= y <= 300 for x, y in frame.corners())
    assert read_figure_project(reviewed.model_dump_json().encode()) == reviewed


@pytest.mark.parametrize("angle", [0, -17.5])
def test_common_policy_accepts_obvious_row_beyond_legacy_marker_and_angle_limits(
    tmp_path: Path, angle: float
) -> None:
    """T080 changes these two declared support limits; the old domain tests remain."""
    from math import cos, radians, sin

    path = tmp_path / "raw.tiff"
    pixels = membrane(angle=angle, marker=True)
    tifffile.imwrite(path, pixels)
    p, ticket = claim_intake_workflow_step(prepared(path), session_key="common")
    assert isinstance(p, WBIntakeCropProject) and ticket
    proposal = propose_intake_crop(str(path), p, "r")
    assert proposal.geometry_policy == "source_common_band_geometry@1"
    assert automatic_intake_crop_allowed(proposal)
    accepted = accept_automatic_intake_crop(p, ticket, proposal)
    assert accepted.intake_crops[0].policy == "intake_crop@4"
    assert not accepted.intake_crops[0].reviewed
    # Generator-defined five sample centres, independent of detector coordinates.
    for i, slot in enumerate(proposal.slots):
        u = -((5 + 1) * 48 + 20) / 2 + 34 + (i + 1) * 48
        x, y = 350 + u * cos(radians(angle)), 150 + u * sin(radians(angle))
        assert slot.roi and slot.roi.x0 < x < slot.roi.x1 and slot.roi.y0 < y < slot.roi.y1
    assert proposal.detection and proposal.detection.candidates[0].display_frame
    assert abs(proposal.detection.candidates[0].display_frame.angle_degrees - angle) < 1
    assert read_figure_project(accepted.model_dump_json().encode()) == accepted


def test_manual_rotation_rejects_real_source_overflow_without_shrinking(tmp_path: Path) -> None:
    from wb_tool.api import LaneROI

    path = tmp_path / "raw.tiff"
    tifffile.imwrite(path, membrane())
    p, ticket = claim_intake_workflow_step(prepared(path), session_key="manual")
    assert isinstance(p, WBIntakeCropProject) and ticket
    p = record_intake_crop_proposal(p, ticket, propose_intake_crop(str(path), p, "r"))
    before = p.model_dump_json()
    with pytest.raises(ValueError, match="超出原图"):
        review_intake_crop(
            p,
            "r",
            LaneROI("r", 0, 0, 250, 40),
            expected_digest=intake_workflow_digest(p),
            display_angle=17.5,
        )
    assert p.model_dump_json() == before


@pytest.mark.parametrize("angle", [0, -17.5])
@pytest.mark.parametrize("marker", [False, True])
def test_editing_saved_automatic_frame_keeps_smaller_dimensions_after_reopen(
    tmp_path: Path, angle: float, marker: bool
) -> None:
    path = tmp_path / "raw.tiff"
    tifffile.imwrite(path, membrane(angle=3, marker=marker))
    original = path.read_bytes()
    proposed, ticket = claim_intake_workflow_step(prepared(path), session_key="detect")
    assert isinstance(proposed, WBIntakeCropProject) and ticket
    evidence = propose_intake_crop(str(path), proposed, "r")
    accepted = accept_automatic_intake_crop(proposed, ticket, evidence)
    original_frame = accepted.composition.slices[0].display_frame
    crop = accepted.rows[0].roi
    assert crop and original_frame
    assert original_frame.width < crop.width
    assert original_frame.height < crop.y1 - crop.y0
    active, crop_ticket = claim_intake_workflow_step(accepted, session_key="save-crop")
    assert isinstance(active, WBIntakeCropProject) and crop_ticket
    crop_path = tmp_path / "automatic-crop.tiff"
    exported = export_intake_crop(str(path), active, "r", str(crop_path), ticket=crop_ticket)
    done = complete_intake_crop(
        active,
        crop_ticket,
        AssetRef(
            asset_id="automatic-crop",
            relative_path="assets/automatic-crop.tiff",
            sha256=exported.sha256,
            size_bytes=exported.size_bytes,
        ),
    )
    original_crop = crop_path.read_bytes()
    before = done.model_dump_json()
    original_evidence = done.intake_crops[0]
    assert original_evidence.policy == ("intake_crop@4" if marker else "intake_crop@3")
    sources = (FigureSourcePath(sha256(original).hexdigest(), str(path)),)
    composing, compose_ticket = claim_intake_workflow_step(done, session_key="before-rotation")
    assert isinstance(composing, WBIntakeFigureProject) and compose_ticket
    old_plan = prepare_intake_figure(
        composing, compose_ticket, sources, str(tmp_path / "before-rotation.png")
    )
    quant_digest = sha256(old_plan.analyses[0].model_dump_json().encode()).hexdigest()
    changed = revise_completed_intake_crop(
        done,
        "r",
        crop,
        expected_digest=intake_workflow_digest(done),
        display_angle=angle,
    )
    frame = changed.composition.slices[0].display_frame
    assert frame and frame.angle_degrees == angle and frame.sampling_policy == "within_source@2"
    assert (frame.center_x, frame.center_y, frame.width, frame.height) == (
        original_frame.center_x,
        original_frame.center_y,
        original_frame.width,
        original_frame.height,
    )
    assert changed.rows[0].roi == crop and changed.intake_crops[0].crop == crop
    changed_evidence = changed.intake_crops[0]
    assert changed_evidence.policy == "intake_crop_display_review@1"
    assert changed_evidence.reviewed and changed_evidence.geometry_ready
    assert changed_evidence.slots == original_evidence.slots
    assert changed_evidence.fixed_grid == original_evidence.fixed_grid
    assert changed_evidence.geometry_policy == original_evidence.geometry_policy
    assert changed_evidence.detection == original_evidence.detection
    assert changed_evidence.selected_index == original_evidence.selected_index
    assert changed_evidence.raw_crop == original_evidence.raw_crop
    with pytest.raises(ValueError, match="人工确认"):
        type(changed_evidence).model_validate(
            {**dict(changed_evidence), "reviewed": False, "raw_crop": None}
        )
    assert done.model_dump_json() == before
    saved = tmp_path / "rotated-project.json"
    saved.write_text(changed.model_dump_json(), encoding="utf-8")
    reopened = read_figure_project(saved.read_bytes())
    assert reopened == changed
    assert isinstance(reopened, WBIntakeCropProject)
    assert reopened.composition.slices[0].display_frame == frame
    assert reopened.rows[0].roi == crop
    assert reopened.intake_crops[0] == changed_evidence
    # A second saved angle before the new export must not reject the preserved
    # raw asset or silently rebuild the already reviewed quantitative geometry.
    second = review_intake_crop(
        reopened,
        "r",
        crop,
        expected_digest=intake_workflow_digest(reopened),
        display_angle=12,
    )
    assert second.intake_crops[0] == changed_evidence
    new_roi = replace(crop, x0=crop.x0 + 2, x1=crop.x1 - 2)
    recropped = review_intake_crop(
        reopened,
        "r",
        new_roi,
        expected_digest=intake_workflow_digest(reopened),
        display_angle=0,
    )
    recropped_evidence = recropped.intake_crops[0]
    assert recropped_evidence.policy == "intake_crop@1"
    assert recropped_evidence.geometry_policy == "explicit_original_roi@1"
    assert recropped_evidence.fixed_grid is None and recropped_evidence.raw_crop is None
    assert all(
        slot.roi and (slot.roi.y0, slot.roi.y1) == (new_roi.y0, new_roi.y1)
        for slot in recropped_evidence.slots
    )
    new_frame = recropped.composition.slices[0].display_frame
    assert new_frame and (new_frame.width, new_frame.height) == (
        new_roi.width,
        new_roi.y1 - new_roi.y0,
    )
    active, next_crop_ticket = claim_intake_workflow_step(
        approve_intake_workflow(reopened, expected_digest=intake_workflow_digest(reopened)),
        session_key="after-rotation-crop",
    )
    assert isinstance(active, WBIntakeCropProject) and next_crop_ticket
    next_crop_path = tmp_path / "rotated-raw-crop.tiff"
    next_export = export_intake_crop(
        str(path), active, "r", str(next_crop_path), ticket=next_crop_ticket
    )
    assert next_crop_path.read_bytes() == original_crop
    done_again = complete_intake_crop(
        active,
        next_crop_ticket,
        AssetRef(
            asset_id="rotated-raw-crop",
            relative_path="assets/rotated-raw-crop.tiff",
            sha256=next_export.sha256,
            size_bytes=next_export.size_bytes,
        ),
    )
    composing_again, next_compose_ticket = claim_intake_workflow_step(
        done_again, session_key="after-rotation"
    )
    assert isinstance(composing_again, WBIntakeFigureProject) and next_compose_ticket
    new_plan = prepare_intake_figure(
        composing_again, next_compose_ticket, sources, str(tmp_path / "after-rotation.png")
    )
    assert new_plan.input_digest != old_plan.input_digest
    assert new_plan.analyses == old_plan.analyses
    assert sha256(new_plan.analyses[0].model_dump_json().encode()).hexdigest() == quant_digest
    assert path.read_bytes() == original and crop_path.read_bytes() == original_crop


@pytest.mark.parametrize("legacy", [False, True])
def test_rotating_guided_geometry_keeps_companion_identity_validation(
    tmp_path: Path, legacy: bool
) -> None:
    if legacy:
        fixture = Path(__file__).parent / "fixtures" / "intake_crop_v2" / "guided.json"
        accepted = read_figure_project(fixture.read_bytes())
        assert isinstance(accepted, WBIntakeCropProject)
    else:
        from tools.wb.tests.test_reliable_geometry_registration import grouped_arrays

        guide = np.full((240, 600), 100, dtype=np.uint16)
        guide[71:170, 151:450] = 50000
        signal = np.full(guide.shape, 50000, dtype=np.uint16)
        merge = guide.copy()
        for x in (275, 325):
            signal[113:128, x - 15 : x + 16] = 8000
            merge[113:128, x - 15 : x + 16] = 8000
        project, sources, row_id = grouped_arrays(tmp_path, (signal, guide, merge))
        active, ticket = claim_intake_workflow_step(project, session_key="guided")
        assert isinstance(active, WBIntakeCropProject) and ticket
        proposal = propose_intake_crop(sources[0].path, active, row_id, sources=sources[1:])
        accepted = accept_automatic_intake_crop(active, ticket, proposal)
    original = accepted.intake_crops[0]
    assert original.crop
    assert original.geometry_policy == f"instrument_guided_geometry@{1 if legacy else 2}"
    change = revise_completed_intake_crop if legacy else review_intake_crop
    rotated = change(
        accepted,
        original.row_id,
        original.crop,
        expected_digest=intake_workflow_digest(accepted),
        display_angle=0,
    )
    evidence = rotated.intake_crops[0]
    assert evidence.slots == original.slots and evidence.fixed_grid == original.fixed_grid
    assert evidence.geometry_policy == original.geometry_policy
    assert read_figure_project(rotated.model_dump_json().encode()) == rotated
    assert evidence.detection
    forged_detection = replace(
        evidence.detection,
        flags=tuple(
            "guide_sha256:" + "0" * 64 if flag.startswith("guide_sha256:") else flag
            for flag in evidence.detection.flags
        ),
    )
    with pytest.raises(ValueError, match="辅助定位"):
        type(rotated).model_validate(
            {
                **dict(rotated),
                "intake_crops": (evidence.model_copy(update={"detection": forged_detection}),),
            }
        )


def test_manual_rotation_uses_same_subpixel_source_boundary_tolerance(tmp_path: Path) -> None:
    path = tmp_path / "raw.tiff"
    tifffile.imwrite(path, membrane(marker=False))
    active, ticket = claim_intake_workflow_step(prepared(path), session_key="detect")
    assert isinstance(active, WBIntakeCropProject) and ticket
    evidence = propose_intake_crop(str(path), active, "r")
    proposed = record_intake_crop_proposal(active, ticket, evidence)
    assert evidence.crop
    reviewed = review_intake_crop(
        proposed,
        "r",
        evidence.crop,
        expected_digest=intake_workflow_digest(proposed),
        display_angle=0,
    )
    segment = reviewed.composition.slices[0]
    assert segment.display_frame
    # This subpixel rounding is already valid under the layout/source contract.
    # It must not be accepted by preview/layout but rejected by manual review.
    frame = segment.display_frame.model_copy(
        update={"center_x": 10.0 - 5e-8, "center_y": 20.0, "width": 20.0, "height": 10.0}
    )
    bounded = type(reviewed).model_validate(
        {
            **dict(reviewed),
            "composition": reviewed.composition.model_copy(
                update={"slices": (segment.model_copy(update={"display_frame": frame}),)}
            ),
        }
    )
    changed = review_intake_crop(
        bounded,
        "r",
        evidence.crop,
        expected_digest=intake_workflow_digest(bounded),
        display_angle=0,
    )
    assert changed.composition.slices[0].display_frame == frame
    assert changed.rows[0].roi == evidence.crop
