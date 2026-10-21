"""The existing host view must not drop unassigned intake assets or reinterpret confirmations."""

from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot
from wb_tool.api import (
    IntakeFigure,
    IntakeProtein,
    PreviewRaster,
    WBFigureProject,
    WBIntakeProject,
    confirm_intake,
    create_figure_project_view,
    intake_digest,
    read_figure_project,
    replace_intake_plan,
)

from tools.wb.tests.owned_widgets import WidgetOwner
from tools.wb.tests.test_instrument_intake import assigned, planned, source


def test_host_view_save_retains_pool_confirmation_and_display_thumbnails(
    qtbot: QtBot, owned_widgets: WidgetOwner
) -> None:
    project = assigned()
    project = confirm_intake(project, expected_digest=intake_digest(project))
    view = create_figure_project_view()
    owned_widgets(view)
    view.set_project(project)
    raster = PreviewRaster(source(3).asset.sha256, 120, 80, 12, 8, b"\x80" * 96, 16, ())
    view.install_thumbnail(raster)
    assert view.thumbnail(source(3).asset.sha256) == raster
    assert view.has_thumbnail(source(3).asset.sha256)
    saved = view.project(revision=7)
    assert isinstance(saved, WBIntakeProject)
    assert saved.intake == project.intake and saved.rows == project.rows
    assert not saved.analyses and saved.ocr is None
    reopened = read_figure_project(saved.model_dump_json().encode())
    view.set_project(reopened)
    assert view.project() == saved
    assert view.thumbnail(source(3).asset.sha256) == raster
    assert all(row.roi is None and not row.reviewed for row in saved.rows)
    view.set_project(WBFigureProject(project_id="another"))
    assert view.thumbnail(source(3).asset.sha256) is None
    view.install_thumbnail(raster)
    assert not view.has_thumbnail(source(3).asset.sha256)


def test_legacy_row_edit_cannot_change_intake_mapping(
    qtbot: QtBot, owned_widgets: WidgetOwner
) -> None:
    view = create_figure_project_view()
    owned_widgets(view)
    project = assigned()
    view.set_project(project)
    view.table.blockSignals(True)
    cell = view.table.item(0, 2)
    assert cell is not None
    cell.setText("legacy changed protein")
    view.table.blockSignals(False)
    with pytest.raises(ValueError, match="清单"):
        view.project()
    view.set_project(project)
    assert view.project().rows == project.rows


@pytest.mark.parametrize(
    "figure,protein", [(" Fig 1 ", "AKT"), ("Fig 1", "AKT "), ("Fig 1, repeat", "AKT")]
)
def test_intake_labels_roundtrip_without_legacy_string_reparsing(
    qtbot: QtBot, owned_widgets: WidgetOwner, figure: str, protein: str
) -> None:
    project = planned()
    project = replace_intake_plan(
        project,
        (IntakeFigure(figure_id="fig-id", label=figure, lane_count=8),),
        (IntakeProtein(protein_id="p1", figure_id="fig-id", label=protein),),
        expected_digest=intake_digest(project),
    )
    view = create_figure_project_view()
    owned_widgets(view)
    view.set_project(project)
    restored = read_figure_project(view.project(revision=4).model_dump_json().encode())
    assert isinstance(restored, WBIntakeProject)
    assert restored.intake == project.intake
    assert restored.rows[0].figure == figure and restored.rows[0].protein == protein
    assert restored.figure_order == (figure,)


def test_host_view_keeps_saved_grid_through_snapshot_and_reopen(
    qtbot: QtBot, owned_widgets: WidgetOwner, tmp_path: Path
) -> None:
    from wb_tool.api import IntakeGrid, WBIntakeGridProject, revise_intake_grid

    from tools.wb.tests.test_intake_output import full_files

    project, _, _ = full_files(tmp_path)
    updated = revise_intake_grid(project, IntakeGrid(columns=1, gap=17, order=("b", "a")))
    view = create_figure_project_view()
    owned_widgets(view)
    view.set_project(updated)
    snapshot = view.project(revision=updated.revision + 1)
    assert isinstance(snapshot, WBIntakeGridProject)
    assert snapshot.grid == updated.grid
    assert snapshot.analyses == updated.analyses
    view.set_project(read_figure_project(snapshot.model_dump_json().encode()))
    reopened = view.project()
    assert isinstance(reopened, WBIntakeGridProject) and reopened.grid == updated.grid
