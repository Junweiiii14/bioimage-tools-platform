"""Frozen independent WBQuant outputs and strict geometry/provenance regression checks."""

from dataclasses import dataclass, replace
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pytest
from pydantic import TypeAdapter
from wb_tool.api import (
    AnalysisRequest,
    LaneROI,
    ProjectRowAnalysis,
    analyze_annotations,
    automatic_project_row,
    load_tiff,
    propose_quant_lanes,
    read_figure_project,
    replan_quant_lanes,
    row_is_ready,
    update_quant_lane,
    wbquant_csv_bytes,
    wbquant_table_rows,
    wbquant_xlsx_bytes,
)
from wb_tool.domain.quantify import integrate_profile

from tools.wb.tests.test_automatic_wb import project_for, source
from tools.wb.tests.test_project_analysis import complete, configured


@dataclass
class ExpectedLane:
    roi: tuple[int, int, int, int]
    bands: tuple[tuple[float, ...], ...]


@dataclass
class Case:
    name: str
    depth: int
    expected: tuple[ExpectedLane, ...]


CASES = TypeAdapter(list[Case]).validate_json(
    (Path(__file__).parent / "fixtures/wbquant143.json").read_bytes()
)


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_frozen_original_143_detection_and_signal(case: Case) -> None:
    # These expected values were produced by the separately installed 1.4.3
    # reference, not by the vendored module or the implementation under test.
    y = np.arange(96, dtype=float)
    signal = 130 * np.exp(-(((y - 40) / 6) ** 2))
    if case.name == "double":
        signal += 95 * np.exp(-(((y - 70) / 4) ** 2))
    if case.name == "flat":
        signal *= 0
    if case.name == "weak":
        signal *= 0.06
    raw = np.repeat(np.rint(220 - signal)[:, None], 60, axis=1)
    if case.name == "frame":
        raw[:2] = 0
        raw[-2:] = 0
    pixels = raw.astype(np.uint8 if case.depth == 8 else np.uint16)
    if case.depth == 16:
        pixels *= 257
    before = pixels.copy()
    proposals = propose_quant_lanes(
        pixels, (LaneROI("1", 0, 0, 30, 96), LaneROI("2", 30, 0, 60, 96))
    )
    for proposal, expected in zip(proposals, case.expected, strict=True):
        roi = proposal.roi
        assert (roi.x0, roi.y0, roi.x1, roi.y1) == expected.roi
        actual_bands = [b for b in proposal.bands if b.bounds is not None]
        assert len(actual_bands) == len(expected.bands)
        profile = (1 << case.depth) - 1 - pixels[roi.y0 : roi.y1, roi.x0 : roi.x1].mean(axis=1)
        for band, (left, right, base_left, base_right, signal) in zip(
            actual_bands, expected.bands, strict=True
        ):
            assert band.bounds and band.baseline
            assert (band.bounds.left, band.bounds.right) == (left, right)
            assert (band.baseline.left_value, band.baseline.right_value) == (base_left, base_right)
            assert integrate_profile(
                profile.tolist(), band.bounds, band.baseline
            ).signal == pytest.approx(signal, abs=1e-10, rel=1e-12)
    np.testing.assert_array_equal(before, pixels)


def test_independent_geometry_roundtrip_and_replan(tmp_path: Path) -> None:
    path = source(tmp_path)
    project = automatic_project_row(path, project_for(path), "r", quant_policy="wbquant_1_4_3@1")
    plan = project.analyses[0]
    lane = plan.request.lanes[0]
    roi = replace(lane.roi, x0=lane.roi.x0 + 2, x1=lane.roi.x1 - 2)
    edited = update_quant_lane(project, "r", lane.roi.lane_id, roi=roi)
    assert edited.analyses[0].run is None
    assert edited.analyses[0].request.lanes[0].bands[0].bounds is None
    assert row_is_ready(edited, edited.rows[0])
    replanned = replan_quant_lanes(path, edited, "r")
    assert replanned.analyses[0].request.lanes[0].bands[0].bounds is not None
    assert row_is_ready(replanned, replanned.rows[0])
    assert read_figure_project(replanned.model_dump_json().encode()) == replanned
    result = analyze_annotations(load_tiff(path), replanned.analyses[0].request)
    assert len(result.lanes) == 5
    with pytest.raises(ValueError, match="重叠"):
        update_quant_lane(project, "r", lane.roi.lane_id, roi=replace(lane.roi, x1=lane.roi.x1 + 1))
    with pytest.raises(ValueError):
        ProjectRowAnalysis(
            row_id=plan.row_id,
            crop=plan.crop,
            request=replace(replanned.analyses[0].request, geometry_policy="fixed_grid@1"),
        )


