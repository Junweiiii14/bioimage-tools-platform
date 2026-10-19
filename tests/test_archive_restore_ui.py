"""Restore to real storage, reopen and run new local measurements without foreign receipts."""

import os
from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

import pytest
from bioimage_app.project_restore import restore_archive_workspace
from platform_runtime.api import IntegrityError, StateConflict, Workspace
from pytestqt.qtbot import QtBot
from wb_tool.api import (
    WBRestoredProject,
    inspect_project_archive,
    read_figure_project,
    stage_project_archive,
)

from tests.test_project_measurements import item
from tests.test_project_measurements import windows as windows
from tools.wb.tests.test_archive_restore import exported

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def test_new_workspace_snapshot_keeps_revision_cas_and_no_foreign_runs(tmp_path: Path) -> None:
    source, project, _ = exported(tmp_path)
    target = tmp_path / "restored"
    result = restore_archive_workspace(str(source), str(target), Event())
    assert not result.error
    with Workspace.open(target) as store:
        snapshot = store.load_draft(project.project_id)
        assert snapshot.revision == project.revision
        restored = read_figure_project(store.read_asset(snapshot.asset))
        assert isinstance(restored, WBRestoredProject) and len(restored.imported_runs) == 3
        assert store.list_runs() == ()
        assert store.read_asset(restored.archive_sources[0].archive) == source.read_bytes()
        with pytest.raises(StateConflict):
            store.import_draft_snapshot("second", "wb-figure", 7, b"{}")
        with pytest.raises(StateConflict):
            store.save_draft(
                project.project_id,
                "wb-figure",
                project.revision + 2,
                b"{}",
                expected_previous_revision=project.revision,
            )
        store.save_draft(
            project.project_id,
            "wb-figure",
            project.revision + 1,
            restored.model_copy(update={"revision": project.revision + 1})
            .model_dump_json()
            .encode(),
            expected_previous_revision=project.revision,
        )
    before = (target / "workspace.json").read_bytes()
    with pytest.raises(FileExistsError):
        restore_archive_workspace(str(source), str(target), Event())
    assert (target / "workspace.json").read_bytes() == before
    marker = target / ".restore-incomplete"
    marker.write_text("incomplete")
    with pytest.raises(IntegrityError, match="尚未完成"):
        Workspace.open(target)


def test_normal_save_still_starts_at_zero(tmp_path: Path) -> None:
    with Workspace.create(tmp_path / "fresh") as store:
        with pytest.raises(StateConflict, match="修订 0"):
            store.save_draft("doc", "wb", 8, b"{}", expected_previous_revision=None)
        snapshot = store.import_draft_snapshot("doc", "wb", 8, b"{}")
        assert snapshot.revision == 8 and store.list_runs() == ()
        store.save_draft("doc", "wb", 9, b"{}", expected_previous_revision=8)


def test_ui_restore_reopen_edit_recompute_and_restore_again(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    source, _, _ = exported(tmp_path)
    target = tmp_path / "restored"
    window = windows()
    window.restore_archive(str(source), str(target))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    project = window.view.project()
    assert isinstance(project, WBRestoredProject), window.view.status.text()
    table = window.view.analysis.results
    assert [item(table, i, 3).text() for i in range(6)] == ["4000", "", "0", "8000", "16000", "0"]
    assert "归档历史" in item(table, 0, 7).text()
    assert window.view.ocr.result_view.table.rowCount() == 6
    assert item(window.view.ocr.result_view.table, 0, 3).text() == "4000"
    assert window.view.history_label.text()
    capture = os.environ.get("BIOIMAGE_RESTORE_CAPTURE")
    if capture:
        window.view.show_section("analysis")
        assert window.grab().save(capture)
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    with Workspace.open(target) as store:
        assert store.list_runs() == ()
    reopened = windows()
    reopened.open_workspace(str(target))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(project.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=20000)
    reopened.view.table.selectRow(0)
    qtbot.waitUntil(reopened.import_button.isEnabled)
    item(reopened.view.analysis.lanes, 0, 4).setText("6035")
    item(reopened.view.analysis.lanes, 0, 5).setText("6035")
    reopened.refresh_project_table()
    qtbot.waitUntil(reopened.import_button.isEnabled)
    assert item(reopened.view.analysis.results, 0, 3).text() == ""
    reopened.analyze_project()
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=20000)
    assert item(reopened.view.analysis.results, 0, 3).text() == "2500", reopened.view.status.text()
    assert item(reopened.view.analysis.results, 0, 7).text() == "本机运行"
    assert "归档历史" in item(reopened.view.analysis.results, 3, 7).text()
    second = tmp_path / "second.zip"
    reopened.compose(str(second))
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=15000)
    assert second.exists(), reopened.view.status.text()
    checked = inspect_project_archive(str(second))
    assert isinstance(checked, WBRestoredProject) and len(checked.imported_runs) == 3
    with ZipFile(second) as archive:
        assert "归档历史证据" in archive.read("tables/source.csv").decode("utf-8-sig")
    reopened.close()
    qtbot.waitUntil(lambda: reopened.resources_closed, timeout=20000)
    with Workspace.open(target) as store:
        runs = store.list_runs()
        assert len(runs) == 1 and runs[0].state == "succeeded" and runs[0].pid
    third = windows()
    third.restore_archive(str(second), str(tmp_path / "restored-again"))
    qtbot.waitUntil(third.import_button.isEnabled, timeout=20000)
    twice = third.view.project()
    assert isinstance(twice, WBRestoredProject) and len(twice.archive_sources) == 2
    assert len(twice.imported_runs) == 4
    assert item(third.view.analysis.results, 0, 3).text() == "2500"


