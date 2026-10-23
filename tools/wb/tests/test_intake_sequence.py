"""Ordered user labels never change the acquisition identity or source-pixel selection."""

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from wb_tool.api import (
    ExportDiscovery,
    ExportObservation,
    IntakeAcquisitionGroup,
    IntakeDraftFigure,
    IntakeGrouping,
    IntakeSequenceProtein,
    IntakeSource,
    WBIntakeCropProject,
    WBIntakeProject,
    approve_intake_workflow,
    begin_intake_group_revision,
    claim_intake_workflow_step,
    configure_intake_sequence,
    confirm_intake,
    continue_intake_sequence,
    finish_intake_workflow_step,
    install_export_discovery,
    intake_digest,
    intake_grouping,
    intake_workflow_digest,
    intake_workflow_snapshot,
    prepare_intake_crops,
    prepare_intake_sequence,
    read_figure_project,
    register_intake_source,
    retry_intake_workflow_step,
    save_intake_grouping,
)

from .test_intake_grouping import pool
from .test_intake_workflow import workflow


def test_interleaved_reference_groups_do_not_consume_sequence_and_cannot_hide_raw_sources() -> None:
    project = pool()
    original = project.intake.sources[0]
    reference = IntakeSource.model_validate(
        {
            **dict(original),
            "source_id": "ref",
            "original_name": "result.tif",
            "relative_path": "manual/result.tif",
        }
    )
    project = register_intake_source(project, reference, expected_digest=intake_digest(project))
    project = type(project).model_validate(
        {
            **dict(project),
            "intake": project.intake.model_copy(
                update={
                    "sources": (project.intake.sources[0], reference, *project.intake.sources[1:-1])
                }
            ),
        }
    )
    discovered = install_export_discovery(
        project,
        ExportDiscovery(
            observations=tuple(
                ExportObservation(
                    source_id=s.source_id,
                    sha256=s.asset.sha256,
                    group_id="0" * 24,
                    role="reference" if s.source_id == "ref" else "signal",
                )
                for s in project.intake.sources
            )
        ),
        expected_digest=intake_digest(project),
    )
    grouping = intake_grouping(discovered)
    assert len(grouping.groups) == 3 and grouping.reference_group_ids == (
        grouping.groups[1].group_id,
    )
    chosen = type(grouping).model_validate(
        {
            **dict(grouping),
            "groups": tuple(
                g.model_copy(update={"selected_source_id": g.source_ids[0]})
                if g.group_id not in grouping.reference_group_ids
                else g
                for g in grouping.groups
            ),
        }
    )
    configured = configure_intake_sequence(
        chosen,
        (IntakeDraftFigure(figure_id="f", label="Fig", lane_count=4),),
        (
            IntakeSequenceProtein(entry_id="a", figure_id="f", label="A"),
            IntakeSequenceProtein(entry_id="b", figure_id="f", label="B"),
        ),
    )
    assert [g.protein_label for g in configured.groups] == ["A", "", "B"]
    saved = prepare_intake_sequence(
        discovered, configured, expected_digest=intake_digest(discovered)
    )
    assert len(saved.rows) == 2 and saved.intake.grouping == configured
    assert read_figure_project(saved.model_dump_json().encode()) == saved
    forged = configure_intake_sequence(
        grouping, (), (), reference_group_ids=(grouping.groups[0].group_id,)
    )
    with pytest.raises(ValueError, match="参考识别证据"):
        save_intake_grouping(discovered, forged, expected_digest=intake_digest(discovered))


def test_one_submission_is_pure_and_compiles_exact_sequence_before_any_attempt() -> None:
    project = pool()
    original = project.model_dump_json()
    grouping = configuration(project, ("A", "B"))
    prepared = prepare_intake_sequence(project, grouping, expected_digest=intake_digest(project))
    assert project.model_dump_json() == original
    assert prepared.workflow.policy == "intake_workflow@4"
    assert all(s.status == "pending" and s.attempt == 0 for s in prepared.workflow.steps)
    assert prepared.intake.grouping == grouping
    assert read_figure_project(prepared.model_dump_json().encode()) == prepared
    with pytest.raises(ValueError, match="修改"):
        prepare_intake_sequence(project, grouping, expected_digest="stale")
    with pytest.raises(ValueError, match="已有执行计划"):
        prepare_intake_sequence(prepared, grouping, expected_digest=intake_digest(prepared))


