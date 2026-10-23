"""Independent synthetic regressions for reliable geometry: registration."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from numpy.typing import NDArray
from tool_contracts.api import AssetRef
from wb_tool.api import (
    AutoWBSettings,
    FigureSourcePath,
    IntakeDraftFigure,
    IntakeGrouping,
    IntakeSource,
    LaneROI,
    WBFigureProject,
    WBIntakeCropProject,
    accept_automatic_intake_crop,
    approve_intake_workflow,
    automatic_intake_crop_allowed,
    claim_intake_workflow_step,
    confirm_intake,
    create_intake,
    intake_digest,
    intake_grouping,
    intake_workflow_digest,
    load_tiff,
    prepare_intake_crops,
    prepare_intake_figures,
    prepare_intake_workflow,
    propose_intake_crop,
    read_figure_project,
    register_intake_source,
    save_intake_grouping,
)
from wb_tool.domain.reliable_geometry import detect_reliable_geometry


def test_implicit_registration_target_cannot_hide_a_narrower_second_row() -> None:
    guide = np.full((300, 500), 100, dtype=np.uint16)
    guide[50:250, 50:450] = 50000
    signal = guide.copy()
    signal[116:125, 210:290] = 8000
    signal[180:189, 240:271] = 8000
    result = detect_reliable_geometry(
        signal,
        guide,
        AutoWBSettings(lane_count=1),
        target=LaneROI("implicit", 200, 100, 300, 140),
        lane_width=100,
        width_is_estimate=True,
        registration_target=True,
    )
    assert not result.candidates
    assert "guided_target_ambiguous" in result.flags


def grouped_offset(
    tmp_path: Path, *, merge_offset: int
) -> tuple[WBIntakeCropProject, tuple[FigureSourcePath, ...], str]:
    yy, xx = np.mgrid[:240, :600]
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[(abs(xx - 300) < 150) & (abs(yy - 120) < 50)] = 50000
    signal = np.full(xx.shape, 50000, dtype=np.uint16)
    merge = guide.copy()
    for x in (275, 325):
        signal[(abs(xx - x) < 16) & (abs(yy - 120) < 8)] = 8000
        merge[(abs(xx - x - merge_offset) < 16) & (abs(yy - 120) < 8)] = 8000
    return grouped_arrays(tmp_path, (signal, guide, merge))


def grouped_arrays(
    tmp_path: Path, arrays: tuple[NDArray[np.uint16], ...], *, count: int = 2
) -> tuple[WBIntakeCropProject, tuple[FigureSourcePath, ...], str]:
    p = create_intake(WBFigureProject(project_id="review-peer-target"))
    sources: list[FigureSourcePath] = []
    for index, pixels in enumerate(arrays, 1):
        path = tmp_path / f"AKT_123456 ({index}).tiff"
        tifffile.imwrite(path, pixels)
        image = load_tiff(path)
        sources.append(FigureSourcePath(image.sha256, str(path)))
        p = register_intake_source(
            p,
            IntakeSource(
                source_id=f"s{index}",
                asset=AssetRef(
                    asset_id=f"a{index}",
                    relative_path=f"assets/{index}.tiff",
                    sha256=image.sha256,
                    size_bytes=path.stat().st_size,
                ),
                original_name=path.name,
                relative_path=path.name,
                width=pixels.shape[1],
                height=pixels.shape[0],
                bit_depth=16,
            ),
            expected_digest=intake_digest(p),
        )
    grouping = intake_grouping(p)
    p = save_intake_grouping(
        p,
        IntakeGrouping(
            figures=(IntakeDraftFigure(figure_id="f", label="Fig", lane_count=count),),
            groups=tuple(
                g.model_copy(
                    update={"figure_id": "f", "protein_label": "AKT", "selected_source_id": "s1"}
                )
                for g in grouping.groups
            ),
        ),
        expected_digest=intake_digest(p),
    )
    p = confirm_intake(p, expected_digest=intake_digest(p))
    p = prepare_intake_figures(
        prepare_intake_crops(
            prepare_intake_workflow(p, expected_digest=intake_digest(p), batch_stages=True)
        )
    )
    p = approve_intake_workflow(p, expected_digest=intake_workflow_digest(p))
    assert isinstance(p, WBIntakeCropProject)
    return p, tuple(sources), p.rows[0].row_id


@pytest.mark.parametrize("merge_offset", [0, 80])
def test_group_must_validate_registration_before_automatic_acceptance(
    tmp_path: Path, merge_offset: int
) -> None:
    p, sources, row_id = grouped_offset(tmp_path, merge_offset=merge_offset)
    active, ticket = claim_intake_workflow_step(p, session_key="review-group")
    assert isinstance(active, WBIntakeCropProject)
    assert ticket
    evidence = propose_intake_crop(sources[0].path, active, row_id, sources=sources[1:])
    allowed = automatic_intake_crop_allowed(evidence)
    if allowed:
        accepted = accept_automatic_intake_crop(active, ticket, evidence)
        assert accepted.intake_crops[0].policy == (
            "intake_crop@4" if merge_offset else "intake_crop@3"
        )
        assert evidence.detection is not None
        flags = evidence.detection.flags
        assert ("registered_signal_pair@1" in flags) == (merge_offset == 0)
        assert ("companion_coordinates_unconfirmed" in flags) == (merge_offset != 0)
        for slot, x in zip(evidence.slots, (275, 325), strict=True):
            assert slot.roi and slot.roi.x0 <= x - 15 and slot.roi.x1 >= x + 16
            assert slot.roi.y0 <= 113 and slot.roi.y1 >= 128
        assert accepted.intake_crops[0].geometry_ready and not accepted.intake_crops[0].reviewed
        assert read_figure_project(accepted.model_dump_json().encode()) == accepted
        data = accepted.model_dump(mode="json")
        data["intake_crops"][0]["detection"]["flags"] = [
            f
            for f in data["intake_crops"][0]["detection"]["flags"]
            if f != "verified_group_sha256:" + sources[1].sha256
        ]
        import json

        with pytest.raises(ValueError):
            read_figure_project(json.dumps(data).encode())
    assert allowed
