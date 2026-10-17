"""Direct images retain display geometry/provenance and cannot become known quantitative input."""

import json
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from threading import Event
from typing import Any, cast

import numpy as np
import pytest
import tifffile
from PIL import Image, ImageFont
from tool_contracts.api import AssetRef
from wb_tool.adapters import figure_image_export
from wb_tool.adapters.tiff_input import DISPLAY_TIFF_SOFTWARE
from wb_tool.api import (
    CropRequest,
    FigureSourcePath,
    ImageInputError,
    LaneROI,
    export_crop,
    export_figure_image,
    load_ocr_image,
    load_tiff,
    render_figure,
)

from tools.wb.tests.test_figure_project import sample


@pytest.mark.parametrize("suffix", [".png", ".tif", ".TIFF"])
def test_complete_display_pixels_provenance_dpi_and_originals(tmp_path: Path, suffix: str) -> None:
    project, paths = sample(tmp_path)
    originals = {p.path: Path(p.path).read_bytes() for p in paths}
    rendered = render_figure(project, paths)
    target = tmp_path / ("figure" + suffix)
    export_figure_image(project, paths, str(target))
    with Image.open(target) as image:
        assert image.mode == "RGB" and image.size == (rendered.width, rendered.height)
        assert image.tobytes() == rendered.rgb
        assert all(abs(v - project.template.dpi) <= 0.013 for v in image.info["dpi"])
        if suffix == ".png":
            assert image.info["wb_provenance"] == rendered.manifest_json
    if suffix != ".png":
        with tifffile.TiffFile(target) as image:
            assert len(image.pages) == 1
            page = image.pages[0]
            assert isinstance(page, tifffile.TiffPage)
            assert page.dtype == np.uint8 and page.shape == (rendered.height, rendered.width, 3)
            assert page.software == DISPLAY_TIFF_SOFTWARE
            assert page.description == rendered.manifest_json
            assert page.tags["XResolution"].value == (project.template.dpi, 1)
        with pytest.raises(ImageInputError, match="显示拼图"):
            load_tiff(target)
        with pytest.raises(ImageInputError, match="显示拼图"):
            export_crop(
                str(target),
                CropRequest(
                    sha256(target.read_bytes()).hexdigest(), 0, LaneROI("crop", 0, 0, 10, 10)
                ),
                str(tmp_path / "raw.tif"),
            )
        assert not (tmp_path / "raw.tif").exists()
    ocr = load_ocr_image(target)
    assert ocr.pixels.shape == (rendered.height, rendered.width)
    rgb = np.frombuffer(rendered.rgb, np.uint8).reshape(rendered.height, rendered.width, 3)
    np.testing.assert_array_equal(ocr.pixels, rgb[..., 0])
    metadata = json.loads(rendered.manifest_json)
    for record in metadata["rows"][:3]:
        x0, y0, x1, y1 = record["output_box"]
        index = int(record["row_id"][1:])
        crop = ocr.pixels[y0:y1, x0:x1]
        assert crop[0, 0] == 100 + index and np.all(crop[3:8, 12:18] == 20 + index)
    assert all(Path(path).read_bytes() == data for path, data in originals.items())
    assert not list(tmp_path.glob(".wb-image-*"))


@pytest.mark.parametrize(
    "fault", ["unreviewed", "source_hash", "source_size", "missing", "extension", "existing"]
)
def test_refuses_invalid_exports_without_overwriting_inputs(tmp_path: Path, fault: str) -> None:
    project, paths = sample(tmp_path)
    row = project.rows[0]
    assert row.source
    target = tmp_path / ("bad.jpg" if fault == "extension" else "bad.tif")
    if fault == "unreviewed":
        row = row.model_copy(update={"reviewed": False})
    elif fault == "source_size":
        row = row.model_copy(
            update={
                "source": row.source.model_copy(update={"size_bytes": row.source.size_bytes + 1})
            }
        )
    elif fault == "source_hash":
        Path(paths[0].path).write_bytes(b"damaged")
    elif fault == "missing":
        paths = paths[1:]
    elif fault == "existing":
        target.write_bytes(b"keep me")
    project = project.model_copy(update={"rows": (row, *project.rows[1:])})
    with pytest.raises((ValueError, OSError)):
        export_figure_image(project, paths, str(target))
    assert target.read_bytes() == b"keep me" if fault == "existing" else not target.exists()
    assert not list(tmp_path.glob(".wb-image-*"))


