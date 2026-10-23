"""Progressive readable delivery, byte preservation, ownership and portable restoration."""

import json
from pathlib import Path

import numpy as np
import pytest
import tifffile
from PIL import Image
from wb_tool.adapters.intake_delivery import select_intake_delivery
from wb_tool.adapters.intake_table_export import intake_table_bytes
from wb_tool.api import (
    FigureSourcePath,
    IntakeAcquisitionGroup,
    IntakeDraftFigure,
    IntakeGrouping,
    IntakeManifest,
    LaneROI,
    WBIntakeCropProject,
    WBIntakeOutputProject,
    WBIntakeProject,
    approve_intake_workflow,
    claim_intake_workflow_step,
    complete_intake_crop,
    export_intake_crop,
    finalize_intake_delivery,
    inspect_intake_delivery,
    intake_digest,
    intake_output_digest,
    intake_workflow_digest,
    load_tiff,
    materialize_intake_delivery,
    plan_intake_delivery,
    prepare_intake_delivery,
    project_assets,
    propose_intake_crop,
    read_figure_project,
    record_intake_crop_proposal,
    review_intake_crop,
    revise_completed_intake_crop,
    stage_project_archive,
)
from wb_tool.application.instrument_intake import intake_manifest_digest, intake_project_rows
from wb_tool.application.intake_delivery import delivery_component

from tools.wb.tests.test_intake_automatic_crop import prepared
from tools.wb.tests.test_intake_execution import confirmed
from tools.wb.tests.test_intake_figure import asset, ready_fig
from tools.wb.tests.test_intake_grouping import grouped, pool
from tools.wb.tests.test_intake_output import full_files, partial_files, pending


def test_versioned_location_keeps_old_wire_and_scientific_digests() -> None:
    for original in (confirmed(), pending()):
        old = original.model_dump_json()
        updated = prepare_intake_delivery(
            original, output_parent="C:/WB", workspace_path="C:/work", delivery_id="a" * 32
        )
        assert updated.intake.schema_version == 5
        assert intake_digest(updated) == intake_digest(original)
        assert read_figure_project(updated.model_dump_json().encode()) == updated
        if isinstance(original, WBIntakeOutputProject):
            assert isinstance(updated, WBIntakeOutputProject)
            assert intake_output_digest(updated) == intake_output_digest(original)
            assert intake_workflow_digest(updated) == intake_workflow_digest(original)
        assert original.model_dump_json() == old and '"delivery"' not in old


def test_readable_names_handle_windows_names_duplicates_and_unicode() -> None:
    for label in ("CON", "nul.txt", "../A<B>:C|D*", "蛋白" * 80, "😎" * 80, "  ."):
        a, b = delivery_component(label, "a"), delivery_component(label, "b")
        assert a != b
        assert not any(c in a for c in '<>:"/\\|?*')
        assert len(a.encode("utf-16-le")) // 2 <= 33
        assert not a.endswith((".", " "))
    plan = plan_intake_delivery(confirmed(label="AKT"))
    assert plan.rows[0].directory != plan.rows[1].directory
    assert all("AKT" in row.directory for row in plan.rows)
    for parent in ("relative/output", "C:relative", "C:/invalid\x00path"):
        with pytest.raises(ValueError, match="绝对路径"):
            prepare_intake_delivery(
                confirmed(), output_parent=parent, workspace_path="C:/work", delivery_id="a" * 32
            )


def test_unconfirmed_location_survives_group_edits_without_creating_directories(
    tmp_path: Path,
) -> None:
    from wb_tool.api import confirm_intake, save_intake_grouping

    original = pool()
    project = prepare_intake_delivery(
        original,
        output_parent=str(tmp_path),
        workspace_path=str(tmp_path / "work"),
        delivery_id="1" * 32,
    )
    with pytest.raises(ValueError, match="先确认"):
        materialize_intake_delivery(project, (), workspace_path=str(tmp_path / "work"))
    project = save_intake_grouping(
        project, grouped(project), expected_digest=intake_digest(project)
    )
    project = confirm_intake(project, expected_digest=intake_digest(project))
    assert project.intake.delivery is not None
    assert project.intake.delivery.output_parent == str(tmp_path)
    assert project.intake.delivery.legacy_schema_version == 3
    assert not list(tmp_path.iterdir())
    assert read_figure_project(project.model_dump_json().encode()) == project
    workspace = tmp_path / "new-work"
    workspace.mkdir()
    unconfirmed = prepare_intake_delivery(
        original,
        output_parent=str(workspace / "outputs"),
        workspace_path=str(workspace),
        delivery_id="f" * 32,
    )
    with pytest.raises(ValueError, match="先确认"):
        materialize_intake_delivery(unconfirmed, (), workspace_path=str(workspace))
    assert not (workspace / "outputs").exists()


