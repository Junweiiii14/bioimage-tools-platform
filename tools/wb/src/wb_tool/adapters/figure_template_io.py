"""Bounded ZIP settings exchange with verified fonts and atomic no-replacement export."""

import os
from collections.abc import Callable
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_STORED, BadZipFile, ZipFile

from PIL import ImageFont

from wb_tool.application.figure_project import FigureSourcePath, WBFigureProject
from wb_tool.application.figure_template import (
    LoadedFigureTemplate,
    PortableFigureTemplate,
    TemplateFont,
)
from wb_tool.application.laboratory_layout import WBLayoutProject

_SETTINGS_LIMIT = 64 * 1024
_FONT_LIMIT = 32 * 1024 * 1024
_FILE_LIMIT = 34 * 1024 * 1024


def _cancel(cancelled: Callable[[], bool]) -> None:
    if cancelled():
        raise ValueError("模板任务已取消，未发布输出")


def _safe_path(path: Path) -> None:
    if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
        raise ValueError("模板路径不能经过符号链接或 junction")


def _bounded_file(path: Path, budget: int, cancelled: Callable[[], bool]) -> bytes:
    _safe_path(path)
    with path.open("rb") as stream:
        if os.fstat(stream.fileno()).st_size > budget:
            raise ValueError("模板文件超出大小预算")
        chunks: list[bytes] = []
        total = 0
        while True:
            _cancel(cancelled)
            chunk = stream.read(min(1024 * 1024, budget + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > budget:
                raise ValueError("模板文件超出大小预算")
    _cancel(cancelled)
    return b"".join(chunks)


def _validate_font(data: bytes) -> None:
    try:
        ImageFont.truetype(BytesIO(data), 12)
    except (OSError, ValueError) as error:
        raise ValueError("模板字体不是有效的 TTF/OTF/TTC 字体") from error


def _read(data: bytes, cancelled: Callable[[], bool]) -> LoadedFigureTemplate:
    try:
        with ZipFile(BytesIO(data)) as archive:
            members = archive.infolist()
            names = [item.filename for item in members]
            if not 1 <= len(members) <= 2 or len(set(names)) != len(names):
                raise ValueError("模板成员数量或名称重复")
            if "settings.json" not in names or any(
                name not in ("settings.json", "font.ttf", "font.otf", "font.ttc") for name in names
            ):
                raise ValueError("模板包含额外或越界成员")
            for item in members:
                limit = _SETTINGS_LIMIT if item.filename == "settings.json" else _FONT_LIMIT
                if (
                    item.is_dir()
                    or item.compress_type != ZIP_STORED
                    or item.flag_bits & 1
                    or item.file_size > limit
                    or item.compress_size != item.file_size
                    or (item.external_attr >> 16) & 0o170000 == 0o120000
                ):
                    raise ValueError("模板成员格式或大小不支持")
            _cancel(cancelled)
            spec = PortableFigureTemplate.from_bytes(archive.read("settings.json"))
            expected = {"settings.json"}
            if spec.font is not None:
                expected.add(spec.font.filename)
            if set(names) != expected:
                raise ValueError("模板字体声明与成员不一致")
            font_data = b"" if spec.font is None else archive.read(spec.font.filename)
            if spec.font is not None:
                if (
                    len(font_data) != spec.font.size_bytes
                    or sha256(font_data).hexdigest() != spec.font.sha256
                ):
                    raise ValueError("模板字体摘要或字节数不一致")
                _cancel(cancelled)
                _validate_font(font_data)
            _cancel(cancelled)
            return LoadedFigureTemplate(spec, font_data)
    except (BadZipFile, KeyError, RuntimeError, EOFError) as error:
        raise ValueError("独立模板 ZIP 损坏或格式不支持") from error


def read_figure_template(
    source: str, *, cancelled: Callable[[], bool] = lambda: False
) -> LoadedFigureTemplate:
    path = Path(source).absolute()
    if path.suffix.lower() != ".wbtemplate":
        raise ValueError("请选择 .wbtemplate 独立模板")
    return _read(_bounded_file(path, _FILE_LIMIT, cancelled), cancelled)


def export_figure_template(
    project: WBFigureProject,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    target = Path(destination).absolute()
    if target.suffix.lower() != ".wbtemplate":
        raise ValueError("请选择新的 .wbtemplate 文件")
    _safe_path(target)
    if target.exists():
        raise FileExistsError("模板目标已存在，请选择新文件")
    _cancel(cancelled)
    paths = {source.sha256: source.path for source in sources}
    if len(paths) != len(sources):
        raise ValueError("来源路径重复")
    font_data = b""
    font = None
    asset = project.template.font
    if asset is not None:
        if asset.sha256 not in paths:
            raise ValueError("缺少模板字体来源路径")
        path = Path(paths[asset.sha256])
        font_data = _bounded_file(path, _FONT_LIMIT, cancelled)
        if len(font_data) != asset.size_bytes or sha256(font_data).hexdigest() != asset.sha256:
            raise ValueError("模板字体摘要或字节数不一致")
        _validate_font(font_data)
        extension = path.suffix.lower()
        if extension not in (".ttf", ".otf", ".ttc"):
            extension = Path(asset.relative_path).suffix.lower()
        filename = {".otf": "font.otf", ".ttc": "font.ttc"}.get(extension, "font.ttf")
        font = TemplateFont.model_validate(
            {"sha256": asset.sha256, "size_bytes": len(font_data), "filename": filename}
        )
    spec = PortableFigureTemplate(
        template=project.template.model_copy(update={"font": None}),
        layout_style=project.layout_style if isinstance(project, WBLayoutProject) else None,
        font=font,
    )
    settings = spec.model_dump_json().encode("utf-8")
    if len(settings) > _SETTINGS_LIMIT:
        raise ValueError("模板设置超出 64 KiB 预算")
    stage = target.parent / (".wb-template-" + uuid4().hex + ".wbtemplate")
    created = False
    try:
        with stage.open("xb") as stream:
            created = True
            with ZipFile(stream, "w", compression=ZIP_STORED) as archive:
                archive.writestr("settings.json", settings)
                if font is not None:
                    _cancel(cancelled)
                    archive.writestr(font.filename, font_data)
            stream.flush()
            os.fsync(stream.fileno())
        checked = read_figure_template(str(stage), cancelled=cancelled)
        if checked != LoadedFigureTemplate(spec, font_data):
            raise ValueError("模板重新读取验证不一致")
        _safe_path(target)
        _cancel(cancelled)
        if os.name == "nt":
            os.rename(stage, target)
        else:
            os.link(stage, target)
        return str(target)
    finally:
        if created:
            stage.unlink(missing_ok=True)
