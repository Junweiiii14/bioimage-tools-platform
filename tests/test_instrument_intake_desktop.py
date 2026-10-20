"""Real storage and desktop boundary of the new instrument intake stage."""

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from threading import Event
from typing import cast

import numpy as np
import pytest
import tifffile
from bioimage_app.intake_workflow import IntakeWorkflowSession
from bioimage_app.project_measurements import ProjectMeasurementSession
from bioimage_app.storage import StorageCommand, StorageReply
from bioimage_app.web_window import WebWorkbenchWindow
from platform_runtime.api import Workspace
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot
from tool_contracts.api import AssetRef, DraftSnapshot, RunRecord
from wb_tool.api import (
    FigureTemplate,
    IntakeWorkflowTicket,
    PreviewRaster,
    ProjectRowAnalysis,
    WBFigureProject,
    WBIntakeCropProject,
    WBIntakeFigureProject,
    WBIntakeOutputProject,
    WBIntakeProject,
    WBIntakeWorkflowProject,
    WBJob,
    WBReply,
    intake_digest,
    intake_workflow_digest,
    prepare_intake_workflow,
    propose_intake_crop,
    read_figure_project,
)

from tooling.qt_test_lifecycle import close_and_dispose_window


@pytest.fixture
def intake_window(qtbot: QtBot, tmp_path: Path) -> Iterator[WebWorkbenchWindow]:
    settings = QSettings(str(tmp_path / "intake.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    window = WebWorkbenchWindow(settings=settings)
    window.show()
    try:
        yield window
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )


def make_source(path: Path, value: int = 1000) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(path, np.full((72, 144), value, dtype=np.uint16))
    return path


def wait_saved(window: WebWorkbenchWindow, qtbot: QtBot) -> None:
    qtbot.waitUntil(
        lambda: not window.host.operation_busy and not window.host.has_unsaved_changes,
        timeout=20000,
    )


def current(window: WebWorkbenchWindow) -> WBIntakeProject:
    project = window.host.view.project()
    assert isinstance(project, WBIntakeProject)
    return project


def request(window: WebWorkbenchWindow, action: str, **data: object) -> None:
    project = current(window)
    window.bridge.request(
        action,
        json.dumps(
            {
                "projectId": project.project_id,
                "sessionEpoch": window.bridge.session_epoch,
                "digest": intake_digest(project),
                **data,
            }
        ),
    )


def start(window: WebWorkbenchWindow, qtbot: QtBot, directory: Path) -> None:
    window.start_from_images([directory], intake=True)
    qtbot.waitUntil(
        lambda: window.shutdown_stage == "idle" and bool(window.host.workspace_path),
        timeout=20000,
    )
    wait_saved(window, qtbot)


def plan(window: WebWorkbenchWindow, qtbot: QtBot) -> None:
    request(
        window,
        "intake_plan",
        figures=[{"figure_id": "fig-a", "label": "Fig 1", "lane_count": 8}],
        proteins=[
            {"protein_id": "protein-a", "figure_id": "fig-a", "label": "GAPDH"},
            {"protein_id": "protein-b", "figure_id": "fig-a", "label": "GAPDH"},
        ],
    )
    wait_saved(window, qtbot)


def test_prepare_workflow_saves_reopens_and_returns_to_editing_without_processing(
    intake_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = intake_window
    directory = tmp_path / "instrument"
    make_source(directory / "a.tif")
    make_source(directory / "b.tif", 2000)
    start(window, qtbot, directory)
    plan(window, qtbot)
    sources = current(window).intake.sources
    request(
        window,
        "intake_assign",
        bindings=[
            {"protein_id": "protein-a", "source_id": sources[0].source_id},
            {"protein_id": "protein-b", "source_id": sources[1].source_id},
        ],
    )
    wait_saved(window, qtbot)
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    request(window, "intake_prepare")
    wait_saved(window, qtbot)
    prepared = current(window)
    assert isinstance(prepared, WBIntakeWorkflowProject)
    assert len(prepared.workflow.steps) == 5
    assert all(step.status == "pending" for step in prepared.workflow.steps)
    assert not prepared.analyses and prepared.ocr is None
    assert all(row.roi is None for row in prepared.rows)
    request(window, "intake_edit")
    wait_saved(window, qtbot)
    assert type(current(window)) is WBIntakeProject
    request(window, "intake_prepare")
    wait_saved(window, qtbot)
    workspace = window.host.workspace_path
    epoch = window.bridge.session_epoch
    window.open_project(workspace)
    qtbot.waitUntil(
        lambda: window.bridge.session_epoch > epoch and window.shutdown_stage == "idle",
        timeout=20000,
    )
    wait_saved(window, qtbot)
    assert isinstance(current(window), WBIntakeWorkflowProject)
    snapshot = cast(dict[str, object], window.bridge.snapshot()["intake"])
    assert isinstance(snapshot["workflow"], dict)


@pytest.mark.parametrize("mode", ["cancel", "edit", "save_failure"])
def test_prepared_workflow_never_installs_after_cancel_edit_or_failed_save(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    window = intake_window
    root = tmp_path / "raw"
    make_source(root / "a.tif")
    make_source(root / "b.tif", 2000)
    start(window, qtbot, root)
    plan(window, qtbot)
    project = current(window)
    request(
        window,
        "intake_assign",
        bindings=[
            {"protein_id": p.protein_id, "source_id": s.source_id}
            for p, s in zip(project.intake.proteins, project.intake.sources, strict=True)
        ],
    )
    wait_saved(window, qtbot)
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    before = current(window)
    replies: list[Callable[[WBReply], None]] = []

    def delayed(
        job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        assert job.operation == "intake_workflow_prepare"
        replies.append(callback)

    def failed_storage(*args: object, **kwargs: object) -> None:
        raise OSError("模拟执行计划保存失败")

    if mode == "save_failure":
        monkeypatch.setattr(Workspace, "save_draft", failed_storage)
    else:
        monkeypatch.setattr(window.host, "submit_tool_job", delayed)
    request(window, "intake_prepare")
    if mode != "save_failure":
        assert len(replies) == 1
        if mode == "cancel":
            window.host.cancel()
        else:
            window.host.view.generation += 1
        prepared = prepare_intake_workflow(before, expected_digest=intake_digest(before))
        replies[0](WBReply("late", value=prepared))
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=10000)
    assert type(current(window)) is WBIntakeProject
    assert current(window).intake == before.intake
    if mode == "save_failure":
        assert "保存失败" in window.host.view.status.text()
    monkeypatch.undo()


def test_prepare_cancel_during_storage_commit_preserves_draft_and_committed_history(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = intake_window
    root = tmp_path / "raw"
    make_source(root / "a.tif")
    make_source(root / "b.tif", 2000)
    start(window, qtbot, root)
    plan(window, qtbot)
    project = current(window)
    request(
        window,
        "intake_assign",
        bindings=[
            {"protein_id": p.protein_id, "source_id": s.source_id}
            for p, s in zip(project.intake.proteins, project.intake.sources, strict=True)
        ],
    )
    wait_saved(window, qtbot)
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    before = current(window)
    entered, release = Event(), Event()
    original = Workspace.save_draft

    def delayed_save(
        self: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None,
    ) -> object:
        entered.set()
        if not release.wait(10):
            raise ValueError("测试未释放保存线程")
        return original(
            self,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )

    monkeypatch.setattr(Workspace, "save_draft", delayed_save)
    try:
        request(window, "intake_prepare")
        qtbot.waitUntil(entered.is_set, timeout=10000)
        window.host.cancel()
    finally:
        release.set()
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=10000)
    assert type(current(window)) is WBIntakeProject
    assert current(window).intake == before.intake
    assert window.host.has_unsaved_changes
    assert "已写入历史" in window.host.view.status.text()
    monkeypatch.undo()
    window.host.save()
    wait_saved(window, qtbot)
    assert current(window).revision == before.revision + 2
    assert not window.host.has_unsaved_changes


def test_fixed_n_crop_run_review_original_asset_and_reopen(
    intake_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = intake_window
    root = tmp_path / "raw"
    make_source(root / "a.tif")
    make_source(root / "b.tif", 2000)
    start(window, qtbot, root)
    plan(window, qtbot)
    before = current(window)
    request(
        window,
        "intake_assign",
        bindings=[
            {"protein_id": p.protein_id, "source_id": s.source_id}
            for p, s in zip(before.intake.proteins, before.intake.sources, strict=True)
        ],
    )
    wait_saved(window, qtbot)
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    request(window, "intake_prepare")
    wait_saved(window, qtbot)
    prepared = current(window)
    assert isinstance(prepared, WBIntakeWorkflowProject)
    request(window, "intake_run", workflowDigest=intake_workflow_digest(prepared))
    wait_saved(window, qtbot)
    proposed = current(window)
    assert isinstance(proposed, WBIntakeCropProject)
    assert len(proposed.intake_crops) == 2
    assert all(
        r["cropStatus"] == "pending"
        for r in cast(list[dict[str, object]], window.bridge.snapshot()["rows"])
    )
    assert all(len(e.slots) == 8 and e.crop is None for e in proposed.intake_crops)
    assert all(s.status == "needs_review" for s in proposed.workflow.steps if s.stage == "crop")
    assert not proposed.analyses and not proposed.automatic_rows
    request(
        window,
        "intake_crop_review",
        rowId="protein-a",
        workflowDigest=intake_workflow_digest(proposed),
        roi={"x": 12, "y": 10, "width": 120, "height": 40},
    )
    wait_saved(window, qtbot)
    reviewed = current(window)
    assert isinstance(reviewed, WBIntakeCropProject)
    request(window, "intake_run", workflowDigest=intake_workflow_digest(reviewed))
    wait_saved(window, qtbot)
    finished = current(window)
    assert isinstance(finished, WBIntakeCropProject)
    evidence = next(e for e in finished.intake_crops if e.row_id == "protein-a")
    assert evidence.raw_crop is not None and evidence.reviewed
    raw_path = Path(window.host.workspace_path) / evidence.raw_crop.relative_path
    with tifffile.TiffFile(raw_path) as exported:
        page = exported.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        assert np.array_equal(page.asarray(), np.full((40, 120), 1000, dtype=np.uint16))
    assert next(s for s in finished.workflow.steps if s.target_id == "protein-a").status == "done"
    assert all(s.status == "pending" for s in finished.workflow.steps if s.stage != "crop")
    assert not finished.analyses
    statuses = {
        r["id"]: r["cropStatus"]
        for r in cast(list[dict[str, object]], window.bridge.snapshot()["rows"])
    }
    assert statuses == {"protein-a": "ready", "protein-b": "pending"}
    previous_host, epoch = window.host, window.bridge.session_epoch
    project_id = finished.project_id
    window.open_project(window.host.workspace_path)
    qtbot.waitUntil(
        lambda: (
            window.host is not previous_host
            and window.bridge.session_epoch > epoch
            and window.shutdown_stage == "idle"
            and current(window).project_id == project_id
        ),
        timeout=20000,
    )
    wait_saved(window, qtbot)
    assert current(window).schema_version == 14
    assert current(window).rows[0].lane_count == 8


@pytest.mark.parametrize("mode", ["cancel_reply", "running_save_failure"])
def test_intake_crop_cancel_and_failed_claim_save_never_advance(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    window = intake_window
    root = tmp_path / "raw"
    make_source(root / "a.tif")
    make_source(root / "b.tif", 2000)
    start(window, qtbot, root)
    plan(window, qtbot)
    p = current(window)
    request(
        window,
        "intake_assign",
        bindings=[
            {"protein_id": r.protein_id, "source_id": s.source_id}
            for r, s in zip(p.intake.proteins, p.intake.sources, strict=True)
        ],
    )
    wait_saved(window, qtbot)
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    request(window, "intake_prepare")
    wait_saved(window, qtbot)
    prepared = current(window)
    assert isinstance(prepared, WBIntakeWorkflowProject)
    original_job, original_save = window.host.submit_tool_job, Workspace.save_draft
    captured: list[tuple[WBJob, Callable[[WBReply], None]]] = []

    def jobs(
        job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        if job.operation == "intake_crop_propose":
            captured.append((job, callback))
        else:
            original_job(job, callback, accept_errors=accept_errors)

    def save(
        self: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None,
    ) -> object:
        if b'"status":"running"' in data:
            raise OSError("模拟裁剪活动票据保存失败")
        return original_save(
            self,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )

    monkeypatch.setattr(window.host, "submit_tool_job", jobs)
    if mode == "running_save_failure":
        monkeypatch.setattr(Workspace, "save_draft", save)
    request(window, "intake_run", workflowDigest=intake_workflow_digest(prepared))
    if mode == "cancel_reply":
        qtbot.waitUntil(lambda: bool(captured), timeout=10000)
        job, callback = captured[0]
        assert isinstance(job.document, WBIntakeCropProject)
        late = propose_intake_crop(job.path, job.document, job.row_id)
        window.host.cancel()
        callback(WBReply("late", value=late))
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=10000)
    current_project = current(window)
    assert isinstance(current_project, WBIntakeCropProject)
    assert not current_project.intake_crops and not current_project.analyses
    crops = [s for s in current_project.workflow.steps if s.stage == "crop"]
    if mode == "cancel_reply":
        assert [s.status for s in crops] == ["cancelled", "pending"]
        assert len(captured) == 1
    else:
        assert not captured and all(s.attempt == 0 and s.status == "pending" for s in crops)
        assert "票据保存失败" in window.host.view.status.text()
    monkeypatch.undo()


def test_grouped_draft_and_original_preview_save_reopen_with_real_storage(
    intake_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = intake_window
    root = tmp_path / "grouped-source"
    make_source(root / "P_123456 (1).tif")
    make_source(root / "P_123456 (2).tif", 2000)
    start(window, qtbot, root)
    snapshot = cast(dict[str, object], window.bridge.snapshot()["intake"])
    draft = cast(dict[str, object], snapshot["grouped_draft"])
    # Explicit legacy draft: new projects now expose the versioned sequence editor.
    draft["schema_version"] = 1
    draft.pop("sequence", None)
    draft.pop("excluded_group_ids", None)
    groups = cast(list[dict[str, object]], draft["groups"])
    assert len(groups) == 1 and len(cast(list[str], groups[0]["source_ids"])) == 2
    draft["figures"] = [{"figure_id": "fig", "label": "Fig 1", "lane_count": None}]
    groups[0].update(figure_id="fig", protein_label="蛋白")
    request(window, "intake_grouping", grouping=draft)
    wait_saved(window, qtbot)
    saved = current(window)
    assert saved.intake.grouping is not None and not saved.rows
    assert window.host.workspace_path is not None
    epoch = window.bridge.session_epoch
    window.open_project(window.host.workspace_path)
    qtbot.waitUntil(
        lambda: window.bridge.session_epoch > epoch and window.shutdown_stage == "idle",
        timeout=20000,
    )
    wait_saved(window, qtbot)
    assert current(window) == saved
    request(window, "intake_preview", sourceId=saved.intake.sources[0].source_id)
    qtbot.waitUntil(
        lambda: window.host.intake.group_preview is not None and not window.host.operation_busy,
        timeout=20000,
    )
    preview = window.host.intake.group_preview
    assert preview is not None and preview[1].sha256 == saved.intake.sources[0].asset.sha256
    assert current(window) == saved and not current(window).analyses
    zoom = cast(
        dict[str, object], cast(dict[str, object], window.bridge.snapshot()["intake"])["zoom"]
    )
    assert zoom["sourceId"] == saved.intake.sources[0].source_id and str(
        zoom["preview"]
    ).startswith("data:image/png;")
    # A valid complete draft commits the same row identity and still requires explicit confirmation.
    draft["figures"] = [{"figure_id": "fig", "label": "Fig 1", "lane_count": 4}]
    groups[0]["selected_source_id"] = saved.intake.sources[0].source_id
    request(window, "intake_grouping", grouping=draft)
    wait_saved(window, qtbot)
    assert current(window).rows[0].row_id == groups[0]["group_id"]
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    assert current(window).intake.confirmed_digest
    request(window, "intake_prepare")
    wait_saved(window, qtbot)
    assert isinstance(current(window), WBIntakeWorkflowProject)
    prepared_snapshot = cast(dict[str, object], window.bridge.snapshot()["intake"])
    assert prepared_snapshot["grouped_draft"] == draft


def test_executed_grouping_incomplete_revision_is_durable_and_blocks_execution(
    intake_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = intake_window
    root = tmp_path / "grouped-revision"
    source = make_source(root / "P_123456 (1).tif")
    before = source.read_bytes()
    start(window, qtbot, root)
    draft = cast(
        dict[str, object],
        cast(dict[str, object], window.bridge.snapshot()["intake"])["grouped_draft"],
    )
    draft["schema_version"] = 1
    draft.pop("sequence", None)
    draft.pop("excluded_group_ids", None)
    groups = cast(list[dict[str, object]], draft["groups"])
    draft["figures"] = [{"figure_id": "fig", "label": "Fig 1", "lane_count": 4}]
    groups[0].update(
        figure_id="fig",
        protein_label="P",
        selected_source_id=current(window).intake.sources[0].source_id,
    )
    request(window, "intake_grouping", grouping=draft)
    wait_saved(window, qtbot)
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    request(window, "intake_prepare")
    wait_saved(window, qtbot)
    prepared = current(window)
    assert isinstance(prepared, WBIntakeWorkflowProject)
    request(window, "intake_run", workflowDigest=intake_workflow_digest(prepared))
    wait_saved(window, qtbot)
    executed = current(window)
    assert isinstance(executed, WBIntakeCropProject)
    assert any(s.attempt for s in executed.workflow.steps)
    request(window, "intake_edit")
    wait_saved(window, qtbot)
    editing = current(window)
    assert isinstance(editing, WBIntakeWorkflowProject) and editing.workflow.editing
    groups[0]["selected_source_id"] = None
    request(window, "intake_grouping", grouping=draft)
    wait_saved(window, qtbot)
    saved = current(window)
    assert isinstance(saved, WBIntakeCropProject)
    assert saved.workflow.editing and not saved.rows and not saved.intake_crops
    assert saved.intake.grouping is not None
    assert saved.intake.grouping.groups[0].selected_source_id is None
    request(window, "intake_run", workflowDigest=intake_workflow_digest(saved))
    wait_saved(window, qtbot)
    assert current(window) == saved
    workspace = window.host.workspace_path
    assert workspace is not None
    epoch = window.bridge.session_epoch
    window.open_project(workspace)
    qtbot.waitUntil(
        lambda: (
            window.bridge.session_epoch > epoch
            and window.shutdown_stage == "idle"
            and window.host.view.project().project_id == saved.project_id
            and not window.host.operation_busy
        ),
        timeout=20000,
    )
    assert current(window) == saved
    assert source.read_bytes() == before
    # Re-selecting creates a pending row, never a recovered success or zero result.
    groups[0]["selected_source_id"] = saved.intake.sources[0].source_id
    request(window, "intake_grouping", grouping=draft)
    wait_saved(window, qtbot)
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    confirmed = current(window)
    assert isinstance(confirmed, WBIntakeWorkflowProject) and not confirmed.workflow.editing
    assert not confirmed.workflow.approved
    assert next(s for s in confirmed.workflow.steps if s.stage == "crop").status == "pending"


def test_raw_variants_assign_and_reopen_without_algorithm(
    intake_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = intake_window
    root = tmp_path / "instrument"
    a = make_source(root / "run1" / "Image001 (1).tif")
    b = make_source(root / "run1" / "Image001 (2).tif", 2000)
    alias = make_source(root / "run2" / a.name)
    broken = root / "bad.tif"
    broken.write_bytes(b"invalid TIFF")
    before = {p: p.read_bytes() for p in (a, b, alias, broken)}
    start(window, qtbot, root)
    project = current(window)
    assert len(project.intake.sources) == 3
    assert not project.rows and not project.analyses and project.ocr is None
    assert {s.relative_path.split("/", 1)[1] for s in project.intake.sources} == {
        "run1/Image001 (1).tif",
        "run1/Image001 (2).tif",
        "run2/Image001 (1).tif",
    }
    assert len(window.host.intake.issues) == 1
    assert not window.host.automatic.last_output_path
    plan(window, qtbot)
    assert all(row.lane_count == 8 and row.source is None for row in current(window).rows)
    sources = current(window).intake.sources
    request(
        window,
        "intake_assign",
        bindings=[
            {"protein_id": "protein-b", "source_id": sources[0].source_id},
            {"protein_id": "protein-a", "source_id": sources[1].source_id},
        ],
    )
    wait_saved(window, qtbot)
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    expected = current(window)
    assert expected.intake.confirmed_digest
    assert expected.rows[0].source == sources[1].asset
    assert all(row.roi is None and not row.reviewed for row in expected.rows)
    window.bridge.request("reanalyze")
    assert "阶段执行" in str(window.bridge.snapshot()["status"])
    path = window.host.workspace_path
    window.open_project(path)
    qtbot.waitUntil(
        lambda: window.bridge.session_epoch == 1 and window.shutdown_stage == "idle",
        timeout=20000,
    )
    wait_saved(window, qtbot)
    restored = current(window)
    assert restored.intake == expected.intake
    assert window.navigation.read(path)["mode"] == "intake"
    snapshot = cast(dict[str, object], window.bridge.snapshot()["intake"])
    thumbnails = cast(list[dict[str, object]], snapshot["sources"])
    assert all(source["preview"] for source in thumbnails)
    assert all(p.read_bytes() == data for p, data in before.items())
    assert set(root.rglob("*.tif")) == set(before)


def test_stale_batch_and_failed_confirmation_preserve_unconfirmed_state(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = intake_window
    root = tmp_path / "raw"
    make_source(root / "a.tif")
    make_source(root / "b.tif", 2000)
    start(window, qtbot, root)
    plan(window, qtbot)
    original = current(window)
    bindings = [
        {"protein_id": p.protein_id, "source_id": s.source_id}
        for p, s in zip(original.intake.proteins, original.intake.sources, strict=True)
    ]
    request(window, "intake_assign", bindings=bindings, sessionEpoch=-1)
    assert current(window) == original
    request(window, "intake_assign", bindings=bindings, digest="old")
    assert current(window) == original
    request(window, "intake_assign", bindings=bindings)
    wait_saved(window, qtbot)

    def failed_storage(*args: object, **kwargs: object) -> None:
        raise OSError("模拟磁盘不可写")

    monkeypatch.setattr(Workspace, "save_draft", failed_storage)
    request(window, "intake_confirm")
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=10000)
    assert not current(window).intake.confirmed_digest
    assert "磁盘不可写" in window.host.view.status.text()
    monkeypatch.undo()


def test_cancelled_late_preview_never_imports_asset(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = intake_window
    root = tmp_path / "raw"
    make_source(root / "first.tif")
    start(window, qtbot, root)
    path = make_source(root / "late.tif", 2000)
    before = current(window)
    replies: list[Callable[[WBReply], None]] = []

    def delayed(
        job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        assert job.operation == "preview"
        replies.append(callback)

    monkeypatch.setattr(window.host, "submit_tool_job", delayed)
    window.host.intake.import_paths((path,), root)
    assert len(replies) == 1
    window.host.cancel()
    replies[0](WBReply("late", value=None))
    assert not window.host.operation_busy
    assert current(window) == before
    monkeypatch.undo()


def test_invalid_thumbnail_reply_finishes_without_importing_or_leaking_busy_state(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = intake_window
    root = tmp_path / "raw"
    make_source(root / "first.tif")
    start(window, qtbot, root)
    path = make_source(root / "invalid-preview.tif", 2000)
    before = current(window)

    def invalid_preview(
        job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        assert job.operation == "preview" and job.preview_edge == 128
        raster = PreviewRaster("a" * 64, 512, 256, 192, 96, b"\x80" * (192 * 96), 16, ())
        callback(WBReply("invalid-preview", value=raster))

    monkeypatch.setattr(window.host, "submit_tool_job", invalid_preview)
    window.host.intake.import_paths((path,), root)
    assert not window.host.operation_busy
    assert current(window) == before
    assert len(window.host.intake.issues) == 1
    assert "128" in window.host.intake.issues[0]
    monkeypatch.undo()


@pytest.mark.parametrize("together", [False, True])
def test_distinct_export_folders_keep_same_named_same_content_candidates(
    intake_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path, together: bool
) -> None:
    window = intake_window
    first = make_source(tmp_path / "a" / "export" / "Image001.tif")
    second = make_source(tmp_path / "b" / "export" / "Image001.tif")
    assert first.read_bytes() == second.read_bytes()
    if together:
        window.start_from_images([first.parent, second.parent], intake=True)
        qtbot.waitUntil(
            lambda: window.shutdown_stage == "idle" and bool(window.host.workspace_path),
            timeout=20000,
        )
    else:
        start(window, qtbot, first.parent)
        window.host.intake.import_folder(second.parent)
    wait_saved(window, qtbot)
    sources = current(window).intake.sources
    assert len(sources) == 2 and sources[0].source_id != sources[1].source_id
    assert sources[0].asset.sha256 == sources[1].asset.sha256
    assert sources[0].asset.size_bytes == sources[1].asset.size_bytes
    assert sources[0].relative_path != sources[1].relative_path
    grouped_snapshot = cast(dict[str, object], window.bridge.snapshot()["intake"])
    grouped_draft = cast(dict[str, object], grouped_snapshot["grouped_draft"])
    assert len(cast(list[object], grouped_draft["groups"])) == 2
    window.host.intake.import_folder(second.parent)
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=10000)
    assert current(window).intake.sources == sources
    path = window.host.workspace_path
    project_id = current(window).project_id
    window.open_project(path)
    qtbot.waitUntil(
        lambda: (
            window.bridge.session_epoch == 1
            and window.shutdown_stage == "idle"
            and window.host.view.project().project_id == project_id
            and not window.host.operation_busy
        ),
        timeout=20000,
    )
    assert current(window).intake.sources == sources
    window.host.intake.import_folder(first.parent)
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=10000)
    assert current(window).intake.sources == sources


def test_intake_rejects_outside_root_before_starting_an_operation(
    intake_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = intake_window
    first = make_source(tmp_path / "selected" / "a.tif")
    outside = make_source(tmp_path / "outside" / "b.tif")
    start(window, qtbot, first.parent)
    saved = current(window)
    with pytest.raises(ValueError, match="不属于"):
        window.host.intake.import_paths((outside,), first.parent)
    assert not window.host.operation_busy and current(window) == saved


def test_font_assets_never_enter_thumbnail_decoder(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = intake_window
    root = tmp_path / "raw"
    make_source(root / "first.tif")
    start(window, qtbot, root)
    font = AssetRef(
        asset_id="font", relative_path="assets/font.ttf", sha256="f" * 64, size_bytes=20
    )
    window.host.view.set_project(
        WBFigureProject(project_id="font-only", template=FigureTemplate(font=font))
    )
    jobs: list[WBJob] = []

    def decoder(
        job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        jobs.append(job)

    monkeypatch.setattr(window.host, "_wb", decoder)
    window.host.load_thumbnails()
    assert not window.host.operation_busy and jobs == []
    monkeypatch.undo()


def reviewed_intake_fig(window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path) -> None:
    root = tmp_path / "raw"
    make_source(root / "a.tif")
    make_source(root / "b.tif", 2000)
    start(window, qtbot, root)
    plan(window, qtbot)
    before = current(window)
    request(
        window,
        "intake_assign",
        bindings=[
            {"protein_id": p.protein_id, "source_id": s.source_id}
            for p, s in zip(before.intake.proteins, before.intake.sources, strict=True)
        ],
    )
    wait_saved(window, qtbot)
    request(window, "intake_confirm")
    wait_saved(window, qtbot)
    request(window, "intake_prepare")
    wait_saved(window, qtbot)
    prepared = current(window)
    assert isinstance(prepared, WBIntakeWorkflowProject)
    request(window, "intake_run", workflowDigest=intake_workflow_digest(prepared))
    wait_saved(window, qtbot)
    for row_id in ("protein-a", "protein-b"):
        pending = current(window)
        assert isinstance(pending, WBIntakeFigureProject)
        request(
            window,
            "intake_crop_review",
            rowId=row_id,
            workflowDigest=intake_workflow_digest(pending),
            roi={"x": 12, "y": 10, "width": 120, "height": 40},
        )
        wait_saved(window, qtbot)


def test_complete_intake_fig_is_saved_before_real_worker_and_restores_verified_runs(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = intake_window
    reviewed_intake_fig(window, qtbot, tmp_path)
    snapshots: list[dict[str, object]] = []
    original_prepare = Workspace.prepare_run

    def record_prepare(
        store: Workspace, document_id: str, revision: int | None = None
    ) -> RunRecord:
        snapshot = store.load_draft(document_id, revision)
        snapshots.append(json.loads(store.read_asset(snapshot.asset)))
        return original_prepare(store, document_id, revision)

    monkeypatch.setattr(Workspace, "prepare_run", record_prepare)
    reviewed = current(window)
    assert isinstance(reviewed, WBIntakeFigureProject)
    request(window, "intake_run", workflowDigest=intake_workflow_digest(reviewed))
    wait_saved(window, qtbot)
    finished = current(window)
    assert isinstance(finished, WBIntakeFigureProject)
    assert len(finished.intake_figures) == 1, window.host.view.status.text()
    assert len(snapshots) == 2, window.host.view.status.text()
    for frozen in snapshots:
        steps = cast(list[dict[str, object]], cast(dict[str, object], frozen["workflow"])["steps"])
        assert next(s for s in steps if s["stage"] == "compose")["status"] == "done"
        assert next(s for s in steps if s["stage"] == "measure")["status"] == "running"
        assert frozen["intake_figures"]
    assert next(s for s in finished.workflow.steps if s.stage == "measure").status == "done", (
        window.host.view.status.text()
    )
    assert isinstance(finished, WBIntakeOutputProject)
    assert next(s for s in finished.workflow.steps if s.stage == "export").status == "done"
    assert len(finished.intake_outputs) == 1 and finished.intake_outputs[0].complete
    output = Path(finished.intake_outputs[0].destination)
    assert (output / "project.zip").is_file() and (output / "measurements.xlsx").is_file()
    index = json.loads((output / "index.json").read_bytes())
    assert index["complete"] is True and index["errors"] == []
    assert len(cast(list[object], window.bridge.snapshot()["cells"])) == 16
    (tmp_path / "complete-web-snapshot.json").write_text(
        json.dumps(window.bridge.snapshot(), ensure_ascii=False), encoding="utf-8"
    )
    assert len(finished.analyses) == 2 and len(window.host.project_results) == 2
    assert all(
        p.run and p.run.state == "succeeded" and p.run.pid and p.run.pid > 0
        for p in finished.analyses
    )
    assert all(p.request.revision == p.run.revision for p in finished.analyses if p.run)
    assert all(
        b.status == "not_detected" and b.measurement is None
        for result in window.host.project_results
        for lane in result.result.lanes
        for b in lane.bands
    )
    png = Path(window.host.workspace_path) / finished.intake_figures[0].image.relative_path
    assert png.read_bytes().startswith(b"\x89PNG")
    request(
        window,
        "intake_view_figure",
        figureId="fig-a",
        workflowDigest=intake_workflow_digest(finished),
    )
    wait_saved(window, qtbot)
    snapshot = window.bridge.snapshot()
    assert snapshot["montage"]
    regions = cast(list[dict[str, object]], snapshot["montageRegions"])
    assert [r["rowId"] for r in regions] == ["protein-a", "protein-b"]
    assert all(r["sourceRoi"] == {"x": 12, "y": 10, "width": 120, "height": 40} for r in regions)
    assert current(window).revision == finished.revision
    previous_host, epoch = window.host, window.bridge.session_epoch
    window.open_project(window.host.workspace_path)
    qtbot.waitUntil(
        lambda: (
            window.host is not previous_host
            and window.bridge.session_epoch > epoch
            and window.shutdown_stage == "idle"
        ),
        timeout=20000,
    )
    wait_saved(window, qtbot)
    restored = current(window)
    assert isinstance(restored, WBIntakeFigureProject)
    assert len(window.host.project_results) == 2
    assert tuple(p.run for p in restored.analyses) == tuple(p.run for p in finished.analyses)
    assert not restored.workflow.approved
    assert isinstance(restored, WBIntakeOutputProject)
    assert restored.intake_outputs == finished.intake_outputs
    old_zip = (output / "project.zip").read_bytes()
    request(window, "intake_export", workflowDigest=intake_workflow_digest(restored))
    wait_saved(window, qtbot)
    repeated = current(window)
    assert isinstance(repeated, WBIntakeOutputProject) and len(repeated.intake_outputs) == 2
    assert repeated.intake_outputs[-1].complete
    assert repeated.intake_outputs[-1].destination != str(output)
    assert (output / "project.zip").read_bytes() == old_zip
    assert len(window.host.project_results) == 2
    settings = QSettings(str(tmp_path / "restored-intake.ini"), QSettings.Format.IniFormat)
    fresh = WebWorkbenchWindow(settings=settings)
    fresh.show()
    try:
        target = tmp_path / "restored-intake"
        fresh.host.restore_archive(str(output / "project.zip"), str(target))
        qtbot.waitUntil(lambda: fresh.host.workspace_path == str(target), timeout=20000)
        wait_saved(fresh, qtbot)
        imported = current(fresh)
        assert isinstance(imported, WBIntakeOutputProject)
        assert len(imported.imported_runs) == 2 and len(fresh.host.project_results) == 2
        assert (
            next(s for s in imported.workflow.steps if s.stage == "export").status == "interrupted"
        )
        replies: list[StorageReply] = []
        fresh.host.submit_storage_job(StorageCommand("runs"), replies.append)
        qtbot.waitUntil(lambda: bool(replies), timeout=10000)
        assert replies[0].value == ()
        request(fresh, "intake_export", workflowDigest=intake_workflow_digest(imported))
        wait_saved(fresh, qtbot)
        again = current(fresh)
        assert isinstance(again, WBIntakeOutputProject)
        assert again.intake_outputs[-1].complete
        assert next(s for s in again.workflow.steps if s.stage == "export").status == "done"
        assert (output / "project.zip").read_bytes() == old_zip
    finally:
        close_and_dispose_window(
            fresh, qtbot, resources_closed=lambda: fresh.host.resources_closed, timeout=20000
        )
    previous_revision = repeated.revision
    historical = repeated.model_dump_json()
    request(
        window,
        "intake_crop_revise",
        rowId="protein-a",
        workflowDigest=intake_workflow_digest(repeated),
        roi={"x": 14, "y": 12, "width": 118, "height": 38},
    )
    wait_saved(window, qtbot)
    corrected = current(window)
    assert isinstance(corrected, WBIntakeOutputProject)
    assert not corrected.analyses and not corrected.intake_figures
    assert corrected.intake_outputs == repeated.intake_outputs
    assert corrected.revision > previous_revision
    assert window.host.intake_workflow.output_snapshot(corrected)["current"] is False
    assert (output / "project.zip").read_bytes() == old_zip
    old_replies: list[StorageReply] = []
    window.host.submit_storage_job(
        StorageCommand("load", document_id=corrected.project_id, revision=previous_revision),
        old_replies.append,
    )
    qtbot.waitUntil(lambda: bool(old_replies), timeout=10000)
    assert old_replies[0].error_code is None
    assert read_figure_project(old_replies[0].data).model_dump_json() == historical
    previous_host, epoch = window.host, window.bridge.session_epoch
    window.open_project(window.host.workspace_path)
    qtbot.waitUntil(
        lambda: (
            window.host is not previous_host
            and window.bridge.session_epoch > epoch
            and window.shutdown_stage == "idle"
        ),
        timeout=20000,
    )
    wait_saved(window, qtbot)
    reopened = current(window)
    assert isinstance(reopened, WBIntakeOutputProject)
    assert reopened.intake_outputs == corrected.intake_outputs
    assert not reopened.analyses and not reopened.intake_figures
    assert window.host.intake_workflow.output_snapshot(reopened)["current"] is False
    monkeypatch.undo()


@pytest.mark.parametrize("fault", ["compose_save", "measure_claim_save", "late_compose_cancel"])
def test_intake_fig_failed_save_or_cancel_never_starts_measurement(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    window = intake_window
    reviewed_intake_fig(window, qtbot, tmp_path)
    original_save = Workspace.save_draft
    original_submit = window.host.submit_tool_job
    replies: list[tuple[Callable[[WBReply], None], WBReply]] = []
    run_count: list[str] = []
    original_prepare = Workspace.prepare_run

    def prepare(store: Workspace, document_id: str, revision: int | None = None) -> RunRecord:
        run_count.append(document_id)
        return original_prepare(store, document_id, revision)

    def save(
        store: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None = None,
    ) -> DraftSnapshot:
        raw = json.loads(data)
        stages = {s["stage"]: s["status"] for s in raw.get("workflow", {}).get("steps", [])}
        if fault == "compose_save" and stages.get("compose") == "done":
            raise OSError("injected compose output save failure")
        if fault == "measure_claim_save" and stages.get("measure") == "running":
            raise OSError("injected measure claim save failure")
        return original_save(
            store,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )

    def submit(
        job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        if fault == "late_compose_cancel" and job.operation == "intake_figure_prepare":
            original_submit(
                job, lambda reply: replies.append((callback, reply)), accept_errors=accept_errors
            )
        else:
            original_submit(job, callback, accept_errors=accept_errors)

    monkeypatch.setattr(Workspace, "prepare_run", prepare)
    monkeypatch.setattr(Workspace, "save_draft", save)
    monkeypatch.setattr(window.host, "submit_tool_job", submit)
    project = current(window)
    assert isinstance(project, WBIntakeFigureProject)
    request(window, "intake_run", workflowDigest=intake_workflow_digest(project))
    if fault == "late_compose_cancel":
        qtbot.waitUntil(lambda: bool(replies), timeout=20000)
        callback, reply = replies.pop()
        assert not reply.error
        window.host.cancel()
        callback(reply)
        wait_saved(window, qtbot)
    else:
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=20000)
    stopped = current(window)
    assert isinstance(stopped, WBIntakeFigureProject)
    assert not run_count
    assert all(p.run is None for p in stopped.analyses)
    assert next(s for s in stopped.workflow.steps if s.stage == "measure").status != "done"
    if fault == "late_compose_cancel":
        assert not stopped.intake_figures and not stopped.analyses
        assert next(s for s in stopped.workflow.steps if s.stage == "compose").status == "cancelled"
    elif fault == "compose_save":
        assert not stopped.intake_figures
    else:
        assert len(stopped.intake_figures) == 1
    monkeypatch.undo()


def test_cancelled_intake_measurement_does_not_launch_next_source(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = intake_window
    reviewed_intake_fig(window, qtbot, tmp_path)
    held: list[tuple[ProjectMeasurementSession, ProjectRowAnalysis, RunRecord, StorageReply]] = []
    launch = cast(
        Callable[[ProjectMeasurementSession, ProjectRowAnalysis, RunRecord, StorageReply], None],
        ProjectMeasurementSession.__dict__["_launch"],
    )

    def hold(
        session: ProjectMeasurementSession,
        plan: ProjectRowAnalysis,
        run: RunRecord,
        reply: StorageReply,
    ) -> None:
        held.append((session, plan, run, reply))

    monkeypatch.setattr(ProjectMeasurementSession, "_launch", hold)
    before = current(window)
    assert isinstance(before, WBIntakeFigureProject)
    request(window, "intake_run", workflowDigest=intake_workflow_digest(before))
    qtbot.waitUntil(lambda: len(held) == 1, timeout=20000)
    assert window.host.operation_busy
    window.host.cancel()
    launch(*held[0])
    wait_saved(window, qtbot)
    cancelled = current(window)
    assert isinstance(cancelled, WBIntakeFigureProject)
    assert len(held) == 1
    assert next(s for s in cancelled.workflow.steps if s.stage == "measure").status == "cancelled"
    assert len(cancelled.intake_figures) == 1
    assert not window.host.project_results
    assert all(p.run is None or p.run.state != "succeeded" for p in cancelled.analyses)
    assert not window.host.has_unsaved_changes
    monkeypatch.undo()


@pytest.mark.parametrize(
    "fault", ["claim_save", "output_save", "late_cancel", "worker_error", "cancel_before_export"]
)
def test_intake_output_failure_and_cancellation_never_fabricate_completion(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    from wb_tool.adapters import intake_output

    window = intake_window
    reviewed_intake_fig(window, qtbot, tmp_path)
    original_save = Workspace.save_draft
    original_export = window.host.submit_export_job
    execute = cast(
        Callable[[IntakeWorkflowSession, IntakeWorkflowTicket], None],
        IntakeWorkflowSession.__dict__["_execute"],
    )
    held: list[tuple[Callable[[WBReply], None], WBReply]] = []

    def save(
        store: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None = None,
    ) -> DraftSnapshot:
        saved = read_figure_project(data)
        step = (
            next((s for s in saved.workflow.steps if s.stage == "export"), None)
            if isinstance(saved, WBIntakeWorkflowProject)
            else None
        )
        status = step.status if step else ""
        if (fault == "claim_save" and status == "running") or (
            fault == "output_save" and status == "done"
        ):
            raise OSError("injected output CAS failure")
        return original_save(
            store,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )

    def submit(
        job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        if fault == "late_cancel" and job.operation == "intake_output_export":
            original_export(
                job, lambda reply: held.append((callback, reply)), accept_errors=accept_errors
            )
        else:
            original_export(job, callback, accept_errors=accept_errors)

    def before_execute(ticket: IntakeWorkflowTicket) -> None:
        if fault == "cancel_before_export" and ticket.stage == "export":
            window.host.cancel()
        execute(window.host.intake_workflow, ticket)

    def error(*args: object, **kwargs: object) -> None:
        raise OSError("injected output disk failure")

    monkeypatch.setattr(Workspace, "save_draft", save)
    monkeypatch.setattr(window.host, "submit_export_job", submit)
    monkeypatch.setattr(window.host.intake_workflow, "_execute", before_execute)
    if fault == "worker_error":
        monkeypatch.setattr(intake_output, "export_intake_outputs", error)
    before = current(window)
    assert isinstance(before, WBIntakeOutputProject)
    request(window, "intake_run", workflowDigest=intake_workflow_digest(before))
    if fault == "late_cancel":
        qtbot.waitUntil(lambda: bool(held), timeout=20000)
        window.host.cancel()
        held[0][0](held[0][1])
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=20000)
    final = current(window)
    assert isinstance(final, WBIntakeOutputProject)
    step = next(s for s in final.workflow.steps if s.stage == "export")
    assert step.status != "done" and not final.intake_outputs
    assert len(window.host.project_results) == 2
    assert all(plan.run and plan.run.state == "succeeded" for plan in final.analyses)
    folders = list((Path(window.host.workspace_path) / "outputs").glob("WB-intake-*"))
    assert len(folders) == (1 if fault in {"output_save", "late_cancel"} else 0)
    if folders:
        assert (folders[0] / "project.zip").is_file()
        assert window.host.intake_workflow.output_snapshot(final)["committed"] is False
    if fault in {"late_cancel", "cancel_before_export"}:
        assert step.status == "cancelled"
    if fault == "worker_error":
        assert step.status == "failed" and "disk failure" in step.reason
    if fault == "output_save":
        request(window, "intake_export", workflowDigest=intake_workflow_digest(final))
        assert not window.host.operation_busy
        assert current(window) == final
        assert list((Path(window.host.workspace_path) / "outputs").glob("WB-intake-*")) == folders
    monkeypatch.undo()


def test_export_discovery_real_worker_save_and_reopen(
    intake_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = intake_window
    directory = tmp_path / "instrument"
    directory.mkdir()
    signal = np.full((180, 360), 60000, dtype=np.uint16)
    white = np.zeros_like(signal)
    white[55:125, 50:310] = 60000
    merged = white.copy()
    for x in (80, 135, 190, 245):
        signal[80:94, x : x + 28] = 8000
        merged[80:94, x : x + 28] = 8000
    for i, raw in enumerate((signal, white, merged), 1):
        tifffile.imwrite(directory / f"P_123456_0 ({i}).tiff", raw)
    start(window, qtbot, directory)
    request(window, "intake_discover")
    qtbot.waitUntil(lambda: current(window).intake.discovery is not None, timeout=20000)
    wait_saved(window, qtbot)
    report = current(window).intake.discovery
    assert report is not None
    signal_record = next(o for o in report.observations if o.role == "signal")
    assert signal_record.regions and not current(window).intake.figures
    request(
        window,
        "intake_accept_discovery",
        selections=[
            {
                "source_id": signal_record.source_id,
                "figure_label": "Fig",
                "protein_label": "P",
                "lane_count": 4,
                "region_index": 0,
            }
        ],
    )
    wait_saved(window, qtbot)
    assert len(current(window).intake.assignments) == 1
    workspace, epoch = window.host.workspace_path, window.bridge.session_epoch
    window.open_project(workspace)
    qtbot.waitUntil(
        lambda: window.bridge.session_epoch > epoch and window.shutdown_stage == "idle",
        timeout=20000,
    )
    wait_saved(window, qtbot)
    restored = current(window).intake.discovery
    assert restored is not None and restored.selections[0].source_id == signal_record.source_id


def test_sequence_real_page_two_figs_pause_continue_stage_barriers_and_reopen(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = intake_window
    root = tmp_path / "sequence-raw"
    a = make_source(root / "A_123456 (1).tif")
    b = make_source(root / "B_123456 (1).tif", 2000)
    originals = {p: p.read_bytes() for p in (a, b)}
    start(window, qtbot, root)

    def js(code: str) -> object:
        replies: list[object] = []
        window.web.page().runJavaScript(code, replies.append)
        qtbot.waitUntil(lambda: bool(replies), timeout=10000)
        return replies[0]

    qtbot.waitUntil(
        lambda: (
            js(
                "!!document.querySelector('[data-group-action=add-fig]') && "
                "!document.querySelector('[data-group-action=add-fig]').disabled"
            )
            is True
        ),
        timeout=10000,
    )
    snapshots: list[dict[str, object]] = []
    original_save = Workspace.save_draft

    def record_save(
        store: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None,
    ) -> object:
        result = original_save(
            store,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )
        snapshots.append(json.loads(data))
        return result

    monkeypatch.setattr(Workspace, "save_draft", record_save)
    assert (
        js("""
      window.sequenceModes=[];window.sequenceSwitch=switchMode;
      switchMode=function(next){const result=sequenceSwitch(next);
        sequenceModes.push(mode);return result;};
      window.fillSequence=(el,value)=>{el.value=value;
        el.dispatchEvent(new Event('input',{bubbles:true}));};
      document.querySelector('[data-group-action=add-fig]').click();
      fillSequence(document.querySelector('[data-group-field=fig-label]'),'First');
      fillSequence(document.querySelector('[data-group-field=lanes]'),'4');
      fillSequence(document.querySelector('[data-group-field=proteins]'),'Alpha');
      document.querySelector('[data-group-action=add-fig]').click();
      fillSequence(document.querySelectorAll('[data-group-field=fig-label]')[1],'Second');
      fillSequence(document.querySelectorAll('[data-group-field=lanes]')[1],'5');
      fillSequence(document.querySelectorAll('[data-group-field=proteins]')[1],'Beta');
      document.querySelectorAll('[data-group-source]')[0].click();
      document.querySelectorAll('[data-group-source]')[1].click();
      !document.querySelector('[data-group-action=start]').disabled
    """)
        is True
    )
    js("document.querySelector('[data-group-action=start]').click();true")
    wait_saved(window, qtbot)
    paused = current(window)
    assert isinstance(paused, WBIntakeCropProject), window.host.view.status.text()
    assert paused.workflow.policy == "intake_workflow@3"
    assert [s.status for s in paused.workflow.steps if s.stage == "crop"] == [
        "needs_review",
        "pending",
    ]
    assert all(s.attempt == 0 for s in paused.workflow.steps if s.stage != "crop")
    qtbot.waitUntil(
        lambda: (
            js(
                "mode==='review' && !state.busy && "
                "state.intake.workflow.steps.some(s=>s.status==='needs_review')"
            )
            is True
        ),
        timeout=10000,
    )
    assert js("row().id") == paused.rows[0].row_id
    for index in (0, 1):
        qtbot.waitUntil(lambda: js("!state.busy") is True, timeout=10000)
        assert (
            js("""
          commitCrop({x:12,y:10,width:120,height:40},row().roi);
          !document.querySelector('[data-intake-crop-action=run]').disabled
        """)
            is True
        ), window.host.view.status.text()
        js("document.querySelector('[data-intake-crop-action=run]').click();true")
        wait_saved(window, qtbot)
        if index == 0:
            halfway = current(window)
            assert isinstance(halfway, WBIntakeCropProject)
            assert [s.status for s in halfway.workflow.steps if s.stage == "crop"] == [
                "done",
                "needs_review",
            ]
            assert all(s.attempt == 0 for s in halfway.workflow.steps if s.stage != "crop")
            qtbot.waitUntil(
                lambda halfway=halfway: js("row().id") == halfway.rows[1].row_id, timeout=10000
            )
    finished = current(window)
    assert isinstance(finished, WBIntakeOutputProject), window.host.view.status.text()
    assert all(s.status == "done" for s in finished.workflow.steps), window.host.view.status.text()
    assert len(finished.intake_figures) == 2 and len(finished.analyses) == 2
    assert all(a.run and a.run.pid and a.run.state == "succeeded" for a in finished.analyses)
    assert len(finished.intake_outputs) == 1 and finished.intake_outputs[0].complete
    qtbot.waitUntil(lambda: js("mode==='results'") is True, timeout=10000)
    modes = js("JSON.stringify(sequenceModes)")
    assert isinstance(modes, str)
    visited = json.loads(modes)
    assert all(m in visited for m in ("review", "layout", "quant", "results")), visited
    for snapshot in snapshots:
        ledger = cast(dict[str, object], snapshot.get("workflow", {}))
        steps = cast(list[dict[str, object]], ledger.get("steps", []))
        for step in steps:
            if step["status"] == "running" and step["stage"] in ("compose", "measure"):
                required = ("crop",) if step["stage"] == "compose" else ("crop", "compose")
                assert all(s["status"] == "done" for s in steps if s["stage"] in required)
    assert any(s.get("workflow") for s in snapshots)
    output = Path(finished.intake_outputs[0].destination)
    old_zip = (output / "project.zip").read_bytes()
    old_host = window.host
    window.open_project(window.host.workspace_path)
    qtbot.waitUntil(
        lambda: window.host is not old_host and window.shutdown_stage == "idle", timeout=20000
    )
    wait_saved(window, qtbot)
    reopened = current(window)
    assert isinstance(reopened, WBIntakeOutputProject)
    assert reopened.intake_outputs == finished.intake_outputs
    assert [s.attempt for s in reopened.workflow.steps] == [
        s.attempt for s in finished.workflow.steps
    ]
    assert (
        cast(
            dict[str, object],
            cast(dict[str, object], window.bridge.snapshot()["intake"])["automation"],
        )["follow"]
        is False
    )
    assert (output / "project.zip").read_bytes() == old_zip
    assert all(p.read_bytes() == content for p, content in originals.items())


@pytest.mark.parametrize("failure", ["stale", "cas-failed", "cancel-encode"])
def test_sequence_start_never_launches_before_exact_cas_commit(
    intake_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    from wb_tool.api import (
        IntakeDraftFigure,
        IntakeSequenceProtein,
        configure_intake_sequence,
        intake_grouping,
    )

    window = intake_window
    make_source(tmp_path / "raw" / "A_123456.tif")
    start(window, qtbot, tmp_path / "raw")
    p = current(window)
    initial = p.model_dump_json()
    grouping = intake_grouping(p)
    grouping = type(grouping).model_validate(
        {
            **dict(grouping),
            "groups": tuple(
                g.model_copy(update={"selected_source_id": g.source_ids[0]})
                for g in grouping.groups
            ),
        }
    )
    grouping = configure_intake_sequence(
        grouping,
        (IntakeDraftFigure(figure_id="f", label="Fig", lane_count=4),),
        (IntakeSequenceProtein(entry_id="a", figure_id="f", label="A"),),
    )
    jobs: list[str] = []
    captured: list[tuple[WBJob, Callable[[WBReply], None]]] = []
    original_job = window.host.submit_tool_job
    original_save = Workspace.save_draft

    def submitted(
        job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        jobs.append(job.operation)
        if failure == "cancel-encode" and job.operation == "encode":
            captured.append((job, callback))
            return
        original_job(job, callback, accept_errors=accept_errors)

    def failed_save(
        store: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None,
    ) -> object:
        if b'"workflow"' in data:
            raise OSError("synthetic CAS save failure")
        return original_save(
            store,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )

    monkeypatch.setattr(window.host, "submit_tool_job", submitted)
    if failure == "cas-failed":
        monkeypatch.setattr(Workspace, "save_draft", failed_save)
    request(
        window,
        "intake_sequence_start",
        grouping=grouping.model_dump(mode="json"),
        requestId="one",
        digest="stale" if failure == "stale" else intake_digest(p),
    )
    if failure == "cancel-encode":
        assert len(captured) == 1
        window.host.cancel()
        captured[0][1](WBReply("late-encode", value=b"cancelled payload must not be committed"))
    wait_saved(window, qtbot)
    assert current(window).model_dump_json() == initial
    assert not any(
        name in jobs
        for name in ("intake_crop_prepare", "intake_crop_propose", "intake_crop_export")
    )
    response = cast(
        dict[str, object],
        cast(dict[str, object], window.bridge.snapshot()["intake"])["sequenceResponse"],
    )
    assert response["status"] == "failed" and response["requestId"] == "one"
