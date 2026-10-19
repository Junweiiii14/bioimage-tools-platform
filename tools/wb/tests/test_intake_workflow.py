"""Workflow dependency, cancellation and recovery oracles with two independent Figs."""

import pytest
from tool_contracts.api import AssetRef
from wb_tool.api import (
    IntakeAssignment,
    IntakeFigure,
    IntakeProtein,
    IntakeSource,
    LaneROI,
    StagedProjectArchive,
    WBFigureProject,
    WBIntakeProject,
    WBIntakeWorkflowProject,
    approve_intake_workflow,
    assign_intake_sources,
    claim_intake_workflow_step,
    confirm_intake,
    create_intake,
    finish_intake_workflow_step,
    intake_digest,
    intake_workflow_digest,
    intake_workflow_snapshot,
    prepare_intake_workflow,
    read_figure_project,
    recover_intake_workflow,
    register_intake_source,
    replace_intake_plan,
    request_intake_workflow_cancel,
    restore_staged_project,
    retry_intake_workflow_step,
    return_to_intake_editing,
)


def workflow() -> WBIntakeWorkflowProject:
    project = create_intake(WBFigureProject(project_id="p"))
    project = replace_intake_plan(
        project,
        tuple(IntakeFigure(figure_id=f"f{i}", label=f"Fig{i}", lane_count=3) for i in (1, 2)),
        tuple(IntakeProtein(protein_id=f"r{i}", figure_id=f"f{i}", label="same") for i in (1, 2)),
        expected_digest=intake_digest(project),
    )
    for i in (1, 2):
        project = register_intake_source(
            project,
            IntakeSource(
                source_id=f"s{i}",
                asset=AssetRef(
                    asset_id=f"a{i}",
                    relative_path=f"assets/{i}.tif",
                    sha256=f"{i:064x}",
                    size_bytes=3,
                ),
                original_name="raw.tif",
                relative_path="raw.tif",
                width=60,
                height=30,
                bit_depth=16,
            ),
            expected_digest=intake_digest(project),
        )
    project = assign_intake_sources(
        project,
        tuple(IntakeAssignment(protein_id=f"r{i}", source_id=f"s{i}") for i in (1, 2)),
        expected_digest=intake_digest(project),
    )
    project = confirm_intake(project, expected_digest=intake_digest(project))
    return prepare_intake_workflow(project, expected_digest=intake_digest(project))


def approved() -> WBIntakeWorkflowProject:
    project = workflow()
    return approve_intake_workflow(project, expected_digest=intake_workflow_digest(project))


def test_two_figs_order_is_crop_compose_measure_without_any_ocr_or_values() -> None:
    project = approved()
    observed: list[tuple[str, str]] = []
    for _ in range(7):
        project, ticket = claim_intake_workflow_step(project, session_key="test-only")
        assert ticket is not None
        observed.append((ticket.stage, ticket.target_id))
        assert claim_intake_workflow_step(project, session_key="test-only")[1] is None
        project = finish_intake_workflow_step(project, ticket, "done")
    assert observed == [
        ("crop", "r1"),
        ("compose", "f1"),
        ("measure", "f1"),
        ("crop", "r2"),
        ("compose", "f2"),
        ("measure", "f2"),
        ("export", "p"),
    ]
    assert intake_workflow_snapshot(project)["stages_finished"] is True
    assert project.analyses == () and project.ocr is None
    # Ledger transitions alone cannot manufacture quantitative runs or values.
    assert all(row.roi is None for row in project.rows)
    assert claim_intake_workflow_step(project, session_key="test-only")[1] is None


def test_failure_blocks_only_its_fig_and_retry_keeps_other_completed_fig() -> None:
    project, ticket = claim_intake_workflow_step(approved(), session_key="a")
    assert ticket is not None
    project = finish_intake_workflow_step(
        project, ticket, "needs_review", reason="首尾空位证据不足"
    )
    for stage in ("crop", "compose", "measure"):
        project, other = claim_intake_workflow_step(project, session_key="a")
        assert other is not None and other.stage == stage
        assert other.target_id in {"r2", "f2"}
        project = finish_intake_workflow_step(project, other, "done")
    assert claim_intake_workflow_step(project, session_key="a")[1] is None
    assert intake_workflow_snapshot(project)["stages_finished"] is False
    reset = retry_intake_workflow_step(
        project, "crop", "r1", expected_digest=intake_workflow_digest(project)
    )
    assert not reset.workflow.approved
    assert [s.status for s in reset.workflow.steps if s.target_id == "f2"] == ["done", "done"]
    reset = approve_intake_workflow(reset, expected_digest=intake_workflow_digest(reset))
    reset, retried = claim_intake_workflow_step(reset, session_key="a")
    assert retried is not None and retried.attempt == 2
    with pytest.raises(ValueError, match="过期"):
        finish_intake_workflow_step(reset, ticket, "done")


