"""Frozen baseline-generated synthetic projects retain their original evidence."""

import json
from pathlib import Path

import pytest
from wb_tool.api import WBIntakeFigureProject, read_figure_project

FIXTURES = Path(__file__).parent / "fixtures" / "intake_crop_v2"


@pytest.mark.parametrize("kind", ["source", "guided"])
def test_historical_automatic_crop_and_completed_figure_round_trip(kind: str) -> None:
    raw = (FIXTURES / f"{kind}.json").read_bytes()
    project = read_figure_project(raw)
    assert isinstance(project, WBIntakeFigureProject)
    assert project.model_dump(mode="json") == json.loads(raw)
    assert read_figure_project(project.model_dump_json().encode()) == project
    evidence = project.intake_crops[0]
    assert evidence.policy == "intake_crop@2" and not evidence.reviewed
    assert evidence.geometry_ready and evidence.raw_crop and project.intake_figures
    assert evidence.detection and evidence.geometry_policy.endswith("@1")
    assert not any(
        flag.startswith(("registered_signal_pair", "verified_group_sha256"))
        for flag in evidence.detection.flags
    )
    assert project.analyses and all(p.run is None for p in project.analyses)


@pytest.mark.parametrize("kind", ["source", "guided"])
def test_historical_crop_cannot_drop_selected_candidate(kind: str) -> None:
    project = read_figure_project((FIXTURES / f"{kind}.json").read_bytes())
    assert isinstance(project, WBIntakeFigureProject)
    evidence = project.intake_crops[0]
    with pytest.raises(ValueError):
        type(evidence).model_validate({**dict(evidence), "selected_index": None})


def test_historical_guided_crop_still_rejects_changed_companion_identity() -> None:
    data = json.loads((FIXTURES / "guided.json").read_bytes())
    flags = data["intake_crops"][0]["detection"]["flags"]
    data["intake_crops"][0]["detection"]["flags"] = [
        "guide_sha256:" + "0" * 64 if flag.startswith("guide_sha256:") else flag for flag in flags
    ]
    with pytest.raises(ValueError, match="辅助定位"):
        read_figure_project(json.dumps(data).encode())
