"""Stable table identities, version compatibility and explicit partial publication evidence."""

import csv
import errno
import json
from collections.abc import Callable
from hashlib import sha256
from io import StringIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import TypeAdapter
from tool_contracts.api import AssetRef, RunRecord
from wb_tool.adapters.project_export import project_table_rows
from wb_tool.api import (
    AnalysisResult,
    ArchiveRunEvidence,
    FigureSourcePath,
    IntakeOutputPreparation,
    LaneROI,
    LoadedProjectResult,
    ProjectRowAnalysis,
    StagedProjectArchive,
    WBFigureProject,
    WBIntakeFigureProject,
    WBIntakeOutputProject,
    analyze_annotations,
    approve_intake_workflow,
    claim_intake_workflow_step,
    complete_intake_crop,
    complete_intake_figure,
    complete_intake_measurement,
    export_intake_crop,
    export_intake_outputs,
    fill_intake_table,
    finish_intake_workflow_step,
    intake_digest,
    intake_output_digest,
    intake_workflow_digest,
    load_tiff,
    prepare_intake_crops,
    prepare_intake_figure,
    prepare_intake_figures,
    prepare_intake_measurement_revision,
    prepare_intake_outputs,
    prepare_intake_workflow,
    project_assets,
    propose_intake_crop,
    read_figure_project,
    read_project_result,
    record_intake_crop_proposal,
    record_intake_output,
    restore_staged_project,
    review_intake_crop,
    revise_completed_intake_crop,
    stage_project_archive,
)

from tools.wb.tests.test_intake_execution import confirmed
from tools.wb.tests.test_intake_figure import asset, compose, ready_fig


def pending(count: int = 3) -> WBIntakeOutputProject:
    source = confirmed(count=count)
    return prepare_intake_outputs(
        prepare_intake_figures(
            prepare_intake_crops(
                prepare_intake_workflow(source, expected_digest=intake_digest(source))
            )
        )
    )


@given(st.integers(min_value=1, max_value=96))
def test_every_sample_position_has_an_independent_blank_identity(count: int) -> None:
    project = pending(count)
    cells = fill_intake_table(project, ())
    assert len(cells) == 2 * count
    assert len({item.slot_id for item in cells}) == 2 * count
    assert [item.cell.lane_index for item in cells] == list(range(1, count + 1)) * 2
    assert {item.figure_id for item in cells} == {"f"}
    assert {item.cell.row_id for item in cells} == {"r1", "r2"}
    assert all(item.cell.value is None and item.cell.raw_integral is None for item in cells)
    assert read_figure_project(project.model_dump_json().encode()) == project
    with pytest.raises(ValueError):
        WBIntakeFigureProject.from_bytes(project.model_dump_json().encode())


def test_failed_crop_is_not_pending_or_zero_and_schema13_tables_stay_unchanged() -> None:
    project = pending()
    old = WBIntakeFigureProject.model_validate(
        {key: value for key, value in dict(project).items() if key != "intake_outputs"}
        | {"schema_version": 13}
    )
    _, old_audit = project_table_rows(old, ())
    assert "稳定槽位 ID" not in old_audit[4]
    active, ticket = claim_intake_workflow_step(
        approve_intake_workflow(project, expected_digest=intake_workflow_digest(project)),
        session_key="failed-crop",
        stage_filter="crop",
    )
    assert ticket is not None
    failed = finish_intake_workflow_step(active, ticket, "failed", reason="原图读取失败")
    assert isinstance(failed, WBIntakeOutputProject)
    cells = fill_intake_table(failed, ())
    assert all(
        item.cell.status == "failed" and item.cell.reason == "原图读取失败" for item in cells[:3]
    )
    assert all(item.cell.value is None for item in cells)
    assert all(item.cell.status != "failed" for item in cells[3:])
    _, audit = project_table_rows(failed, ())
    assert audit[4][-4:] == ("稳定 Fig ID", "稳定槽位 ID", "填表策略", "定量策略")
    assert [row[-3] for row in audit[5:]] == [item.slot_id for item in cells]


