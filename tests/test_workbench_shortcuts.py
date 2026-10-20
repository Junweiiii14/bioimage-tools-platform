"""Action preference validation, persistence and real workbench key routing."""

import json
from pathlib import Path

import pytest
from bioimage_app.installation_check_intake import SHORTCUT_PROBE_SCRIPT
from bioimage_app.shortcuts import WorkbenchShortcuts
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from tests.test_intake_web_ui import bridge_snapshot, javascript
from tests.test_intake_web_ui import intake_page as intake_page
from tooling.qt_test_lifecycle import close_and_dispose_window


def test_shortcut_preferences_reject_conflicts_and_preserve_last_saved_map(tmp_path: Path) -> None:
    settings = QSettings(str(tmp_path / "keys.ini"), QSettings.Format.IniFormat)
    preferences = WorkbenchShortcuts(settings)
    original = preferences.bindings.copy()
    with pytest.raises(ValueError, match="同时绑定"):
        preferences.validate({"project.save": "Ctrl+O"})
    for value in ("S", "Meta+S", "Ctrl+Ctrl+S", "Alt+Ctrl+S", "Ctrl+C"):
        with pytest.raises(ValueError):
            preferences.validate({"project.save": value})
    with pytest.raises(ValueError, match="未知动作"):
        preferences.validate({"load.user.module": "Ctrl+J"})
    preferences.update({"project.save": "Ctrl+Shift+S", "group.assign": ""}, "saved")
    assert preferences.receipt == "saved" and not preferences.error
    assert preferences.bindings["project.save"] == "Ctrl+Shift+S"
    reloaded = WorkbenchShortcuts(QSettings(str(tmp_path / "keys.ini"), QSettings.Format.IniFormat))
    assert reloaded.bindings == preferences.bindings
    assert reloaded.bindings["group.assign"] == ""
    preferences.update({"project.save": "Ctrl+O"}, "conflict")
    assert preferences.error and preferences.bindings == reloaded.bindings
    assert WorkbenchShortcuts(settings).bindings == reloaded.bindings
    preferences.update({}, "defaults")
    assert preferences.bindings == original and not preferences.error


def test_invalid_saved_preferences_are_not_deleted_or_claimed_as_applied(tmp_path: Path) -> None:
    settings = QSettings(str(tmp_path / "invalid.ini"), QSettings.Format.IniFormat)
    invalid = json.dumps({"schema_version": 500, "bindings": {"project.save": "Ctrl+S"}})
    settings.setValue("workbench_shortcuts_v1", invalid)
    settings.sync()
    preferences = WorkbenchShortcuts(settings)
    assert preferences.error and preferences.bindings == preferences.defaults
    assert settings.value("workbench_shortcuts_v1") == invalid


def grouped_page(window: WebWorkbenchWindow, qtbot: QtBot) -> None:
    javascript(
        window,
        qtbot,
        "workbenchActions.receive(" + json.dumps(window.shortcuts.snapshot()) + ");true",
    )
    javascript(
        window,
        qtbot,
        """
      setState({intake:{...state.intake,proteins:[],grouped_draft:{schema_version:1,
        figures:[{figure_id:'f',label:'Fig',lane_count:4}],groups:[
          {group_id:'g',source_ids:['source-a','source-b'],figure_id:'f',protein_label:'P',selected_source_id:null,region_index:null,reuse_confirmed:false}]}}});
      document.querySelector('.grouped-card').tabIndex=-1;
      document.querySelector('.grouped-card').focus();true
    """,
    )
    window.activateWindow()
    window.web.setFocus()
    qtbot.waitUntil(lambda: javascript(window, qtbot, "document.hasFocus()") is True)


