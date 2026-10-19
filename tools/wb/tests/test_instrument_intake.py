"""Intake identities, atomic mapping and durable source-pool evidence without algorithms."""

import json

import pytest
from tool_contracts.api import AssetRef
from wb_tool.api import (
    FigureRow,
    IntakeAssignment,
    IntakeFigure,
    IntakeProtein,
    IntakeSource,
    LaneROI,
    StagedProjectArchive,
    WBFigureProject,
    WBIntakeProject,
    assign_intake_sources,
    confirm_intake,
    create_intake,
    intake_digest,
    intake_snapshot,
    project_assets,
    read_figure_project,
    register_intake_source,
    replace_intake_plan,
    restore_staged_project,
    unassign_intake_sources,
)


def source(number: int, *, digest: str = "", relative: str = "") -> IntakeSource:
    return IntakeSource(
        source_id=f"source-{number}",
        asset=AssetRef(
            asset_id=f"asset-{number}",
            relative_path=f"assets/{number}.tiff",
            sha256=digest or f"{number:064x}",
            size_bytes=128,
        ),
        original_name="Image001.tiff",
        relative_path=relative or f"folder-{number}/Image001.tiff",
        width=120,
        height=80,
        bit_depth=16,
    )


def planned() -> WBIntakeProject:
    project = create_intake(WBFigureProject(project_id="intake"))
    project = replace_intake_plan(
        project,
        (IntakeFigure(figure_id="fig-id", label="Fig1", lane_count=8),),
        (
            IntakeProtein(protein_id="p1", figure_id="fig-id", label="GAPDH"),
            IntakeProtein(protein_id="p2", figure_id="fig-id", label="GAPDH"),
        ),
        expected_digest=intake_digest(project),
    )
    for index in (1, 2, 3):
        project = register_intake_source(
            project, source(index), expected_digest=intake_digest(project)
        )
    return project


def assigned() -> WBIntakeProject:
    project = planned()
    return assign_intake_sources(
        project,
        (
            IntakeAssignment(protein_id="p1", source_id="source-2"),
            IntakeAssignment(protein_id="p2", source_id="source-1"),
        ),
        expected_digest=intake_digest(project),
    )


def test_duplicate_names_and_unassigned_sources_survive_confirm_save_reopen() -> None:
    project = assigned()
    confirmed = confirm_intake(project, expected_digest=intake_digest(project))
    reopened = read_figure_project(confirmed.model_dump_json().encode())
    assert isinstance(reopened, WBIntakeProject) and reopened == confirmed
    assert [r.row_id for r in reopened.rows] == ["p1", "p2"]
    assert [r.source for r in reopened.rows] == [source(2).asset, source(1).asset]
    assert [s.relative_path for s in reopened.intake.sources] == [
        "folder-1/Image001.tiff",
        "folder-2/Image001.tiff",
        "folder-3/Image001.tiff",
    ]
    assert {asset.asset_id: asset for asset in project_assets(reopened)} == {
        source(n).asset.asset_id: source(n).asset for n in (1, 2, 3)
    }
    assert all(r.roi is None and not r.reviewed and not r.empty_lanes for r in reopened.rows)
    assert not reopened.analyses and reopened.ocr is None and not reopened.partition_sources
    assert intake_snapshot(reopened)["confirmed"] is True
    assert json.loads(json.dumps(intake_snapshot(reopened)))["digest"] == intake_digest(reopened)


def test_fig_plan_can_precede_sources_and_keeps_only_shared_count() -> None:
    empty = create_intake(WBFigureProject(project_id="empty"))
    figure = IntakeFigure(figure_id="stable", label="Figure alpha", lane_count=96)
    empty_fig = replace_intake_plan(empty, (figure,), (), expected_digest=intake_digest(empty))
    assert not empty_fig.rows and not empty_fig.figure_order
    assert read_figure_project(empty_fig.model_dump_json().encode()) == empty_fig
    project = replace_intake_plan(
        empty_fig,
        (figure,),
        (IntakeProtein(protein_id="p", figure_id="stable", label="AKT"),),
        expected_digest=intake_digest(empty_fig),
    )
    assert project.rows[0].source is None and project.rows[0].lane_count == 96
    assert "sample" not in project.intake.model_dump_json()
    with pytest.raises(ValueError, match="未分配"):
        confirm_intake(project, expected_digest=intake_digest(project))


def test_plan_edit_preserves_ids_and_assignments_and_revokes_confirmation() -> None:
    project = assigned()
    confirmed = confirm_intake(project, expected_digest=intake_digest(project))
    edited = replace_intake_plan(
        confirmed,
        (IntakeFigure(figure_id="fig-id", label="Renamed Fig", lane_count=3),),
        confirmed.intake.proteins,
        expected_digest=intake_digest(confirmed),
    )
    assert [r.row_id for r in edited.rows] == ["p1", "p2"]
    assert [r.lane_count for r in edited.rows] == [3, 3]
    assert [r.figure for r in edited.rows] == ["Renamed Fig", "Renamed Fig"]
    assert edited.intake.assignments == confirmed.intake.assignments
    assert not edited.intake.confirmed_digest
    with pytest.raises(ValueError, match="已修改"):
        confirm_intake(edited, expected_digest=intake_digest(confirmed))


