"""Real adapter lifecycle and rejection of stale graph edits."""

import gc
import json
from collections.abc import Iterator
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import tifffile
from bioimage_app.figure_window import FigureProjectWindow
from bioimage_app.web_bridge import WorkbenchBridge
from pytestqt.qtbot import QtBot
from wb_tool.api import FigureRow, FolderDiscoveryReport, ProjectTableCell, WBFigureProject

from tooling.qt_test_lifecycle import close_and_dispose_window


def crop_identity(bridge: WorkbenchBridge) -> dict[str, object]:
    snapshot = bridge.snapshot()
    selected = bridge.host.view.selected_row()
    assert selected is not None and selected.source is not None
    return {
        key: snapshot[key] for key in ("cropEditContract", "projectId", "sessionEpoch", "revision")
    } | {"id": selected.row_id, "sourceId": selected.source.sha256}


def test_idle_publish_and_progress_do_not_rebuild_project_snapshot(
    bridge: WorkbenchBridge, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge.publish()
    calls: list[str] = []
    progress: list[str] = []
    original = bridge.snapshot

    def snapshot() -> dict[str, object]:
        calls.append("snapshot")
        return original()

    monkeypatch.setattr(bridge, "snapshot", snapshot)
    bridge.progressChanged.connect(progress.append)
    for index in range(8):
        bridge.host.view.status.setText(f"正在计算 {index}")
        bridge.host.quant_progress = {"phase": "measure", "finished": index, "total": 10}
        bridge.publish()
    assert calls == []
    assert len(progress) == 8
    bridge.host.view.generation += 1
    bridge.publish()
    assert calls == ["snapshot"]


def test_shared_result_transport_keeps_order_failures_zero_and_row_summaries(
    bridge: WorkbenchBridge,
) -> None:
    project = WBFigureProject(
        project_id="shared-cell-projection",
        rows=(FigureRow(row_id="a", figure="Fig1"), FigureRow(row_id="b", figure="Fig1")),
        figure_order=("Fig1",),
    )
    bridge.host.view.set_project(project)
    zero = ProjectTableCell("b", "Fig1", "B", 1, "", "b1", "", None, "", 0, "valid", "")
    failed = replace(zero, row_id="a", value=None, status="failed", reason="failed evidence")
    missing = replace(failed, lane_index=2, status="missing_source", reason="missing evidence")
    orphan = replace(failed, row_id="historical-orphan", reason="retained flat-table evidence")
    cells = (zero, failed, missing, orphan)
    bridge.host.view.analysis.result_view.show_cells(cells)
    snapshot = bridge.snapshot()
    assert snapshot["snapshotContract"] == "wb-workbench-snapshot@1"
    assert snapshot["cells"] == [
        {
            "rowId": c.row_id,
            "fig": c.figure,
            "protein": c.protein,
            "lane": c.lane_index,
            "value": c.value,
            "rawIntegral": c.raw_integral,
            "status": c.status,
            "reason": c.reason,
        }
        for c in cells
    ]
    rows = cast(list[dict[str, object]], snapshot["rows"])
    assert [row["id"] for row in rows] == ["a", "b"]
    assert all("results" not in row for row in rows)
    assert rows[0]["reason"] == "failed evidence；missing evidence"
    assert rows[1]["status"] == "valid"
    assert bridge.host.view.analysis.result_view.cells == cells


def test_folder_report_is_visible_and_only_current_variant_can_be_added(
    bridge: WorkbenchBridge, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = (
        FolderDiscoveryReport.model_validate(
            {
                "paths": ["input/original.tif"],
                "skipped": [
                    {"path": "input/other (2).tif", "reason": "numbered_acquisition_variant"},
                    {"path": "input/display.tif", "reason": "generated_display_or_crop"},
                ],
            }
        )
        .model_dump_json()
        .encode()
    )
    bridge.host.automatic.discovery_report = report
    calls: list[tuple[tuple[str, ...], bool]] = []

    def capture(paths: tuple[str, ...], *, automatic: bool = False) -> None:
        calls.append((paths, automatic))

    monkeypatch.setattr(bridge.host, "import_images", capture)
    identity = sha256(report).hexdigest()
    snapshot = bridge.snapshot()["sourceDiscovery"]
    assert isinstance(snapshot, dict) and snapshot["id"] == identity
    bridge.host.automatic.include_discovered_source(0, identity)
    assert calls == [(("input/other (2).tif",), True)]
    current_identity = sha256(bridge.host.automatic.discovery_report).hexdigest()
    assert current_identity != identity
    for index, token in [
        (1, current_identity),
        (0, "old-report"),
        (True, current_identity),
        (99, current_identity),
    ]:
        with pytest.raises(ValueError):
            bridge.host.automatic.include_discovered_source(index, token)
    assert len(calls) == 1


def test_folder_report_cannot_cross_project_or_workspace(
    bridge: WorkbenchBridge, monkeypatch: pytest.MonkeyPatch
) -> None:
    workflow = bridge.host.automatic
    workflow.discovery_report = (
        FolderDiscoveryReport.model_validate(
            {
                "paths": ["A/source.tif"],
                "skipped": [{"path": "A/source (2).tif", "reason": "numbered_acquisition_variant"}],
            }
        )
        .model_dump_json()
        .encode()
    )
    identity = sha256(workflow.discovery_report).hexdigest()
    first = bridge.host.view.project()
    bridge.host.view.set_project(first.model_copy(update={"project_id": "another-project"}))
    assert workflow.discovery_report == b""
    assert bridge.snapshot()["sourceDiscovery"] is None
    with pytest.raises(ValueError, match="筛选记录已改变"):
        workflow.include_discovered_source(0, identity)
    bridge.host.view.set_project(first)
    assert workflow.discovery_report
    monkeypatch.setattr(bridge.host, "_workspace", "different-workspace")
    assert workflow.discovery_report == b""
    assert bridge.snapshot()["sourceDiscovery"] is None


@pytest.fixture
def bridge(qtbot: QtBot) -> Iterator[WorkbenchBridge]:
    host = FigureProjectWindow()
    adapter = WorkbenchBridge(host, lambda action: None)
    yield adapter
    adapter.timer.stop()
    close_and_dispose_window(
        host, qtbot, resources_closed=lambda: host.resources_closed, timeout=20000
    )


def test_web_adapter_real_import_output_and_original_coordinates(
    qtbot: QtBot, tmp_path: Path, bridge: WorkbenchBridge
) -> None:
    source = tmp_path / "originals" / "original.tif"
    source.parent.mkdir()
    image = np.full((180, 360), 50000, dtype=np.uint16)
    for x in (60, 120, 180, 240, 300):
        image[70:85, x - 17 : x + 17] = 15000
    tifffile.imwrite(source, image)
    before = source.read_bytes()
    host = bridge.host
    host.start_project_from_images([source], project_parent=tmp_path / "projects")
    qtbot.waitUntil(
        lambda: bool(host.automatic.last_output_path) or "操作失败" in host.view.status.text(),
        timeout=45000,
    )
    assert host.automatic.last_output_path, host.view.status.text()
    qtbot.waitUntil(lambda: not host.operation_busy, timeout=20000)
    row = host.view.project().rows[0]
    bridge.request("select", json.dumps({"id": row.row_id}))
    qtbot.waitUntil(lambda: not host.operation_busy, timeout=15000)
    state = bridge.snapshot()
    assert state["outputPath"]
    assert state["selectedId"] == row.row_id
    assert '"bitDepth": 16' in json.dumps(state)
    assert host.view.source_preview is not None
    assert "data:image/png;base64," in json.dumps(state)
    assert source.read_bytes() == before
    initial = host.view.project().rows[0].roi
    payload = {
        **crop_identity(bridge),
        "id": row.row_id,
        "sourceId": "stale",
        "roi": {"x": 20, "y": 60, "width": 300, "height": 40},
    }
    bridge.request("crop", json.dumps(payload))
    assert host.view.project().rows[0].roi == initial
    assert "身份" in str(bridge.snapshot()["status"])
    payload["sourceId"] = row.source.sha256 if row.source else ""
    bridge.request("crop", json.dumps(payload))
    changed = host.view.project().rows[0].roi
    assert changed is not None and (changed.x0, changed.y0, changed.x1, changed.y1) == (
        20,
        60,
        320,
        100,
    )
    assert not host.view.project().rows[0].reviewed
    bridge.request("undo", "{}")
    assert host.view.project().rows[0].roi == initial
    assert source.read_bytes() == before


def test_web_adapter_rejects_unknown_busy_and_oversize(bridge: WorkbenchBridge) -> None:
    bridge.request("anything", "{}")
    assert bridge.snapshot()["status"] == "未知操作"
    bridge.request("refresh", "x" * 4097)
    assert bridge.snapshot()["status"] == "操作参数过长"
    bridge.host.begin_operation()
    bridge.request("compose", "{}")
    assert "处理中" in str(bridge.snapshot()["status"])
    bridge.host.finish_operation("结束")


def test_local_page_channel_and_drain(qtbot: QtBot, tmp_path: Path) -> None:
    from bioimage_app.web_window import WebWorkbenchWindow
    from PySide6.QtCore import QUrl
    from PySide6.QtWebEngineCore import QWebEnginePage
    from pytestqt.exceptions import TimeoutError as QtTimeoutError

    (tmp_path / "index.html").write_text(
        "<html><script>window.channelPhase='before-qrc';"
        "window.addEventListener('error',e=>window.channelError=e.message||'resource-error');"
        '</script><script src="qrc:///qtwebchannel/qwebchannel.js"></script>'
        "<script>window.channelPhase='initializing';"
        "new QWebChannel(qt.webChannelTransport, function(c) {"
        "window.channelPhase='connected';"
        "c.objects.workbench.stateChanged.connect(function(s) {"
        "window.channelPhase='received';"
        'document.title = JSON.parse(s).projectName || "ready";});'
        'c.objects.workbench.request("refresh", "{}");});</script></html>',
        encoding="utf-8",
    )
    window = WebWorkbenchWindow(asset_directory=tmp_path)
    loads: list[bool] = []
    renderer_exits: list[tuple[str, int]] = []

    def renderer_stopped(status: QWebEnginePage.RenderProcessTerminationStatus, code: int) -> None:
        renderer_exits.append((str(status), code))

    window.web.loadFinished.connect(loads.append)
    window.web.page().renderProcessTerminated.connect(renderer_stopped)
    window.show()
    try:
        try:
            qtbot.waitUntil(lambda: window.web.title() not in ("", "index.html"), timeout=15000)
        except QtTimeoutError as error:
            observed: list[object] = []
            window.web.page().runJavaScript(
                "JSON.stringify({ready:document.readyState,phase:window.channelPhase,"
                "error:window.channelError,qt:typeof qt,channel:typeof QWebChannel})",
                observed.append,
            )
            qtbot.wait(250)  # Failure-only capture; the original pass deadline is unchanged.
            error.add_note(
                json.dumps(
                    {"loadFinished": loads, "rendererExits": renderer_exits, "dom": observed},
                    ensure_ascii=False,
                )
            )
            raise
        assert window.web.title() == window.host.view.project().name
        page = window.web.page()
        assert not page.acceptNavigationRequest(
            QUrl("https://example.com"),
            QWebEnginePage.NavigationType.NavigationTypeLinkClicked,
            True,
        )
        assert not page.acceptNavigationRequest(
            QUrl.fromLocalFile(str(tmp_path / "secret.txt")),
            QWebEnginePage.NavigationType.NavigationTypeLinkClicked,
            True,
        )
        window.bridge.request("advanced", '{"section":"metadata"}')
        assert window.host.isVisible()
        window.host.hide()
        window.bridge.request("advanced", '{"section":"analysis"}')
        assert not window.host.isVisible()
        assert "灰度定量页" in str(window.bridge.snapshot()["status"])
        window.host.close()
        assert not window.host.isVisible() and not window.host.resources_closed
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )
        qtbot.wait(20)
        gc.collect()


def test_existing_web_project_appends_files_and_folder(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bioimage_app.web_window import WebWorkbenchWindow
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QFileDialog

    assets = tmp_path / "web"
    assets.mkdir()
    (assets / "index.html").write_text("<html>WB</html>", encoding="utf-8")
    originals = tmp_path / "originals"
    originals.mkdir()
    extra_folder = originals / "next"
    extra_folder.mkdir()
    sources = [originals / "first.tif", originals / "second.tif", extra_folder / "third.tif"]
    for number, source in enumerate(sources):
        image = np.full((180, 360), 50000 + number * 100, dtype=np.uint16)
        for x in (60, 120, 180, 240, 300):
            image[70:85, x - 17 : x + 17] = 15000
        tifffile.imwrite(source, image)
    originals_before = [source.read_bytes() for source in sources]
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    window = WebWorkbenchWindow(asset_directory=assets, settings=settings)
    try:
        window.start_from_images([sources[0]])
        qtbot.waitUntil(lambda: bool(window.host.automatic.last_output_path), timeout=45000)
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=15000)
        project_id = window.host.view.project().project_id
        workspace = window.host.workspace_path
        previous_output = window.host.automatic.last_output_path

        def selected_files(*args: object) -> tuple[list[str], str]:
            return [str(sources[1])], ""

        monkeypatch.setattr(QFileDialog, "getOpenFileNames", selected_files)
        window.choose("import")
        qtbot.waitUntil(lambda: len(window.host.view.project().rows) == 2, timeout=15000)
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=45000)
        assert window.host.automatic.last_output_path != previous_output
        previous_output = window.host.automatic.last_output_path

        def selected_folder(*args: object) -> str:
            return str(extra_folder)

        monkeypatch.setattr(QFileDialog, "getExistingDirectory", selected_folder)
        window.choose("import_folder")
        qtbot.waitUntil(lambda: len(window.host.view.project().rows) == 3, timeout=15000)
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=45000)
        assert window.host.automatic.last_output_path != previous_output
        assert window.host.workspace_path == workspace
        assert window.host.view.project().project_id == project_id
        assert len(list((tmp_path / "projects").glob("*/workspace.json"))) == 1
        assert [source.read_bytes() for source in sources] == originals_before
        rows = window.host.view.project().rows
        window.bridge.request("select", json.dumps({"id": rows[0].row_id}))
        qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=15000)
        for index in (0, 1):
            window.bridge.request(
                "confirm", json.dumps({**crop_identity(window.bridge), "id": rows[index].row_id})
            )
            qtbot.waitUntil(lambda: not window.host.operation_busy, timeout=15000)
            assert window.host.view.project().rows[index].reviewed
            selected = window.host.view.selected_row()
            assert selected is not None and selected.row_id == rows[index + 1].row_id

    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )
        qtbot.wait(20)
        gc.collect()


