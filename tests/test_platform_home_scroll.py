"""Shell browsing retains the live project; every Fig curve and editor remains reachable."""

import json

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from pytestqt.qtbot import QtBot

from tests.test_intake_web_ui import bridge_snapshot, javascript
from tests.test_intake_web_ui import intake_page as intake_page


def test_platform_and_tool_home_preserve_draft_and_ignore_background_navigation(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    javascript(
        window,
        qtbot,
        """
      window.beforeProject=state.projectId;
      platformHome.show('platform');true
    """,
    )
    assert javascript(
        window,
        qtbot,
        "!document.querySelector('#platform-view').hidden && "
        "document.querySelector('#home-view').hidden && "
        "document.querySelectorAll('.installed-tool').length===1",
    )
    # An actual WebChannel snapshot must not reopen the workspace while browsing.
    bridge_snapshot(window, qtbot, "({...state,status:'后台状态已更新'})")
    assert javascript(window, qtbot, "platformHome.current()==='platform'")
    javascript(window, qtbot, "document.querySelector('.installed-tool').click();true")
    assert javascript(
        window,
        qtbot,
        "platformHome.current()==='wb' && !document.querySelector('#home-view').hidden && "
        "document.querySelector('.home-art').getBoundingClientRect().width>0",
    )
    javascript(window, qtbot, "platformHome.show('project');true")
    javascript(
        window,
        qtbot,
        """
      const field=document.querySelector('[data-intake-field="protein"]');
      field.value='手工草稿';field.dispatchEvent(new Event('input',{bubbles:true}));
      platformHome.show('platform');platformHome.show('wb');platformHome.show('project');true
    """,
    )
    assert javascript(
        window,
        qtbot,
        "state.projectId===beforeProject && intakeWorkspace.hasDraft() && "
        "document.querySelector('[data-intake-field=protein]').value==='手工草稿' && "
        "!sent.some(x=>['home','quant_edit'].includes(x.action))",
    )


def large_matrix(window: WebWorkbenchWindow, qtbot: QtBot) -> None:
    javascript(
        window,
        qtbot,
        """
      window.testRows=Array.from({length:10},(_,i)=>({id:'p-'+i,sourceId:'source-'+i,
        name:'source-'+i+'.tif',protein:'Protein '+(i+1),fig:'Fig 1',lanes:18}));
      window.testQuantRows=testRows.map(r=>({rowId:r.id,lanes:Array.from({length:18},(_,i)=>({
        lane:i+1,roi:{y:10},profile:[0,2,5,8,5,2,0],bands:[{id:'target',start:1,end:5,
        baselineStart:1,baselineEnd:1,reason:''}]}))}));
      setState({selectedId:'p-9',rows:testRows,
        quant:{rowId:'p-9',revision:1,sourceId:'source-9',status:'ready',
          lanes:testQuantRows[9].lanes,group:{rows:testQuantRows}},
        intake:{...state.intake,cropEnabled:true,figureEnabled:true,crops:[],
          figures:[{figure_id:'fig-a',label:'Fig 1',lane_count:18}],
          proteins:testRows.map(r=>({protein_id:r.id,figure_id:'fig-a',label:r.protein})),
          figuresReady:[{figure_id:'fig-a',row_ids:testRows.map(r=>r.id),image:{sha256:'fig'}}],
          workflow:{policy:'intake_workflow@3',digest:'matrix-scroll',steps:[]}}});
      switchMode('quant');true
    """,
    )


def test_matrix_editor_reveal_uses_current_dom_after_consecutive_snapshots(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    large_matrix(window, qtbot)
    qtbot.waitUntil(
        lambda: javascript(window, qtbot, "document.getAnimations().length===0") is True
    )
    javascript(
        window,
        qtbot,
        """
      document.documentElement.dataset.motion='reduced';
      document.querySelector('[data-iq-action=toggle-preview]').click();
      const main=document.querySelector('.intake-measure-main');
      main.scrollTop=main.scrollHeight;
      document.querySelector('.intake-figure-curves-scroll').scrollLeft=100000;
      window.beforeReveal=main.scrollTop;
      document.querySelector('[data-iq-row="p-9"][data-iq-lane="18"]').click();
      setState({busy:true});setState({busy:false});true
    """,
    )
    qtbot.waitUntil(
        lambda: (
            javascript(
                window,
                qtbot,
                """(()=>{
          const main=document.querySelector('.intake-measure-main');
          const input=document.querySelector('.intake-figure-editor input');
          if(!input)return false;const r=input.getBoundingClientRect();
          return main.scrollTop>beforeReveal && r.bottom<=main.getBoundingClientRect().bottom &&
            input.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})()""",
            )
            is True
        )
    )


@pytest.mark.parametrize("size,zoom", [((1440, 900), 1.0), ((960, 640), 1.0), ((1440, 960), 1.5)])
def test_large_matrix_last_cell_editor_and_restored_position_are_reachable(
    intake_page: WebWorkbenchWindow, qtbot: QtBot, size: tuple[int, int], zoom: float
) -> None:
    window = intake_page
    window.resize(*size)
    window.web.setZoomFactor(zoom)
    large_matrix(window, qtbot)
    qtbot.waitUntil(
        lambda: javascript(window, qtbot, "document.getAnimations().length===0") is True
    )
    javascript(
        window,
        qtbot,
        """
      window.scientificBefore=JSON.stringify([state.rows,state.quant,state.cells]);
      document.querySelector('[data-iq-action=toggle-preview]').click();
      const main=document.querySelector('.intake-measure-main');
      const matrix=document.querySelector('.intake-figure-curves-scroll');
      main.scrollTop=main.scrollHeight;matrix.scrollLeft=matrix.scrollWidth;
      window.matrixReturn={x:matrix.scrollLeft,y:main.scrollTop};true
    """,
    )
    metrics = javascript(
        window,
        qtbot,
        """JSON.stringify((()=>{
      const cell=document.querySelector('[data-iq-row="p-9"][data-iq-lane="18"]');
      const r=cell.getBoundingClientRect();
      const main=document.querySelector('.intake-measure-main').getBoundingClientRect();
      const name=document.querySelector('[data-iq-protein="p-9"]').getBoundingClientRect();
      return {hit:cell.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)),
        lastVisible:r.top>=main.top && r.bottom<=main.bottom,
        nameVisible:name.left>=main.left && name.right<r.left,
        scrollX:matrixReturn.x,scrollY:matrixReturn.y,count:document.querySelectorAll('.intake-curve-card').length};
      })())""",
    )
    assert isinstance(metrics, str)
    measured = json.loads(metrics)
    assert measured["hit"] and measured["lastVisible"] and measured["nameVisible"], measured
    assert measured["scrollX"] > 0 and measured["scrollY"] > 0 and measured["count"] == 180
    javascript(
        window,
        qtbot,
        'document.querySelector(\'[data-iq-row="p-9"][data-iq-lane="18"]\').click();true',
    )
    qtbot.waitUntil(
        lambda: (
            javascript(
                window,
                qtbot,
                "!!document.querySelector('.intake-figure-editor') && "
                "document.getAnimations().length===0",
            )
            is True
        )
    )
    # Native scrollTo is interruptible; explicitly scrolling to the end must expose
    # the actual save target above the status bar, even at high zoom.
    javascript(
        window,
        qtbot,
        "document.querySelector('.intake-measure-main').scrollTo({top:100000,behavior:'instant'});true",
    )
    assert javascript(
        window,
        qtbot,
        """(()=>{const button=document.querySelector('[data-iq-action=save]');
      const r=button.getBoundingClientRect();
      return button.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)) &&
        r.bottom<=document.querySelector('.status-bar').getBoundingClientRect().top;})()""",
    )
    javascript(window, qtbot, "document.querySelector('[data-iq-action=all]').click();true")
    qtbot.waitUntil(
        lambda: (
            javascript(
                window,
                qtbot,
                "document.activeElement?.dataset.iqRow==='p-9' && "
                "document.activeElement?.dataset.iqLane==='18'",
            )
            is True
        )
    )
    assert javascript(
        window,
        qtbot,
        """
      Math.abs(document.querySelector('.intake-figure-curves-scroll').scrollLeft-
        matrixReturn.x)<1 &&
      Math.abs(document.querySelector('.intake-measure-main').scrollTop-matrixReturn.y)<1 &&
      JSON.stringify([state.rows,state.quant,state.cells])===scientificBefore
    """,
    )
    # Changed status / new markup preserves both scroll axes and manual collapse.
    javascript(window, qtbot, "setState({status:'刷新',busy:true});true")
    assert javascript(
        window,
        qtbot,
        """
      document.querySelector('.intake-measure-main').classList.contains('preview-collapsed') &&
      Math.abs(document.querySelector('.intake-measure-main').scrollTop-matrixReturn.y)<1 &&
      Math.abs(document.querySelector('.intake-figure-curves-scroll').scrollLeft-matrixReturn.x)<1
    """,
    )
