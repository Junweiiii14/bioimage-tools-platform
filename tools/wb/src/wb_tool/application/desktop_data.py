"""Immutable tool-owned messages shared by the optional view and desktop assembly."""

from dataclasses import dataclass
from typing import Literal

from wb_tool.application.analysis import AnalysisResult
from wb_tool.application.document import WBDocument


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
    operation: Literal["preview", "document", "encode", "result"]
    path: str = ""
    data: bytes = b""
    document: WBDocument | None = None


@dataclass(frozen=True)
class WBReply:
    request_id: str
    value: PreviewRaster | WBDocument | AnalysisResult | bytes | None = None
    error: str = ""
