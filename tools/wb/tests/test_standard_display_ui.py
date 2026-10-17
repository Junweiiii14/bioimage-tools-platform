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
