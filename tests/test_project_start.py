"""New-project interaction: original selection owns no storage-directory decisions."""

from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.platform_window import PlatformWindow
from bioimage_app.project_entry import collect_source_images
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot

from tooling.qt_test_lifecycle import close_and_dispose_window


@pytest.fixture
def entry_hub(qtbot: QtBot, tmp_path: Path) -> Iterator[PlatformWindow]:
    settings = QSettings(str(tmp_path / "entry.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "managed-projects"))
    window = PlatformWindow(settings=settings)
    window.show()
    yield window
    close_and_dispose_window(
        window, qtbot, resources_closed=lambda: window.active_tool is None, timeout=20000
    )


def source_image(path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    pixels = np.full((180, 360), 50000, dtype=np.uint16)
    for x in (60, 120, 180, 240, 300):
        pixels[70:85, x - 17 : x + 17] = 15000
    tifffile.imwrite(path, pixels)
    return path.read_bytes()


def test_select_original_creates_independent_project_and_outputs(
    qtbot: QtBot, tmp_path: Path, entry_hub: PlatformWindow
) -> None:
    source = tmp_path / "实验原图" / "sample.tif"
    original = source_image(source)
    entry_hub.start_from_images([source])
    tool = entry_hub.active_tool
    assert tool is not None
    qtbot.waitUntil(
        lambda: bool(tool.automatic.last_output_path) or "操作失败" in tool.view.status.text(),
        timeout=45000,
    )
    assert tool.automatic.last_output_path, tool.view.status.text()
    qtbot.waitUntil(lambda: not tool.operation_busy, timeout=15000)
    project_path = Path(tool.workspace_path)
    assert project_path.parent == tmp_path / "managed-projects"
    assert (project_path / "workspace.json").is_file()
    assert source.read_bytes() == original
    assert list(source.parent.iterdir()) == [source]
    assert entry_hub.recent_list.count() == 1
    output = Path(tool.automatic.last_output_path)
    assert (output / "measurements.xlsx").is_file()
    assert (output / "figure.png").is_file()
    assert (output / "status.json").is_file()
    row = tool.view.project().rows[0]
    assert row.filename == source.name
    # Portable explicit unknown label; source identity must not masquerade as protein.
    assert row.protein == "Unassigned"


def test_invalid_tiff_creates_no_workspace_or_history(
    qtbot: QtBot, tmp_path: Path, entry_hub: PlatformWindow
) -> None:
    source = tmp_path / "broken.tif"
    source.write_bytes(b"not a TIFF")
    entry_hub.start_from_images([source])
    tool = entry_hub.active_tool
    assert tool is not None
    qtbot.waitUntil(lambda: not tool.operation_busy, timeout=15000)
    assert not list((tmp_path / "managed-projects").glob("*/workspace.json"))
    assert not tool.workspace_path
    assert entry_hub.recent_list.count() == 0
    assert not tool.automatic.last_output_path
    assert "TIFF" in tool.view.status.text() or "原图" in tool.view.status.text()
    assert source.read_bytes() == b"not a TIFF"


def test_project_parent_inside_source_directory_is_actionable_failure(
    qtbot: QtBot, tmp_path: Path, entry_hub: PlatformWindow
) -> None:
    source_dir = tmp_path / "原图"
    source = source_dir / "sample.tif"
    original = source_image(source)
    entry_hub.settings.setValue("project_parent", str(source_dir / "projects"))
    entry_hub.start_from_images([source_dir])
    tool = entry_hub.active_tool
    assert tool is not None
    qtbot.waitUntil(lambda: not tool.operation_busy, timeout=15000)
    assert not tool.workspace_path
    assert entry_hub.recent_list.count() == 0
    assert "保存" in tool.view.status.text() and "原图" in tool.view.status.text()
    assert list(source_dir.iterdir()) == [source]
    assert source.read_bytes() == original


def test_cancel_during_scan_creates_no_project(
    qtbot: QtBot, tmp_path: Path, entry_hub: PlatformWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    from threading import Event

    import bioimage_app.project_start as start_module

    entered = Event()
    released = Event()
    original_scan = collect_source_images

    def gated_scan(paths: list[Path], cancellation: Event) -> tuple[Path, ...]:
        entered.set()
        if not released.wait(timeout=10):
            raise ValueError("Test scan gate was not released")
        return original_scan(paths, cancellation)

    source = tmp_path / "originals" / "sample.tif"
    original = source_image(source)
    monkeypatch.setattr(start_module, "collect_source_images", gated_scan)
    try:
        entry_hub.start_from_images([source])
        tool = entry_hub.active_tool
        assert tool is not None
        qtbot.waitUntil(entered.is_set, timeout=5000)
        tool.cancel()
    finally:
        released.set()
    qtbot.waitUntil(lambda: not tool.operation_busy, timeout=15000)
    assert not tool.workspace_path
    assert not list((tmp_path / "managed-projects").glob("*/workspace.json"))
    assert entry_hub.recent_list.count() == 0
    assert not tool.automatic.last_output_path
    assert source.read_bytes() == original
