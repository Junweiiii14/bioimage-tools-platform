"""JSON arrays cross the strict grid boundary without weakening scalar validation."""

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from bioimage_app.web_bridge import WorkbenchBridge
from bioimage_app.web_intake_supervision import apply_supervision
from wb_tool.api import WBFigureProject, WBIntakeGridProject, intake_workflow_digest

from tools.wb.tests.test_intake_output import full_files


def test_grid_bridge_accepts_json_array_order_and_rejects_fractional_columns(
    tmp_path: Path,
) -> None:
    project, _, _ = full_files(tmp_path)
    saved: list[WBFigureProject] = []

    def save(**kwargs: object) -> None:
        transform = cast(Callable[[WBFigureProject], WBFigureProject], kwargs["transform"])
        saved.append(transform(project))

    bridge = cast(
        WorkbenchBridge,
        SimpleNamespace(
            session_epoch=7,
            host=SimpleNamespace(
                view=SimpleNamespace(project=lambda: project, generation=project.revision),
                save=save,
            ),
        ),
    )
    payload: dict[str, object] = {
        "projectId": project.project_id,
        "sessionEpoch": 7,
        "workflowDigest": intake_workflow_digest(project),
        "grid": {"columns": 1, "gap": 17, "order": ["b", "a"]},
    }
    apply_supervision(bridge, "intake_grid_save", payload)
    assert len(saved) == 1 and isinstance(saved[0], WBIntakeGridProject)
    assert saved[0].grid.order == ("b", "a")
    assert saved[0].analyses == project.analyses
    payload["grid"] = {"columns": 1.5, "gap": 17, "order": ["b", "a"]}
    with pytest.raises(ValueError):
        apply_supervision(bridge, "intake_grid_save", payload)
    assert len(saved) == 1
