"""The N control is one original-coordinate edit and one undo step."""

from PySide6.QtTest import QSignalSpy
from pytestqt.qtbot import QtBot
from tool_contracts.api import AssetRef
from wb_tool.api import FigureRow, LaneROI, WBFigureProject, create_figure_project_view


def test_lane_count_and_crop_are_one_undoable_edit(qtbot: QtBot) -> None:
    view = create_figure_project_view()
    qtbot.addWidget(view)
    original = LaneROI("r", 300, 100, 600, 180)
    project = WBFigureProject(
        project_id="test",
        figure_order=("Fig1",),
        rows=(
            FigureRow(
                row_id="r",
                source=AssetRef(
                    asset_id="s", relative_path="assets/s.tif", sha256="a" * 64, size_bytes=1
                ),
                filename="source.tif",
                width=1000,
                height=800,
                bit_depth=16,
                lane_count=3,
                roi=original,
            ),
        ),
    )
    view.set_project(project)
    view.table.setCurrentCell(0, 0)
    changes = QSignalSpy(view.changed)
    view.set_crop_lane_count(5)
    assert changes.count() == 1
    changed = view.project().rows[0]
    assert changed.lane_count == 5
    assert changed.roi == LaneROI("r", 200, 100, 700, 180)
    view.undo_review()
    restored = view.project().rows[0]
    assert restored.roi == original and restored.lane_count == 3
    view.redo_review()
    assert view.project().rows[0].lane_count == 5
    view.set_crop_lane_count(2)
    assert view.project().rows[0].lane_count == 2
