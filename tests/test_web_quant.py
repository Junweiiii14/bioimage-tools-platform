"""Real supervision edits must invalidate stale evidence and commit a new result."""

import csv
import json
from pathlib import Path
from typing import Any, cast
from zipfile import ZipFile

import numpy as np
import tifffile
from bioimage_app.figure_window import FigureProjectWindow
from bioimage_app.web_bridge import WorkbenchBridge
from pytestqt.qtbot import QtBot


def test_quant_supervision_recomputes_and_exports(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "originals" / "source.tif"
    source.parent.mkdir()
    pixels = np.full((180, 360), 50000, dtype=np.uint16)
    curve = 50000 - 35000 * np.exp(-(((np.arange(180) - 77) / 6) ** 2))
    for x in (100, 160, 220):
        pixels[:, x - 17 : x + 17] = curve[:, None].astype(np.uint16)
    tifffile.imwrite(source, pixels)
    before = source.read_bytes()
    host = FigureProjectWindow()
    bridge = WorkbenchBridge(host, lambda _: None)
    host.automatic.crop_policy = "lane_ratio@1"
    host.automatic.quant_policy = "wbquant_1_4_3@1"

    def settled() -> None:
        qtbot.waitUntil(lambda: not host.operation_busy, timeout=30000)

    def state() -> dict[str, Any]:
        return cast(dict[str, Any], bridge.snapshot()["quant"])

    try:
        host.start_project_from_images([source], project_parent=tmp_path / "projects")
        qtbot.waitUntil(
            lambda: bool(host.automatic.last_output_path) or "操作失败" in host.view.status.text(),
            timeout=45000,
        )
        assert host.automatic.last_output_path, host.view.status.text()
        settled()
        quant = state()
        assert len(quant["lanes"]) == 3
        assert all(lane["profile"] and lane["bands"][0]["signal"] > 0 for lane in quant["lanes"])
        assert not any(row.reviewed for row in host.view.project().rows)
        band = quant["lanes"][0]["bands"][0]
        payload = {
            "id": quant["rowId"],
            "sourceId": quant["sourceId"],
            "revision": quant["revision"],
            "lane": 1,
            "bandId": "target",
            "baselineStart": band["baselineStart"] + 1000,
        }
        bridge.request("quant_edit", json.dumps(payload))
        settled()
        changed = state()
        assert changed["lanes"][0]["bands"][0]["signal"] < band["signal"]
        assert changed["revision"] != quant["revision"]
        committed = host.view.project()
        bridge.request("quant_edit", json.dumps(payload))
        assert "改变" in str(bridge.snapshot()["status"])
        assert host.view.project() == committed
        lane = changed["lanes"][0]
        roi = dict(lane["roi"])
        roi["x"] += 1
        roi["width"] -= 2
        bridge.request(
            "quant_edit", json.dumps({**payload, "revision": changed["revision"], "roi": roi})
        )
        settled()
        assert state()["lanes"][0]["roi"] == roi
        assert state()["lanes"][0]["bands"][0]["signal"] is not None
        for ext in ("csv", "xlsx"):
            path = tmp_path / ("quant." + ext)
            host.export_project_table(str(path), quant=True)
            settled()
            assert path.is_file(), host.view.status.text()
        with (tmp_path / "quant.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
        assert rows[0][:3] == ["组序", "组名", "条带"]
        with ZipFile(tmp_path / "quant.xlsx") as book:
            assert "灰度分析" in book.read("xl/workbook.xml").decode("utf-8")
        assert source.read_bytes() == before
    finally:
        bridge.timer.stop()
        host.close()
        qtbot.waitUntil(lambda: host.resources_closed, timeout=20000)