@pytest.mark.parametrize("action", ["cancel", "close"])
def test_cancel_or_close_waits_for_restore_thread_and_publishes_nothing(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    from bioimage_app import project_restore

    source, _, _ = exported(tmp_path)
    original = stage_project_archive
    entered, release = Event(), Event()

    def delayed(*args: Any, **kwargs: Any):
        entered.set()
        if not release.wait(5):
            raise ValueError("restore test timed out")
        return original(*args, **kwargs)

    monkeypatch.setattr(project_restore, "stage_project_archive", delayed)
    window = windows()
    target = tmp_path / "cancelled"
    window.restore_archive(str(source), str(target))
    try:
        qtbot.waitUntil(entered.is_set)
        if action == "close":
            window.close()
            assert not window.resources_closed
        else:
            window.cancel()
    finally:
        release.set()
    qtbot.waitUntil(
        (lambda: window.resources_closed) if action == "close" else window.restore_button.isEnabled,
        timeout=15000,
    )
    assert not target.exists() and not list(tmp_path.glob(".wb-restore-*"))


def test_corrupt_history_on_reopen_blanks_only_its_values(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    source, project, _ = exported(tmp_path)
    target = tmp_path / "restored"
    restore_archive_workspace(str(source), str(target), Event())
    with Workspace.open(target) as store:
        restored = read_figure_project(store.read_asset(store.load_draft(project.project_id).asset))
        assert isinstance(restored, WBRestoredProject)
        result = restored.imported_runs[0].result
        assert result
        damaged = store.asset_path(result)
    damaged.write_bytes(b"bad")
    window = windows()
    window.open_workspace(str(target))
    qtbot.waitUntil(window.import_button.isEnabled)
    window.load_document(project.project_id)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=15000)
    assert isinstance(window.view.project(), WBRestoredProject), window.view.status.text()
    table = window.view.analysis.results
    assert item(table, 0, 3).text() == "" and item(table, 0, 4).text() == "result_unavailable"
    assert item(table, 3, 3).text() == "8000"


def test_publication_failure_leaves_no_usable_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bioimage_app import project_restore

    source, _, _ = exported(tmp_path)
    target = tmp_path / "failed"

    def fail_publish(*args: Any) -> None:
        raise OSError("controlled publication failure")

    monkeypatch.setattr(project_restore, "_publish", fail_publish)
    with pytest.raises(OSError, match="controlled"):
        restore_archive_workspace(str(source), str(target), Event())
    assert not target.exists() and not list(tmp_path.glob(".wb-restore-*"))


def test_close_after_publication_keeps_complete_project_without_opening_it(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bioimage_app import project_restore

    source, project, _ = exported(tmp_path)
    entered, release = Event(), Event()

    def completed_then_delayed(*args: Any, **kwargs: Any):
        result = restore_archive_workspace(*args, **kwargs)
        entered.set()
        if not release.wait(5):
            raise ValueError("published restore test timed out")
        return result

    monkeypatch.setattr(project_restore, "restore_archive_workspace", completed_then_delayed)
    target = tmp_path / "published"
    window = windows()
    window.restore_archive(str(source), str(target))
    try:
        qtbot.waitUntil(entered.is_set, timeout=10000)
        window.close()
        assert not window.resources_closed
    finally:
        release.set()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=15000)
    with Workspace.open(target) as store:
        assert store.load_draft(project.project_id).revision == project.revision
        assert store.list_runs() == ()