def test_cancel_records_intent_until_executor_exit_ack_and_rejects_duplicate_reply() -> None:
    project, ticket = claim_intake_workflow_step(approved(), session_key="a")
    assert ticket is not None
    cancelled = request_intake_workflow_cancel(project)
    assert cancelled.workflow.steps[0].status == "running"
    assert claim_intake_workflow_step(cancelled, session_key="a")[1] is None
    finished = finish_intake_workflow_step(cancelled, ticket, "done")
    assert finished.workflow.steps[0].status == "cancelled"
    assert intake_workflow_snapshot(finished)["stages_finished"] is False
    with pytest.raises(ValueError, match="过期"):
        finish_intake_workflow_step(finished, ticket, "done")


def test_reopen_preserves_ledger_and_recovery_does_not_resume_unknown_running_step() -> None:
    original = workflow()
    assert return_to_intake_editing(original).schema_version == 10
    with pytest.raises(ValueError, match="先核对"):
        claim_intake_workflow_step(original, session_key="a")
    active, ticket = claim_intake_workflow_step(approved(), session_key="a")
    assert ticket is not None
    reopened = read_figure_project(active.model_dump_json().encode())
    assert isinstance(reopened, WBIntakeWorkflowProject) and reopened == active
    with pytest.raises(ValueError):
        WBIntakeProject.from_bytes(active.model_dump_json().encode())
    recovered = recover_intake_workflow(reopened)
    assert recovered.workflow.steps[0].status == "interrupted"
    assert not recovered.workflow.approved
    with pytest.raises(ValueError, match="历史"):
        return_to_intake_editing(recovered)


def test_tampered_stage_order_and_identity_and_stale_summary_are_rejected() -> None:
    project = workflow()
    with pytest.raises(ValueError, match="变化"):
        approve_intake_workflow(project, expected_digest="0" * 64)
    ledger = project.workflow.model_dump(mode="python")
    ledger["steps"] = (project.workflow.steps[1], *project.workflow.steps[1:])
    with pytest.raises(ValueError, match="完整对应"):
        WBIntakeWorkflowProject.model_validate({**dict(project), "workflow": ledger})
    premature = tuple(
        s.model_copy(
            update={"status": "done", "attempt": 1, "claim_id": "a" * 64, "input_digest": "b" * 64}
        )
        if s.stage == "measure"
        else s
        for s in project.workflow.steps
    )
    with pytest.raises(ValueError, match="依赖"):
        WBIntakeWorkflowProject.model_validate(
            {**dict(project), "workflow": {**dict(project.workflow), "steps": premature}}
        )


def test_restore_remaps_sources_and_interrupts_claims_without_losing_stages() -> None:
    project, ticket = claim_intake_workflow_step(approved(), session_key="old")
    assert ticket is not None
    archive = AssetRef(asset_id="z", relative_path="assets/z.zip", sha256="a" * 64, size_bytes=100)
    staged = StagedProjectArchive(project, "z.zip", archive.sha256, (), (), 2)
    imported = tuple(
        s.asset.model_copy(update={"asset_id": "new-" + s.source_id})
        for s in project.intake.sources
    )
    restored = restore_staged_project(staged, imported, archive)
    assert isinstance(restored, WBIntakeWorkflowProject)
    assert restored.intake.confirmed_digest == intake_digest(restored)
    assert restored.workflow.steps[0].status == "interrupted"
    assert not restored.workflow.approved
    assert len(restored.workflow.steps) == len(project.workflow.steps)
    assert restored.intake.sources[0].asset == imported[0]


def test_claim_binds_actual_inputs_but_allows_save_revision_only() -> None:
    project, crop = claim_intake_workflow_step(approved(), session_key="a")
    assert crop is not None
    project = finish_intake_workflow_step(project, crop, "done")
    project, compose = claim_intake_workflow_step(project, session_key="a")
    assert compose is not None and compose.stage == "compose"
    saved = WBIntakeWorkflowProject.model_validate({**dict(project), "revision": 3})
    assert finish_intake_workflow_step(saved, compose, "done").workflow.steps[2].status == "done"
    changed_row = project.rows[0].model_copy(
        update={"roi": LaneROI("r1", 0, 5, 60, 25), "reviewed": True}
    )
    changed = {**dict(project), "rows": (changed_row, *project.rows[1:])}
    with pytest.raises(ValueError, match="输入已改变"):
        WBIntakeWorkflowProject.model_validate(changed)
    # Even bypassing construction cannot make a stale reply acceptable.
    with pytest.raises(ValueError, match="输入已改变"):
        finish_intake_workflow_step(
            project.model_copy(update={"rows": changed["rows"]}), compose, "done"
        )


def test_nested_model_copy_cannot_bypass_attempt_validation() -> None:
    project, ticket = claim_intake_workflow_step(approved(), session_key="a")
    assert ticket is not None
    invalid = project.workflow.steps[0].model_copy(update={"attempt": 0, "claim_id": ""})
    ledger = project.workflow.model_copy(update={"steps": (invalid, *project.workflow.steps[1:])})
    tampered = project.model_copy(update={"workflow": ledger})
    with pytest.raises(ValueError, match="实际尝试"):
        intake_workflow_snapshot(tampered)
