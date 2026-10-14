"""Immutable tool-owned messages shared by the optional view and desktop assembly."""

from dataclasses import dataclass
from threading import Event
from typing import Literal

from wb_tool.application.analysis import AnalysisResult
from wb_tool.application.crop import CropRequest
from wb_tool.application.crop_suggestions import CropSuggestion
from wb_tool.application.document import WBDocument, WBWorksheetDocument
from wb_tool.application.figure_project import FigureRender, FigureSourcePath, WBFigureProject
from wb_tool.domain.crop_detection import CropDetectionSettings
from wb_tool.domain.worksheet import OCRRecognition, Worksheet


@dataclass(frozen=True)
class PreviewRaster:
    sha256: str
    width: int
    height: int
    preview_width: int
    preview_height: int
    pixels: bytes
    bit_depth: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class WBJob:
    operation: Literal[
        "preview",
        "document",
        "encode",
        "result",
        "ocr_result",
        "stored_result",
        "export",
        "crop",
        "figure_document",
        "figure_preview",
        "figure_export",
        "font_digest",
        "crop_suggest",
    ]
    path: str = ""
    data: bytes = b""
    document: WBDocument | WBWorksheetDocument | WBFigureProject | None = None
    worksheet: Worksheet | None = None
    result: AnalysisResult | None = None
    crop: CropRequest | None = None
    destination: str = ""
    sources: tuple[FigureSourcePath, ...] = ()
    cancellation: Event | None = None
    detection_settings: CropDetectionSettings | None = None
    row_id: str = ""
    source_sha256: str = ""
    revision: int = 0


@dataclass(frozen=True)
class WBReply:
    request_id: str
    value: (
        PreviewRaster
        | WBDocument
        | WBWorksheetDocument
        | WBFigureProject
        | FigureRender
        | CropSuggestion
        | AnalysisResult
        | OCRRecognition
        | bytes
        | str
        | None
    ) = None
    error: str = ""