def test_web_close_reopen_restores_saved_project(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bioimage_app.web_window import WebWorkbenchWindow
    from PySide6.QtCore import QSettings

    assets = tmp_path / "web"
    assets.mkdir()
    (assets / "index.html").write_text("<html>WB</html>", encoding="utf-8")
    originals = tmp_path / "originals"
    originals.mkdir()
    source = originals / "source.tif"
    image = np.full((180, 360), 50000, dtype=np.uint16)
    for x in (60, 120, 180, 240, 300):
        image[70:85, x - 17 : x + 17] = 15000
    tifffile.imwrite(source, image)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    first = WebWorkbenchWindow(asset_directory=assets, settings=settings)
    try:
        first.start_from_images([source])
        qtbot.waitUntil(lambda: bool(first.host.automatic.last_output_path), timeout=45000)
        qtbot.waitUntil(lambda: not first.host.operation_busy, timeout=15000)
        workspace = first.host.workspace_path
        original_project = first.host.view.project()
    finally:
        close_and_dispose_window(
            first, qtbot, resources_closed=lambda: first.host.resources_closed, timeout=20000
        )
        qtbot.wait(20)
        gc.collect()
    reopened = WebWorkbenchWindow(asset_directory=assets, settings=settings)
    try:
        reopened.open_project(workspace)
        qtbot.waitUntil(lambda: bool(reopened.host.view.project().rows), timeout=20000)
        qtbot.waitUntil(lambda: not reopened.host.operation_busy, timeout=20000)
        restored = reopened.host.view.project()
        assert restored.project_id == original_project.project_id
        assert restored.rows == original_project.rows
        assert reopened.host.view.analysis.result_view.cells
        assert reopened.host.view.source_preview is not None
        # Same-window opening is supported now. Cancelling its chooser keeps this project.
        from PySide6.QtWidgets import QFileDialog

        def cancel_directory(*args: object) -> str:
            return ""

        monkeypatch.setattr(QFileDialog, "getExistingDirectory", cancel_directory)
        reopened.bridge.request("open_project", "{}")
        assert reopened.host.workspace_path == workspace
        assert reopened.host.view.project().project_id == original_project.project_id
    finally:
        close_and_dispose_window(
            reopened, qtbot, resources_closed=lambda: reopened.host.resources_closed, timeout=20000
        )
        qtbot.wait(20)
        gc.collect()


def test_ratio_crop_no_confirmation_montage_and_lane_resize(
    qtbot: QtBot, tmp_path: Path, bridge: WorkbenchBridge
) -> None:
    host = bridge.host
    host.automatic.crop_policy = "lane_ratio@1"
    source = tmp_path / "originals" / "ratio-original.tif"
    source.parent.mkdir()
    image = np.full((180, 360), 50000, dtype=np.uint16)
    for x in (100, 160, 220):
        image[70:85, x - 17 : x + 17] = 15000
    tifffile.imwrite(source, image)
    before = source.read_bytes()
    host.start_project_from_images([source], project_parent=tmp_path / "projects")
    qtbot.waitUntil(
        lambda: bool(host.automatic.last_output_path) or "操作失败" in host.view.status.text(),
        timeout=45000,
    )
    assert host.automatic.last_output_path, host.view.status.text()
    qtbot.waitUntil(lambda: not host.operation_busy, timeout=20000)
    row = host.view.project().rows[0]
    assert row.roi is not None and row.lane_count == 3
    assert abs(row.roi.width - 1.25 * row.lane_count * (row.roi.y1 - row.roi.y0)) <= 0.5
    assert not row.reviewed
    snapshot = bridge.snapshot()
    assert snapshot["autoCompletedKey"]
    assert snapshot["montage"] and snapshot["montageRegions"]
    assert snapshot["montageWidth"] and snapshot["montageHeight"]
    bridge.request("select", json.dumps({"id": row.row_id}))
    qtbot.waitUntil(lambda: not host.operation_busy, timeout=15000)
    assert row.source is not None
    bridge.request(
        "set_lanes",
        json.dumps(
            {**crop_identity(bridge), "id": row.row_id, "sourceId": row.source.sha256, "n": 4}
        ),
    )
    changed = host.view.project().rows[0]
    assert changed.roi is not None and changed.lane_count == 4
    assert changed.roi.y1 - changed.roi.y0 == row.roi.y1 - row.roi.y0
    assert abs(changed.roi.width - 1.25 * 4 * (row.roi.y1 - row.roi.y0)) <= 0.5
    assert not changed.reviewed
    bridge.request("undo", "{}")
    restored = host.view.project().rows[0]
    assert restored.roi == row.roi and restored.lane_count == 3
    assert source.read_bytes() == before


def test_stage_publication_is_immediate_and_detaches_replaced_host(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    published: list[FigureProjectWindow] = []

    def publish(self: WorkbenchBridge) -> None:
        published.append(self.host)

    monkeypatch.setattr(WorkbenchBridge, "publish", publish)
    first, second = FigureProjectWindow(), FigureProjectWindow()
    adapter = WorkbenchBridge(first, lambda action: None)
    adapter.timer.stop()
    try:
        first.intake_stage_committed.emit()
        assert published == [first]
        adapter.replace_host(second)
        adapter.timer.stop()
        first.intake_stage_committed.emit()
        assert published == [first]
        second.intake_stage_committed.emit()
        assert published == [first, second]
    finally:
        adapter.timer.stop()
        for host in (first, second):
            close_and_dispose_window(
                host, qtbot, resources_closed=lambda host=host: host.resources_closed, timeout=20000
            )