def test_legacy_request_policy_defaults() -> None:
    data = (
        b'{"source_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
        b'"revision":0,"polarity":"dark","lanes":[{"roi":{"lane_id":"1",'
        b'"x0":0,"y0":0,"x1":5,"y1":5},"bands":[]}]}'
    )
    request = TypeAdapter(AnalysisRequest).validate_json(data)
    assert request.geometry_policy == "fixed_grid@1"
    assert request.quant_policy == "legacy_bounds@1"


def test_export_formats_and_stale_result_exclusion(tmp_path: Path) -> None:
    project, paths = configured(tmp_path)
    project, results = complete(project, paths)
    rows = wbquant_table_rows(project, results)
    assert rows[0] == ("组序", "组名", "条带", "泳道 1", "泳道 2", "泳道 3")
    assert rows[1][:3] == ("第 1 组", "Fig1", "AKT")
    assert rows[1][3:] == (4000, None, 0)
    csv = wbquant_csv_bytes(project, results).decode("utf-8-sig")
    assert "4000.00,,0.00" in csv
    assert all(
        value is None
        for row in wbquant_table_rows(project, (replace(results[0], run_id="old"), results[1]))[1:2]
        for value in row[3:]
    )
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with ZipFile(BytesIO(wbquant_xlsx_bytes(project, results))) as archive:
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        pane = root.find(f"{ns}sheetViews/{ns}sheetView/{ns}pane")
        assert pane is not None and pane.get("topLeftCell") == "C1"
        assert pane.get("xSplit") == "2" and pane.get("ySplit") is None
        merges = root.findall(f"{ns}mergeCells/{ns}mergeCell")
        assert [m.get("ref") for m in merges] == ["A1:A3", "A5:A6"]
        first = root.find(f"{ns}sheetData/{ns}row/{ns}c/{ns}is/{ns}t")
        assert first is not None and first.text == "Fig1"
        assert b'numFmtId="2"' in archive.read("xl/styles.xml")


def test_multi_band_missing_slot_preserves_vertical_order(tmp_path: Path) -> None:
    from wb_tool.api import BandAnnotation, project_with_analyses

    project, paths = configured(tmp_path)
    plan = project.analyses[0]
    lane = plan.request.lanes[0]
    changed = replace(
        lane,
        bands=(
            lane.bands[0],
            BandAnnotation("target-2", None),
            replace(lane.bands[0], band_id="target-3"),
        ),
    )
    request = replace(
        plan.request,
        lanes=(changed, *plan.request.lanes[1:]),
        geometry_policy="independent_lanes@1",
        quant_policy="wbquant_1_4_3@1",
    )
    project = project_with_analyses(
        project, (plan.model_copy(update={"request": request}), *project.analyses[1:])
    )
    project, results = complete(project, paths)
    rows = wbquant_table_rows(project, results)
    assert [row[3] for row in rows[1:4]] == [4000, None, 4000]
    assert results[0].result.lanes[0].bands[1].status == "not_detected"


