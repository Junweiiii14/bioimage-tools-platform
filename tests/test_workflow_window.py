"""Visible controls use actual workers, immutable storage and asynchronous shutdown."""

import csv
import io
from pathlib import Path

import pytest
from bioimage_app.desktop_entry import create_desktop_window, desktop_mode
from bioimage_app.workflow_input import prepare_wb_workspace
from bioimage_app.workflow_window import WorkflowWindow
from platform_runtime.api import Workspace, load_workflow_ledger
from PySide6.QtCore import Qt, QThread
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot
from tool_contracts.api import ExecutionPlan


@pytest.mark.parametrize("mode", ["complete", "pause_reopen", "pause_adjust", "cancel_close"])
def test_visible_workflow_controls_run_and_recover(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    entry = create_desktop_window(desktop_mode(["--workflow-ui"]))
    assert isinstance(entry, WorkflowWindow)
    window: WorkflowWindow = entry
    qtbot.addWidget(window)
    workspace = tmp_path / "workspace"
    window.location.setText(str(workspace))
    window.mode.setCurrentIndex(1)
    threads: list[QThread] = []
    original = prepare_wb_workspace

    def prepare(path: Path, **kwargs: str) -> ExecutionPlan:
        threads.append(QThread.currentThread())
        return original(path, **kwargs)

    monkeypatch.setattr("bioimage_app.workflow_window.prepare_wb_workspace", prepare)
    window.show()
    windows = [window]
    try:
        QTest.mouseClick(window.start_button, Qt.MouseButton.LeftButton)
        assert not window.start_button.isEnabled()
        execution_id = window.execution.text()
        assert execution_id
        if mode == "cancel_close":
            window.close()
            qtbot.waitUntil(lambda: not window.isVisible(), timeout=30000)
        elif mode in ("pause_reopen", "pause_adjust"):
            qtbot.waitUntil(window.pause_button.isEnabled, timeout=30000)
            QTest.mouseClick(window.pause_button, Qt.MouseButton.LeftButton)
            qtbot.waitUntil(lambda: "已暂停" in window.summary.text(), timeout=30000)
            if mode == "pause_adjust":
                window.report_layout.setCurrentIndex(1)
                QTest.mouseClick(window.apply_button, Qt.MouseButton.LeftButton)
                qtbot.waitUntil(lambda: window.execution.text() != execution_id, timeout=30000)
                execution_id = window.execution.text()
            else:
                window.close()
                qtbot.waitUntil(lambda: not window.isVisible(), timeout=30000)
                reopened = WorkflowWindow()
                qtbot.addWidget(reopened)
                windows.append(reopened)
                reopened.location.setText(str(workspace))
                reopened.execution.setText(execution_id)
                reopened.show()
                QTest.mouseClick(reopened.open_button, Qt.MouseButton.LeftButton)
                qtbot.waitUntil(reopened.resume_button.isEnabled, timeout=30000)
                QTest.mouseClick(reopened.resume_button, Qt.MouseButton.LeftButton)
                window = reopened
        if mode != "cancel_close":
            qtbot.waitUntil(window.start_button.isEnabled, timeout=30000)
            assert "已提交全部成果" in window.summary.text(), window.summary.text()
            assert window.progress.value() == 3
            assert window.steps.topLevelItemCount() == 3
            assert window.outputs.topLevelItemCount() == 4
        assert threads and all(thread != window.thread() for thread in threads)
        with Workspace.open(workspace) as store:
            ledger = load_workflow_ledger(
                store.read_asset(store.load_draft(execution_id).asset).decode()
            )
            if mode == "cancel_close":
                assert ledger.state == "cancelled" and not store.list_runs()
            else:
                assert ledger.state == "succeeded" and len(store.list_runs()) == 3
                table = next(
                    item.asset for item in ledger.results[-1].outputs if item.port == "measurements"
                )
                rows = list(
                    csv.DictReader(io.StringIO(store.read_asset(table).decode("utf-8-sig")))
                )
                assert rows[0]["value"] == "4000.0"
        if mode == "complete":
            window.report_layout.setCurrentIndex(1)
            QTest.mouseClick(window.apply_button, Qt.MouseButton.LeftButton)
            rerun_id = window.execution.text()
            assert rerun_id != execution_id
            qtbot.waitUntil(window.start_button.isEnabled, timeout=30000)
            assert "复用 2 步" in window.summary.text(), window.summary.text()
            with Workspace.open(workspace) as store:
                rerun = load_workflow_ledger(
                    store.read_asset(store.load_draft(rerun_id).asset).decode()
                )
                original_ledger = load_workflow_ledger(
                    store.read_asset(store.load_draft(execution_id).asset).decode()
                )
                assert rerun.state == "succeeded" and len(store.list_runs()) == 4
                assert original_ledger == ledger
                assert rerun.plan.revision == ledger.plan.revision + 1
    finally:
        for widget in windows:
            widget.close()
            qtbot.waitUntil(lambda w=widget: not w.isVisible(), timeout=30000)


def test_visible_input_failure_does_not_overwrite_workspace(qtbot: QtBot, tmp_path: Path) -> None:
    workspace = tmp_path / "existing"
    with Workspace.create(workspace):
        pass
    window = WorkflowWindow()
    qtbot.addWidget(window)
    window.location.setText(str(workspace))
    window.mode.setCurrentIndex(1)
    window.show()
    QTest.mouseClick(window.start_button, Qt.MouseButton.LeftButton)
    try:
        qtbot.waitUntil(window.start_button.isEnabled, timeout=30000)
        assert "已提交全部成果" not in window.summary.text()
        assert "Error" in window.summary.text()
        with Workspace.open(workspace) as store:
            assert not store.list_runs() and not store.list_documents()
    finally:
        window.close()
        qtbot.waitUntil(lambda: not window.isVisible(), timeout=30000)
