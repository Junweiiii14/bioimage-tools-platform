"""Compact wire snapshots restore existing display fields through the actual WebChannel."""

import json

from bioimage_app.web_bridge import image_url
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtGui import QImage
from pytestqt.qtbot import QtBot

from tests.test_intake_web_ui import bridge_snapshot, javascript
from tests.test_intake_web_ui import intake_page as intake_page
from tests.test_web_boundary_diagnostics import page as page


def test_compact_cells_restore_order_values_and_shared_references_without_losing_draft(
    page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    identity = javascript(page, qtbot, "[state.projectId,state.sessionEpoch,state.selectedId]")
    bridge_snapshot(
        page,
        qtbot,
        """({...state,snapshotContract:'wb-workbench-snapshot@1',
        rows:state.rows.map(({results,...r})=>r),
        cells:[
          {rowId:state.rows[1].id,lane:2,value:null,rawIntegral:null,status:'failed',reason:'failed'},
          {rowId:state.rows[0].id,lane:2,value:0,rawIntegral:0,status:'valid',reason:''},
          {rowId:state.rows[0].id,lane:1,value:null,rawIntegral:5,status:'quality_review',reason:'review'},
          {rowId:state.rows[1].id,lane:1,value:null,rawIntegral:null,status:'missing_source',reason:'missing'}]})""",
    )
    assert (
        javascript(page, qtbot, "[state.projectId,state.sessionEpoch,state.selectedId]") == identity
    )
    assert javascript(
        page,
        qtbot,
        "state.rows[0].results[0]===state.cells[1] && state.rows[0].results[1]===state.cells[2]"
        " && state.rows[1].results[0]===state.cells[0]"
        " && state.rows[1].results[1]===state.cells[3]",
    )
    assert javascript(
        page,
        qtbot,
        "JSON.stringify(state.cells.map(c=>[c.lane,c.value,c.rawIntegral,c.status]))",
    ) == json.dumps(
        [
            [2, None, None, "failed"],
            [2, 0, 0, "valid"],
            [1, None, 5, "quality_review"],
            [1, None, None, "missing_source"],
        ],
        separators=(",", ":"),
    )
    assert javascript(page, qtbot, "advancedWorkspace.hasDraft()") is True
    assert (
        javascript(
            page, qtbot, "document.querySelector('[data-adv-path=\"template.row_gap\"]').value"
        )
        == "29"
    )


def test_explicit_legacy_results_remain_and_failed_compact_render_restores_previous_state(
    page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    bridge_snapshot(
        page,
        qtbot,
        "({...state,rows:state.rows.map((r,i)=>({...r,results:i===0?[]:[{lane:7,value:0}]}))})",
    )
    assert javascript(page, qtbot, "state.rows[0].results.length") == 0
    assert javascript(page, qtbot, "state.rows[1].results[0].lane") == 7
    original = javascript(page, qtbot, "JSON.stringify(state)")
    assert isinstance(original, str)
    javascript(
        page,
        qtbot,
        "window.compactionPrevious=state;window.compactionRender=render;"
        "render=()=>{window.compactionFailed=true;"
        "throw new TypeError('controlled render failure')};true",
    )
    try:
        failed = json.loads(original)
        failed["projectId"] = "different-project"
        failed["sessionEpoch"] += 1
        failed["snapshotContract"] = "wb-workbench-snapshot@1"
        for row in failed["rows"]:
            del row["results"]
        page.bridge.stateChanged.emit(json.dumps(failed))
        qtbot.waitUntil(lambda: javascript(page, qtbot, "window.compactionFailed") is True)
        assert javascript(page, qtbot, "JSON.stringify(state)") == original
        assert javascript(page, qtbot, "advancedWorkspace.hasDraft()") is True
        assert javascript(page, qtbot, "state.rows===compactionPrevious.rows") is True
    finally:
        javascript(page, qtbot, "render=window.compactionRender;true")
    bridge_snapshot(page, qtbot, "({...state,rows:state.rows.map(({results,...r})=>r)})")
    assert javascript(page, qtbot, "advancedWorkspace.hasDraft()") is True


def test_intake_and_row_preview_references_display_shared_image_and_preserve_zoom(
    intake_page: WebWorkbenchWindow, qtbot: QtBot
) -> None:
    window = intake_page
    image = QImage(4, 4, QImage.Format.Format_RGB32)
    image.fill(0xFF336699)
    preview = image_url(image)
    assert preview is not None
    zoom_image = QImage(8, 8, QImage.Format.Format_RGB32)
    zoom_image.fill(0xFF993366)
    zoom = image_url(zoom_image)
    assert zoom is not None and zoom != preview
    javascript(window, qtbot, "window.sharedPreview=" + json.dumps(preview) + ";true")
    javascript(window, qtbot, "window.separateZoom=" + json.dumps(zoom) + ";true")
    bridge_snapshot(
        window,
        qtbot,
        """({...state,snapshotContract:'wb-workbench-snapshot@1',
        sourcePreviews:{shared:sharedPreview},
        rows:['a','b'].map(k=>({id:'protein-'+k,sourceId:'shared',name:k+'.tif',
          fig:'Fig 1',protein:'Actin',lanes:6,width:180,height:90,roi:null,preview:null})),
        cells:[],intake:{...state.intake,
          sources:state.intake.sources.map(s=>({...s,asset:{sha256:'shared'},preview:null})),
          zoom:{sourceId:'source-a',preview:separateZoom}}})""",
    )
    assert javascript(
        window,
        qtbot,
        "state.rows.every(r=>r.preview===sharedPreview) && "
        "state.intake.sources.every(s=>s.preview===sharedPreview)",
    )
    assert javascript(window, qtbot, "state.intake.zoom.preview===separateZoom") is True
    qtbot.waitUntil(
        lambda: (
            javascript(
                window,
                qtbot,
                "[...document.querySelectorAll('#intake-workspace img')]"
                ".filter(i=>i.src===sharedPreview)"
                ".length===2 && [...document.querySelectorAll('#intake-workspace img')]"
                ".filter(i=>i.src===sharedPreview).every(i=>i.complete&&i.naturalWidth===4)",
            )
            is True
        )
    )
    assert javascript(window, qtbot, "state.projectId") == "intake-project"
    assert javascript(window, qtbot, "state.sessionEpoch") == 1
