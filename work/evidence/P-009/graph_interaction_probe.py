import json
from pathlib import Path

from bioimage_app.wb_workflow_host import wb_workflow_registry
from bioimage_app.workflow_input import prepare_wb_workspace
from platform_runtime.api import execution_plan_definition
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView

from tooling.qt_test_lifecycle import close_and_dispose_window


def test_native_graph_keyboard_and_ports(qtbot, tmp_path):
    Path(".local/p009-probe").mkdir(parents=True, exist_ok=True)
    plan = prepare_wb_workspace(tmp_path / "source", validation="triangle_u16")
    definition = execution_plan_definition(plan).model_dump(mode="json")
    titles = {
        "wb-verify-original": "原图预检",
        "wb-analyze-original": "WB 粗分析",
        "wb-publish-original": "发布表与曲线",
    }
    catalogue = []
    for host in wb_workflow_registry(plan):
        interface = host.registration.interface
        catalogue.append(
            {
                "module_id": interface.module.module_id,
                "title": titles[interface.module.module_id],
                "inputs": [{"name": p.name, "label": p.name} for p in interface.input_ports],
                "outputs": [{"name": p.port, "label": p.port} for p in interface.output_ports],
            }
        )
    layout = {
        "positions": [
            {"node_id": n["node_id"], "x": i * 300, "y": 40}
            for i, n in enumerate(definition["nodes"])
        ]
    }
    web = Path("apps/desktop/src/bioimage_app/web_ui").resolve()
    html = (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><link rel="stylesheet" href="'
        + (web / "design_tokens.css").as_uri()
        + '"><link rel="stylesheet" href="'
        + (web / "workflow_graph.css").as_uri()
        + '"><style>body{margin:0}#graph{height:100dvh;overflow:auto}</'
        'style><div id="graph"></div><script src="'
        + (web / "workflow_graph.js").as_uri()
        + '"></script><script>'
    )
    html += (
        "const definition="
        + json.dumps(definition)
        + ";const layout="
        + json.dumps(layout)
        + ";const catalogue="
        + json.dumps(catalogue)
        + ';window.edits=[];window.selected="";const before=JSON.string'
        "ify(definition);const graph=new WorkflowGraph(document.query"
        'Selector("#graph"),(edit)=>{edits.push(edit);if(edit.operati'
        'on==="move"){Object.assign(layout.positions.find(p=>p.node_i'
        "d===edit.node_id),{x:edit.x,y:edit.y});graph.render(definiti"
        "on,layout,catalogue);}},(id)=>{selected=id;});graph.render(d"
        "efinition,layout,catalogue);</script></html>"
    )
    page = tmp_path / "probe.html"
    page.write_text(html, encoding="utf-8")
    view = QWebEngineView()
    view.resize(1440, 940)
    view.show()

    def js(code):
        replies = []
        view.page().runJavaScript(code, replies.append)
        qtbot.waitUntil(lambda: bool(replies), timeout=10000)
        return replies[0]

    try:
        view.load(QUrl.fromLocalFile(str(page)))
        qtbot.waitUntil(
            lambda: js('document.querySelectorAll(".wf-node").length') == 3, timeout=15000
        )
        assert js('document.querySelectorAll(".wf-graph-lines path").length') == 2
        view.setFocus()
        js('document.querySelector("[data-node=analyze] .wf-node-title").focus()')
        assert view.focusProxy() is not None
        qtbot.keyClick(view.focusProxy(), Qt.Key.Key_Right)
        qtbot.waitUntil(lambda: js("edits.length") == 1)
        assert json.loads(js("JSON.stringify(edits[0])")) == {
            "operation": "move",
            "node_id": "analyze",
            "x": 320,
            "y": 40,
        }
        assert js("JSON.stringify(definition)===before") is True
        qtbot.keyClick(view.focusProxy(), Qt.Key.Key_Delete)
        qtbot.waitUntil(lambda: js("edits.length") == 2)
        assert json.loads(js("JSON.stringify(edits[1])")) == {
            "operation": "delete_node",
            "node_id": "analyze",
        }
        js(
            'document.querySelector("[data-node=verify] [data-direction=o'
            'utput]").click();document.querySelector("[data-node=analyze]'
            ' [data-port=validation]").click()'
        )
        assert json.loads(js("JSON.stringify(edits[2])")) == {
            "operation": "connect",
            "source_node": "verify",
            "source_port": "validation",
            "target_node": "analyze",
            "target_port": "validation",
        }
        qtbot.waitUntil(lambda: js("document.fonts.status") == "loaded")
        Path(".local/p009-probe/geometry.json").write_text(
            js(
                'JSON.stringify([...document.querySelectorAll(".wf-graph-line'
                's path")].map(p=>({d:p.getAttribute("d"),length:p.getTotalLe'
                "ngth()})))"
            ),
            encoding="utf-8",
        )
        assert view.grab().save(str(Path(".local/p009-probe/graph-1440.png").resolve()))
        view.resize(960, 640)
        qtbot.waitUntil(lambda: js("innerWidth") == 960)
        assert js("document.documentElement.scrollWidth<=innerWidth") is True
        assert view.grab().save(str(Path(".local/p009-probe/graph-960.png").resolve()))
    finally:
        close_and_dispose_window(view, qtbot, resources_closed=lambda: True, timeout=10000)
