"""Immutable tool-owned messages shared by the optional view and desktop assembly."""

from dataclasses import dataclass
from typing import Literal

from wb_tool.application.analysis import AnalysisResult
from wb_tool.application.crop import CropRequest
from wb_tool.application.document import WBDocument, WBWorksheetDocument
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
        "preview", "document", "encode", "result", "ocr_result", "stored_result", "export", "crop"
    ]
    path: str = ""
    data: bytes = b""
    document: WBDocument | WBWorksheetDocument | None = None
    worksheet: Worksheet | None = None
    result: AnalysisResult | None = None
    crop: CropRequest | None = None
    destination: str = ""


@dataclass(frozen=True)
class WBReply:
    request_id: str
    value: (
        PreviewRaster
        | WBDocument
        | WBWorksheetDocument
        | AnalysisResult
        | OCRRecognition
        | bytes
        | str
        | None
    ) = None
    error: str = ""
