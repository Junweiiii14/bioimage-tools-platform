"""Reject resource-heavy or unsupported metadata before any pixel decode."""

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import tifffile
from wb_tool.adapters import crop_export
from wb_tool.adapters.ocr_input import load_ocr_image
from wb_tool.adapters.tiff_input import LoadedTiff
from wb_tool.api import CropRequest, ImageInputError, LaneROI, load_tiff


def forbid_decode(monkeypatch: pytest.MonkeyPatch) -> list[bool]:
    calls: list[bool] = []

    def forbidden(*_args: object, **_kwargs: object) -> None:
        calls.append(True)
        raise AssertionError("Resource admission must run before asarray")

    monkeypatch.setattr(tifffile.TiffPage, "asarray", forbidden)
    return calls


@pytest.mark.parametrize("reader", [load_tiff, load_ocr_image])
def test_tiny_compressed_file_with_giant_header_never_decodes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reader: Callable[[Path], object]
) -> None:
    path = tmp_path / "compressed.tif"
    tifffile.imwrite(path, np.zeros((4, 4), dtype=np.uint8), compression="deflate", metadata=None)
    with tifffile.TiffFile(path, mode="r+") as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        page.tags["ImageWidth"].overwrite(65535)
        page.tags["ImageLength"].overwrite(65535)
    before = path.read_bytes()
    assert len(before) < 1024
    calls = forbid_decode(monkeypatch)
    with pytest.raises(ImageInputError, match="预算"):
        reader(path)
    assert not calls and path.read_bytes() == before


@pytest.mark.parametrize("layout", ["gray_alpha", "rgb_five", "volume", "multipage"])
def test_unsupported_layout_never_decodes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, layout: str
) -> None:
    path = tmp_path / "unsupported.tif"
    if layout == "gray_alpha":
        tifffile.imwrite(
            path,
            np.ones((4, 4, 2), dtype=np.uint8),
            photometric="minisblack",
            planarconfig="contig",
        )
    elif layout == "rgb_five":
        tifffile.imwrite(
            path, np.ones((4, 4, 5), dtype=np.uint8), photometric="rgb", planarconfig="contig"
        )
    elif layout == "volume":
        tifffile.imwrite(
            path, np.ones((3, 4, 4), dtype=np.uint8), photometric="minisblack", volumetric=True
        )
    else:
        with tifffile.TiffWriter(path) as writer:
            for _ in range(2):
                writer.write(np.ones((4, 4), dtype=np.uint8))
    calls = forbid_decode(monkeypatch)
    with pytest.raises(ImageInputError, match="二维|通道|单页"):
        load_tiff(path)
    assert not calls


@pytest.mark.parametrize("metadata", ["tile", "compressed_count"])
def test_tiny_visible_image_with_huge_decoder_segment_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, metadata: str
) -> None:
    path = tmp_path / "decoder.tif"
    tifffile.imwrite(
        path,
        np.ones((4, 4), dtype=np.uint8),
        compression="deflate",
        tile=(16, 16) if metadata == "tile" else None,
        metadata=None,
    )
    with tifffile.TiffFile(path, mode="r+") as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        if metadata == "tile":
            page.tags["TileWidth"].overwrite(65536)
            page.tags["TileLength"].overwrite(65536)
        else:
            page.tags["StripByteCounts"].overwrite(3 * 1024**3)
    assert path.stat().st_size < 1024
    calls = forbid_decode(monkeypatch)
    with pytest.raises(ImageInputError, match="峰值内存预算"):
        load_tiff(path)
    assert not calls


@pytest.mark.parametrize("reader", [load_tiff, load_ocr_image])
def test_memory_boundary_and_bounded_decoder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reader: Callable[[Path], object]
) -> None:
    path = tmp_path / "memory.tif"
    tifffile.imwrite(path, np.ones((2, 2), dtype=np.uint8), metadata=None)
    calls: list[dict[str, Any]] = []
    decode = tifffile.TiffPage.asarray

    def observed(page: tifffile.TiffPage, **kwargs: Any) -> Any:
        calls.append(kwargs)
        return decode(page, **kwargs)

    # Four gray bytes + eight immutable/copy bytes + four mask bytes + 24 OCR
    # bytes + twelve segment/scratch bytes + three four-byte encoded groups.
    admitted_peak = 64
    monkeypatch.setattr(tifffile.TiffPage, "asarray", observed)
    monkeypatch.setenv("BIOIMAGE_TIFF_MAX_PEAK_BYTES", str(admitted_peak))
    reader(path)
    assert calls == [{"maxworkers": 1, "buffersize": 16 * 1024**2}]
    monkeypatch.setenv("BIOIMAGE_TIFF_MAX_PEAK_BYTES", str(admitted_peak - 1))
    with pytest.raises(ImageInputError, match="峰值内存预算"):
        reader(path)
    assert len(calls) == 1