def test_display_order_and_automatic_layout_preservation(tmp_path: Path) -> None:
    from wb_tool.api import (
        FigureColumn,
        FigureComposition,
        FigureSlice,
        ordered_quant_rows,
        with_figure_layout,
    )

    project, paths = configured(tmp_path)
    composition = FigureComposition(
        slices=(
            FigureSlice(
                row_id="row0", figure="Fig1", line=2, position=1, first_lane=1, last_lane=3
            ),
            FigureSlice(
                row_id="row1", figure="Fig1", line=1, position=1, first_lane=1, last_lane=3
            ),
            FigureSlice(
                row_id="missing", figure="Fig2", line=1, position=1, first_lane=1, last_lane=2
            ),
        ),
        columns=(FigureColumn(figure="Fig1", column=2), FigureColumn(figure="Fig2", column=1)),
    )
    laid_out = with_figure_layout(project, composition)
    assert [row.row_id for row in ordered_quant_rows(laid_out)] == ["row1", "row0", "missing"]
    completed, loaded = complete(laid_out, paths)
    assert wbquant_table_rows(completed, loaded)[1][3] == 8000
    refreshed = automatic_project_row(paths[0], laid_out, "row0", quant_policy="wbquant_1_4_3@1")
    assert refreshed.composition == composition
    # A whole-row segment adapts only its N and retains every other placement/column.
    expanded = automatic_project_row(
        paths[0], refreshed, "row0", lane_count=4, quant_policy="wbquant_1_4_3@1"
    )
    assert expanded.composition.slices[0].last_lane == 4
    assert expanded.composition.slices[1:] == composition.slices[1:]
    assert expanded.composition.columns == composition.columns
    assert any(
        "other_rows_preserved" in warning for warning in expanded.automatic_rows[-1].warnings
    )
    # Explicit multi-segment placement cannot be silently flattened after changing N.
    split = composition.model_copy(
        update={
            "slices": (
                composition.slices[0].model_copy(update={"last_lane": 1}),
                composition.slices[0].model_copy(update={"line": 3, "first_lane": 2}),
                *composition.slices[1:],
            )
        }
    )
    split_project = with_figure_layout(project, split)
    assert [row.row_id for row in ordered_quant_rows(split_project)] == ["row1", "row0", "missing"]
    with pytest.raises(ValueError, match="未重置"):
        automatic_project_row(
            paths[0], split_project, "row0", lane_count=4, quant_policy="wbquant_1_4_3@1"
        )
    assert split_project.composition == split
    assert [row.row_id for row in ordered_quant_rows(project)] == ["row0", "row1", "missing"]


def test_appended_pending_sources_receive_segments_without_resetting_layout(tmp_path: Path) -> None:
    from wb_tool.api import FigureColumn, FigureRow, FigureSlice, with_figure_layout

    path = source(tmp_path)
    project = automatic_project_row(path, project_for(path), "r", quant_policy="wbquant_1_4_3@1")
    original = project.composition.model_copy(
        update={
            "columns": (FigureColumn(figure="Fig1", column=3),),
            "slices": (
                FigureSlice(
                    row_id="r", figure="Fig1", line=2, position=1, first_lane=1, last_lane=5
                ),
            ),
        }
    )
    project = with_figure_layout(project, original)
    row = project.rows[0]
    second = FigureRow.model_validate(
        {
            **row.model_dump(),
            "row_id": "second",
            "figure": "Fig2",
            "roi": None,
            "lane_count": 6,
            "reviewed": False,
        }
    )
    third = second.model_copy(update={"row_id": "third", "figure": "Fig3"})
    project = project.model_copy(
        update={"rows": (*project.rows, second, third), "figure_order": ("Fig1", "Fig2", "Fig3")}
    )
    first_done = automatic_project_row(path, project, "second", quant_policy="wbquant_1_4_3@1")
    assert first_done.composition.slices[0] == original.slices[0]
    assert first_done.composition.columns[0] == original.columns[0]
    assert [(s.row_id, s.last_lane) for s in first_done.composition.slices] == [
        ("r", 5),
        ("second", 5),
        ("third", 6),
    ]
    finished = automatic_project_row(path, first_done, "third", quant_policy="wbquant_1_4_3@1")
    assert finished.composition.slices[:2] == first_done.composition.slices[:2]
    assert finished.composition.slices[-1].last_lane == 5
    assert all(row.roi is not None for row in finished.rows)
