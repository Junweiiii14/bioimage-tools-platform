"""Portable templates reject scientific state, corrupt fonts and unsafe publication."""

import json
from hashlib import sha256
from pathlib import Path
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from PIL import ImageFont
from tool_contracts.api import AssetRef
from wb_tool.adapters import figure_template_io
from wb_tool.adapters.figure_template_io import export_figure_template, read_figure_template
from wb_tool.application.figure_project import FigureSourcePath, FigureTemplate, WBFigureProject
from wb_tool.application.figure_template import LoadedFigureTemplate, PortableFigureTemplate
from wb_tool.application.laboratory_layout import FigureLayoutStyle, WBLayoutProject


def project() -> WBFigureProject:
    return WBFigureProject(project_id="secret-project", name="private experiment")


def write_archive(path: Path, settings: bytes, extra: dict[str, bytes] | None = None) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr("settings.json", settings)
        for name, value in (extra or {}).items():
            archive.writestr(name, value)


def test_roundtrip_legacy_and_laboratory_settings_only(tmp_path: Path) -> None:
    old = project()
    new = WBLayoutProject(project_id="private-new", layout_style=FigureLayoutStyle(heading_size=35))
    for index, original in enumerate((old, new)):
        target = tmp_path / f"{index}.wbtemplate"
        export_figure_template(original, (), str(target))
        loaded = read_figure_template(str(target))
        assert loaded.spec.template == original.template
        assert loaded.spec.layout_style == (new.layout_style if index else None)
        assert loaded.font_data == b""
        with ZipFile(target) as archive:
            assert archive.namelist() == ["settings.json"]
            data = archive.read("settings.json")
            assert b"private" not in data and b"secret" not in data
            assert not {"rows", "composition", "project_id", "revision"} & json.loads(data).keys()


def test_font_roundtrip_into_another_workspace_without_source(tmp_path: Path) -> None:
    font = ImageFont.load_default()
    assert isinstance(font, ImageFont.FreeTypeFont)
    data = font.font_bytes
    digest = sha256(data).hexdigest()
    source = tmp_path / "font-asset-without-extension"
    source.write_bytes(data)
    asset = AssetRef(
        asset_id="font1", relative_path="assets/font1", sha256=digest, size_bytes=len(data)
    )
    original = project().model_copy(update={"template": FigureTemplate(font=asset)})
    target = tmp_path / "portable.wbtemplate"
    export_figure_template(original, (FigureSourcePath(digest, str(source)),), str(target))
    source.unlink()
    loaded = read_figure_template(str(target))
    assert loaded.font_data == data
    assert loaded.spec.template.font is None
    assert loaded.spec.font is not None and loaded.spec.font.filename == "font.ttf"
    assert b"assets/font1" not in target.read_bytes()


@pytest.mark.parametrize("field,value", [("schema_version", 2), ("project_id", "leak")])
def test_reject_future_and_unknown_settings(tmp_path: Path, field: str, value: object) -> None:
    raw = PortableFigureTemplate(template=FigureTemplate()).model_dump()
    raw[field] = value
    target = tmp_path / "bad.wbtemplate"
    write_archive(target, json.dumps(raw).encode())
    with pytest.raises(ValueError):
        read_figure_template(str(target))


@pytest.mark.parametrize("member", ["../font.ttf", "/font.ttf", "font.ttf", "rows.json"])
def test_reject_extra_missing_declared_or_unsafe_members(tmp_path: Path, member: str) -> None:
    target = tmp_path / "bad.wbtemplate"
    write_archive(
        target,
        PortableFigureTemplate(template=FigureTemplate()).model_dump_json().encode(),
        {member: b"untrusted"},
    )
    with pytest.raises(ValueError):
        read_figure_template(str(target))


def test_reject_duplicate_json_and_zip_members(tmp_path: Path) -> None:
    target = tmp_path / "bad.wbtemplate"
    write_archive(target, b'{"schema_version":1,"schema_version":1,"template":{}}')
    with pytest.raises(ValueError, match="重复"):
        read_figure_template(str(target))
    with ZipFile(target, "a") as archive, pytest.warns(UserWarning, match="Duplicate"):
        archive.writestr("settings.json", b"{}")
    with pytest.raises(ValueError, match="重复"):
        read_figure_template(str(target))