def test_continue_requires_human_crop_review_and_retries_only_one_blocked_item() -> None:
    project = pool()
    prepared = prepare_intake_sequence(
        project, configuration(project, ("A", "B")), expected_digest=intake_digest(project)
    )
    # Preserve the historical strict policy's explicit review/retry behavior.
    prepared = type(prepared).model_validate(
        {**dict(prepared), "workflow": {**dict(prepared.workflow), "policy": "intake_workflow@3"}}
    )
    crop = prepare_intake_crops(prepared)
    approved = approve_intake_workflow(crop, expected_digest=intake_workflow_digest(crop))
    active, ticket = claim_intake_workflow_step(approved, session_key="test")
    assert ticket is not None
    review = finish_intake_workflow_step(
        active, ticket, "needs_review", reason="original crop needs confirmation"
    )
    assert isinstance(review, WBIntakeCropProject)
    with pytest.raises(ValueError, match="确认裁剪范围"):
        continue_intake_sequence(review, expected_digest=intake_workflow_digest(review))
    failed = finish_intake_workflow_step(active, ticket, "failed", reason="reader failed")
    assert isinstance(failed, WBIntakeCropProject)
    retried = continue_intake_sequence(failed, expected_digest=intake_workflow_digest(failed))
    assert [s.status for s in retried.workflow.steps] == ["pending"] * len(retried.workflow.steps)
    assert not retried.workflow.approved
    assert retried.workflow.steps[0].attempt == 1


def test_one_submission_confirms_an_explicit_sequence_revision_without_mutating_history() -> None:
    project = pool()
    grouping = configuration(project, ("A", "B"))
    prepared = prepare_intake_sequence(project, grouping, expected_digest=intake_digest(project))
    history = prepared.model_dump_json()
    editing = begin_intake_group_revision(prepared, expected_digest=intake_digest(prepared))
    renamed = configure_intake_sequence(
        grouping,
        (grouping.figures[0].model_copy(update={"label": "Renamed"}),),
        grouping.sequence or (),
    )
    revised = prepare_intake_sequence(editing, renamed, expected_digest=intake_digest(editing))
    assert not revised.workflow.editing and revised.workflow.policy == "intake_workflow@4"
    assert revised.intake.figures[0].label == "Renamed"
    assert prepared.model_dump_json() == history
    assert [(g.group_id, g.selected_source_id) for g in renamed.groups] == [
        (g.group_id, g.selected_source_id) for g in grouping.groups
    ]


def configuration(project: WBIntakeProject, labels: tuple[str, ...]) -> IntakeGrouping:
    original = intake_grouping(project)
    selected = IntakeGrouping(
        groups=tuple(
            g.model_copy(update={"selected_source_id": g.source_ids[0]}) for g in original.groups
        )
    )
    return configure_intake_sequence(
        selected,
        (IntakeDraftFigure(figure_id="f", label="Fig 1", lane_count=4),),
        tuple(
            IntakeSequenceProtein(entry_id=str(i), figure_id="f", label=label)
            for i, label in enumerate(labels)
        ),
    )


def test_sequence_roundtrip_preserves_incomplete_names_and_original_group_identity() -> None:
    project = pool()
    grouping = configuration(project, ("A/B", "", "A/B", "extra"))
    assert [g.protein_label for g in grouping.groups] == ["A/B", "A/B"]
    saved = save_intake_grouping(project, grouping, expected_digest=intake_digest(project))
    assert saved.intake.schema_version == 4
    assert read_figure_project(saved.model_dump_json().encode()) == saved
    assert saved.intake.grouping == grouping
    assert intake_grouping(saved) == grouping
    with pytest.raises(ValueError, match="缺少1个采集组"):
        confirm_intake(saved, expected_digest=intake_digest(saved))
    assert project.intake.schema_version == 1 and not project.intake.grouping


