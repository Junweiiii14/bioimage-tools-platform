"""Visible, static tool hub; tool windows own their asynchronous workspace lifecycle."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from bioimage_app.figure_window import FigureProjectWindow
from bioimage_app.project_entry import default_project_parent


@dataclass(frozen=True)
class ToolRegistration:
    tool_id: str
    title: str
    summary: str
    create_window: Callable[[], FigureProjectWindow]


# Code-owned registrations only: no executable modules read from projects or settings.
TOOLS = (
    ToolRegistration(
        "wb", "WB 自动化", "原图导入、泳道与裁剪、定量复核、拼图与结果导出", FigureProjectWindow
    ),
)


class PlatformWindow(QMainWindow):
    """Project hub with one active tool and recently opened workspace paths."""

    def __init__(self, *, settings: QSettings | None = None) -> None:
        super().__init__()
        self.setWindowTitle("BioImage · 生物图像工具平台")
        self.setObjectName("platformWindow")
        self.resize(1380, 880)
        self.setMinimumSize(1000, 680)
        self.setFont(QFont("Microsoft YaHei UI", 10))
        self.settings = settings if settings is not None else QSettings("BioImageTools", "Platform")
        self.active_tool: FigureProjectWindow | None = None
        self._exit_requested = False
        self._recent_paths: list[str] = []
        self._build()
        self._theme()
        self._load_recent()

    def _build(self) -> None:
        surface = QWidget()
        self.setCentralWidget(surface)
        root = QVBoxLayout(surface)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        top = QFrame()
        top.setObjectName("platformTop")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(28, 20, 28, 20)
        brand = QLabel("BioImage")
        brand.setObjectName("platformBrand")
        top_layout.addWidget(brand)
        top_layout.addWidget(QLabel("生物图像工具平台"))
        top_layout.addStretch()
        top_layout.addWidget(QLabel("本地项目 · 原图与结果可追溯"))
        root.addWidget(top)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)
        left = QFrame()
        left.setObjectName("platformRail")
        left.setFixedWidth(190)
        nav = QVBoxLayout(left)
        nav.setContentsMargins(20, 30, 20, 24)
        nav.setSpacing(14)
        nav.addWidget(self._label("工作台", "sectionTitle"))
        self.home_button = QPushButton("项目与工具")
        self.home_button.setObjectName("selectedNav")
        self.home_button.clicked.connect(self.recent_list_focus)
        nav.addWidget(self.home_button)
        nav.addSpacing(22)
        nav.addWidget(self._label("可用工具", "sectionTitle"))
        self.tool_button = QPushButton(TOOLS[0].title)
        self.tool_button.clicked.connect(self.choose_new)
        nav.addWidget(self.tool_button)
        nav.addStretch()
        nav.addWidget(self._label("本地运行 · 原图保留", "muted"))
        body.addWidget(left)

        center = QWidget()
        content = QVBoxLayout(center)
        content.setContentsMargins(34, 30, 34, 28)
        content.setSpacing(16)
        content.addWidget(self._label("把原图交给工作台", "pageTitle"))
        content.addWidget(self._label("自动识别与处理，集中复核，再输出实验结果。", "muted"))
        content.addSpacing(8)
        tool = QFrame()
        tool.setObjectName("toolSurface")
        tool_layout = QVBoxLayout(tool)
        tool_layout.setContentsMargins(24, 24, 24, 24)
        tool_layout.setSpacing(14)
        tool_layout.addWidget(self._label(TOOLS[0].title, "toolTitle"))
        tool_layout.addWidget(self._label(TOOLS[0].summary, "muted"))
        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.new_button = QPushButton("选择 WB 原图并开始")
        self.new_button.setAccessibleName("选择 WB 原图并自动创建项目")
        self.new_button.setShortcut("Ctrl+N")
        self.new_button.setObjectName("primaryAction")
        self.new_button.clicked.connect(self.choose_new)
        self.open_button = QPushButton("打开已有项目")
        self.open_button.clicked.connect(self.choose_open)
        actions.addWidget(self.new_button)
        self.folder_button = QPushButton("选择原图文件夹")
        self.folder_button.clicked.connect(self.choose_source_folder)
        actions.addWidget(self.folder_button)
        actions.addStretch()
        tool_layout.addLayout(actions)
        tool_layout.addWidget(
            self._label("自动创建项目文件夹，原图无须移动。支持 TIFF 原图。", "muted")
        )
        content.addWidget(tool)
        recent_header = QHBoxLayout()
        recent_header.setContentsMargins(0, 14, 0, 0)
        recent_header.addWidget(self._label("最近项目", "sectionTitle"))
        recent_header.addStretch()
        recent_header.addWidget(self.open_button)
        self.reopen_button = QPushButton("继续所选项目")
        self.reopen_button.setEnabled(False)
        self.reopen_button.clicked.connect(self.open_selected)
        recent_header.addWidget(self.reopen_button)
        content.addLayout(recent_header)
        self.recent_list = QListWidget()
        self.recent_list.setObjectName("recentProjects")
        self.recent_list.setSpacing(5)
        self.recent_list.itemSelectionChanged.connect(self._selection_changed)
        self.recent_list.itemDoubleClicked.connect(self.open_selected)
        content.addWidget(self.recent_list, 1)
        self.empty_label = self._label(
            "还没有项目。选择上方的 WB 原图，即可开始自动处理。", "muted"
        )
        content.insertWidget(content.indexOf(self.recent_list), self.empty_label)
        self.status = self._label("就绪", "platformStatus")
        content.addWidget(self.status)
        body.addWidget(center, 1)

        self.project_path = self._label("项目会自动保存在文档 / BioImage / Projects", "muted")
        self.project_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content.addWidget(self.project_path)
        self.location_button = QPushButton("更改新项目保存位置")
        self.location_button.setObjectName("quietAction")
        self.location_button.clicked.connect(self.choose_project_parent)
        content.addWidget(self.location_button, 0, Qt.AlignmentFlag.AlignLeft)

    @staticmethod
    def _label(text: str, name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        return label

    def _theme(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f6f5f2; color: #242723; }
            QFrame#platformTop, QFrame#platformRail, QFrame#platformDetails {
                background: #ffffff;
            }
            QFrame#platformTop { border-bottom: 1px solid #e3e5df; }
            QLabel { background: transparent; }
            QLabel#platformBrand { color: #256f82; font-size: 23px; font-weight: 600; }
            QLabel#pageTitle { font-size: 28px; font-weight: 600; }
            QLabel#toolTitle { font-size: 22px; font-weight: 600; }
            QLabel#sectionTitle { font-size: 15px; font-weight: 600; }
            QLabel#stepTitle { font-size: 14px; font-weight: 600; }
            QLabel#muted, QLabel#platformStatus { color: #61645f; }
            QFrame#toolSurface { background: #ffffff; border: 1px solid #d9dcd6;
                border-radius: 8px; }
            QPushButton { background: #ffffff; color: #242723; border: 1px solid #d9dcd6;
                border-radius: 6px; padding: 10px 14px; min-height: 18px; }
            QPushButton:hover { background: #e8f0f1; border-color: #256f82; }
            QPushButton:focus { border: 2px solid #256f82; }
            QPushButton:pressed { background: #e1ecef; }
            QPushButton:disabled { background: #edf1f3; color: #697a84; border-color: #e3e5df; }
            QPushButton#primaryAction { background: #256f82; color: #ffffff;
                border-color: #256f82; font-weight: 600; }
            QPushButton#primaryAction:hover { background: #1d5868; }
            QPushButton#selectedNav { background: #e8f0f1; color: #1d5868;
                border-color: #e8f0f1; text-align: left; }
            QListWidget#recentProjects { background: #f6f5f2; border: none;  }
            QPushButton#quietAction { border: none; background: transparent; padding: 4px 0;
                color: #256f82; }
            QListWidget#recentProjects:focus { border: 1px solid #256f82; }
            QListWidget#recentProjects::item { background: #ffffff; padding: 15px 12px;
                border: 1px solid #e3e5df; border-radius: 6px; }
            QListWidget#recentProjects::item:selected { background: #e1ecef;
                color: #242723; border-color: #256f82; }
            QListWidget#recentProjects::item:hover { border-color: #256f82; }
        """)

    def recent_list_focus(self) -> None:
        self.recent_list.setFocus()

    def _load_recent(self) -> None:
        value = self.settings.value("recent_workspaces", [])
        paths = cast(list[object], value) if isinstance(value, list) else [value]
        self._recent_paths = list(dict.fromkeys(p for p in paths if isinstance(p, str) and p))[:8]
        self._refresh_recent()

    def _refresh_recent(self) -> None:
        self.recent_list.clear()
        for path in self._recent_paths:
            opened = self.settings.value(f"recent_opened/{path}", "")
            detail = f"最近打开 {opened}" if opened else "已保存的项目位置"
            name = Path(path).name
            if name.casefold() == "workspace":
                name = f"{Path(path).parent.name} · {name}"
            item = QListWidgetItem(f"{name}\nWB 项目 · {detail}")
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.recent_list.addItem(item)
        self.empty_label.setVisible(not self._recent_paths)

    def _selection_changed(self) -> None:
        selected = self.recent_list.selectedItems()
        self.reopen_button.setEnabled(bool(selected))
        path = str(selected[0].data(Qt.ItemDataRole.UserRole)) if selected else "未选择项目"
        self.project_path.setText(path)

    def choose_new(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择 WB 原始图像", "", "TIFF 原图 (*.tif *.tiff)"
        )
        if paths:
            self.start_from_images([Path(path) for path in paths])

    def choose_source_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择 WB 原图文件夹")
        if path:
            self.start_from_images([Path(path)])

    def choose_project_parent(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择项目保存位置（自动创建子文件夹）")
        if path:
            self.settings.setValue("project_parent", path)
            self.project_path.setText(f"新项目保存位置：{path}（自动创建子文件夹）")

    def start_from_images(self, paths: list[Path]) -> None:
        if self.active_tool is not None:
            self.active_tool.show()
            self.active_tool.raise_()
            return
        parent_value = self.settings.value("project_parent", "")
        parent = (
            Path(parent_value)
            if isinstance(parent_value, str) and parent_value
            else default_project_parent()
        )
        self.launch_tool()
        if self.active_tool is not None:
            self.active_tool.start_project_from_images(paths, project_parent=parent)

    def choose_open(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "打开已有项目文件夹")
        if path:
            self.open_workspace(path)

    def open_selected(self) -> None:
        selected = self.recent_list.selectedItems()
        if selected:
            self.open_workspace(str(selected[0].data(Qt.ItemDataRole.UserRole)))

    def open_workspace(self, path: str, *, create: bool = False) -> None:
        if self.active_tool is not None:
            self.active_tool.show()
            self.active_tool.raise_()
            return
        # Workspace validates emptiness, format, permissions and locking asynchronously.
        # Do not inspect source folders or load project data in the GUI thread.
        self.launch_tool()
        if self.active_tool is not None:
            self.active_tool.open_workspace(path, create=create)

    def launch_tool(self) -> None:
        if self.active_tool is not None:
            self.active_tool.show()
            self.active_tool.raise_()
            return
        window = TOOLS[0].create_window()
        self.active_tool = window
        toolbar = QToolBar("平台导航", window)
        toolbar.setObjectName("platformReturnBar")
        toolbar.setMovable(False)
        self.return_button = QPushButton("返回工具平台")
        self.return_button.setToolTip("保存当前有效修改，结束后台任务后返回平台")
        self.return_button.clicked.connect(window.close)
        toolbar.addWidget(self.return_button)
        window.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        window.workspace_opened.connect(self._workspace_ready)
        window.closed.connect(lambda: self._tool_closed(window))
        window.show()
        self.hide()

    def _workspace_ready(self, path: str) -> None:
        normalized = str(Path(path).absolute())
        self._recent_paths = [normalized, *(p for p in self._recent_paths if p != normalized)][:8]
        self.settings.setValue("recent_workspaces", self._recent_paths)
        self.settings.setValue(
            f"recent_opened/{normalized}", datetime.now().strftime("%m月%d日 %H:%M")
        )
        self.settings.sync()
        self._refresh_recent()
        if self.settings.status() != QSettings.Status.NoError:
            self.status.setText("项目已打开；最近项目列表未能保存，可通过项目文件夹重新打开。")
        else:
            self.status.setText(f"已打开：{Path(normalized).name}")
        window = self.active_tool
        if window is not None and window.documents.count() > 1:
            document_id = window.documents.itemData(1)
            if isinstance(document_id, str):
                window.load_document(document_id)

    def _tool_closed(self, window: FigureProjectWindow) -> None:
        self.active_tool = None
        QTimer.singleShot(0, window.deleteLater)
        if self._exit_requested:
            self.close()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.active_tool is None:
            event.accept()
            return
        self._exit_requested = True
        event.ignore()
        self.active_tool.close()
