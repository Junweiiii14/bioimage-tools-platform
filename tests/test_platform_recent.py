"""Native drop routing and bounded saved recent-project previews."""

from datetime import datetime
from pathlib import Path
from threading import Event

import pytest
from bioimage_app.platform_window import PlatformWindow
from bioimage_app.project_start import ProjectSelectionJob
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QMimeData, QPointF, QSettings, Qt, QUrl
from PySide6.QtGui import QDropEvent, QIcon, QImage, QPixmap
from PySide6.QtWidgets import QListWidgetItem
from pytestqt.qtbot import QtBot


def test_native_drop_routes_local_files_without_directory_work(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    window = PlatformWindow(
        settings=QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(window)
    received: list[list[Path]] = []
    monkeypatch.setattr(window, "start_from_images", received.append)
    mime = QMimeData()
    source = tmp_path / "original.tif"
    mime.setUrls([QUrl.fromLocalFile(str(source))])
    event = QDropEvent(
        QPointF(20, 20),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.dropEvent(event)
    assert event.isAccepted()
    assert received == [[source]]
    mime.setUrls([QUrl("https://example.com/image.tif")])
    rejected = QDropEvent(
        QPointF(20, 20),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.dropEvent(rejected)
    assert not rejected.isAccepted() and received == [[source]]


def test_recent_cached_name_and_bounded_thumbnail(qtbot: QtBot, tmp_path: Path) -> None:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    path = str(tmp_path / "saved-project")
    settings.setValue("recent_workspaces", [path])
    settings.setValue(f"recent_name/{path}", "实验 · 2026-10-16")
    settings.setValue(f"recent_summary/{path}", "上次查看：10 张来源")
    image = QImage(72, 48, QImage.Format.Format_Grayscale8)
    image.fill(128)
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert QPixmap.fromImage(image).save(buffer, "PNG")
    settings.setValue(f"recent_thumbnail/{path}", data)
    window = PlatformWindow(settings=settings)
    qtbot.addWidget(window)
    item = window.recent_list.item(0)
    assert item is not None and not item.icon().isNull()
    assert "实验 · 2026-10-16" in item.text() and "上次查看：10 张来源" in item.text()
    assert "完成" not in item.text()
    settings.setValue(f"recent_thumbnail/{path}", QByteArray(b"x" * 65537))
    reopened = PlatformWindow(settings=settings)
    qtbot.addWidget(reopened)
    assert reopened.recent_list.item(0).icon().isNull()


def test_project_display_name_includes_source_and_date(tmp_path: Path) -> None:
    folder = tmp_path / "实验原图"
    folder.mkdir()
    (folder / "source.tif").touch()
    job = ProjectSelectionJob([folder], tmp_path / "projects", Event())
    job.run()
    assert not job.result.error
    assert job.result.name == f"实验原图 · {datetime.now():%Y-%m-%d}"
    assert job.result.destination is not None and not job.result.destination.exists()


@pytest.mark.parametrize("dpr", [1.5, 2.0])
def test_high_dpi_thumbnail_survives_close_and_reopen(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dpr: float
) -> None:
    settings = QSettings(str(tmp_path / "high-dpi.ini"), QSettings.Format.IniFormat)
    hub = PlatformWindow(settings=settings)
    qtbot.addWidget(hub)
    workspace = tmp_path / "project"
    hub.open_workspace(str(workspace), create=True)
    tool = hub.active_tool
    assert tool is not None
    try:
        qtbot.waitUntil(tool.import_button.isEnabled, timeout=10000)
        physical = QPixmap(round(96 * dpr), round(64 * dpr))
        physical.fill(Qt.GlobalColor.gray)
        physical.setDevicePixelRatio(dpr)
        tool.view.source_list.addItem(QListWidgetItem(QIcon(physical), "actual source thumbnail"))

        # A native high-DPI QIcon return is simulated independently of the test monitor's DPI.
        def high_dpi_pixmap(*_args: object, **_kwargs: object) -> QPixmap:
            return QPixmap(physical)

        monkeypatch.setattr(QIcon, "pixmap", high_dpi_pixmap)
        hub.return_button.click()
        qtbot.waitUntil(lambda: hub.active_tool is None, timeout=15000)
    finally:
        hub.close()
        qtbot.waitUntil(lambda: hub.active_tool is None, timeout=15000)
    data = settings.value(f"recent_thumbnail/{workspace}")
    assert isinstance(data, QByteArray)
    decoded = QImage.fromData(data)
    assert not decoded.isNull()
    assert decoded.width() <= 96 and decoded.height() <= 64
    reopened = PlatformWindow(settings=settings)
    qtbot.addWidget(reopened)
    assert not reopened.recent_list.item(0).icon().isNull()
