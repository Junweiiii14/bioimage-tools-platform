"""Assigned-source-only fixed N detection and verified original-sample export."""

from collections.abc import Callable

from wb_tool.adapters.crop_export import export_crop
from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.crop import CropRequest
from wb_tool.application.intake_crop import (
    IntakeCropEvidence,
    WBIntakeCropProject,
    make_intake_crop_evidence,
)
from wb_tool.application.intake_workflow import (
    IntakeWorkflowTicket,
    validate_intake_workflow_ticket,
)
from wb_tool.domain.automatic import AutoWBSettings, detect_automatic_geometry


def propose_intake_crop(
    path: str,
    project: WBIntakeCropProject,
    row_id: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> IntakeCropEvidence:
    type(project).model_validate(dict(project))
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or row.source is None or cancelled():
        raise ValueError("原图未分配或定位已取消")
    image = load_tiff(path)
    if (image.sha256, image.pixels.shape, image.bit_depth) != (
        row.source.sha256,
        (row.height, row.width),
        row.bit_depth,
    ):
        raise ValueError("裁剪定位原图身份、尺寸或位深改变")
    detection = detect_automatic_geometry(
        image.pixels,
        AutoWBSettings(lane_count=row.lane_count, crop_policy="source_geometry@2"),
        cancelled=cancelled,
    )
    if cancelled():
        raise ValueError("固定N定位已取消")
    return make_intake_crop_evidence(project, row_id, detection)


def export_intake_crop(
    path: str,
    project: WBIntakeCropProject,
    row_id: str,
    destination: str,
    *,
    ticket: IntakeWorkflowTicket,
    cancelled: Callable[[], bool] = lambda: False,
) -> str:
    validate_intake_workflow_ticket(project, ticket)
    if ticket.stage != "crop" or ticket.target_id != row_id:
        raise ValueError("原值裁剪必须属于当前活动裁剪票据")
    if project.workflow.cancel_requested or cancelled():
        raise ValueError("原值裁剪已取消，不发布新文件")
    evidence = next((e for e in project.intake_crops if e.row_id == row_id), None)
    if evidence is None or not evidence.reviewed or evidence.crop is None:
        raise ValueError("请先明确核对并审核原图裁剪范围")
    return export_crop(
        path,
        CropRequest(evidence.source_sha256, project.revision, evidence.crop),
        destination,
        cancelled=cancelled,
    )