def test_all_group_sources_and_unassigned_retained_only_proven_peer_cropped(tmp_path: Path) -> None:
    original, _ = ready_fig(tmp_path)
    source = original.intake.sources[0]
    duplicate = source.model_copy(
        update={"source_id": "copy", "original_name": "same.tiff", "relative_path": "same.tiff"}
    )
    white_path = tmp_path / "white.tiff"
    tifffile.imwrite(white_path, np.full((80, 120), 45000, dtype=np.uint16))
    white = source.model_copy(
        update={
            "source_id": "white",
            "asset": asset(white_path),
            "original_name": white_path.name,
            "relative_path": white_path.name,
        }
    )
    unassigned = white.model_copy(
        update={
            "source_id": "unassigned",
            "original_name": "unassigned.tiff",
            "relative_path": "unassigned.tiff",
        }
    )
    groups = tuple(
        IntakeAcquisitionGroup(
            group_id=p.protein_id,
            source_ids=(p.protein_id, "copy", "white") if p.protein_id == "a1" else (p.protein_id,),
            figure_id=p.figure_id,
            protein_label=p.label,
            selected_source_id=p.protein_id,
        )
        for p in original.intake.proteins
    )
    grouping = IntakeGrouping(
        figures=tuple(
            IntakeDraftFigure(figure_id=f.figure_id, label=f.label, lane_count=f.lane_count)
            for f in original.intake.figures
        ),
        groups=groups,
    )
    manifest = IntakeManifest.model_validate(
        {
            **dict(original.intake),
            "schema_version": 3,
            "grouping": grouping,
            "sources": (*original.intake.sources, duplicate, white, unassigned),
            "confirmed_digest": "",
        }
    )
    digest = intake_manifest_digest(original.project_id, manifest)
    manifest = manifest.model_copy(update={"confirmed_digest": digest})
    original = type(original).model_validate(
        {
            **dict(original),
            "intake": manifest,
            "workflow": original.workflow.model_copy(update={"intake_digest": digest}),
        }
    )
    project = prepare_intake_delivery(
        original,
        output_parent=str(tmp_path),
        workspace_path=str(tmp_path / "work"),
        delivery_id="2" * 32,
    )
    paths = tuple(
        FigureSourcePath(a.sha256, str(tmp_path / Path(a.relative_path).name))
        for a in project_assets(project)
    )
    receipt = materialize_intake_delivery(
        project, paths, workspace_path=str(tmp_path / "work"), row_id="a1"
    )
    root = Path(receipt.destination)
    row = plan_intake_delivery(project).rows[0]
    assert len(list((root / row.directory / "原始图片").iterdir())) == 3
    assert len(list((root / "未分配来源").iterdir())) == 1
    assert len(list((root / row.directory / "原值裁剪").iterdir())) == 2
    record = json.loads((root / row.directory / "裁剪与来源记录.json").read_bytes())
    statuses = {p["source_id"]: p["status"] for p in record["companions"]}
    assert "已生成" in statuses["copy"]
    assert "未生成" in statuses["white"]


