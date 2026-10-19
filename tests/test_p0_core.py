"""Failure-oriented protocol and analytic image checks for the P0 probe."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import tifffile

from tooling.p0.imaging import digest, load, preview, profile
from tooling.p0.numerics import smooth
from tooling.p0.protocol import LIMIT, Decoder, Frame, Sequence, encode


def test_protocol_fragments_stale_and_limits() -> None:
    first = Frame(run_id="中文", seq=0, kind="hello")
    second = Frame(run_id="中文", seq=1, kind="result")
    wire = encode(first) + encode(second)
    decoder = Decoder()
    frames: list[Frame] = []
    for byte in wire:
        frames.extend(decoder.feed(bytes([byte])))
    decoder.finish()
    assert frames == [first, second]
    sequence = Sequence("中文")
    assert sequence.accept(second)
    assert not sequence.accept(first)
    assert not sequence.accept(second)
    assert not sequence.accept(Frame(run_id="old", seq=100, kind="result"))
    with pytest.raises(ValueError, match="1 MiB"):
        Decoder().feed(b"x" * (LIMIT + 1))
    with pytest.raises(ValueError):
        Decoder().feed(b"\xff\n")
    with pytest.raises(ValueError):
        Decoder().feed(b'{"kind":"unknown"}\n')
    decoder.feed(b'{"kind"')
    with pytest.raises(ValueError, match="Truncated"):
        decoder.finish()


def test_uint16_and_rgb_semantics(tmp_path: Path) -> None:
    # Exact high bits make accidental uint8 quantitative data immediately visible.
    raw = np.array([[65535, 32768], [1, 32768]], dtype=np.uint16)
    path = tmp_path / "中文.tif"
    tifffile.imwrite(path, raw)
    pixels = load(path)
    before = digest(pixels)
    display = preview(pixels)
    display[:] = 0
    np.testing.assert_array_equal(profile(pixels, (0, 0, 2, 2)), [32768.0, 32768.0])
    np.testing.assert_array_equal(profile(pixels, (1, 1, 1, 1)), [32768.0])
    assert digest(pixels) == before
    assert not pixels.flags.writeable
    with pytest.raises(ValueError):
        profile(pixels, (1, 0, 2, 1))
    with pytest.raises(ValueError):
        profile(pixels, (0, 0, 0, 1))
    rgb = np.full((2, 2, 3), 200, dtype=np.uint8)
    rgb[:, :, 0] = 10
    np.testing.assert_array_equal(profile(rgb, (0, 0, 2, 2)), [10.0, 10.0])


def test_gaussian_preserves_constant_and_source() -> None:
    source = np.full((64, 64), 12345.0, dtype=np.float32)
    result = np.empty_like(source)
    smooth(source, result)
    np.testing.assert_allclose(result, 12345.0, rtol=0, atol=0.002)
    np.testing.assert_array_equal(source, np.full_like(source, 12345.0))
