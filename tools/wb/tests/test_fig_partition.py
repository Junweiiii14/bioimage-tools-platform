"""Sheet geometry is evidence driven, preserves segments and refuses ambiguous pitch."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.adapters import fig_quant
from wb_tool.api import (
    FigureRow,
    WBFigureProject,
    analysis_is_current,
    load_tiff,
    read_figure_project,
)
from wb_tool.domain.fig_partition import partition_sheet, sheet_lane_pitch
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.worksheet import OCRRecognition, TextBounds, TextToken


def sheet(tmp_path: Path):
    raw = np.full((600, 900), 255, dtype=np.uint8)
    tokens: list[TextToken] = []

    def token(text: str, x: int, y: int):
        tokens.append(TextToken(str(len(tokens)), text, TextBounds(x, y, x + 40, y + 12), 0.95))

    for index, n in enumerate((2, 3, 4)):
        top = 20 + index * 185
        token(f"Fig{index + 1}A", 10, top)
        for row_number, name in enumerate(("Target", "Control")):
            y = top + 30 + row_number * 60
            x = 100
            width = n * 60
            token(name, 20, y + 18)
            raw[y : y + 48, x : x + width] = 140
            for lane in range(n):
                cx = x + 30 + lane * 60
                raw[y + 14 : y + 30, cx - 18 : cx + 18] = 40
    path = tmp_path / "sheet.tif"
    tifffile.imwrite(path, raw)
    image = load_tiff(path)
    recognition = OCRRecognition(image.sha256, 900, 600, tuple(tokens), "test", ())
    source = FigureRow(
        row_id="sheet",
        source=AssetRef(
            asset_id="a",
            relative_path="inputs/sheet.tif",
            sha256=image.sha256,
            size_bytes=path.stat().st_size,
        ),
        filename=path.name,
        width=900,
        height=600,
        bit_depth=8,
    )
    return (
        path,
        image,
        recognition,
        WBFigureProject(project_id="p", rows=(source,), figure_order=("Fig1",)),
    )


def test_groups_lane_width_evidence_and_raw_coordinate_scaling(tmp_path: Path) -> None:
    _, image, recognition, _ = sheet(tmp_path)
    rows = partition_sheet(image.pixels, recognition)
    assert [r.figure for r in rows] == ["Fig1A", "Fig1A", "Fig2A", "Fig2A", "Fig3A", "Fig3A"]
    assert [len(r.lanes) for r in rows] == [2, 2, 3, 3, 4, 4]
    assert [r.protein for r in rows] == ["Target", "Control"] * 3
    assert all(r.crop.x0 == 102 and r.crop.y0 >= 52 for r in rows)
    assert all(all(r.crop.x0 <= lane.x0 < lane.x1 <= r.crop.x1 for lane in r.lanes) for r in rows)
    assert sheet_lane_pitch((LaneROI("a", 0, 0, 120, 30), LaneROI("b", 0, 40, 120, 70))) is None


def test_schema9_installs_unreviewed_machine_plans_roundtrips_and_cancel_preserves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, image, recognition, project = sheet(tmp_path)

    def recognize(*args: object, **kwargs: object) -> OCRRecognition:
        return recognition

    monkeypatch.setattr(fig_quant, "recognize_figure", recognize)
    prepared = fig_quant.prepare_fig_quantification(path, project, "sheet")
    assert len(prepared.rows) == 6 and len(prepared.analyses) == 6
    assert prepared.partition_sources == (recognition,) and not any(
        r.reviewed for r in prepared.rows
    )
    assert all(analysis_is_current(prepared, p) for p in prepared.analyses)
    assert read_figure_project(prepared.model_dump_json().encode()) == prepared
    assert project.rows[0].roi is None and load_tiff(path).sha256 == image.sha256
    with pytest.raises(ValueError, match="取消"):
        fig_quant.prepare_fig_quantification(path, project, "sheet", cancelled=lambda: True)
    with pytest.raises(ValueError, match="已切分"):
        fig_quant.prepare_fig_quantification(path, prepared, prepared.rows[0].row_id)
