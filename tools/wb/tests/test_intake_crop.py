"""Known original pixels and fixed identity oracles; no scientific accuracy claims."""

from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest
import tifffile
from hypothesis import given, settings
from hypothesis import strategies as st
from tool_contracts.api import AssetRef
from wb_tool.api import (
    IntakeAssignment,
    IntakeFigure,
    IntakeProtein,
    IntakeSource,
    LaneROI,
    StagedProjectArchive,
    WBFigureProject,
    WBIntakeCropProject,
    WBIntakeWorkflowProject,
    approve_intake_workflow,
    assign_intake_sources,
    claim_intake_workflow_step,
    complete_intake_crop,
    confirm_intake,
    create_intake,
    export_intake_crop,
    intake_digest,
    intake_workflow_digest,
    prepare_intake_crops,
    prepare_intake_workflow,
    project_assets,
    propose_intake_crop,
    read_figure_project,
    record_intake_crop_proposal,
    register_intake_source,
    replace_intake_plan,
    request_intake_workflow_cancel,
    restore_staged_project,
    review_intake_crop,
)
from wb_tool.application.intake_crop import make_intake_crop_evidence
from wb_tool.domain.automatic import AutoWBSettings, detect_automatic_geometry


def project(
    count: int, digest: str = "a" * 64, *, width: int = 144, height: int = 72
) -> WBIntakeCropProject:
    p = create_intake(WBFigureProject(project_id="fixed-n"))
    p = replace_intake_plan(
        p,
        (IntakeFigure(figure_id="f", label="Fig", lane_count=count),),
        (IntakeProtein(protein_id="r", figure_id="f", label="AKT"),),
        expected_digest=intake_digest(p),
    )
    p = register_intake_source(
        p,
        IntakeSource(
            source_id="s",
            asset=AssetRef(
                asset_id="s", relative_path="assets/raw.tiff", sha256=digest, size_bytes=1
            ),
            original_name="raw.tiff",
            relative_path="raw.tiff",
            width=width,
            height=height,
            bit_depth=16,
        ),
        expected_digest=intake_digest(p),
    )
    p = assign_intake_sources(
        p, (IntakeAssignment(protein_id="r", source_id="s"),), expected_digest=intake_digest(p)
    )
    p = confirm_intake(p, expected_digest=intake_digest(p))
    return prepare_intake_crops(prepare_intake_workflow(p, expected_digest=intake_digest(p)))


def approve(p: WBIntakeCropProject) -> WBIntakeCropProject:
    result = approve_intake_workflow(p, expected_digest=intake_workflow_digest(p))
    assert isinstance(result, WBIntakeCropProject)
    return result


@settings(max_examples=20)
@given(count=st.integers(min_value=1, max_value=96))
def test_all_blank_preserves_every_manifest_slot_without_fake_coordinates(count: int) -> None:
    p = project(count)
    detection = detect_automatic_geometry(
        np.full((72, 144), 1000, dtype=np.uint16),
        AutoWBSettings(lane_count=count, crop_policy="source_geometry@2"),
    )
    evidence = make_intake_crop_evidence(p, "r", detection)
    assert len(evidence.slots) == count
    assert len({s.slot_id for s in evidence.slots}) == count
    assert all(s.roi is None and s.signal == "unlocated" for s in evidence.slots)
    assert evidence.crop is None and not evidence.reviewed and evidence.raw_crop is None
    active, ticket = claim_intake_workflow_step(approve(p), session_key="test")
    assert isinstance(active, WBIntakeCropProject) and ticket is not None
    recorded = record_intake_crop_proposal(active, ticket, evidence)
    assert recorded.workflow.steps[0].status == "needs_review"
    assert recorded.analyses == () and recorded.rows[0].empty_lanes == ()
    assert read_figure_project(recorded.model_dump_json().encode()) == recorded


