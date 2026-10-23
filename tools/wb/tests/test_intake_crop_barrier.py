"""Every crop asset is required, while failed rows never suppress later crop attempts."""

from pathlib import Path

import pytest
from tool_contracts.api import AssetRef
from wb_tool.api import (
    IntakeWorkflowTicket,
    LaneROI,
    WBIntakeCropProject,
    adopt_intake_crop_barrier,
    approve_intake_workflow,
    claim_intake_workflow_step,
    complete_intake_crop,
    continue_intake_sequence,
    export_intake_outputs,
    fail_intake_crop,
    finalize_intake_delivery,
    finish_intake_workflow_step,
    intake_workflow_digest,
    intake_workflow_snapshot,
    materialize_intake_delivery,
    prepare_intake_crops,
    prepare_intake_delivery,
    read_figure_project,
    record_intake_crop_proposal,
    review_intake_crop,
)

from .test_intake_workflow import workflow


def batch(policy: str = "intake_workflow@5") -> WBIntakeCropProject:
    old = workflow()
    project = prepare_intake_crops(
        type(old).model_validate(
            {**dict(old), "workflow": {**dict(old.workflow), "policy": policy}}
        )
    )
    return approve(project)


def approve(project: WBIntakeCropProject) -> WBIntakeCropProject:
    result = approve_intake_workflow(project, expected_digest=intake_workflow_digest(project))
    assert isinstance(result, WBIntakeCropProject)
    return result


def commit_reviewed_crop(project: WBIntakeCropProject, row_id: str) -> WBIntakeCropProject:
    reviewed = review_intake_crop(
        project,
        row_id,
        LaneROI(row_id, 6, 5, 54, 20),
        expected_digest=intake_workflow_digest(project),
    )
    active, ticket = claim_intake_workflow_step(approve(reviewed), session_key="crop-export")
    assert isinstance(active, WBIntakeCropProject)
    assert ticket is not None and ticket.stage == "crop" and ticket.target_id == row_id
    return complete_intake_crop(
        active,
        ticket,
        AssetRef(
            asset_id=f"raw-{row_id}",
            relative_path=f"assets/{row_id}.tiff",
            sha256=("a" if row_id == "r1" else "b") * 64,
            size_bytes=16,
        ),
    )


def unresolved(
    project: WBIntakeCropProject, ticket: IntakeWorkflowTicket, outcome: str
) -> WBIntakeCropProject:
    failed = fail_intake_crop(project, ticket, "source needs correction")
    if outcome == "failed":
        return failed
    evidence = next(e for e in failed.intake_crops if e.row_id == ticket.target_id)
    return record_intake_crop_proposal(project, ticket, evidence)


@pytest.mark.parametrize("outcome", ["needs_review", "failed"])
def test_failed_row_drains_other_crops_but_blocks_every_downstream_stage(outcome: str) -> None:
    active, first = claim_intake_workflow_step(batch(), session_key="initial")
    assert first is not None and isinstance(active, WBIntakeCropProject)
    paused = unresolved(active, first, outcome)
    assert isinstance(paused, WBIntakeCropProject)
    assert intake_workflow_snapshot(paused)["pending_ready"] == 1
    active, second = claim_intake_workflow_step(paused, session_key="remaining")
    assert second is not None and second.target_id == "r2"
    assert isinstance(active, WBIntakeCropProject)
    proposed = unresolved(active, second, "needs_review")
    assert isinstance(proposed, WBIntakeCropProject)
    cropped = commit_reviewed_crop(proposed, "r2")
    saved_step = cropped.workflow.steps[1]
    saved_crop = next(e for e in cropped.intake_crops if e.row_id == "r2")
    assert saved_crop.raw_crop is not None
    assert not intake_workflow_snapshot(cropped)["crop_barrier_ready"]
    assert intake_workflow_snapshot(cropped)["pending_ready"] == 0
    for stage in (None, "compose", "measure", "export"):
        assert (
            claim_intake_workflow_step(cropped, session_key="blocked", stage_filter=stage)[1]
            is None
        )
    repaired = commit_reviewed_crop(cropped, "r1")
    assert repaired.workflow.steps[1] == saved_step
    assert next(e for e in repaired.intake_crops if e.row_id == "r2") == saved_crop
    assert intake_workflow_snapshot(repaired)["crop_barrier_ready"]
    _, next_ticket = claim_intake_workflow_step(repaired, session_key="after-repair")
    assert next_ticket is not None and next_ticket.stage == "compose"
    assert read_figure_project(repaired.model_dump_json().encode()) == repaired


