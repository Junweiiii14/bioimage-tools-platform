"""Versioned public WB API; importing this module has no runtime side effects."""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from wb_tool.ui.background import WBBackground as WBBackground
    from wb_tool.ui.figure_view import FigureProjectView
    from wb_tool.ui.view import WBView

from wb_tool.adapters.automatic import automatic_project_row
from wb_tool.adapters.automatic_export import discover_tiffs
from wb_tool.adapters.export_discovery import discover_exports
from wb_tool.adapters.intake_crop import export_intake_crop, propose_intake_crop
from wb_tool.adapters.intake_figure import load_intake_figure_preview, prepare_intake_figure
from wb_tool.adapters.intake_output import export_intake_outputs
from wb_tool.adapters.metadata_input import read_metadata_file
from wb_tool.adapters.ocr_input import OCRImage, load_ocr_image
from wb_tool.adapters.quant_export import (
    export_wbquant_table,
    wbquant_csv_bytes,
    wbquant_table_rows,
    wbquant_xlsx_bytes,
)
from wb_tool.adapters.quant_supervision import replan_quant_lanes
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
from wb_tool.application.automatic import (
    AutomaticRowEvidence,
    AutomaticWBResult,
    WBAutomaticProject,
    install_automatic_request,
    install_automatic_result,
    row_is_ready,
    suggest_analysis_for_crop,
    suggest_automatic_wb,
    with_automatic_rows,
)
from wb_tool.application.crop import CropRequest
from wb_tool.application.crop_return import ReturnedCrop
from wb_tool.application.crop_suggestions import (
    CropSuggestion,
    WBReviewProject,
    apply_crop_suggestion,
    project_with_suggestions,
    read_figure_project,
    record_crop_suggestion,
)
from wb_tool.application.desktop_data import PreviewRaster, ProjectDerivedTables, WBJob, WBReply
from wb_tool.application.discovery import (
    ExportDiscovery,
    ExportObservation,
    ExportSelection,
    SignalRegion,
)
from wb_tool.application.document import WBDocument, WBWorksheetDocument, read_wb_document
from wb_tool.application.fig_quant import WBPartitionProject
from wb_tool.application.figure_project import (
    FigurePNG,
    FigureRender,
    FigureRow,
    FigureSourcePath,
    FigureTemplate,
    WBFigureProject,
    plan_figure_layout,
)
from wb_tool.application.figure_template import (
    LoadedFigureTemplate,
    PortableFigureTemplate,
    TemplateFont,
)
from wb_tool.application.group_review import confirm_quant_group, quant_group_reviewed
from wb_tool.application.import_labels import (
    FolderDiscoveryReport,
    SourceImportLabels,
    source_import_labels,
)
from wb_tool.application.instrument_intake import (
    IntakeAssignment,
    IntakeFigure,
    IntakeManifest,
    IntakeProtein,
    IntakeSource,
    WBIntakeProject,
    accept_export_selections,
    assign_intake_sources,
    confirm_intake,
    create_intake,
    install_export_discovery,
    intake_digest,
    intake_grouping,
    intake_needs_reference_discovery,
    intake_snapshot,
    register_intake_source,
    replace_intake_plan,
    save_intake_grouping,
    unassign_intake_sources,
)
from wb_tool.application.intake_crop import (
    IntakeCropEvidence,
    IntakeCropFile,
    IntakeCropSlot,
    WBIntakeCropProject,
    accept_automatic_intake_crop,
    automatic_intake_crop_allowed,
    complete_intake_crop,
    fail_intake_crop,
    intake_crop_companion_assets,
    prepare_intake_crops,
    record_intake_crop_proposal,
    review_intake_crop,
)
from wb_tool.application.intake_execution import (
    IntakeExecutionPlan,
    IntakePlannedCell,
    IntakePlannedFigure,
    IntakePlannedRow,
    IntakePlannedSlot,
    build_intake_execution_plan,
)
from wb_tool.application.intake_figure import (
    IntakeFigureEvidence,
    IntakeFigurePreparation,
    WBIntakeFigureProject,
    complete_intake_figure,
    complete_intake_measurement,
    intake_figure_digest,
    intake_figure_projection,
    intake_figure_rows,
    prepare_intake_figures,
    prepare_intake_measurement_revision,
)
from wb_tool.application.intake_grouping import (
    IntakeAcquisitionGroup,
    IntakeDraftFigure,
    IntakeGrouping,
    IntakeSequenceProtein,
    configure_intake_sequence,
)
from wb_tool.application.intake_output import (
    IntakeOutputEvidence,
    IntakeOutputPreparation,
    IntakeResultCell,
    WBIntakeOutputProject,
    fill_intake_table,
    intake_output_digest,
    prepare_intake_outputs,
    record_intake_output,
)
from wb_tool.application.intake_result_table import IntakeVisibleTable, intake_visible_table
from wb_tool.application.intake_revision import (
    begin_intake_group_revision,
    confirm_intake_group_revision,
    revise_completed_intake_crop,
    revise_intake_grouping,
)
from wb_tool.application.intake_sequence import continue_intake_sequence, prepare_intake_sequence
from wb_tool.application.intake_supervision import (
    IntakeGrid,
    WBIntakeGridProject,
    revise_intake_grid,
    revise_intake_quant,
)
from wb_tool.application.intake_workflow import (
    IntakeWorkflowLedger,
    IntakeWorkflowStep,
    IntakeWorkflowTicket,
    WBIntakeWorkflowProject,
    approve_intake_workflow,
    claim_intake_workflow_step,
    finish_intake_workflow_step,
    intake_workflow_digest,
    intake_workflow_snapshot,
    prepare_intake_workflow,
    recover_intake_workflow,
    request_intake_workflow_cancel,
    retry_intake_workflow_step,
    return_to_intake_editing,
)
from wb_tool.application.laboratory_layout import (
    DisplayFrame,
    FigureColumn,
    FigureComposition,
    FigureLayoutStyle,
    FigureSlice,
    LaboratoryLayout,
    WBLayoutProject,
    initial_composition,
    ordered_quant_rows,
    plan_laboratory_layout,
    with_figure_layout,
)
from wb_tool.application.manual_groups import add_manual_group, edit_quant_band
from wb_tool.application.ocr_protocol import (
    OCRConversation,
    OCRRequest,
    OCRResultFrame,
    OCRStartFrame,
    encode_ocr_frame,
    ocr_protocol_schema,
    parse_ocr_frame,
)
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    ProjectRowAnalysis,
    ProjectTableCell,
    ProjectTableSnapshot,
    WBAnalysisProject,
    analysis_is_current,
    fill_project_table,
    make_row_analysis,
    prepare_project_analyses,
    project_with_analyses,
    read_project_result,
    record_project_run,
    set_row_analysis,
    update_row_analysis_request,
)
from wb_tool.application.project_archive import ArchiveRunEvidence, project_runs
from wb_tool.application.project_metadata import (
    MetadataBook,
    MetadataCell,
    MetadataEntry,
    MetadataKey,
    MetadataPreview,
    MetadataSheet,
    apply_metadata,
    filename_metadata,
    preview_metadata,
)
from wb_tool.application.project_normalization import (
    ControlMode,
    NormalizationPlan,
    NormalizationSnapshot,
    NormalizationSource,
    NormalizedCell,
    ReferenceKind,
    SamplePair,
    WBNormalizedProject,
    fill_project_normalization,
    make_normalization_plan,
    normalization_is_current,
    project_with_normalizations,
)
from wb_tool.application.project_ocr import (
    LoadedProjectOCR,
    ProjectOCRLink,
    ProjectOCRRow,
    ProjectOCRState,
    WBProjectOCR,
    bind_project_ocr_row,
    fill_project_ocr_table,
    install_project_recognition,
    ocr_link_is_current,
    project_with_ocr,
    read_project_ocr_result,
)
from wb_tool.application.project_restore import (
    RestoredProjectResults,
    StagedProjectArchive,
    WBRestoredProject,
    imported_run,
    project_assets,
    restore_staged_project,
)
from wb_tool.application.quant_supervision import install_quant_request, update_quant_lane
from wb_tool.application.standalone_quant import ManualQuantTarget, configure_manual_quantification
from wb_tool.application.workbench_revision import (
    apply_workbench_metadata,
    prepare_workbench_revision,
    revise_workbench_figure_order,
    workbench_project_digest,
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
from wb_tool.domain.automatic import (
    AutoWBSettings,
    CropPolicy,
    detect_automatic_geometry,
    resize_crop_for_lane_count,
)
from wb_tool.domain.crop_detection import (
    CropCandidate,
    CropDetection,
    CropDetectionSettings,
    detect_crop_candidates,
)
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneProfiles, LaneROI, Polarity, compute_lane_profiles
from wb_tool.domain.quant_supervision import (
    QuantBandProposal,
    QuantLaneProposal,
    propose_quant_lane,
    propose_quant_lanes,
)
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
    "apply_workbench_metadata",
    "prepare_workbench_revision",
    "revise_workbench_figure_order",
    "workbench_project_digest",
    "IntakeGrid",
    "WBIntakeGridProject",
    "revise_intake_grid",
    "revise_intake_quant",
    "begin_intake_group_revision",
    "confirm_intake_group_revision",
    "revise_intake_grouping",
    "IntakeAcquisitionGroup",
    "IntakeDraftFigure",
    "IntakeGrouping",
    "IntakeSequenceProtein",
    "configure_intake_sequence",
    "prepare_intake_sequence",
    "continue_intake_sequence",
    "intake_needs_reference_discovery",
    "intake_grouping",
    "save_intake_grouping",
    "ExportDiscovery",
    "ExportObservation",
    "ExportSelection",
    "SignalRegion",
    "discover_exports",
    "install_export_discovery",
    "accept_export_selections",
    "export_intake_outputs",
    "intake_visible_table",
    "IntakeVisibleTable",
    "IntakeOutputEvidence",
    "IntakeOutputPreparation",
    "IntakeResultCell",
    "WBIntakeOutputProject",
    "fill_intake_table",
    "intake_output_digest",
    "prepare_intake_outputs",
    "record_intake_output",
    "revise_completed_intake_crop",
    "load_intake_figure_preview",
    "IntakeFigureEvidence",
    "IntakeFigurePreparation",
    "WBIntakeFigureProject",
    "complete_intake_figure",
    "complete_intake_measurement",
    "intake_figure_digest",
    "intake_figure_projection",
    "intake_figure_rows",
    "prepare_intake_figures",
    "prepare_intake_measurement_revision",
    "prepare_intake_figure",
    "IntakeCropEvidence",
    "IntakeCropFile",
    "IntakeCropSlot",
    "WBIntakeCropProject",
    "accept_automatic_intake_crop",
    "automatic_intake_crop_allowed",
    "intake_crop_companion_assets",
    "complete_intake_crop",
    "fail_intake_crop",
    "export_intake_crop",
    "prepare_intake_crops",
    "propose_intake_crop",
    "record_intake_crop_proposal",
    "review_intake_crop",
    "IntakeWorkflowLedger",
    "IntakeWorkflowStep",
    "IntakeWorkflowTicket",
    "WBIntakeWorkflowProject",
    "approve_intake_workflow",
    "claim_intake_workflow_step",
    "finish_intake_workflow_step",
    "intake_workflow_digest",
    "intake_workflow_snapshot",
    "prepare_intake_workflow",
    "recover_intake_workflow",
    "request_intake_workflow_cancel",
    "return_to_intake_editing",
    "retry_intake_workflow_step",
    "IntakeExecutionPlan",
    "IntakePlannedCell",
    "IntakePlannedFigure",
    "IntakePlannedRow",
    "IntakePlannedSlot",
    "build_intake_execution_plan",
    "IntakeAssignment",
    "IntakeFigure",
    "IntakeManifest",
    "IntakeProtein",
    "IntakeSource",
    "WBIntakeProject",
    "assign_intake_sources",
    "confirm_intake",
    "create_intake",
    "intake_digest",
    "intake_snapshot",
    "register_intake_source",
    "replace_intake_plan",
    "unassign_intake_sources",
    "confirm_quant_group",
    "quant_group_reviewed",
    "discover_tiffs",
    "ReturnedCrop",
    "return_reviewed_crop",
    "ManualQuantTarget",
    "add_manual_group",
    "edit_quant_band",
    "WBPartitionProject",
    "prepare_fig_quantification",
    "configure_manual_quantification",
    "export_wbquant_table",
    "wbquant_table_rows",
    "wbquant_csv_bytes",
    "wbquant_xlsx_bytes",
    "replan_quant_lanes",
    "update_quant_lane",
    "install_quant_request",
    "propose_quant_lane",
    "propose_quant_lanes",
    "QuantBandProposal",
    "QuantLaneProposal",
    "automatic_project_row",
    "with_automatic_rows",
    "AutoWBSettings",
    "CropPolicy",
    "resize_crop_for_lane_count",
    "AutomaticRowEvidence",
    "AutomaticWBResult",
    "WBAutomaticProject",
    "detect_automatic_geometry",
    "install_automatic_request",
    "install_automatic_result",
    "row_is_ready",
    "suggest_analysis_for_crop",
    "suggest_automatic_wb",
    "LoadedFigureTemplate",
    "PortableFigureTemplate",
    "TemplateFont",
    "export_figure_template",
    "read_figure_template",
    "FigureColumn",
    "FigureComposition",
    "ordered_quant_rows",
    "DisplayFrame",
    "FigureLayoutStyle",
    "FigureSlice",
    "LaboratoryLayout",
    "WBLayoutProject",
    "initial_composition",
    "plan_laboratory_layout",
    "with_figure_layout",
    "export_figure_image",
    "RestoredProjectResults",
    "StagedProjectArchive",
    "WBRestoredProject",
    "imported_run",
    "project_assets",
    "restore_staged_project",
    "stage_project_archive",
    "inspect_project_archive",
    "ArchiveRunEvidence",
    "project_runs",
    "MetadataBook",
    "MetadataCell",
    "MetadataEntry",
    "MetadataKey",
    "MetadataPreview",
    "MetadataSheet",
    "apply_metadata",
    "filename_metadata",
    "SourceImportLabels",
    "FolderDiscoveryReport",
    "source_import_labels",
    "preview_metadata",
    "read_metadata_file",
    "ProjectDerivedTables",
    "ControlMode",
    "NormalizationPlan",
    "NormalizationSnapshot",
    "NormalizationSource",
    "NormalizedCell",
    "ReferenceKind",
    "SamplePair",
    "WBNormalizedProject",
    "fill_project_normalization",
    "make_normalization_plan",
    "normalization_is_current",
    "project_with_normalizations",
    "export_project_normalization",
    "export_project_ocr_table",
    "LoadedProjectOCR",
    "ProjectOCRLink",
    "ProjectOCRRow",
    "ProjectOCRState",
    "WBProjectOCR",
    "bind_project_ocr_row",
    "fill_project_ocr_table",
    "install_project_recognition",
    "ocr_link_is_current",
    "project_with_ocr",
    "read_project_ocr_result",
    "export_project_table",
    "ProjectRowAnalysis",
    "WBAnalysisProject",
    "LoadedProjectResult",
    "ProjectTableCell",
    "ProjectTableSnapshot",
    "analysis_is_current",
    "project_with_analyses",
    "make_row_analysis",
    "set_row_analysis",
    "update_row_analysis_request",
    "prepare_project_analyses",
    "record_project_run",
    "read_project_result",
    "fill_project_table",
    "CropSuggestion",
    "WBReviewProject",
    "apply_crop_suggestion",
    "project_with_suggestions",
    "read_figure_project",
    "record_crop_suggestion",
    "CropCandidate",
    "CropDetection",
    "CropDetectionSettings",
    "detect_crop_candidates",
    "suggest_crops",
    "FigureTemplate",
    "FigureRow",
    "WBFigureProject",
    "FigureRender",
    "FigurePNG",
    "OCRImage",
    "load_ocr_image",
    "FigureSourcePath",
    "plan_figure_layout",
    "create_figure_project_view",
    "render_figure",
    "export_figure_bundle",
    "CropRequest",
    "export_crop",
    "fixed_lane_grid",
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


def suggest_crops(
    source: str,
    source_sha256: str,
    row_id: str,
    revision: int,
    settings: CropDetectionSettings,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> CropSuggestion:
    from wb_tool.adapters.crop_suggestions import suggest_crops as suggest

    return suggest(source, source_sha256, row_id, revision, settings, cancelled=cancelled)


def create_figure_project_view(parent: "QWidget | None" = None) -> "FigureProjectView":
    from wb_tool.ui.figure_view import FigureProjectView

    return FigureProjectView(parent)


def return_reviewed_crop(
    project: WBFigureProject,
    row_id: str,
    original_path: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> ReturnedCrop:
    from wb_tool.adapters.crop_return import return_reviewed_crop as export

    return export(project, row_id, original_path, cancelled=cancelled)


def render_figure(
    project: WBFigureProject, sources: tuple[FigureSourcePath, ...], *, require_review: bool = True
) -> FigureRender:
    from wb_tool.adapters.figure_export import render_figure as render

    return render(project, sources, require_review=require_review)


def export_figure_bundle(
    project: WBFigureProject,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
    runs: tuple[ArchiveRunEvidence, ...] = (),
) -> str:
    from wb_tool.adapters.figure_export import export_figure_bundle as export

    return export(project, sources, destination, cancelled=cancelled, runs=runs)


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


def prepare_fig_quantification(
    source: str,
    project: WBFigureProject,
    row_id: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> WBPartitionProject:
    from wb_tool.adapters.fig_quant import prepare_fig_quantification as prepare

    return prepare(source, project, row_id, cancelled=cancelled)


def export_worksheet(worksheet: Worksheet, result: AnalysisResult, destination: str) -> str:
    from wb_tool.adapters.worksheet_export import export_worksheet as export

    return str(export(worksheet, result, destination))


def export_project_table(
    project: WBFigureProject,
    results: tuple[LoadedProjectResult, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    from wb_tool.adapters.project_export import export_project_table as export

    return str(export(project, results, destination, cancelled=cancelled))


def export_project_ocr_table(
    project: WBProjectOCR,
    results: tuple[LoadedProjectResult, ...],
    loaded: LoadedProjectOCR | None,
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    from wb_tool.adapters.project_ocr_export import export_project_ocr_table as export

    return str(export(project, results, loaded, destination, cancelled=cancelled))


def export_project_normalization(
    project: WBNormalizedProject,
    results: tuple[LoadedProjectResult, ...],
    loaded: LoadedProjectOCR | None,
    destination: str,
    *,
    ocr_labels: bool = False,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    from wb_tool.adapters.normalization_export import export_project_normalization as export

    return str(
        export(project, results, loaded, destination, ocr_labels=ocr_labels, cancelled=cancelled)
    )


def export_crop(source: str, request: CropRequest, destination: str) -> str:
    from wb_tool.adapters.crop_export import export_crop as export

    return export(source, request, destination)


def export_figure_image(
    project: WBFigureProject,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    from wb_tool.adapters.figure_image_export import export_figure_image as export

    return export(project, sources, destination, cancelled=cancelled)


def stage_project_archive(
    source: str, destination: str, *, cancelled: Callable[[], bool] = lambda: False
) -> StagedProjectArchive:
    from wb_tool.adapters.archive_restore import stage_project_archive as stage

    return stage(source, destination, cancelled=cancelled)


def inspect_project_archive(
    source: str, *, cancelled: Callable[[], bool] = lambda: False
) -> WBFigureProject:
    from wb_tool.adapters.archive_restore import inspect_project_archive as inspect

    return inspect(source, cancelled=cancelled)


def export_figure_template(
    project: WBFigureProject,
    sources: tuple[FigureSourcePath, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    from wb_tool.adapters.figure_template_io import export_figure_template as export

    return export(project, sources, destination, cancelled=cancelled)


def read_figure_template(
    source: str, *, cancelled: Callable[[], bool] = lambda: False
) -> LoadedFigureTemplate:
    from wb_tool.adapters.figure_template_io import read_figure_template as read

    return read(source, cancelled=cancelled)