def test_initial_directory_then_committed_crop_before_other_fig_finishes(tmp_path: Path) -> None:
    original, _ = ready_fig(tmp_path)
    configured = prepare_intake_delivery(
        WBIntakeProject(
            project_id=original.project_id,
            name=original.name,
            intake=original.intake,
            rows=intake_project_rows(original.intake),
            figure_order=original.figure_order,
        ),
        output_parent=str(tmp_path),
        workspace_path=str(tmp_path / "work"),
        delivery_id="a" * 32,
    )
    project = type(original).model_validate({**dict(original), "intake": configured.intake})
    assert isinstance(project, WBIntakeCropProject)
    paths = tuple(
        FigureSourcePath(a.sha256, str(tmp_path / Path(a.relative_path).name))
        for a in project_assets(project)
    )
    initial = materialize_intake_delivery(configured, paths, workspace_path=str(tmp_path / "work"))
    root = Path(initial.destination)
    plan = plan_intake_delivery(project)
    assert all((root / f.directory).is_dir() for f in plan.figures)
    assert len(list(root.rglob("原始图片/*.tiff"))) == 3
    assert not list(root.rglob("原值裁剪/*.tiff"))
    assert not (root / "index.json").exists()
    materialize_intake_delivery(project, paths, workspace_path=str(tmp_path / "work"), row_id="a1")
    raw = next((root / plan.rows[0].directory / "原值裁剪").glob("*.tiff"))
    with tifffile.TiffFile(raw) as cropped, tifffile.TiffFile(tmp_path / "a1.tiff") as source:
        cp, sp = cropped.pages[0], source.pages[0]
        assert isinstance(cp, tifffile.TiffPage) and isinstance(sp, tifffile.TiffPage)
        assert np.array_equal(cp.asarray(), sp.asarray()[10:60, :])
        assert cp.asarray().dtype == np.uint16
    assert len(list((root / plan.rows[0].directory / "展示图片").glob("*"))) == 2
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    materialize_intake_delivery(project, paths, workspace_path=str(tmp_path / "work"), row_id="a1")
    assert all(p.read_bytes() == data for p, data in before.items())
    with pytest.raises(ValueError, match="真实提交"):
        materialize_intake_delivery(
            project, paths, workspace_path=str(tmp_path / "work"), row_id="b1"
        )
    assert not list((root / plan.rows[-1].directory / "原值裁剪").glob("*"))
    materialize_intake_delivery(project, paths, workspace_path=str(tmp_path / "work"))
    assert len(list(root.rglob("原值裁剪/*.tiff"))) == 2  # Resume includes both committed rows.
    resumed = select_intake_delivery(
        project, workspace_path=str(tmp_path / "work"), output_parent=str(tmp_path)
    )
    assert resumed.intake.delivery == project.intake.delivery
    changed = revise_completed_intake_crop(
        project,
        "a1",
        LaneROI("a1", 2, 12, 118, 58),
        expected_digest=intake_workflow_digest(project),
    )
    renewed = select_intake_delivery(
        changed, workspace_path=str(tmp_path / "work"), output_parent=str(tmp_path)
    )
    assert renewed.intake.delivery is not None
    assert renewed.intake.delivery != project.intake.delivery
    assert all(p.read_bytes() == data for p, data in before.items())