def test_partial_output_is_versioned_and_restore_relocates_only_assets() -> None:
    project = pending()
    # Application-boundary fixture only; no filesystem publication or runtime receipt claimed.
    index = AssetRef(
        asset_id="index", relative_path="assets/index.json", sha256="a" * 64, size_bytes=64
    )
    prepared = IntakeOutputPreparation(
        output_id="1" * 32,
        project_id=project.project_id,
        revision=project.revision,
        input_digest=intake_output_digest(project),
        destination="C:/synthetic/new-output",
        path="C:/synthetic/new-output/index.json",
        sha256=index.sha256,
        size_bytes=index.size_bytes,
        complete=False,
        errors=("尚有未计算Fig",),
    )
    with pytest.raises(ValueError, match="冻结内容"):
        record_intake_output(project, prepared.model_copy(update={"complete": True}), index)
    with pytest.raises(ValueError, match="冻结内容"):
        record_intake_output(project, prepared, index.model_copy(update={"sha256": "b" * 64}))
    saved = record_intake_output(project, prepared, index)
    assert saved.intake_outputs[0].complete is False
    assert all(step.status == "pending" for step in saved.workflow.steps)
    original = saved.model_dump_json()
    archive = AssetRef(
        asset_id="zip", relative_path="assets/original.zip", sha256="c" * 64, size_bytes=32
    )
    staged = StagedProjectArchive(
        project=saved,
        archive_path="",
        archive_sha256=archive.sha256,
        assets=(),
        runs=(),
        format_version=2,
    )
    relocated = tuple(
        ref.model_copy(
            update={"asset_id": "restored-" + ref.asset_id, "relative_path": "assets/" + ref.sha256}
        )
        for ref in project_assets(saved)
    )
    restored = restore_staged_project(staged, relocated, archive)
    assert isinstance(restored, WBIntakeOutputProject)
    assert restored.intake_outputs[0].index.relative_path == "assets/" + index.sha256
    assert intake_output_digest(restored) == intake_output_digest(saved)
    assert saved.model_dump_json() == original


def partial_files(tmp_path: Path) -> tuple[WBIntakeOutputProject, tuple[FigureSourcePath, ...]]:
    project, originals = ready_fig(tmp_path)
    project = compose(prepare_intake_outputs(project), originals, tmp_path / "saved-figure.png")
    assert isinstance(project, WBIntakeOutputProject)
    paths = tuple(
        FigureSourcePath(ref.sha256, str(tmp_path / Path(ref.relative_path).name))
        for ref in project_assets(project)
    )
    return project, paths


def test_partial_files_keep_full_manifest_and_can_restore_without_fabricating_completion(
    tmp_path: Path,
) -> None:
    project, paths = partial_files(tmp_path)
    old = project.model_dump_json()
    output = tmp_path / "new-output"
    prepared = export_intake_outputs(project, paths, str(output))
    assert prepared.complete is False and any("未完成" in error for error in prepared.errors)
    assert (output / "project.zip").is_file()
    index = json.loads((output / "index.json").read_bytes())
    for member in index["members"]:
        data = (output / member["path"]).read_bytes()
        assert (sha256(data).hexdigest(), len(data)) == (member["sha256"], member["size_bytes"])
    staged = stage_project_archive(str(output / "project.zip"), str(tmp_path / "restore"))
    assert isinstance(staged.project, WBIntakeOutputProject)
    assert [row.row_id for row in staged.project.rows] == ["a1", "a2", "b1"]
    assert staged.project.model_dump_json() == old
    saved = record_intake_output(project, prepared, asset(output / "index.json"))
    assert all(s.status != "done" for s in saved.workflow.steps if s.stage == "export")
    with pytest.raises(FileExistsError):
        export_intake_outputs(project, paths, str(output))
    assert project.model_dump_json() == old


def test_changed_source_is_reported_without_a_complete_archive_or_zero_values(
    tmp_path: Path,
) -> None:
    project, paths = partial_files(tmp_path)
    wrong = tmp_path / "changed.tiff"
    wrong.write_bytes(b"changed source")
    paths = (FigureSourcePath(paths[0].sha256, str(wrong)), *paths[1:])
    output = tmp_path / "changed-output"
    prepared = export_intake_outputs(project, paths, str(output))
    assert not prepared.complete
    assert any("来源文件" in error for error in prepared.errors)
    assert not (output / "project.zip").exists()
    status = json.loads((output / "status.json").read_bytes())
    assert len(status["cells"]) == 9
    assert all(item["cell"]["value"] is None for item in status["cells"])


