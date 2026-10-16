"""Real adapter lifecycle and rejection of stale graph edits."""

import json
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.figure_window import FigureProjectWindow
from bioimage_app.web_bridge import WorkbenchBridge
from pytestqt.qtbot import QtBot


@pytest.fixture
def bridge(qtbot: QtBot) -> Iterator[WorkbenchBridge]:
    host = FigureProjectWindow()
    adapter = WorkbenchBridge(host, lambda action: None)
    yield adapter
    adapter.timer.stop()
    host.close()
    qtbot.waitUntil(lambda: host.resources_closed, timeout=20000)


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
    assert host.view.source_preview is not None
    assert "data:image/png;base64," in json.dumps(state)
    assert source.read_bytes() == before
    initial = host.view.project().rows[0].roi
    payload = {
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

    (tmp_path / "index.html").write_text(
        '<html><script src="qrc:///qtwebchannel/qwebchannel.js"></script>'
        "<script>new QWebChannel(qt.webChannelTransport, function(c) {"
        "c.objects.workbench.stateChanged.connect(function(s) {"
        'document.title = JSON.parse(s).projectName || "ready";});'
        'c.objects.workbench.request("refresh", "{}");});</script></html>',
        encoding="utf-8",
    )
    window = WebWorkbenchWindow(asset_directory=tmp_path)
    window.show()
    try:
        qtbot.waitUntil(lambda: window.web.title() not in ("", "index.html"), timeout=15000)
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
        window.host.close()
        assert not window.host.isVisible() and not window.host.resources_closed
    finally:
        window.close()
        qtbot.waitUntil(lambda: window.host.resources_closed, timeout=20000)