def test_chinese_source_warning_survives_ascii_tiff_metadata_and_idempotent_resume(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "中文原图目录"
    directory.mkdir()
    source = directory / "蛋白原图.tiff"
    pixels = np.full((72, 144), 40000, dtype=np.uint16)
    pixels[20:30, 20:120] = 0  # The real reader adds a non-ASCII saturation warning.
    tifffile.imwrite(source, pixels)
    before = source.read_bytes()
    project = prepared(source, count=3)
    active, ticket = claim_intake_workflow_step(project, session_key="chinese-crop")
    assert isinstance(active, WBIntakeCropProject) and ticket is not None
    project = record_intake_crop_proposal(
        active, ticket, propose_intake_crop(str(source), active, "r")
    )
    project = review_intake_crop(
        project,
        "r",
        LaneROI("r", 12, 10, 132, 50),
        expected_digest=intake_workflow_digest(project),
    )
    active, ticket = claim_intake_workflow_step(
        approve_intake_workflow(project, expected_digest=intake_workflow_digest(project)),
        session_key="chinese-crop",
    )
    assert isinstance(active, WBIntakeCropProject) and ticket is not None
    raw_path = directory / "raw-crop.tiff"
    export_intake_crop(str(source), active, "r", str(raw_path), ticket=ticket)
    project = complete_intake_crop(active, ticket, asset(raw_path))
    project = prepare_intake_delivery(
        project,
        output_parent=str(directory),
        workspace_path=str(directory / "工作区"),
        delivery_id="c" * 32,
    )
    paths = (
        FigureSourcePath(load_tiff(source).sha256, str(source)),
        FigureSourcePath(asset(raw_path).sha256, str(raw_path)),
    )
    receipt = materialize_intake_delivery(project, paths, workspace_path=str(directory / "工作区"))
    root = Path(receipt.destination)
    row = plan_intake_delivery(project).rows[0]
    display = root / row.directory / "展示图片"
    with tifffile.TiffFile(next(display.glob("*.tiff"))) as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        assert page.description.isascii()
        metadata = json.loads(page.description)
    warnings = load_tiff(source).warnings
    assert warnings and any(not warning.isascii() for warning in warnings)
    assert metadata["source_warnings"] == list(warnings)
    with Image.open(next(display.glob("*.png"))) as image:
        png_metadata = image.info["wb_provenance"]
        assert json.loads(png_metadata) == metadata
        assert not png_metadata.isascii()  # Retains pre-fix PNG publication bytes.
    copied = next((root / row.directory / "原始图片").iterdir())
    assert "蛋白原图" in copied.name and copied.read_bytes() == before
    raw = next((root / row.directory / "原值裁剪").glob("*.tiff"))
    with tifffile.TiffFile(raw) as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        assert np.array_equal(page.asarray(), pixels[10:50, 12:132])
        assert page.asarray().dtype == np.uint16
    published = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    materialize_intake_delivery(project, paths, workspace_path=str(directory / "工作区"))
    assert all(p.read_bytes() == data for p, data in published.items())
    assert source.read_bytes() == before


def test_existing_foreign_directory_relocation_cancel_and_tampering_rejected(
    tmp_path: Path,
) -> None:
    original, paths = partial_files(tmp_path)
    project = prepare_intake_delivery(
        original,
        output_parent=str(tmp_path),
        workspace_path=str(tmp_path / "work"),
        delivery_id="b" * 32,
    )
    assert project.intake.delivery is not None
    root = tmp_path / project.intake.delivery.directory_name
    with pytest.raises(ValueError, match="取消"):
        materialize_intake_delivery(
            project, paths, workspace_path=str(tmp_path / "work"), cancelled=lambda: True
        )
    assert not root.exists()
    with pytest.raises(ValueError, match="迁移"):
        materialize_intake_delivery(project, paths, workspace_path=str(tmp_path / "different"))
    root.mkdir()
    sentinel = root / "existing.txt"
    sentinel.write_text("keep")
    with pytest.raises(ValueError, match="不能接管"):
        materialize_intake_delivery(project, paths, workspace_path=str(tmp_path / "work"))
    assert sentinel.read_text() == "keep"
    project = prepare_intake_delivery(
        project,
        output_parent=str(tmp_path),
        workspace_path=str(tmp_path / "work"),
        delivery_id="c" * 32,
    )
    receipt = materialize_intake_delivery(project, paths, workspace_path=str(tmp_path / "work"))
    changed = next(Path(receipt.destination).rglob("原始图片/*.tiff"))
    changed.write_bytes(b"user edited")
    with pytest.raises(FileExistsError, match="不同"):
        materialize_intake_delivery(project, paths, workspace_path=str(tmp_path / "work"))
    assert changed.read_bytes() == b"user edited"


@pytest.mark.parametrize("complete", (False, True))
def test_final_project_full_or_partial_and_standard_archive_restores(
    tmp_path: Path, complete: bool
) -> None:
    if complete:
        original, paths, runs = full_files(tmp_path)
    else:
        original, paths = partial_files(tmp_path)
        runs = ()
    project = prepare_intake_delivery(
        original,
        output_parent=str(tmp_path),
        workspace_path=str(tmp_path / "work"),
        delivery_id="d" * 32,
    )
    assert isinstance(project, WBIntakeOutputProject)
    prepared = finalize_intake_delivery(
        project, paths, workspace_path=str(tmp_path / "work"), runs=runs
    )
    assert prepared.complete is complete
    root = Path(prepared.destination)
    assert (root / "灰度汇总.xlsx").is_file()
    assert (root / "完整拼图.png").is_file() is complete
    assert len(list(root.glob("Fig组/*/*_灰度.xlsx"))) == 2
    archive = inspect_intake_delivery(str(root))
    with pytest.raises(ValueError, match="取消"):
        inspect_intake_delivery(str(root), cancelled=lambda: True)
    restored = stage_project_archive(archive, str(tmp_path / "restored"))
    assert restored.project.model_dump_json() == project.model_dump_json()
    csv = (root / "灰度汇总.csv").read_text(encoding="utf-8-sig")
    assert "—" in csv
    assert (
        len(
            intake_table_bytes(project, (), csv=True, figure_id="b")
            .decode("utf-8-sig")
            .splitlines()
        )
        == 2
    )
    index = json.loads((root / "index.json").read_bytes())
    assert index["complete"] is complete
    with pytest.raises(ValueError, match="封存"):
        materialize_intake_delivery(project, paths, workspace_path=str(tmp_path / "work"))
    (root / "灰度汇总.csv").write_text("changed")
    with pytest.raises(ValueError, match="摘要不一致"):
        inspect_intake_delivery(str(root))
