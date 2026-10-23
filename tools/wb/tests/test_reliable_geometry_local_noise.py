"""Independent synthetic regressions for reliable geometry: local noise."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from numpy.typing import NDArray
from wb_tool.api import (
    WBIntakeCropProject,
    accept_automatic_intake_crop,
    automatic_intake_crop_allowed,
    claim_intake_workflow_step,
    propose_intake_crop,
)

from tools.wb.tests.common_policy_assertions import assert_prominent_row
from tools.wb.tests.test_intake_automatic_crop import prepared
from tools.wb.tests.test_reliable_geometry_registration import grouped_arrays


def _source_proposal(
    tmp_path: Path, pixels: NDArray[np.uint16], count: int, name: str, *, prominent: bool = False
) -> bool:
    path = tmp_path / f"{name}.tiff"
    tifffile.imwrite(path, pixels)
    active, ticket = claim_intake_workflow_step(prepared(path, count=count), session_key=name)
    assert isinstance(active, WBIntakeCropProject)
    assert ticket
    evidence = propose_intake_crop(str(path), active, "r")
    allowed = automatic_intake_crop_allowed(evidence)
    if prominent:
        assert_prominent_row(evidence, path, pixels, [(235, 116, 266, 125), (285, 116, 316, 125)])
    return allowed


@pytest.mark.parametrize("amplitude", [0, 200, 500, 1000])
def test_distant_correlated_texture_cannot_erase_locally_clean_terminal_band(
    tmp_path: Path, amplitude: int
) -> None:
    yy, xx = np.mgrid[:240, :600]
    membrane = (abs(xx - 300) < 230) & (abs(yy - 120) < 65)
    pixels = np.full(xx.shape, 100, dtype=np.uint16)
    pixels[membrane] = 50000
    # The third lane and its full vertical background strip stay noiseless.
    # Only distant columns contain a deterministic correlated texture.
    textured = membrane & ~((xx >= 330) & (xx <= 375))
    texture = np.rint(amplitude * np.sin(2 * np.pi * yy / 40)).astype(np.int32)
    pixels[textured] = (50000 + texture[textured]).astype(np.uint16)
    for x, value in [(250, 8000), (300, 8000), (350, 49000)]:
        pixels[(abs(xx - x) < 16) & (abs(yy - 120) < 5)] = value
    assert np.all(pixels[90:110, 335:366] == 50000)
    assert np.all(pixels[116:125, 335:366] == 49000)
    assert _source_proposal(tmp_path, pixels, 2, f"correlated_{amplitude}", prominent=True)


@pytest.mark.parametrize("count", [2, 3])
def test_left_sample_doublet_is_not_proven_to_be_a_marker(tmp_path: Path, count: int) -> None:
    yy, xx = np.mgrid[:240, :600]
    pixels = np.full(xx.shape, 100, dtype=np.uint16)
    pixels[(abs(xx - 300) < 230) & (abs(yy - 120) < 65)] = 50000
    for x in [300 + 50 * i for i in range(count)]:
        pixels[(abs(xx - x) < 16) & (abs(yy - 120) < 5)] = 8000
    # First sample at the preceding equal-pitch position has a split doublet.
    # No white-light corroboration or explicit marker selection is available.
    for y in (110, 130):
        pixels[(abs(xx - 250) < 16) & (abs(yy - y) < 5)] = 8000
    assert not _source_proposal(tmp_path, pixels, count, f"left_doublet_{count}")


@pytest.mark.parametrize("shape", ["uniform", "strong-core", "one-by-six", "two-by-three"])
def test_unfit_direction_retains_observed_third_component(tmp_path: Path, shape: str) -> None:
    yy, xx = np.mgrid[:240, :600]
    pixels = np.full(xx.shape, 100, dtype=np.uint16)
    pixels[(abs(xx - 300) < 230) & (abs(yy - 120) < 65)] = 50000
    for x in (250, 300):
        pixels[(abs(xx - x) < 16) & (abs(yy - 120) < 5)] = 8000
    if shape in {"uniform", "strong-core"}:
        pixels[(abs(xx - 350) < 16) & (abs(yy - 120) < 5)] = 49000
        if shape == "strong-core":
            pixels[116:125, 350] = 8000
    elif shape == "one-by-six":
        pixels[117:123, 350] = 8000
    else:
        pixels[119:122, 350:352] = 8000
    assert _source_proposal(tmp_path, pixels, 2, shape, prominent=True)


@pytest.mark.parametrize("extra_peer_row", [False, True])
def test_peer_target_must_not_turn_repeated_rows_into_registration_proof(
    tmp_path: Path, extra_peer_row: bool
) -> None:
    yy, xx = np.mgrid[:300, :600]
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[(abs(xx - 300) < 150) & (abs(yy - 150) < 90)] = 50000
    signal = np.full(xx.shape, 50000, dtype=np.uint16)
    merge = guide.copy()
    for x in (275, 325):
        signal[(abs(xx - x) < 16) & (abs(yy - 120) < 10)] = 8000
        for y in (120, 180) if extra_peer_row else (120,):
            merge[(abs(xx - x) < 16) & (abs(yy - y) < 10)] = 8000
    p, sources, row_id = grouped_arrays(tmp_path, (signal, guide, merge))
    active, ticket = claim_intake_workflow_step(p, session_key="peer-target")
    assert isinstance(active, WBIntakeCropProject)
    assert ticket
    evidence = propose_intake_crop(sources[0].path, active, row_id, sources=sources[1:])
    allowed = automatic_intake_crop_allowed(evidence)
    if allowed:
        accepted = accept_automatic_intake_crop(active, ticket, evidence)
        assert accepted.intake_crops[0].policy == (
            "intake_crop@4" if extra_peer_row else "intake_crop@3"
        )
        assert evidence.detection is not None
        flags = evidence.detection.flags
        assert ("registered_signal_pair@1" in flags) == (not extra_peer_row)
        assert ("companion_coordinates_unconfirmed" in flags) == extra_peer_row
        for slot, x in zip(evidence.slots, (275, 325), strict=True):
            assert slot.roi and slot.roi.x0 <= x - 15 and slot.roi.x1 >= x + 16
            assert slot.roi.y0 <= 111 and slot.roi.y1 >= 130
        assert accepted.intake_crops[0].geometry_ready and not accepted.intake_crops[0].reviewed
    assert allowed
