"""Intake drafts preserve explicit identity choices across asynchronous snapshots."""

import json
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

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


def bridge_snapshot(window: WebWorkbenchWindow, qtbot: QtBot, expression: str) -> None:
    """Deliver the actual WebChannel state signal, including bootstrap routing."""
    raw = javascript(window, qtbot, "JSON.stringify(" + expression + ")")
    assert isinstance(raw, str)
    payload = json.loads(raw)
    probe = uuid4().hex
    payload["snapshotProbe"] = probe
    window.bridge.stateChanged.emit(json.dumps(payload))
    qtbot.waitUntil(
        lambda: javascript(window, qtbot, "state.snapshotProbe") == probe, timeout=10000
    )


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
    javascript(window, qtbot, "document.querySelector('[data-intake=prepare]').focus();true")
    javascript(window, qtbot, "setState({busy:true,status:'正在保存'});true")
    assert javascript(window, qtbot, "document.activeElement.matches('.intake-summary h2')")
    javascript(window, qtbot, "setState({busy:false,status:'保存失败'});true")
    assert javascript(window, qtbot, "document.activeElement.dataset.intake==='prepare'")
    assert javascript(
        window, qtbot, "document.querySelector('#intake-live-status').textContent==='保存失败'"
    )
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
    assert javascript(window, qtbot, "document.activeElement.matches('.intake-summary h2')")
    assert javascript(
        window,
        qtbot,
        "document.querySelector('#intake-live-status').textContent.includes('已保存')",
    )
    javascript(window, qtbot, "document.querySelector('[data-intake=edit]').click();true")
    sent = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(sent, str) and json.loads(sent)[-1]["action"] == "intake_edit"
    javascript(window, qtbot, "setState({intake:{...state.intake,workflow:null}});true")
    assert javascript(window, qtbot, "document.activeElement.dataset.intakeField==='fig-label'")