def test_cancel_and_disk_full_never_publish_a_complete_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, paths = partial_files(tmp_path)
    cancelled = tmp_path / "cancelled-output"
    calls = 0

    def cancel_during_copy() -> bool:
        nonlocal calls
        calls += 1
        return calls >= 4

    with pytest.raises(ValueError, match="取消"):
        export_intake_outputs(project, paths, str(cancelled), cancelled=cancel_during_copy)
    assert not cancelled.exists()
    assert not list(tmp_path.glob(".wb-intake-output-*"))

    def full(*args: object, **kwargs: object) -> None:
        raise OSError(errno.ENOSPC, "synthetic disk full")

    monkeypatch.setattr("wb_tool.adapters.worksheet_export.publish_table_bytes", full)
    full_path = tmp_path / "disk-full-output"
    with pytest.raises(OSError, match="disk full"):
        export_intake_outputs(project, paths, str(full_path))
    assert not full_path.exists()
    assert not list(tmp_path.glob(".wb-intake-output-*"))


def full_files(
    tmp_path: Path,
) -> tuple[WBIntakeOutputProject, tuple[FigureSourcePath, ...], tuple[ArchiveRunEvidence, ...]]:
    project, paths = partial_files(tmp_path)
    active, ticket = claim_intake_workflow_step(project, session_key="b-crop", stage_filter="crop")
    assert isinstance(active, WBIntakeOutputProject) and ticket is not None
    project = record_intake_crop_proposal(
        active, ticket, propose_intake_crop(str(tmp_path / "b1.tiff"), active, "b1")
    )
    project = review_intake_crop(
        project,
        "b1",
        LaneROI("b1", 0, 10, 120, 60),
        expected_digest=intake_workflow_digest(project),
    )
    active, ticket = claim_intake_workflow_step(
        approve_intake_workflow(project, expected_digest=intake_workflow_digest(project)),
        session_key="b-crop",
        stage_filter="crop",
    )
    assert isinstance(active, WBIntakeOutputProject) and ticket is not None
    raw = tmp_path / "b1-crop.tiff"
    export_intake_crop(str(tmp_path / "b1.tiff"), active, "b1", str(raw), ticket=ticket)
    project = complete_intake_crop(active, ticket, asset(raw))
    active, ticket = claim_intake_workflow_step(
        project, session_key="b-compose", stage_filter="compose"
    )
    assert isinstance(active, WBIntakeOutputProject) and ticket is not None
    image = tmp_path / "b-figure.png"
    project = complete_intake_figure(
        active, ticket, prepare_intake_figure(active, ticket, paths, str(image)), asset(image)
    )
    assert isinstance(project, WBIntakeOutputProject)
    evidence: list[ArchiveRunEvidence] = []
    for fig in ("a", "b"):
        project = prepare_intake_measurement_revision(project, fig, project.revision + 1)
        active, ticket = claim_intake_workflow_step(
            project, session_key=fig, stage_filter="measure"
        )
        assert (
            isinstance(active, WBIntakeOutputProject)
            and ticket is not None
            and ticket.target_id == fig
        )
        frozen = tmp_path / ("frozen-" + fig + ".json")
        frozen.write_bytes(active.model_dump_json().encode())
        completed: list[ProjectRowAnalysis] = []
        decoded: list[LoadedProjectResult] = []
        for plan in active.analyses:
            if not plan.row_id.startswith(fig):
                continue
            result = analyze_annotations(
                load_tiff(tmp_path / (plan.row_id + ".tiff")), plan.request
            )
            result_path = tmp_path / (plan.row_id + "-result.json")
            result_path.write_bytes(TypeAdapter(AnalysisResult).dump_json(result))
            # Explicit application fixture; real host/worker receipts are tested separately.
            run = RunRecord(
                document_id=active.project_id,
                tool_id="wb-figure",
                revision=plan.request.revision,
                run_id="synthetic-" + plan.row_id,
                pid=123,
                state="succeeded",
                request=asset(frozen),
                result=asset(result_path),
            )
            measured = ProjectRowAnalysis.model_validate({**dict(plan), "run": run})
            completed.append(measured)
            decoded.append(read_project_result(measured, result_path.read_bytes()))
            evidence.append(ArchiveRunEvidence(run, str(frozen), str(result_path)))
        finished = complete_intake_measurement(active, ticket, tuple(completed), tuple(decoded))
        assert isinstance(finished, WBIntakeOutputProject)
        project = finished
    return (
        project,
        tuple(
            FigureSourcePath(ref.sha256, str(tmp_path / Path(ref.relative_path).name))
            for ref in project_assets(project)
        ),
        tuple(evidence),
    )


