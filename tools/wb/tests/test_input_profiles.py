"""Synthetic TIFF and analytical row means, independently known pixel values."""

from hashlib import sha256
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import tifffile
from numpy.typing import NDArray
from wb_tool.api import (
    BandBounds,
    ImageInputError,
    LaneROI,
    QuantificationError,
    compute_lane_profiles,
    integrate_profile,
    load_tiff,
)


@pytest.mark.parametrize("dtype", ["uint8", "uint16"])
@pytest.mark.parametrize("width", [1, 2, 5])
def test_original_mean_profile_and_width_invariance(tmp_path: Path, dtype: str, width: int) -> None:
    maximum = 255 if dtype == "uint8" else 65535
    pixels = np.tile(
        np.array([maximum - 10, maximum - 20, maximum - 10], dtype=dtype)[:, None], (1, width)
    )
    path = tmp_path / "中文样本.tif"
    tifffile.imwrite(path, pixels, photometric="minisblack")
    before = path.read_bytes()
    image = load_tiff(path)
    assert image.sha256 == sha256(before).hexdigest()
    assert image.bit_depth == (8 if dtype == "uint8" else 16)
    assert np.array_equal(image.pixels, pixels)
    with pytest.raises(ValueError):
        image.pixels.setflags(write=True)
    lane = compute_lane_profiles(image.pixels, LaneROI("L-1", 0, 0, width, 3), "dark")
    assert lane.quantitative == (10.0, 20.0, 10.0)
    assert integrate_profile(lane.quantitative, BandBounds(0, 2)).signal == 10
    assert path.read_bytes() == before


def test_half_open_roi_and_light_polarity() -> None:
    pixels = np.array([[0, 0, 0], [0, 8, 12], [0, 18, 22], [0, 8, 12]], dtype=np.uint16)
    profiles = compute_lane_profiles(pixels, LaneROI("stable-id", 1, 1, 3, 4), "light")
    assert profiles.raw == profiles.quantitative == (10, 20, 10)
    assert profiles.dtype_max == 65535


@pytest.mark.parametrize("planar", ["contig", "separate"])
def test_rgb_integer_conversion(tmp_path: Path, planar: str) -> None:
    raw = np.zeros((2, 2, 3), dtype=np.uint16)
    raw[0, 0] = (65535, 0, 0)
    if planar == "separate":
        raw = np.moveaxis(raw, -1, 0)
    path = tmp_path / "rgb.tif"
    tifffile.imwrite(path, raw, photometric="rgb", planarconfig=planar)
    image = load_tiff(path)
    assert image.pixels[0, 0] == 19595
    assert image.conversion == "rgb-bt601-integer@1"
    assert image.source_shape == raw.shape


def test_miniswhite_is_not_silently_inverted(tmp_path: Path) -> None:
    raw = np.array([[10, 20], [30, 40]], dtype=np.uint8)
    path = tmp_path / "white.tif"
    tifffile.imwrite(path, raw, photometric="miniswhite")
    image = load_tiff(path)
    assert np.array_equal(image.pixels, raw)
    assert image.photometric == "MINISWHITE"
    assert any("MINISWHITE" in warning for warning in image.warnings)


def test_transparency_rejected(tmp_path: Path) -> None:
    path = tmp_path / "rgba.tif"
    tifffile.imwrite(path, np.zeros((2, 2, 4), dtype=np.uint8), photometric="rgb")
    with pytest.raises(ImageInputError, match="透明"):
        load_tiff(path)


def test_multi_page_rejected(tmp_path: Path) -> None:
    path = tmp_path / "multiple.tif"
    with tifffile.TiffWriter(path) as writer:
        for _ in range(2):
            writer.write(np.ones((2, 2), dtype=np.uint8), photometric="minisblack")
    with pytest.raises(ImageInputError, match="单页"):
        load_tiff(path)


def test_rotated_orientation_rejected(tmp_path: Path) -> None:
    path = tmp_path / "orientation.tif"
    tifffile.imwrite(path, np.ones((2, 2), dtype=np.uint8), extratags=[(274, "H", 1, 6, False)])
    with pytest.raises(ImageInputError, match="方向"):
        load_tiff(path)


def test_float_input_rejected(tmp_path: Path) -> None:
    path = tmp_path / "float.tif"
    tifffile.imwrite(path, np.ones((2, 2), dtype=np.float32), photometric="minisblack")
    with pytest.raises(ImageInputError, match="uint8"):
        load_tiff(path)


def test_invalid_roi_and_pixels() -> None:
    with pytest.raises(QuantificationError):
        LaneROI("L", 0, 0, 0, 2)
    with pytest.raises(QuantificationError):
        LaneROI("", 0, 0, 1, 2)
    with pytest.raises(QuantificationError):
        compute_lane_profiles(np.ones((2, 2), dtype=np.uint8), LaneROI("L", 0, 0, 3, 2), "dark")
    invalid = cast(NDArray[np.uint8 | np.uint16], np.ones((2, 2), dtype=np.float64))
    with pytest.raises(QuantificationError):
        compute_lane_profiles(invalid, LaneROI("L", 0, 0, 2, 2), "dark")
