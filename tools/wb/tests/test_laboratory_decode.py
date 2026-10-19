"""Decode once per source while preserving ordered pixels and provenance."""

import json
import weakref
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image
from wb_tool.adapters import laboratory_figure
from wb_tool.adapters.tiff_input import LoadedTiff, load_tiff
from wb_tool.api import (
    FigureSlice,
    FigureSourcePath,
    WBLayoutProject,
    initial_composition,
    render_figure,
    with_figure_layout,
)

from tools.wb.tests.test_laboratory_layout import laboratory


def repeated_source(tmp_path: Path) -> tuple[WBLayoutProject, tuple[FigureSourcePath, ...]]:
    project, paths = laboratory(tmp_path)
    # A / B / A: one source occurs in separate rows with another source between them.
    first = project.rows[0]
    assert first.roi is not None
    repeated = first.model_copy(
        update={"row_id": "repeat", "roi": replace(first.roi, lane_id="repeat")}
    )
    project = project.model_copy(update={"rows": (*project.rows[:2], repeated, *project.rows[2:])})
    composition = initial_composition(project)
    parts: list[FigureSlice] = []
    for part in composition.slices:
        if part.figure == "Fig1":
            parts.extend(
                (
                    part.model_copy(update={"last_lane": 1}),
                    part.model_copy(update={"position": 2, "first_lane": 2}),
                )
            )
        else:
            parts.append(part)
    return with_figure_layout(
        project, composition.model_copy(update={"slices": tuple(parts)}), project.layout_style
    ), paths


def test_each_source_decoded_once_released_and_order_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, paths = repeated_source(tmp_path)
    calls: list[str] = []
    arrays: list[weakref.ReferenceType[NDArray[np.uint8 | np.uint16]]] = []

    def tracked(path: str) -> LoadedTiff:
        assert all(array() is None for array in arrays), "previous full source retained"
        calls.append(path)
        original = load_tiff(path)
        arrays.append(weakref.ref(original.pixels))
        return original

    monkeypatch.setattr(laboratory_figure, "load_tiff", tracked)
    result = render_figure(project, paths)
    assert calls == [paths[2].path, paths[0].path, paths[1].path]
    assert all(array() is None for array in arrays)
    manifest = json.loads(result.manifest_json)
    assert [record["row_id"] for record in manifest["rows"]] == [
        "r2",
        "r0",
        "r0",
        "r1",
        "r1",
        "repeat",
        "repeat",
        "missing",
        "missing",
    ]
    pixels = np.frombuffer(result.rgb, np.uint8).reshape(result.height, result.width, 3)
    for record in manifest["rows"]:
        if record["status"] == "missing":
            assert record["source_sha256"] is None and record["roi"] is None
            continue
        index = 0 if record["row_id"] == "repeat" else int(record["row_id"][1:])
        roi = record["roi"]
        x0, y0, x1, y1 = record["output_box"]
        expected = np.full((y1 - y0, x1 - x0), 100 + index, np.uint8)
        for y in range(8, 13):
            for x in range(12, 18):
                if roi["x0"] <= x < roi["x1"] and roi["y0"] <= y < roi["y1"]:
                    expected[y - roi["y0"], x - roi["x0"]] = 20 + index
        np.testing.assert_array_equal(pixels[y0:y1, x0:x1], np.repeat(expected[..., None], 3, 2))
        assert record["display_pixel_sha256"] == sha256(expected.tobytes()).hexdigest()
    # Frozen with the pre-refactor renderer at 82d673a using this same deterministic fixture.
    assert (
        sha256(result.rgb).hexdigest()
        == "a92c46baee4764d323841fa11922a7656a0e13c145b0b7fe265be6ff76db9c27"
    )
    assert (
        sha256(result.manifest_json.encode()).hexdigest()
        == "1ff09bfa4d93a4a40f5748023a278b9a6c76144c7999ad2894f9dbe054d3d2a9"
    )


@pytest.mark.parametrize("fault", ["sha256", "size_bytes", "shape", "bit_depth"])
def test_shared_source_still_validates_every_row(tmp_path: Path, fault: str) -> None:
    project, paths = repeated_source(tmp_path)
    rows = list(project.rows)
    row = rows[2]
    assert row.source is not None
    if fault in ("sha256", "size_bytes"):
        value = "f" * 64 if fault == "sha256" else row.source.size_bytes + 1
        rows[2] = row.model_copy(update={"source": row.source.model_copy(update={fault: value})})
        if fault == "sha256":
            paths = (*paths, FigureSourcePath(cast(str, value), paths[0].path))
    else:
        rows[2] = row.model_copy(
            update={"width": row.width + 1} if fault == "shape" else {"bit_depth": 8}
        )
    project = project.model_copy(update={"rows": tuple(rows)})
    with pytest.raises(ValueError, match="摘要/字节数/尺寸/位深"):
        render_figure(project, paths)


@pytest.mark.parametrize("phase", ["before", "decode", "paste", "paste_shared"])
def test_cancellation_stops_without_decoding_later_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    project, paths = repeated_source(tmp_path)
    stopped = phase == "before"
    calls: list[str] = []
    paste = Image.Image.paste

    def tracked(path: str) -> LoadedTiff:
        nonlocal stopped
        calls.append(path)
        original = load_tiff(path)
        if phase == "decode":
            stopped = True
        return original

    def cancel_paste(self: Image.Image, im: Image.Image, box: tuple[int, int]) -> None:
        nonlocal stopped
        paste(self, im, box)
        if phase == "paste" or (phase == "paste_shared" and len(calls) == 2):
            stopped = True

    monkeypatch.setattr(laboratory_figure, "load_tiff", tracked)
    monkeypatch.setattr(Image.Image, "paste", cancel_paste)
    with pytest.raises(ValueError, match="已取消"):
        laboratory_figure.render_laboratory_figure(project, paths, cancelled=lambda: stopped)
    assert len(calls) == {"before": 0, "decode": 1, "paste": 1, "paste_shared": 2}[phase]


def test_corrupt_source_failure_does_not_return_partial_render(tmp_path: Path) -> None:
    project, paths = repeated_source(tmp_path)
    Path(paths[0].path).write_bytes(b"broken TIFF")
    with pytest.raises(ValueError, match="无法读取 TIFF"):
        render_figure(project, paths)
