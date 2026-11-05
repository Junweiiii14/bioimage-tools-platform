"""GUI controller boundaries using real background I/O and workflow initialization."""

import hashlib
import json
import sys
from pathlib import Path
from threading import Event
from typing import cast

import numpy as np
import pytest
from bioimage_app import nuclei_bridge
from bioimage_app.nuclei_bridge import NucleiBridge
from bioimage_app.nuclei_cli import prepare
from bioimage_app.nuclei_workflow_host import NucleiHost
from nuclei_tool.api import NucleiInput, read_nuclei_input
from PIL import Image
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog, QWidget
from pytestqt.qtbot import QtBot


def make_bridge(qtbot: QtBot, tmp_path: Path) -> tuple[NucleiBridge, list[dict[str, object]]]:
    window = QWidget()
    qtbot.addWidget(window)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    bridge = NucleiBridge(window, settings, lambda: False)
    states: list[dict[str, object]] = []

    def record(raw: str) -> None:
        states.append(cast(dict[str, object], json.loads(raw)))

    bridge.changed.connect(record)
    return bridge, states


def select_source(monkeypatch: pytest.MonkeyPatch, bridge: NucleiBridge, path: Path) -> None:
    def choose(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return str(path), "TIFF"

    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose)
    bridge.choose("source")


def test_unsupported_selection_preserves_previous_source(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge, states = make_bridge(qtbot, tmp_path)
    source, bad = tmp_path / "original.tif", tmp_path / "16bit.tif"
    Image.fromarray(np.zeros((8, 12), dtype=np.uint8)).save(source)
    Image.fromarray(np.zeros((8, 12), dtype=np.uint16)).save(bad)
    select_source(monkeypatch, bridge, source)
    qtbot.waitUntil(lambda: not bridge.busy)
    before = states[-1]
    select_source(monkeypatch, bridge, bad)
    qtbot.waitUntil(lambda: not bridge.busy)
    after = states[-1]
    assert after["state"] == "failed"
    assert after["count"] is None
    assert after["source"] == before["source"]
    assert after["source_sha256"] == before["source_sha256"]
    assert after["original"] == before["original"]
    bridge.close()


def test_missing_settings_and_model_are_failures_not_zero(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge, states = make_bridge(qtbot, tmp_path)
    source = tmp_path / "original.tif"
    Image.fromarray(np.zeros((8, 12), dtype=np.uint8)).save(source)
    select_source(monkeypatch, bridge, source)
    qtbot.waitUntil(lambda: not bridge.busy)
    bridge.run()
    assert states[-1]["count"] is None
    assert "运行设置" in str(states[-1]["message"])
    bridge.settings.setValue("nuclei_worker_v1", sys.executable)
    bridge.settings.setValue("nuclei_model_v1", str(tmp_path / "missing"))
    bridge.run()
    qtbot.waitUntil(lambda: not bridge.busy, timeout=10000)
    assert states[-1]["state"] == "failed"
    assert states[-1]["count"] is None
    assert not Path(str(states[-1]["workspace"])).exists()
    bridge.close()


def test_close_waits_for_source_reader_and_rejects_late_preview(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge, states = make_bridge(qtbot, tmp_path)
    source = tmp_path / "original.tif"
    Image.fromarray(np.zeros((8, 12), dtype=np.uint8)).save(source)
    entered, release = Event(), Event()

    def delayed(path: str) -> NucleiInput:
        entered.set()
        assert release.wait(5)
        return read_nuclei_input(path)

    monkeypatch.setattr(nuclei_bridge, "read_nuclei_input", delayed)
    select_source(monkeypatch, bridge, source)
    try:
        qtbot.waitUntil(entered.is_set)
        bridge.choose("source")  # Re-entrant selection must not start a second read.
        bridge.close()
        assert not bridge.resources_closed
    finally:
        release.set()
    qtbot.waitUntil(lambda: bridge.resources_closed)
    assert all(not state["source"] and not state["original"] for state in states)


def test_changed_source_rejected_before_workspace_creation(tmp_path: Path) -> None:
    source = tmp_path / "original.tif"
    Image.fromarray(np.zeros((8, 12), dtype=np.uint8)).save(source)
    previous = hashlib.sha256(source.read_bytes()).hexdigest()
    Image.fromarray(np.ones((8, 12), dtype=np.uint8)).save(source)
    workspace = tmp_path / "new-workspace"
    with pytest.raises(ValueError, match="原图已改变"):
        prepare(
            workspace,
            str(source),
            NucleiHost(sys.executable, str(tmp_path)),
            expected_sha256=previous,
        )
    assert not workspace.exists()
