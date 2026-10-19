"""Real storage and desktop boundary of the new instrument intake stage."""

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from threading import Event
from typing import cast

import numpy as np
import pytest
import tifffile
from bioimage_app.web_window import WebWorkbenchWindow
from platform_runtime.api import Workspace
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot
from tool_contracts.api import AssetRef
from wb_tool.api import (
    FigureTemplate,
    PreviewRaster,
    WBFigureProject,
    WBIntakeCropProject,
    WBIntakeProject,
    WBIntakeWorkflowProject,
    WBJob,
    WBReply,
    intake_digest,
    intake_workflow_digest,
    prepare_intake_workflow,
    propose_intake_crop,
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
    window.open_project(window.host.workspace_path)
    wait_saved(window, qtbot)
    assert current(window).schema_version == 12
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
    assert {s.relative_path for s in project.intake.sources} == {
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
    assert "尚未接通" in str(window.bridge.snapshot()["status"])
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


def test_distinct_export_folders_keep_same_named_same_content_candidates(
    intake_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = intake_window
    first = make_source(tmp_path / "export-a" / "Image001.tif")
    second = make_source(tmp_path / "export-b" / "Image001.tif")
    assert first.read_bytes() == second.read_bytes()
    start(window, qtbot, first.parent)
    window.host.intake.import_folder(second.parent)
    wait_saved(window, qtbot)
    sources = current(window).intake.sources
    assert len(sources) == 2 and sources[0].source_id != sources[1].source_id
    assert sources[0].asset.sha256 == sources[1].asset.sha256
    assert sources[0].asset.size_bytes == sources[1].asset.size_bytes
    window.host.intake.import_folder(second.parent)
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=10000)
    assert current(window).intake.sources == sources
    path = window.host.workspace_path
    window.open_project(path)
    qtbot.waitUntil(
        lambda: window.bridge.session_epoch == 1 and window.shutdown_stage == "idle", timeout=20000
    )
    assert current(window).intake.sources == sources
    window.host.intake.import_folder(first.parent)
    qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=10000)
    assert current(window).intake.sources == sources


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
