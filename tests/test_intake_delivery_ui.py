"""The deliverable controls are visible and dispatch guarded product actions."""

import json
from pathlib import Path

from bioimage_app.web_window import WebWorkbenchWindow
from pytestqt.qtbot import QtBot

from tests.test_intake_web_ui import bridge_snapshot, javascript
from tests.test_intake_web_ui import intake_page as intake_page


def test_saved_display_rotation_remains_editable_with_retained_raw_crop(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    bridge_snapshot(
        window,
        qtbot,
        """({...state,selectedId:'protein-a',rows:[{id:'protein-a',sourceId:'sha',
        name:'raw.tif',fig:'Fig 1',protein:'P',width:180,height:90,lanes:6,
        roi:{x:20,y:25,width:120,height:30},results:[]}],intake:{...state.intake,
        confirmed:true,cropEnabled:true,crops:[{row_id:'protein-a',reviewed:true,
        policy:'intake_crop_display_review@1',raw_crop:{sha256:'retained'},
        crop:{x0:20,y0:25,x1:140,y1:55},reason:'',displayFrame:{center_x:80,center_y:40,
        width:120,height:16,angle_degrees:3,sampling_policy:'within_source@2'}}],
        workflow:{policy:'intake_workflow@4',digest:'display-saved',steps:[
        {stage:'crop',target_id:'protein-a',status:'pending',attempt:1}]}}})""",
    )
    javascript(window, qtbot, "switchMode('review');true")
    assert javascript(window, qtbot, "!document.querySelector('[data-intake-rotation]').disabled")
    javascript(
        window,
        qtbot,
        "const angle=document.querySelector('[data-intake-rotation]');angle.value='5';"
        "angle.dispatchEvent(new Event('input',{bubbles:true}));"
        "angle.dispatchEvent(new Event('change',{bubbles:true}));"
        "document.querySelector('[data-intake-crop-action=confirm]').click();true",
    )
    assert javascript(window, qtbot, "sent.at(-1).payload.displayAngle===5")
    bridge_snapshot(
        window,
        qtbot,
        """({...state,intake:{...state.intake,crops:[{...state.intake.crops[0],
        displayFrame:{...state.intake.crops[0].displayFrame,angle_degrees:5}}],
        workflow:{...state.intake.workflow,digest:'display-next'}}})""",
    )
    assert javascript(window, qtbot, "intakeWorkspace.cropEditable('protein-a')")
    # A fresh session must reconstruct editability from saved evidence, not a draft map.
    bridge_snapshot(window, qtbot, "({...state,sessionEpoch:2})")
    javascript(window, qtbot, "switchMode('review');intakeWorkspace.stageRotation('-17');true")
    assert javascript(
        window,
        qtbot,
        "intakeWorkspace.rotationFrame().angle_degrees===-17&&"
        "intakeWorkspace.rotationFrame().width===120&&"
        "intakeWorkspace.rotationFrame().height===16&&row().roi.height===30",
    )


def test_new_batch_can_continue_ready_groups_despite_another_review(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    javascript(
        intake_page,
        qtbot,
        """
        setState({intake:{...state.intake,confirmed:true,cropEnabled:true,
        figureEnabled:true,outputEnabled:true,crops:[],
        automation:{complete:false,paused:true,follow:false},
        workflow:{policy:'intake_workflow@4',digest:'remaining',pending_ready:1,steps:[
          {stage:'crop',target_id:'protein-a',status:'needs_review'},
          {stage:'crop',target_id:'protein-b',status:'pending'}]}}});
        sent=[];document.querySelector('#intake-primary').click();true
        """,
    )
    assert javascript(
        intake_page,
        qtbot,
        "sent.length===1&&sent[0].action==='intake_sequence_continue'&&"
        "sent[0].payload.workflowDigest==='remaining'",
    )


def test_visible_delivery_controls_and_unsaved_layout_guard(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    window.resize(1440, 900)
    javascript(
        window,
        qtbot,
        """
        setState({intake:{...state.intake,confirmed:true,cropEnabled:true,
        figureEnabled:true,outputEnabled:true,crops:[],figuresReady:[
        {figure_id:'fig-a',row_ids:['protein-a','protein-b']}],
        delivery:{rootPath:'C:/synthetic/project',phase:'sealed'},
        automation:{complete:true,follow:false},
        workflow:{policy:'intake_workflow@3',digest:'delivery-wf',steps:[]}}});
        switchMode('results');true
        """,
    )
    assert javascript(window, qtbot, "!document.querySelector('.intake-delivery-bar').hidden")
    for selector, action in (
        ('[data-intake-crop-action="export"]', "intake_export"),
        ('[data-ig-export="all"]', "intake_grid_export"),
        ("[data-intake-table-export]", "intake_export_table"),
        ("[data-intake-open-directory]", "intake_open_directory"),
    ):
        javascript(
            window,
            qtbot,
            "sent=[];document.querySelector("
            + json.dumps(".intake-delivery-bar " + selector)
            + ").click();true",
        )
        raw = javascript(window, qtbot, "JSON.stringify(sent)")
        assert isinstance(raw, str)
        commands = json.loads(raw)
        assert len(commands) == 1 and commands[0]["action"] == action
        assert commands[0]["payload"]["projectId"] == "intake-project"
    evidence = Path(".local/T080/delivery-ui")
    evidence.mkdir(parents=True, exist_ok=True)
    qtbot.wait(150)  # Allow the native compositor to present the rendered results page.
    assert window.grab().save(str(evidence / "results-wide.png"))
    window.resize(1024, 900)
    qtbot.wait(150)
    assert javascript(
        window,
        qtbot,
        "[...document.querySelectorAll('.intake-delivery-actions button')].every(e=>"
        "{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth;})",
    )
    assert window.grab().save(str(evidence / "results-narrow.png"))
    javascript(
        window,
        qtbot,
        "switchMode('layout');const f=document.querySelector('[data-ig-field=columns]');"
        "f.value=2;f.dispatchEvent(new Event('change',{bubbles:true}));true",
    )
    assert javascript(
        window, qtbot, "document.querySelector('.intake-delivery-bar [data-ig-export]').disabled"
    )
    assert javascript(
        window,
        qtbot,
        "document.querySelector('.intake-delivery-bar').textContent.includes('请先保存')",
    )
    javascript(window, qtbot, "intakeGrid.reset();setState({busy:true});true")
    assert javascript(
        window,
        qtbot,
        "[...document.querySelectorAll('.intake-delivery-actions button')].every(e=>e.disabled)",
    )