def test_batch_failure_is_atomic_and_replacement_requires_explicit_action() -> None:
    project = planned()
    before = project.model_dump_json()
    with pytest.raises(ValueError, match="不存在"):
        assign_intake_sources(
            project,
            (
                IntakeAssignment(protein_id="p1", source_id="source-1"),
                IntakeAssignment(protein_id="p2", source_id="missing"),
            ),
            expected_digest=intake_digest(project),
        )
    assert project.model_dump_json() == before
    project = assigned()
    with pytest.raises(ValueError, match="重新分配"):
        assign_intake_sources(
            project,
            (IntakeAssignment(protein_id="p1", source_id="source-3"),),
            expected_digest=intake_digest(project),
        )
    replaced = assign_intake_sources(
        project,
        (IntakeAssignment(protein_id="p1", source_id="source-3"),),
        expected_digest=intake_digest(project),
        replace=True,
    )
    assert replaced.rows[0].row_id == "p1" and replaced.rows[0].source == source(3).asset
    assert replaced.intake.sources == project.intake.sources


def test_source_alias_cannot_bypass_explicit_reuse() -> None:
    project = planned()
    alias = source(4, digest=source(1).asset.sha256, relative="folder-1/Image001.tiff")
    project = register_intake_source(project, alias, expected_digest=intake_digest(project))
    bindings = (
        IntakeAssignment(protein_id="p1", source_id="source-1"),
        IntakeAssignment(protein_id="p2", source_id="source-4", reuse_confirmed=True),
    )
    with pytest.raises(ValueError, match="复用"):
        assign_intake_sources(project, bindings, expected_digest=intake_digest(project))
    reused = assign_intake_sources(
        project, bindings, expected_digest=intake_digest(project), allow_reuse=True
    )
    assert all(binding.reuse_confirmed for binding in reused.intake.assignments)
    assert reused.rows[0].source and reused.rows[1].source
    assert reused.rows[0].source.sha256 == reused.rows[1].source.sha256
    assert read_figure_project(reused.model_dump_json().encode()) == reused


def test_deleting_target_requires_unassignment_and_keeps_raw_pool() -> None:
    project = assigned()
    with pytest.raises(ValueError, match="解除"):
        replace_intake_plan(
            project,
            project.intake.figures,
            project.intake.proteins[:1],
            expected_digest=intake_digest(project),
        )
    cleared = unassign_intake_sources(project, ("p2",), expected_digest=intake_digest(project))
    trimmed = replace_intake_plan(
        cleared,
        cleared.intake.figures,
        cleared.intake.proteins[:1],
        expected_digest=intake_digest(cleared),
    )
    assert len(trimmed.rows) == 1 and trimmed.intake.sources == project.intake.sources


def test_existing_work_and_tampered_projection_are_rejected() -> None:
    project = assigned()
    with pytest.raises(ValueError, match="空项目"):
        create_intake(WBFigureProject(project_id="old", rows=project.rows, figure_order=("Fig1",)))
    row = project.rows[0].model_copy(update={"roi": LaneROI("p1", 0, 0, 120, 40)})
    tampered = {**dict(project), "rows": (row, project.rows[1])}
    with pytest.raises(ValueError, match="裁剪"):
        WBIntakeProject.model_validate(tampered)
    tampered["rows"] = (project.rows[0].model_copy(update={"protein": "wrong"}), project.rows[1])
    with pytest.raises(ValueError, match="不一致"):
        WBIntakeProject.model_validate(tampered)
    confirmed = confirm_intake(project, expected_digest=intake_digest(project))
    payload = confirmed.model_dump(mode="json")
    payload["project_id"] = "another-project"
    with pytest.raises(ValueError, match="过期"):
        read_figure_project(json.dumps(payload).encode())


@pytest.mark.parametrize("count", [0, 97, True, 2.5])
def test_slot_count_is_strict_and_bounded(count: object) -> None:
    with pytest.raises(ValueError):
        IntakeFigure.model_validate({"figure_id": "f", "label": "Fig", "lane_count": count})


@pytest.mark.parametrize("relative", ["../Image001.tiff", "/Image001.tiff", "C:/Image001.tiff"])
def test_source_path_cannot_be_used_for_escape(relative: str) -> None:
    with pytest.raises(ValueError, match="相对路径"):
        source(1, relative=relative)


def test_restore_remaps_unassigned_pool_and_keeps_verified_confirmation() -> None:
    project = assigned()
    project = confirm_intake(project, expected_digest=intake_digest(project))
    archive = AssetRef(
        asset_id="archive", relative_path="assets/archive.zip", sha256="a" * 64, size_bytes=100
    )
    staged = StagedProjectArchive(project, "archive.zip", archive.sha256, (), (), 2)
    imported = tuple(
        source(index).asset.model_copy(
            update={"asset_id": f"new-{index}", "relative_path": f"assets/new-{index}.tiff"}
        )
        for index in (1, 2, 3)
    )
    restored = restore_staged_project(staged, imported, archive)
    assert isinstance(restored, WBIntakeProject)
    assert [s.asset for s in restored.intake.sources] == list(imported)
    assert restored.intake.confirmed_digest == intake_digest(restored)
    assert restored.rows[0].source == imported[1]
    assert {asset.asset_id: asset for asset in project_assets(restored)} == {
        asset.asset_id: asset for asset in (*imported, archive)
    }


def test_schema_one_stays_schema_one() -> None:
    old = WBFigureProject(project_id="old", rows=(FigureRow(row_id="r"),), figure_order=("Fig1",))
    assert type(read_figure_project(old.model_dump_json().encode())) is WBFigureProject
    new = create_intake(WBFigureProject(project_id="new"))
    with pytest.raises(ValueError):
        WBFigureProject.from_bytes(new.model_dump_json().encode())
