"""Visible, static tool hub; tool windows own their asynchronous workspace lifecycle."""

from collections.abc import Callable
from dataclasses import dataclass
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
        left.setFixedWidth(216)
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
        self.tool_button.clicked.connect(self.launch_tool)
        nav.addWidget(self.tool_button)
        nav.addStretch()
        nav.addWidget(self._label("后续工具将在这里接入。\n当前可用：WB 自动化。", "muted"))
        body.addWidget(left)

        center = QWidget()
        content = QVBoxLayout(center)
        content.setContentsMargins(34, 30, 34, 28)
        content.setSpacing(16)
        content.addWidget(self._label("从一个实验项目开始", "pageTitle"))
        content.addWidget(
            self._label("选择工具，导入原图，在同一项目中完成处理、复核与输出。", "muted")
        )
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
        self.new_button = QPushButton("新建 WB 项目")
        self.new_button.setObjectName("primaryAction")
        self.new_button.clicked.connect(self.choose_new)
        self.open_button = QPushButton("打开项目文件夹")
        self.open_button.clicked.connect(self.choose_open)
        actions.addWidget(self.new_button)
        actions.addWidget(self.open_button)
        actions.addStretch()
        tool_layout.addLayout(actions)
        content.addWidget(tool)
        recent_header = QHBoxLayout()
        recent_header.setContentsMargins(0, 14, 0, 0)
        recent_header.addWidget(self._label("最近项目", "sectionTitle"))
        recent_header.addStretch()
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
            "还没有最近项目。新建项目后，在 WB 工作区导入原始 TIFF。", "muted"
        )
        content.addWidget(self.empty_label)
        self.status = self._label("就绪", "platformStatus")
        content.addWidget(self.status)
        body.addWidget(center, 1)

        right = QFrame()
        right.setObjectName("platformDetails")
        right.setFixedWidth(270)
        details = QVBoxLayout(right)
        details.setContentsMargins(24, 32, 24, 28)
        details.setSpacing(18)
        details.addWidget(self._label("项目流程", "sectionTitle"))
        for title, description in (
            ("导入原图", "原始文件作为分析来源。"),
            ("处理与复核", "查看识别建议，在图上调整。"),
            ("结果与输出", "保留数据、图像和项目记录。"),
        ):
            details.addWidget(self._label(title, "stepTitle"))
            details.addWidget(self._label(description, "muted"))
        details.addStretch()
        details.addWidget(self._label("所选项目位置", "sectionTitle"))
        self.project_path = self._label("选择最近项目可查看保存位置。", "muted")
        self.project_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details.addWidget(self.project_path)
        details.addWidget(self._label("新项目请使用空文件夹。原图可从其他文件夹导入。", "muted"))
        body.addWidget(right)

    @staticmethod
    def _label(text: str, name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        return label

    def _theme(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f3f6f7; color: #24363b; }
            QFrame#platformTop, QFrame#platformRail, QFrame#platformDetails {
                background: #ffffff;
            }
            QFrame#platformTop { border-bottom: 1px solid #dce4e9; }
            QLabel { background: transparent; }
            QLabel#platformBrand { color: #087677; font-size: 23px; font-weight: 600; }
            QLabel#pageTitle { font-size: 26px; font-weight: 600; }
            QLabel#toolTitle { font-size: 22px; font-weight: 600; }
            QLabel#sectionTitle { font-size: 15px; font-weight: 600; }
            QLabel#stepTitle { font-size: 14px; font-weight: 600; }
            QLabel#muted, QLabel#platformStatus { color: #526970; }
            QFrame#toolSurface { background: #ffffff; border: 1px solid #cbd8dd;
                border-radius: 12px; }
            QPushButton { background: #ffffff; color: #24363b; border: 1px solid #cbd8dd;
                border-radius: 6px; padding: 10px 14px; min-height: 18px; }
            QPushButton:hover { background: #eaf5f3; border-color: #087677; }
            QPushButton:focus { border: 2px solid #087677; }
            QPushButton:pressed { background: #dff1ed; }
            QPushButton:disabled { background: #edf1f3; color: #697a84; border-color: #dce4e9; }
            QPushButton#primaryAction { background: #087677; color: #ffffff;
                border-color: #087677; font-weight: 600; }
            QPushButton#primaryAction:hover { background: #096568; }
            QPushButton#selectedNav { background: #eaf5f3; color: #096568;
                border-color: #eaf5f3; text-align: left; }
            QListWidget#recentProjects { background: #f3f6f7; border: none; outline: 0; }
            QListWidget#recentProjects::item { background: #ffffff; padding: 15px 12px;
                border: 1px solid #dce4e9; border-radius: 6px; }
            QListWidget#recentProjects::item:selected { background: #dff1ed;
                color: #24363b; border-color: #087677; }
            QListWidget#recentProjects::item:hover { border-color: #087677; }
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
            item = QListWidgetItem(f"{Path(path).name}\nWB 项目")
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
        path = QFileDialog.getExistingDirectory(self, "为新 WB 项目选择空文件夹")
        if path:
            self.open_workspace(path, create=True)

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
        self.settings.sync()
        self._refresh_recent()
        if self.settings.status() != QSettings.Status.NoError:
            self.status.setText("项目已打开；最近项目列表未能保存，可通过项目文件夹重新打开。")
        else:
            self.status.setText(f"已打开：{Path(normalized).name}")

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
