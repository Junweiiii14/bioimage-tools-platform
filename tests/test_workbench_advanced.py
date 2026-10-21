"""Web command receipts go through actual workers and CAS; legacy widgets are only fixture setup."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from bioimage_app.figure_window import FigureProjectWindow
from bioimage_app.web_bridge import WorkbenchBridge
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot
from wb_tool.api import WBNormalizedProject, WBProjectOCR

from tests.test_intake_web_ui import javascript
from tests.test_project_measurements import setup
from tests.test_project_measurements import windows as windows
from tooling.qt_test_lifecycle import close_and_dispose_window


def dialog(path: Path) -> Callable[..., tuple[str, str]]:
    def choose(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return str(path), ""

    return choose


def test_web_advanced_save_reopen_and_import_receipts(
    qtbot: QtBot,
    tmp_path: Path,
    windows: Callable[[], FigureProjectWindow],
    monkeypatch: pytest.MonkeyPatch,
):
    host = windows()
    setup(qtbot, tmp_path, host)
    bridge = WorkbenchBridge(host, lambda action: None)
    bridge.timer.stop()
    manager = bridge.advanced_commands
    replies: list[dict[str, Any]] = []

    def receive(raw: str) -> None:
        replies.append(json.loads(raw))

    bridge.advancedStateChanged.connect(receive)

    def command(operation: str, value: dict[str, object]) -> dict[str, Any]:
        request = f"request-{len(replies)}"
        manager.command(
            {
                "schema_version": 1,
                "requestId": request,
                "projectId": host.view.project().project_id,
                "sessionEpoch": bridge.session_epoch,
                "revision": host.view.generation,
                "operation": operation,
                "value": value,
            }
        )

        def finished() -> bool:
            manager.poll()
            return any(r["requestId"] == request and r["status"] != "pending" for r in replies)

        qtbot.waitUntil(finished, timeout=20000)
        response = next(
            r for r in reversed(replies) if r["requestId"] == request and r["status"] != "pending"
        )
        assert response["status"] == "done", response.get("error")
        return response["data"]

    data = command("open", {"section": "metadata"})
    row_ids = [r["id"] for r in data["rows"]]
    data = command(
        "metadata_preview", {"mode": "common", "rows": row_ids, "common": {"notes": "网页保存"}}
    )
    data = command(
        "metadata_apply",
        {
            "previewId": data["metadataPreview"]["id"],
            "fields": ["notes"],
            "entries": [{"index": i, "target": key, "values": {}} for i, key in enumerate(row_ids)],
        },
    )
    assert data["persisted"] and all(r.notes == "网页保存" for r in host.view.project().rows)
    data = command(
        "template_apply",
        {
            "template": {"row_gap": 23},
            "figureOrder": data["figureOrder"],
            "composition": data["composition"],
            "style": data["style"],
        },
    )
    assert data["persisted"] and host.view.project().template.row_gap == 23
    command(
        "normalization_create",
        {"target": row_ids[0], "reference": row_ids[1], "kind": "housekeeping"},
    )
    original = host.view.project()
    assert isinstance(original, WBNormalizedProject) and not original.normalizations[0].confirmed
    table = tmp_path / "book.csv"
    table.write_text("row_id,备注\n" + row_ids[0] + ",next\n", encoding="utf-8")
    monkeypatch.setattr("bioimage_app.web_advanced.QFileDialog.getOpenFileName", dialog(table))
    data = command("metadata_import", {})
    assert "rows" not in data["book"]["sheets"][0]
    assert data["book"]["header"]["cells"][1]["text"] == "备注"
    table.write_text(
        "row_id,备注\n" + "\n".join(f"unknown-{i},note-{i}" for i in range(47)), encoding="utf-8"
    )
    command("metadata_import", {})
    data = command(
        "metadata_preview",
        {
            "mode": "table",
            "rows": [],
            "sheet": 0,
            "header": 0,
            "keyKind": "row_id",
            "keyColumn": 0,
            "columns": {"notes": 1},
        },
    )
    preview_id = data["metadataPreview"]["id"]
    assert data["metadataPreview"]["total"] == 47
    assert len(data["metadataPreview"]["entries"]) == 20
    data = command("metadata_page", {"previewId": preview_id, "page": 2})
    assert data["metadataPreview"]["offset"] == 40
    assert len(data["metadataPreview"]["entries"]) == 7
    assert data["metadataPreview"]["entries"][0]["key"] == "unknown-40"

    monkeypatch.setattr(
        "bioimage_app.web_advanced.QFileDialog.getOpenFileName",
        dialog(tmp_path / "original0.tiff"),
    )
    data = command("ocr_import", {})
    assert data["persisted"] and data["ocr"]["source"]
    saved = host.view.project()
    host.load_document(saved.project_id)
    qtbot.waitUntil(lambda: not host.operation_busy, timeout=20000)
    assert host.view.project() == saved
    # A previously loaded table cannot survive even a non-scientific draft revision.
    command("tables_refresh", {})
    assert manager.snapshot()["tables"]
    host.view.generation += 1
    assert manager.snapshot()["tables"] == {}


def test_actual_web_forms_save_reopen_and_export(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    window = WebWorkbenchWindow(
        settings=QSettings(str(tmp_path / "web.ini"), QSettings.Format.IniFormat)
    )
    window.show()
    host = window.host
    try:
        qtbot.waitUntil(
            lambda: javascript(window, qtbot, "typeof bridge!=='undefined'&&!!bridge") is True
        )
        setup(qtbot, tmp_path, host)
        host.analyze_project(True)
        qtbot.waitUntil(lambda: not host.operation_busy, timeout=20000)
        window.bridge.publish()
        qtbot.waitUntil(lambda: javascript(window, qtbot, "state.rows.length===2") is True)

        def js(code: str) -> object:
            return javascript(window, qtbot, code + ";true")

        def open_tool(name: str) -> None:
            js("advancedWorkspace.open(" + json.dumps(name) + ")")
            qtbot.waitUntil(
                lambda: (
                    javascript(window, qtbot, "!!document.querySelector('#advanced-editor')")
                    is True
                )
            )

        def field(path: str, value: str | int) -> None:
            js(
                "(()=>{const e=document.querySelector('[data-adv-path=\""
                + path
                + "\"]');e.value="
                + json.dumps(value)
                + ";e.dispatchEvent(new Event(e.tagName==='SELECT'?'change':'input',"
                + "{bubbles:true}));})()"
            )

        def click(action: str) -> None:
            js("document.querySelector('[data-advanced=\"" + action + "\"]').click()")

        def completed():
            qtbot.waitUntil(
                lambda: (
                    javascript(
                        window,
                        qtbot,
                        "!!document.querySelector('#advanced-editor')&&!document.querySelector('#advanced-status').textContent.startsWith('正在')",
                    )
                    is True
                ),
                timeout=20000,
            )
            status = javascript(
                window, qtbot, "document.querySelector('#advanced-status').textContent"
            )
            assert (
                javascript(
                    window,
                    qtbot,
                    "document.querySelector('#advanced-status').dataset.error!=='true'",
                )
                is True
            ), status

        open_tool("template")
        # A late open receipt may update stored state, never replace a newer drawer.
        js("advancedWorkspace.open('template');workbenchAppearance.open()")
        qtbot.waitUntil(lambda: not host.operation_busy)
        qtbot.wait(100)
        assert (
            javascript(window, qtbot, "document.querySelector('#drawer-title').textContent")
            == "外观与交互"
        )
        assert (
            javascript(window, qtbot, "document.querySelector('#advanced-footer')===null") is True
        )
        open_tool("template")
        field("template.row_gap", 19)
        click("template_apply")
        completed()
        assert host.current_draft_saved and host.view.project().template.row_gap == 19
        # Concurrent replacement of the same scalar must be acknowledged in the page.
        field("template.row_gap", 24)
        assert javascript(window, qtbot, "advancedWorkspace.hasDraft()") is True
        before_generation = host.view.generation
        current = host.view.project()
        host.view.set_project(
            type(current).model_validate(
                {**dict(current), "template": current.template.model_copy(update={"row_gap": 30})}
            )
        )
        host.view.generation += 1  # Match the host commit/install protocol.
        assert host.view.generation != before_generation
        window.bridge.publish()
        qtbot.waitUntil(lambda: javascript(window, qtbot, "state.revision") == host.view.generation)
        open_tool("template")
        assert (
            javascript(window, qtbot, "!!document.querySelector('.advanced-conflicts')") is True
        ), javascript(window, qtbot, "document.querySelector('#drawer-content').innerText")
        js("document.querySelector('[data-choice=local]').click()")
        click("resolve")
        click("template_apply")
        completed()
        assert host.view.project().template.row_gap == 24
        template_path = tmp_path / "web.wbtemplate"
        monkeypatch.setattr(
            "bioimage_app.web_advanced.QFileDialog.getSaveFileName",
            dialog(template_path),
        )
        click("template_export")
        completed()
        assert template_path.is_file()

        open_tool("metadata")
        js("document.querySelector('[data-adv-path^=\"row:\"]').click()")
        field("common.notes", "网页中文实验备注")
        click("metadata_preview")
        completed()
        js(
            "document.querySelector('[data-adv-path=\"field:notes\"]').click();document.querySelector('[data-adv-path=\"entries.0.selected\"]').click()"
        )
        click("metadata_apply")
        completed()
        assert host.view.project().rows[0].notes == "网页中文实验备注"

        open_tool("ocr")
        monkeypatch.setattr(
            "bioimage_app.web_advanced.QFileDialog.getOpenFileName",
            dialog(tmp_path / "original0.tiff"),
        )
        click("ocr_import")
        completed()
        click("add_ocr")
        field("rows.0.figure", host.view.project().rows[0].figure)
        field("rows.0.protein", "AKT")
        field("rows.0.target", host.view.project().rows[0].row_id)
        js("document.querySelector('[data-adv-path=\"rows.0.confirmed\"]').click()")
        click("ocr_apply")
        completed()
        ocr_project = host.view.project()
        assert isinstance(ocr_project, WBProjectOCR) and ocr_project.ocr is not None
        assert ocr_project.ocr.rows[0].confirmed
        ocr_path = tmp_path / "web-ocr.csv"
        monkeypatch.setattr(
            "bioimage_app.web_advanced.QFileDialog.getSaveFileName",
            dialog(ocr_path),
        )
        click("ocr_export")
        completed()
        assert ocr_path.is_file()

        open_tool("normalization")
        field("target", host.view.project().rows[0].row_id)
        field("reference", host.view.project().rows[1].row_id)
        field("kind", "housekeeping")
        click("normalization_create")
        completed()
        normalized = host.view.project()
        assert isinstance(normalized, WBNormalizedProject)
        assert all(p.reference_lane is None for p in normalized.normalizations[0].pairs)
        for i in range(3):
            field(f"plans.0.pairs.{i}.sample", f"sample-{i + 1}")
            field(f"plans.0.pairs.{i}.reference_lane", i + 1)
        js("document.querySelector('[data-adv-path=\"plans.0.confirmed\"]').click()")
        click("normalization_apply")
        completed()
        norm_path = tmp_path / "web-normalization.csv"
        monkeypatch.setattr(
            "bioimage_app.web_advanced.QFileDialog.getSaveFileName",
            dialog(norm_path),
        )
        click("normalization_export")
        completed()
        assert norm_path.is_file()
        saved = host.view.project()
        assert isinstance(saved, WBNormalizedProject)
        assert saved.normalizations[0].confirmed and host.current_draft_saved
        js("closeDrawer()")
        host.load_document(saved.project_id)
        qtbot.waitUntil(lambda: not host.operation_busy, timeout=20000)
        assert host.view.project() == saved
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: host.resources_closed, timeout=20000
        )