def test_custom_font_identity_and_source_bytes(tmp_path: Path) -> None:
    project, sources = sample(tmp_path)
    font = ImageFont.load_default(size=12)
    assert isinstance(font, ImageFont.FreeTypeFont)
    data = font.font_bytes
    assert isinstance(data, bytes)
    path = tmp_path / "font.ttf"
    path.write_bytes(data)
    ref = AssetRef(
        asset_id="font",
        relative_path="input/font.ttf",
        sha256=sha256(data).hexdigest(),
        size_bytes=len(data),
    )
    project = project.model_copy(
        update={"template": project.template.model_copy(update={"font": ref})}
    )
    sources += (FigureSourcePath(ref.sha256, str(path)),)
    output = tmp_path / "font.tif"
    export_figure_image(project, sources, str(output))
    broken = project.model_copy(
        update={
            "template": project.template.model_copy(
                update={"font": ref.model_copy(update={"size_bytes": len(data) + 1})}
            )
        }
    )
    with pytest.raises(ValueError, match="字体"):
        export_figure_image(broken, sources, str(tmp_path / "broken.tif"))
    assert path.read_bytes() == data


@pytest.mark.parametrize("marker", ["software", "description", "foreign_json"])
def test_derived_tiff_admission_is_explicit_and_ocr_remains_available(
    tmp_path: Path, marker: str
) -> None:
    target = tmp_path / "marked.tif"
    data = np.full((20, 30), 12345, dtype=np.uint16)
    description = (
        json.dumps(
            {"operation": "figure_original_geometry@1", "purpose": "display_only_not_quantitative"}
        )
        if marker == "description"
        else '{"vendor":"instrument","original":true}'
    )
    tifffile.imwrite(
        target,
        data,
        description=description,
        metadata=None,
        software=DISPLAY_TIFF_SOFTWARE if marker == "software" else "instrument",
    )
    if marker == "foreign_json":
        np.testing.assert_array_equal(load_tiff(target).pixels, data)
    else:
        with pytest.raises(ImageInputError, match="显示拼图"):
            load_tiff(target)
    np.testing.assert_array_equal(
        load_ocr_image(target).pixels, np.full((20, 30), 12345 // 257, np.uint8)
    )


@pytest.mark.parametrize("fault", ["pixels", "dpi", "description"])
def test_reread_rejects_inconsistent_encoder_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    project, sources = sample(tmp_path)
    original = tifffile.imwrite

    def broken(file: Any, data: Any, **kwargs: Any):
        if fault == "pixels":
            data = np.zeros_like(data)
        elif fault == "dpi":
            kwargs["resolution"] = (72, 72)
        else:
            kwargs["description"] = "not the provenance"
        return original(file, data, **kwargs)

    monkeypatch.setattr(tifffile, "imwrite", broken)
    output = tmp_path / "broken.tif"
    with pytest.raises(ValueError, match="不一致"):
        export_figure_image(project, sources, str(output))
    assert not output.exists() and not list(tmp_path.glob(".wb-image-*"))


@pytest.mark.parametrize("action", ["cancel", "target_race"])
def test_cancel_or_competing_target_after_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, action: str
) -> None:
    project, sources = sample(tmp_path)
    output, event = tmp_path / "last.tif", Event()
    verify = cast(Callable[..., None], vars(figure_image_export)["_verify"])

    def final_check(*args: Any, **kwargs: Any) -> None:
        verify(*args, **kwargs)
        if action == "cancel":
            event.set()
        else:
            output.write_bytes(b"concurrent owner")

    monkeypatch.setattr(figure_image_export, "_verify", final_check)
    with pytest.raises((ValueError, FileExistsError)):
        export_figure_image(project, sources, str(output), cancelled=event.is_set)
    assert not output.exists() if action == "cancel" else output.read_bytes() == b"concurrent owner"
    assert not list(tmp_path.glob(".wb-image-*"))