def test_reordering_figs_reassigns_labels_but_sources_stay_with_acquisition() -> None:
    project = pool()
    old = configuration(project, ("A", "B"))
    figures = (
        IntakeDraftFigure(figure_id="f1", label="First", lane_count=4),
        IntakeDraftFigure(figure_id="f2", label="Second", lane_count=5),
    )
    names = (
        IntakeSequenceProtein(entry_id="a", figure_id="f1", label="A"),
        IntakeSequenceProtein(entry_id="b", figure_id="f2", label="B"),
    )
    first = configure_intake_sequence(old, figures, names)
    second = configure_intake_sequence(first, tuple(reversed(figures)), names)
    assert [(g.figure_id, g.protein_label) for g in second.groups] == [("f2", "B"), ("f1", "A")]
    assert [(g.group_id, g.source_ids, g.selected_source_id) for g in first.groups] == [
        (g.group_id, g.source_ids, g.selected_source_id) for g in second.groups
    ]
    assert second.sequence and [p.entry_id for p in second.sequence] == ["b", "a"]


def test_remaining_groups_need_identity_scoped_exclusion_and_cannot_hide_selected_source() -> None:
    project = pool()
    original = configuration(project, ("A",))
    last = original.groups[1]
    unused = last.model_copy(update={"selected_source_id": None})
    original = IntakeGrouping.model_validate(
        {**dict(original), "groups": (original.groups[0], unused)}
    )
    saved = save_intake_grouping(project, original, expected_digest=intake_digest(project))
    with pytest.raises(ValueError, match="剩余采集组"):
        confirm_intake(saved, expected_digest=intake_digest(saved))
    acknowledged = IntakeGrouping.model_validate(
        {**dict(original), "excluded_group_ids": (last.group_id,)}
    )
    saved = save_intake_grouping(saved, acknowledged, expected_digest=intake_digest(saved))
    assert confirm_intake(saved, expected_digest=intake_digest(saved)).intake.confirmed_digest
    selected = IntakeGrouping.model_validate(
        {**dict(acknowledged), "groups": (acknowledged.groups[0], last)}
    )
    saved = save_intake_grouping(saved, selected, expected_digest=intake_digest(saved))
    with pytest.raises(ValueError, match="未归入Fig"):
        confirm_intake(saved, expected_digest=intake_digest(saved))


def test_sequence_projection_and_old_wire_cannot_be_forged() -> None:
    old = IntakeGrouping()
    assert json.loads(old.model_dump_json()) == {"schema_version": 1, "figures": [], "groups": []}
    grouping = configuration(pool(), ("A", "B"))
    wire = json.loads(grouping.model_dump_json())
    wire["groups"][0]["protein_label"] = "different"
    with pytest.raises(ValueError, match="顺序投影"):
        IntakeGrouping.model_validate_json(json.dumps(wire))
    with pytest.raises(ValueError, match="所属Fig"):
        configure_intake_sequence(
            old, (), (IntakeSequenceProtein(entry_id="a", figure_id="missing", label="A"),)
        )


