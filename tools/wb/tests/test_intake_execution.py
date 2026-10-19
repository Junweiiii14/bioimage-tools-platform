"""Plan invariants under editing, reopening, hostile labels and independent rows."""

from pathlib import PurePosixPath

import pytest
from hypothesis import given
from hypothesis import strategies as st
from tool_contracts.api import AssetRef
from wb_tool.api import (
    IntakeAssignment,
    IntakeFigure,
    IntakeProtein,
    IntakeSource,
    WBFigureProject,
    WBIntakeProject,
    assign_intake_sources,
    build_intake_execution_plan,
    confirm_intake,
    create_intake,
    intake_digest,
    read_figure_project,
    register_intake_source,
    replace_intake_plan,
)


def confirmed(*, count: int = 3, label: str = "AKT", project_id: str = "p") -> WBIntakeProject:
    project = create_intake(WBFigureProject(project_id=project_id))
    project = replace_intake_plan(
        project,
        (IntakeFigure(figure_id="f", label="Fig1", lane_count=count),),
        (
            IntakeProtein(protein_id="r1", figure_id="f", label=label),
            IntakeProtein(protein_id="r2", figure_id="f", label=label),
        ),
        expected_digest=intake_digest(project),
    )
    for i in (1, 2):
        source = IntakeSource(
            source_id=f"s{i}",
            asset=AssetRef(
                asset_id=f"a{i}", relative_path=f"assets/{i}.tif", sha256=f"{i:064x}", size_bytes=32
            ),
            original_name="001.tif",
            relative_path="instrument/001.tif",
            width=60,
            height=30,
            bit_depth=16,
        )
        project = register_intake_source(project, source, expected_digest=intake_digest(project))
    project = assign_intake_sources(
        project,
        tuple(IntakeAssignment(protein_id=f"r{i}", source_id=f"s{i}") for i in (1, 2)),
        expected_digest=intake_digest(project),
    )
    return confirm_intake(project, expected_digest=intake_digest(project))


def test_plan_has_independent_slots_empty_values_and_no_input_mutation() -> None:
    project = confirmed()
    original = project.model_dump_json()
    plan = build_intake_execution_plan(project, expected_digest=intake_digest(project))
    rows = plan.figures[0].rows
    assert [r.row_id for r in rows] == ["r1", "r2"]
    assert [r.layout_row for r in rows] == [0, 1]
    assert len(plan.cells) == 6
    assert len({c.slot_id for c in plan.cells}) == 6
    assert all(c.value is None and c.status == "pending" for c in plan.cells)
    assert [s.position for s in rows[0].slots] == [1, 2, 3]
    assert project.model_dump_json() == original
    assert project.schema_version == 10 and all(r.roi is None for r in project.rows)


def test_confirmation_and_current_digest_are_required() -> None:
    with pytest.raises(ValueError, match="已确认"):
        build_intake_execution_plan(WBFigureProject(project_id="old"), expected_digest="0" * 64)
    project = confirmed()
    with pytest.raises(ValueError, match="修改"):
        build_intake_execution_plan(project, expected_digest="0" * 64)
    project = replace_intake_plan(
        project,
        (IntakeFigure(figure_id="f", label="Fig changed", lane_count=3),),
        project.intake.proteins,
        expected_digest=intake_digest(project),
    )
    with pytest.raises(ValueError, match="先确认"):
        build_intake_execution_plan(project, expected_digest=intake_digest(project))


@given(st.integers(min_value=1, max_value=96))
def test_save_reopen_and_revision_preserve_plan_and_slot_count(count: int) -> None:
    project = confirmed(count=count)
    plan = build_intake_execution_plan(project, expected_digest=intake_digest(project))
    reopened = read_figure_project(project.model_dump_json().encode())
    assert isinstance(reopened, WBIntakeProject)
    assert build_intake_execution_plan(reopened, expected_digest=intake_digest(reopened)) == plan
    revised = WBIntakeProject.model_validate({**dict(project), "revision": 5})
    revised_plan = build_intake_execution_plan(revised, expected_digest=intake_digest(revised))
    assert revised_plan.plan_key == plan.plan_key
    assert revised_plan.figures == plan.figures and len(plan.cells) == 2 * count


