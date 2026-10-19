"""Exercise delayed saves and native feedback, rather than only immediate widget edits."""

from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.figure_window import FigureProjectWindow
from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot
from wb_tool.api import WBAnalysisProject


@pytest.fixture
def prepared(qtbot: QtBot, tmp_path: Path) -> Iterator[FigureProjectWindow]:
    source = tmp_path / "source" / "bands.tif"
    source.parent.mkdir()
    pixels = np.full((180, 360), 50000, dtype=np.uint16)
    for x in (60, 120, 180, 240, 300):
        pixels[70:85, x - 17 : x + 17] = 15000
    tifffile.imwrite(source, pixels)
    window = FigureProjectWindow()
    window.show()
    window.start_project_from_images([source], tmp_path / "projects")
    qtbot.waitUntil(lambda: bool(window.automatic.last_output_path), timeout=40000)
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=15000)
    yield window
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)


def test_delayed_save_keeps_source_and_recomputes_graphical_crop(
    qtbot: QtBot, prepared: FigureProjectWindow
) -> None:
    view = prepared.view
    original = view.selected_row()
    assert original is not None and original.roi is not None
    project = view.project()
    assert isinstance(project, WBAnalysisProject) and project.analyses[0].run is not None
    old_run = project.analyses[0].run.run_id
    QTest.keyClick(view.canvas, Qt.Key.Key_Right)

    def recomputed() -> bool:
        project = view.project()
        return bool(
            isinstance(project, WBAnalysisProject)
            and project.analyses[0].run
            and project.analyses[0].run.run_id != old_run
            and not prepared.operation_busy
        )

    qtbot.waitUntil(recomputed, timeout=30000)
    selected = view.selected_row()
    assert selected is not None and selected.row_id == original.row_id and selected.roi is not None
    assert selected.roi.x0 == original.roi.x0 + 1
    assert original.source is not None
    assert view.analysis.source_preview_sha256 == original.source.sha256
    view.undo_review()
    restored = view.selected_row()
    assert restored is not None and restored.roi == original.roi


def test_invalid_draft_close_stays_open_for_correction(
    qtbot: QtBot, prepared: FigureProjectWindow
) -> None:
    view = prepared.view
    field = view.table.item(0, 3)
    assert field is not None
    previous = field.text()
    field.setText("invalid")
    prepared.close()
    assert not prepared.is_closing
    assert not prepared.resources_closed
    assert "操作失败" in view.status.text()
    field.setText(previous)
    qtbot.waitUntil(lambda: not prepared.operation_busy)


def test_idle_toolbar_and_reduced_motion_are_truthful(
    qtbot: QtBot, tmp_path: Path, prepared: FigureProjectWindow
) -> None:
    assert not prepared.cancel_action.isVisible()
    assert not prepared.progress_action.isVisible()
    prepared.motion.settings = QSettings(str(tmp_path / "motion.ini"), QSettings.Format.IniFormat)
    prepared.motion.settings.setValue("reduce_motion", True)
    prepared.view.show_section("export")
    qtbot.wait(30)
    assert prepared.motion.animation.state().name == "Stopped"
    assert prepared.motion.indicator.geometry().width() > 0
    prepared.begin_operation()
    assert prepared.cancel_action.isVisible() and prepared.progress_action.isVisible()
    prepared.finish_operation("已取消测试任务")
    assert not prepared.cancel_action.isVisible() and not prepared.progress_action.isVisible()


def test_motion_can_be_interrupted_and_disabled(
    qtbot: QtBot, tmp_path: Path, prepared: FigureProjectWindow
) -> None:
    motion = prepared.motion
    motion.settings = QSettings(str(tmp_path / "motion-switch.ini"), QSettings.Format.IniFormat)
    previous = QApplication.isEffectEnabled(Qt.UIEffect.UI_AnimateCombo)
    QApplication.setEffectEnabled(Qt.UIEffect.UI_AnimateCombo, True)
    try:
        motion.settings.setValue("reduce_motion", False)
        prepared.view.show_section("export")
        qtbot.wait(35)
        prepared.view.show_section("source")
        qtbot.waitUntil(lambda: motion.animation.state().name == "Stopped")
        rect = prepared.view.steps.visualItemRect(prepared.view.steps.currentItem())
        assert motion.indicator.geometry().x() == rect.x() + 12
        motion.settings.setValue("reduce_motion", True)
        prepared.view.show_section("export")
        assert motion.animation.state().name == "Stopped"
        rect = prepared.view.steps.visualItemRect(prepared.view.steps.currentItem())
        assert motion.indicator.geometry().x() == rect.x() + 12
    finally:
        QApplication.setEffectEnabled(Qt.UIEffect.UI_AnimateCombo, previous)