@settings(max_examples=80, deadline=None)
@given(
    st.lists(st.lists(st.text(alphabet="AB 同名/,_012 ", max_size=12), max_size=6), max_size=4),
    st.integers(min_value=0, max_value=16),
)
def test_sequence_conserves_sources_is_idempotent_and_roundtrips(
    names: list[list[str]], group_count: int
) -> None:
    original = IntakeGrouping(
        groups=tuple(
            IntakeAcquisitionGroup(
                group_id=f"g{i}", source_ids=(f"s{i}", f"aux{i}"), selected_source_id=f"s{i}"
            )
            for i in range(group_count)
        )
    )
    figures = tuple(
        IntakeDraftFigure(figure_id=f"f{i}", label=f"Fig{i}", lane_count=i + 1)
        for i in range(len(names))
    )
    entries = tuple(
        IntakeSequenceProtein(entry_id=f"p{i}-{j}", figure_id=f"f{i}", label=label)
        for i, row in enumerate(names)
        for j, label in enumerate(row)
    )
    configured = configure_intake_sequence(original, figures, entries)
    assert [(g.group_id, g.source_ids, g.selected_source_id) for g in configured.groups] == [
        (g.group_id, g.source_ids, g.selected_source_id) for g in original.groups
    ]
    assert configure_intake_sequence(configured, figures, entries) == configured
    assert IntakeGrouping.model_validate_json(configured.model_dump_json()) == configured
    assert configured.sequence == entries


def batch_workflow():
    old = workflow()
    batch = type(old).model_validate(
        {**dict(old), "workflow": {**dict(old.workflow), "policy": "intake_workflow@3"}}
    )
    return approve_intake_workflow(batch, expected_digest=intake_workflow_digest(batch))


def test_batch_barriers_require_all_crops_then_all_figures_before_measurement() -> None:
    project = batch_workflow()
    observed: list[tuple[str, str]] = []
    for _ in range(7):
        if len(observed) < 2:
            assert (
                claim_intake_workflow_step(project, session_key="batch", stage_filter="compose")[1]
                is None
            )
        if len(observed) < 4:
            assert (
                claim_intake_workflow_step(project, session_key="batch", stage_filter="measure")[1]
                is None
            )
        project, ticket = claim_intake_workflow_step(project, session_key="batch")
        assert ticket is not None
        observed.append((ticket.stage, ticket.target_id))
        project = finish_intake_workflow_step(project, ticket, "done")
    assert observed == [
        ("crop", "r1"),
        ("crop", "r2"),
        ("compose", "f1"),
        ("compose", "f2"),
        ("measure", "f1"),
        ("measure", "f2"),
        ("export", "p"),
    ]
    assert not project.analyses  # Stage records never invent real runs.
    assert read_figure_project(project.model_dump_json().encode()) == project


def test_batch_review_pauses_other_figs_and_retry_resumes_owned_attempt() -> None:
    project, first = claim_intake_workflow_step(batch_workflow(), session_key="batch")
    assert first is not None
    project = finish_intake_workflow_step(project, first, "needs_review", reason="核对原图范围")
    assert claim_intake_workflow_step(project, session_key="batch")[1] is None
    assert intake_workflow_snapshot(project)["pending_ready"] == 0
    project = retry_intake_workflow_step(
        project, "crop", "r1", expected_digest=intake_workflow_digest(project)
    )
    project = approve_intake_workflow(project, expected_digest=intake_workflow_digest(project))
    _, retry = claim_intake_workflow_step(project, session_key="batch")
    assert retry is not None and retry.target_id == "r1" and retry.attempt == 2