def test_completed_crop_correction_invalidates_only_its_fig_and_preserves_published_history(
    tmp_path: Path,
) -> None:
    project, paths, runs = full_files(tmp_path)
    active, ticket = claim_intake_workflow_step(
        project, session_key="export", stage_filter="export"
    )
    assert isinstance(active, WBIntakeOutputProject) and ticket is not None
    destination = tmp_path / "before-correction"
    output = export_intake_outputs(active, paths, str(destination), runs=runs, ticket=ticket)
    saved = record_intake_output(active, output, asset(destination / "index.json"), ticket=ticket)
    original = saved.model_dump_json()
    files = {p: sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob("*") if p.is_file()}
    roi = LaneROI("a1", 0, 12, 120, 58)
    with pytest.raises(ValueError, match="只能重试"):
        review_intake_crop(saved, "a1", roi, expected_digest=intake_workflow_digest(saved))
    with pytest.raises(ValueError, match="输入已变化"):
        revise_completed_intake_crop(saved, "a1", roi, expected_digest="old")
    revised = revise_completed_intake_crop(
        saved, "a1", roi, expected_digest=intake_workflow_digest(saved)
    )
    assert isinstance(revised, WBIntakeOutputProject)
    assert saved.model_dump_json() == original
    assert revised.intake_outputs == saved.intake_outputs
    assert intake_output_digest(revised) != saved.intake_outputs[-1].input_digest
    assert {e.figure_id for e in revised.intake_figures} == {"b"}
    assert revised.analyses == tuple(p for p in saved.analyses if p.row_id == "b1")
    before = {(s.stage, s.target_id): s for s in saved.workflow.steps}
    after = {(s.stage, s.target_id): s for s in revised.workflow.steps}
    for address in (
        ("crop", "a1"),
        ("compose", "a"),
        ("measure", "a"),
        ("export", saved.project_id),
    ):
        assert after[address].status == "pending"
        assert after[address].attempt == before[address].attempt
    for address in (("crop", "a2"), ("crop", "b1"), ("compose", "b"), ("measure", "b")):
        assert after[address] == before[address]
    evidence = next(e for e in revised.intake_crops if e.row_id == "a1")
    assert evidence.crop == roi and evidence.reviewed and evidence.raw_crop is None
    assert tuple(s.slot_id for s in evidence.slots) == tuple(
        s.slot_id for e in saved.intake_crops if e.row_id == "a1" for s in e.slots
    )
    assert not revised.workflow.approved and not revised.workflow.cancel_requested
    assert read_figure_project(revised.model_dump_json().encode()) == revised
    assert {p: sha256(p.read_bytes()).hexdigest() for p in files} == files
    newer_roi = LaneROI("a1", 2, 14, 120, 60)
    newer = review_intake_crop(
        revised, "a1", newer_roi, expected_digest=intake_workflow_digest(revised)
    )
    assert isinstance(newer, WBIntakeOutputProject)
    assert next(e for e in newer.intake_crops if e.row_id == "a1").crop == newer_roi
    assert newer.intake_outputs == revised.intake_outputs
    assert newer.analyses == revised.analyses
    assert read_figure_project(newer.model_dump_json().encode()) == newer
    with pytest.raises(ValueError, match="仅用于"):
        revise_completed_intake_crop(
            revised, "a1", roi, expected_digest=intake_workflow_digest(revised)
        )
    running, new_ticket = claim_intake_workflow_step(
        approve_intake_workflow(revised, expected_digest=intake_workflow_digest(revised)),
        session_key="new-crop",
        stage_filter="crop",
    )
    assert isinstance(running, WBIntakeOutputProject) and new_ticket is not None
    assert new_ticket.attempt == before["crop", "a1"].attempt + 1
    with pytest.raises(ValueError, match="当前阶段退出"):
        revise_completed_intake_crop(
            running,
            "b1",
            LaneROI("b1", 0, 12, 120, 58),
            expected_digest=intake_workflow_digest(running),
        )
    target = tmp_path / "corrected-original.tiff"
    export_intake_crop(str(tmp_path / "a1.tiff"), running, "a1", str(target), ticket=new_ticket)
    corrected = complete_intake_crop(running, new_ticket, asset(target))
    assert read_figure_project(corrected.model_dump_json().encode()) == corrected
    assert {p: sha256(p.read_bytes()).hexdigest() for p in files} == files


