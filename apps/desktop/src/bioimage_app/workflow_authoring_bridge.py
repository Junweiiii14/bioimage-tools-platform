"""Native choices and view receipts for the existing workbench's workflow editor."""

import json
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from PySide6.QtCore import QObject, QSettings, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QWidget

from bioimage_app.workflow_authoring_models import AuthoringProjection
from bioimage_app.workflow_authoring_session import WorkflowAuthoringSession
from bioimage_app.workflow_batch_session import WorkflowBatchStatus


class WorkflowAuthoringBridge(QObject):
    documentChanged = Signal(str, str, str, str)
    progressChanged = Signal(str)
    activityChanged = Signal(bool, bool)
    workspaceChanged = Signal(str)
    revealRequested = Signal()
    draftDiscarded = Signal()
    idle = Signal()

    def __init__(
        self, window: QWidget, unavailable: Callable[[], bool], settings: QSettings | None = None
    ) -> None:
        super().__init__(window)
        self._settings = settings
        self._window = window
        self._unavailable = unavailable
        self._session: WorkflowAuthoringSession | None = None
        self._switch_to: tuple[str, str, bytes | None] | None = None
        self._opening_token = ""
        self._dirty = False

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def busy(self) -> bool:
        status = self._session.batch_status if self._session is not None else None
        return self._switch_to is not None or (
            self._session is not None
            and (
                self._session.pending
                or (self._session.running and (status is None or status.state != "paused"))
            )
        )

    @property
    def resources_closed(self) -> bool:
        return self._session is None and self._switch_to is None

    @property
    def projection(self) -> AuthoringProjection | None:
        return self._session.projection if self._session is not None else None

    @Slot(bool)
    def setDirty(self, dirty: bool) -> None:
        self._dirty = dirty

    def discard_draft(self) -> None:
        self._dirty = False
        self.draftDiscarded.emit()

    def reveal(self) -> None:
        self.revealRequested.emit()

    @Slot(str, str)
    def command(self, token: str, payload: str) -> None:
        try:
            if len(payload) > 1048576 or len(token) > 80:
                raise ValueError("工作流请求超过容量预算")
            if self._unavailable():
                raise ValueError("当前 WB 会话仍在处理中，请等待或取消后再操作工作流")
            if self._session is None:
                raise ValueError("请先新建或打开工作流项目")
            self._session.request(token, payload.encode("utf-8"))
        except (ValueError, RuntimeError) as error:
            self.documentChanged.emit(token, "", "", str(error))

    @Slot(str, str, str)
    def choose(self, token: str, action: str, payload: str) -> None:
        try:
            if len(payload) > 4096 or len(token) > 80:
                raise ValueError("文件选择参数超过容量预算")
            if self.busy:
                raise ValueError("请先完成或取消当前批次，再切换输入或项目")
            if self._dirty:
                raise ValueError("请先保存当前草稿，或撤销未保存修改")
            raw: object = json.loads(payload)
            if not isinstance(raw, dict):
                raise ValueError("工作流选项必须是对象")
            options = cast(dict[str, object], raw)
            if action == "open_project":
                path = QFileDialog.getExistingDirectory(self._window, "打开工作流项目目录")
                if path:
                    self._switch(token, path, None)
                else:
                    self.documentChanged.emit(token, "cancelled", "", "")
                return
            if action in ("new_original", "new_example", "new_template", "new_nuclei", "new_bca"):
                source = ""
                record = ""
                tool = {"new_nuclei": "nuclei", "new_bca": "bca"}.get(action, "wb")
                template = ""
                if action == "new_template":
                    template, _filter = QFileDialog.getOpenFileName(
                        self._window, "选择实验室工作流模板", "", "工作流模板 (*.json)"
                    )
                    if not template:
                        self.documentChanged.emit(token, "cancelled", "", "")
                        return
                    from bioimage_app.workflow_template import load_workflow_template

                    with Path(template).open("r", encoding="utf-8") as stream:
                        definition = load_workflow_template(stream.read(1048577)).definition
                    tool = {"nuclei-research": "nuclei", "bca-research": "bca"}.get(
                        definition.workflow_id, "wb"
                    )
                if action != "new_example":
                    source, _filter = QFileDialog.getOpenFileName(
                        self._window,
                        "选择原始输入",
                        "",
                        "单板长 CSV (*.csv)" if tool == "bca" else "原始图像 (*.tif *.tiff)",
                    )
                    if not source:
                        self.documentChanged.emit(token, "cancelled", "", "")
                        return
                if tool == "bca":
                    record, _filter = QFileDialog.getOpenFileName(
                        self._window, "选择对应板记录", "", "板记录 (*.json)"
                    )
                    if not record:
                        self.documentChanged.emit(token, "cancelled", "", "")
                        return
                parent = QFileDialog.getExistingDirectory(
                    self._window, "选择新工作流项目的保存位置"
                )
                if not parent:
                    self.documentChanged.emit(token, "cancelled", "", "")
                    return
                path = Path(parent) / (
                    "工作流-" + datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:6]
                )
                values: dict[str, object] = {
                    "operation": "initialize",
                    "document_id": uuid4().hex,
                    "tool": tool,
                    "record_path": record,
                }
                if action == "new_example":
                    values["validation_cases"] = [options.get("validation", "triangle_u16")]
                else:
                    values.update(
                        source_paths=[source],
                        polarity=options.get("polarity", "dark"),
                        template_path=template,
                    )
                    if action == "new_original":
                        values["lane_count"] = options.get("lane_count")
                self._switch(token, str(path), json.dumps(values).encode("utf-8"))
                return
            if self._session is None or self._session.projection is None:
                raise ValueError("请先新建或打开工作流项目")
            project = self._session.projection.project
            values = {"document_id": project.document_id}
            if action == "export_template":
                destination, _filter = QFileDialog.getSaveFileName(
                    self._window, "保存为新的实验室模板", "实验室流程.json", "工作流模板 (*.json)"
                )
                if not destination:
                    self.documentChanged.emit(token, "cancelled", "", "")
                    return
                values.update(operation="export", destination=destination)
            elif action in ("bind_sources", "bind_example"):
                values.update(operation="bind", previous_revision=project.revision)
                if action == "bind_sources" and project.tool != "wb":
                    source, _filter = QFileDialog.getOpenFileName(
                        self._window,
                        "选择新研究输入",
                        "",
                        "CSV (*.csv)" if project.tool == "bca" else "原始图像 (*.tif *.tiff)",
                    )
                    if not source:
                        self.documentChanged.emit(token, "cancelled", "", "")
                        return
                    record = ""
                    if project.tool == "bca":
                        record, _filter = QFileDialog.getOpenFileName(
                            self._window, "选择对应板记录", "", "板记录 (*.json)"
                        )
                        if not record:
                            self.documentChanged.emit(token, "cancelled", "", "")
                            return
                    values.update(source_paths=[source], record_path=record, tool=project.tool)
                elif action == "bind_sources":
                    sources, _filter = QFileDialog.getOpenFileNames(
                        self._window,
                        "绑定下一批原始 TIFF（最多16个）",
                        "",
                        "原始图像 (*.tif *.tiff)",
                    )
                    if not sources:
                        self.documentChanged.emit(token, "cancelled", "", "")
                        return
                    values["source_paths"] = sources
                else:
                    values["validation_cases"] = [options.get("validation", "triangle_u8")]
            else:
                raise ValueError("未知工作流文件操作")
            self.command(token, json.dumps(values, ensure_ascii=False))
        except (ValueError, OSError, RuntimeError) as error:
            self.documentChanged.emit(token, "", "", str(error))

    def _switch(self, token: str, path: str, initialization: bytes | None) -> None:
        if self._unavailable():
            raise ValueError("当前 WB 会话仍在处理中，请等待或取消后再打开工作流")
        self._switch_to = (token, path, initialization)
        if self._session is not None:
            self._session.close()
        else:
            self._start_switch()

    def _start_switch(self) -> None:
        from bioimage_app.wb_workflow_host import wb_workflow_registry

        assert self._switch_to is not None
        token, path, initialization = self._switch_to
        self._switch_to = None
        from tool_contracts.api import ExecutionPlan

        from bioimage_app.bca_workflow_host import BcaHost
        from bioimage_app.nuclei_workflow_host import NucleiHost
        from bioimage_app.workflow_preparation import WorkflowHostModule

        config = (
            str(self._settings.value("nuclei_worker_v1", "")) if self._settings else "",
            str(self._settings.value("nuclei_model_v1", "")) if self._settings else "",
        )

        def registry(plan: ExecutionPlan) -> tuple[WorkflowHostModule, ...]:
            if plan.workflow_id == "nuclei-research":
                return NucleiHost(*config).registry(plan)
            if plan.workflow_id == "bca-research":
                return BcaHost().registry(plan)
            return wb_workflow_registry(plan)

        session = WorkflowAuthoringSession(registry, self, nuclei_configuration=config)
        self._session = session
        self._opening_token = token

        def document(receipt: str, operation: str, data: str, error: str) -> None:
            if self._session is not session:
                return
            current_token = self._opening_token or receipt
            self._opening_token = ""
            self.documentChanged.emit(current_token, operation, data, error)
            if operation == "open" and session.projection is not None:
                path = session.projection.opened_path
                if path and not QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
                    self.documentChanged.emit(
                        current_token, "", "", "无法打开成果，请检查本机文件关联"
                    )

        def progress(status: WorkflowBatchStatus) -> None:
            if self._session is session:
                self.progressChanged.emit(json.dumps(asdict(status), ensure_ascii=False))

        def activity(pending: bool, running: bool) -> None:
            if self._session is session:
                self.activityChanged.emit(pending, running)

        def finished() -> None:
            if self._session is not session:
                return
            self._session = None
            session.deleteLater()
            if self._switch_to is not None:
                self._start_switch()
            else:
                self.idle.emit()

        session.documentChanged.connect(document)
        session.progressChanged.connect(progress)
        session.activityChanged.connect(activity)
        session.finished.connect(finished)
        self.workspaceChanged.emit(path)
        if initialization is None:
            session.reopen(path)
        else:
            session.create(path, initialization)

    @Slot(str)
    def control(self, action: str) -> None:
        if self._session is None:
            return
        if action == "resume" and self._unavailable():
            self.documentChanged.emit("", "", "", "请先完成或取消当前 WB 任务，再继续工作流")
            return
        if action == "pause":
            accepted = self._session.pause()
        elif action == "resume":
            accepted = self._session.resume()
        elif action == "cancel":
            accepted = self._session.cancel()
        else:
            accepted = False
        if not accepted:
            self.documentChanged.emit("", "", "", "当前状态不能执行该控制，请等待实际暂停或结束")

    def cancel(self) -> None:
        if self._session is not None:
            self._session.cancel()

    def close(self) -> None:
        self._switch_to = None
        if self._session is not None:
            self._session.close()
        else:
            self.idle.emit()
