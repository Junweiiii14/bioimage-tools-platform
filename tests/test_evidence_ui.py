"""Evidence layout uses the existing scientific request and verified result contracts."""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QSignalSpy
from pytestqt.qtbot import QtBot
from wb_tool.api import LaneROI, PreviewRaster

from tests.test_project_measurements import item, setup
from tests.test_project_measurements import windows as windows

if TYPE_CHECKING:
    from bioimage_app.api import FigureProjectWindow


def test_compact_lane_editor_and_full_table_stay_bidirectionally_identical(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    view.show_section("analysis")
    panel = view.analysis
    field = panel.lane_fields[2]
    changed = QSignalSpy(view.changed)
    field.setText("1")
    field.textEdited.emit("1")
    assert item(panel.lanes, 0, 2).text() == "1"
    assert panel.request() is not None
    assert changed.count() == 1
    item(panel.lanes, 0, 3).setText("7")
    assert panel.lane_fields[3].text() == "7"
    panel.lane_selector.setCurrentIndex(1)
    panel.lane_selector.activated.emit(1)
    assert panel.lanes.currentRow() == 1
    assert panel.lane_fields[2].text() == item(panel.lanes, 1, 2).text()
    # An incomplete compact edit must keep the current source, editor text and plan intact.
    original_id = panel.plan.row_id if panel.plan else ""
    panel.lane_fields[3].setText("")
    panel.lane_fields[3].textEdited.emit("")
    view.analysis_sources.setCurrentRow(0)
    assert view.analysis_sources.currentRow() == 1
    assert view.table.currentRow() == 1
    assert panel.plan is not None and panel.plan.row_id == original_id
    assert panel.lane_fields[3].text() == ""
    panel.lane_fields[3].setText("6")
    panel.lane_fields[3].textEdited.emit("6")
    view.analysis_sources.setCurrentRow(0)
    qtbot.waitUntil(window.import_button.isEnabled)
    panel.lane_selector.setCurrentIndex(1)
    panel.lane_selector.activated.emit(1)
    assert not panel.included.isEnabled()
    assert not panel.included.isChecked()
    assert item(panel.lanes, 1, 1).checkState() == Qt.CheckState.Unchecked


def test_evidence_overlay_uses_original_coordinates_and_missing_source_clears_preview(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    panel = view.analysis
    row = view.project().rows[1]
    assert row.source is not None
    assert panel.source_preview_sha256 == row.source.sha256
    captured: list[tuple[LaneROI, ...]] = []
    original = panel.source_canvas.set_lanes

    def capture(lanes: tuple[LaneROI, ...]) -> None:
        captured.append(lanes)
        original(lanes)

    monkeypatch.setattr(panel.source_canvas, "set_lanes", capture)
    panel.lane_selector.setCurrentIndex(2)
    panel.lane_selector.activated.emit(2)
    assert panel.plan is not None
    assert panel.plan.crop.y0 == 5
    assert [(lane.x0, lane.y0, lane.x1, lane.y1) for lane in captured[-1]] == [
        (lane.roi.x0, lane.roi.y0, lane.roi.x1, lane.roi.y1) for lane in panel.plan.request.lanes
    ]
    old_preview = PreviewRaster(
        row.source.sha256, row.width, row.height, 2, 2, b"\x7f" * 4, row.bit_depth, ()
    )
    view.add_missing()
    view.table.setCurrentCell(view.table.rowCount() - 1, 0)
    assert panel.source_preview_sha256 == ""
    assert not panel.plot.values
    view.set_source_preview(old_preview)
    assert panel.source_preview_sha256 == ""
    assert all(item(panel.summary, i, 1).text() == "—" for i in range(panel.summary.rowCount()))


def test_review_summary_preserves_real_zero_and_excluded_values(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.analyze_project(True)
    qtbot.waitUntil(window.import_button.isEnabled, timeout=20000)
    view = window.view
    # Saved refresh may deselect the source; choose the verified second row explicitly.
    view.table.setCurrentCell(1, 0)
    qtbot.waitUntil(window.import_button.isEnabled)
    assert [item(view.analysis.summary, i, 1).text() for i in range(3)] == ["8000", "1.6e+04", "0"]
    view.table.setCurrentCell(0, 0)
    qtbot.waitUntil(window.import_button.isEnabled)
    assert item(view.analysis.summary, 1, 1).text() == "—"
    assert item(view.analysis.summary, 1, 2).text() == "排除"
    assert view.analysis.results.rowCount() == 6


def test_evidence_columns_fit_without_horizontal_page_scroll(
    qtbot: QtBot, tmp_path: Path, windows: Callable[[], "FigureProjectWindow"]
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    window.view.show_section("analysis")
    page = window.view.pages.currentWidget()
    assert page is not None
    for width, height in ((1440, 900), (1100, 780)):
        window.resize(width, height)
        qtbot.waitUntil(lambda: page.width() <= window.view.pages.width())
        assert window.view.canvas.isVisible()
        assert window.view.analysis.plot.isVisible()
        assert window.view.analysis.summary.isVisible()
        assert window.view.canvas.width() >= 280
        assert window.width() == width and window.height() == height
        for evidence in (
            window.view.canvas,
            window.view.analysis.plot,
            window.view.analysis.advanced_toggle,
        ):
            bottom = evidence.mapTo(window, QPoint(0, evidence.height())).y()
            assert bottom < window.height()
            assert not evidence.visibleRegion().isEmpty()


def test_geometry_edit_withdraws_stale_evidence_without_source_reselection(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], "FigureProjectWindow"],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = windows()
    setup(qtbot, tmp_path, window)
    view = window.view
    panel = view.analysis
    assert panel.plan is not None
    source_sha = panel.source_preview_sha256
    captured: list[tuple[LaneROI, ...]] = []
    original = panel.source_canvas.set_lanes

    def capture(lanes: tuple[LaneROI, ...]) -> None:
        captured.append(lanes)
        original(lanes)

    monkeypatch.setattr(panel.source_canvas, "set_lanes", capture)
    item(view.table, view.table.currentRow(), 4).setText("1")
    view.show_section("analysis")
    assert panel.plan is None
    assert not panel.plot.values
    assert captured[-1] == ()
    assert panel.source_preview_sha256 == source_sha  # unchanged original pixels remain valid
    assert all(not field.isEnabled() for field in panel.lane_fields.values())
    assert all(item(panel.summary, i, 1).text() == "—" for i in range(panel.summary.rowCount()))
