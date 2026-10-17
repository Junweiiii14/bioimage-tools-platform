"""Real Qt view save/restore keeps display policy and experimental affine metadata."""

from pathlib import Path

from pytestqt.qtbot import QtBot
from wb_tool.api import DisplayFrame, WBLayoutProject, create_figure_project_view

from tools.wb.tests.test_standard_display import mixed_resolution


def test_view_roundtrip_retains_standard_style_and_frames(qtbot: QtBot, tmp_path: Path) -> None:
    project, _ = mixed_resolution(tmp_path)
    slices = list(project.composition.slices)
    frame = DisplayFrame(center_x=18, center_y=15, width=20, height=8, angle_degrees=15)
    slices[0] = slices[0].model_copy(update={"display_frame": frame})
    project = project.model_copy(
        update={"composition": project.composition.model_copy(update={"slices": tuple(slices)})}
    )
    view = create_figure_project_view()
    qtbot.addWidget(view)
    view.set_project(project)
    current = view.project()
    assert isinstance(current, WBLayoutProject)
    assert current.layout_style == project.layout_style
    assert current.composition.slices == project.composition.slices
    assert {c.figure: c.column for c in current.composition.columns} == {
        c.figure: c.column for c in project.composition.columns
    }
    view.laboratory_layout.heading.setValue(14)
    current = view.project()
    assert isinstance(current, WBLayoutProject)
    assert current.layout_style.display_policy == "standard_lane_ratio@1"
    assert current.layout_style.lane_unit == 120
    assert current.composition.slices[0].display_frame == frame
    item = view.laboratory_layout.table.item(0, 5)
    assert item is not None
    item.setText("2")
    assert view.laboratory_layout.composition().slices[0].display_frame is None


def test_crop_edits_clear_only_changed_frame_and_undo_restores(
    qtbot: QtBot, tmp_path: Path
) -> None:
    project, _ = mixed_resolution(tmp_path)
    frame = DisplayFrame(center_x=18, center_y=15, width=20, height=8, angle_degrees=15)
    slices = tuple(
        s.model_copy(update={"display_frame": frame}) if s.row_id == "r0" else s
        for s in project.composition.slices
    )
    project = project.model_copy(
        update={"composition": project.composition.model_copy(update={"slices": slices})}
    )
    view = create_figure_project_view()
    qtbot.addWidget(view)
    view.set_project(project)
    view.table.setCurrentCell(0, 0)
    roi = project.rows[0].roi
    assert roi is not None
    view.canvas.roi_drawn.emit((roi.x0 + 5, roi.y0, roi.x1, roi.y1))
    changed = view.project()
    assert isinstance(changed, WBLayoutProject)
    assert changed.composition.slices[0].display_frame is None
    assert changed.composition.slices[1:] == project.composition.slices[1:]
    view.undo_review()
    restored = view.project()
    assert isinstance(restored, WBLayoutProject)
    assert restored.rows[0].roi == roi
    assert restored.composition.slices[0].display_frame == frame
    view.redo_review()
    assert view.project().rows[0].roi != roi
