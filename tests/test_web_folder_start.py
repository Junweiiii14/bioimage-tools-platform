"""The homepage folder route must use the same original discovery as an open project."""

import json
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import tifffile
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot
from wb_tool.api import CropRequest, FolderDiscoveryReport, LaneROI, export_crop, load_tiff


def test_first_folder_import_filters_before_creating_project_and_records_choices(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "originals"
    directory.mkdir()
    sources: list[Path] = []
    for i, name in enumerate(
        (
            "ProteinA_100646_0_14_0_0 (1).tiff",
            "ProteinA_100646_0_14_0_0 (2).tiff",
            "ProteinB_100646_0_14_0_0 (1).tiff",
        )
    ):
        pixels = np.full((180, 360), 50000 + i, dtype=np.uint16)
        for x in (60, 120, 180, 240, 300):
            pixels[70:85, x - 17 : x + 17] = 15000 + i
        path = directory / name
        tifffile.imwrite(path, pixels)
        sources.append(path)
    image = load_tiff(sources[0])
    export_crop(
        str(sources[0]),
        CropRequest(image.sha256, 0, LaneROI("raw", 20, 60, 340, 100)),
        str(directory / "old-crop.tiff"),
    )
    before = {path: path.read_bytes() for path in directory.iterdir()}
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    window = WebWorkbenchWindow(settings=settings)

    def choose(*args: object) -> str:
        return str(directory)

    monkeypatch.setattr(QFileDialog, "getExistingDirectory", choose)

    def js(code: str) -> object:
        received: list[object] = []

        def completed(value: object) -> None:
            received.append(value)

        window.web.page().runJavaScript(code, completed)
        qtbot.waitUntil(lambda: bool(received), timeout=10000)
        return received[0]

    try:
        window.show()
        qtbot.waitUntil(
            lambda: js("Boolean(typeof bridge !== 'undefined' && bridge)") is True, timeout=15000
        )
        assert js("document.querySelector('[data-action=import_folder]').click(); true") is True
        qtbot.waitUntil(
            lambda: (
                bool(window.host.automatic.last_output_path)
                or (not window.host.operation_busy and "失败" in window.host.view.status.text())
            ),
            timeout=45000,
        )
        assert window.host.automatic.last_output_path, window.host.view.status.text()
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=15000)
        assert [row.filename for row in window.host.view.project().rows] == [
            sources[0].name,
            sources[2].name,
        ]
        report = FolderDiscoveryReport.model_validate_json(window.host.automatic.discovery_report)
        assert report.paths == (str(sources[0]), str(sources[2]))
        assert {item.reason for item in report.skipped} == {
            "numbered_acquisition_variant",
            "generated_display_or_crop",
        }
        snapshot = window.bridge.snapshot()["sourceDiscovery"]
        assert isinstance(snapshot, dict)
        assert len(cast(list[object], snapshot["skipped"])) == 2
        output = Path(window.host.automatic.last_output_path)
        exported = json.loads((output / "status.json").read_bytes())
        assert exported["source_discovery"]["paths"] == list(report.paths)
        assert all(path.read_bytes() == data for path, data in before.items())
        assert set(directory.iterdir()) == set(before)
    finally:
        window.close()
        qtbot.waitUntil(lambda: window.host.resources_closed, timeout=20000)
