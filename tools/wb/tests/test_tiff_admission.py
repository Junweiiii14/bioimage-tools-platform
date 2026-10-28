"""Reject resource-heavy or unsupported metadata before any pixel decode."""

import lzma
import struct
import zlib
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
@pytest.mark.parametrize(
    "variable",
    [
        "BIOIMAGE_TIFF_MAX_PIXELS",
        "BIOIMAGE_TIFF_MAX_PEAK_BYTES",
        "BIOIMAGE_TIFF_LZMA_MAX_MEMORY_BYTES",
    ],
)
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


def encoded_tiff(path: Path, compression: int, payload: bytes, *, fillorder: int = 1) -> None:
    """Write only tiny test data, then change its codec declaration and byte count."""
    tifffile.imwrite(
        path,
        np.ones((4, 4), dtype=np.uint8),
        metadata=None,
        extratags=[(65000, "H", 1, fillorder, False)],
    )
    with tifffile.TiffFile(path, mode="r+") as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        page.tags["Compression"].overwrite(compression)
        page.tags["StripByteCounts"].overwrite(len(payload))
        offset = page.dataoffsets[0]
        fillorder_offset = page.tags[65000].offset
    with path.open("r+b") as stream:
        stream.seek(fillorder_offset)
        stream.write(struct.pack("<H", 266))
        stream.seek(offset)
        stream.write(payload)


@pytest.mark.parametrize("compression", [8, 32946, 50013, 32773, 34925])
def test_compressed_content_cannot_exceed_declared_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, compression: int
) -> None:
    expanded = bytes([1]) * 65536  # A controlled 64 KiB, never an actual OOM probe.
    payload = (
        bytes([129, 1]) * 512
        if compression == 32773
        else lzma.compress(expanded)
        if compression == 34925
        else zlib.compress(expanded)
    )
    path = tmp_path / "understated.tif"
    encoded_tiff(path, compression, payload)
    monkeypatch.setenv("BIOIMAGE_TIFF_MAX_PEAK_BYTES", str(128 * 1024**2))
    calls = forbid_decode(monkeypatch)
    with pytest.raises(ImageInputError, match="展开|压缩"):
        load_tiff(path)
    assert not calls


def test_lzma_dictionary_limit_before_decoder_allocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = bytearray(lzma.compress(bytes([1]) * 16, format=lzma.FORMAT_ALONE))
    # Modify the ALONE header's dictionary field without allocating that dictionary.
    payload[1:5] = struct.pack("<I", 128 * 1024**2)
    path = tmp_path / "dictionary.tif"
    encoded_tiff(path, 34925, bytes(payload))
    calls = forbid_decode(monkeypatch)
    with pytest.raises(ImageInputError, match="LZMA|压缩"):
        load_tiff(path)
    assert not calls


@pytest.mark.parametrize("compression", [8, 32946, 50013, 32773, 34925])
@pytest.mark.parametrize("fillorder", [1, 2])
def test_valid_compression_keeps_pixels_and_fillorder(
    tmp_path: Path, compression: int, fillorder: int
) -> None:
    expanded = bytes([1]) * 16
    payload = (
        bytes([128, 7]) + bytes([1]) * 8 + bytes([249, 1])
        if compression == 32773
        else lzma.compress(expanded)
        if compression == 34925
        else zlib.compress(expanded)
    )
    if fillorder == 2:
        payload = bytes(int(f"{value:08b}"[::-1], 2) for value in payload)
    path = tmp_path / "valid-compressed.tif"
    encoded_tiff(path, compression, payload, fillorder=fillorder)
    before = path.read_bytes()
    image = load_tiff(path)
    assert image.sha256 == sha256(before).hexdigest()
    np.testing.assert_array_equal(image.pixels, np.ones((4, 4), dtype=np.uint8))
    assert path.read_bytes() == before


def test_declared_whole_strip_padding_and_concatenated_lzma_are_preserved(tmp_path: Path) -> None:
    path = tmp_path / "padded.tif"
    payload = lzma.compress(bytes([1]) * 16) + lzma.compress(bytes([2]) * 16)
    encoded_tiff(path, 34925, payload)
    with tifffile.TiffFile(path, mode="r+") as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        page.tags["RowsPerStrip"].overwrite(8)
    np.testing.assert_array_equal(load_tiff(path).pixels, np.ones((4, 4), dtype=np.uint8))


def test_compressed_reread_must_match_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "changed.tif"
    encoded_tiff(path, 8, zlib.compress(bytes([1]) * 16))

    def changed_decode(page: tifffile.TiffPage, **_kwargs: object) -> object:
        return page.decode(zlib.compress(bytes([2]) * 16), 0)

    monkeypatch.setattr(tifffile.TiffPage, "asarray", changed_decode)
    with pytest.raises(ImageInputError, match="压缩块改变"):
        load_tiff(path)


def test_lzma_memory_policy_can_be_lowered(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "lzma-policy.tif"
    encoded_tiff(path, 34925, lzma.compress(bytes([1]) * 16))
    monkeypatch.setenv("BIOIMAGE_TIFF_LZMA_MAX_MEMORY_BYTES", str(1024**2))
    calls = forbid_decode(monkeypatch)
    with pytest.raises(ImageInputError, match="LZMA"):
        load_tiff(path)
    assert not calls


@pytest.mark.parametrize("compression", ["deflate", "lzma"])
def test_planar_rgba16_tiles_preserve_padding_and_segment_identities(
    tmp_path: Path, compression: str
) -> None:
    gray = np.arange(17 * 19, dtype=np.uint16).reshape(17, 19) + 1000
    raw = np.stack([gray, gray, gray, np.full_like(gray, 65535)])
    path = tmp_path / "tiled-planar.tif"
    tifffile.imwrite(
        path,
        raw,
        photometric="rgb",
        planarconfig="separate",
        tile=(16, 16),
        compression=compression,
    )
    np.testing.assert_array_equal(load_tiff(path).pixels, gray)


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
