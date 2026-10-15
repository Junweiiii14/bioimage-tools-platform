"""Portable templates cross workspaces without importing an experiment or stale callbacks."""

import os
from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING

import pytest
from PIL import ImageFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget
from pytestqt.qtbot import QtBot
from wb_tool.api import LoadedFigureTemplate, WBLayoutProject, read_figure_template

from tests.test_project_measurements import item, setup
from tests.test_project_measurements import windows as windows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def test_template_cross_workspace_font_reopen_and_previous_project_saved(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    first = windows()
    setup(qtbot, tmp_path, first, crop_height=30)
    first.view.rebuild_layout()
    first.view.laboratory_layout.heading.setValue(31)
    first.view.numbers["label_width"].setValue(185)
    font = ImageFont.load_default(size=12)
    assert isinstance(font, ImageFont.FreeTypeFont)
    font_path = tmp_path / "labels.ttf"
    font_path.write_bytes(font.font_bytes)
    first.import_font(str(font_path))
    qtbot.waitUntil(first.import_button.isEnabled)
    source_project = first.view.project()
    target = tmp_path / "lab.wbtemplate"
    first.export_template(str(target))
    qtbot.waitUntil(first.import_button.isEnabled)
    assert target.exists(), first.view.status.text()
    portable = read_figure_template(str(target))
    assert portable.spec.template.font is None and portable.font_data == font.font_bytes

    second_root = tmp_path / "second"
    second_root.mkdir()
    second = windows()
    setup(qtbot, second_root, second)
    previous = second.view.project()
    second.import_template(str(target))
    qtbot.waitUntil(second.import_button.isEnabled, timeout=15000)
    fresh = second.view.project()
    assert isinstance(fresh, WBLayoutProject), second.view.status.text()
    assert fresh.project_id != previous.project_id
    assert fresh.rows == fresh.figure_order == fresh.analyses == fresh.composition.slices == ()
    assert fresh.ocr is None and fresh.normalizations == fresh.archive_sources == ()
    assert fresh.template.label_width == 185 and fresh.layout_style.heading_size == 31
    assert fresh.template.font is not None and source_project.template.font is not None
    assert fresh.template.font.sha256 == source_project.template.font.sha256
    assert second.documents.findData(previous.project_id) >= 0
    capture = os.environ.get("BIOIMAGE_TEMPLATE_CAPTURE")
    if capture:
        tabs = second.view.findChild(QTabWidget)
        assert tabs is not None
        tabs.setCurrentIndex(2)
        # Locate by the action's containing scroll area, not by a fragile tab index.
        for index in range(tabs.count()):
            if tabs.tabText(index) == "模板与排序":
                tabs.setCurrentIndex(index)
        assert second.grab().save(capture)
    # Render from the destination asset after the original font file has gone away.
    font_path.unlink()
    source = str(second_root / "original0.tiff")
    second.import_images((source,))
    qtbot.waitUntil(second.import_button.isEnabled)
    second.view.numbers["font_size"].setValue(8)
    for col, text in {2: "AKT", 3: "3", 4: "0", 5: "5", 6: "30", 7: "15"}.items():
        item(second.view.table, 0, col).setText(text)
    item(second.view.table, 0, 9).setCheckState(Qt.CheckState.Checked)
    second.view.rebuild_layout()
    output = second_root / "render.png"
    second.export_figure_image(str(output))
    qtbot.waitUntil(second.import_button.isEnabled, timeout=15000)
    assert output.exists(), second.view.status.text()
    project = second.view.project()
    second.close()
    qtbot.waitUntil(lambda: second.resources_closed, timeout=15000)
    reopened = windows()
    reopened.open_workspace(str(second_root / "workspace"))
    qtbot.waitUntil(reopened.import_button.isEnabled)
    reopened.load_document(project.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=15000)
    assert reopened.view.project() == project
    reopened.load_document(previous.project_id)
    qtbot.waitUntil(reopened.import_button.isEnabled, timeout=15000)
    assert reopened.view.project().rows == previous.rows


@pytest.mark.parametrize("action", ["cancel", "edit", "close"])
def test_late_template_read_keeps_current_project(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    from wb_tool.adapters import figure_template_io

    window = windows()
    setup(qtbot, tmp_path, window)
    target = tmp_path / "template.wbtemplate"
    window.export_template(str(target))
    qtbot.waitUntil(window.import_button.isEnabled)
    before = window.view.project()
    entered, release = Event(), Event()
    original = figure_template_io.read_figure_template

    def delayed(
        source: str, *, cancelled: Callable[[], bool] = lambda: False
    ) -> LoadedFigureTemplate:
        result = original(source, cancelled=cancelled)
        entered.set()
        if not release.wait(10):
            raise ValueError("test reader release timed out")
        return result

    monkeypatch.setattr(figure_template_io, "read_figure_template", delayed)
    window.import_template(str(target))
    try:
        qtbot.waitUntil(entered.is_set)
        if action == "close":
            window.close()
        elif action == "cancel":
            window.cancel()
        else:
            window.view.name.setText("new edit")
            window.view.name.textEdited.emit("new edit")
    finally:
        release.set()
    if action == "close":
        qtbot.waitUntil(lambda: window.resources_closed, timeout=15000)
    else:
        qtbot.waitUntil(window.import_button.isEnabled)
    current = window.view.project()
    assert current.project_id == before.project_id and current.rows == before.rows
    if action == "edit":
        assert current.name == "new edit"


def test_template_read_error_keeps_current_project(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    before = window.view.project()
    invalid = tmp_path / "bad.wbtemplate"
    invalid.write_bytes(b"not a template")
    window.import_template(str(invalid))
    qtbot.waitUntil(window.import_button.isEnabled)
    assert "失败" in window.view.status.text()
    assert window.view.project() == before
    # No extra toolbar controls: template file actions live with the template settings.
    tabs = window.view.findChild(QTabWidget)
    assert tabs is not None
    assert window.view.template_export_button.text() == "保存模板文件…"


@pytest.mark.parametrize("action", ["cancel", "edit", "close"])
def test_template_import_after_save_still_checks_current_generation(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    target = tmp_path / "template.wbtemplate"
    window.export_template(str(target))
    qtbot.waitUntil(window.import_button.isEnabled)
    before = window.view.project()
    original_save = window.save

    def save_then_steer(after: Callable[[], None] | None = None) -> None:
        def saved() -> None:
            if action == "close":
                window.close()
            elif action == "cancel":
                window.cancel()
            else:
                window.view.name.setText("new edit after save")
                window.view.name.textEdited.emit("new edit after save")
            if after is not None:
                after()

        original_save(after=saved)

    monkeypatch.setattr(window, "save", save_then_steer)
    window.import_template(str(target))
    if action == "close":
        qtbot.waitUntil(lambda: window.resources_closed, timeout=15000)
    else:
        qtbot.waitUntil(window.import_button.isEnabled)
    assert window.view.project().project_id == before.project_id
    assert window.view.project().rows == before.rows
    if action == "edit":
        assert window.view.project().name == "new edit after save"
