"""Independent analytic profile oracles for supported whole-peak boundaries."""

from dataclasses import dataclass

import numpy as np
import pytest
from wb_tool.api import AutoWBSettings, LaneROI, analyze_annotations, suggest_analysis_for_crop


@dataclass
class Image:
    pixels: np.ndarray
    sha256: str = "a" * 64
    conversion: str | None = None


def request(profile: np.ndarray):
    image = Image(np.repeat((60000 - profile).astype(np.uint16)[:, None], 12, axis=1))
    plan = suggest_analysis_for_crop(
        image,
        crop=LaneROI("r", 0, 0, 12, len(profile)),
        lane_count=1,
        revision=0,
        quant_policy="background_support@1",
    )
    return plan, analyze_annotations(image, plan)


def test_peak_internal_notch_does_not_cut_peak() -> None:
    profile = np.full(100, 3000.0)
    profile[25:75] += 12000
    profile[45:48] -= 3000
    plan, result = request(profile)
    band = plan.lanes[0].bands[0]
    assert band.bounds and band.bounds.left < 25 and band.bounds.right >= 75
    measurement = result.lanes[0].bands[0]
    assert measurement.status == "valid"
    assert measurement.signal == pytest.approx(50 * 12000 - 3 * 3000)


def test_sloping_background_integrates_original_profile() -> None:
    profile = 3000 + np.arange(100) * 15.0
    profile[30:70] += 10000
    _, result = request(profile)
    assert result.lanes[0].bands[0].signal == pytest.approx(400000)


def test_adjacent_peak_is_review_not_silent_combination() -> None:
    profile = np.full(100, 3000.0)
    profile[20:40] += 12000
    profile[65:80] += 6000
    _, result = request(profile)
    band = result.lanes[0].bands[0]
    assert band.status == "quality_review" and band.signal is None
    assert "boundary_review:multiple_signal_regions" in band.quality_flags


def test_flat_profile_has_no_valid_zero() -> None:
    _, result = request(np.full(100, 3000.0))
    assert result.lanes[0].bands[0].status == "not_detected"
    assert result.lanes[0].bands[0].signal is None
    AutoWBSettings(quant_policy="background_support@1")


def test_truncated_broad_peak_requires_background_review() -> None:
    profile = 3000 + 12000 * np.exp(-(((np.arange(60) - 30) / 30) ** 2))
    _, result = request(profile)
    band = result.lanes[0].bands[0]
    assert band.status == "quality_review" and band.signal is None
    assert "boundary_review:insufficient_background_support" in band.quality_flags


@pytest.mark.parametrize("gap", [5, 8, 12])
def test_nearby_peaks_with_deep_valley_are_reviewed(gap: int) -> None:
    profile = np.full(100, 3000.0)
    profile[20:40] += 12000
    profile[40 + gap : 60 + gap] += 6000
    _, result = request(profile)
    assert result.lanes[0].bands[0].status == "quality_review"


def test_background_quality_survives_worker_wire_roundtrip() -> None:
    from wb_tool.api import ResultFrame, encode_worker_frame, parse_worker_frame

    profile = 3000 + 12000 * np.exp(-(((np.arange(60) - 30) / 30) ** 2))
    _, result = request(profile)
    frame = ResultFrame(
        protocol_version=1,
        kind="result",
        sequence=2,
        run_id="run",
        attempt_id="attempt",
        request_id="request",
        result=result,
    )
    assert parse_worker_frame(encode_worker_frame(frame)) == frame
