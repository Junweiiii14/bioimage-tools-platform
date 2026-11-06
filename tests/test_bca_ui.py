"""Cancellation and invalid records never become valid zero or saved results."""

import json
from pathlib import Path
from typing import Any

import pytest
from bioimage_app.bca_bridge import BcaBridge
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QFileDialog, QWidget
from pytestqt.qtbot import QtBot

EXAMPLES = Path(__file__).parents[1] / "tools/bca/examples"


def test_cancel_and_missing_facts_preserve_no_result(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = QWidget()
    qtbot.addWidget(window)
    bridge = BcaBridge(window, lambda: False)
    states: list[dict[str, Any]] = []

    def record(raw: str) -> None:
        states.append(json.loads(raw))

    bridge.changed.connect(record)

    def directory(*_args: object) -> str:
        return str(tmp_path)

    def choose(*_args: object) -> tuple[str, str]:
        return str(EXAMPLES / "synthetic.csv"), ""

    monkeypatch.setattr(QStandardPaths, "writableLocation", directory)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose)
    bridge.choose("source")
    qtbot.waitUntil(lambda: not bridge.busy)
    metadata = json.loads((EXAMPLES / "record.json").read_text())
    metadata["cooled_to_room_temperature"] = False
    bridge.run(json.dumps(metadata))
    assert states[-1]["state"] == "failed" and states[-1]["result"] is None
    assert not (tmp_path / "BioImage").exists()
    metadata["cooled_to_room_temperature"] = True
    bridge.run(json.dumps(metadata))
    session = bridge.findChild(WorkflowSession)
    assert session is not None
    pids: list[int] = []

    def cancel_on_start(status: WorkflowStatus) -> None:
        if status.pid is not None and not pids:
            pids.append(status.pid)
            bridge.cancel()

    session.changed.connect(cancel_on_start)
    qtbot.waitUntil(lambda: not bridge.busy, timeout=15000)
    assert pids and states[-1]["state"] == "cancelled"
    assert states[-1]["result"] is None
    bridge.close()


def test_run_reports_another_tool_busy(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch) -> None:
    window = QWidget()
    qtbot.addWidget(window)
    unavailable = False
    bridge = BcaBridge(window, lambda: unavailable)
    states: list[dict[str, Any]] = []

    def record(raw: str) -> None:
        states.append(json.loads(raw))

    def choose(*_args: object) -> tuple[str, str]:
        return str(EXAMPLES / "synthetic.csv"), ""

    bridge.changed.connect(record)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose)
    bridge.choose("source")
    qtbot.waitUntil(lambda: not bridge.busy)
    unavailable = True
    bridge.run("{}")
    state = states[-1]
    assert state["state"] == "failed"
    assert "请等待当前任务完成" in state["message"]
    assert state["result"] is None and not bridge.busy
    bridge.close()
