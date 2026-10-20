"""Explicit post-execution edits retain history and invalidate only dependent identities."""

import json
from pathlib import Path

import pytest
from wb_tool.api import (
    IntakeAcquisitionGroup,
    IntakeDraftFigure,
    IntakeGrouping,
    IntakeManifest,
    WBIntakeOutputProject,
    approve_intake_workflow,
    begin_intake_group_revision,
    claim_intake_workflow_step,
    complete_intake_figure,
    confirm_intake_group_revision,
    intake_digest,
    intake_workflow_digest,
    prepare_intake_figure,
    read_figure_project,
    revise_intake_grouping,
)

from .test_intake_figure import asset
from .test_intake_output import full_files


def grouped_full(tmp_path: Path):
    project, paths, runs = full_files(tmp_path)
    # Equivalent grouping annotations for the existing synthetic full-chain fixture.
    grouping = IntakeGrouping(
        figures=tuple(IntakeDraftFigure(**dict(f)) for f in project.intake.figures),
        groups=tuple(
            IntakeAcquisitionGroup(
                group_id=p.protein_id,
                source_ids=(p.protein_id,),
                figure_id=p.figure_id,
                protein_label=p.label,
                selected_source_id=p.protein_id,
            )
            for p in project.intake.proteins
        ),
    )
    first = grouping.groups[0]
    grouping = grouping.model_copy(
        update={
            "groups": (
                first.model_copy(update={"source_ids": (*first.source_ids, "alternate")}),
                *grouping.groups[1:],
            )
        }
    )
    original = project.intake.sources[0]
    alternate = original.model_copy(
        update={
            "source_id": "alternate",
            "original_name": "alternate.tiff",
            "relative_path": "alternate.tiff",
        }
    )
    manifest = IntakeManifest.model_validate(
        {
            **dict(project.intake),
            "schema_version": 3,
            "grouping": grouping,
            "sources": (*project.intake.sources, alternate),
            "confirmed_digest": "",
        }
    )
    candidate = project.model_copy(update={"intake": manifest})
    digest = intake_digest(candidate)
    return (
        WBIntakeOutputProject.model_validate(
            {
                **dict(project),
                "intake": manifest.model_copy(update={"confirmed_digest": digest}),
                "workflow": project.workflow.model_copy(update={"intake_digest": digest}),
            }
        ),
        paths,
        runs,
    )


def statuses(project: WBIntakeOutputProject):
    return {(s.stage, s.target_id): s.status for s in project.workflow.steps}


@pytest.mark.parametrize("change", ["source", "cancel", "n", "unknown-n", "move"])
def test_geometry_changes_revoke_only_affected_current_evidence(
    tmp_path: Path, change: str
) -> None:
    original, _, _ = grouped_full(tmp_path)
    frozen = original.model_dump_json()
    editing = begin_intake_group_revision(original, expected_digest=intake_digest(original))
    assert isinstance(editing, WBIntakeOutputProject)
    grouping = editing.intake.grouping
    assert grouping is not None
    if change in {"n", "unknown-n"}:
        grouping = grouping.model_copy(
            update={
                "figures": (
                    grouping.figures[0].model_copy(
                        update={"lane_count": 4 if change == "n" else None}
                    ),
                    *grouping.figures[1:],
                )
            }
        )
    else:
        update = {"selected_source_id": "alternate" if change == "source" else None}
        if change == "move":
            update = {"figure_id": "b"}
        grouping = grouping.model_copy(
            update={
                "groups": (
                    grouping.groups[0].model_copy(update=update),
                    *grouping.groups[1:],
                )
            }
        )
    revised = revise_intake_grouping(editing, grouping, expected_digest=intake_digest(editing))
    assert isinstance(revised, WBIntakeOutputProject)
    assert revised.workflow.editing and not revised.workflow.approved
    assert not revised.intake.confirmed_digest
    assert not any(e.row_id == "a1" for e in revised.intake_crops)
    assert not any(p.row_id == "a1" for p in revised.analyses)
    assert not any(e.figure_id == "a" for e in revised.intake_figures)
    if change == "move":
        assert not revised.intake_figures
        assert statuses(revised)["compose", "b"] == "pending"
    else:
        assert next(e for e in revised.intake_figures if e.figure_id == "b") == next(
            e for e in original.intake_figures if e.figure_id == "b"
        )
        assert statuses(revised)["measure", "b"] == "done"
        assert (
            next(p for p in revised.analyses if p.row_id == "b1").run
            == next(p for p in original.analyses if p.row_id == "b1").run
        )
    if change in {"n", "unknown-n"}:
        assert not any(e.row_id == "a2" for e in revised.intake_crops)
    else:
        assert next(e for e in revised.intake_crops if e.row_id == "a2").raw_crop is not None
    assert original.model_dump_json() == frozen
    assert read_figure_project(revised.model_dump_json().encode()) == revised
    with pytest.raises(ValueError, match="先保存并确认"):
        approve_intake_workflow(revised, expected_digest=intake_workflow_digest(revised))
    if change in {"cancel", "unknown-n"}:
        with pytest.raises(ValueError):
            confirm_intake_group_revision(revised, expected_digest=intake_digest(revised))
    else:
        confirmed = confirm_intake_group_revision(revised, expected_digest=intake_digest(revised))
        assert not confirmed.workflow.editing and not confirmed.workflow.approved