def test_diagnostic_waits_for_rendered_idle_before_one_real_shortcut(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    grouped_page(window, qtbot)
    bridge_snapshot(window, qtbot, "({...state,busy:true})")
    raw = javascript(window, qtbot, SHORTCUT_PROBE_SCRIPT)
    assert isinstance(raw, str)
    probe = json.loads(raw)
    assert isinstance(probe, dict)
    # These were the old diagnostic's entire ready conditions.
    assert probe["focused"] is True and probe["loaded"] is True
    assert probe["busy"] is True and probe["ready"] is False
    target = window.web.focusProxy()
    assert target is not None
    modifiers = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
    QTest.keyClick(target, Qt.Key.Key_K, modifiers)
    qtbot.waitUntil(lambda: javascript(window, qtbot, "__intakeDiagnosticKeys.length>0") is True)
    assert javascript(window, qtbot, "!document.querySelector('#shortcuts-dialog').open")
    assert javascript(
        window, qtbot, "__intakeDiagnosticKeys.some(e=>e.key.toLowerCase()==='k'&&e.busy)"
    )
    bridge_snapshot(window, qtbot, "({...state,busy:false})")
    raw = javascript(window, qtbot, SHORTCUT_PROBE_SCRIPT)
    assert isinstance(raw, str)
    probe = json.loads(raw)
    assert isinstance(probe, dict) and probe["ready"] is True
    # Arrival of the idle snapshot cannot replay an already rejected native key.
    assert javascript(window, qtbot, "!document.querySelector('#shortcuts-dialog').open")
    QTest.keyClick(target, Qt.Key.Key_K, modifiers)
    qtbot.waitUntil(
        lambda: (
            javascript(window, qtbot, "document.querySelector('#shortcuts-dialog').open") is True
        )
    )


def test_real_key_saves_group_draft_once_through_the_button_action(
    intake_page: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = intake_page
    grouped_page(window, qtbot)
    javascript(
        window,
        qtbot,
        """
      const protein=document.querySelector('[data-group-field=protein]');
      protein.value='P changed';protein.dispatchEvent(new Event('input',{bubbles:true}));
      document.querySelector('.grouped-card').focus();true
    """,
    )
    proxy = window.web.focusProxy()
    assert proxy is not None
    QTest.keyClick(proxy, Qt.Key.Key_S, modifier=Qt.KeyboardModifier.ControlModifier)
    qtbot.waitUntil(lambda: javascript(window, qtbot, "sent.length") == 1)
    raw = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(raw, str)
    assert json.loads(raw)[0]["action"] == "intake_grouping"
    javascript(window, qtbot, "document.querySelector('[data-session=save]').click();true")
    assert javascript(window, qtbot, "sent.length") == 2
    assert javascript(window, qtbot, "sent[1].action") == "intake_grouping"
    custom = window.shortcuts.snapshot()
    custom["bindings"] = {**window.shortcuts.bindings, "project.save": "Ctrl+Shift+S"}
    javascript(window, qtbot, "workbenchActions.receive(" + json.dumps(custom) + ");true")
    QTest.keyClick(proxy, Qt.Key.Key_S, modifier=Qt.KeyboardModifier.ControlModifier)
    assert javascript(window, qtbot, "sent.length") == 2
    QTest.keyClick(
        proxy,
        Qt.Key.Key_S,
        modifier=Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
    )
    qtbot.waitUntil(lambda: javascript(window, qtbot, "sent.length") == 3)


def test_qt_undo_and_web_undo_do_not_both_fire_for_one_key(
    intake_page: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = intake_page
    grouped_page(window, qtbot)
    native_calls: list[bool] = []

    def native_undo(checked: bool = False) -> None:
        native_calls.append(checked)

    undo_action = next(a for a in window.host.project_menu.actions() if a.text() == "撤销图上调整")
    undo_action.triggered.connect(native_undo)
    javascript(
        window,
        qtbot,
        """
      setState({selectedId:'protein-a',rows:[{id:'protein-a',name:'synthetic.tiff',sourceId:'sha',
        fig:'Fig',protein:'P',width:180,height:90,lanes:4,roi:{x:20,y:20,width:120,height:16},results:[]}],
        intake:{...state.intake,cropEnabled:true,crops:[{row_id:'protein-a',reviewed:false}],
          workflow:{digest:'undo',steps:[{stage:'crop',target_id:'protein-a',status:'needs_review'}]}}});
      switchMode('review');commitCrop({x:22,y:22,width:118,height:16},row().roi);
      const previousUndo=intakeWorkspace.undoCrop;window.webUndoCalls=0;
      intakeWorkspace.undoCrop=redo=>{webUndoCalls++;previousUndo(redo);};
      document.body.tabIndex=-1;document.body.focus();true
    """,
    )
    proxy = window.web.focusProxy()
    assert proxy is not None
    QTest.keyClick(proxy, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    qtbot.waitUntil(lambda: javascript(window, qtbot, "webUndoCalls") == 1)
    assert javascript(window, qtbot, "row().roi.x") == 20
    assert native_calls == []


def test_source_key_follows_the_group_clicked_before_dom_replacement(
    intake_page: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = intake_page
    grouped_page(window, qtbot)
    javascript(
        window,
        qtbot,
        """
      const first={...state.intake.grouped_draft.groups[0],source_ids:['source-a'],
        selected_source_id:'source-a'};
      const second={...first,group_id:'other',source_ids:['source-b'],selected_source_id:null};
      setState({intake:{...state.intake,digest:'two-groups',grouped_draft:{
        ...state.intake.grouped_draft,groups:[first,second]}}});
      document.querySelector('[data-group-source=source-b]').click();
      document.body.tabIndex=-1;document.body.focus();
      document.body.dispatchEvent(new KeyboardEvent('keydown',{
        key:'0',code:'Digit0',altKey:true,bubbles:true,cancelable:true}));true
    """,
    )
    assert javascript(
        window, qtbot, "!document.querySelector('[data-group-source=source-b]').checked"
    )
    assert javascript(
        window, qtbot, "document.querySelector('[data-group-source=source-a]').checked"
    )


def test_shortcuts_respect_ime_editable_modal_focus_busy_and_disabled_controls(
    intake_page: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = intake_page
    grouped_page(window, qtbot)
    javascript(
        window,
        qtbot,
        """
      window.pressSource=(target=document.body,extra={})=>target.dispatchEvent(new KeyboardEvent(
        'keydown',{key:'1',code:'Digit1',altKey:true,bubbles:true,cancelable:true,...extra}));
      document.querySelector('.grouped-card').focus();pressSource();true
    """,
    )
    assert javascript(
        window, qtbot, "document.querySelector('[data-group-source=source-a]').checked"
    )
    javascript(window, qtbot, "document.querySelector('[data-group-action=unpick]').click();true")
    for code in (
        "const input=document.querySelector('[data-group-field=protein]');"
        "input.focus();pressSource(input)",
        "const input=document.createElement('div');input.contentEditable='true';"
        "document.body.append(input);input.focus();pressSource(input);input.remove()",
        "pressSource(document.body,{isComposing:true})",
        "document.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true}));"
        "pressSource();"
        "document.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true}))",
        "const d=document.createElement('dialog');document.body.append(d);"
        "d.showModal();pressSource();d.close();d.remove()",
        "window.dispatchEvent(new Event('blur'));pressSource();"
        "window.dispatchEvent(new Event('focus'))",
        "setState({busy:true});pressSource();setState({busy:false})",
        "pressSource(document.body,{repeat:true})",
    ):
        javascript(window, qtbot, "(()=>{" + code + ";return true;})()")
        assert javascript(
            window, qtbot, "!document.querySelector('[data-group-source=source-a]').checked"
        )
    javascript(window, qtbot, "document.querySelector('.grouped-card').focus();pressSource();true")
    assert javascript(
        window, qtbot, "document.querySelector('[data-group-source=source-a]').checked"
    )
    # With no selected group the assign button is disabled, so the key cannot assign it.
    javascript(
        window,
        qtbot,
        "document.body.dispatchEvent(new KeyboardEvent('keydown',"
        "{key:'g',code:'KeyG',ctrlKey:true,shiftKey:true,bubbles:true}));true",
    )
    assert javascript(window, qtbot, "sent.length") == 0


def test_custom_shortcut_settings_save_restore_and_restart_in_the_real_window(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    path = tmp_path / "window-shortcuts.ini"
    for first in (True, False):
        window = WebWorkbenchWindow(settings=QSettings(str(path), QSettings.Format.IniFormat))
        window.show()
        try:
            qtbot.waitUntil(
                lambda window=window: (
                    javascript(window, qtbot, "!!window.workbenchActions?.loaded()") is True
                ),
                timeout=10000,
            )
            window.activateWindow()
            window.web.setFocus()
            qtbot.waitUntil(
                lambda window=window: javascript(window, qtbot, "document.hasFocus()") is True
            )
            javascript(
                window,
                qtbot,
                "document.querySelector('[data-action=shortcut-settings]').click();true",
            )
            assert javascript(window, qtbot, "document.querySelector('#shortcuts-dialog').open")
            if first:
                javascript(
                    window,
                    qtbot,
                    """
                  const field=document.querySelector('[data-shortcut-record="project.save"]');
                  field.focus();field.dispatchEvent(new KeyboardEvent('keydown',
                    {key:'o',code:'KeyO',ctrlKey:true,bubbles:true,cancelable:true}));true
                """,
                )
                assert javascript(
                    window, qtbot, "document.querySelector('[data-shortcut-command=save]').disabled"
                )
                javascript(
                    window,
                    qtbot,
                    """
                  const newKey=document.querySelector('[data-shortcut-record="project.save"]');
                  newKey.focus();newKey.dispatchEvent(new KeyboardEvent('keydown',
                    {key:'s',code:'KeyS',ctrlKey:true,shiftKey:true,bubbles:true,cancelable:true}));
                  document.querySelector('[data-shortcut-command=save]').click();true
                """,
                )
                qtbot.waitUntil(
                    lambda window=window: (
                        window.shortcuts.bindings["project.save"] == "Ctrl+Shift+S"
                    ),
                    timeout=10000,
                )
            else:
                assert (
                    javascript(
                        window,
                        qtbot,
                        "document.querySelector('[data-shortcut-record=\"project.save\"]').value",
                    )
                    == "Ctrl+Shift+S"
                )
                javascript(
                    window,
                    qtbot,
                    "document.querySelector('[data-shortcut-command=restore]').click();document.querySelector('[data-shortcut-command=save]').click();true",
                )
                qtbot.waitUntil(
                    lambda window=window: window.shortcuts.bindings == window.shortcuts.defaults,
                    timeout=10000,
                )
        finally:
            close_and_dispose_window(
                window,
                qtbot,
                resources_closed=lambda window=window: window.host.resources_closed,
                timeout=20000,
            )


def test_executed_group_revision_uses_source_keys_and_one_group_save(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    grouped_page(window, qtbot)
    javascript(
        window,
        qtbot,
        """
      setState({intake:{...state.intake,workflow:{editing:true,steps:[],pending_ready:0}}});
      document.querySelector('.grouped-card').tabIndex=-1;
      document.querySelector('.grouped-card').focus();window.sent=[];true
    """,
    )
    target = window.web.focusProxy()
    assert target is not None
    QTest.keyClick(target, Qt.Key.Key_2, Qt.KeyboardModifier.AltModifier)
    qtbot.waitUntil(
        lambda: (
            javascript(
                window, qtbot, "document.querySelector('[data-group-source=source-b]').checked"
            )
            is True
        )
    )
    QTest.keyClick(target, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
    qtbot.waitUntil(lambda: javascript(window, qtbot, "sent.length===1") is True)
    assert javascript(
        window,
        qtbot,
        "sent[0].action==='intake_grouping' && "
        "sent[0].payload.grouping.groups[0].selected_source_id==='source-b'",
    )


def test_explicit_error_dialog_open_button_still_uses_the_open_action(
    intake_page: WebWorkbenchWindow,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = intake_page
    grouped_page(window, qtbot)
    calls: list[str] = []
    monkeypatch.setattr(window, "choose", calls.append)
    window.bridge.sessionRequested.emit("invalid-shortcut-recovery-test", "{}")
    qtbot.waitUntil(
        lambda: (
            javascript(
                window,
                qtbot,
                "!!document.querySelector('#session-dialog[open] [data-session=open]')",
            )
            is True
        )
    )
    javascript(
        window,
        qtbot,
        """
      document.body.dispatchEvent(new KeyboardEvent('keydown',{
        key:'o',code:'KeyO',ctrlKey:true,bubbles:true,cancelable:true}));true
    """,
    )
    assert calls == []
    javascript(
        window, qtbot, "document.querySelector('#session-dialog [data-session=open]').click();true"
    )
    qtbot.waitUntil(lambda: bool(calls))
    assert calls == ["open_project"]


def test_settings_buttons_preserve_focus_and_list_scroll_during_save_ack(
    intake_page: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = intake_page
    grouped_page(window, qtbot)
    javascript(
        window,
        qtbot,
        "window.prefCatalog="
        + json.dumps(window.shortcuts.snapshot())
        + ";workbenchActions.open();true",
    )
    javascript(
        window,
        qtbot,
        """
      const list=document.querySelector('.shortcut-list');list.scrollTop=list.scrollHeight;
      window.prefScroll=list.scrollTop;
      const clear=document.querySelector('[data-shortcut-clear="shortcuts.settings"]');
      clear.focus({preventScroll:true});clear.click();true
    """,
    )
    assert javascript(
        window, qtbot, "document.activeElement.dataset.shortcutClear==='shortcuts.settings'"
    )
    assert javascript(
        window, qtbot, "document.querySelector('.shortcut-list').scrollTop===prefScroll"
    )
    javascript(
        window,
        qtbot,
        """
      const restore=document.querySelector('[data-shortcut-command=restore]');
      restore.focus();restore.click();
      const previousRequest=desktopSession.request;
      desktopSession.request=(name,data)=>{
        if(name==='shortcuts'){window.prefSubmission=data;return true;}
        return previousRequest(name,data);
      };
      const save=document.querySelector('[data-shortcut-command=save]');
      save.focus();save.click();true
    """,
    )
    assert javascript(window, qtbot, "document.activeElement.matches('[data-shortcut-status]')")
    assert javascript(
        window, qtbot, "document.querySelector('.shortcut-list').scrollTop===prefScroll"
    )
    javascript(
        window,
        qtbot,
        """
      workbenchActions.receive({...prefCatalog,bindings:prefSubmission.bindings,
        receipt:prefSubmission.requestId,error:''});true
    """,
    )
    assert javascript(window, qtbot, "document.activeElement.dataset.shortcutCommand==='save'")
    assert javascript(
        window, qtbot, "document.querySelector('.shortcut-list').scrollTop===prefScroll"
    )
