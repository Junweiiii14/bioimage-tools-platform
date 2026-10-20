"""Incomplete acquisition drafts, immutable identities and old wire formats."""

import json

import pytest
from tool_contracts.api import AssetRef
from wb_tool.api import (
    ExportDiscovery,
    ExportObservation,
    IntakeDraftFigure,
    IntakeGrouping,
    IntakeManifest,
    IntakeSource,
    WBFigureProject,
    WBIntakeProject,
    build_intake_execution_plan,
    confirm_intake,
    create_intake,
    install_export_discovery,
    intake_digest,
    intake_grouping,
    read_figure_project,
    register_intake_source,
    save_intake_grouping,
)


def pool() -> WBIntakeProject:
    project = create_intake(WBFigureProject(project_id="grouped"))
    for number, path in enumerate(
        ("batch-a/P_123456 (1).tiff", "batch-a/P_123456 (2).tiff", "batch-b/P_123456 (1).tiff"), 1
    ):
        project = register_intake_source(
            project,
            IntakeSource(
                source_id=f"s{number}",
                asset=AssetRef(
                    asset_id=f"a{number}",
                    relative_path=f"assets/{number}.tiff",
                    sha256=f"{number:064x}",
                    size_bytes=100,
                ),
                original_name=path.split("/")[-1],
                relative_path=path,
                width=100,
                height=60,
                bit_depth=16,
            ),
            expected_digest=intake_digest(project),
        )
    return project


def grouped(project: WBIntakeProject, n: int | None = 4) -> IntakeGrouping:
    grouping = intake_grouping(project)
    return IntakeGrouping(
        figures=(IntakeDraftFigure(figure_id="fig", label="Fig 1", lane_count=n),),
        groups=tuple(
            group.model_copy(
                update={
                    "figure_id": "fig",
                    "protein_label": "P",
                    "selected_source_id": group.source_ids[0],
                }
            )
            for group in grouping.groups
        ),
    )


def test_incomplete_group_draft_survives_roundtrip_without_executable_rows() -> None:
    project = pool()
    grouping = grouped(project, None)
    assert len(grouping.groups) == 2
    assert grouping.groups[0].source_ids == ("s1", "s2")
    saved = save_intake_grouping(project, grouping, expected_digest=intake_digest(project))
    assert saved.intake.schema_version == 3 and not saved.rows
    assert read_figure_project(saved.model_dump_json().encode()) == saved
    with pytest.raises(ValueError, match="Fig级N"):
        confirm_intake(saved, expected_digest=intake_digest(saved))
    assert project.intake.schema_version == 1 and not project.intake.grouping


@pytest.mark.parametrize("failed", [False, True])
def test_latest_reference_or_failed_observation_blocks_previously_saved_selection(
    failed: bool,
) -> None:
    project = pool()
    saved = save_intake_grouping(project, grouped(project), expected_digest=intake_digest(project))
    observation = ExportObservation(
        source_id="s1",
        sha256=project.intake.sources[0].asset.sha256,
        group_id="0" * 24,
        role="unknown" if failed else "reference",
        error="读取失败" if failed else "",
    )
    current = install_export_discovery(
        saved, ExportDiscovery(observations=(observation,)), expected_digest=intake_digest(saved)
    )
    assert current.intake.grouping == saved.intake.grouping
    with pytest.raises(ValueError, match="重新核对原图"):
        confirm_intake(current, expected_digest=intake_digest(current))
    forged = current.model_copy(
        update={
            "intake": current.intake.model_copy(update={"confirmed_digest": intake_digest(current)})
        }
    )
    with pytest.raises(ValueError, match="重新核对原图"):
        build_intake_execution_plan(forged, expected_digest=intake_digest(forged))


def test_n_and_source_changes_preserve_group_row_identity_but_change_geometry() -> None:
    project = pool()
    first = save_intake_grouping(project, grouped(project), expected_digest=intake_digest(project))
    first = confirm_intake(first, expected_digest=intake_digest(first))
    before = build_intake_execution_plan(first, expected_digest=intake_digest(first))
    draft = intake_grouping(first)
    changed = IntakeGrouping(
        figures=(draft.figures[0].model_copy(update={"lane_count": 5}),), groups=draft.groups
    )
    second = save_intake_grouping(first, changed, expected_digest=intake_digest(first))
    assert not second.intake.confirmed_digest
    assert [row.row_id for row in second.rows] == [row.row_id for row in first.rows]
    second = confirm_intake(second, expected_digest=intake_digest(second))
    after = build_intake_execution_plan(second, expected_digest=intake_digest(second))
    assert before.figures[0].rows[0].geometry_key != after.figures[0].rows[0].geometry_key
    assert before.figures[0].rows[0].slots[0].slot_id == after.figures[0].rows[0].slots[0].slot_id
    stale = intake_digest(first)
    with pytest.raises(ValueError, match="已修改"):
        save_intake_grouping(second, changed, expected_digest=stale)


def test_auxiliary_membership_and_unselected_source_are_not_lost_or_executed() -> None:
    project = pool()
    draft = grouped(project)
    draft = IntakeGrouping(
        figures=draft.figures,
        groups=(
            draft.groups[0],
            draft.groups[1].model_copy(update={"figure_id": None, "selected_source_id": None}),
        ),
    )
    saved = save_intake_grouping(project, draft, expected_digest=intake_digest(project))
    assert len(saved.intake.sources) == 3
    assert len(saved.rows) == 1 and saved.rows[0].source == project.intake.sources[0].asset
    assert saved.intake.grouping == draft
    confirmed = confirm_intake(saved, expected_digest=intake_digest(saved))
    assert confirmed.intake.confirmed_digest
    bad = json.loads(saved.model_dump_json())
    bad["intake"]["grouping"]["groups"][0]["selected_source_id"] = "s3"
    with pytest.raises(ValueError, match="属于当前采集组"):
        read_figure_project(json.dumps(bad).encode())
    missing = IntakeGrouping(figures=draft.figures, groups=(draft.groups[0],))
    with pytest.raises(ValueError, match="全部来源"):
        save_intake_grouping(project, missing, expected_digest=intake_digest(project))


@pytest.mark.parametrize("version", [1, 2])
def test_old_manifest_wire_shape_and_digest_exclude_new_group_fields(version: int) -> None:
    project = pool()
    fields = dict(project)
    fields["intake"] = IntakeManifest(schema_version=version, sources=project.intake.sources)
    old = WBIntakeProject.model_validate(fields)
    wire = json.loads(old.model_dump_json())
    assert "grouping" not in wire["intake"]
    if version == 1:
        assert "discovery" not in wire["intake"]
    reopened = read_figure_project(old.model_dump_json().encode())
    assert isinstance(reopened, WBIntakeProject)
    assert intake_digest(reopened) == intake_digest(old)
