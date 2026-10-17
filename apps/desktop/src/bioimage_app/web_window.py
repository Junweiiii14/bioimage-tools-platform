"""Same local HTML document in browser preview and Qt desktop shell."""

from pathlib import Path

from PySide6.QtCore import QSettings, QUrl
from PySide6.QtGui import QCloseEvent
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

from bioimage_app.figure_window import FigureProjectWindow
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
        self.setWindowTitle("BioImage · WB 工作台")
        self.resize(1440, 940)
        self.settings = settings or QSettings("BioImageTools", "Platform")
        self.host = AdvancedHost()
        self.host.automatic.crop_policy = "source_geometry@2"
        self.host.automatic.quant_policy = "wbquant_1_4_3@1"
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
        self.bridge.timer.timeout.connect(self._check_close_failure)
        self.channel.registerObject("workbench", self.bridge)
        page.setWebChannel(self.channel)
        self.setCentralWidget(self.web)
        self.web.setUrl(QUrl.fromLocalFile(str(index.resolve())))
        self._closing = False

    def choose(self, action: str) -> None:
        if action == "import":
            paths, _ = QFileDialog.getOpenFileNames(
                self, "选择 WB 原图", "", "TIFF 原图 (*.tif *.tiff)"
            )
            if paths:
                if self.host.workspace_path:
                    self.host.import_images(tuple(paths), automatic=True)
                else:
                    self.start_from_images([Path(path) for path in paths])
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
            if self.host.workspace_path:
                raise ValueError("当前已有项目；请新开一个工作台窗口，再打开其他项目。")
            path = QFileDialog.getExistingDirectory(self, "打开已有 BioImage 项目")
            if path:
                self.open_project(path)

    def open_project(self, path: str) -> None:
        """Open persisted project data, rather than only its storage container."""
        if self.host.workspace_path:
            raise ValueError("当前已有项目；请新开一个工作台窗口，再打开其他项目。")
        if self.host.operation_busy or self.host.is_closing:
            raise ValueError("当前任务仍在处理中，请稍候或取消")
        self.host.open_workspace(path)

    def _workspace_ready(self, _path: str) -> None:
        if self.host.documents.count() > 1:
            document_id = self.host.documents.itemData(1)
            if isinstance(document_id, str) and document_id:
                self.host.load_document(document_id)

    def start_from_images(self, paths: list[Path]) -> None:
        parent = str(self.settings.value("project_parent", ""))
        self.host.start_project_from_images(paths, project_parent=Path(parent) if parent else None)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.host.resources_closed:
            event.accept()
            return
        event.ignore()
        if not self._closing:
            self._closing = True
            self.host.shutdown_requested = True
            self.host.close()
            # Invalid advanced edits abort native shutdown; retain a visible correction route.
            if not self.host.is_closing and not self.host.resources_closed:
                self._closing = False
                self.host.shutdown_requested = False
                self.host.show()

    def _check_close_failure(self) -> None:
        if self._closing and not self.host.is_closing and not self.host.resources_closed:
            self._closing = False
            self.host.shutdown_requested = False
            self.host.show()

    def _backend_closed(self) -> None:
        self.bridge.timer.stop()
        self.web.stop()
        self.web.page().deleteLater()
        self.close()
