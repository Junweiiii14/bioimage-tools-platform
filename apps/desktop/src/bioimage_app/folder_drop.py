"""Native URL drops retain Explorer paths that HTML File objects do not expose."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QWidget


def folder_paths(urls: tuple[QUrl, ...]) -> list[Path]:
    if not urls or len(urls) > 32:
        raise ValueError("请一次拖入 1–32 个本地原图文件夹。")
    paths: list[Path] = []
    for url in urls:
        if not url.isLocalFile() or url.host() not in ("", "localhost"):
            raise ValueError("仅支持本机文件夹，请勿拖入网页链接或网络位置。")
        path = Path(url.toLocalFile())
        if not path.is_absolute() or any(ord(c) < 32 for c in str(path)):
            raise ValueError("拖入路径无效，请选择本机原图文件夹。")
        # Filesystem access stays in ProjectSelectionJob, including directory validation.
        if path not in paths:
            paths.append(path)
    return paths


class FolderDropView(QWebEngineView):
    def __init__(
        self,
        parent: QWidget,
        dropped: Callable[[tuple[QUrl, ...]], None],
        context: Callable[[], object],
    ) -> None:
        super().__init__(parent)
        self.dropped = dropped
        self.context = context
        self.setAcceptDrops(True)

    def _target(self, event: QDropEvent, *, drop: bool = False) -> None:
        point = event.position() / self.zoomFactor()
        urls = tuple(QUrl(url) for url in event.mimeData().urls())
        context = self.context()
        script = f"window.folderDrop?.target({point.x()},{point.y()},{str(not drop).lower()})"

        def checked(accepted: object) -> None:
            if drop:
                self.page().runJavaScript("window.folderDrop?.clear()")
                if accepted is True and context == self.context():
                    self.dropped(urls)
                else:
                    self.page().runJavaScript(
                        "window.folderDrop?.message('请将原图文件夹拖到 WB 工具入口。')"
                    )

        self.page().runJavaScript(script, checked)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self._target(event)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self._target(event)
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.page().runJavaScript("window.folderDrop?.clear()")
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self._target(event, drop=True)
        else:
            event.ignore()
