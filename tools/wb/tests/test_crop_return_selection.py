"""A current-row return must never silently approve other selected sources."""

from pathlib import Path

from PySide6.QtCore import QItemSelectionModel
from pytestqt.qtbot import QtBot
from wb_tool.api import create_figure_project_view

from tools.wb.tests.owned_widgets import WidgetOwner
from tools.wb.tests.test_figure_project import sample


def test_bound_confirmation_does_not_approve_other_selected_rows(
    qtbot: QtBot, owned_widgets: WidgetOwner, tmp_path: Path
) -> None:
    project, _ = sample(tmp_path)
    project = project.model_copy(
        update={"rows": tuple(row.model_copy(update={"reviewed": False}) for row in project.rows)}
    )
    view = create_figure_project_view()
    owned_widgets(view)
    view.set_project(project)
    view.table.setCurrentCell(1, 0)
    selection = view.table.selectionModel()
    flags = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
    selection.select(view.table.model().index(0, 0), flags)
    selection.select(view.table.model().index(1, 0), flags)
    assert view.table.currentRow() == 1 and len(selection.selectedRows()) == 2
    view.confirm_row("r1")
    assert [row.reviewed for row in view.project().rows] == [False, True, False, False]
    # Retain the advanced tool's explicitly requested batch-confirm behavior.
    view.confirm_selected()
    assert [row.reviewed for row in view.project().rows] == [True, True, False, False]
