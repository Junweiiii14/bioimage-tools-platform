"""Complete Fig prerequisites and analytic original-pixel oracles, independent of display."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest
import tifffile
from PIL import Image
from pydantic import TypeAdapter
from tool_contracts.api import AssetRef, RunRecord
from wb_tool.api import (
    AnalysisResult,
    FigureSourcePath,
    IntakeAssignment,
    IntakeFigure,
    IntakeProtein,
    IntakeSource,
    LaneROI,
    LoadedProjectResult,
    ProjectRowAnalysis,
    StagedProjectArchive,
    WBFigureProject,
    WBIntakeCropProject,
    WBIntakeFigureProject,
    analyze_annotations,
    approve_intake_workflow,
    assign_intake_sources,
    claim_intake_workflow_step,
    complete_intake_crop,
    complete_intake_figure,
    complete_intake_measurement,
    confirm_intake,
    create_intake,
    export_intake_crop,
    intake_digest,
    intake_figure_projection,
    intake_workflow_digest,
    load_tiff,
    prepare_intake_crops,
    prepare_intake_figure,
    prepare_intake_figures,
    prepare_intake_measurement_revision,
    prepare_intake_workflow,
    project_assets,
    propose_intake_crop,
    read_figure_project,
    read_project_result,
    record_intake_crop_proposal,
    register_intake_source,
    replace_intake_plan,
    request_intake_workflow_cancel,
    restore_staged_project,
    review_intake_crop,
)


def asset(path: Path) -> AssetRef:
    data = path.read_bytes()
    return AssetRef(
        asset_id=path.stem,
        relative_path="assets/" + path.name,
        sha256=sha256(data).hexdigest(),
        size_bytes=len(data),
    )


def ready_fig(tmp_path: Path) -> tuple[WBIntakeFigureProject, tuple[FigureSourcePath, ...]]:
    p = create_intake(WBFigureProject(project_id="intake-fig"))
    figures = (
        IntakeFigure(figure_id="a", label="Fig A", lane_count=3),
        IntakeFigure(figure_id="b", label="Fig B", lane_count=3),
    )
    proteins = tuple(
        IntakeProtein(protein_id=key, figure_id=fig, label="AKT")
        for key, fig in (("a1", "a"), ("a2", "a"), ("b1", "b"))
    )
    p = replace_intake_plan(p, figures, proteins, expected_digest=intake_digest(p))
    sources: list[FigureSourcePath] = []
    for index, key in enumerate(("a1", "a2", "b1"), 1):
        pixels = np.full((80, 120), 50000, dtype=np.uint16)
        for lane, scale in enumerate((1, 2, 0)):
            pixels[30:40, lane * 40 : (lane + 1) * 40] -= (
                np.array([0, 0, 0, 100, 200, 100, 0, 0, 0, 0], dtype=np.uint16) * index * scale
            )[:, None]
        path = tmp_path / (key + ".tiff")
        tifffile.imwrite(path, pixels)
        ref = asset(path)
        sources.append(FigureSourcePath(ref.sha256, str(path)))
        p = register_intake_source(
            p,
            IntakeSource(
                source_id=key,
                asset=ref,
                original_name=path.name,
                relative_path=path.name,
                width=120,
                height=80,
                bit_depth=16,
            ),
            expected_digest=intake_digest(p),
        )
    p = assign_intake_sources(
        p,
        tuple(IntakeAssignment(protein_id=r.protein_id, source_id=r.protein_id) for r in proteins),
        expected_digest=intake_digest(p),
    )
    p = confirm_intake(p, expected_digest=intake_digest(p))
    cropped = prepare_intake_crops(prepare_intake_workflow(p, expected_digest=intake_digest(p)))
    for key, source in zip(("a1", "a2"), sources[:2], strict=True):
        active, ticket = claim_intake_workflow_step(
            approve_intake_workflow(cropped, expected_digest=intake_workflow_digest(cropped)),
            session_key="crop",
            stage_filter="crop",
        )
        assert isinstance(active, WBIntakeCropProject) and ticket is not None
        cropped = record_intake_crop_proposal(
            active, ticket, propose_intake_crop(source.path, active, key)
        )
        cropped = review_intake_crop(
            cropped,
            key,
            LaneROI(key, 0, 10, 120, 60),
            expected_digest=intake_workflow_digest(cropped),
        )
        active, ticket = claim_intake_workflow_step(
            approve_intake_workflow(cropped, expected_digest=intake_workflow_digest(cropped)),
            session_key="crop",
            stage_filter="crop",
        )
        assert isinstance(active, WBIntakeCropProject) and ticket is not None
        path = tmp_path / (key + "-crop.tiff")
        export_intake_crop(source.path, active, key, str(path), ticket=ticket)
        cropped = complete_intake_crop(active, ticket, asset(path))
    return prepare_intake_figures(cropped), tuple(sources)


def compose(
    p: WBIntakeFigureProject, sources: tuple[FigureSourcePath, ...], path: Path
) -> WBIntakeFigureProject:
    active, ticket = claim_intake_workflow_step(
        approve_intake_workflow(p, expected_digest=intake_workflow_digest(p)),
        session_key="compose",
        stage_filter="compose",
    )
    assert (
        isinstance(active, WBIntakeFigureProject) and ticket is not None and ticket.target_id == "a"
    )
    result = prepare_intake_figure(active, ticket, sources, str(path))
    with Image.open(path) as display:
        assert display.mode == "RGB" and "wb_provenance" in display.info
    return complete_intake_figure(active, ticket, result, asset(path))


def test_complete_fig_retains_duplicate_protein_rows_and_other_fig_stays_pending(
    tmp_path: Path,
) -> None:
    p, sources = ready_fig(tmp_path)
    with pytest.raises(ValueError, match="完整Fig"):
        intake_figure_projection(p, "b")
    p = compose(p, sources, tmp_path / "fig.png")
    assert p.intake_figures[0].row_ids == ("a1", "a2")
    assert len({slot for row in p.intake_figures[0].slot_ids for slot in row}) == 6
    assert tuple(plan.row_id for plan in p.analyses) == ("a1", "a2")
    assert all(plan.run is None for plan in p.analyses)
    assert (
        next(s for s in p.workflow.steps if (s.stage, s.target_id) == ("crop", "b1")).status
        == "pending"
    )
    assert read_figure_project(p.model_dump_json().encode()) == p
    with pytest.raises(ValueError):
        WBIntakeCropProject.from_bytes(p.model_dump_json().encode())

    archive = AssetRef(
        asset_id="zip", relative_path="assets/a.zip", sha256="f" * 64, size_bytes=100
    )
    restored = restore_staged_project(
        StagedProjectArchive(p, "a.zip", archive.sha256, (), (), 2),
        tuple(
            a.model_copy(
                update={
                    "asset_id": "new-" + a.asset_id,
                    "relative_path": "restored/" + a.relative_path,
                }
            )
            for a in project_assets(p)
        ),
        archive,
    )
    assert isinstance(restored, WBIntakeFigureProject)
    assert restored.intake_figures[0].image.asset_id.startswith("new-")
    assert not restored.workflow.approved


def test_composition_rejects_unowned_cancelled_or_changed_sources_before_publication(
    tmp_path: Path,
) -> None:
    p, sources = ready_fig(tmp_path)
    active, ticket = claim_intake_workflow_step(
        approve_intake_workflow(p, expected_digest=intake_workflow_digest(p)),
        session_key="compose",
        stage_filter="compose",
    )
    assert isinstance(active, WBIntakeFigureProject) and ticket is not None
    path = tmp_path / "no-output.png"
    with pytest.raises(ValueError, match="过期"):
        prepare_intake_figure(p, ticket, sources, str(path))
    cancelled = request_intake_workflow_cancel(active)
    assert isinstance(cancelled, WBIntakeFigureProject)
    with pytest.raises(ValueError, match="取消"):
        prepare_intake_figure(cancelled, ticket, sources, str(path))
    wrong = tmp_path / "wrong.tiff"
    tifffile.imwrite(wrong, np.full((80, 120), 123, dtype=np.uint16))
    changed = (FigureSourcePath(sources[0].sha256, str(wrong)), *sources[1:])
    with pytest.raises(ValueError):
        prepare_intake_figure(active, ticket, changed, str(path))
    assert not path.exists()


def test_original_triangle_integrals_do_not_depend_on_display_and_finish_requires_real_runs(
    tmp_path: Path,
) -> None:
    p, sources = ready_fig(tmp_path)
    changed = type(p).model_validate(
        {**dict(p), "layout_style": p.layout_style.model_copy(update={"lane_unit": 60})}
    )
    left = compose(p, sources, tmp_path / "large.png")
    right = compose(changed, sources, tmp_path / "small.png")
    assert left.intake_figures[0].width != right.intake_figures[0].width
    assert tuple(a.request for a in left.analyses) == tuple(a.request for a in right.analyses)
    revised = prepare_intake_measurement_revision(left, "a", left.revision + 1)
    active, ticket = claim_intake_workflow_step(
        revised, session_key="measure", stage_filter="measure"
    )
    assert isinstance(active, WBIntakeFigureProject) and ticket is not None
    assert ticket.stage == "measure" and ticket.target_id == "a"
    failed = complete_intake_measurement(active, ticket, (), ())
    assert (
        next(s for s in failed.workflow.steps if s.stage == "measure" and s.target_id == "a").status
        == "failed"
    )
    committed: list[ProjectRowAnalysis] = []
    decoded: list[LoadedProjectResult] = []
    frozen_path = tmp_path / "frozen.json"
    frozen_path.write_bytes(active.model_dump_json().encode())
    for index, plan in enumerate(active.analyses, 1):
        original = load_tiff(sources[index - 1].path)
        result = analyze_annotations(original, plan.request)
        data = TypeAdapter(AnalysisResult).dump_json(result)
        result_path = tmp_path / (plan.row_id + ".json")
        result_path.write_bytes(data)
        run = RunRecord(
            document_id=p.project_id,
            tool_id="wb-figure",
            revision=plan.request.revision,
            run_id=plan.row_id,
            state="succeeded",
            pid=123,
            request=asset(frozen_path),
            result=asset(result_path),
        )
        measured = ProjectRowAnalysis.model_validate({**dict(plan), "run": run})
        committed.append(measured)
        decoded.append(read_project_result(measured, data))
        # Full triangular profile area = (100 + 200 + 100), scaled per original source/lane.
        assert result.lanes[0].bands[0].measurement is not None
        assert result.lanes[0].bands[0].measurement.signal == 400 * index
        assert result.lanes[1].bands[0].measurement is not None
        assert result.lanes[1].bands[0].measurement.signal == 800 * index
        assert result.lanes[2].bands[0].status == "not_detected"
    finished = complete_intake_measurement(active, ticket, tuple(committed), tuple(decoded))
    assert (
        next(
            s for s in finished.workflow.steps if s.stage == "measure" and s.target_id == "a"
        ).status
        == "done"
    )
    assert all(r.run for r in finished.analyses)
    cancelled = request_intake_workflow_cancel(active)
    assert isinstance(cancelled, WBIntakeFigureProject)
    assert (
        next(
            s
            for s in complete_intake_measurement(
                cancelled, ticket, tuple(committed), tuple(decoded)
            ).workflow.steps
            if s.stage == "measure" and s.target_id == "a"
        ).status
        == "cancelled"
    )
    with pytest.raises(ValueError, match="冻结"):
        complete_intake_measurement(
            active,
            ticket,
            (
                committed[0].model_copy(
                    update={"request": replace(committed[0].request, polarity="light")}
                ),
            ),
            (),
        )
