"""Prepare source selection off-thread without creating a project or changing inputs."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Event

from PySide6.QtCore import QThread

from bioimage_app.project_entry import allocate_project_path, collect_source_images


@dataclass(frozen=True)
class ProjectSelection:
    paths: tuple[Path, ...] = ()
    destination: Path | None = None
    name: str = ""
    error: str = ""


class ProjectSelectionJob(QThread):
    """Owner reads result only after finished; cancellation never publishes a workspace."""

    def __init__(self, paths: list[Path], parent: Path, cancellation: Event) -> None:
        super().__init__()
        self.paths = list(paths)
        self.destination_parent = parent
        self.cancellation = cancellation
        self.result = ProjectSelection()

    def run(self) -> None:
        try:
            paths = collect_source_images(self.paths, self.cancellation)
            parent = self.destination_parent.absolute()
            if any(p.is_symlink() or p.is_junction() for p in (parent, *parent.parents)):
                raise ValueError("项目保存位置不能经过链接，请换一个本地文件夹。")
            source_folders = [p if p.is_dir() else p.parent for p in self.paths]
            if any(parent.resolve().is_relative_to(p.resolve()) for p in source_folders):
                raise ValueError("项目保存位置与原图目录重叠，请选择原图目录以外的位置。")
            source_name = (self.paths[0] if self.paths[0].is_dir() else paths[0].parent).name
            destination = allocate_project_path(parent, source_name)
            if self.cancellation.is_set():
                raise InterruptedError("已取消选择原图")
            display_name = f"{source_name[:120] or 'WB 项目'} · {datetime.now():%Y-%m-%d}"
            self.result = ProjectSelection(paths, destination, display_name)
        except (OSError, ValueError) as error:
            self.result = ProjectSelection(error=str(error))
