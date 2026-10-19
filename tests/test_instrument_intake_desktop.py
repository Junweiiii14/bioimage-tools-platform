"""Real storage and desktop boundary of the new instrument intake stage."""

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import tifffile
from bioimage_app.web_window import WebWorkbenchWindow
from platform_runtime.api import Workspace
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot
from wb_tool.api import PreviewRaster, WBIntakeProject, WBJob, WBReply, intake_digest

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
