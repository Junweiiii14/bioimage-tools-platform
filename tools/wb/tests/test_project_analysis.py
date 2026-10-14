"""Independent triangle areas and strict provenance for a multi-source project table."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from pydantic import TypeAdapter
from tool_contracts.api import AssetRef, RunRecord
from wb_tool.api import (
    AnalysisResult,
    BandBounds,
    Baseline,
    FigureRow,
    FigureTemplate,
    LaneROI,
    LoadedProjectResult,
    ProjectRowAnalysis,
    WBAnalysisProject,
    WBFigureProject,
    WBReviewProject,
    analysis_is_current,
    analyze_annotations,
    export_project_table,
    fill_project_table,
    load_tiff,
    make_row_analysis,
    prepare_project_analyses,
    project_with_analyses,
    read_figure_project,
    read_project_result,
    record_project_run,
    set_row_analysis,
    update_row_analysis_request,
)


def asset(data: bytes, name: str) -> AssetRef:
    return AssetRef(
        asset_id=name,
        relative_path=f"data/{name}.json",
        sha256=sha256(data).hexdigest(),
        size_bytes=len(data),
    )


def configured(tmp_path: Path) -> tuple[WBAnalysisProject, tuple[Path, ...]]:
    paths: list[Path] = []
    rows: list[FigureRow] = []
    profile = np.array([0, 0, 0, 10, 20, 10, 0, 0, 0, 0], dtype=np.uint16)
    for index in range(2):
        pixels = np.full((20, 30), 60000, dtype=np.uint16)
        for lane, scale in enumerate((1, 2, 0)):
            pixels[5:15, lane * 10 : (lane + 1) * 10] -= (profile * 100 * (index + 1) * scale)[
                :, None
            ]
        path = tmp_path / f"source{index}.tif"
        tifffile.imwrite(path, pixels)
        paths.append(path)
        rows.append(
            FigureRow(
                row_id=f"row{index}",
                source=asset(path.read_bytes(), f"source{index}"),
                filename=path.name,
                width=30,
                height=20,
                bit_depth=16,
                protein="AKT",
                lane_count=3,
                roi=LaneROI(f"row{index}", 0, 5, 30, 15),
                empty_lanes=(2,) if index == 0 else (),
                reviewed=True,
            )
        )
    rows.append(FigureRow(row_id="missing", figure="Fig2", protein="AKT", lane_count=2))
    base = WBFigureProject(
        project_id="project",
        rows=tuple(rows),
        figure_order=("Fig1", "Fig2"),
        template=FigureTemplate(crop_height=10),
    )
    project = project_with_analyses(base, ())
    for row in rows[:2]:
        plan = make_row_analysis(project, row.row_id, "dark")
        assert all(lane.bands[0].bounds is None for lane in plan.request.lanes)
        request = replace(
            plan.request,
            lanes=tuple(
                replace(lane, bands=(replace(lane.bands[0], bounds=BandBounds(2, 6)),))
                for lane in plan.request.lanes
            ),
        )
        plan = ProjectRowAnalysis(
            row_id=plan.row_id, crop=plan.crop, empty_lanes=plan.empty_lanes, request=request
        )
        project = set_row_analysis(project, plan)
    return prepare_project_analyses(project, ("row0", "row1"), 1), tuple(paths)


def complete(
    project: WBAnalysisProject, paths: tuple[Path, ...]
) -> tuple[WBAnalysisProject, tuple[LoadedProjectResult, ...]]:
    loaded: list[LoadedProjectResult] = []
    request_asset = asset(project.model_dump_json().encode(), "frozen")
    for plan, path in zip(project.analyses, paths, strict=True):
        result = analyze_annotations(load_tiff(path), plan.request)
        data = TypeAdapter(AnalysisResult).dump_json(result)
        run = RunRecord(
            document_id=project.project_id,
            tool_id="wb-figure",
            revision=plan.request.revision,
            run_id=plan.row_id,
            state="succeeded",
            request=request_asset,
            pid=123,
            result=asset(data, plan.row_id),
        )
        project = record_project_run(project, plan.row_id, plan.request, run)
        recorded = next(p for p in project.analyses if p.row_id == plan.row_id)
        loaded.append(read_project_result(recorded, data))
    return project, tuple(loaded)


def test_two_sources_duplicate_names_empty_missing_and_zero(tmp_path: Path) -> None:
    project, paths = configured(tmp_path)
    project, results = complete(project, paths)
    cells = fill_project_table(project, results)
    assert [c.value for c in cells] == [4000, None, 0, 8000, 16000, 0, None, None]
    assert [c.status for c in cells] == [
        "valid",
        "excluded",
        "valid",
        "valid",
        "valid",
        "valid",
        "missing_source",
        "missing_source",
    ]
    assert cells[0].source_sha256 != cells[3].source_sha256
    assert cells[0].lane_id != cells[3].lane_id
    assert all(c.protein == "AKT" for c in cells)
    raw = project.model_dump_json().encode()
    restored = read_figure_project(raw)
    assert isinstance(restored, WBAnalysisProject) and restored == project
    assert fill_project_table(restored, results) == cells
    assert b'"profiles"' not in raw  # Project size is bounded independently of result profiles.
    with pytest.raises(ValueError):
        WBReviewProject.from_bytes(raw)
    renamed = project.model_copy(
        update={"rows": tuple(row.model_copy(update={"protein": "=1+2"}) for row in project.rows)}
    )
    target = Path(export_project_table(renamed, results, str(tmp_path / "project.xlsx")))
    with ZipFile(target) as archive:
        ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        assert [float(v.text or "nan") for v in sheet.findall(".//s:v", ns)] == [
            4000,
            0,
            8000,
            16000,
            0,
        ]
        assert sheet.findall(".//s:f", ns) == []
        assert "=1+2" in archive.read("xl/worksheets/sheet1.xml").decode()
        audit = archive.read("xl/worksheets/sheet2.xml").decode()
        assert "excluded" in audit and "missing_source" in audit
        assert all(r.source.sha256 in audit for r in project.rows if r.source)
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        export_project_table(renamed, results, str(target))
    assert target.read_bytes() == before


@pytest.mark.parametrize("change", ["roi", "source", "count", "empty", "review", "height"])
def test_geometry_edits_hide_previous_values(tmp_path: Path, change: str) -> None:
    project, paths = configured(tmp_path)
    project, results = complete(project, paths)
    row = project.rows[0]
    if change == "roi":
        row = row.model_copy(update={"roi": LaneROI(row.row_id, 0, 6, 30, 16)})
    elif change == "source":
        row = row.model_copy(update={"source": project.rows[1].source})
    elif change == "count":
        row = row.model_copy(update={"lane_count": 4})
    elif change == "empty":
        row = row.model_copy(update={"empty_lanes": ()})
    elif change == "review":
        row = row.model_copy(update={"reviewed": False})
    else:
        project = project.model_copy(update={"template": FigureTemplate(crop_height=11)})
    project = project.model_copy(update={"rows": (row, *project.rows[1:])})
    assert not analysis_is_current(project, project.analyses[0])
    assert all(
        c.value is None for c in fill_project_table(project, results) if c.row_id == row.row_id
    )
    assert read_figure_project(project.model_dump_json().encode()) == project
    with pytest.raises(ValueError, match="过期"):
        prepare_project_analyses(project, (row.row_id,), 2)


def test_metadata_edits_preserve_values_rerun_invalidates_selected_only(tmp_path: Path) -> None:
    project, paths = configured(tmp_path)
    project, results = complete(project, paths)
    rows = (
        project.rows[0].model_copy(update={"protein": "p-AKT", "figure": "Fig2"}),
        *project.rows[1:],
    )
    project = project.model_copy(update={"rows": rows, "figure_order": ("Fig2", "Fig1")})
    assert next(c for c in fill_project_table(project, results) if c.row_id == "row0").value == 4000
    pending = prepare_project_analyses(project, ("row0",), 2)
    values = fill_project_table(pending, results)
    assert next(c for c in values if c.row_id == "row0").status == "not_run"
    assert next(c for c in values if c.row_id == "row1").value == 8000
    old = project.analyses[0]
    assert old.run is not None
    with pytest.raises(ValueError, match="旧运行"):
        record_project_run(pending, old.row_id, old.request, old.run)


def test_uncommitted_bad_identity_and_bad_result_bytes_rejected(tmp_path: Path) -> None:
    project, paths = configured(tmp_path)
    project, results = complete(project, paths)
    plan = project.analyses[0]
    assert plan.run is not None and plan.run.result is not None
    data = TypeAdapter(AnalysisResult).dump_json(results[0].result)
    for bad in (data[:-1], data.replace(b'"dark"', b'"light"'), b"{}"):
        with pytest.raises(ValueError, match="摘要"):
            read_project_result(plan, bad)
    duplicate = data.replace(b'"bit_depth":16', b'"bit_depth":16,"bit_depth":16')
    altered = plan.model_copy(
        update={"run": plan.run.model_copy(update={"result": asset(duplicate, "duplicate")})}
    )
    with pytest.raises(ValueError, match="重复"):
        read_project_result(altered, duplicate)
    wrong = TypeAdapter(AnalysisResult).dump_json(results[1].result)
    altered = plan.model_copy(
        update={"run": plan.run.model_copy(update={"result": asset(wrong, "wrong")})}
    )
    with pytest.raises(ValueError, match="不对应"):
        read_project_result(altered, wrong)
    running = plan.run.model_copy(update={"state": "running", "result": None})
    with pytest.raises(ValueError, match="终态"):
        ProjectRowAnalysis(
            row_id=plan.row_id,
            crop=plan.crop,
            empty_lanes=plan.empty_lanes,
            request=plan.request,
            run=running,
        )
    with pytest.raises(ValueError, match="项目"):
        record_project_run(
            project,
            plan.row_id,
            plan.request,
            plan.run.model_copy(update={"document_id": "foreign"}),
        )


@pytest.mark.parametrize("state", ["failed", "interrupted", "cancelled"])
def test_terminal_failure_is_never_zero(tmp_path: Path, state: str) -> None:
    project, _ = configured(tmp_path)
    plan = project.analyses[0]
    run = RunRecord.model_validate(
        dict(
            document_id=project.project_id,
            tool_id="wb-figure",
            revision=plan.request.revision,
            run_id="failed",
            state=state,
            request=asset(b"{}", "frozen"),
            pid=123,
            reason="test failure",
        )
    )
    project = record_project_run(project, plan.row_id, plan.request, run)
    cells = [c for c in fill_project_table(project, ()) if c.row_id == plan.row_id]
    assert all(c.status == state and c.value is None for c in cells)


def test_plan_keeps_geometry_and_manual_baseline_edits_need_new_run(tmp_path: Path) -> None:
    project, paths = configured(tmp_path)
    project, results = complete(project, paths)
    plan = project.analyses[0]
    edited_lanes = tuple(
        replace(lane, bands=(replace(lane.bands[0], baseline=Baseline(5535, 5535)),))
        for lane in plan.request.lanes
    )
    edited = update_row_analysis_request(
        project, plan.row_id, replace(plan.request, lanes=edited_lanes)
    )
    assert next(p for p in edited.analyses if p.row_id == plan.row_id).run is None
    assert all(
        c.value is None for c in fill_project_table(edited, results) if c.row_id == plan.row_id
    )
    assert [c.value for c in fill_project_table(edited, results) if c.row_id == "row1"] == [
        8000,
        16000,
        0,
    ]
    assert update_row_analysis_request(project, plan.row_id, plan.request) == project
    with pytest.raises(ValueError, match="固定N"):
        ProjectRowAnalysis(
            row_id=plan.row_id,
            crop=plan.crop,
            request=replace(plan.request, lanes=tuple(reversed(plan.request.lanes))),
        )
    lanes = list(plan.request.lanes)
    lanes[1] = replace(lanes[1], bands=(replace(lanes[1].bands[0], included=True),))
    with pytest.raises(ValueError, match="空泳道"):
        ProjectRowAnalysis(
            row_id=plan.row_id,
            crop=plan.crop,
            empty_lanes=plan.empty_lanes,
            request=replace(plan.request, lanes=tuple(lanes)),
        )
    unreviewed = project.model_copy(
        update={"rows": (project.rows[0].model_copy(update={"reviewed": False}), *project.rows[1:])}
    )
    with pytest.raises(ValueError, match="确认"):
        make_row_analysis(unreviewed, "row0", "dark")
