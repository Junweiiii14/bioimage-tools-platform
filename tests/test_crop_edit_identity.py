"""A stale web edit cannot overwrite or approve a newer source crop."""

import json
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.web_bridge import WorkbenchBridge
from pytestqt.qtbot import QtBot

from tests.test_web_bridge import bridge as bridge


def crop_payload(bridge: WorkbenchBridge) -> dict[str, object]:
    snapshot = bridge.snapshot()
    row = bridge.host.view.selected_row()
    assert row is not None and row.source is not None
    return {
        "cropEditContract": "legacy_crop_edit@1",
        "projectId": snapshot["projectId"],
        "sessionEpoch": snapshot["sessionEpoch"],
        "revision": snapshot["revision"],
        "id": row.row_id,
        "sourceId": row.source.sha256,
        "roi": {"x": 50, "y": 40, "width": 300, "height": 30},
        "n": 7,
    }


@pytest.mark.parametrize("action", ["crop", "confirm"])
def test_stale_crop_commands_preserve_new_draft_and_fresh_edit_works(
    qtbot: QtBot,
    tmp_path: Path,
    bridge: WorkbenchBridge,
    action: str,
) -> None:
    source = tmp_path / "original.tif"
    tifffile.imwrite(source, np.full((120, 400), 40000, dtype=np.uint16))
    original = source.read_bytes()
    host = bridge.host
    host.open_workspace(str(tmp_path / "workspace"), create=True)
    qtbot.waitUntil(host.import_button.isEnabled, timeout=10000)
    host.import_images((str(source),))
    qtbot.waitUntil(host.import_button.isEnabled, timeout=10000)
    host.view.table.setCurrentCell(0, 0)
    qtbot.waitUntil(lambda: not host.operation_busy, timeout=10000)
    host.view.numbers["crop_height"].setValue(30)
    host.view.canvas.roi_drawn.emit((30, 30, 330, 60))
    stale = crop_payload(bridge)
    # Simulate a newer edit in the existing native advanced editor.
    host.view.canvas.roi_drawn.emit((40, 40, 340, 70))
    advanced = host.view.project()
    assert advanced.rows[0].roi is not None and not advanced.rows[0].reviewed
    fresh = crop_payload(bridge)
    assert fresh["revision"] != stale["revision"]
    invalid = [
        stale,
        {**fresh, "projectId": "other-project"},
        {**fresh, "sessionEpoch": int(bridge.session_epoch) + 1},
        {**fresh, "sessionEpoch": False},
        {k: v for k, v in fresh.items() if k != "revision"},
        {**fresh, "cropEditContract": "legacy_crop_edit@0"},
    ]
    for payload in invalid:
        bridge.request(action, json.dumps(payload))
        current = host.view.project()
        assert current == advanced, {
            name: (getattr(advanced, name), getattr(current, name))
            for name in type(advanced).model_fields
            if getattr(advanced, name) != getattr(current, name)
        }
        assert "改变" in str(bridge.snapshot()["status"])
    bridge.request(action, json.dumps(fresh))
    changed = host.view.project().rows[0]
    if action == "crop":
        assert changed.roi is not None and changed.roi.x0 == 50
    elif action == "confirm":
        assert changed.reviewed
    else:
        assert changed.lane_count == 7
    assert source.read_bytes() == original