@pytest.mark.parametrize("value", ["", "0", "-1", "1.5", "NaN", "１２", str(2**63)])
@pytest.mark.parametrize("variable", ["BIOIMAGE_TIFF_MAX_PIXELS", "BIOIMAGE_TIFF_MAX_PEAK_BYTES"])
def test_bad_policy_fails_before_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str, variable: str
) -> None:
    path = tmp_path / "small.tif"
    tifffile.imwrite(path, np.ones((2, 2), dtype=np.uint8))
    monkeypatch.setenv(variable, value)
    calls = forbid_decode(monkeypatch)
    with pytest.raises(ImageInputError, match=variable):
        load_tiff(path)
    assert not calls


def test_crop_second_read_enforces_current_policy_without_publishing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, target = tmp_path / "source.tif", tmp_path / "crop.tif"
    tifffile.imwrite(source, np.ones((4, 4), dtype=np.uint8))
    original = source.read_bytes()
    calls: list[bool] = []

    def validate_then_tighten(path: str | Path) -> LoadedTiff:
        nonlocal calls
        image = load_tiff(path)
        calls = forbid_decode(monkeypatch)
        monkeypatch.setenv("BIOIMAGE_TIFF_MAX_PIXELS", "15")
        return image

    monkeypatch.setattr(crop_export, "load_tiff", validate_then_tighten)
    request = CropRequest(sha256(original).hexdigest(), 0, LaneROI("crop", 0, 0, 2, 2))
    with pytest.raises(ImageInputError, match="预算"):
        crop_export.export_crop(str(source), request, str(target))
    assert not calls and not target.exists() and not list(tmp_path.glob(".wb-crop-*"))
    assert source.read_bytes() == original


@pytest.mark.parametrize("dtype", ["float32", "uint32", "int16", "bool"])
def test_unsupported_dtype_rejected_before_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dtype: str
) -> None:
    path = tmp_path / "unsupported.tif"
    tifffile.imwrite(path, np.ones((4, 4), dtype=dtype), photometric="minisblack")
    calls = forbid_decode(monkeypatch)
    with pytest.raises(ImageInputError, match="uint8"):
        load_tiff(path)
    assert not calls


@pytest.mark.parametrize("dtype", ["uint8", "uint16"])
@pytest.mark.parametrize("layout", ["gray", "rgb", "rgba", "rgb_planar", "rgba_planar"])
def test_pixel_budget_boundary_and_exact_small_pixels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dtype: str, layout: str
) -> None:
    gray = np.arange(12, dtype=dtype).reshape(3, 4) + 1
    raw = (
        gray
        if layout == "gray"
        else np.repeat(gray[..., None], 4 if "rgba" in layout else 3, axis=2)
    )
    if "rgba" in layout:
        raw[..., 3] = np.iinfo(raw.dtype).max
    if "planar" in layout:
        raw = np.moveaxis(raw, -1, 0)
    path = tmp_path / "原图.tif"
    tifffile.imwrite(
        path,
        raw,
        photometric="minisblack" if layout == "gray" else "rgb",
        planarconfig="separate" if "planar" in layout else "contig",
        compression="deflate",
        metadata=None,
    )
    before = path.read_bytes()
    monkeypatch.setenv("BIOIMAGE_TIFF_MAX_PIXELS", "12")
    image = load_tiff(path)
    assert image.sha256 == sha256(before).hexdigest()
    assert image.pixels.dtype == gray.dtype and image.source_shape == raw.shape
    np.testing.assert_array_equal(image.pixels, gray)
    assert not image.pixels.flags.writeable
    monkeypatch.setenv("BIOIMAGE_TIFF_MAX_PIXELS", "11")
    calls = forbid_decode(monkeypatch)
    with pytest.raises(ImageInputError, match="预算"):
        load_tiff(path)
    assert not calls and path.read_bytes() == before
