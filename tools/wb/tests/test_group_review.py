"""Review is attached to scientific parameters and durable runs, not crop approval."""

from dataclasses import replace
from pathlib import Path

import pytest
from wb_tool.api import (
    confirm_quant_group,
    project_with_analyses,
    quant_group_reviewed,
    read_figure_project,
)

from tools.wb.tests.test_project_analysis import complete, configured


def test_review_survives_save_revision_and_reopen_but_not_new_parameters(tmp_path: Path) -> None:
    project, paths = configured(tmp_path)
    with pytest.raises(ValueError, match="未完成"):
        confirm_quant_group(project, "Fig1")
    project, _ = complete(project, paths)
    reviewed = confirm_quant_group(project, "Fig1")
    assert quant_group_reviewed(reviewed, "Fig1")
    assert not quant_group_reviewed(project, "Fig1")
    assert [r.reviewed for r in reviewed.rows] == [r.reviewed for r in project.rows]
    reopened = read_figure_project(
        reviewed.model_copy(update={"revision": 5}).model_dump_json().encode()
    )
    assert quant_group_reviewed(reopened, "Fig1")
    plan = project.analyses[0]
    changed = project_with_analyses(
        reviewed, (plan.model_copy(update={"run": None}), project.analyses[1])
    )
    assert not quant_group_reviewed(changed, "Fig1")
    request = replace(plan.request, polarity="light")
    changed = project_with_analyses(
        reviewed, (plan.model_copy(update={"request": request}), project.analyses[1])
    )
    assert not quant_group_reviewed(changed, "Fig1")
    assert quant_group_reviewed(reviewed, "Fig1")


def test_group_membership_and_new_run_invalidate_receipt(tmp_path: Path) -> None:
    project, paths = configured(tmp_path)
    project, _ = complete(project, paths)
    reviewed = confirm_quant_group(project, "Fig1")
    renamed = reviewed.model_copy(
        update={
            "rows": (reviewed.rows[0].model_copy(update={"protein": "other"}), *reviewed.rows[1:])
        }
    )
    assert not quant_group_reviewed(renamed, "Fig1")
    plan = project.analyses[0]
    assert plan.run is not None
    changed = project_with_analyses(
        reviewed,
        (
            plan.model_copy(update={"run": plan.run.model_copy(update={"run_id": "new"})}),
            project.analyses[1],
        ),
    )
    assert not quant_group_reviewed(changed, "Fig1")
    # A missing source in a different group cannot be acknowledged as reviewed.
    with pytest.raises(ValueError, match="未完成"):
        confirm_quant_group(reviewed, "Fig2")
