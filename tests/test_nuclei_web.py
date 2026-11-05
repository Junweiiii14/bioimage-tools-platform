"""Workbench entry, image controls and actionable setup through the real WebChannel."""

from pathlib import Path

import numpy as np
import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from PIL import Image
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot

from tests.test_project_navigation_session import js
from tests.test_project_navigation_session import session_window as session_window


def test_nuclei_entry_preview_zoom_and_missing_setup(
    session_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = session_window
    window.resize(960, 640)
    source = tmp_path / "image.tif"
    Image.fromarray(np.arange(96, dtype=np.uint8).reshape(8, 12)).save(source)

    def choose(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return str(source), "TIFF"

    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose)
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!!window.nucleiView && !!window.desktopSession") is True,
        timeout=10000,
    )
    js(window, qtbot, "document.querySelector('[data-nuclei-open]').click();true")
    assert js(window, qtbot, "document.querySelector('#nuclei-dialog').open") is True
    qtbot.waitUntil(
        lambda: (
            js(window, qtbot, "!document.querySelector('[data-nuclei-choose=source]').disabled")
            is True
        )
    )
    js(window, qtbot, "document.querySelector('[data-nuclei-choose=source]').click();true")
    qtbot.waitUntil(
        lambda: js(window, qtbot, "document.querySelector('#nuclei-image').naturalWidth") == 12
    )
    assert js(window, qtbot, "document.querySelector('#nuclei-overlay').disabled") is True
    js(
        window,
        qtbot,
        "document.querySelector('#nuclei-zoom').value='2';"
        "document.querySelector('#nuclei-zoom').dispatchEvent(new Event('change'));true",
    )
    assert js(window, qtbot, "document.querySelector('#nuclei-image').style.width") == "24px"
    js(window, qtbot, "document.querySelector('#nuclei-run').click();true")
    qtbot.waitUntil(
        lambda: js(window, qtbot, "!document.querySelector('#nuclei-settings').hidden") is True
    )
    assert js(window, qtbot, "document.querySelector('#nuclei-count').textContent") == "尚无结果"
    assert (
        js(
            window,
            qtbot,
            "(()=>{const d=document.querySelector('#nuclei-dialog').getBoundingClientRect();"
            "return d.left>=0 && d.right<=innerWidth && d.top>=0 && d.bottom<=innerHeight;})()",
        )
        is True
    )
    assert not window.nuclei.busy
    assert not window.host.workspace_path
