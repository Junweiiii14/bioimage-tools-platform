"""Latest Intake edits retain history while invalidating only the appropriate dependencies."""

from hashlib import sha256
from pathlib import Path

import pytest
from wb_tool.api import (
    IntakeManifest,
    IntakeSequenceProtein,
    MetadataCell,
    MetadataEntry,
    MetadataPreview,
    ProjectOCRState,
    WBFigureProject,
    WBIntakeOutputProject,
    apply_workbench_metadata,
    claim_intake_workflow_step,
    configure_intake_sequence,
    export_intake_outputs,
    intake_digest,
    prepare_workbench_revision,
    project_with_normalizations,
    project_with_ocr,
    read_figure_project,
    record_intake_output,
    revise_workbench_figure_order,
    workbench_project_digest,
)

from .test_intake_execution import confirmed
from .test_intake_figure import asset
from .test_intake_group_revision import grouped_full, statuses


def apply(project: WBFigureProject, rows: tuple[str, ...], **values: str) -> WBFigureProject:
    entries = tuple(
        MetadataEntry(
            i + 1,
            key,
            (key,),
            key,
            tuple((field, MetadataCell(value)) for field, value in values.items()),
        )
        for i, key in enumerate(rows)
    )
    return apply_workbench_metadata(
        project,
        MetadataPreview(
            workbench_project_digest(project),
            "explicit",
            entries,
        ),
        entries,
        tuple(values),
    )


def test_presentation_change_keeps_original_pixels_runs_and_current_schema(tmp_path: Path):
    original, _, _ = grouped_full(tmp_path)
    frozen = original.model_dump_json()
    prepared = prepare_workbench_revision(
        original, expected_digest=workbench_project_digest(original), impact="figures"
    )
    updated = type(prepared).model_validate(
        {**dict(prepared), "template": prepared.template.model_copy(update={"font_size": 25})}
    )
    assert isinstance(updated, WBIntakeOutputProject)
    assert updated.analyses == original.analyses
    assert updated.intake_crops == original.intake_crops
    assert updated.intake_outputs == original.intake_outputs
    assert not updated.intake_figures and not updated.workflow.approved
    assert {s.status for s in updated.workflow.steps if s.stage != "crop"} == {"pending"}
    assert original.model_dump_json() == frozen
    assert read_figure_project(updated.model_dump_json().encode()) == updated
    with pytest.raises(ValueError, match="项目已改变"):
        prepare_workbench_revision(updated, expected_digest=workbench_project_digest(original))


def test_auxiliary_change_preserves_completed_measurement(tmp_path: Path):
    original, _, _ = grouped_full(tmp_path)
    prepared = prepare_workbench_revision(
        original, expected_digest=workbench_project_digest(original)
    )
    updated = project_with_normalizations(prepared, ())
    assert isinstance(updated, WBIntakeOutputProject)
    assert updated.intake_figures == original.intake_figures
    assert updated.analyses == original.analyses
    assert statuses(updated)["measure", "a"] == "done"
    assert statuses(updated)["export", updated.project_id] == "pending"


def test_metadata_renaming_and_n_keep_stable_source_identities(tmp_path: Path):
    original, _, _ = grouped_full(tmp_path)
    renamed = apply(original, ("a1",), protein="AKT2")
    assert isinstance(renamed, WBIntakeOutputProject)
    assert renamed.workflow.editing and not renamed.workflow.approved
    assert renamed.rows[0].protein == "AKT2"
    assert renamed.analyses == original.analyses and renamed.intake_crops == original.intake_crops
    assert statuses(renamed)["measure", "b"] == "done"
    with pytest.raises(ValueError, match="必须一致"):
        apply(original, ("a1",), lane_count="4")
    changed = apply(original, ("a1", "a2"), lane_count="4")
    assert isinstance(changed, WBIntakeOutputProject)
    assert [r.lane_count for r in changed.rows[:2]] == [4, 4]
    assert not any(e.row_id in {"a1", "a2"} for e in changed.intake_crops)
    assert (
        next(p for p in changed.analyses if p.row_id == "b1").run
        == next(p for p in original.analyses if p.row_id == "b1").run
    )
    assert changed.intake.grouping is not None and original.intake.grouping is not None
    assert [
        (g.group_id, g.source_ids, g.selected_source_id) for g in changed.intake.grouping.groups
    ] == [(g.group_id, g.source_ids, g.selected_source_id) for g in original.intake.grouping.groups]
    assert read_figure_project(changed.model_dump_json().encode()) == changed


