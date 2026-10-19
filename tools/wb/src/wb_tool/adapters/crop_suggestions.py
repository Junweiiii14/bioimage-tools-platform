"""Read and verify an original image for review-only crop suggestions."""

from collections.abc import Callable

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.crop_suggestions import CropSuggestion
from wb_tool.domain.crop_detection import CropDetectionSettings, detect_crop_candidates


def suggest_crops(
    source: str,
    source_sha256: str,
    row_id: str,
    revision: int,
    settings: CropDetectionSettings,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> CropSuggestion:
    if cancelled():
        raise ValueError("候选检测已取消")
    image = load_tiff(source)
    if image.sha256 != source_sha256:
        raise ValueError("候选检测的原图摘要不一致")
    result = detect_crop_candidates(image.pixels, settings, cancelled=cancelled)
    return CropSuggestion(
        row_id=row_id,
        source_sha256=source_sha256,
        source_revision=revision,
        settings=settings,
        result=result,
        source_warnings=image.warnings,
    )