def test_review_crop_exports_exact_original_samples_and_no_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "raw.tiff"
    # Each sample encodes its original y/x; a shifted or resampled crop must fail.
    pixels = np.arange(72 * 144, dtype=np.uint16).reshape(72, 144)
    tifffile.imwrite(source, pixels)
    before = source.read_bytes()
    p = approve(project(6, sha256(before).hexdigest()))
    p, ticket = claim_intake_workflow_step(p, session_key="test")
    assert isinstance(p, WBIntakeCropProject) and ticket is not None
    p = record_intake_crop_proposal(p, ticket, propose_intake_crop(str(source), p, "r"))
    p = review_intake_crop(
        p, "r", LaneROI("r", 12, 10, 132, 50), expected_digest=intake_workflow_digest(p)
    )
    assert not p.workflow.approved
    assert all(s.signal == "undetermined" for s in p.intake_crops[0].slots)
    assert p.rows[0].empty_lanes == ()
    p, ticket = claim_intake_workflow_step(approve(p), session_key="test")
    assert isinstance(p, WBIntakeCropProject) and ticket is not None
    target = tmp_path / "crop.tiff"
    export_intake_crop(str(source), p, "r", str(target))
    expected = np.array(
        [list(range(y * 144 + 12, y * 144 + 132)) for y in range(10, 50)], dtype=np.uint16
    )
    with tifffile.TiffFile(target) as exported:
        page = exported.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        assert np.array_equal(page.asarray(), expected)
    assert source.read_bytes() == before
    with pytest.raises(FileExistsError):
        export_intake_crop(str(source), p, "r", str(target))
    asset = AssetRef(
        asset_id="crop",
        relative_path="assets/crop.tiff",
        sha256=sha256(target.read_bytes()).hexdigest(),
        size_bytes=target.stat().st_size,
    )
    finished = complete_intake_crop(p, ticket, asset)
    assert finished.workflow.steps[0].status == "done"
    assert finished.intake_crops[0].raw_crop == asset
    next_project, compose = claim_intake_workflow_step(finished, session_key="test")
    assert isinstance(next_project, WBIntakeCropProject)
    assert compose is not None and compose.stage == "compose"
    assert asset in project_assets(next_project)
    archive = AssetRef(
        asset_id="zip", relative_path="assets/project.zip", sha256="f" * 64, size_bytes=100
    )
    staged = StagedProjectArchive(next_project, "project.zip", archive.sha256, (), (), 2)
    imported = tuple(
        a.model_copy(update={"asset_id": "new-" + a.asset_id}) for a in project_assets(next_project)
    )
    restored = restore_staged_project(staged, imported, archive)
    assert isinstance(restored, WBIntakeCropProject)
    assert restored.intake_crops[0].raw_crop is not None
    assert restored.intake_crops[0].raw_crop.asset_id == "new-crop"
    assert next(s for s in restored.workflow.steps if s.stage == "compose").status == "interrupted"
    with pytest.raises(ValueError):
        WBIntakeWorkflowProject.from_bytes(finished.model_dump_json().encode())


def test_cancelled_detection_cannot_install_a_candidate() -> None:
    p, ticket = claim_intake_workflow_step(approve(project(3)), session_key="test")
    assert isinstance(p, WBIntakeCropProject) and ticket is not None
    detection = detect_automatic_geometry(
        np.full((72, 144), 1000, dtype=np.uint16),
        AutoWBSettings(lane_count=3, crop_policy="source_geometry@2"),
    )
    evidence = make_intake_crop_evidence(p, "r", detection)
    cancelled = request_intake_workflow_cancel(p)
    assert isinstance(cancelled, WBIntakeCropProject)
    finished = record_intake_crop_proposal(cancelled, ticket, evidence)
    assert finished.workflow.steps[0].status == "cancelled"
    assert finished.intake_crops == ()


def test_source_changed_rejected_before_any_crop_publication(tmp_path: Path) -> None:
    source = tmp_path / "changed.tiff"
    tifffile.imwrite(source, np.full((72, 144), 1000, dtype=np.uint16))
    with pytest.raises(ValueError, match="身份"):
        propose_intake_crop(str(source), project(3), "r")


def test_marker_is_not_a_slot_and_conflicting_n_stays_unlocated() -> None:
    from tools.wb.tests.test_source_geometry import membrane

    pixels = membrane()
    p = project(5, width=700, height=300)
    detection = detect_automatic_geometry(
        pixels, AutoWBSettings(lane_count=5, crop_policy="source_geometry@2")
    )
    evidence = make_intake_crop_evidence(p, "r", detection)
    assert detection.marker is not None
    assert len(evidence.slots) == 5 and not evidence.reviewed
    for slot, x in zip(evidence.slots, (278, 326, 374, 422, 470), strict=True):
        assert slot.roi is not None and slot.roi.x0 < x < slot.roi.x1
        assert slot.roi.y0 < 150 < slot.roi.y1
        assert slot.roi.x0 >= detection.marker.x1
    conflict = make_intake_crop_evidence(
        project(6, width=700, height=300),
        "r",
        detect_automatic_geometry(
            pixels, AutoWBSettings(lane_count=6, crop_policy="source_geometry@2")
        ),
    )
    assert len(conflict.slots) == 6 and all(s.roi is None for s in conflict.slots)
    assert "explicit_lane_count_conflicts_with_evidence" in conflict.reason


def test_nested_slot_tampering_is_rejected_when_reloading_project() -> None:
    p, ticket = claim_intake_workflow_step(approve(project(3)), session_key="test")
    assert isinstance(p, WBIntakeCropProject) and ticket is not None
    detection = detect_automatic_geometry(
        np.full((72, 144), 1000, dtype=np.uint16),
        AutoWBSettings(lane_count=3, crop_policy="source_geometry@2"),
    )
    evidence = make_intake_crop_evidence(p, "r", detection)
    p = record_intake_crop_proposal(p, ticket, evidence)
    invalid = evidence.model_copy(
        update={
            "slots": tuple(
                s.model_copy(update={"slot_id": evidence.slots[0].slot_id}) for s in evidence.slots
            )
        }
    )
    with pytest.raises(ValueError, match="重复"):
        WBIntakeCropProject.model_validate({**dict(p), "intake_crops": (invalid,)})
