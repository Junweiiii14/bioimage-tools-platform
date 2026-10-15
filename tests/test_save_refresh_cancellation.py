"""Cancellation across actual save/worker phases never restarts a cancelled follow-up."""

from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING

import pytest
from pytestqt.qtbot import QtBot
from wb_tool.api import (
    LoadedProjectOCR,
    LoadedProjectResult,
    ProjectTableCell,
    WBAutomaticProject,
    WBFigureProject,
    WBProjectOCR,
    fill_project_ocr_table,
    fill_project_table,
)

from tests.test_project_measurements import windows as windows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


@pytest.mark.parametrize("phase", ["project_table", "project_derived_tables"])
def test_cancel_saved_schema8_refresh_does_not_launch_follow_up(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
) -> None:
    window = windows()
    window.open_workspace(str(tmp_path / "workspace"), create=True)
    qtbot.waitUntil(window.import_button.isEnabled)
    window.view.set_project(WBAutomaticProject(project_id="cancel-saved-project"))
    entered, release = Event(), Event()
    operations: list[str] = []
    followups: list[str] = []

    def pause(operation: str) -> None:
        operations.append(operation)
        if operation == phase:
            entered.set()
            if not release.wait(10):
                raise ValueError("test phase release timed out")

    def table(
        project: WBFigureProject, results: tuple[LoadedProjectResult, ...]
    ) -> tuple[ProjectTableCell, ...]:
        pause("project_table")
        return fill_project_table(project, results)

    def derived(
        project: WBProjectOCR,
        results: tuple[LoadedProjectResult, ...],
        loaded: LoadedProjectOCR | None,
    ) -> tuple[ProjectTableCell, ...]:
        pause("project_derived_tables")
        return fill_project_ocr_table(project, results, loaded)

    monkeypatch.setattr("wb_tool.ui.background.fill_project_table", table)
    monkeypatch.setattr("wb_tool.ui.background.fill_project_ocr_table", derived)
    # Actual asynchronous storage save then actual background-table phase; only
    # the scheduling boundary is held, not its result or cancellation handling.
    window.save(after=lambda: followups.append("export-or-recognition"))
    try:
        qtbot.waitUntil(entered.is_set, timeout=10000)
        monkeypatch.setattr(window, "_ocr_refresh_pending", True)
        window.cancel()
        assert window.cancellation.is_set()
    finally:
        release.set()
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=10000)
    qtbot.wait(200)  # Queued derived-table timers must not revive the operation.
    assert window.cancellation.is_set()
    assert followups == []
    assert operations == (
        ["project_table"]
        if phase == "project_table"
        else ["project_table", "project_derived_tables"]
    )
    assert "取消" in window.view.status.text()

    # A fresh explicit refresh is a new operation and must remain available.
    window.refresh_ocr_table(after=lambda: followups.append("explicit-refresh"))
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=10000)
    assert followups == ["explicit-refresh"]
    assert not window.cancellation.is_set()