def test_complete_output_requires_verified_runs_and_reexports_without_overwriting(
    tmp_path: Path,
) -> None:
    project, paths, runs = full_files(tmp_path)
    active, ticket = claim_intake_workflow_step(
        project, session_key="export", stage_filter="export"
    )
    assert isinstance(active, WBIntakeOutputProject) and ticket is not None
    destination = tmp_path / "complete-output"
    prepared = export_intake_outputs(active, paths, str(destination), runs=runs, ticket=ticket)
    assert prepared.complete is True and prepared.errors == ()
    rows = list(
        csv.DictReader(StringIO((destination / "measurements.csv").read_text(encoding="utf-8-sig")))
    )
    assert len(rows) == 9
    assert len({row["稳定槽位 ID"] for row in rows}) == 9
    for row in rows:
        row_id = row["行 ID"].removeprefix("text:")
        lane = int(row["泳道序号"])
        assert row["运行 ID"] == "text:synthetic-" + row_id
        if lane == 3:
            assert row["原始积分（待复核）"] == "" and row["积分"] == ""
        else:
            scale = {"a1": 1, "a2": 2, "b1": 3}[row_id]
            assert float(row["原始积分（待复核）"]) == 400 * scale * lane
    old_zip = (destination / "project.zip").read_bytes()
    saved = record_intake_output(active, prepared, asset(destination / "index.json"), ticket=ticket)
    assert all(s.status == "done" for s in saved.workflow.steps)
    paths = (*paths, FigureSourcePath(prepared.sha256, prepared.path))
    repeated = export_intake_outputs(saved, paths, str(tmp_path / "repeated-output"), runs=runs)
    assert repeated.complete and repeated.output_id != prepared.output_id
    assert (destination / "project.zip").read_bytes() == old_zip
    stage_project_archive(repeated.destination + "/project.zip", str(tmp_path / "restored-again"))
    missing = export_intake_outputs(project, paths[:-1], str(tmp_path / "missing-runs"))
    assert not missing.complete and any("运行" in error for error in missing.errors)


@pytest.mark.parametrize("tamper_frozen", (False, True))
def test_runs_are_frozen_once_and_archive_evidence_cannot_silently_degrade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper_frozen: bool
) -> None:
    from wb_tool.adapters import figure_export

    project, paths, original_runs = full_files(tmp_path)
    export = figure_export.export_figure_bundle

    def change_after_first_verification(
        snapshot: WBFigureProject,
        sources: tuple[FigureSourcePath, ...],
        destination: str,
        *,
        cancelled: Callable[[], bool] = lambda: False,
        runs: tuple[ArchiveRunEvidence, ...] = (),
    ) -> str:
        changed = runs if tamper_frozen else original_runs
        Path(changed[0].result_path).write_bytes(b"changed after first verification")
        assert runs[0].result_path != original_runs[0].result_path
        return export(snapshot, sources, destination, cancelled=cancelled, runs=runs)

    monkeypatch.setattr(figure_export, "export_figure_bundle", change_after_first_verification)
    destination = tmp_path / "raced-output"
    prepared = export_intake_outputs(project, paths, str(destination), runs=original_runs)
    with ZipFile(destination / "project.zip") as archive:
        index = json.loads(archive.read("archive.json"))
    if tamper_frozen:
        assert not prepared.complete
        assert any("发布前改变" in error for error in prepared.errors)
        assert index["runs"][0]["verification"] == "unavailable"
    else:
        assert prepared.complete and prepared.errors == ()
        assert index["runs"][0]["verification"] == "verified_result"
