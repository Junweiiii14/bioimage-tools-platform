"""Local web presentation adapter; original-pixel work remains in the WB host."""

import base64
import json
import math
from collections import Counter
from collections.abc import Callable
from hashlib import sha256
from typing import cast

from PySide6.QtCore import QBuffer, QIODevice, QObject, QTimer, Signal, Slot
from PySide6.QtGui import QImage, QImageWriter
from wb_tool.api import (
    BandBounds,
    Baseline,
    LaneROI,
    ManualQuantTarget,
    ProjectTableCell,
    WBAnalysisProject,
    WBIntakeProject,
    WBLayoutProject,
    WBPartitionProject,
    confirm_quant_group,
    intake_snapshot,
    quant_group_reviewed,
    row_is_ready,
)

from bioimage_app.figure_window import FigureProjectWindow
from bioimage_app.web_intake import apply_intake_command
from bioimage_app.web_manual_quant import ManualQuantCommands
from bioimage_app.web_quant import quant_snapshot


def image_url(image: QImage) -> str | None:
    if image.isNull():
        return None
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not QImageWriter(buffer, b"png").write(image):
        return None
    return "data:image/png;base64," + base64.b64encode(buffer.data().data()).decode("ascii")


def cell_state(cell: ProjectTableCell) -> dict[str, object]:
    return {
        "rowId": cell.row_id,
        "fig": cell.figure,
        "protein": cell.protein,
        "lane": cell.lane_index,
        "value": cell.value,
        "rawIntegral": cell.raw_integral,
        "status": cell.status,
        "reason": cell.reason,
    }