def test_notes_empty_lanes_order_and_schema10_constraints(tmp_path: Path):
    original, _, _ = grouped_full(tmp_path)
    notes = apply(original, ("a1",), notes="explicit review")
    assert notes.rows[0].notes == "explicit review"
    assert isinstance(notes, WBIntakeOutputProject)
    assert [f.figure_id for f in notes.intake_figures] == ["b"]
    changed = apply(original, ("a1",), empty_lanes="2")
    assert isinstance(changed, WBIntakeOutputProject)
    assert changed.rows[0].empty_lanes == (2,) and not changed.rows[0].reviewed
    assert statuses(changed)["crop", "a1"] == "pending"
    assert statuses(changed)["measure", "b"] == "done"
    reordered = revise_workbench_figure_order(
        original,
        tuple(reversed(original.figure_order)),
        expected_digest=workbench_project_digest(original),
    )
    assert reordered.figure_order == tuple(reversed(original.figure_order))
    assert read_figure_project(reordered.model_dump_json().encode()) == reordered
    initial = confirmed()
    with pytest.raises(ValueError, match="准备阶段"):
        apply(initial, (initial.rows[0].row_id,), notes="not yet")
    assert initial.rows[0].source is not None
    with pytest.raises(ValueError):
        project_with_ocr(
            initial,
            ProjectOCRState(
                source=initial.rows[0].source,
                filename=initial.rows[0].filename,
                width=initial.rows[0].width,
                height=initial.rows[0].height,
            ),
        )


def test_latest_sequence_preserves_entry_and_source_identity_across_web_edits(tmp_path: Path):
    original, _, _ = grouped_full(tmp_path)
    grouping = original.intake.grouping
    assert grouping is not None
    sequence = configure_intake_sequence(
        grouping,
        grouping.figures,
        tuple(
            IntakeSequenceProtein(
                entry_id="entry-" + g.group_id,
                figure_id=g.figure_id,
                label=g.protein_label,
            )
            for g in grouping.groups
            if g.figure_id is not None
        ),
    )
    manifest = IntakeManifest.model_validate(
        {**dict(original.intake), "schema_version": 4, "grouping": sequence, "confirmed_digest": ""}
    )
    digest = intake_digest(original.model_copy(update={"intake": manifest}))
    original = type(original).model_validate(
        {
            **dict(original),
            "intake": manifest.model_copy(update={"confirmed_digest": digest}),
            "workflow": original.workflow.model_copy(update={"intake_digest": digest}),
        }
    )
    renamed = apply(original, ("a1",), protein="new protein")
    reordered = revise_workbench_figure_order(
        original,
        tuple(reversed(original.figure_order)),
        expected_digest=workbench_project_digest(original),
    )
    for updated in (renamed, reordered, apply(original, ("a1", "a2"), lane_count="4")):
        assert isinstance(updated, WBIntakeOutputProject)
        assert updated.intake.schema_version == 4
        assert updated.intake.grouping is not None
        assert updated.intake.grouping.sequence is not None
        assert {e.entry_id for e in updated.intake.grouping.sequence} == {
            "entry-" + g.group_id for g in grouping.groups
        }
        assert {
            g.group_id: (g.source_ids, g.selected_source_id) for g in updated.intake.grouping.groups
        } == {g.group_id: (g.source_ids, g.selected_source_id) for g in grouping.groups}
        assert read_figure_project(updated.model_dump_json().encode()) == updated


def test_completed_publication_is_immutable_after_web_presentation_and_ocr_revision(tmp_path: Path):
    project, paths, runs = grouped_full(tmp_path)
    active, ticket = claim_intake_workflow_step(
        project, session_key="publish", stage_filter="export"
    )
    assert ticket is not None and isinstance(active, WBIntakeOutputProject)
    destination = tmp_path / "published"
    output = export_intake_outputs(active, paths, str(destination), runs=runs, ticket=ticket)
    saved = record_intake_output(active, output, asset(destination / "index.json"), ticket=ticket)
    files = {p: sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob("*") if p.is_file()}
    for impact in ("outputs", "figures"):
        updated = prepare_workbench_revision(
            saved,
            expected_digest=workbench_project_digest(saved),
            impact=impact,
        )
        assert isinstance(updated, WBIntakeOutputProject)
        assert updated.intake_outputs == saved.intake_outputs and updated.intake_outputs
        assert updated.analyses == saved.analyses
        assert statuses(updated)["export", updated.project_id] == "pending"
        assert read_figure_project(updated.model_dump_json().encode()) == updated
    assert files == {
        p: sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob("*") if p.is_file()
    }
