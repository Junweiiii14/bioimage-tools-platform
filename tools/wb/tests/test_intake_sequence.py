"""Ordered user labels never change the acquisition identity or source-pixel selection."""

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from wb_tool.api import (
    IntakeAcquisitionGroup,
    IntakeDraftFigure,
    IntakeGrouping,
    IntakeSequenceProtein,
    WBIntakeProject,
    approve_intake_workflow,
    claim_intake_workflow_step,
    configure_intake_sequence,
    confirm_intake,
    finish_intake_workflow_step,
    intake_digest,
    intake_grouping,
    intake_workflow_digest,
    intake_workflow_snapshot,
    read_figure_project,
    retry_intake_workflow_step,
    save_intake_grouping,
)

from .test_intake_grouping import pool
from .test_intake_workflow import workflow


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
    observed = []
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
