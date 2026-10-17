"""Actual asynchronous storage/run resolution, result revalidation and export cancellation."""

import json
from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

import pytest
from pytestqt.qtbot import QtBot
from wb_tool.api import WBAnalysisProject

from tests.test_project_measurements import configure_normalization, item, setup
from tests.test_project_measurements import windows as windows
from tools.wb.tests.test_project_archive import csv_rows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def test_real_saved_archive_and_csv_revalidate_current_result_files(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.view.numbers["font_size"].setValue(8)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    configure_normalization(window)
    qtbot.waitUntil(lambda: window.view.normalization.results.rowCount() == 3)
    output = tmp_path / "real.zip"
    window.compose(str(output))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=15000)
    assert output.exists(), window.view.status.text()
    project = window.view.project()
    assert isinstance(project, WBAnalysisProject)
    with ZipFile(output) as archive:
        index = json.loads(archive.read("archive.json"))
        assert index["revision"] == project.revision
        assert all(r["verification"] == "verified_result" for r in index["runs"])
        assert json.loads(archive.read("project.json")) == project.model_dump(mode="json")
        assert [r["积分"] for r in csv_rows(archive.read("tables/source.csv"))] == [
            "4000.0",
            "",
            "0.0",
            "8000.0",
            "16000.0",
            "0.0",
        ]
    # After a valid cache was shown, corrupt exactly one immutable test asset externally.
    run = project.analyses[0].run
    assert run and run.result
    (tmp_path / "workspace" / run.result.relative_path).write_bytes(b"bad")
    csv = tmp_path / "fresh.csv"
    window.export_project_table(str(csv))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=15000)
    assert csv.exists(), window.view.status.text()
    rows = csv_rows(csv.read_bytes())
    assert all(r["状态"] == "result_unavailable" and not r["积分"] for r in rows[:3])
    assert [r["积分"] for r in rows[3:]] == ["8000.0", "16000.0", "0.0"]
    partial = tmp_path / "partial.zip"
    window.compose(str(partial))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=15000)
    with ZipFile(partial) as archive:
        index = json.loads(archive.read("archive.json"))
        assert index["runs"][0]["verification"] == "unavailable"
        assert index["runs"][1]["verification"] == "verified_result"


@pytest.mark.parametrize("action", ["cancel", "edit", "close"])
def test_delayed_export_cannot_publish_after_cancel_edit_or_close(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    from wb_tool.adapters import figure_export

    window = windows()
    setup(qtbot, tmp_path, window)
    window.view.numbers["font_size"].setValue(8)
    original = figure_export.render_figure
    entered, release = Event(), Event()

    def delayed(*args: Any, **kwargs: Any):
        entered.set()
        if not release.wait(5):
            raise ValueError("test export release timed out")
        return original(*args, **kwargs)

    monkeypatch.setattr(figure_export, "render_figure", delayed)
    target = tmp_path / "late.zip"
    window.compose(str(target))
    try:
        qtbot.waitUntil(entered.is_set)
        if action == "cancel":
            window.cancel()
        elif action == "edit":
            item(window.view.table, 0, 2).setText("new label")
        else:
            window.close()
    finally:
        release.set()
    qtbot.waitUntil(
        (lambda: window.resources_closed) if action == "close" else window.import_button.isEnabled,
        timeout=15000,
    )
    assert not target.exists() and not list(tmp_path.glob(".wb-figure-*.tmp"))
    if action == "edit":
        assert window.view.project().rows[0].protein == "new label"