@given(st.text(alphabet="a中/\\:.?*<>|, _😀", min_size=1, max_size=40).map(lambda s: "x" + s))
def test_labels_never_become_paths_or_slot_identity(label: str) -> None:
    first, second = confirmed(), confirmed(label=label)
    a = build_intake_execution_plan(first, expected_digest=intake_digest(first))
    b = build_intake_execution_plan(second, expected_digest=intake_digest(second))
    assert a.plan_key != b.plan_key
    assert a.figures[0].rows[0].slots == b.figures[0].rows[0].slots
    assert a.figures[0].rows[0].geometry_key == b.figures[0].rows[0].geometry_key
    assert a.figures[0].rows[0].raw_crop_path == b.figures[0].rows[0].raw_crop_path
    for row in b.figures[0].rows:
        path = PurePosixPath(row.raw_crop_path)
        assert not path.is_absolute() and ".." not in path.parts and len(path.parts) == 3
        assert row.raw_crop_path.isascii() and "\\" not in row.raw_crop_path


def test_reorder_changes_placement_but_not_geometry_and_n_invalidates_geometry() -> None:
    project = confirmed()
    old = build_intake_execution_plan(project, expected_digest=intake_digest(project))
    changed = replace_intake_plan(
        project,
        project.intake.figures,
        tuple(reversed(project.intake.proteins)),
        expected_digest=intake_digest(project),
    )
    changed = confirm_intake(changed, expected_digest=intake_digest(changed))
    new = build_intake_execution_plan(changed, expected_digest=intake_digest(changed))
    assert [r.row_id for r in new.figures[0].rows] == ["r2", "r1"]
    assert new.figures[0].rows[1].geometry_key == old.figures[0].rows[0].geometry_key
    larger = confirmed(count=4)
    expanded = build_intake_execution_plan(larger, expected_digest=intake_digest(larger))
    assert expanded.figures[0].rows[0].geometry_key != old.figures[0].rows[0].geometry_key
    assert expanded.figures[0].rows[0].slots[:3] == old.figures[0].rows[0].slots


def test_different_projects_and_sources_do_not_share_slot_or_geometry_identity() -> None:
    project = confirmed()
    other = confirmed(project_id="other")
    a = build_intake_execution_plan(project, expected_digest=intake_digest(project))
    b = build_intake_execution_plan(other, expected_digest=intake_digest(other))
    assert {c.slot_id for c in a.cells}.isdisjoint(c.slot_id for c in b.cells)
    row1, row2 = a.figures[0].rows
    assert row1.geometry_key != row2.geometry_key
    assert row1.output_directory != row2.output_directory


def test_source_rebinding_and_fig_move_invalidate_only_the_correct_dependencies() -> None:
    project = confirmed()
    before = build_intake_execution_plan(project, expected_digest=intake_digest(project))
    project = assign_intake_sources(
        project,
        (IntakeAssignment(protein_id="r1", source_id="s2"),),
        expected_digest=intake_digest(project),
        replace=True,
        allow_reuse=True,
    )
    project = confirm_intake(project, expected_digest=intake_digest(project))
    rebound = build_intake_execution_plan(project, expected_digest=intake_digest(project))
    assert before.figures[0].rows[0].geometry_key != rebound.figures[0].rows[0].geometry_key
    assert before.figures[0].rows[1].geometry_key == rebound.figures[0].rows[1].geometry_key
    project = replace_intake_plan(
        project,
        (*project.intake.figures, IntakeFigure(figure_id="g", label="Fig2", lane_count=3)),
        (
            IntakeProtein(protein_id="r1", figure_id="g", label="AKT"),
            IntakeProtein(protein_id="r2", figure_id="f", label="AKT"),
        ),
        expected_digest=intake_digest(project),
    )
    project = confirm_intake(project, expected_digest=intake_digest(project))
    moved = build_intake_execution_plan(project, expected_digest=intake_digest(project))
    assert moved.plan_key != rebound.plan_key
    row = moved.figures[1].rows[0]
    assert row.slots == rebound.figures[0].rows[0].slots
    assert row.geometry_key == rebound.figures[0].rows[0].geometry_key
    assert row.raw_crop_path != rebound.figures[0].rows[0].raw_crop_path
