"""Analytical manual annotations exercise the public analysis use case."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from wb_tool.api import (
    AnalysisCancelled,
    AnalysisError,
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    Baseline,
    LaneAnnotation,
    LaneROI,
    LoadedTiff,
    analyze_annotations,
    load_tiff,
)


@pytest.fixture
def image(tmp_path: Path) -> LoadedTiff:
    path = tmp_path / "analytic.tif"
    tifffile.imwrite(path, np.array([[245, 245], [235, 235], [245, 245]], dtype=np.uint8))
    return load_tiff(path)


def request(image: LoadedTiff, bands: tuple[BandAnnotation, ...]) -> AnalysisRequest:
    return AnalysisRequest(
        image.sha256, 7, "dark", (LaneAnnotation(LaneROI("sample-1", 0, 0, 2, 3), bands),)
    )


def test_manual_closed_loop_preserves_provenance_and_input(image: LoadedTiff) -> None:
    planned = request(image, (BandAnnotation("protein-row-1", BandBounds(0, 2)),))
    original = image.pixels.copy()
    result = analyze_annotations(image, planned)
    assert result.request == planned
    assert result.request.revision == 7
    assert result.bit_depth == 8
    assert result.algorithm_id == "profile_integral@1"
    assert result.lanes[0].roi.lane_id == "sample-1"
    measured = result.lanes[0].bands[0]
    assert measured.annotation.band_id == "protein-row-1"
    assert measured.status == "valid" and measured.signal == 10
    assert measured.measurement is not None and measured.measurement.baseline == Baseline(10, 10)
    assert np.array_equal(original, image.pixels)


def test_missing_excluded_invalid_and_valid_are_distinct(image: LoadedTiff) -> None:
    planned = request(
        image,
        (
            BandAnnotation("missing", None),
            BandAnnotation("excluded", BandBounds(0, 2), included=False),
            BandAnnotation("outside", BandBounds(0, 3)),
            BandAnnotation("valid", BandBounds(0, 2)),
        ),
    )
    bands = analyze_annotations(image, planned).lanes[0].bands
    assert [band.status for band in bands] == ["not_detected", "excluded", "invalid", "valid"]
    assert [band.signal for band in bands] == [None, None, None, 10]


def test_zero_is_a_valid_measurement(image: LoadedTiff) -> None:
    planned = request(image, (BandAnnotation("zero", BandBounds(0, 2), Baseline(20, 20)),))
    band = analyze_annotations(image, planned).lanes[0].bands[0]
    assert band.status == "valid" and band.signal == 0


def test_empty_lane_is_retained(image: LoadedTiff) -> None:
    result = analyze_annotations(image, request(image, ()))
    assert len(result.lanes) == 1 and result.lanes[0].bands == ()
    assert result.lanes[0].profiles is not None


def test_invalid_lane_does_not_destroy_other_lane(image: LoadedTiff) -> None:
    band = BandAnnotation("B", BandBounds(0, 2))
    planned = AnalysisRequest(
        image.sha256,
        2,
        "dark",
        (
            LaneAnnotation(LaneROI("outside", 0, 0, 3, 3), (band,)),
            LaneAnnotation(LaneROI("valid", 0, 0, 1, 3), (band,)),
        ),
    )
    result = analyze_annotations(image, planned)
    assert result.lanes[0].profiles is None and result.lanes[0].reason
    assert result.lanes[0].bands[0].signal is None
    assert result.lanes[1].bands[0].signal == 10


def test_limits_are_review_prompt_not_valid_signal(tmp_path: Path) -> None:
    path = tmp_path / "limits.tif"
    tifffile.imwrite(path, np.array([[255], [0], [255]], dtype=np.uint8))
    image = load_tiff(path)
    planned = AnalysisRequest(
        image.sha256,
        0,
        "dark",
        (LaneAnnotation(LaneROI("L", 0, 0, 1, 3), (BandAnnotation("B", BandBounds(0, 2)),)),),
    )
    band = analyze_annotations(image, planned).lanes[0].bands[0]
    assert band.status == "quality_review" and band.signal is None
    assert band.measurement is not None and band.measurement.signal == 255
    assert band.quality_flags == ("dtype_min_present", "dtype_max_present")


def test_baseline_must_be_in_image_range(image: LoadedTiff) -> None:
    planned = request(image, (BandAnnotation("B", BandBounds(0, 2), Baseline(256, 0)),))
    band = analyze_annotations(image, planned).lanes[0].bands[0]
    assert band.status == "invalid" and band.signal is None


def test_wrong_source_rejected(image: LoadedTiff) -> None:
    planned = AnalysisRequest("0" * 64, 0, "dark", (LaneAnnotation(LaneROI("L", 0, 0, 1, 3), ()),))
    with pytest.raises(AnalysisError, match="摘要"):
        analyze_annotations(image, planned)


@pytest.mark.parametrize("late", [False, True])
def test_cancellation_does_not_return_result(image: LoadedTiff, late: bool) -> None:
    calls = 0

    def cancelled() -> bool:
        nonlocal calls
        calls += 1
        return calls >= 3 if late else True

    with pytest.raises(AnalysisCancelled):
        analyze_annotations(
            image, request(image, (BandAnnotation("B", BandBounds(0, 2)),)), cancelled=cancelled
        )


def test_duplicate_stable_ids_rejected(image: LoadedTiff) -> None:
    band = BandAnnotation("B", BandBounds(0, 2))
    with pytest.raises(AnalysisError, match="条带身份"):
        request(image, (band, band))
    lane = LaneAnnotation(LaneROI("L", 0, 0, 1, 3), ())
    with pytest.raises(AnalysisError, match="泳道身份"):
        AnalysisRequest(image.sha256, 0, "dark", (lane, lane))


def test_invalid_request_revision_and_hash() -> None:
    lane = LaneAnnotation(LaneROI("L", 0, 0, 1, 3), ())
    with pytest.raises(AnalysisError):
        AnalysisRequest("x" * 64, 0, "dark", (lane,))
    with pytest.raises(AnalysisError):
        AnalysisRequest("0" * 64, True, "dark", (lane,))
