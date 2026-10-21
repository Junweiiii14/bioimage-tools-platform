"""Late OCR callbacks and guarded persistence retain the previous association."""

from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
import tifffile
from PIL import Image, ImageDraw, ImageFont
from platform_runtime.api import Workspace
from pytestqt.qtbot import QtBot
from tool_contracts.api import DraftSnapshot, RunRecord
from wb_tool.api import (
    LoadedProjectOCR,
    WBFigureProject,
    WBProjectOCR,
    install_project_recognition,
    prepare_workbench_revision,
    read_figure_project,
    read_project_ocr_result,
)

from tests.test_project_measurements import windows as windows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def ocr_project(window: "FigureProjectWindow") -> WBProjectOCR:
    project = window.view.project()
    assert isinstance(project, WBProjectOCR)
    return project


def recognized_project(window: "FigureProjectWindow", qtbot: QtBot, root: Path) -> WBProjectOCR:
    source = root / "labels.tif"
    with Image.new("L", (600, 400), 245) as figure:
        draw = ImageDraw.Draw(figure)
        draw.text((30, 20), "Fig 1A", font=ImageFont.load_default(size=42), fill=0)
        draw.text((30, 150), "AKT", font=ImageFont.load_default(size=42), fill=0)
        tifffile.imwrite(source, np.array(figure))
    window.open_workspace(str(root / "workspace"), create=True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    window.import_ocr_image(str(source))
    qtbot.waitUntil(window.import_button.isEnabled, timeout=10000)
    window.recognize_project()
    qtbot.waitUntil(window.import_button.isEnabled, timeout=30000)
    project = window.view.project()
    assert isinstance(project, WBProjectOCR) and project.ocr and project.ocr.run
    assert project.ocr.run.state == "succeeded" and project.ocr.rows
    return project


@pytest.mark.parametrize("phase", ["decode", "install"])
@pytest.mark.parametrize("action", ["cancel", "close", "edit"])
def test_late_committed_ocr_never_replaces_cancelled_or_edited_association(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
    action: str,
) -> None:
    window = windows()
    old = recognized_project(window, qtbot, tmp_path)
    source_before = (tmp_path / "labels.tif").read_bytes()
    entered, release = Event(), Event()
    committed: list[RunRecord] = []

    def hold(run: RunRecord) -> None:
        committed.append(run)
        entered.set()
        if not release.wait(10):
            raise ValueError("OCR regression did not release its held background phase")

    def decode(project: WBProjectOCR, run: RunRecord, data: bytes) -> LoadedProjectOCR:
        loaded = read_project_ocr_result(project, run, data)
        hold(run)
        return loaded

    def install(project: WBProjectOCR, loaded: LoadedProjectOCR) -> WBProjectOCR:
        candidate = install_project_recognition(project, loaded)
        hold(loaded.run)
        return candidate

    monkeypatch.setattr(
        "wb_tool.ui.background."
        + ("read_project_ocr_result" if phase == "decode" else "install_project_recognition"),
        decode if phase == "decode" else install,
    )
    window.recognize_project()
    try:
        qtbot.waitUntil(entered.is_set, timeout=30000)
        assert len(committed) == 1 and committed[0].state == "succeeded"
        if action == "close":
            window.close()
        elif action == "cancel":
            window.cancel()
        else:
            window.view.name.setText("newer OCR edit")
            window.view.name.textEdited.emit("newer OCR edit")
    finally:
        release.set()
    if action == "close":
        qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    else:
        qtbot.waitUntil(lambda: not window.operation_busy, timeout=20000)
    current = window.view.project()
    assert isinstance(current, WBProjectOCR) and current.ocr == old.ocr
    if action == "edit":
        assert current.name == "newer OCR edit"
    assert (tmp_path / "labels.tif").read_bytes() == source_before
    if action != "close":
        window.close()
        qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    with Workspace.open(tmp_path / "workspace") as store:
        assert store.get_run(committed[0].run_id) == committed[0]
        assert committed[0].pid and committed[0].pid > 0
        saved = read_figure_project(store.read_asset(store.load_draft(old.project_id).asset))
        assert isinstance(saved, WBProjectOCR) and saved.ocr == old.ocr


@pytest.mark.parametrize("phase", ["encode", "cas_before", "cas_after"])
@pytest.mark.parametrize("action", ["cancel", "close"])
def test_ocr_candidate_save_cancel_preserves_current_and_committed_history(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
    action: str,
) -> None:
    window = windows()
    old = recognized_project(window, qtbot, tmp_path)
    entered, release = Event(), Event()
    snapshots: list[DraftSnapshot] = []
    old_dump = WBProjectOCR.model_dump_json
    old_save = Workspace.save_draft

    def is_candidate(project: WBFigureProject) -> bool:
        return isinstance(project, WBProjectOCR) and project.ocr != old.ocr

    def pause() -> None:
        entered.set()
        if not release.wait(10):
            raise ValueError("OCR persistence regression did not release its held phase")

    def encoded(project: WBProjectOCR, *args: Any, **kwargs: Any) -> str:
        data = old_dump(project, *args, **kwargs)
        if phase == "encode" and is_candidate(project):
            pause()
        return data

    def saved(
        store: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None,
    ) -> DraftSnapshot:
        candidate = is_candidate(read_figure_project(data))
        if candidate and phase == "cas_before":
            pause()
        snapshot = old_save(
            store,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )
        if candidate:
            snapshots.append(snapshot)
            if phase == "cas_after":
                pause()
        return snapshot

    monkeypatch.setattr(WBProjectOCR, "model_dump_json", encoded)
    monkeypatch.setattr(Workspace, "save_draft", saved)
    window.recognize_project()
    try:
        qtbot.waitUntil(entered.is_set, timeout=30000)
        # Candidate encoding/CAS must never install association before success.
        assert isinstance(window.view.project(), WBProjectOCR)
        assert ocr_project(window).ocr == old.ocr
        if action == "close":
            window.close()
        else:
            window.cancel()
    finally:
        release.set()
    if action == "close":
        qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    else:
        qtbot.waitUntil(lambda: not window.operation_busy, timeout=20000)
        assert window.has_unsaved_changes == (phase != "encode")
    assert ocr_project(window).ocr == old.ocr
    if action != "close":
        window.close()
        qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    with Workspace.open(tmp_path / "workspace") as store:
        latest = read_figure_project(store.read_asset(store.load_draft(old.project_id).asset))
        assert isinstance(latest, WBProjectOCR) and latest.ocr == old.ocr
        if phase == "encode":
            assert snapshots == []
        else:
            # Once CAS is queued, cancellation does not erase committed history.
            assert len(snapshots) == 1
            historical = read_figure_project(store.read_asset(snapshots[0].asset))
            assert isinstance(historical, WBProjectOCR) and historical.ocr != old.ocr
            assert historical.ocr and historical.ocr.run
            assert store.get_run(historical.ocr.run.run_id) == historical.ocr.run


def test_ocr_association_save_failure_preserves_old_and_allows_explicit_retry(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = windows()
    old = recognized_project(window, qtbot, tmp_path)
    old_text = window.view.ocr.raw.toPlainText()
    old_save = Workspace.save_draft
    rejected: list[WBProjectOCR] = []
    receipts: list[str] = []

    def fail_candidate(
        store: Workspace,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None,
    ) -> DraftSnapshot:
        candidate = read_figure_project(data)
        if isinstance(candidate, WBProjectOCR) and candidate.ocr != old.ocr:
            rejected.append(candidate)
            raise OSError("OCR association save failure")
        return old_save(
            store,
            document_id,
            tool_id,
            revision,
            data,
            expected_previous_revision=expected_previous_revision,
        )

    monkeypatch.setattr(Workspace, "save_draft", fail_candidate)
    window.recognize_project(after=lambda: receipts.append("saved"))
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=30000)
    assert len(rejected) == 1
    assert receipts == []
    assert "OCR association save failure" in window.view.status.text()
    assert ocr_project(window).ocr == old.ocr and window.view.ocr.raw.toPlainText() == old_text
    monkeypatch.undo()
    window.recognize_project(after=lambda: receipts.append("saved"))
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=30000)
    assert receipts == ["saved"]
    final = window.view.project()
    assert isinstance(final, WBProjectOCR) and final.ocr and final.ocr.run
    assert final.ocr != old.ocr
    assert "AKT" in window.view.ocr.raw.toPlainText()
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)
    with Workspace.open(tmp_path / "workspace") as store:
        failed_candidate = rejected[0]
        assert failed_candidate.ocr and failed_candidate.ocr.run
        assert store.get_run(failed_candidate.ocr.run.run_id) == failed_candidate.ocr.run
        saved = read_figure_project(store.read_asset(store.load_draft(old.project_id).asset))
        assert isinstance(saved, WBProjectOCR) and saved.ocr == final.ocr


@pytest.mark.parametrize("reject_call", [1, 2])
def test_ocr_revision_guard_failure_ends_operation(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    reject_call: int,
) -> None:
    """The preflight and Qt completion paths both retain the prior association."""
    window = windows()
    old = recognized_project(window, qtbot, tmp_path)
    calls = 0
    receipts: list[str] = []

    def guarded(project: WBFigureProject, *, expected_digest: str) -> WBFigureProject:
        nonlocal calls
        calls += 1
        if calls == reject_call:
            raise ValueError("grouping revision must be confirmed before OCR")
        return prepare_workbench_revision(project, expected_digest=expected_digest)

    monkeypatch.setattr("bioimage_app.figure_window.prepare_workbench_revision", guarded)
    window.recognize_project(after=lambda: receipts.append("saved"))
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=30000)
    assert calls == reject_call
    assert receipts == []
    assert "grouping revision must be confirmed" in window.operation_error
    assert ocr_project(window).ocr == old.ocr
