"""Intake drafts preserve explicit identity choices across asynchronous snapshots."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot

from tooling.qt_test_lifecycle import close_and_dispose_window


def javascript(window: WebWorkbenchWindow, qtbot: QtBot, code: str) -> object:
    replies: list[object] = []
    window.web.page().runJavaScript(code, replies.append)
    qtbot.waitUntil(lambda: bool(replies), timeout=10000)
    return replies[0]


def test_prepared_workflow_summary_preserves_pending_and_edit_guard(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    javascript(
        window,
        qtbot,
        "setState({intake:{...state.intake,confirmed:true,assignments:["
        "{protein_id:'protein-a',source_id:'source-a'},"
        "{protein_id:'protein-b',source_id:'source-b'}]}});true",
    )
    assert javascript(window, qtbot, "!!document.querySelector('[data-intake=prepare]')")
    javascript(
        window,
        qtbot,
        "setState({intake:{...state.intake,workflow:{ready_count:0,steps:["
        "{stage:'crop',target_id:'protein-a',status:'pending',attempt:0,reason:''},"
        "{stage:'crop',target_id:'protein-b',status:'pending',attempt:0,reason:''},"
        "{stage:'compose',target_id:'fig-a',status:'pending',attempt:0,reason:''},"
        "{stage:'measure',target_id:'fig-a',status:'pending',attempt:0,reason:''},"
        "{stage:'export',target_id:'intake-project',status:'pending',attempt:0,reason:''}"
        "]}}});true",
    )
    assert javascript(
        window, qtbot, "document.querySelector('.intake-workflow').innerText.includes('0 / 5')"
    )
    assert javascript(
        window,
        qtbot,
        "Array.from(document.querySelectorAll('[data-intake-field]')).every(el=>el.disabled)",
    )
    assert javascript(window, qtbot, "!document.querySelector('[data-intake=edit]').disabled")
    assert javascript(window, qtbot, "!document.querySelector('[data-intake=start]')")
    javascript(window, qtbot, "document.querySelector('[data-intake=edit]').click();true")
    sent = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(sent, str) and json.loads(sent)[-1]["action"] == "intake_edit"


@pytest.fixture
def intake_page(qtbot: QtBot, tmp_path: Path) -> Iterator[WebWorkbenchWindow]:
    window = WebWorkbenchWindow(
        settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat)
    )
    window.show()
    try:
        qtbot.waitUntil(
            lambda: javascript(window, qtbot, "typeof bridge!=='undefined'&&!!bridge") is True,
            timeout=10000,
        )
        window.bridge.timer.stop()
        javascript(
            window,
            qtbot,
            "window.sent=[];bridge={request:(action,payload)=>sent.push({action,payload:"
            "JSON.parse(payload)})};true",
        )
        payload: dict[str, object] = {
            "projectId": "intake-project",
            "sessionEpoch": 1,
            "projectName": "合成仪器导入测试",
            "rows": [],
            "cells": [],
            "busy": False,
            "intake": {
                "digest": "first-digest",
                "confirmed": False,
                "figures": [{"figure_id": "fig-a", "label": "Fig 1", "lane_count": 6}],
                "proteins": [
                    {"protein_id": "protein-a", "figure_id": "fig-a", "label": "Actin"},
                    {"protein_id": "protein-b", "figure_id": "fig-a", "label": "Actin"},
                ],
                "sources": [
                    {
                        "source_id": source_id,
                        "original_name": "0001.tiff",
                        "relative_path": relative,
                        "width": 180,
                        "height": 90,
                        "bit_depth": 16,
                        "preview": None,
                    }
                    for source_id, relative in (
                        ("source-a", "Run 1/0001.tiff"),
                        ("source-b", "Run 2/0001.tiff"),
                    )
                ],
                "assignments": [],
            },
        }
        javascript(window, qtbot, "setState(" + json.dumps(payload) + ");switchMode('intake');true")
        yield window
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )


def test_batch_requires_explicit_targets_and_preserves_duplicate_names(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    assert javascript(window, qtbot, "document.querySelectorAll('.intake-source').length") == 2
    javascript(
        window,
        qtbot,
        "document.querySelectorAll('[data-intake-source]').forEach(el=>el.click());"
        "document.querySelector('[data-intake=stage]').click();true",
    )
    assert javascript(window, qtbot, "document.querySelector('[data-intake=assign]').disabled")
    assert javascript(
        window,
        qtbot,
        "Array.from(document.querySelectorAll('[data-intake-target]')).every(el=>el.value==='')",
    )
    javascript(
        window,
        qtbot,
        "document.querySelectorAll('[data-intake-target]').forEach((el,i)=>{"
        "el.value=i?'protein-a':'protein-b';"
        "el.dispatchEvent(new Event('change',{bubbles:true}));});"
        "document.querySelector('[data-intake=assign]').click();true",
    )
    sent = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(sent, str)
    request = json.loads(sent)[-1]
    assert request["action"] == "intake_assign"
    assert request["payload"]["bindings"] == [
        {"source_id": "source-a", "protein_id": "protein-b"},
        {"source_id": "source-b", "protein_id": "protein-a"},
    ]
    assert request["payload"]["digest"] == "first-digest"
    assert request["payload"]["projectId"] == "intake-project"
    assert request["payload"]["allowReuse"] is False
    assert request["payload"]["replace"] is False
    assert javascript(window, qtbot, "desktopSession.hasDraft()")
    javascript(
        window,
        qtbot,
        "setState({intake:{...state.intake,digest:'assigned-digest',"
        "assignments:sent[sent.length-1].payload.bindings}});true",
    )
    assert javascript(window, qtbot, "desktopSession.hasDraft()") is False
    assert (
        javascript(window, qtbot, "document.querySelector('[data-intake=confirm]').disabled")
        is False
    )
    assert (
        javascript(
            window, qtbot, "document.querySelectorAll('.intake-source-binding')[0].textContent"
        )
        == "Fig 1 / Actin · 第 2 行"
    )


def test_snapshots_preserve_local_draft_and_require_explicit_conflict_reload(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    javascript(
        window,
        qtbot,
        "let input=document.querySelector('[data-intake-field=fig-label]');input.focus();"
        "input.value='Local draft';input.dispatchEvent(new Event('input',{bubbles:true}));"
        "input.setSelectionRange(3,3);setState({status:'Background status'});true",
    )
    assert javascript(window, qtbot, "document.activeElement.value") == "Local draft"
    assert javascript(window, qtbot, "document.activeElement.selectionStart") == 3
    assert javascript(window, qtbot, "desktopSession.hasDraft()")
    javascript(
        window,
        qtbot,
        "setState({intake:{...state.intake,digest:'changed-elsewhere'}});true",
    )
    assert javascript(window, qtbot, "document.querySelector('[data-intake=save-plan]').disabled")
    assert (
        javascript(window, qtbot, "document.querySelector('[data-intake-field=fig-label]').value")
        == "Local draft"
    )
    assert javascript(window, qtbot, "!!document.querySelector('.intake-conflict')")
    javascript(window, qtbot, "document.querySelector('[data-intake=reload]').click();true")
    assert javascript(window, qtbot, "desktopSession.hasDraft()") is False
    assert (
        javascript(window, qtbot, "document.querySelector('[data-intake-field=fig-label]').value")
        == "Fig 1"
    )


def test_invalid_slot_count_cannot_submit_and_new_session_retires_draft(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    javascript(
        window,
        qtbot,
        "let count=document.querySelector('[data-intake-field=lanes]');count.value='0';"
        "count.dispatchEvent(new Event('input',{bubbles:true}));true",
    )
    assert javascript(window, qtbot, "document.querySelector('[data-intake=save-plan]').disabled")
    assert (
        javascript(window, qtbot, "document.querySelector('#intake-plan-error').textContent")
        == "每个 Fig 的样本槽位数必须为 1–96 的整数。"
    )
    javascript(window, qtbot, "setState({sessionEpoch:2,projectId:'next-project'});true")
    assert javascript(window, qtbot, "desktopSession.hasDraft()") is False
    assert (
        javascript(window, qtbot, "document.querySelector('[data-intake-field=lanes]').value")
        == "6"
    )
    assert javascript(window, qtbot, "!!document.querySelector('[data-session=new_intake_folder]')")
    assert javascript(
        window, qtbot, "!!document.querySelector('[name=session-workflow][value=quant]')"
    )


def test_accidental_new_entries_can_be_removed_without_losing_other_edits_or_sending_crop_undo(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    javascript(
        window,
        qtbot,
        "let label=document.querySelector('[data-intake-field=fig-label]');"
        "label.value='Edited Fig';"
        "label.dispatchEvent(new Event('input',{bubbles:true}));"
        "document.querySelector('[data-intake=add-fig]').click();"
        "document.querySelector('[data-intake=remove-new-fig]').click();"
        "document.querySelector('[data-intake=add-protein]').click();"
        "document.querySelector('[data-intake=remove-new-protein]').click();true",
    )
    assert (
        javascript(
            window, qtbot, "document.querySelectorAll('[data-intake-field=fig-label]').length"
        )
        == 1
    )
    assert (
        javascript(window, qtbot, "document.querySelectorAll('[data-intake-field=protein]').length")
        == 2
    )
    assert (
        javascript(window, qtbot, "document.querySelector('[data-intake-field=fig-label]').value")
        == "Edited Fig"
    )
    assert (
        javascript(window, qtbot, "document.querySelector('[data-intake=save-plan]').disabled")
        is False
    )
    assert javascript(window, qtbot, "document.activeElement.dataset.intake") == "add-protein"
    javascript(
        window,
        qtbot,
        "document.activeElement.dispatchEvent(new KeyboardEvent('keydown',"
        "{key:'z',ctrlKey:true,bubbles:true}));"
        "document.activeElement.dispatchEvent(new KeyboardEvent('keydown',"
        "{key:'z',metaKey:true,shiftKey:true,bubbles:true}));true",
    )
    assert (
        javascript(window, qtbot, "sent.some(item=>['undo','redo'].includes(item.action))") is False
    )


def test_existing_confirmed_reuse_does_not_block_unrelated_assignment(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    javascript(
        window,
        qtbot,
        "setState({intake:{...state.intake,digest:'reused',proteins:[...state.intake.proteins,"
        "{protein_id:'protein-c',figure_id:'fig-a',label:'Other'}],assignments:["
        "{protein_id:'protein-a',source_id:'source-a',reuse_confirmed:true},"
        "{protein_id:'protein-b',source_id:'source-a',reuse_confirmed:true}]}});"
        "document.querySelector('[data-intake-source=source-b]').click();"
        "document.querySelector('[data-intake=stage]').click();"
        "let target=document.querySelector('[data-intake-target]');target.value='protein-c';"
        "target.dispatchEvent(new Event('change',{bubbles:true}));true",
    )
    assert (
        javascript(window, qtbot, "document.querySelector('[data-intake=assign]').disabled")
        is False
    )
    assert (
        javascript(
            window, qtbot, "document.querySelector('[data-intake-permission=reuse]').checked"
        )
        is False
    )
