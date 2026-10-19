"""Bounded, cancellable entry preparation. Call filesystem helpers off the GUI thread."""

import os
import re
from datetime import datetime
from pathlib import Path
from threading import Event
from uuid import uuid4

from PySide6.QtCore import QStandardPaths


def default_project_parent() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    return (Path(location) if location else Path.home() / "Documents") / "BioImage" / "Projects"


def collect_source_images(paths: list[Path], cancellation: Event) -> tuple[Path, ...]:
    """Collect TIFF candidates without following links or traversing app-owned results.

    Decode/quantitative-source validation remains in the existing WB import worker.
    Empty, inaccessible and oversized selections never produce a workspace.
    """
    found: dict[str, Path] = {}
    pending = list(reversed(paths))
    directories: set[str] = set()
    while pending:
        if cancellation.is_set():
            raise InterruptedError("已取消选择原图")
        path = pending.pop()
        if path.is_symlink() or path.is_junction():
            continue
        if not path.exists():
            raise ValueError(f"找不到原图位置：{path}。请重新选择。")
        resolved = path.resolve()
        if path.is_dir():
            key = os.path.normcase(str(resolved))
            if key in directories:
                continue
            directories.add(key)
            if len(directories) > 4096:
                raise ValueError("目录超过 4096 个，请选择更具体的原图文件夹。")
            if path.name.casefold() in {"outputs", ".git", ".venv"}:
                continue
            if (path / "workspace.json").exists():
                continue
            try:
                pending.extend(reversed(sorted(path.iterdir(), key=lambda p: p.name.casefold())))
            except OSError as error:
                raise ValueError(f"无法读取原图文件夹：{path}。请检查访问权限。") from error
        elif path.is_file() and path.suffix.casefold() in {".tif", ".tiff"}:
            # Explicit selections inside a workspace/output are not quantitative originals.
            if any(
                p.name.casefold() == "outputs" or (p / "workspace.json").exists()
                for p in path.parents
            ):
                continue
            found[os.path.normcase(str(resolved))] = resolved
            if len(found) > 512:
                raise ValueError("一次最多处理 512 张原图，请分成多个项目。")
    if cancellation.is_set():
        raise InterruptedError("已取消选择原图")
    if not found:
        raise ValueError("未找到可导入的 TIFF 原图。请选择 .tif / .tiff 文件或原图文件夹。")
    return tuple(found.values())


def allocate_project_path(parent: Path, source_name: str) -> Path:
    """Prepare the parent only; Workspace.create exclusively owns the final directory."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", source_name).strip(" .")[:48] or "WB"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    parent.mkdir(parents=True, exist_ok=True)
    for _ in range(16):
        candidate = parent / f"{name}-{stamp}-{uuid4().hex[:8]}"
        if not candidate.exists():
            return candidate
    raise FileExistsError("无法分配新的项目文件夹，请更换保存位置后重试。")
