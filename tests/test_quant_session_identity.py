"""Historical quantitative requests cannot cross project/session boundaries."""

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from bioimage_app.figure_window import FigureProjectWindow
from bioimage_app.web_bridge import WorkbenchBridge
from pytestqt.qtbot import QtBot

from tools.wb.tests.test_project_analysis import configured


@pytest.mark.parametrize("invalid", ["project", "epoch", "boolean_epoch", "missing_epoch"])
def test_quant_edit_rejects_prior_session_before_mutating(
    qtbot: QtBot, tmp_path: Path, invalid: str
) -> None:
    project, _ = configured(tmp_path)
    row = project.rows[0]
    assert row.source is not None

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Old session reached installation or recomputation")

    def connection(callback: object) -> None:
        pass

    class SessionProbe(WorkbenchBridge):
        def apply(self, data: dict[str, object]) -> None:
            self._edit_quant(data)

    host = cast(
        FigureProjectWindow,
        SimpleNamespace(
            view=SimpleNamespace(
                project=lambda: project,
                selected_row=lambda: row,
                generation=9,
                set_project=forbidden,
            ),
            automatic=SimpleNamespace(finished=SimpleNamespace(connect=connection)),
            analyze_project=forbidden,
            project_results=[],
            operation_busy=False,
            is_closing=False,
        ),
    )
    bridge = SessionProbe(host, lambda _: None)
    bridge.timer.stop()
    bridge.session_epoch = 2
    box = project.analyses[0].request.lanes[0].roi
    payload: dict[str, object] = {
        "projectId": project.project_id,
        "sessionEpoch": 2,
        "id": row.row_id,
        "sourceId": row.source.sha256,
        "revision": 9,
        "lane": 1,
        "roi": {"x": box.x0, "y": box.y0, "width": box.width, "height": box.y1 - box.y0},
    }
    if invalid == "project":
        payload["projectId"] = "another-project"
    elif invalid == "epoch":
        payload["sessionEpoch"] = 1
    elif invalid == "boolean_epoch":
        payload["sessionEpoch"] = True
    else:
        payload.pop("sessionEpoch")
    with pytest.raises(ValueError, match="会话已改变"):
        bridge.apply(payload)
    assert host.view.project() is project and host.view.generation == 9