@pytest.mark.parametrize("kind", ["size", "digest", "font"])
def test_reject_invalid_font_metadata_and_payload(tmp_path: Path, kind: str) -> None:
    data = b"not a font"
    raw = PortableFigureTemplate(template=FigureTemplate()).model_dump()
    raw["font"] = {
        "filename": "font.ttf",
        "size_bytes": len(data) + (kind == "size"),
        "sha256": "0" * 64 if kind == "digest" else sha256(data).hexdigest(),
    }
    target = tmp_path / "bad.wbtemplate"
    write_archive(target, json.dumps(raw).encode(), {"font.ttf": data})
    with pytest.raises(ValueError):
        read_figure_template(str(target))


def test_budget_and_compression_rejection(tmp_path: Path) -> None:
    target = tmp_path / "huge.wbtemplate"
    write_archive(target, b" " * (64 * 1024 + 1))
    with pytest.raises(ValueError, match="大小"):
        read_figure_template(str(target))
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("settings.json", b"{}")
    with pytest.raises(ValueError, match="格式"):
        read_figure_template(str(target))
    with target.open("wb") as stream:
        stream.truncate(34 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="预算"):
        read_figure_template(str(target))


def test_cancelled_export_cleans_stage_and_never_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "saved.wbtemplate"
    calls = 0

    def cancelled() -> bool:
        nonlocal calls
        calls += 1
        return calls >= 4

    with pytest.raises(ValueError, match="取消"):
        export_figure_template(project(), (), str(target), cancelled=cancelled)
    assert not target.exists()
    assert not list(tmp_path.glob(".wb-template-*"))
    target.write_bytes(b"existing result")
    with pytest.raises(FileExistsError):
        export_figure_template(project(), (), str(target))
    assert target.read_bytes() == b"existing result"


def test_reject_workspace_font_reference_in_settings(tmp_path: Path) -> None:
    raw = PortableFigureTemplate(template=FigureTemplate()).model_dump()
    raw["template"]["font"] = {
        "asset_id": "old",
        "relative_path": "assets/old",
        "sha256": "0" * 64,
        "size_bytes": 1,
    }
    target = tmp_path / "bad.wbtemplate"
    write_archive(target, json.dumps(raw).encode())
    with pytest.raises(ValueError, match="工作区"):
        read_figure_template(str(target))


def test_foreign_stage_collision_is_not_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    identity = UUID(int=1)
    monkeypatch.setattr(figure_template_io, "uuid4", lambda: identity)
    stage = tmp_path / f".wb-template-{identity.hex}.wbtemplate"
    stage.write_bytes(b"another operation")
    with pytest.raises(FileExistsError):
        export_figure_template(project(), (), str(tmp_path / "new.wbtemplate"))
    assert stage.read_bytes() == b"another operation"


def test_target_appearing_during_verification_is_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "race.wbtemplate"
    real_read = figure_template_io.read_figure_template

    def read_and_create(source: str, *, cancelled: object) -> LoadedFigureTemplate:
        checked = real_read(source)
        target.write_bytes(b"concurrent result")
        return checked

    monkeypatch.setattr(figure_template_io, "read_figure_template", read_and_create)
    with pytest.raises(FileExistsError):
        export_figure_template(project(), (), str(target))
    assert target.read_bytes() == b"concurrent result"
    assert not list(tmp_path.glob(".wb-template-*"))


def test_parent_junction_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.is_junction

    def junction(path: Path) -> bool:
        return path == tmp_path or original(path)

    monkeypatch.setattr(Path, "is_junction", junction)
    with pytest.raises(ValueError, match="junction"):
        export_figure_template(project(), (), str(tmp_path / "unsafe.wbtemplate"))
    assert not list(tmp_path.glob(".wb-template-*"))
