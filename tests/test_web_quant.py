"""Real supervision edits must invalidate stale evidence and commit a new result."""

import csv
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from zipfile import ZipFile

import numpy as np
import tifffile
from bioimage_app.figure_window import FigureProjectWindow
from bioimage_app.web_bridge import WorkbenchBridge
from bioimage_app.web_quant import quant_snapshot
from pytestqt.qtbot import QtBot
from wb_tool.api import WBAnalysisProject, initial_composition, make_row_analysis


def test_same_target_bridge_keeps_generation_and_manual_parameters(qtbot: QtBot) -> None:
    from wb_tool.api import Baseline, update_quant_lane

    from tools.wb.tests.test_anchored_analysis import anchored_project

    project = anchored_project()
    annotation = project.analyses[0].request.lanes[0]
    assert annotation.target_roi is not None
    target = annotation.target_roi
    project = update_quant_lane(project, "r", annotation.roi.lane_id, baseline=Baseline(1, 1))
    view = SimpleNamespace(
        project=lambda: project, selected_row=lambda: project.rows[0], generation=9
    )

    # No setters/replan methods: any attempted mutation or recompute fails this control.
    class NoErrorBridge(WorkbenchBridge):
        def publish(self) -> None:
            assert not self._error

    def ignore_connection(callback: object) -> None:
        pass

    host = cast(
        FigureProjectWindow,
        SimpleNamespace(
            view=view,
            project_results=[],
            operation_busy=False,
            is_closing=False,
            automatic=SimpleNamespace(finished=SimpleNamespace(connect=ignore_connection)),
        ),
    )
    bridge = NoErrorBridge(host, lambda _: None)
    bridge.timer.stop()
    bridge.request(
        "quant_edit",
        json.dumps(
            {
                "id": "r",
                "sourceId": project.rows[0].source.sha256 if project.rows[0].source else "",
                "revision": 9,
                "lane": 1,
                "roi": {
                    "x": target.x0,
                    "y": target.y0,
                    "width": target.width,
                    "height": target.y1 - target.y0,
                },
            }
        ),
    )
    assert view.generation == 9
    assert view.project() is project


def test_anchored_snapshot_keeps_target_distinct_from_sampling_context() -> None:
    from tool_contracts.api import AssetRef
    from wb_tool.api import FigureRow, FigureTemplate, LaneROI, ProjectRowAnalysis

    from tools.wb.tests.test_anchored_analysis import anchored_request

    image, request = anchored_request()
    crop = LaneROI("r", 0, 38, 4, 62)
    row = FigureRow(
        row_id="r",
        figure="Fig1",
        protein="target",
        lane_count=1,
        source=AssetRef(
            asset_id="source", relative_path="inputs/source.tif", sha256=image.sha256, size_bytes=1
        ),
        filename="source.tif",
        width=4,
        height=120,
        bit_depth=16,
        roi=crop,
        reviewed=True,
    )
    project = WBAnalysisProject(
        project_id="p",
        rows=(row,),
        figure_order=("Fig1",),
        template=FigureTemplate(crop_height=24),
        analyses=(ProjectRowAnalysis(row_id="r", crop=crop, request=request),),
    )
    # A presentation unit test needs no filesystem or live native host.
    host = cast(
        FigureProjectWindow,
        SimpleNamespace(
            view=SimpleNamespace(project=lambda: project, selected_row=lambda: row, generation=0),
            project_results=[],
            operation_busy=False,
        ),
    )
    data = cast(dict[str, Any], quant_snapshot(host))
    lane = data["lanes"][0]
    assert lane["targetRoi"] == {"x": 0, "y": 38, "width": 4, "height": 24}
    assert lane["roi"]["y"] < 38
    assert lane["contextExpansionPercent"] > 0
    assert data["contextBounds"] == lane["roi"]


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
        # A Fig is the unit of quantitative supervision; duplicated row geometry
        # is acceptable, but results must retain separate protein row identities.
        project = host.view.project()
        assert isinstance(project, WBAnalysisProject)
        original = project.rows[0]
        assert original.roi is not None
        second = original.model_copy(
            update={
                "row_id": "second-protein",
                "protein": "Control",
                "reviewed": True,
                "roi": replace(original.roi, lane_id="second-protein"),
            }
        )
        draft = project.model_copy(update={"rows": (*project.rows, second)})
        duplicate = make_row_analysis(draft, second.row_id, "dark")
        source_request = project.analyses[0].request
        duplicate = duplicate.model_copy(
            update={
                "request": replace(
                    source_request,
                    lanes=tuple(
                        replace(lane, roi=replace(lane.roi, lane_id=f"{second.row_id}:{i:02d}"))
                        for i, lane in enumerate(source_request.lanes, 1)
                    ),
                )
            }
        )
        grouped = project.model_copy(
            update={"rows": (*project.rows, second), "analyses": (*project.analyses, duplicate)}
        )
        grouped = grouped.model_copy(update={"composition": initial_composition(grouped)})
        host.view.set_project(grouped)
        host.view.generation += 1
        bridge.request("quant_group", json.dumps({"figure": original.figure}))
        settled()
        group = state()["group"]
        assert group["compatible"] and len(group["rows"]) == 2
        assert all(len(r["lanes"]) == 3 for r in group["rows"])
        assert len(state()["table"]) == 2
        assert all(v["signal"] is not None for r in state()["table"] for v in r["values"])
        committed_group = host.view.project()
        bridge.request("quant_group", json.dumps({"figure": "stale-figure"}))
        assert host.view.project() == committed_group
        incompatible = second.model_copy(update={"lane_count": 2})
        host.view.set_project(committed_group.model_copy(update={"rows": (original, incompatible)}))
        assert not state()["group"]["compatible"]
        bridge.request("quant_group", json.dumps({"figure": original.figure}))
        assert "泳道数一致" in str(bridge.snapshot()["status"])
        host.view.set_project(committed_group)
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
        # An overview request queues its montage until source loading releases the host.
        host.view.set_project(host.view.project())
        bridge.request("quant_select", json.dumps({"id": original.row_id, "overview": True}))
        qtbot.waitUntil(lambda: bool(bridge.snapshot()["montage"]), timeout=30000)
        settled()
        assert source.read_bytes() == before
    finally:
        bridge.timer.stop()
        host.close()
        qtbot.waitUntil(lambda: host.resources_closed, timeout=20000)
