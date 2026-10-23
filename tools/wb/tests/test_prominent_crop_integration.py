"""New prominent fixed-N evidence reaches real original-value export."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from tool_contracts.api import AssetRef
from wb_tool.api import (
    WBIntakeCropProject,
    accept_automatic_intake_crop,
    automatic_intake_crop_allowed,
    claim_intake_workflow_step,
    complete_intake_crop,
    export_intake_crop,
    load_tiff,
    propose_intake_crop,
    read_figure_project,
)

from tools.wb.tests.test_intake_automatic_crop import prepared
from tools.wb.tests.test_source_geometry import membrane


@pytest.mark.parametrize("angle", [0, 18])
def test_prominent_policy_keeps_fixed_n_original_samples_and_roundtrip(
    tmp_path: Path, angle: int
) -> None:
    path = tmp_path / "source.tiff"
    pixels = membrane(angle=angle, marker=False)
    tifffile.imwrite(path, pixels)
    before = path.read_bytes()
    p = prepared(path)
    p = type(p).model_validate(
        {**dict(p), "workflow": {**dict(p.workflow), "policy": "intake_workflow@5"}}
    )
    p, ticket = claim_intake_workflow_step(p, session_key="prominent")
    assert isinstance(p, WBIntakeCropProject) and ticket
    evidence = propose_intake_crop(str(path), p, "r")
    assert evidence.geometry_policy == "source_prominent_band_geometry@1"
    assert automatic_intake_crop_allowed(evidence), evidence.reason
    assert len(evidence.slots) == 5
    accepted = accept_automatic_intake_crop(p, ticket, evidence)
    e = accepted.intake_crops[0]
    assert e.policy == "intake_crop@5" and not e.reviewed and e.geometry_ready
    assert read_figure_project(accepted.model_dump_json().encode()) == accepted
    active, crop_ticket = claim_intake_workflow_step(accepted, session_key="export")
    assert isinstance(active, WBIntakeCropProject) and crop_ticket
    destination = tmp_path / "crop.tiff"
    result = export_intake_crop(str(path), active, "r", str(destination), ticket=crop_ticket)
    assert e.crop is not None
    assert np.array_equal(
        load_tiff(destination).pixels, pixels[e.crop.y0 : e.crop.y1, e.crop.x0 : e.crop.x1]
    )
    done = complete_intake_crop(
        active,
        crop_ticket,
        AssetRef(
            asset_id="raw",
            relative_path="assets/crop.tiff",
            sha256=result.sha256,
            size_bytes=result.size_bytes,
        ),
    )
    assert done.intake_crops[0].raw_crop
    assert path.read_bytes() == before
    # A valid candidate is insufficient if its recorded fixed N is changed.
    with pytest.raises(ValueError):
        type(e).model_validate({**dict(e), "lane_count": 4})