@pytest.mark.parametrize("change", ["protein", "figure", "order"])
def test_label_and_order_edits_rebuild_display_and_reuse_identical_actual_runs(
    tmp_path: Path, change: str
) -> None:
    original, paths, _ = grouped_full(tmp_path)
    editing = begin_intake_group_revision(original, expected_digest=intake_digest(original))
    grouping = editing.intake.grouping
    assert grouping is not None
    if change == "figure":
        grouping = grouping.model_copy(
            update={
                "figures": (
                    grouping.figures[0].model_copy(update={"label": "Updated Fig"}),
                    *grouping.figures[1:],
                )
            }
        )
    else:
        groups = (
            (grouping.groups[1], grouping.groups[0], grouping.groups[2])
            if change == "order"
            else (
                grouping.groups[0].model_copy(update={"protein_label": "AKT2"}),
                *grouping.groups[1:],
            )
        )
        grouping = grouping.model_copy(update={"groups": groups})
    revised = revise_intake_grouping(editing, grouping, expected_digest=intake_digest(editing))
    assert isinstance(revised, WBIntakeOutputProject)
    assert revised.intake_crops == original.intake_crops
    assert revised.analyses == original.analyses
    assert statuses(revised)["compose", "a"] == "pending"
    confirmed = confirm_intake_group_revision(revised, expected_digest=intake_digest(revised))
    active, ticket = claim_intake_workflow_step(
        approve_intake_workflow(confirmed, expected_digest=intake_workflow_digest(confirmed)),
        session_key="new-label",
        stage_filter="compose",
    )
    assert isinstance(active, WBIntakeOutputProject) and ticket is not None
    path = tmp_path / "relabeled.png"
    result = prepare_intake_figure(active, ticket, paths, str(path))
    completed = complete_intake_figure(active, ticket, result, asset(path))
    assert isinstance(completed, WBIntakeOutputProject)
    assert statuses(completed)["measure", "a"] == "done"
    assert {p.row_id: p.run for p in completed.analyses} == {
        p.row_id: p.run for p in original.analyses
    }
    assert statuses(completed)["export", completed.project_id] == "pending"
    assert read_figure_project(completed.model_dump_json().encode()) == completed


def test_editing_requires_explicit_entry_and_keeps_v1_wire_shape(tmp_path: Path) -> None:
    original, _, _ = grouped_full(tmp_path)
    assert "editing" not in json.loads(original.model_dump_json())["workflow"]
    assert original.intake.grouping is not None
    with pytest.raises(ValueError, match="先明确进入"):
        revise_intake_grouping(
            original, original.intake.grouping, expected_digest=intake_digest(original)
        )
    with pytest.raises(ValueError, match="当前清单已变化"):
        begin_intake_group_revision(original, expected_digest="old")
    active, ticket = claim_intake_workflow_step(original, session_key="running-export")
    assert ticket is not None
    with pytest.raises(ValueError, match="阶段退出"):
        begin_intake_group_revision(active, expected_digest=intake_digest(active))
    editing = begin_intake_group_revision(original, expected_digest=intake_digest(original))
    assert json.loads(editing.model_dump_json())["workflow"]["policy"] == "intake_workflow@2"
    confirmed = confirm_intake_group_revision(editing, expected_digest=intake_digest(editing))
    assert isinstance(confirmed, WBIntakeOutputProject)
    assert confirmed.intake_crops == original.intake_crops
    assert confirmed.analyses == original.analyses
