"""Automatic geometry and immutable original-pixel analysis, with explicit provenance."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.api import (
    AutoWBSettings,
    BandBounds,
    FigureRow,
    LaneROI,
    WBAutomaticProject,
    WBFigureProject,
    analysis_is_current,
    analyze_annotations,
    automatic_project_row,
    detect_automatic_geometry,
    install_automatic_result,
    load_tiff,
    prepare_project_analyses,
    read_figure_project,
    row_is_ready,
    suggest_analysis_for_crop,
    suggest_automatic_wb,
    with_automatic_rows,
)


def source(tmp_path: Path, light: bool = False) -> Path:
    # Independent geometry: 5 rectangular sample bands, equally spaced; no marker.
    a = np.full((180, 360), 50000, dtype=np.uint16)
    for x in (60, 120, 180, 240, 300):
        a[70:85, x - 17 : x + 17] = 15000
    if light:
        a = 65535 - a
    path = tmp_path / "original.tif"
    tifffile.imwrite(path, a)
    return path


def project_for(path: Path) -> WBFigureProject:
    image = load_tiff(path)
    return WBFigureProject(
        project_id="p",
        figure_order=("Fig1",),
        rows=(
            FigureRow(
                row_id="r",
                source=AssetRef(
                    asset_id="s",
                    relative_path="inputs/s.tif",
                    sha256=image.sha256,
                    size_bytes=path.stat().st_size,
                ),
                filename=path.name,
                width=image.pixels.shape[1],
                height=image.pixels.shape[0],
                bit_depth=16,
                protein="Unassigned",
            ),
        ),
    )


@pytest.mark.parametrize("light", [False, True])
def test_detect_five_original_lanes_and_bounds(tmp_path: Path, light: bool) -> None:
    image = load_tiff(source(tmp_path, light))
    before = image.pixels.copy()
    result = suggest_automatic_wb(
        image,
        row_id="r",
        revision=0,
        settings=AutoWBSettings(polarity="light" if light else "dark"),
    )
    assert result.estimated_lane_count == 5
    assert result.requests
    roi = result.detection.candidates[0].roi
    assert roi.y0 <= 70 and roi.y1 >= 85
    assert roi.x0 < 43 and roi.x1 > 317
    analysis = analyze_annotations(image, result.requests[0])
    for lane in analysis.lanes:
        band = lane.bands[0]
        assert band.status == "valid" and band.signal is not None and band.signal > 0
    assert np.array_equal(image.pixels, before)
    assert result.algorithm_id == "automatic_wb_proposals@1"


@pytest.mark.parametrize("noise", [False, True])
def test_blank_and_noise_do_not_fabricate_success(noise: bool) -> None:
    a = np.full((180, 360), 40000, dtype=np.uint16)
    if noise:
        a = np.clip(
            a.astype(float) + np.random.default_rng(8).normal(0, 50, a.shape), 0, 65535
        ).astype(np.uint16)
    detection = detect_automatic_geometry(a, AutoWBSettings())
    assert not detection.candidates
    assert "no_sample_bands" in detection.flags


def test_left_marker_only_not_sample() -> None:
    a = np.full((180, 360), 50000, dtype=np.uint16)
    a[65:85, 20:70] = 10000
    assert not detect_automatic_geometry(a, AutoWBSettings()).candidates


def test_two_candidate_rows() -> None:
    a = np.full((250, 360), 50000, dtype=np.uint16)
    for y in (70, 170):
        for x in (60, 120, 180, 240, 300):
            a[y : y + 12, x - 17 : x + 17] = 15000
    r = detect_automatic_geometry(a, AutoWBSettings())
    assert len(r.candidates) == 2
    assert all(len(c.detected_lanes) == 5 for c in r.candidates)


def test_explicit_grid_preserves_blank_lane(tmp_path: Path) -> None:
    path = source(tmp_path)
    image = load_tiff(path)
    a = image.pixels.copy()
    a[:, 163:197] = 50000
    tifffile.imwrite(tmp_path / "blank.tif", a)
    image = load_tiff(tmp_path / "blank.tif")
    request = suggest_analysis_for_crop(
        image, crop=LaneROI("r", 30, 50, 330, 110), lane_count=5, revision=0
    )
    assert len(request.lanes) == 5
    assert request.lanes[2].bands[0].bounds is None
    result = analyze_annotations(image, request)
    assert result.lanes[2].bands[0].signal is None
    assert result.lanes[2].bands[0].status == "not_detected"


def test_schema_evidence_and_stale_edits(tmp_path: Path) -> None:
    path = source(tmp_path)
    project = project_for(path)
    auto = automatic_project_row(path, project, "r")
    assert isinstance(auto, WBAutomaticProject)
    assert not auto.rows[0].reviewed
    assert row_is_ready(auto, auto.rows[0])
    assert analysis_is_current(auto, auto.analyses[0])
    restored = read_figure_project(auto.model_dump_json().encode("utf-8"))
    assert restored == auto
    rebased = prepare_project_analyses(auto, ("r",), 1)
    assert row_is_ready(rebased, rebased.rows[0])
    changed = auto.model_copy(update={"rows": (auto.rows[0].model_copy(update={"lane_count": 4}),)})
    assert not row_is_ready(changed, changed.rows[0])
    plan = auto.analyses[0]
    lane = plan.request.lanes[0]
    edited = replace(lane, bands=(replace(lane.bands[0], bounds=BandBounds(0, 2)),))
    req = replace(plan.request, lanes=(edited, *plan.request.lanes[1:]))
    changed = auto.model_copy(update={"analyses": (plan.model_copy(update={"request": req}),)})
    assert not row_is_ready(changed, changed.rows[0])
    assert with_automatic_rows(auto, auto.automatic_rows) == auto


def test_identity_and_cancellation(tmp_path: Path) -> None:
    path = source(tmp_path)
    image = load_tiff(path)
    project = project_for(path)
    result = suggest_automatic_wb(image, row_id="r", revision=0)
    with pytest.raises(ValueError, match="来源"):
        install_automatic_result(project, "r", replace(result, source_sha256="f" * 64))
    with pytest.raises(ValueError, match="过期"):
        install_automatic_result(project, "r", replace(result, source_revision=1))
    with pytest.raises(ValueError, match="取消"):
        suggest_automatic_wb(image, row_id="r", revision=0, cancelled=lambda: True)


def test_rerun_preserves_dragged_geometry(tmp_path: Path) -> None:
    path = source(tmp_path)
    auto = automatic_project_row(path, project_for(path), "r")
    crop = LaneROI("r", 25, 45, 335, 115)
    edited = auto.model_copy(update={"rows": (auto.rows[0].model_copy(update={"roi": crop}),)})
    assert not row_is_ready(edited, edited.rows[0])
    updated = automatic_project_row(path, edited, "r", lane_count=5)
    assert updated.rows[0].roi == crop and row_is_ready(updated, updated.rows[0])


def test_bounds_measure_original_unsmoothed_rectangle_area(tmp_path: Path) -> None:
    image = load_tiff(source(tmp_path))
    request = suggest_analysis_for_crop(
        image, crop=LaneROI("r", 30, 50, 330, 110), lane_count=5, revision=0
    )
    result = analyze_annotations(image, request)
    # Fifteen full-height pixels, 35000 intensity contrast, 34/60 occupied width.
    # This analytical area would differ if detection smoothing entered quantification.
    for lane in result.lanes:
        assert lane.bands[0].signal == pytest.approx(297500, abs=1e-8)


def test_quality_review_raw_integral_separate_from_valid_output(tmp_path: Path) -> None:
    from pydantic import TypeAdapter
    from tool_contracts.api import RunRecord
    from wb_tool.adapters.project_export import project_table_rows
    from wb_tool.api import (
        AnalysisResult,
        fill_project_table,
        read_project_result,
        record_project_run,
    )

    path = source(tmp_path)
    pixels = load_tiff(path).pixels.copy()
    pixels[75, 60] = 0  # Actual original rail pixel; retain frozen quality review policy.
    rail_path = tmp_path / "rail.tif"
    tifffile.imwrite(rail_path, pixels)
    project = automatic_project_row(rail_path, project_for(rail_path), "r")
    plan = project.analyses[0]
    result = analyze_annotations(load_tiff(rail_path), plan.request)
    data = TypeAdapter(AnalysisResult).dump_json(result)
    from hashlib import sha256

    result_asset = AssetRef(
        asset_id="result",
        relative_path="results/r.json",
        sha256=sha256(data).hexdigest(),
        size_bytes=len(data),
    )
    source_asset = project.rows[0].source
    assert source_asset is not None
    run = RunRecord(
        document_id="p",
        tool_id="wb-figure",
        revision=0,
        run_id="run",
        state="succeeded",
        pid=123,
        request=source_asset,
        result=result_asset,
    )
    project = record_project_run(project, "r", plan.request, run)
    loaded = read_project_result(project.analyses[0], data)
    cells = fill_project_table(project, (loaded,))
    cell = cells[0]
    assert cell.status == "quality_review" and cell.value is None
    assert cell.raw_integral is not None and cell.raw_integral > 0
    assert "自动建议计算" in cell.reason
    rows, audit = project_table_rows(project, (loaded,))
    assert rows[1][2] is None  # Main results do not promote raw measurement.
    assert audit[4][-1] == "原始积分（待复核）"
    assert audit[5][-1] == cell.raw_integral
    from io import BytesIO
    from zipfile import ZipFile

    from wb_tool.adapters.project_export import project_csv_bytes, project_xlsx_bytes

    csv = project_csv_bytes(project, (loaded,)).decode("utf-8-sig")
    assert "原始积分（待复核）" in csv and "quality_review" in csv
    with ZipFile(BytesIO(project_xlsx_bytes(project, (loaded,)))) as archive:
        audit_xml = archive.read("xl/worksheets/sheet2.xml").decode("utf-8")
        assert "原始积分（待复核）" in audit_xml and "quality_review" in audit_xml
    # Missing/mismatched cached result identities cannot expose raw measurements either.
    assert all(c.raw_integral is None for c in fill_project_table(project, ()))
    changed = replace(loaded, asset_sha256="f" * 64)
    assert all(c.raw_integral is None for c in fill_project_table(project, (changed,)))
    shifted = project.model_copy(
        update={
            "rows": (project.rows[0].model_copy(update={"roi": LaneROI("r", 20, 40, 340, 100)}),)
        }
    )
    assert all(c.raw_integral is None for c in fill_project_table(shifted, (loaded,)))
    legacy = WBFigureProject(project_id="empty")
    assert "原始积分（待复核）" not in project_table_rows(legacy, ())[1][4]


def test_raw_integral_ui_separates_quality_review(qtbot: object) -> None:
    from PySide6.QtWidgets import QApplication, QTableWidget
    from wb_tool.api import ProjectTableCell
    from wb_tool.ui.project_analysis import ProjectAnalysisPanel
    from wb_tool.ui.project_results import ProjectResultsView

    def item_text(table: QTableWidget, column: int) -> str:
        item = table.item(0, column)
        assert item is not None
        return item.text()

    assert QApplication.instance() is not None
    cell = ProjectTableCell(
        "r",
        "Fig1",
        "AKT",
        1,
        "a" * 64,
        "r-1",
        "target",
        0,
        "run",
        None,
        "quality_review",
        "质量复核",
        raw_integral=125.5,
    )
    table = ProjectResultsView()
    panel = ProjectAnalysisPanel()
    try:
        table.show_cells((cell,))
        assert item_text(table.table, 3) == ""
        assert item_text(table.table, 4) == "质量待复核"
        from PySide6.QtCore import Qt

        status = table.table.item(0, 4)
        assert status is not None and status.data(Qt.ItemDataRole.UserRole) == "quality_review"
        assert item_text(table.table, 8) == "125.5"
        panel.source_row = FigureRow(row_id="r", protein="AKT", lane_count=1)
        panel.show_cells((cell,))
        assert item_text(panel.summary, 1) == "—"
        assert item_text(panel.summary, 2) == "需质量复核"
        assert item_text(panel.summary, 3) == "125.5"
        panel.invalidate()
        assert item_text(panel.summary, 3) == "—"
    finally:
        table.close()
        panel.close()


@pytest.mark.parametrize("prior_automatic", [False, True])
def test_rerun_preserves_latest_same_source_light_polarity(
    tmp_path: Path, prior_automatic: bool
) -> None:
    from wb_tool.api import (
        make_row_analysis,
        set_row_analysis,
        update_row_analysis_request,
    )

    path = source(tmp_path, light=True)
    project = project_for(path)
    crop = LaneROI("r", 30, 50, 330, 110)
    project = project.model_copy(
        update={
            "rows": (
                project.rows[0].model_copy(update={"roi": crop, "lane_count": 5, "reviewed": True}),
            )
        }
    )
    if prior_automatic:
        # Earlier automatic dark proposal exists; the user subsequently chose light.
        automatic = automatic_project_row(path, project, "r")
        assert automatic.automatic_rows[0].settings.polarity == "dark"
        plan = automatic.analyses[0]
        project = update_row_analysis_request(
            automatic, "r", replace(plan.request, polarity="light")
        )
    else:
        # Legacy manually configured projects have no automatic provenance at all.
        project = set_row_analysis(project, make_row_analysis(project, "r", "light"))
    rerun = automatic_project_row(path, project, "r")
    assert rerun.rows[0].roi == crop
    assert rerun.analyses[0].request.polarity == "light"
    assert rerun.automatic_rows[0].settings.polarity == "light"
    result = analyze_annotations(load_tiff(path), rerun.analyses[0].request)
    for lane in result.lanes:
        assert lane.bands[0].signal == pytest.approx(297500, abs=1e-8)


def test_rerun_does_not_take_polarity_from_foreign_source_plan(tmp_path: Path) -> None:
    path = source(tmp_path)
    project = automatic_project_row(path, project_for(path), "r")
    plan = project.analyses[0]
    foreign = plan.model_copy(
        update={"request": replace(plan.request, source_sha256="f" * 64, polarity="light")}
    )
    project = project.model_copy(update={"analyses": (foreign,)})
    rerun = automatic_project_row(path, project, "r")
    assert rerun.analyses[0].request.polarity == "dark"
    assert rerun.analyses[0].request.source_sha256 == load_tiff(path).sha256
