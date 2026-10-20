"""Same local HTML document in browser preview and Qt desktop shell."""

import json
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import cast

from PySide6.QtCore import QSettings, Qt, QTimer, QUrl, Slot
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow
from wb_tool.api import WBIntakeProject

from bioimage_app.figure_window import FigureProjectWindow
from bioimage_app.project_navigation import MODES, ProjectNavigation
from bioimage_app.shortcuts import WorkbenchShortcuts
from bioimage_app.source_origins import SourceOrigins
from bioimage_app.web_bridge import WorkbenchBridge


class LocalAssetFilter(QWebEngineUrlRequestInterceptor):
    def __init__(self, root: Path, parent: QWebEnginePage) -> None:
        super().__init__(parent)
        self.root = root.resolve()

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        url = info.requestUrl()
        allowed = url.scheme() == "data" or url.toString() == "qrc:///qtwebchannel/qwebchannel.js"
        if url.isLocalFile():
            allowed = Path(url.toLocalFile()).resolve().is_relative_to(self.root)
        info.block(not allowed)


class LocalWorkbenchPage(QWebEnginePage):
    def __init__(self, index: Path, parent: QWebEngineView) -> None:
        self.local_profile = QWebEngineProfile(QApplication.instance())
        super().__init__(self.local_profile, parent)
        self.destroyed.connect(self.local_profile.deleteLater)
        self.index = index.resolve()

    def acceptNavigationRequest(
        self, url: QUrl | str, navigation_type: QWebEnginePage.NavigationType, is_main_frame: bool
    ) -> bool:
        url = QUrl(url)
        return url.isLocalFile() and Path(url.toLocalFile()).resolve() == self.index


class AdvancedHost(FigureProjectWindow):
    shutdown_requested = False

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self.shutdown_requested:
            self.hide()
            event.ignore()
        else:
            super().closeEvent(event)


