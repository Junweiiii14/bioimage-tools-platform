"""The existing host view must not drop unassigned intake assets or reinterpret confirmations."""

import pytest
from pytestqt.qtbot import QtBot
from wb_tool.api import (
    PreviewRaster,
    WBFigureProject,
    WBIntakeProject,
    confirm_intake,
    create_figure_project_view,
    intake_digest,
    read_figure_project,
)

from tools.wb.tests.test_instrument_intake import assigned, source


def test_host_view_save_retains_pool_confirmation_and_display_thumbnails(qtbot: QtBot) -> None:
    project = assigned()
    project = confirm_intake(project, expected_digest=intake_digest(project))
    view = create_figure_project_view()
    qtbot.addWidget(view)
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


def test_legacy_row_edit_cannot_change_intake_mapping(qtbot: QtBot) -> None:
    view = create_figure_project_view()
    qtbot.addWidget(view)
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
