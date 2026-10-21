"""Additional T074 steps within the single installed two-Fig workflow."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image
from wb_tool.api import WBIntakeGridProject, WBIntakeOutputProject

if TYPE_CHECKING:
    from bioimage_app.web_window import WebWorkbenchWindow


class SupervisionCheck:
    def __init__(self, window: "WebWorkbenchWindow", root: Path) -> None:
        self.window = window
        self.root = root
        self.stage = "open-quant"
        self.pending = False
        self.result: object = None
        self.old_runs: tuple[str, ...] = ()
        self.preview = b""
        self.size = (0, 0)
        self.export_name = "single.png"

    def destination(self, *args: object, **kwargs: object) -> tuple[str, str]:
        return str(self.root / self.export_name), ""

    def js(self, code: str) -> None:
        self.pending = True
        self.result = None

        def received(value: object) -> None:
            self.result = value
            self.pending = False

        self.window.web.page().runJavaScript(code, received)

    def poll(self) -> bool:
        if self.pending or self.window.host.operation_busy:
            return False
        project = self.window.host.view.project()
        if not isinstance(project, WBIntakeOutputProject):
            return False
        runs = tuple(p.run.run_id for p in project.analyses if p.run)
        if self.stage == "open-quant":
            self.old_runs = runs
            self.js("select(state.rows[0].id);switchMode('quant');true")
            self.stage = "edit"
        elif self.stage == "edit":
            if self.result is True:
                self.js("""(()=>{const lane=document.querySelector('[data-iq-lane]');
                  if(!lane||state.busy)return false;lane.click();
                  const input=document.querySelector('[data-iq-field=baselineStart]');
                  if(!input)return false;window.checkedBaseline=Number(input.value)+1;
                  input.value=checkedBaseline;
                  input.dispatchEvent(new Event('change',{bubbles:true}));
                  const save=document.querySelector('[data-iq-action=save]');
                  if(!save||save.disabled)throw Error('Baseline save unavailable');
                  save.click();return 'submitted';})()""")
            elif self.result == "submitted":
                self.stage = "recomputed"
            else:
                self.js("!!document.querySelector('[data-iq-lane]')")
        elif self.stage == "recomputed":
            if runs == self.old_runs or any(s.status != "done" for s in project.workflow.steps):
                return False
            if self.result is True:
                self.stage = "single"
                self.js("switchMode('layout');true")
            else:
                self.js("""(()=>{if(state.busy||sequenceOutstanding)return false;
                  switchMode('quant');intakeWorkspace.renderActive();
                  return quantData()?.lanes?.[0]?.bands?.[0]?.baselineStart===checkedBaseline
                    &&!intakeQuant.hasDraft();})()""")
        elif self.stage == "single":
            self.js("""(()=>{const b=document.querySelectorAll('[data-ig-view]')[2];
              if(!b||state.busy)return false;b.click();return true;})()""")
            self.stage = "single-export"
        elif self.stage == "single-export":
            if self.result is True:
                self.js("""(()=>{if(state.busy||sequenceOutstanding||mode!=='layout')return false;
                  if(state.intake.displayFigureId!==state.intake.figures[1].figure_id)return false;
                  const b=document.querySelector('[data-ig-export=single]');
                  if(!b||b.disabled)return false;b.click();return 'exported';})()""")
            elif self.result == "exported":
                self.stage = "grid"
            else:
                self.js("!state.busy&&!sequenceOutstanding")
        elif self.stage == "grid":
            if not (self.root / "single.png").exists():
                return False
            self.js("""(()=>{const change=(field,value)=>{
                const e=document.querySelector('[data-ig-field='+field+']');e.value=value;
                e.dispatchEvent(new Event('change',{bubbles:true}));};
              change('columns','1');change('gap','17');
              document.querySelector('[data-ig-down="0"]').click();
              document.querySelector('[data-ig-save]').click();return true;})()""")
            self.stage = "grid-preview"
        elif self.stage == "grid-preview":
            if not isinstance(project, WBIntakeGridProject):
                return False
            rendered = self.window.host.view.rendered_preview
            if rendered is None or "aggregate" not in json.loads(rendered.manifest_json):
                return False
            manifest = json.loads(rendered.manifest_json)
            expected = [f.figure_id for f in reversed(project.intake.figures)]
            if (
                project.grid.columns != 1
                or project.grid.gap != 17
                or list(project.grid.order) != expected
                or [f["figure_id"] for f in manifest["figures"]] != expected
            ):
                raise ValueError("Grid persistence or preview order differs")
            self.preview = rendered.rgb
            self.size = rendered.width, rendered.height
            self.export_name = "all.png"
            self.js("document.querySelector('[data-ig-export=all]').click();true")
            self.stage = "png"
        elif self.stage == "png":
            if not (self.root / "all.png").exists():
                return False
            self.export_name = "all.tiff"
            self.js("document.querySelector('[data-ig-export=all]').click();true")
            self.stage = "tiff"
        elif self.stage == "tiff":
            if not (self.root / "all.tiff").exists():
                return False
            for name in ("all.png", "all.tiff"):
                with Image.open(self.root / name) as image:
                    if image.size != self.size or image.convert("RGB").tobytes() != self.preview:
                        raise ValueError("Export pixels differ from the visible grid")
            return True
        return False