class WorkbenchBridge(QObject):
    stateChanged = Signal(str)
    progressChanged = Signal(str)
    sessionRequested = Signal(str, str)
    sessionStateChanged = Signal(str)

    @Slot(str, str)
    def session(self, action: str, payload: str = "{}") -> None:
        if len(payload) <= 8192:
            self.sessionRequested.emit(action, payload)

    def replace_host(self, host: FigureProjectWindow) -> None:
        self.session_epoch += 1
        self.host.automatic.finished.disconnect(self._automatic_completed)
        self.host = host
        self.host.automatic.finished.connect(self._automatic_completed)
        self._previous = ""
        self._previous_progress = ""
        self._published_key = None
        self._images.clear()
        self._montage_key = 0
        self._montage = None
        self._error = ""
        self._completed_key = ""
        self._quant_overview = None
        self._pending_source = None
        self.timer.start()

    def __init__(
        self,
        host: FigureProjectWindow,
        choose: Callable[[str], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.host = host
        self.choose = choose
        self.session_epoch = 0
        self._previous = ""
        self._published_key: tuple[object, ...] | None = None
        self._images: dict[str, str | None] = {}
        self._montage_key = 0
        self._montage: str | None = None
        self._error = ""
        self._completed_key = ""
        self._quant_overview: tuple[str, str] | None = None
        self._pending_source: tuple[str, str] | None = None
        self.manual_commands = ManualQuantCommands(self)
        self.host.automatic.finished.connect(self._automatic_completed)
        self.timer = QTimer(self)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.publish)
        self.timer.start()

    def _automatic_completed(self, output: str) -> None:
        self._completed_key = output

    def snapshot(self) -> dict[str, object]:
        view = self.host.view
        project = view.project()
        selected_index = view.table.currentRow()
        selected = project.rows[selected_index] if 0 <= selected_index < len(project.rows) else None
        preview = view.source_preview
        if preview and preview.sha256 not in self._images:
            image = QImage(
                preview.pixels,
                preview.preview_width,
                preview.preview_height,
                preview.preview_width,
                QImage.Format.Format_Grayscale8,
            )
            self._images[preview.sha256] = image_url(image)
        live_sources = {r.source.sha256 for r in project.rows if r.source}
        intake = None
        if isinstance(project, WBIntakeProject):
            live_sources.update(source.asset.sha256 for source in project.intake.sources)
            intake = intake_snapshot(project)
            sources: list[dict[str, object]] = []
            for source in project.intake.sources:
                raster = view.thumbnail(source.asset.sha256)
                if raster and source.asset.sha256 not in self._images:
                    self._images[source.asset.sha256] = image_url(
                        QImage(
                            raster.pixels,
                            raster.preview_width,
                            raster.preview_height,
                            raster.preview_width,
                            QImage.Format.Format_Grayscale8,
                        )
                    )
                sources.append(
                    {
                        **source.model_dump(mode="json"),
                        "preview": self._images.get(source.asset.sha256),
                    }
                )
            intake["sources"] = sources
            intake["issues"] = list(self.host.intake.issues)
        source_counts = Counter(r.source.sha256 for r in project.rows if r.source)
        self._images = {key: value for key, value in self._images.items() if key in live_sources}
        pixmap = view.preview_label.full_pixmap
        if pixmap.cacheKey() != self._montage_key:
            self._montage_key = pixmap.cacheKey()
            self._montage = image_url(pixmap.toImage())
        regions: list[dict[str, object]] = []
        rendered = view.rendered_preview
        montage_width = montage_height = 0
        montage = None
        if rendered and not pixmap.isNull():
            manifest = json.loads(rendered.manifest_json)
            if (
                manifest.get("project_id") == project.project_id
                and manifest.get("revision") == project.revision
            ):
                montage = self._montage
                montage_width, montage_height = rendered.width, rendered.height
                for item in manifest.get("rows", []):
                    box = item.get("output_box")
                    if box and item.get("source_sha256"):
                        peers = [
                            r["output_box"]
                            for r in manifest.get("rows", [])
                            if r.get("figure") == item.get("figure") and r.get("output_box")
                        ]
                        label = project.template.label_width
                        border = project.template.border
                        heading = (
                            project.layout_style.heading_size
                            if isinstance(project, WBLayoutProject)
                            else project.template.font_size
                        )
                        gx = max(
                            0,
                            min(b[0] for b in peers)
                            - border
                            - (label if project.template.label_side == "left" else 0),
                        )
                        gy = max(
                            0,
                            min(b[1] for b in peers) - border - heading - project.template.row_gap,
                        )
                        gr = min(
                            rendered.width,
                            max(b[2] for b in peers)
                            + border
                            + (label if project.template.label_side == "right" else 0),
                        )
                        gb = min(
                            rendered.height,
                            max(b[3] for b in peers) + border + project.template.row_gap,
                        )
                        regions.append(
                            {
                                "rowId": item["row_id"],
                                "sourceLaneRange": item.get("source_lane_range"),
                                "sourceToOutput": item.get("source_to_output"),
                                "groupBounds": {
                                    "x": gx,
                                    "y": gy,
                                    "width": gr - gx,
                                    "height": gb - gy,
                                },
                                "displayLine": item.get("display_line"),
                                "sourceRoi": {
                                    "x": item["roi"]["x0"],
                                    "y": item["roi"]["y0"],
                                    "width": item["roi"]["x1"] - item["roi"]["x0"],
                                    "height": item["roi"]["y1"] - item["roi"]["y0"],
                                }
                                if item.get("roi")
                                else None,
                                "x": box[0],
                                "y": box[1],
                                "width": box[2] - box[0],
                                "height": box[3] - box[1],
                            }
                        )
        cells = [cell_state(c) for c in view.analysis.result_view.cells]
        rows: list[dict[str, object]] = []
        for row in project.rows:
            results = [cell for cell in cells if cell["rowId"] == row.row_id]
            reasons = list(dict.fromkeys(str(cell["reason"]) for cell in results if cell["reason"]))
            roi = row.roi
            rows.append(
                {
                    "id": row.row_id,
                    "sourceId": row.source.sha256 if row.source else "",
                    "name": row.filename,
                    "fig": row.figure,
                    "protein": row.protein,
                    "notes": row.notes,
                    "width": row.width,
                    "bitDepth": row.bit_depth,
                    "height": row.height,
                    "roi": {"x": roi.x0, "y": roi.y0, "width": roi.width, "height": roi.y1 - roi.y0}
                    if roi
                    else None,
                    "lanes": row.lane_count,
                    "emptyLanes": list(row.empty_lanes),
                    "reviewed": row.reviewed,
                    "cropStatus": "ready"
                    if row.roi and row_is_ready(project, row)
                    else "pending"
                    if row.roi
                    else "failed",
                    "preview": self._images.get(row.source.sha256)
                    if row.source and source_counts[row.source.sha256] == 1
                    else None,
                    "reason": "；".join(reasons) or ("尚未定位裁剪区域" if not roi else "等待复核"),
                    "status": "valid"
                    if results and all(c["status"] == "valid" for c in results)
                    else "pending_review"
                    if roi
                    else "not_detected",
                    "results": results,
                }
            )
        return {
            "sessionEpoch": self.session_epoch,
            "sourcePreviews": {
                key: value for key, value in self._images.items() if source_counts[key] > 1
            },
            "projectId": project.project_id,
            "revision": view.generation,
            "projectName": project.name,
            "intake": intake,
            "canRetryLocation": not self.host.retry_location_button.isHidden(),
            "busy": self.host.operation_busy,
            "status": self._error or view.status.text(),
            "selectedId": selected.row_id if selected else "",
            "rows": rows,
            "cells": cells,
            "quant": quant_snapshot(self.host, project),
            "montage": montage,
            "montageRegions": regions,
            "montageWidth": montage_width,
            "montageHeight": montage_height,
            "autoCompletedKey": self._completed_key,
            "outputPath": self.host.automatic.last_output_path,
            "sourceDiscovery": {
                **json.loads(self.host.automatic.discovery_report),
                "id": sha256(self.host.automatic.discovery_report).hexdigest(),
            }
            if self.host.automatic.discovery_report
            else None,
        }

    @Slot()
    def publish(self) -> None:
        if self.host.resources_closed:
            self.timer.stop()
            return
        try:
            if self._pending_source and not self.host.operation_busy and not self.host.is_closing:
                project_id, row_id = self._pending_source
                self._pending_source = None
                if self.host.view.project_identity == project_id:
                    self.host.select_source(row_id)
            progress = json.dumps(
                {
                    "busy": self.host.operation_busy,
                    "status": self._error or self.host.view.status.text(),
                    "progress": self.host.quant_progress,
                },
                ensure_ascii=False,
            )
            if progress != getattr(self, "_previous_progress", ""):
                self._previous_progress = progress
                self.progressChanged.emit(progress)
            if self._quant_overview and not self.host.operation_busy and not self.host.is_closing:
                project_id, row_id = self._quant_overview
                self._quant_overview = None
                current = self.host.view.project()
                selected = self.host.view.selected_row()
                if (
                    current.project_id == project_id
                    and selected
                    and selected.row_id == row_id
                    and self.host.view.rendered_preview is None
                ):
                    self.host.compose()
            view = self.host.view
            key = (
                view.presentation_key,
                id(self.host.project_results),
                id(view.analysis.result_view.cells),
                id(view.source_preview),
                view.preview_label.full_pixmap.cacheKey(),
                self.host.operation_busy,
                self.host.retry_location_button.isHidden(),
                self.host.automatic.last_output_path,
                self.host.automatic.discovery_report,
                self._completed_key,
                self._error,
            )
            if self._previous and key == self._published_key:
                return
            state = json.dumps(self.snapshot(), ensure_ascii=False, allow_nan=False)
            self._published_key = key
        except ValueError:
            return  # An incomplete native advanced edit is not a replacement project.
        if state != self._previous:
            self._previous = state
            self.stateChanged.emit(state)

    @Slot(str, str)
    def request(self, action: str, payload: str = "{}") -> None:
        try:
            limit = (
                262144
                if action in {"intake_plan", "intake_assign"}
                else 32768
                if action == "quant_target"
                else 4096
            )
            if len(payload) > limit:
                raise ValueError("操作参数过长")
            parsed: object = json.loads(payload)
            if not isinstance(parsed, dict):
                raise ValueError("无效操作参数")
            data = cast(dict[str, object], parsed)
            if action in {"state", "refresh"}:
                self._previous = ""
            elif action == "cancel":
                self._quant_overview = None
                self.host.cancel()
            elif self.host.is_closing or (
                self.host.operation_busy and action not in {"select", "quant_select"}
            ):
                raise ValueError("当前任务仍在处理中，请稍候或取消")
            elif isinstance(self.host.view.project(), WBIntakeProject) and action not in {
                "intake_plan",
                "intake_assign",
                "intake_confirm",
                "intake_import_folder",
                "open_project",
                "retry_location",
            }:
                raise ValueError("仪器导入项目当前仅支持清单与原图分配；后续裁剪流程尚未接通")
            elif action in {"intake_plan", "intake_assign", "intake_confirm"}:
                apply_intake_command(self, action, data)
            elif action in {
                "import",
                "quant_import",
                "import_folder",
                "open_project",
                "retry_location",
                "intake_import_folder",
            }:
                self.choose(action)
            elif action == "include_folder_source":
                self.host.automatic.include_discovered_source(
                    data.get("index"), data.get("reportId")
                )
            elif action in {"select", "quant_select"}:
                rows = self.host.view.project().rows
                index = next((i for i, row in enumerate(rows) if row.row_id == data.get("id")), -1)
                if index < 0:
                    raise ValueError("原图已改变，请重新选择")
                if (
                    action == "quant_select"
                    and data.get("overview") is True
                    and not isinstance(self.host.view.project(), WBPartitionProject)
                ):
                    self._quant_overview = (self.host.view.project().project_id, rows[index].row_id)
                else:
                    self._quant_overview = None
                previous_index = self.host.view.table.currentRow()
                self.host.view.table.setCurrentCell(index, 0)
                if self.host.operation_busy:
                    self._pending_source = (self.host.view.project_identity, rows[index].row_id)
                elif previous_index == index:
                    self.host.select_source(rows[index].row_id)
            elif action == "quant_edit":
                self._edit_quant(data)
            elif action in {
                "quant_new_group",
                "quant_rename",
                "quant_move_row",
                "quant_merge_group",
                "quant_band",
                "quant_history",
                "quant_fig",
            }:
                self.manual_commands.run(action, data)
            elif action == "return_crop":
                project = self.host.view.project()
                row = self.host.view.selected_row()
                if (
                    row is None
                    or row.source is None
                    or data.get("projectId") != project.project_id
                    or data.get("id") != row.row_id
                    or data.get("sourceId") != row.source.sha256
                    or type(data.get("revision")) is not int
                    or data.get("revision") != self.host.view.generation
                    or type(data.get("locate", False)) is not bool
                ):
                    raise ValueError("原图或裁剪已改变，请重新审核后回存")
                self.host.return_selected_crop(locate=data.get("locate", False) is True)
            elif action == "quant_target":
                self._configure_quant_target(data)
            elif action in {"quant_review_group", "quant_reset_group"}:
                project = self.host.view.project()
                selected = self.host.view.selected_row()
                if (
                    selected is None
                    or data.get("projectId") != project.project_id
                    or data.get("figure") != selected.figure
                    or type(data.get("revision")) is not int
                    or data.get("revision") != self.host.view.generation
                ):
                    raise ValueError("当前分组或参数已改变，请重新审核")
                if action == "quant_reset_group":
                    self.manual_commands.remember()
                    self.host.reset_quant_group(selected.row_id)
                else:
                    self.manual_commands.remember()

                    def next_group() -> None:
                        current = self.host.view.project()
                        current_row = self.host.view.selected_row()
                        if (
                            current.project_id != project.project_id
                            or current_row is None
                            or current_row.figure != selected.figure
                        ):
                            return  # Browsing another group while saving is a newer intent.
                        figures = list(current.figure_order)
                        index = figures.index(selected.figure)
                        following = figures[index + 1 :] + figures[:index]
                        target = next(
                            (f for f in following if not quant_group_reviewed(current, f)), None
                        )
                        if target:
                            row_index = next(
                                i for i, r in enumerate(current.rows) if r.figure == target
                            )
                            self.host.view.table.setCurrentCell(row_index, 0)
                            self.host.select_source(current.rows[row_index].row_id)
                        else:
                            self.host.view.status.setText("全部分组已审核并保存")

                    self.host.save(
                        after=next_group,
                        transform=lambda current: confirm_quant_group(current, selected.figure),
                    )
            elif action == "quant_group":
                selected = self.host.view.selected_row()
                if selected is None or selected.figure != data.get("figure"):
                    raise ValueError("当前 Fig 组已改变，请重新选择")
                members = tuple(
                    r
                    for r in self.host.view.project().rows
                    if r.figure == selected.figure and r.source
                )
                if (
                    not members
                    or len({r.lane_count for r in members}) != 1
                    or any(not r.roi for r in members)
                ):
                    raise ValueError("组内各蛋白行须有裁剪且泳道数一致，才能按列对应定量")
                self.host.analyze_project(
                    row_ids=tuple(r.row_id for r in members),
                    after=None
                    if isinstance(self.host.view.project(), WBPartitionProject)
                    else self.host.compose,
                )
            elif action == "quant_auto":
                row = self.host.view.selected_row()
                if row is None or row.row_id != data.get("id"):
                    raise ValueError("当前原图已改变，请重新选择")
                self.host.automatic.analyze(row_ids=(row.row_id,), publish_output=False)
            elif action == "quant_export":
                format_name = data.get("format")
                if format_name not in {"xlsx", "csv"}:
                    raise ValueError("请选择Excel或CSV格式")
                self.choose("quant_export_" + str(format_name))
            elif action == "set_lanes":
                row = self.host.view.selected_row()
                if (
                    row is None
                    or data.get("id") != row.row_id
                    or not row.source
                    or data.get("sourceId") != row.source.sha256
                ):
                    raise ValueError("当前原图已改变，请重新调整")
                count = data.get("n")
                if type(count) is not int or not 1 <= count <= 96:
                    raise ValueError("泳道数须为1–96的整数")
                self.host.view.set_crop_lane_count(count)
            elif action in {"crop", "confirm"}:
                row = self.host.view.selected_row()
                if row is None or data.get("id") != row.row_id:
                    raise ValueError("当前原图已改变，请重新调整")
                if action == "crop":
                    if not row.source or data.get("sourceId") != row.source.sha256:
                        raise ValueError("原图身份已改变，请重新调整")
                    roi = data.get("roi")
                    if not isinstance(roi, dict):
                        raise ValueError("裁剪参数缺失")
                    coords = cast(dict[str, object], roi)
                    values = [coords.get(k) for k in ("x", "y", "width", "height")]
                    if any(type(value) is not int for value in values):
                        raise ValueError("裁剪必须采用原图整数像素")
                    x, y, width, height = cast(list[int], values)
                    if not (
                        0 <= x < x + width <= row.width
                        and 0 <= y < y + height <= row.height
                        and width >= row.lane_count
                    ):
                        raise ValueError("裁剪超出原图或泳道宽度不足")
                    self.host.view.canvas.roi_drawn.emit((x, y, x + width, y + height))
                else:
                    self.host.view.confirm_selected()
                    rows = self.host.view.project().rows
                    current = next(i for i, item in enumerate(rows) if item.row_id == row.row_id)
                    following = list(range(current + 1, len(rows))) + list(range(current))
                    next_index = next(
                        (i for i in following if rows[i].source and not rows[i].reviewed), None
                    )
                    if next_index is not None:
                        self.host.view.table.setCurrentCell(next_index, 0)
            elif action == "undo":
                self.host.view.undo_review()
            elif action == "redo":
                self.host.view.redo_review()
            elif action == "reanalyze":
                self.host.automatic.analyze()
            elif action == "compose":
                self.host.compose()
            elif action == "export":
                self.host.automatic.publish_default()
            elif action == "open_output":
                self.host.output_button.click()
            elif action == "advanced":
                section = data.get("section")
                if section == "analysis":
                    raise ValueError("请使用工作台中的灰度定量页")
                if section not in {"metadata", "ocr", "normalization", "template", "analysis"}:
                    raise ValueError("未知高级工具")
                self.host.view.show_section(str(section))
                self.host.show()
                self.host.raise_()
            else:
                raise ValueError("未知操作")
            self._error = ""
        except (ValueError, TypeError) as error:
            self._error = str(error)
        self.publish()

    def _configure_quant_target(self, data: dict[str, object]) -> None:
        project = self.host.view.project()
        row = self.host.view.selected_row()
        if (
            data.get("projectId") != project.project_id
            or row is None
            or not row.source
            or data.get("id") != row.row_id
            or data.get("sourceId") != row.source.sha256
            or type(data.get("revision")) is not int
            or data.get("revision") != self.host.view.generation
        ):
            raise ValueError("当前项目、原图或参数已改变，请重新选择测量区域")
        roi = data.get("roi")
        if not isinstance(roi, dict):
            raise ValueError("请先在原图上选择测量区域")
        coords = cast(dict[str, object], roi)
        values = [coords.get(key) for key in ("x", "y", "width", "height")]
        if any(type(value) is not int for value in values):
            raise ValueError("测量区域须使用原图整数像素")
        x, y, width, height = cast(list[int], values)
        if not (0 <= x < x + width <= row.width and 0 <= y < y + height <= row.height):
            raise ValueError("测量区域超出原图")
        count, polarity, empty = data.get("n"), data.get("polarity"), data.get("emptyLanes")
        if (
            type(count) is not int
            or polarity not in ("dark", "light")
            or not isinstance(empty, list)
        ):
            raise ValueError("请指定整数泳道数、信号极性及排除泳道")
        raw_empty = cast(list[object], empty)
        if any(type(value) is not int for value in raw_empty):
            raise ValueError("排除泳道须为整数编号")
        reset = data.get("resetBounds", False)
        if type(reset) is not bool:
            raise ValueError("重置边界须为明确布尔值")
        raw_lanes = data.get("laneRois", [])
        measurement_mode = data.get("measurementMode", "peaks")
        if (
            not isinstance(raw_lanes, list)
            or len(cast(list[object], raw_lanes)) > 96
            or measurement_mode not in ("peaks", "smear")
        ):
            raise ValueError("泳道列表或测量模式无效")
        lane_rois: list[LaneROI] = []
        for index, raw_box in enumerate(cast(list[object], raw_lanes), 1):
            if not isinstance(raw_box, dict):
                raise ValueError("泳道坐标无效")
            box = cast(dict[str, object], raw_box)
            coords = [box.get(key) for key in ("x", "y", "width", "height")]
            if any(type(value) is not int for value in coords):
                raise ValueError("泳道须使用整数原图坐标")
            lx, ly, lw, lh = cast(list[int], coords)
            lane_rois.append(LaneROI(f"{row.row_id}:{index:02d}", lx, ly, lx + lw, ly + lh))
        target = ManualQuantTarget(
            row.source.sha256,
            project.revision,
            LaneROI(row.row_id, x, y, x + width, y + height),
            count,
            polarity,
            tuple(cast(list[int], raw_empty)),
            reset,
            tuple(lane_rois),
            measurement_mode,
        )
        self.host.analyze_manual_target(target)

    def _edit_quant(self, data: dict[str, object]) -> None:
        from wb_tool.api import update_quant_lane

        project = self.host.view.project()
        row = self.host.view.selected_row()
        if (
            not isinstance(project, WBAnalysisProject)
            or row is None
            or not row.source
            or data.get("id") != row.row_id
            or data.get("sourceId") != row.source.sha256
            or type(data.get("revision")) is not int
            or data.get("revision") != self.host.view.generation
        ):
            raise ValueError("原图或参数已改变，请等待刷新后重新调整")
        plan = next((p for p in project.analyses if p.row_id == row.row_id), None)
        lane = data.get("lane")
        if plan is None or type(lane) is not int or not 1 <= lane <= len(plan.request.lanes):
            raise ValueError("泳道已改变，请重新选择")
        annotation = plan.request.lanes[lane - 1]
        band_id = data.get("bandId") or "target"
        if not isinstance(band_id, str) or not any(b.band_id == band_id for b in annotation.bands):
            raise ValueError("当前目标条带不存在")
        roi = None
        bounds = None
        baseline = None
        if "roi" in data:
            box = data["roi"]
            if not isinstance(box, dict):
                raise ValueError("泳道范围缺失")
            fields = cast(dict[str, object], box)
            coords = [fields.get(k) for k in ("x", "y", "width", "height")]
            if any(type(v) is not int for v in coords):
                raise ValueError("泳道须使用原图整数坐标")
            x, y, width, height = cast(list[int], coords)
            roi = LaneROI(annotation.roi.lane_id, x, y, x + width, y + height)
        elif any(k in data for k in ("start", "end", "baselineStart", "baselineEnd")):
            current_band = next(b for b in annotation.bands if b.band_id == band_id)
            current_bounds, current_baseline = current_band.bounds, current_band.baseline
            loaded = next(
                (
                    r
                    for r in self.host.project_results
                    if plan.run and r.run_id == plan.run.run_id and r.result.request == plan.request
                ),
                None,
            )
            if loaded:
                measured_lane = next(
                    (r for r in loaded.result.lanes if r.roi == annotation.roi), None
                )
                measured = (
                    next(
                        (
                            b.measurement
                            for b in measured_lane.bands
                            if b.annotation.band_id == band_id
                        ),
                        None,
                    )
                    if measured_lane
                    else None
                )
                if measured:
                    current_bounds, current_baseline = measured.bounds, measured.baseline
            start = data.get("start", current_bounds.left if current_bounds else None)
            end = data.get("end", current_bounds.right if current_bounds else None)
            if type(start) is not int or type(end) is not int:
                raise ValueError("积分边界须为整数像素")
            bounds = BandBounds(start, end)
            raw = [
                data.get(
                    "baselineStart", current_baseline.left_value if current_baseline else None
                ),
                data.get("baselineEnd", current_baseline.right_value if current_baseline else None),
            ]
            if any(v is not None for v in raw):
                if any(
                    type(v) not in (int, float) or not math.isfinite(float(cast(float, v)))
                    for v in raw
                ):
                    raise ValueError("封底端点须为有限数值")
                baseline = Baseline(float(cast(float, raw[0])), float(cast(float, raw[1])))
        else:
            raise ValueError("缺少泳道范围或积分边界")
        updated = update_quant_lane(
            project,
            row.row_id,
            annotation.roi.lane_id,
            roi=roi,
            bounds=bounds,
            baseline=baseline,
            band_id=band_id,
        )
        if updated is project:
            return
        self.manual_commands.remember()
        self.host.view.set_project(updated)
        self.host.view.generation += 1
        self.manual_commands.bind()
        if roi is not None:
            self.host.replan_quant_lane(row.row_id)
        else:
            self.host.analyze_project(row_ids=(row.row_id,))
