"""Immutable tool-owned messages shared by the optional view and desktop assembly."""

from dataclasses import dataclass
from threading import Event
from typing import Literal

from tool_contracts.api import RunRecord

from wb_tool.application.analysis import AnalysisResult
from wb_tool.application.crop import CropRequest
from wb_tool.application.crop_suggestions import CropSuggestion
from wb_tool.application.document import WBDocument, WBWorksheetDocument
from wb_tool.application.figure_project import (
    FigurePNG,
    FigureRender,
    FigureSourcePath,
    WBFigureProject,
)
from wb_tool.application.figure_template import LoadedFigureTemplate
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    ProjectRowAnalysis,
    ProjectTableCell,
    ProjectTableSnapshot,
)
from wb_tool.application.project_archive import ArchiveRunEvidence
from wb_tool.application.project_metadata import MetadataBook
from wb_tool.application.project_normalization import NormalizationSnapshot
from wb_tool.application.project_ocr import LoadedProjectOCR
from wb_tool.application.project_restore import RestoredProjectResults
from wb_tool.domain.automatic import CropPolicy, QuantPolicy
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
        "discover_tiffs",
        "automatic_row",
        "automatic_export",
        "metadata_read",
        "ocr_preview",
        "document",
        "encode",
        "result",
        "ocr_result",
        "stored_result",
        "export",
        "crop",
        "figure_document",
        "figure_preview",
        "figure_ocr",
        "figure_export",
        "figure_image_export",
        "font_digest",
        "template_read",
        "template_export",
        "crop_suggest",
        "project_result",
        "project_table",
        "project_export",
        "quant_export",
        "quant_replan",
        "project_ocr_result",
        "project_ocr_install",
        "project_ocr_table",
        "project_ocr_export",
        "project_derived_tables",
        "project_normalization_export",
        "project_evidence",
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
    crop_policy: CropPolicy = "legacy_fixed_height@1"
    quant_policy: QuantPolicy = "legacy_bounds@1"
    source_sha256: str = ""
    revision: int = 0
    analysis_plan: ProjectRowAnalysis | None = None
    project_results: tuple[LoadedProjectResult, ...] = ()
    ocr_run: RunRecord | None = None
    project_ocr_result: LoadedProjectOCR | None = None
    ocr_labels: bool = False
    preview_edge: int = 2048
    archive_runs: tuple[ArchiveRunEvidence, ...] | None = None
    processing_errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectDerivedTables:
    ocr_cells: tuple[ProjectTableCell, ...] = ()
    normalization: NormalizationSnapshot = NormalizationSnapshot()


@dataclass(frozen=True)
class WBReply:
    request_id: str
    value: (
        PreviewRaster
        | WBDocument
        | WBWorksheetDocument
        | WBFigureProject
        | FigureRender
        | FigurePNG
        | LoadedFigureTemplate
        | MetadataBook
        | CropSuggestion
        | LoadedProjectResult
        | ProjectTableSnapshot
        | LoadedProjectOCR
        | ProjectDerivedTables
        | RestoredProjectResults
        | AnalysisResult
        | OCRRecognition
        | bytes
        | str
        | None
    ) = None
    error: str = ""
