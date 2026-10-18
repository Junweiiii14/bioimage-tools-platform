"""Analytic integer geometry and lossless source samples, including color and MINISWHITE."""

import json
import struct
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import tifffile
from wb_tool.api import CropRequest, LaneROI, export_crop, fixed_lane_grid, load_tiff


def test_genuinely_changed_resolution_is_not_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, target = tmp_path / "device.tiff", tmp_path / "crop.tiff"
    tifffile.imwrite(source, np.zeros((10, 12), dtype=np.uint16), resolution=(600, 600))
    original = source.read_bytes()
    write = tifffile.imwrite

    def wrong_resolution(*args: Any, **kwargs: Any) -> None:
        kwargs["resolution"] = (720, 720)
        write(*args, **kwargs)

    monkeypatch.setattr(tifffile, "imwrite", wrong_resolution)
    request = CropRequest(sha256(original).hexdigest(), 0, LaneROI("r", 2, 3, 8, 7))
    with pytest.raises(ValueError, match="分辨率写后核验失败"):
        export_crop(str(source), request, str(target))
    assert not target.exists() and not list(tmp_path.glob(".wb-crop-*"))
    assert source.read_bytes() == original


def test_equivalent_unreduced_device_resolution_is_accepted(tmp_path: Path) -> None:
    source, target = tmp_path / "device.tiff", tmp_path / "crop.tiff"
    pixels = np.arange(120, dtype=np.uint16).reshape(10, 12)
    tifffile.imwrite(source, pixels, resolution=(600, 600), resolutionunit="INCH", byteorder="<")
    with tifffile.TiffFile(source) as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        offsets = [page.tags[name].valueoffset for name in ("XResolution", "YResolution")]
    # Real acquisition headers can store unreduced rationals. Patch only these
    # two known header slots; the input pixels remain unchanged.
    with source.open("r+b") as stream:
        for offset in offsets:
            stream.seek(offset)
            stream.write(struct.pack("<II", 6000000, 10000))
    original = source.read_bytes()
    request = CropRequest(sha256(original).hexdigest(), 0, LaneROI("r", 2, 3, 8, 7))
    export_crop(str(source), request, str(target))
    with tifffile.TiffFile(target) as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        assert page.tags["XResolution"].value == (600, 1)
        assert page.tags["YResolution"].value == (600, 1)
        np.testing.assert_array_equal(page.asarray(), pixels[3:7, 2:8])
    assert source.read_bytes() == original


def test_fixed_grid_keeps_blanks_and_remainder() -> None:
    # x=10..29; exclude left marker of width 4 and right border 1 => fourteen pixels.
    region = LaneROI("row", 10, 3, 29, 9)
    lanes = fixed_lane_grid(region, 3, exclude_left=4, exclude_right=1)
    assert [(r.x0, r.x1) for r in lanes] == [(14, 18), (18, 23), (23, 28)]
    assert [(r.y0, r.y1) for r in lanes] == [(3, 9)] * 3
    assert [r.lane_id for r in lanes] == ["row:01", "row:02", "row:03"]
    assert fixed_lane_grid(region, 3, exclude_left=4, exclude_right=1) == lanes
    for count in (0, 97, True):
        with pytest.raises(ValueError):
            fixed_lane_grid(region, count)
    with pytest.raises(ValueError, match="太窄"):
        fixed_lane_grid(region, 3, exclude_left=17)
    with pytest.raises(ValueError):
        fixed_lane_grid(region, 3, exclude_right=-1)


@pytest.mark.parametrize("mode", ["u8", "u16", "big16", "white", "rgb", "rgba", "planar"])
def test_crop_preserves_samples_and_provenance(tmp_path: Path, mode: str) -> None:
    dtype = np.dtype(">u2" if mode == "big16" else "uint16" if mode in ("u16", "rgba") else "uint8")
    values = np.arange(120, dtype=dtype).reshape(10, 12)
    args: dict[str, Any] = {}
    expected = values
    if mode in ("rgb", "rgba", "planar"):
        expected = np.stack([values, values + 1, values + 2], axis=-1)
        args["photometric"] = "rgb"
        if mode == "rgba":
            expected = np.concatenate(
                [expected, np.full((10, 12, 1), 65535, dtype=np.uint16)], axis=-1
            )
        values = np.moveaxis(expected, -1, 0) if mode == "planar" else expected
        if mode == "planar":
            args["planarconfig"] = "separate"
    elif mode == "white":
        args["photometric"] = "miniswhite"
    source, destination = tmp_path / "原图.tif", tmp_path / "裁剪.tif"
    tifffile.imwrite(source, values, resolution=(300, 240), resolutionunit="INCH", **args)
    original = source.read_bytes()
    request = CropRequest(sha256(original).hexdigest(), 3, LaneROI("目标蛋白", 2, 3, 8, 7))
    assert export_crop(str(source), request, str(destination)) == str(destination)
    assert source.read_bytes() == original
    with tifffile.TiffFile(destination) as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        actual = page.asarray()
        np.testing.assert_array_equal(actual, expected[3:7, 2:8])
        assert actual.dtype.kind == "u" and actual.dtype.itemsize == dtype.itemsize
        meta = json.loads(page.description)
        assert meta["source_sha256"] == request.source_sha256
        assert meta["source_revision"] == 3 and meta["roi"]["lane_id"] == "目标蛋白"
        assert meta["roi"]["x0"] == 2 and meta["roi"]["x1"] == 8
        assert meta["transforms"] == []
        samples = page.asarray().astype(np.dtype(meta["dtype"]))
        assert sha256(samples.tobytes()).hexdigest() == meta["pixel_sha256"]
        assert page.tags["XResolution"].value == (300, 1)
        assert page.tags["YResolution"].value == (240, 1)
        if mode == "white":
            assert page.photometric == tifffile.PHOTOMETRIC.MINISWHITE
    # Quantitative grayscale of a raw color crop agrees with the same original region.
    np.testing.assert_array_equal(load_tiff(destination).pixels, load_tiff(source).pixels[3:7, 2:8])
    before = destination.read_bytes()
    with pytest.raises(FileExistsError):
        export_crop(str(source), request, str(destination))
    assert destination.read_bytes() == before


def test_crop_rejects_source_mismatch_and_bounds(tmp_path: Path) -> None:
    source, target = tmp_path / "source.tif", tmp_path / "crop.tif"
    tifffile.imwrite(source, np.full((3, 5), 80, dtype=np.uint8))
    digest = sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="来源"):
        export_crop(str(source), CropRequest("f" * 64, 0, LaneROI("x", 0, 0, 2, 2)), str(target))
    with pytest.raises(ValueError, match="超出"):
        export_crop(str(source), CropRequest(digest, 0, LaneROI("x", 0, 0, 6, 2)), str(target))
    assert not target.exists() and not list(tmp_path.glob(".wb-crop-*"))
