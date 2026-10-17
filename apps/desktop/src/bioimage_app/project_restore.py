"""One-shot background restore: validate, build an owned workspace, close, then publish."""

import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event

from platform_runtime.api import Workspace
from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from tool_contracts.api import AssetRef
from wb_tool.api import restore_staged_project, stage_project_archive


@dataclass(frozen=True)
class ArchiveRestoreResult:
    path: str = ""
    project_id: str = ""
    error: str = ""


def _cancel(event: Event) -> None:
    if event.is_set():
        raise ValueError("恢复已取消，未发布新工作区")


def _plain(path: Path) -> None:
    if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
        raise ValueError("恢复目录不能经过链接或junction")


def _publish(source: Path, target: Path, owned: Path) -> None:
    _plain(source)
    _plain(target)
    if (
        not source.resolve().is_relative_to(owned.resolve())
        or target.parent.resolve() != owned.parent.resolve()
    ):
        raise ValueError("恢复发布超出本次暂存目录或目标父目录")
    if target.exists():
        raise FileExistsError("恢复目标已存在，请选择新的目录")
    if os.name == "nt":
        os.rename(source, target)  # Windows directory rename never replaces an existing target.
        return
    target.mkdir()
    marker = target / ".restore-incomplete"
    marker.write_text(
        "Workspace publication incomplete. Restore again to a new directory.\n", encoding="utf-8"
    )
    for child in source.iterdir():
        destination = target / child.name
        _plain(child)
        _plain(destination)
        if (
            not child.resolve().is_relative_to(owned.resolve())
            or destination.parent.resolve() != target.resolve()
        ):
            raise ValueError("恢复成员发布路径无效")
        os.rename(child, destination)
    marker.unlink()


def restore_archive_workspace(
    source: str, destination: str, cancellation: Event
) -> ArchiveRestoreResult:
    target = Path(destination).absolute()
    _plain(target)
    if target.exists():
        raise FileExistsError("恢复目标已存在，请选择新的目录")
    _cancel(cancellation)
    with TemporaryDirectory(prefix=".wb-restore-", dir=target.parent) as temporary:
        owned = Path(temporary).resolve()
        staged = stage_project_archive(
            source, str(owned / "checked"), cancelled=cancellation.is_set
        )
        _cancel(cancellation)
        workspace_path = owned / "workspace"
        with Workspace.create(workspace_path) as store:
            original = store.import_asset(staged.archive_path, staged.archive_sha256)
            assets: list[AssetRef] = []
            for item in staged.assets:
                _cancel(cancellation)
                assets.append(store.import_asset(item.path, item.sha256))
            project = restore_staged_project(staged, tuple(assets), original)
            _cancel(cancellation)
            store.import_draft_snapshot(
                project.project_id,
                "wb-figure",
                project.revision,
                project.model_dump_json().encode(),
            )
        _cancel(cancellation)
        _publish(workspace_path, target, owned)
        return ArchiveRestoreResult(str(target), project.project_id)


class _RestoreWorker(QObject):
    replied = Signal(object)

    def __init__(self, source: str, destination: str, cancellation: Event) -> None:
        super().__init__()
        self.source, self.destination, self.cancellation = source, destination, cancellation

    @Slot()
    def run(self) -> None:
        try:
            result = restore_archive_workspace(self.source, self.destination, self.cancellation)
        except Exception as error:
            # A terminal worker boundary must drain the thread even for decoder/storage failures.
            result = ArchiveRestoreResult(error=f"{type(error).__name__}: {error}")
        self.replied.emit(result)


class ArchiveRestoreJob(QObject):
    finished = Signal(object)
    _requested = Signal()

    def __init__(self, source: str, destination: str, cancellation: Event, parent: QObject) -> None:
        super().__init__(parent)
        self._thread = QThread(self)
        self._worker = _RestoreWorker(source, destination, cancellation)
        self._worker.moveToThread(self._thread)
        self._result: ArchiveRestoreResult | None = None
        self._requested.connect(self._worker.run, Qt.ConnectionType.QueuedConnection)
        self._worker.replied.connect(self._replied, Qt.ConnectionType.QueuedConnection)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._stopped)

    def start(self) -> None:
        self._thread.start()
        self._requested.emit()

    @Slot(object)
    def _replied(self, result: ArchiveRestoreResult) -> None:
        self._result = result
        self._thread.quit()

    @Slot()
    def _stopped(self) -> None:
        if not self._thread.wait(0):
            QTimer.singleShot(1, self._stopped)
            return
        self.finished.emit(self._result or ArchiveRestoreResult(error="恢复线程未返回结果"))