def test_crop_review_uses_fixed_n_draft_and_acknowledges_only_saved_snapshot(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    bridge_snapshot(
        window,
        qtbot,
        """
      ({...state,selectedId:'protein-a',rows:[{id:'protein-a',sourceId:'sha',name:'raw.tif',
        fig:'Fig 1',protein:'Actin',
        width:180,height:90,lanes:6,roi:null,results:[]}],
        intake:{...state.intake,confirmed:true,cropEnabled:true,crops:[{row_id:'protein-a',
          crop:null,reviewed:false,raw_crop:null,reason:'空图未定位'}],workflow:{digest:'wf1',
          ready_count:0,steps:[{stage:'crop',target_id:'protein-a',status:'needs_review',attempt:1,reason:'空图未定位'}]}}})
    """,
    )
    javascript(window, qtbot, "document.querySelector('[data-intake=review-crop]').click();true")
    bridge_snapshot(window, qtbot, "({...state,status:'原图选择与缩略图刷新'})")
    assert javascript(window, qtbot, "mode==='review'")
    assert javascript(window, qtbot, "!document.querySelector('[data-lane-count]')")
    javascript(window, qtbot, "commitCrop({x:20,y:20,width:120,height:16},null);true")
    assert javascript(window, qtbot, "intakeWorkspace.hasDraft()&&row().lanes===6")
    bridge_snapshot(window, qtbot, "({...state,rows:[{...row(),roi:null}]})")
    assert javascript(window, qtbot, "row().roi.x===20&&row().roi.width===120")
    javascript(
        window,
        qtbot,
        """
      document.querySelector('[data-intake-crop-action=confirm]').focus();
      document.querySelector('[data-intake-crop-action=confirm]').click();true
    """,
    )
    sent = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(sent, str)
    command = json.loads(sent)[-1]
    assert command["action"] == "intake_crop_review"
    assert command["payload"]["workflowDigest"] == "wf1"
    assert command["payload"]["rowId"] == "protein-a"
    bridge_snapshot(window, qtbot, "({...state,busy:true,status:'正在保存'})")
    assert javascript(window, qtbot, "document.activeElement.id==='inspector-title'")
    bridge_snapshot(window, qtbot, "({...state,busy:false,status:'保存失败'})")
    assert javascript(window, qtbot, "intakeWorkspace.hasDraft()")
    assert javascript(window, qtbot, "document.activeElement.dataset.intakeCropAction==='confirm'")
    bridge_snapshot(
        window,
        qtbot,
        """
      ({...state,rows:[{...row(),roi:{x:20,y:20,width:120,height:16},draft:false}],
        intake:{...state.intake,crops:[{...state.intake.crops[0],reviewed:true,
          crop:{lane_id:'protein-a',x0:20,y0:20,x1:140,y1:36}}],
          workflow:{...state.intake.workflow,digest:'wf2',steps:[{stage:'crop',target_id:'protein-a',status:'pending',attempt:1,reason:''}]}}})
    """,
    )
    assert javascript(window, qtbot, "!intakeWorkspace.hasDraft()")
    assert javascript(window, qtbot, "document.activeElement.dataset.intakeCropAction==='run'")
    assert javascript(window, qtbot, "row().lanes===6")

    assert javascript(window, qtbot, "mode==='review'")
    bridge_snapshot(window, qtbot, "({...state,sessionEpoch:state.sessionEpoch+1})")
    assert javascript(window, qtbot, "mode==='intake'")


def test_intake_fig_routes_preserve_saved_preview_results_and_source_identity(
    intake_page: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = intake_page
    bridge_snapshot(
        window,
        qtbot,
        """({...state,rows:[
      {id:'protein-a',name:'a.tiff',fig:'Fig 1',protein:'Actin',
        width:180,height:90,lanes:6,roi:{x:10,y:10,width:120,height:30}},
      {id:'protein-b',name:'b.tiff',fig:'Fig 1',protein:'Actin',
        width:180,height:90,lanes:6,roi:{x:20,y:20,width:120,height:30}}],
      cells:[{rowId:'protein-a',fig:'Fig 1',protein:'Actin',
          lane:1,value:400,rawIntegral:400,status:'valid',reason:''},
        {rowId:'protein-b',fig:'Fig 1',protein:'Actin',
          lane:1,value:null,rawIntegral:800,status:'quality_review',reason:'背景待复核'},
        {rowId:'protein-b',fig:'Fig 1',protein:'Actin',
          lane:2,value:null,rawIntegral:null,status:'not_detected',reason:'尚未建立边界'}],
      intake:{...state.intake,confirmed:true,cropEnabled:true,figureEnabled:true,
        figuresReady:[{figure_id:'fig-a',row_ids:['protein-a','protein-b']}],crops:[],
        workflow:{digest:'wf-fig',pending_ready:0,ready_count:4,steps:[
          {stage:'crop',target_id:'protein-a',status:'done',attempt:1},
          {stage:'crop',target_id:'protein-b',status:'done',attempt:1},
          {stage:'compose',target_id:'fig-a',status:'done',attempt:1},
          {stage:'measure',target_id:'fig-a',status:'done',attempt:1},
          {stage:'export',target_id:'intake-project',status:'pending',attempt:0}]}}})""",
    )
    assert javascript(window, qtbot, "document.querySelector('[data-intake=run]').disabled")
    javascript(window, qtbot, "document.querySelector('[data-intake=view-figure]').click();true")
    assert javascript(window, qtbot, "mode==='layout'")
    assert javascript(
        window,
        qtbot,
        "getComputedStyle(document.querySelector('.intake-source-links')).flexDirection==='column'"
        "&&document.querySelectorAll('.intake-source-links "
        "[data-intake-crop-action=source]').length===2",
    )
    sent = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(sent, str)
    assert json.loads(sent)[-1]["action"] == "intake_view_figure"
    assert json.loads(sent)[-1]["payload"]["figureId"] == "fig-a"
    bridge_snapshot(
        window,
        qtbot,
        """({...state,intake:{...state.intake,displayFigureId:'fig-a'},
      montage:'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jvXkAAAAASUVORK5CYII=',
      montageWidth:200,montageHeight:120,montageRegions:[
        {rowId:'protein-b',x:10,y:50,width:120,height:30}]})""",
    )
    assert javascript(window, qtbot, "mode==='layout'")
    assert javascript(
        window, qtbot, "!document.querySelector('[data-edit-row=protein-b]').disabled"
    )
    javascript(window, qtbot, "document.querySelector('[data-edit-row=protein-b]').click();true")
    assert javascript(window, qtbot, "mode==='review'&&state.selectedId==='protein-b'")
    javascript(window, qtbot, "switchMode('results');true")
    bridge_snapshot(window, qtbot, "({...state,status:'记录保持'})")
    assert javascript(window, qtbot, "mode==='results'")
    assert javascript(
        window, qtbot, "document.querySelector('#results-body').innerText.includes('未检测到')"
    )
    assert javascript(
        window,
        qtbot,
        "document.querySelector('#results-body tr:nth-child(2) td:nth-child(3)').innerText==='—'",
    )
    assert javascript(
        window,
        qtbot,
        "document.querySelector('#results-body tr:nth-child(2) td:nth-child(4)').innerText==='800'",
    )
    assert javascript(
        window, qtbot, "document.querySelector('#results-body').innerText.includes('第 2 行')"
    )
    javascript(
        window, qtbot, "document.querySelector('#results-body tr:nth-child(2) button').click();true"
    )
    assert javascript(window, qtbot, "state.selectedId==='protein-b'&&mode==='review'")

    bridge_snapshot(
        window,
        qtbot,
        """({...state,intake:{...state.intake,workflow:{...state.intake.workflow,
      digest:'wf-retry',steps:state.intake.workflow.steps.map(s=>s.stage==='measure'?{...s,status:'failed',reason:'运行未完成'}:s)}}})""",
    )
    javascript(
        window,
        qtbot,
        "switchMode('intake');document.querySelector('[data-intake=retry-stage]').click();true",
    )
    sent = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(sent, str)
    retry = json.loads(sent)[-1]
    assert retry["action"] == "intake_stage_retry"
    assert retry["payload"]["stage"] == "measure" and retry["payload"]["targetId"] == "fig-a"
    assert retry["payload"]["workflowDigest"] == "wf-retry"

    bridge_snapshot(
        window,
        qtbot,
        "({...state,cells:Array.from({length:201},(_,i)=>({...state.cells[0],"
        "rowId:i===200?'protein-b':'protein-a',lane:i+1,"
        "value:i===200?null:400,status:i===200?'failed':'valid',"
        "reason:i===200?'最后槽位真实失败':''}))})",
    )
    javascript(window, qtbot, "switchMode('results');true")
    assert javascript(window, qtbot, "document.querySelectorAll('#results-body tr').length") == 200
    javascript(
        window,
        qtbot,
        "document.querySelector('[data-intake-crop-action=next-results]').click();true",
    )
    assert javascript(window, qtbot, "document.querySelectorAll('#results-body tr').length") == 1
    assert javascript(
        window,
        qtbot,
        "document.querySelector('#results-body').innerText.includes('最后槽位真实失败')",
    )
    assert javascript(
        window, qtbot, "document.querySelector('#results-body td:nth-child(3)').innerText==='—'"
    )
    assert javascript(
        window, qtbot, "document.querySelector('#result-count').innerText.includes('201–201')"
    )
    bridge_snapshot(window, qtbot, "({...state,status:'刷新后保持结果页'})")
    assert javascript(window, qtbot, "document.querySelectorAll('#results-body tr').length") == 1
    javascript(window, qtbot, "document.querySelector('#results-body button').click();true")
    assert javascript(window, qtbot, "state.selectedId==='protein-b'&&mode==='review'")
    javascript(
        window,
        qtbot,
        "switchMode('results');document.querySelector('[data-intake-crop-action=previous-results]').click();true",
    )
    assert javascript(window, qtbot, "document.querySelectorAll('#results-body tr').length") == 200


def test_output_snapshot_actions_distinguish_partial_busy_and_unregistered_publication(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    bridge_snapshot(
        window,
        qtbot,
        """({...state,quant:{table:[{figure:"Fig 1",protein:"GAPDH",lanes:[]}]},
      intake:{...state.intake,confirmed:true,
      cropEnabled:true,figureEnabled:true,outputEnabled:true,
      output:{path:'C:/合成结果/首次快照',committed:true},
      outputs:[{destination:'C:/合成结果/首次快照',complete:false,errors:['原资产缺项']}],
      workflow:{digest:'wf-output',pending_ready:0,ready_count:0,steps:[
        {stage:'export',target_id:'intake-project',status:'failed',reason:'原资产缺项',attempt:1}]}}})""",
    )
    javascript(window, qtbot, "switchMode('results');true")
    assert javascript(
        window,
        qtbot,
        "document.querySelector('#inspector-content').innerText.includes('部分快照已登记')",
    )
    javascript(
        window,
        qtbot,
        "document.querySelector('#inspector-content "
        "[data-intake-crop-action=export]').click();true",
    )
    assert javascript(window, qtbot, "document.querySelector('#gr-workspace').hidden")
    assert javascript(window, qtbot, "!document.querySelector('.workspace').hidden")
    sent = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(sent, str)
    assert json.loads(sent)[-1]["action"] == "intake_export"
    assert json.loads(sent)[-1]["payload"]["workflowDigest"] == "wf-output"
    bridge_snapshot(
        window,
        qtbot,
        "({...state,busy:true,intake:{...state.intake,output:{path:'C:/合成结果/新快照',committed:false}}})",
    )
    assert javascript(
        window,
        qtbot,
        "document.querySelector('#inspector-content [data-intake-crop-action=export]').disabled",
    )
    assert javascript(
        window,
        qtbot,
        "document.querySelector('#inspector-content').innerText.includes('正在登记项目')",
    )
    bridge_snapshot(window, qtbot, "({...state,busy:false})")
    assert javascript(
        window,
        qtbot,
        "document.querySelector('#inspector-content').innerText.includes('项目尚未登记')",
    )
    assert javascript(
        window,
        qtbot,
        "!document.querySelector('#inspector-content').innerText.includes('完整快照已登记')",
    )
    javascript(
        window,
        qtbot,
        "switchMode('intake');document.querySelector('[data-intake=retry-stage]').click();true",
    )
    sent = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(sent, str)
    assert json.loads(sent)[-1]["payload"]["stage"] == "export"
    assert json.loads(sent)[-1]["payload"]["targetId"] == "intake-project"


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


def test_grouped_grid_saves_fig_n_and_keeps_newer_edits_across_save_ack(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    grouping = {
        "schema_version": 1,
        "figures": [],
        "groups": [
            {
                "group_id": "group-" + suffix,
                "source_ids": ["source-" + suffix],
                "figure_id": None,
                "protein_label": "",
                "selected_source_id": None,
                "region_index": None,
                "reuse_confirmed": False,
            }
            for suffix in ("a", "b")
        ],
    }
    javascript(
        window,
        qtbot,
        "setState({intake:{...state.intake,figures:[],proteins:[],grouped_draft:"
        + json.dumps(grouping)
        + "}});true",
    )
    assert javascript(window, qtbot, "document.querySelectorAll('.grouped-card').length") == 2
    assert javascript(window, qtbot, "!document.querySelector('.intake-columns')")
    assert javascript(
        window, qtbot, "document.querySelector('.grouped-card-title').innerText.includes('Run 1')"
    )
    assert javascript(
        window,
        qtbot,
        "document.querySelector('[data-group-select]').getAttribute('aria-label')"
        ".includes('采集组 01')",
    )
    bridge_snapshot(
        window, qtbot, "({...state,intake:{...state.intake,issues:['合成失败.tif：格式无效']}})"
    )
    assert javascript(
        window,
        qtbot,
        "document.querySelector('[aria-label=导入失败文件]').innerText.includes('成功读取的原图仍可继续')",
    )
    javascript(
        window,
        qtbot,
        """
      document.querySelector('[data-group-action=add-fig]').click();
      document.querySelector('[data-group-action=select-visible]').click();
      document.querySelector('[data-group-action=assign]').click();
      for(const el of document.querySelectorAll('[data-group-field=protein]')){
        el.value='蛋白';el.dispatchEvent(new Event('input',{bubbles:true}));
      }
      const n=document.querySelector('[data-group-field=lanes]');
      n.value='4';n.dispatchEvent(new Event('input',{bubbles:true}));
      document.querySelector('[data-group-source=source-a]').click();
      document.querySelector('[data-group-source=source-b]').click();
      document.querySelector('[data-group-action=save]').click();
      window.groupSubmission=sent.at(-1);true
    """,
    )
    raw = javascript(window, qtbot, "JSON.stringify(groupSubmission)")
    assert isinstance(raw, str)
    command = json.loads(raw)
    assert command["action"] == "intake_grouping"
    assert command["payload"]["grouping"]["figures"][0]["lane_count"] == 4
    assert len({g["figure_id"] for g in command["payload"]["grouping"]["groups"]}) == 1
    assert javascript(window, qtbot, "intakeWorkspace.hasDraft()")
    javascript(
        window,
        qtbot,
        """
      const el=document.querySelector('[data-group-field=protein]');
      el.value='保存期间的新草稿';el.dispatchEvent(new Event('input',{bubbles:true}));
      setState({intake:{...state.intake,digest:'grouped-saved',grouped_draft:groupSubmission.payload.grouping}});true
    """,
    )
    assert javascript(window, qtbot, "intakeWorkspace.hasDraft()")
    assert (
        javascript(window, qtbot, "document.querySelector('[data-group-field=protein]').value")
        == "保存期间的新草稿"
    )
    assert javascript(window, qtbot, "!document.querySelector('.intake-conflict[role=alert]')")
    bridge_snapshot(window, qtbot, "({...state,busy:false,status:'保存失败保留草稿'})")
    assert (
        javascript(window, qtbot, "document.querySelector('[data-group-field=protein]').value")
        == "保存期间的新草稿"
    )
    bridge_snapshot(window, qtbot, "({...state,sessionEpoch:state.sessionEpoch+1})")
    assert javascript(window, qtbot, "!intakeWorkspace.hasDraft()")
    assert (
        javascript(window, qtbot, "document.querySelector('[data-group-field=protein]').value")
        == "蛋白"
    )


def test_grouped_save_accepts_explicit_reuse_normalization_without_false_conflict(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    grouping = {
        "schema_version": 1,
        "figures": [{"figure_id": "fig", "label": "Fig 1", "lane_count": 4}],
        "groups": [
            {
                "group_id": "g-" + suffix,
                "source_ids": ["source-" + suffix],
                "figure_id": "fig",
                "protein_label": "P",
                "selected_source_id": "source-" + suffix,
                "region_index": None,
                "reuse_confirmed": False,
            }
            for suffix in ("a", "b")
        ],
    }
    javascript(
        window,
        qtbot,
        "setState({intake:{...state.intake,figures:[],proteins:[],sources:state.intake.sources.map(s=>({...s,asset:{sha256:'a'.repeat(64)}})),grouped_draft:"
        + json.dumps(grouping)
        + "}});true",
    )
    javascript(
        window,
        qtbot,
        """
      const el=document.querySelector('[data-group-field=protein]');
      el.value='修改';el.dispatchEvent(new Event('input',{bubbles:true}));
      document.querySelector('[data-group-reuse]').click();
      document.querySelector('[data-group-action=save]').click();
      window.normalized=JSON.parse(JSON.stringify(sent.at(-1).payload.grouping));
      normalized.groups.forEach(g=>g.reuse_confirmed=true);
      const later=document.querySelector('[data-group-field=protein]');
      later.value='保存期间后写';later.dispatchEvent(new Event('input',{bubbles:true}));
      setState({intake:{...state.intake,digest:'reuse-saved',grouped_draft:normalized}});true
    """,
    )
    assert javascript(window, qtbot, "intakeWorkspace.hasDraft()")
    assert (
        javascript(window, qtbot, "document.querySelector('[data-group-field=protein]').value")
        == "保存期间后写"
    )
    assert javascript(window, qtbot, "!document.querySelector('.intake-conflict[role=alert]')")
    javascript(
        window,
        qtbot,
        """
      document.querySelector('[data-group-reuse]').click();
      document.querySelector('[data-group-action=save]').click();
      const normalized=JSON.parse(JSON.stringify(sent.at(-1).payload.grouping));
      normalized.groups.forEach(g=>g.reuse_confirmed=true);
      setState({intake:{...state.intake,digest:'reuse-later-saved',grouped_draft:normalized}});true
    """,
    )
    assert javascript(window, qtbot, "!intakeWorkspace.hasDraft()")
    assert javascript(
        window, qtbot, "!document.querySelector('[data-group-action=confirm]').disabled"
    )
    javascript(
        window,
        qtbot,
        """
      document.querySelector('[data-group-action=unpick]').click();
      document.querySelector('[data-group-action=save]').click();
      const normalized=sent.at(-1).payload.grouping;
      normalized.groups.forEach(g=>g.reuse_confirmed=false);
      setState({intake:{...state.intake,digest:'reuse-removed',grouped_draft:normalized}});true
    """,
    )
    assert javascript(window, qtbot, "!intakeWorkspace.hasDraft()")


def test_grouped_region_choice_is_explicit_and_original_coordinates_survive_save(
    intake_page: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = intake_page
    javascript(
        window,
        qtbot,
        """
      setState({intake:{...state.intake,proteins:[],grouped_draft:{schema_version:1,
        figures:[{figure_id:'f',label:'Fig',lane_count:4},
          {figure_id:'other',label:'Fig 2',lane_count:6}],
        groups:[{group_id:'g',source_ids:['source-a','source-b'],figure_id:'f',protein_label:'P',selected_source_id:'source-a',region_index:null,reuse_confirmed:false}]},
        sources:state.intake.sources.map(s=>({...s,preview:'data:image/png;base64,iVBORw0KGgo='})),
        discovery:{observations:[{source_id:'source-a',regions:[{x0:10,y0:20,x1:100,y1:40},{x0:30,y0:55,x1:150,y1:75}]}]}}});true
    """,
    )
    assert (
        javascript(window, qtbot, "document.querySelector('[data-group-field=region]').value") == ""
    )
    javascript(
        window,
        qtbot,
        """
      const regionChoice=document.querySelector('[data-group-field=region]');
      regionChoice.value='1';regionChoice.dispatchEvent(new Event('change',{bubbles:true}));
      document.querySelector('[data-group-action=save]').click();true
    """,
    )
    raw = javascript(window, qtbot, "JSON.stringify(sent.at(-1))")
    assert isinstance(raw, str)
    command = json.loads(raw)
    assert command["payload"]["grouping"]["groups"][0]["region_index"] == 1
    assert (
        javascript(window, qtbot, "document.querySelector('.grouped-zoom rect').getAttribute('x')")
        == "30"
    )
    assert (
        javascript(
            window, qtbot, "document.querySelector('.grouped-zoom svg').getAttribute('viewBox')"
        )
        == "0 0 180 90"
    )
    javascript(
        window,
        qtbot,
        """
      setState({intake:{...state.intake,digest:'region-saved',grouped_draft:sent.at(-1).payload.grouping}});
      const owner=document.querySelector('[data-group-field=figure]');owner.value='other';
      owner.dispatchEvent(new Event('change',{bubbles:true}));true
    """,
    )
    assert javascript(window, qtbot, "document.querySelector('[data-group-field=region]').disabled")
    javascript(
        window,
        qtbot,
        """
      document.querySelector('[data-group-action=save]').click();
      setState({intake:{...state.intake,digest:'moved-fig',grouped_draft:sent.at(-1).payload.grouping}});
      true
    """,
    )
    assert javascript(window, qtbot, "!intakeWorkspace.hasDraft()")
    assert javascript(window, qtbot, "!document.querySelector('.intake-conflict[role=alert]')")
    javascript(
        window,
        qtbot,
        """
      const n=document.querySelector('[data-group-field=lanes][data-id=other]');n.value='5';
      n.dispatchEvent(new Event('input',{bubbles:true}));
      n.dispatchEvent(new Event('change',{bubbles:true}));true
    """,
    )
    assert javascript(window, qtbot, "document.querySelector('[data-group-field=region]').disabled")
    assert javascript(window, qtbot, "!document.querySelector('.grouped-zoom rect')")
    assert javascript(window, qtbot, "intakeWorkspace.hasDraft()")


def test_completed_crop_requires_explicit_changed_draft_and_uses_revision_action(
    intake_page: WebWorkbenchWindow,
    qtbot: QtBot,
) -> None:
    window = intake_page
    bridge_snapshot(
        window,
        qtbot,
        """
      ({...state,selectedId:'protein-a',rows:[{id:'protein-a',sourceId:'sha',name:'raw.tif',
        fig:'Fig 1',protein:'P',width:180,height:90,lanes:6,
        roi:{x:20,y:20,width:120,height:16},results:[]}],
       intake:{...state.intake,confirmed:true,cropEnabled:true,crops:[{row_id:'protein-a',crop:{x0:20,y0:20,x1:140,y1:36},reviewed:true,raw_crop:{sha256:'raw'},reason:''}],
         workflow:{digest:'completed',ready_count:1,steps:[{stage:'crop',target_id:'protein-a',status:'done',attempt:2,reason:''}]}}})
    """,
    )
    javascript(window, qtbot, "document.querySelector('[data-intake=review-crop]').click();true")
    assert javascript(
        window, qtbot, "document.querySelector('[data-intake-crop-action=confirm]').disabled"
    )
    javascript(window, qtbot, "commitCrop({x:22,y:22,width:118,height:16},row().roi);true")
    assert javascript(
        window,
        qtbot,
        "document.querySelector('#inspector-content').innerText.includes('历史文件保留')",
    )
    javascript(
        window, qtbot, "document.querySelector('[data-intake-crop-action=confirm]').click();true"
    )
    raw = javascript(window, qtbot, "JSON.stringify(sent.at(-1))")
    assert isinstance(raw, str)
    command = json.loads(raw)
    assert command["action"] == "intake_crop_revise"
    assert command["payload"]["workflowDigest"] == "completed"
    assert command["payload"]["roi"]["x"] == 22
    javascript(window, qtbot, "commitCrop({x:24,y:24,width:116,height:16},row().roi);true")
    bridge_snapshot(
        window,
        qtbot,
        """
      ({...state,rows:state.rows.map(r=>({...r,roi:{x:22,y:22,width:118,height:16},draft:false})),
        intake:{...state.intake,crops:[{row_id:'protein-a',
          crop:{x0:22,y0:22,x1:140,y1:38},reviewed:true,raw_crop:null,reason:''}],
          workflow:{...state.intake.workflow,digest:'saved-first',steps:[
            {stage:'crop',target_id:'protein-a',status:'pending',attempt:2,reason:''}]}}})
    """,
    )
    assert javascript(window, qtbot, "row().roi.x===24 && intakeWorkspace.hasDraft()")
    assert javascript(
        window, qtbot, "!document.querySelector('[data-intake-crop-action=confirm]').disabled"
    )
    javascript(
        window, qtbot, "document.querySelector('[data-intake-crop-action=confirm]').click();true"
    )
    raw = javascript(window, qtbot, "JSON.stringify(sent.at(-1))")
    assert isinstance(raw, str)
    command = json.loads(raw)
    assert command["action"] == "intake_crop_review"
    assert command["payload"]["workflowDigest"] == "saved-first"
    assert command["payload"]["roi"]["x"] == 24
    bridge_snapshot(window, qtbot, "({...state,busy:false,status:'保存失败，草稿保留'})")
    assert javascript(window, qtbot, "intakeWorkspace.hasDraft()")
    javascript(
        window, qtbot, "document.querySelector('[data-intake-crop-action=discard]').click();true"
    )
    assert javascript(window, qtbot, "row().roi.x===22 && !intakeWorkspace.hasDraft()")


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


def test_stage_pages_reach_late_output_and_survive_busy_refresh(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    bridge_snapshot(
        window,
        qtbot,
        """({...state,intake:{...state.intake,confirmed:true,
      cropEnabled:true,figureEnabled:true,outputEnabled:true,
      proteins:Array.from({length:101},(_,i)=>({protein_id:'page-'+i,figure_id:'fig-a',label:'AKT'})),
      workflow:{digest:'wf-pages',pending_ready:0,ready_count:103,steps:[
        ...Array.from({length:101},(_,i)=>({stage:'crop',target_id:'page-'+i,status:'done',attempt:1})),
        {stage:'compose',target_id:'fig-a',status:'done',attempt:1},
        {stage:'measure',target_id:'fig-a',status:'done',attempt:1},
        {stage:'export',target_id:state.projectId,status:'failed',reason:'最后输出失败保留',attempt:1}]}}})""",
    )
    javascript(window, qtbot, "switchMode('intake');true")
    assert (
        javascript(window, qtbot, "document.querySelectorAll('.intake-workflow ol>li').length")
        == 50
    )
    assert javascript(
        window, qtbot, "document.querySelector('[data-intake=previous-stages]').disabled"
    )
    javascript(window, qtbot, "document.querySelector('[data-intake=next-stages]').click();true")
    assert javascript(window, qtbot, "document.querySelector('.intake-workflow ol').start") == 51
    assert javascript(window, qtbot, "document.activeElement.id==='intake-stages-heading'")
    bridge_snapshot(window, qtbot, "({...state,busy:true,status:'后台保存中'})")
    assert javascript(window, qtbot, "document.querySelector('.intake-workflow ol').start") == 51
    assert javascript(window, qtbot, "document.activeElement.id==='intake-stages-heading'")
    sent_before = javascript(window, qtbot, "JSON.stringify(sent)")
    javascript(window, qtbot, "document.querySelector('[data-intake=next-stages]').click();true")
    assert (
        javascript(window, qtbot, "document.querySelectorAll('.intake-workflow ol>li').length") == 4
    )
    assert javascript(window, qtbot, "document.querySelector('[data-intake=next-stages]').disabled")
    assert javascript(
        window,
        qtbot,
        "document.querySelector('.intake-workflow ol').innerText.includes('最后输出失败保留')",
    )
    assert javascript(window, qtbot, "JSON.stringify(sent)") == sent_before
    assert javascript(window, qtbot, "document.querySelector('[data-intake=retry-stage]').disabled")
    bridge_snapshot(window, qtbot, "({...state,busy:false})")
    javascript(window, qtbot, "document.querySelector('[data-intake=retry-stage]').click();true")
    sent = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(sent, str)
    retry = json.loads(sent)[-1]
    assert retry["action"] == "intake_stage_retry"
    assert (
        retry["payload"]["stage"] == "export" and retry["payload"]["workflowDigest"] == "wf-pages"
    )
    bridge_snapshot(
        window,
        qtbot,
        "({...state,intake:{...state.intake,workflow:{...state.intake.workflow,steps:state.intake.workflow.steps.slice(0,1)}}})",
    )
    assert javascript(window, qtbot, "document.querySelector('.intake-workflow ol').start") == 1
    assert (
        javascript(
            window, qtbot, "document.querySelectorAll('nav[aria-label=阶段列表分页]').length"
        )
        == 0
    )


def test_export_suggestions_require_explicit_n_and_target_choice(
    intake_page: WebWorkbenchWindow, qtbot: QtBot, tmp_path: Path
) -> None:
    window = intake_page
    report = {
        "schema_version": 1,
        "algorithm": "export_signal_regions@1",
        "selections": [],
        "observations": [
            {
                "source_id": "source-a",
                "sha256": "a" * 64,
                "group_id": "b" * 24,
                "role": "signal",
                "reasons": ["待确认"],
                "error": "",
                "regions": [
                    {
                        "x0": 20,
                        "y0": 30,
                        "x1": 160,
                        "y1": 60,
                        "lane_counts": [4, 5],
                        "angle_degrees": 4.0,
                    }
                ],
            }
        ],
    }
    javascript(
        window,
        qtbot,
        "setState({intake:{...state.intake,figures:[],proteins:[],"
        "discovery:" + json.dumps(report) + "}});true",
    )
    assert (
        javascript(
            window,
            qtbot,
            "document.querySelector('[data-intake-field=discovery-lane_count]').value",
        )
        == ""
    )
    javascript(
        window, qtbot, "document.querySelector('[data-intake=accept-discovery]').click();true"
    )
    assert javascript(window, qtbot, "sent.length") == 0
    javascript(
        window,
        qtbot,
        """
      document.querySelector('[data-discovery-include]').click();
      const edits=[['figure_label','Fig'],['protein_label','P'],['lane_count','4'],
                   ['region_index','0']];
      for(const [field,value] of edits){
        const input=document.querySelector('[data-intake-field=discovery-'+field+']');
        input.value=value; input.dispatchEvent(new Event('input',{bubbles:true}));
      }
      document.querySelector('[data-intake=accept-discovery]').click();true
    """,
    )
    raw = javascript(window, qtbot, "JSON.stringify(sent)")
    assert isinstance(raw, str)
    command = json.loads(raw)[-1]
    assert command["action"] == "intake_accept_discovery"
    assert command["payload"]["selections"] == [
        {
            "source_id": "source-a",
            "figure_label": "Fig",
            "protein_label": "P",
            "lane_count": 4,
            "region_index": 0,
        }
    ]

    window.resize(1280, 720)
    window.grab().save(str(tmp_path / "export-review.png"))
    report["selections"] = command["payload"]["selections"]
    acknowledged = {
        "digest": "accepted-discovery",
        "figures": [{"figure_id": "f", "label": "Fig", "lane_count": 4}],
        "proteins": [{"protein_id": "p", "figure_id": "f", "label": "P"}],
        "assignments": [{"protein_id": "p", "source_id": "source-a"}],
        "discovery": report,
    }
    javascript(
        window,
        qtbot,
        "setState({intake:{...state.intake,..." + json.dumps(acknowledged) + "}});true",
    )
    assert javascript(window, qtbot, "window.intakeWorkspace.hasDraft()") is False
