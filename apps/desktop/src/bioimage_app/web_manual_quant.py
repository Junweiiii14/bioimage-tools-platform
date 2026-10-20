"""Bounded manual group/peak editing on the current workbench document."""

from dataclasses import replace
from typing import TYPE_CHECKING

from wb_tool.api import (
    AnalysisRequest,
    BandBounds,
    WBAnalysisProject,
    add_manual_group,
    edit_quant_band,
    install_quant_request,
)

if TYPE_CHECKING:
    from bioimage_app.web_bridge import WorkbenchBridge


class ManualQuantCommands:
    def __init__(self, bridge: "WorkbenchBridge") -> None:
        self.bridge = bridge
        self.undo: list[AnalysisRequest] = []
        self.redo: list[AnalysisRequest] = []
        self.binding: tuple[str, str] | None = None
        self.expected: AnalysisRequest | None = None

    def remember(self) -> None:
        host = self.bridge.host
        project, row = host.view.project(), host.view.selected_row()
        if not isinstance(project, WBAnalysisProject) or row is None:
            return
        key = (project.project_id, row.row_id)
        plan = next((p for p in project.analyses if p.row_id == row.row_id), None)
        if (
            self.binding != key
            or plan is None
            or self.expected is None
            or replace(plan.request, revision=0) != replace(self.expected, revision=0)
        ):
            self.undo.clear()
            self.redo.clear()
        if plan:
            self.undo = [*self.undo[-31:], plan.request]
            self.redo.clear()

    def bind(self) -> None:
        host = self.bridge.host
        row = host.view.selected_row()
        project = host.view.project()
        self.binding = (project.project_id, row.row_id) if row else None
        self.expected = (
            next((p.request for p in project.analyses if row and p.row_id == row.row_id), None)
            if isinstance(project, WBAnalysisProject)
            else None
        )

    def run(self, action: str, data: dict[str, object]) -> None:
        host = self.bridge.host
        project, row = host.view.project(), host.view.selected_row()
        if (
            row is None
            or row.source is None
            or (
                data.get("projectId") != project.project_id
                or data.get("id") != row.row_id
                or data.get("sourceId") != row.source.sha256
                or type(data.get("revision")) is not int
                or data.get("revision") != host.view.generation
            )
        ):
            raise ValueError("项目、分组或参数已改变，请刷新后重试")
        if action == "quant_new_group":
            name = data.get("name")
            if not isinstance(name, str):
                raise ValueError("请输入分组名称")
            updated = add_manual_group(project, row.row_id, name)
            host.view.set_project(updated)
            host.view.generation += 1
            host.view.table.setCurrentCell(len(updated.rows) - 1, 0)
            host.select_source(updated.rows[-1].row_id)
            return
        if action == "quant_fig":
            host.analyze_fig_sheet(row.row_id)
            return
        if action in {"quant_rename", "quant_move_row", "quant_merge_group"}:
            figure, protein = data.get("figure"), data.get("protein")
            if not isinstance(figure, str) or not isinstance(protein, str):
                raise ValueError("请输入Fig和条带名称")
            figure = figure.strip()
            if action == "quant_rename" and figure != row.figure and figure in project.figure_order:
                raise ValueError("该Fig已存在，请使用明确的合并分组操作")
            changed = type(row).model_validate(
                {
                    **{key: getattr(row, key) for key in type(row).model_fields},
                    "figure": figure.strip(),
                    "protein": protein.strip(),
                }
            )
            rows = tuple(
                changed
                if x.row_id == row.row_id
                else type(x).model_validate(
                    {**{key: getattr(x, key) for key in type(x).model_fields}, "figure": figure}
                )
                if action != "quant_move_row" and x.figure == row.figure
                else x
                for x in project.rows
            )
            fields = {key: getattr(project, key) for key in type(project).model_fields}
            fields.update(rows=rows, figure_order=tuple(dict.fromkeys(x.figure for x in rows)))
            host.view.set_project(type(project).model_validate(fields))
            host.view.generation += 1
            return
        if not isinstance(project, WBAnalysisProject):
            raise ValueError("请先计算当前组")
        plan = next((p for p in project.analyses if p.row_id == row.row_id), None)
        if plan is None:
            raise ValueError("当前组没有定量计划")
        if action == "quant_history":
            if (
                self.binding != (project.project_id, row.row_id)
                or self.expected is None
                or replace(plan.request, revision=0) != replace(self.expected, revision=0)
            ):
                raise ValueError("分组或参数已改变；当前会话撤销历史已失效")
            direction = data.get("direction")
            if direction not in ("undo", "redo"):
                raise ValueError("未知历史操作")
            stack, other = (self.undo, self.redo) if direction == "undo" else (self.redo, self.undo)
            if not stack:
                raise ValueError("没有可撤销/重做的操作")
            updated = install_quant_request(
                project, row.row_id, replace(stack[-1], revision=plan.request.revision)
            )
            stack.pop()
            other.append(plan.request)
        else:
            lane = data.get("lane")
            if type(lane) is not int or not 1 <= lane <= len(plan.request.lanes):
                raise ValueError("泳道编号无效")
            start, end = data.get("start"), data.get("end")
            bounds = None
            if data.get("operation") == "add":
                if type(start) is not int or type(end) is not int:
                    raise ValueError("补峰边界须为整数")
                bounds = BandBounds(start, end)
            band_id = data.get("bandId", "target")
            if not isinstance(band_id, str):
                raise ValueError("条带身份无效")
            updated = edit_quant_band(
                project,
                row.row_id,
                plan.request.lanes[lane - 1].roi.lane_id,
                str(data.get("operation")),
                band_id,
                bounds,
            )
            self.remember()
        host.view.set_project(updated)
        host.view.generation += 1
        self.bind()
        host.analyze_project(row_ids=(row.row_id,))