def test_done_ledger_without_saved_original_crop_is_not_a_barrier_pass() -> None:
    project = batch()
    for _ in range(2):
        active, ticket = claim_intake_workflow_step(project, session_key="ledger-only")
        assert ticket is not None and ticket.stage == "crop"
        done = finish_intake_workflow_step(active, ticket, "done")
        assert isinstance(done, WBIntakeCropProject)
        project = done
    assert not project.intake_crops
    assert not intake_workflow_snapshot(project)["crop_barrier_ready"]
    assert claim_intake_workflow_step(project, session_key="no-assets")[1] is None


def test_explicit_v4_continue_upgrades_without_rewriting_success_or_history() -> None:
    active, first = claim_intake_workflow_step(batch("intake_workflow@4"), session_key="legacy")
    assert first is not None
    blocked = finish_intake_workflow_step(active, first, "needs_review", reason="missing row")
    assert isinstance(blocked, WBIntakeCropProject)
    before = blocked.model_dump_json()
    with pytest.raises(ValueError, match="阶段输入已变化"):
        adopt_intake_crop_barrier(blocked, expected_digest="stale")
    upgraded = continue_intake_sequence(
        blocked,
        expected_digest=intake_workflow_digest(blocked),
        use_crop_barrier=True,
    )
    assert upgraded.workflow.policy == "intake_workflow@5"
    assert upgraded.workflow.steps == blocked.workflow.steps
    assert upgraded.intake_crops == blocked.intake_crops
    assert blocked.model_dump_json() == before
    assert read_figure_project(before.encode()) == blocked  # Opening alone preserves v4.
    active, second = claim_intake_workflow_step(approve(upgraded), session_key="new-policy")
    assert second is not None and second.target_id == "r2"
    with pytest.raises(ValueError, match="等待当前阶段退出"):
        adopt_intake_crop_barrier(active, expected_digest=intake_workflow_digest(active))


def test_v5_public_publish_apis_reject_before_writing_but_v4_keeps_partial_outputs(
    tmp_path: Path,
) -> None:
    from wb_tool.adapters.intake_table_export import export_intake_table

    from .test_intake_output import partial_files

    original, sources = partial_files(tmp_path)
    legacy = type(original).model_validate(
        {**dict(original), "workflow": {**dict(original.workflow), "policy": "intake_workflow@4"}}
    )
    modern = adopt_intake_crop_barrier(legacy, expected_digest=intake_workflow_digest(legacy))
    assert isinstance(modern, type(original))
    before = legacy.model_dump_json()
    output = tmp_path / "blocked-output"
    table = tmp_path / "blocked.csv"
    delivery_parent = tmp_path / "blocked-delivery"
    configured = prepare_intake_delivery(
        modern,
        output_parent=str(delivery_parent),
        workspace_path=str(tmp_path / "workspace"),
        delivery_id="a" * 32,
    )
    assert isinstance(configured, type(original))
    with pytest.raises(ValueError, match="全部裁剪"):
        export_intake_outputs(modern, sources, str(output), ticket=None)
    with pytest.raises(ValueError, match="全部裁剪"):
        export_intake_table(modern, (), str(table))
    with pytest.raises(ValueError, match="全部裁剪"):
        finalize_intake_delivery(configured, sources, workspace_path=str(tmp_path / "workspace"))
    assert not output.exists() and not table.exists() and not delivery_parent.exists()
    assert not list(tmp_path.glob(".wb-intake-output-*"))

    # Incremental source/raw-crop placement is still allowed; final publication is not.
    delivery_parent.mkdir()
    receipt = materialize_intake_delivery(
        configured, sources, workspace_path=str(tmp_path / "workspace")
    )
    staged_root = Path(receipt.destination)
    staged = {
        p.relative_to(staged_root): p.read_bytes() for p in staged_root.rglob("*") if p.is_file()
    }
    assert any("原始图片" in str(p) for p in staged)
    assert any("原值裁剪" in str(p) for p in staged)
    with pytest.raises(ValueError, match="全部裁剪"):
        finalize_intake_delivery(configured, sources, workspace_path=str(tmp_path / "workspace"))
    assert {
        p.relative_to(staged_root): p.read_bytes() for p in staged_root.rglob("*") if p.is_file()
    } == staged

    # Compatibility controls execute each real publisher, without bypassing its verifier.
    partial = export_intake_outputs(legacy, sources, str(tmp_path / "legacy-output"))
    assert not partial.complete and Path(partial.path).is_file()
    assert export_intake_table(legacy, (), str(tmp_path / "legacy.csv")).is_file()
    old_delivery = prepare_intake_delivery(
        legacy,
        output_parent=str(tmp_path),
        workspace_path=str(tmp_path / "workspace"),
        delivery_id="b" * 32,
    )
    assert isinstance(old_delivery, type(original))
    published = finalize_intake_delivery(
        old_delivery, sources, workspace_path=str(tmp_path / "workspace")
    )
    assert not published.complete and Path(published.path).is_file()
    assert legacy.model_dump_json() == before