class WebWorkbenchWindow(QMainWindow):
    def __init__(
        self, *, asset_directory: Path | None = None, settings: QSettings | None = None
    ) -> None:
        super().__init__()
        channel = os.environ.get("BIOIMAGE_RELEASE_CHANNEL")
        candidate = channel in {
            "candidate",
            "win10-test",
            "wb-execution-test",
            "wb-grouped-intake-test",
        }
        self.setWindowTitle("BioImage WB · 候选版" if candidate else "BioImage · WB 工作台")
        self.setWindowIcon(QIcon(str(Path(__file__).with_name("web_ui") / "bioimage.svg")))
        self.resize(1440, 940)
        settings_name = {
            "candidate": "Candidate",
            "win10-test": "Win10Test",
            "wb-execution-test": "E7Test",
            "wb-grouped-intake-test": "GroupedIntakeTest",
        }.get(channel or "", "Platform")
        self.settings = settings or QSettings("BioImageTools", settings_name)
        self.shortcuts = WorkbenchShortcuts(self.settings)
        self.navigation = ProjectNavigation(self.settings)
        self._stage = "idle"
        self._message = ""
        self._intent = "exit"
        self._continuation: Callable[[], None] | None = None
        self._exit_ready = False
        self._discard = False
        self._draft = False
        self._starting = False
        self._ready_project = ""
        self._target_mode = "quant"
        self._restore: dict[str, object] = {}
        self._last_open_path = ""
        self._route: dict[str, object] = {}
        self._route_number = 0
        self._since = time.monotonic()
        self._previous_session = ""
        self.host = AdvancedHost()
        self.host.source_origins = SourceOrigins(self.settings)
        self.host.setParent(self, Qt.WindowType.Window)
        self.host.automatic.crop_policy = "source_geometry@2"
        self.host.automatic.quant_policy = "anchored_background@1"
        self.host.closed.connect(self._backend_closed)
        self.host.workspace_opened.connect(self._workspace_ready)
        self.web = QWebEngineView(self)
        index = (asset_directory or Path(__file__).with_name("web_ui")) / "index.html"
        page = LocalWorkbenchPage(index, self.web)
        self.web.setPage(page)
        self.asset_filter = LocalAssetFilter(index.parent, page)
        page.profile().setUrlRequestInterceptor(self.asset_filter)
        page.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False
        )
        page.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
        )
        page.settings().setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False
        )
        self.channel = QWebChannel(page)
        self.bridge = WorkbenchBridge(self.host, self.choose, self)
        self.bridge.sessionRequested.connect(self._session_request)
        self.channel.registerObject("workbench", self.bridge)
        page.setWebChannel(self.channel)
        self.setCentralWidget(self.web)
        self.web.setUrl(QUrl.fromLocalFile(str(index.resolve())))
        self._closing = False
        self.session_timer = QTimer(self)
        self.session_timer.setInterval(150)
        self.session_timer.timeout.connect(self._poll_session)
        self.session_timer.start()

    def choose(self, action: str) -> None:
        if action in {"new_intake_folder", "intake_import_folder"}:
            directory = QFileDialog.getExistingDirectory(self, "选择仪器直接导出的 TIFF 文件夹")
            if directory:
                if action == "intake_import_folder" and self.host.workspace_path:
                    self.host.intake.import_folder(Path(directory))
                else:
                    self.start_from_images([Path(directory)], automatic=False, intake=True)
        elif action in {"import", "quant_import", "quant_import_folder"}:
            if action == "quant_import_folder":
                directory = QFileDialog.getExistingDirectory(self, "选择 TIFF 原图文件夹")
                if directory:
                    self._import_paths([Path(directory)], automatic=False)
                return
            paths, _ = QFileDialog.getOpenFileNames(
                self, "选择 WB 原图", "", "TIFF 原图 (*.tif *.tiff)"
            )
            if paths:
                self._import_paths(
                    [Path(path) for path in paths], automatic=action != "quant_import"
                )
        elif action == "retry_location":
            if self.host.retry_location_button.isHidden():
                raise ValueError("当前没有等待重新选择保存位置的项目")
            self._starting = True
            self._stage = "opening"
            self.host.retry_location_button.click()
        elif action in {"quant_export_xlsx", "quant_export_csv"}:
            extension = action.rsplit("_", 1)[-1]
            path, _ = QFileDialog.getSaveFileName(
                self,
                "导出灰度分析",
                "灰度分析." + extension,
                "Excel (*.xlsx)" if extension == "xlsx" else "CSV (*.csv)",
            )
            if path:
                self.host.export_project_table(path, quant=True)
        elif action == "import_folder":
            path = QFileDialog.getExistingDirectory(self, "选择 WB 原图文件夹")
            if path:
                if self.host.workspace_path:
                    self.host.automatic.import_directory(path)
                else:
                    self.start_from_images([Path(path)])
        elif action == "open_project":
            path = QFileDialog.getExistingDirectory(self, "打开已有 BioImage 项目")
            if path:
                self.open_project(path)

    def open_project(self, path: str) -> None:
        """Open persisted project data, rather than only its storage container."""
        if self.host.workspace_path:
            self._request_transition("open", lambda: self.open_project(path))
            return
        if self.host.operation_busy or self.host.is_closing:
            raise ValueError("当前任务仍在处理中，请稍候或取消")
        self._restore = self.navigation.read(path)
        self._last_open_path = path
        self._target_mode = str(self._restore.get("mode", "quant"))
        if self._target_mode not in MODES:
            self._target_mode = "quant"
        self._starting = True
        self._stage = "opening"
        self._message = "正在打开项目并校验原图与历史结果…"
        self.host.open_workspace(path)

    def _workspace_ready(self, _path: str) -> None:
        if self.host.documents.count() > 1:
            remembered = self._restore.get("projectId")
            index = self.host.documents.findData(remembered) if remembered else -1
            document_id = self.host.documents.itemData(index if index > 0 else 1)
            if isinstance(document_id, str) and document_id:
                self.host.load_document(document_id)

    def start_from_images(
        self, paths: list[Path], *, automatic: bool = True, intake: bool = False
    ) -> None:
        if self.host.workspace_path:
            self._request_transition(
                "new", lambda: self.start_from_images(paths, automatic=automatic, intake=intake)
            )
            return
        self._starting = True
        self._stage = "opening"
        self._message = "正在核验原图并创建独立项目…"
        self._target_mode = "intake" if intake else "layout" if automatic else "quant"
        self._restore = {}
        parent = str(self.settings.value("project_parent", ""))
        self.host.start_project_from_images(
            paths,
            project_parent=Path(parent) if parent else None,
            automatic=automatic,
            intake=intake,
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._exit_ready:
            event.accept()
            return
        event.ignore()
        self._request_transition("exit")

    def _check_close_failure(self) -> None:
        if self._closing and not self.host.is_closing and not self.host.resources_closed:
            self._closing = False
            self.host.shutdown_requested = False
            self._stage = "failed"
            self._message = "退出未完成：" + self.host.view.status.text()
            self.raise_()

    def _backend_closed(self) -> None:
        self.bridge.timer.stop()
        self.host.closed.disconnect(self._backend_closed)
        if self._intent == "exit":
            self.session_timer.stop()
            self._exit_ready = True
            self.web.stop()
            self.web.page().deleteLater()
            # Advanced editors belong to this host and must not keep the session alive.
            self.host.hide()
            for child in self.host.findChildren(QMainWindow):
                child.hide()
            QTimer.singleShot(0, self.close)
            return
        previous = self.host
        self.host = AdvancedHost()
        self.host.setParent(self, Qt.WindowType.Window)
        self.host.source_origins = SourceOrigins(self.settings)
        self.host.automatic.crop_policy = "source_geometry@2"
        self.host.automatic.quant_policy = "anchored_background@1"
        self.host.closed.connect(self._backend_closed)
        self.host.workspace_opened.connect(self._workspace_ready)
        self.bridge.replace_host(self.host)
        previous.deleteLater()
        self._closing = False
        self._starting = False
        self._ready_project = ""
        self._draft = False
        self._stage = "idle"
        self._route_number += 1
        self._route = {"token": self._route_number, "mode": "home"}
        continuation = self._continuation
        self._continuation = None
        self._publish_session()
        if continuation:
            QTimer.singleShot(0, continuation)

    def _import_paths(self, paths: list[Path], *, automatic: bool) -> None:
        self._target_mode = "review" if automatic else "quant"
        if self.host.workspace_path:
            self._starting = True
            self._stage = "opening"
            self.host.import_images(tuple(str(path) for path in paths), automatic=automatic)
        else:
            self.start_from_images(paths, automatic=automatic)

    @property
    def shutdown_stage(self) -> str:
        return self._stage

    def _request_transition(
        self, intent: str, continuation: Callable[[], None] | None = None
    ) -> None:
        if self._stage in {"confirm_busy", "confirm_dirty", "confirm_draft", "cancel", "shutdown"}:
            if intent == "exit":
                self._intent = "exit"
                self._continuation = None
                self._publish_session()
            return
        self._intent = intent
        self._continuation = continuation
        self._discard = False
        self.host.pause_auto_save(True)
        if self.host.operation_busy:
            self._stage = "confirm_busy"
            self._message = "正在处理项目。取消任务后，已提交的结果会保留。"
        elif self._draft:
            self._stage = "confirm_draft"
            self._message = "有尚未应用的清单、分配或图像调整。请返回应用修改，或放弃这部分草稿。"
        elif self.host.has_unsaved_changes:
            self._stage = "confirm_dirty"
            self._message = "当前项目有未保存修改。保存后可从当前页面和 Fig 继续工作。"
        else:
            self._begin_shutdown()
        self._publish_session()

    def _begin_shutdown(self) -> None:
        self._stage = "shutdown"
        self._message = "正在保存项目并结束本次会话…"
        self._since = time.monotonic()
        self._closing = True
        self.host.prepare_shutdown(save_changes=not self._discard)
        self.host.shutdown_requested = True
        self.host.close()
        self._check_close_failure()

    def _reply(self, choice: str) -> None:
        if choice == "return":
            self._stage = "opening" if self._starting else "idle"
            self._closing = False
            self.host.pause_auto_save(False)
            self._continuation = None
        elif choice == "retry" and self._stage == "failed":
            self._request_transition(self._intent, self._continuation)
        elif choice == "cancel" and self._stage == "confirm_busy":
            self.host.cancel()
            self._stage = "cancel"
            self._since = time.monotonic()
            self._message = "正在取消任务，等待工作进程结束…"
        elif choice == "discard" and self._stage == "confirm_draft":
            self._draft = False
            if self.host.has_unsaved_changes:
                self._stage = "confirm_dirty"
                self._message = "项目还有未保存修改。请选择保存，或明确放弃未保存修改。"
            else:
                self._begin_shutdown()
        elif choice in {"save", "discard"} and self._stage == "confirm_dirty":
            self._discard = choice == "discard"
            self._draft = False
            self._begin_shutdown()
        self._publish_session()

    @Slot(str, str)
    def _session_request(self, action: str, payload: str) -> None:
        try:
            if action == "shortcuts" and len(payload) > 32768:
                raise ValueError("快捷键设置超出容量预算")
            raw: object = json.loads(payload)
            if not isinstance(raw, dict):
                raise ValueError("操作参数无效")
            data = cast(dict[str, object], raw)
            if action == "position":
                if self._ready_project and data.get("projectId") == self._ready_project:
                    # A queued page heartbeat may predate the close request. Once
                    # cancelling/closing, it must not erase the captured draft.
                    if self._stage in {"idle", "opening"}:
                        self._draft = data.get("draft") is True
                    elif self._stage in {"confirm_busy", "cancel"}:
                        self._draft = self._draft or data.get("draft") is True
                    self.navigation.remember(self.host.workspace_path, data)
            elif action == "reply":
                self._reply(str(data.get("choice", "")))
            elif action == "exit":
                self._request_transition("exit")
            elif action == "home":
                self._request_transition("home")
            elif action == "recent":
                index = data.get("index")
                recent = self.navigation.recent()
                if type(index) is not int or not 0 <= index < len(recent):
                    raise ValueError("最近项目已改变，请重新选择")
                self.open_project(str(recent[index]["path"]))
            elif action == "open":
                self.choose("open_project")
            elif action == "new_from_folder":
                if self._last_open_path and not self.host.workspace_path:
                    self.start_from_images([Path(self._last_open_path)], automatic=False)
            elif action == "new":
                self._request_transition("new", lambda: self.choose("quant_import"))
            elif action == "new_intake_folder":
                self._request_transition("new", lambda: self.choose("new_intake_folder"))
            elif action == "folder":
                self.choose("quant_import_folder")
            elif action == "shortcuts":
                receipt = data.get("requestId")
                if not isinstance(receipt, str) or not receipt or len(receipt) > 80:
                    raise ValueError("快捷键保存身份无效")
                self.shortcuts.update(data.get("bindings"), receipt)
            elif action == "save":
                self.host.save()
            elif action == "location":
                path = QFileDialog.getExistingDirectory(self, "选择新项目保存位置")
                if path:
                    self.settings.setValue("project_parent", path)
            elif action == "refresh":
                self._previous_session = ""
            elif action != "refresh":
                raise ValueError("未知项目入口操作")
        except (ValueError, OSError) as error:
            self._message = str(error)
            self._stage = "entry_error"
        self._publish_session()

    def _poll_session(self) -> None:
        self._check_close_failure()
        if self._stage == "cancel" and not self.host.operation_busy:
            # Cancellation can leave submitted results, unsaved edits, and UI drafts.
            # Reevaluate them without losing the requested exit/project switch.
            self._stage = "idle"
            self._request_transition(self._intent, self._continuation)
        elif self._stage in {"cancel", "shutdown"} and time.monotonic() - self._since > 20:
            self._message = "仍在等待本次会话的后台资源退出，窗口将保持可见。"
        if self._starting and self._stage == "opening" and not self.host.operation_busy:
            project = self.host.view.project()
            has_content = bool(project.rows) or (
                isinstance(project, WBIntakeProject) and bool(project.intake.sources)
            )
            if (
                has_content
                and not self.host.view.status.text().startswith("操作失败")
                and self.host.has_unsaved_changes
            ):
                self.host.save()
                return
            self._starting = False
            if has_content and not self.host.view.status.text().startswith("操作失败"):
                self._ready_project = project.project_id
                if isinstance(project, WBIntakeProject):
                    self._target_mode = "intake"
                restore = (
                    self._restore if self._restore.get("projectId") == project.project_id else {}
                )
                selected = next((r for r in project.rows if r.row_id == restore.get("rowId")), None)
                if selected is None:
                    selected = next(
                        (r for r in project.rows if r.figure == restore.get("figure")),
                        project.rows[0] if project.rows else None,
                    )
                self._route_number += 1
                self._route = {
                    "token": self._route_number,
                    "projectId": project.project_id,
                    "mode": self._target_mode,
                    "rowId": selected.row_id if selected else "",
                    "lane": restore.get("lane", 1),
                }
                self.navigation.remember(
                    self.host.workspace_path,
                    {
                        "projectId": project.project_id,
                        "name": project.name,
                        "mode": self._target_mode,
                        "rowId": selected.row_id if selected else "",
                        "figure": selected.figure if selected else "",
                        "lane": 1,
                    },
                )
                self._stage = "idle"
            else:
                self._stage = "entry_error"
                self._message = self.host.view.status.text()
        self._publish_session()

    def _publish_session(self) -> None:
        state = json.dumps(
            {
                "stage": self._stage,
                "epoch": self.bridge.session_epoch,
                "message": self._message,
                "intent": self._intent,
                "route": self._route,
                "recents": self.navigation.recent(),
                "shortcuts": self.shortcuts.snapshot(),
                "workspace": self.host.workspace_path,
                "saveState": "处理中"
                if self.host.operation_busy
                else "有未保存修改"
                if self.host.has_unsaved_changes
                else "已保存"
                if self.host.workspace_path
                else "尚未打开项目",
                "projectParent": str(
                    self.settings.value("project_parent", "文档 / BioImage / Projects")
                ),
                "canImportFailedFolder": bool(self._last_open_path)
                and not self.host.workspace_path,
            },
            ensure_ascii=False,
        )
        if state != self._previous_session:
            self._previous_session = state
            self.bridge.sessionStateChanged.emit(state)
