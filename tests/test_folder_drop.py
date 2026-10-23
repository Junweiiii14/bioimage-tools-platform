"""Native Explorer-style URL events reach the current WebEngine entry and real intake."""

import json
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.folder_drop import folder_paths
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QMimeData, QPoint, QPointF, QSettings, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot
from wb_tool.api import WBIntakeProject

from tests.test_intake_web_ui import javascript
from tooling.qt_test_lifecycle import close_and_dispose_window


@pytest.fixture
def drop_window(qtbot: QtBot, tmp_path: Path) -> Iterator[WebWorkbenchWindow]:
    settings = QSettings(str(tmp_path / "drop.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    window = WebWorkbenchWindow(settings=settings)
    window.show()
    try:
        qtbot.waitUntil(
            lambda: (
                javascript(
                    window, qtbot, "!!window.folderDrop&&typeof bridge!=='undefined'&&!!bridge"
                )
                is True
            )
        )
        javascript(window, qtbot, "platformHome.show('platform');true")
        yield window
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )


def native_drop(window: WebWorkbenchWindow, qtbot: QtBot, urls: list[QUrl]) -> None:
    raw = javascript(
        window,
        qtbot,
        "JSON.stringify((()=>{const r=document.querySelector('[data-folder-drop]')"
        ".getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})())",
    )
    assert isinstance(raw, str)
    x, y = json.loads(raw)
    point = QPoint(round(x * window.web.zoomFactor()), round(y * window.web.zoomFactor()))
    mime = QMimeData()
    mime.setUrls(urls)
    enter = QDragEnterEvent(
        point,
        Qt.DropAction.CopyAction | Qt.DropAction.MoveAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    receiver = window.web.focusProxy() or window.web
    QApplication.sendEvent(receiver, enter)
    assert enter.isAccepted() and enter.dropAction() == Qt.DropAction.CopyAction
    drop = QDropEvent(
        QPointF(point),
        Qt.DropAction.CopyAction | Qt.DropAction.MoveAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(receiver, drop)
    assert drop.isAccepted() and drop.dropAction() == Qt.DropAction.CopyAction


@pytest.mark.parametrize("zoom", (1.0, 1.5))
def test_native_multi_folder_drop_creates_real_intake(
    drop_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path, zoom: float
) -> None:
    window = drop_window
    window.web.setZoomFactor(zoom)
    roots = [tmp_path / "原图 一", tmp_path / "原图 二"]
    for root in roots:
        root.mkdir()
        tifffile.imwrite(root / "0001.tiff", np.full((32, 64), 3000, dtype=np.uint16))
    native_drop(window, qtbot, [QUrl.fromLocalFile(str(p)) for p in roots])

    def ready() -> bool:
        project = window.host.view.project()
        return (
            isinstance(project, WBIntakeProject)
            and len(project.intake.sources) == 2
            and not window.host.operation_busy
        )

    qtbot.waitUntil(ready, timeout=30000)
    project = window.host.view.project()
    assert isinstance(project, WBIntakeProject)
    assert len(project.intake.sources) == 2
    assert not project.intake.proteins and not project.rows
    assert all(p.exists() for p in roots)
    assert window.host.workspace_path


@pytest.mark.parametrize("kind", ("file", "missing", "empty", "remote"))
def test_invalid_batch_is_rejected_without_project(
    drop_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path, kind: str
) -> None:
    window = drop_window
    valid = tmp_path / "valid"
    valid.mkdir()
    tifffile.imwrite(valid / "original.tif", np.ones((32, 64), dtype=np.uint16))
    bad = tmp_path / "bad"
    if kind == "file":
        bad.write_text("ordinary file", encoding="utf-8")
    if kind == "empty":
        # An empty directory alone must not allocate a project.
        bad.mkdir()
        urls = [QUrl.fromLocalFile(str(bad))]
    else:
        urls = [
            QUrl.fromLocalFile(str(valid)),
            QUrl("https://example.invalid/") if kind == "remote" else QUrl.fromLocalFile(str(bad)),
        ]
    native_drop(window, qtbot, urls)
    qtbot.waitUntil(
        lambda: (
            not window.host.operation_busy
            and (
                window.shutdown_stage == "entry_error"
                if kind != "remote"
                else javascript(
                    window,
                    qtbot,
                    "document.querySelector('#folder-drop-status').textContent.includes('仅支持')",
                )
                is True
            )
        ),
        timeout=20000,
    )
    assert not window.host.workspace_path
    assert not window.navigation.recent()
    assert list(valid.glob("*.tif"))
    if kind != "remote":
        assert ("无效目录" if kind != "empty" else "未找到") in window.host.view.status.text()


def test_url_validation_rejects_remote_and_relative_paths() -> None:
    for urls in (
        (),
        (QUrl("https://example.invalid"),),
        (QUrl("file://server/share/folder"),),
        (QUrl.fromLocalFile("relative"),),
    ):
        with pytest.raises(ValueError):
            folder_paths(urls)


def test_busy_drop_reports_reason_without_starting_import(
    drop_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = drop_window
    window.host.begin_operation()
    try:
        native_drop(window, qtbot, [QUrl.fromLocalFile(str(tmp_path))])
        qtbot.waitUntil(
            lambda: (
                javascript(
                    window,
                    qtbot,
                    "document.querySelector('#folder-drop-status').textContent.includes('当前任务')",
                )
                is True
            )
        )
        assert not window.host.workspace_path and not window.host.intake.scanning
    finally:
        window.host.finish_operation("busy drop test finished")


def test_drop_reuses_existing_project_draft_protection(
    drop_window: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = drop_window
    root = tmp_path / "originals"
    root.mkdir()
    tifffile.imwrite(root / "one.tif", np.ones((32, 64), dtype=np.uint16))
    native_drop(window, qtbot, [QUrl.fromLocalFile(str(root))])
    qtbot.waitUntil(
        lambda: window.shutdown_stage == "idle" and bool(window.host.workspace_path), timeout=20000
    )
    qtbot.waitUntil(lambda: not window.host.operation_busy and not window.host.has_unsaved_changes)
    old_path = window.host.workspace_path
    qtbot.waitUntil(
        lambda: (
            javascript(
                window,
                qtbot,
                "!!document.querySelector('[data-group-action=add-fig]')&&!state.busy",
            )
            is True
        )
    )
    javascript(window, qtbot, "document.querySelector('[data-group-action=add-fig]').click();true")
    window.bridge.session(
        "position", json.dumps({"projectId": window.host.view.project_identity, "draft": True})
    )
    javascript(window, qtbot, "platformHome.show('platform');true")
    native_drop(window, qtbot, [QUrl.fromLocalFile(str(root))])
    qtbot.waitUntil(lambda: window.shutdown_stage == "confirm_draft")
    assert window.host.workspace_path == old_path
    window.bridge.session("reply", '{"choice":"return"}')
    assert window.host.workspace_path == old_path
