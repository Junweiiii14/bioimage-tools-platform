"""Versioned public WB API; importing this module has no runtime side effects."""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from wb_tool.ui.background import WBBackground
    from wb_tool.ui.view import WBView

from wb_tool.adapters.tiff_input import ImageInputError, LoadedTiff, load_tiff
from wb_tool.application.analysis import (
    AnalysisCancelled,
    AnalysisError,
    AnalysisRequest,
    AnalysisResult,
    BandAnalysis,
    BandAnnotation,
    LaneAnalysis,
    LaneAnnotation,
    analyze_annotations,
)
from wb_tool.application.desktop_data import PreviewRaster, WBJob, WBReply
from wb_tool.application.document import WBDocument, WBWorksheetDocument, read_wb_document
from wb_tool.application.ocr_protocol import (
    OCRConversation,
    OCRRequest,
    OCRResultFrame,
    OCRStartFrame,
    encode_ocr_frame,
    ocr_protocol_schema,
    parse_ocr_frame,
)
from wb_tool.application.worker_protocol import (
    AcceptedFrame,
    CancelFrame,
    CancelledFrame,
    FailureFrame,
    HelloFrame,
    ProtocolErrorFrame,
    ResultFrame,
    StartFrame,
    WorkerConversation,
    encode_worker_frame,
    parse_worker_frame,
    worker_protocol_schema,
)
from wb_tool.application.worksheet import WorksheetCell, fill_worksheet, propose_worksheet
from wb_tool.domain.lanes import LaneProfiles, LaneROI, Polarity, compute_lane_profiles
from wb_tool.domain.quantify import (
    BandBounds,
    Baseline,
    ProfileMeasurement,
    QuantificationError,
    integrate_profile,
)
from wb_tool.domain.worksheet import (
    FigureSuggestion,
    MeasurementBinding,
    OCRRecognition,
    TextBounds,
    TextToken,
    Worksheet,
    WorksheetColumn,
    WorksheetRow,
    suggest_figures,
)

__all__ = [
    "WBWorksheetDocument",
    "read_wb_document",
    "OCRRequest",
    "OCRStartFrame",
    "OCRResultFrame",
    "OCRConversation",
    "encode_ocr_frame",
    "parse_ocr_frame",
    "ocr_protocol_schema",
    "run_ocr_worker",
    "FigureSuggestion",
    "MeasurementBinding",
    "OCRRecognition",
    "TextBounds",
    "TextToken",
    "Worksheet",
    "WorksheetColumn",
    "WorksheetRow",
    "WorksheetCell",
    "fill_worksheet",
    "suggest_figures",
    "recognize_figure",
    "propose_worksheet",
    "export_worksheet",
    "WBDocument",
    "PreviewRaster",
    "WBJob",
    "WBReply",
    "create_wb_view",
    "create_wb_background",
    "run_wb_worker",
    "AcceptedFrame",
    "CancelFrame",
    "CancelledFrame",
    "FailureFrame",
    "HelloFrame",
    "ProtocolErrorFrame",
    "ResultFrame",
    "StartFrame",
    "WorkerConversation",
    "encode_worker_frame",
    "parse_worker_frame",
    "worker_protocol_schema",
    "AnalysisCancelled",
    "AnalysisError",
    "AnalysisRequest",
    "AnalysisResult",
    "BandAnalysis",
    "BandAnnotation",
    "LaneAnalysis",
    "LaneAnnotation",
    "analyze_annotations",
    "BandBounds",
    "LaneROI",
    "LaneProfiles",
    "Polarity",
    "compute_lane_profiles",
    "ImageInputError",
    "LoadedTiff",
    "load_tiff",
    "Baseline",
    "ProfileMeasurement",
    "QuantificationError",
    "integrate_profile",
]


def create_wb_view(parent: "QWidget | None" = None) -> "WBView":
    from wb_tool.ui.view import WBView

    return WBView(parent)


def create_wb_background() -> "WBBackground":
    from wb_tool.ui.background import WBBackground

    return WBBackground()


def run_wb_worker() -> int:
    from wb_tool.worker import main

    return main()


def run_ocr_worker() -> int:
    from wb_tool.adapters.ocr_worker import main

    return main()


def recognize_figure(
    source: str,
    expected_sha256: str,
    *,
    cancelled: Callable[[], bool] | None = None,
) -> OCRRecognition:
    from wb_tool.adapters.ocr import recognize_figure as recognize

    return recognize(source, expected_sha256, cancelled=cancelled)


def export_worksheet(worksheet: Worksheet, result: AnalysisResult, destination: str) -> str:
    from wb_tool.adapters.worksheet_export import export_worksheet as export

    return str(export(worksheet, result, destination))