@pytest.mark.parametrize("outcome", ["needs_review", "failed"])
def test_v4_skips_only_blocked_fig_and_claims_partial_export_after_runnable_work(
    outcome: str,
) -> None:
    old = batch_workflow()
    historical = old.model_dump_json()
    project = type(old).model_validate(
        {**dict(old), "workflow": {**dict(old.workflow), "policy": "intake_workflow@4"}}
    )
    active, ticket = claim_intake_workflow_step(project, session_key="resilient")
    assert ticket is not None and (ticket.stage, ticket.target_id) == ("crop", "r1")
    project = finish_intake_workflow_step(
        active,
        ticket,
        "needs_review" if outcome == "needs_review" else "failed",
        reason="unresolved source",
    )
    observed: list[tuple[str, str]] = []
    for _ in range(3):
        active, ticket = claim_intake_workflow_step(project, session_key="resilient")
        assert ticket is not None
        observed.append((ticket.stage, ticket.target_id))
        project = finish_intake_workflow_step(active, ticket, "done")
    assert observed == [("crop", "r2"), ("compose", "f2"), ("measure", "f2")]
    # This stage-only schema11 fixture has no output payload; the UI deliberately
    # does not advertise an export until schema14+ evidence exists.
    assert intake_workflow_snapshot(project)["pending_ready"] == 0
    active, ticket = claim_intake_workflow_step(project, session_key="resilient")
    assert ticket is not None and ticket.stage == "export"
    # Stage-only fixture makes no scientific success claim. Real partial export is
    # covered through the desktop worker/storage test.
    project = finish_intake_workflow_step(active, ticket, "failed", reason="partial output")
    assert claim_intake_workflow_step(project, session_key="resilient")[1] is None
    assert not intake_workflow_snapshot(project)["stages_finished"]
    assert old.model_dump_json() == historical
    repaired = retry_intake_workflow_step(
        project, "crop", "r1", expected_digest=intake_workflow_digest(project)
    )
    repaired = approve_intake_workflow(repaired, expected_digest=intake_workflow_digest(repaired))
    _, ticket = claim_intake_workflow_step(repaired, session_key="repaired")
    assert ticket is not None and ticket.target_id == "r1" and ticket.attempt == 2
    assert all(s.status == "done" for s in repaired.workflow.steps if s.target_id in {"r2", "f2"})


def test_v4_measurement_failure_keeps_next_fig_runnable() -> None:
    old = batch_workflow()
    project = type(old).model_validate(
        {**dict(old), "workflow": {**dict(old.workflow), "policy": "intake_workflow@4"}}
    )
    for _ in range(4):
        active, ticket = claim_intake_workflow_step(project, session_key="measurement")
        assert ticket is not None
        project = finish_intake_workflow_step(active, ticket, "done")
    active, ticket = claim_intake_workflow_step(project, session_key="measurement")
    assert ticket is not None and (ticket.stage, ticket.target_id) == ("measure", "f1")
    project = finish_intake_workflow_step(active, ticket, "failed", reason="worker failed")
    _, ticket = claim_intake_workflow_step(project, session_key="measurement")
    assert ticket is not None and (ticket.stage, ticket.target_id) == ("measure", "f2")


@pytest.mark.parametrize("policy", ["intake_workflow@3", "intake_workflow@4"])
def test_continue_after_reopen_prioritizes_runnable_v4_work_without_retrying_review(
    policy: str,
) -> None:
    old = batch_workflow()
    project = prepare_intake_crops(
        type(old).model_validate(
            {**dict(old), "workflow": {**dict(old.workflow), "policy": policy}}
        )
    )
    active, ticket = claim_intake_workflow_step(project, session_key="before-reopen")
    assert ticket is not None
    blocked = finish_intake_workflow_step(active, ticket, "needs_review", reason="manual review")
    reopened = read_figure_project(blocked.model_dump_json().encode())
    assert isinstance(reopened, WBIntakeCropProject)
    before = reopened.model_dump_json()
    if policy == "intake_workflow@3":
        with pytest.raises(ValueError, match="确认裁剪范围"):
            continue_intake_sequence(reopened, expected_digest=intake_workflow_digest(reopened))
        return
    with pytest.raises(ValueError, match="阶段输入已变化"):
        continue_intake_sequence(reopened, expected_digest="stale")
    resumed = continue_intake_sequence(reopened, expected_digest=intake_workflow_digest(reopened))
    assert resumed is reopened and resumed.model_dump_json() == before
    active, next_ticket = claim_intake_workflow_step(resumed, session_key="after-reopen")
    assert next_ticket is not None and next_ticket.target_id == "r2"
    assert active.workflow.steps[0] == reopened.workflow.steps[0]
    drained = finish_intake_workflow_step(
        active, next_ticket, "needs_review", reason="second manual review"
    )
    assert isinstance(drained, WBIntakeCropProject)
    with pytest.raises(ValueError, match="确认裁剪范围"):
        continue_intake_sequence(drained, expected_digest=intake_workflow_digest(drained))
