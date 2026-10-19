"""Local web presentation adapter; original-pixel work remains in the WB host."""

import base64
import json
from collections.abc import Callable
from typing import cast

from PySide6.QtCore import QBuffer, QIODevice, QObject, QTimer, Signal, Slot
from PySide6.QtGui import QImage, QImageWriter
from wb_tool.api import ProjectTableCell

from bioimage_app.figure_window import FigureProjectWindow

_CROP_EDIT_CONTRACT = "legacy_crop_edit@1"


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

    def __init__(
        self,
        host: FigureProjectWindow,
        choose: Callable[[str], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.host = host
        self.session_epoch = 0
        self.choose = choose
        self._previous = ""
        self._images: dict[str, str | None] = {}
        self._montage_key = 0
        self._montage: str | None = None
        self._error = ""
        self.timer = QTimer(self)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.publish)
        self.timer.start()

    def snapshot(self) -> dict[str, object]:
        view = self.host.view
        project = view.project()
        selected = view.selected_row()
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
        self._images = {key: value for key, value in self._images.items() if key in live_sources}
        pixmap = view.preview_label.full_pixmap
        if pixmap.cacheKey() != self._montage_key:
            self._montage_key = pixmap.cacheKey()
            self._montage = image_url(pixmap.toImage())
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
                    "width": row.width,
                    "bitDepth": row.bit_depth,
                    "height": row.height,
                    "roi": {"x": roi.x0, "y": roi.y0, "width": roi.width, "height": roi.y1 - roi.y0}
                    if roi
                    else None,
                    "lanes": row.lane_count,
                    "reviewed": row.reviewed,
                    "preview": self._images.get(row.source.sha256) if row.source else None,
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
            "projectName": project.name,
            "projectId": project.project_id,
            "sessionEpoch": self.session_epoch,
            "revision": view.generation,
            "cropEditContract": _CROP_EDIT_CONTRACT,
            "busy": self.host.operation_busy,
            "status": self._error or view.status.text(),
            "selectedId": selected.row_id if selected else "",
            "rows": rows,
            "cells": cells,
            "montage": self._montage,
            "outputPath": self.host.automatic.last_output_path,
        }

    @Slot()
    def publish(self) -> None:
        if self.host.resources_closed:
            self.timer.stop()
            return
        try:
            state = json.dumps(self.snapshot(), ensure_ascii=False, allow_nan=False)
        except ValueError:
            return  # An incomplete native advanced edit is not a replacement project.
        if state != self._previous:
            self._previous = state
            self.stateChanged.emit(state)

    @Slot(str, str)
    def request(self, action: str, payload: str = "{}") -> None:
        try:
            if len(payload) > 4096:
                raise ValueError("操作参数过长")
            parsed: object = json.loads(payload)
            if not isinstance(parsed, dict):
                raise ValueError("无效操作参数")
            data = cast(dict[str, object], parsed)
            if action in {"state", "refresh"}:
                self._previous = ""
            elif action == "cancel":
                self.host.cancel()
            elif self.host.operation_busy or self.host.is_closing:
                raise ValueError("当前任务仍在处理中，请稍候或取消")
            elif action in {"import", "import_folder", "open_project"}:
                self.choose(action)
            elif action == "select":
                rows = self.host.view.project().rows
                index = next((i for i, row in enumerate(rows) if row.row_id == data.get("id")), -1)
                if index < 0:
                    raise ValueError("原图已改变，请重新选择")
                self.host.view.table.setCurrentCell(index, 0)
                if not self.host.operation_busy:
                    self.host.select_source(rows[index].row_id)
            elif action in {"crop", "confirm"}:
                self._validate_crop_edit(data)
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

    def _validate_crop_edit(self, data: dict[str, object]) -> None:
        project = self.host.view.project()
        row = self.host.view.selected_row()
        if (
            data.get("cropEditContract") != _CROP_EDIT_CONTRACT
            or data.get("projectId") != project.project_id
            or type(data.get("sessionEpoch")) is not int
            or data.get("sessionEpoch") != self.session_epoch
            or type(data.get("revision")) is not int
            or data.get("revision") != self.host.view.generation
            or row is None
            or row.source is None
            or data.get("id") != row.row_id
            or data.get("sourceId") != row.source.sha256
        ):
            raise ValueError("原图身份或裁剪已改变，请重新调整并复核")
