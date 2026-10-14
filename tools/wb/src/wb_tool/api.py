"""Versioned public WB API; importing this module has no runtime side effects."""

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
from wb_tool.application.document import WBDocument
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
from wb_tool.domain.lanes import LaneProfiles, LaneROI, Polarity, compute_lane_profiles
from wb_tool.domain.quantify import (
    BandBounds,
    Baseline,
    ProfileMeasurement,
    QuantificationError,
    integrate_profile,
)

__all__ = [
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
