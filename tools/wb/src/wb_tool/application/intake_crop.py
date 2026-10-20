"""Fixed manifest slots and reviewable source geometry, separate from measurements."""

from dataclasses import replace
from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from tool_contracts.api import AssetRef

from wb_tool.application.document import DocumentIO
from wb_tool.application.intake_execution import planned_intake_slots
from wb_tool.application.intake_workflow import (
    IntakeWorkflowLedger,
    IntakeWorkflowTicket,
    WBIntakeWorkflowProject,
    finish_intake_workflow_step,
    intake_workflow_digest,
    retry_intake_workflow_step,
)
from wb_tool.domain.crop_detection import CropDetection
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI


class IntakeCropSlot(DocumentIO):
    model_config = ConfigDict(revalidate_instances="always")
    slot_id: str = Field(pattern="^[0-9a-f]{64}$")
    position: int = Field(ge=1, le=96)
    roi: LaneROI | None = None
    # Signal evidence is not loading/exclusion status or a quantitative value.
    signal: Literal["unlocated", "undetermined", "detected", "weak", "not_detected"] = "unlocated"


class IntakeCropFile(DocumentIO):
    path: str = Field(min_length=1, max_length=32768)
    sha256: str = Field(pattern="^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0, le=512 * 1024 * 1024)


class IntakeCropEvidence(DocumentIO):
    model_config = ConfigDict(revalidate_instances="always")
    policy: Literal["intake_crop@1"] = "intake_crop@1"
    row_id: str = Field(min_length=1, max_length=80)
    source_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    source_revision: int = Field(ge=0)
    lane_count: int = Field(ge=1, le=96)
    detection: CropDetection | None = None
    selected_index: int | None = Field(default=None, ge=0, le=7)
    crop: LaneROI | None = None
    slots: tuple[IntakeCropSlot, ...] = Field(min_length=1, max_length=96)
    reviewed: bool = False
    raw_crop: AssetRef | None = None
    reason: str = Field(default="", max_length=2000)
    geometry_policy: Literal["source_geometry@2", "explicit_original_roi@1"] = "source_geometry@2"

    @model_validator(mode="after")
    def coherent(self) -> "IntakeCropEvidence":
        if len(self.slots) != self.lane_count or tuple(s.position for s in self.slots) != tuple(
            range(1, self.lane_count + 1)
        ):
            raise ValueError("裁剪证据必须保留完整固定N槽位")
        if len({s.slot_id for s in self.slots}) != self.lane_count:
            raise ValueError("槽位身份不能重复")
        if self.crop is None:
            if self.reviewed or self.raw_crop or any(s.roi is not None for s in self.slots):
                raise ValueError("未定位不能带审核成功、原值产物或伪造槽位坐标")
        else:
            if self.crop.lane_id != self.row_id:
                raise ValueError("裁剪证据行身份不一致")
            previous = self.crop.x0
            for slot in self.slots:
                roi = slot.roi
                if (
                    roi is None
                    or roi.lane_id != slot.slot_id
                    or not (
                        previous == roi.x0 < roi.x1 <= self.crop.x1
                        and self.crop.y0 <= roi.y0 < roi.y1 <= self.crop.y1
                    )
                ):
                    raise ValueError("槽位须从左到右完整覆盖裁剪宽度且位于原坐标范围内")
                previous = roi.x1
            if previous != self.crop.x1:
                raise ValueError("槽位不能丢失裁剪末端")
        if any((s.roi is None) != (s.signal == "unlocated") for s in self.slots):
            raise ValueError("未定位槽位不能伪装为信号状态")
        if self.raw_crop is not None and not self.reviewed:
            raise ValueError("未经明确审核不能发布原值裁剪")
        if self.selected_index is not None and (
            self.detection is None or self.selected_index >= len(self.detection.candidates)
        ):
            raise ValueError("裁剪候选选择越界")
        if self.detection is not None:
            d = self.detection
            if (
                d.width < 1
                or d.height < 1
                or d.width * d.height > 16_000_000
                or len(d.candidates) > 8
            ):
                raise ValueError("检测证据超出尺寸或候选预算")
            rois = [d.membrane, d.marker, d.sample_region]
            for c in d.candidates:
                rois.extend((c.roi, *c.lane_rois))
                if len(c.lane_snr) != self.lane_count or len(c.lane_rois) != self.lane_count:
                    raise ValueError("检测候选不能丢失固定N槽位")
            if any(r is not None and (r.x1 > d.width or r.y1 > d.height) for r in rois):
                raise ValueError("检测候选超出原图尺寸")
        return self


class WBIntakeCropProject(WBIntakeWorkflowProject):
    schema_version: int = Field(default=12, ge=12, le=12)
    intake_crops: tuple[IntakeCropEvidence, ...] = Field(default=(), max_length=512)

    @model_validator(mode="after")
    def crop_identity(self) -> "WBIntakeCropProject":
        rows = {r.row_id: r for r in self.rows}
        if len({e.row_id for e in self.intake_crops}) != len(self.intake_crops):
            raise ValueError("同一行不能保存重复当前裁剪证据")
        for evidence in self.intake_crops:
            row = rows.get(evidence.row_id)
            if (
                row is None
                or row.source is None
                or (
                    evidence.source_sha256 != row.source.sha256
                    or evidence.source_revision > self.revision
                    or evidence.lane_count != row.lane_count
                )
            ):
                raise ValueError("裁剪证据与清单来源、N或修订不一致")
            expected = planned_intake_slots(self.project_id, row.row_id, row.lane_count)
            if tuple(s.slot_id for s in evidence.slots) != tuple(s.slot_id for s in expected):
                raise ValueError("裁剪槽位身份偏离已确认清单")
            if evidence.crop is not None and (
                evidence.crop.x1 > row.width or evidence.crop.y1 > row.height
            ):
                raise ValueError("裁剪证据超出原图")
            if evidence.detection is not None and (
                evidence.detection.width != row.width
                or evidence.detection.height != row.height
                or evidence.detection.settings.lane_count != row.lane_count
            ):
                raise ValueError("检测证据尺寸或固定N与原图不一致")
            if evidence.reviewed and (row.roi != evidence.crop or not row.reviewed):
                raise ValueError("已审核裁剪须与当前行几何一致")
        evidence_by_row = {e.row_id: e for e in self.intake_crops}
        for step in self.workflow.steps:
            if step.stage in {"compose", "measure"} and step.status in {"running", "done"}:
                members = [p for p in self.intake.proteins if p.figure_id == step.target_id]
                if any(
                    (e := evidence_by_row.get(p.protein_id)) is None
                    or not e.reviewed
                    or e.raw_crop is None
                    for p in members
                ):
                    raise ValueError("完整Fig必须先有全部已审核原值裁剪证据")
        return self


def prepare_intake_crops(project: WBIntakeWorkflowProject) -> WBIntakeCropProject:
    checked = type(project).model_validate(dict(project))
    if isinstance(checked, WBIntakeCropProject):
        return checked
    if any(s.attempt for s in checked.workflow.steps):
        raise ValueError("旧执行账本已有尝试，不能无证据迁移为裁剪完成")
    return WBIntakeCropProject.model_validate({**dict(checked), "schema_version": 12})


def make_intake_crop_evidence(
    project: WBIntakeCropProject, row_id: str, detection: CropDetection
) -> IntakeCropEvidence:
    """Keep every slot even when no geometry can be located; never infer missing ends."""
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or row.source is None:
        raise ValueError("请选择已分配原图的蛋白行")
    candidate = detection.candidates[0] if len(detection.candidates) == 1 else None
    # Source policy must locate all original-coordinate lanes itself. No grid fallback.
    located = candidate is not None and len(candidate.lane_rois) == row.lane_count
    identities = planned_intake_slots(project.project_id, row_id, row.lane_count)
    slots = tuple(
        IntakeCropSlot(
            slot_id=slot.slot_id,
            position=slot.position,
            roi=replace(candidate.lane_rois[i], lane_id=slot.slot_id)
            if located and candidate
            else None,
            signal=(
                "detected"
                if slot.position in candidate.detected_lanes
                else "weak"
                if slot.position in candidate.weak_lanes
                else "not_detected"
            )
            if located and candidate
            else "unlocated",
        )
        for i, slot in enumerate(identities)
    )
    return IntakeCropEvidence(
        row_id=row_id,
        source_sha256=row.source.sha256,
        source_revision=project.revision,
        lane_count=row.lane_count,
        detection=detection,
        selected_index=0 if located else None,
        crop=replace(candidate.roi, lane_id=row_id) if located and candidate else None,
        slots=slots,
        reason="自动定位建议未经审核；请核对Marker、首尾空槽和每个样本范围"
        if located
        else "未取得完整固定N几何：" + ";".join(detection.flags),
    )


def review_intake_crop(
    project: WBIntakeCropProject, row_id: str, crop: LaneROI, *, expected_digest: str
) -> WBIntakeCropProject:
    """Explicitly confirm an original rectangle, then require a fresh owned crop attempt."""
    if project.workflow.editing:
        raise ValueError("分组编辑中不能同时修正裁剪")
    if expected_digest != intake_workflow_digest(project):
        raise ValueError("裁剪草稿已变化，请重新核对")
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or row.source is None or crop.lane_id != row_id:
        raise ValueError("裁剪行或来源不一致")
    identities = planned_intake_slots(project.project_id, row_id, row.lane_count)
    geometry = fixed_lane_grid(crop, row.lane_count)
    previous = next((e for e in project.intake_crops if e.row_id == row_id), None)
    if previous is None:
        raise ValueError("请先取得该行定位状态，不能跳过失败/复核记录")
    step = next(s for s in project.workflow.steps if s.stage == "crop" and s.target_id == row_id)
    if step.status == "pending" and previous.reviewed and previous.raw_crop is None:
        # A saved review awaiting export may be corrected again. Rebase against the
        # actual saved digest; never broaden retry to arbitrary pending/done stages.
        if any(s.status == "running" for s in project.workflow.steps):
            raise ValueError("请等待当前阶段退出后再修正裁剪")
        workflow = IntakeWorkflowLedger.model_validate(
            {
                **dict(project.workflow),
                "approved": False,
                "steps": tuple(
                    s.model_copy(
                        update={"status": "needs_review", "reason": "明确调整尚未导出的已审核范围"}
                    )
                    if s == step
                    else s
                    for s in project.workflow.steps
                ),
            }
        )
        project = type(project).model_validate({**dict(project), "workflow": workflow})
        expected_digest = intake_workflow_digest(project)
    reset = retry_intake_workflow_step(project, "crop", row_id, expected_digest=expected_digest)
    evidence = IntakeCropEvidence(
        row_id=row_id,
        source_sha256=row.source.sha256,
        source_revision=project.revision,
        lane_count=row.lane_count,
        detection=previous.detection,
        crop=crop,
        slots=tuple(
            IntakeCropSlot(
                slot_id=s.slot_id,
                position=s.position,
                roi=replace(r, lane_id=s.slot_id),
                signal="undetermined",
            )
            for s, r in zip(identities, geometry, strict=True)
        ),
        reviewed=True,
        geometry_policy="explicit_original_roi@1",
        reason="人工明确确认原图范围；槽位信号状态待原像素测量，不推断未上样",
    )
    return type(project).model_validate(
        {
            **dict(reset),
            "rows": tuple(
                r.model_copy(update={"roi": crop, "reviewed": True}) if r.row_id == row_id else r
                for r in reset.rows
            ),
            "intake_crops": (*[e for e in project.intake_crops if e.row_id != row_id], evidence),
        }
    )


def record_intake_crop_proposal(
    project: WBIntakeCropProject, ticket: IntakeWorkflowTicket, evidence: IntakeCropEvidence
) -> WBIntakeCropProject:
    if ticket.stage != "crop" or ticket.target_id != evidence.row_id:
        raise ValueError("裁剪建议回复身份不一致")
    if evidence.reviewed or evidence.raw_crop is not None:
        raise ValueError("自动定位不能伪造人工审核或已发布裁剪")
    finished = finish_intake_workflow_step(project, ticket, "needs_review", reason=evidence.reason)
    if not isinstance(finished, WBIntakeCropProject):
        raise ValueError("缺少固定N裁剪项目")
    if finished.workflow.cancel_requested:
        return finished
    return type(project).model_validate(
        {
            **dict(finished),
            "intake_crops": (
                *[e for e in project.intake_crops if e.row_id != evidence.row_id],
                evidence,
            ),
        }
    )


def complete_intake_crop(
    project: WBIntakeCropProject, ticket: IntakeWorkflowTicket, raw_crop: AssetRef
) -> WBIntakeCropProject:
    evidence = next((e for e in project.intake_crops if e.row_id == ticket.target_id), None)
    if ticket.stage != "crop" or evidence is None or not evidence.reviewed:
        raise ValueError("原值裁剪完成需要明确审核的同一行几何")
    finished = finish_intake_workflow_step(project, ticket, "done")
    if not isinstance(finished, WBIntakeCropProject):
        raise ValueError("缺少固定N裁剪项目")
    if finished.workflow.cancel_requested:
        return finished
    return type(project).model_validate(
        {
            **dict(finished),
            "intake_crops": tuple(
                e.model_copy(update={"raw_crop": raw_crop}) if e.row_id == ticket.target_id else e
                for e in project.intake_crops
            ),
        }
    )


def fail_intake_crop(
    project: WBIntakeCropProject, ticket: IntakeWorkflowTicket, reason: str
) -> WBIntakeCropProject:
    if ticket.stage != "crop":
        raise ValueError("裁剪失败回复须属于当前裁剪阶段")
    finished = finish_intake_workflow_step(project, ticket, "failed", reason=reason)
    if not isinstance(finished, WBIntakeCropProject):
        raise ValueError("缺少固定N裁剪项目")
    if finished.workflow.cancel_requested:
        return finished
    row = next(r for r in project.rows if r.row_id == ticket.target_id)
    if row.source is None:
        raise ValueError("裁剪原图缺失")
    evidence = IntakeCropEvidence(
        row_id=row.row_id,
        source_sha256=row.source.sha256,
        source_revision=project.revision,
        lane_count=row.lane_count,
        slots=tuple(
            IntakeCropSlot(slot_id=s.slot_id, position=s.position)
            for s in planned_intake_slots(project.project_id, row.row_id, row.lane_count)
        ),
        reason=reason,
    )
    return type(project).model_validate(
        {
            **dict(finished),
            "intake_crops": (
                *[e for e in project.intake_crops if e.row_id != row.row_id],
                evidence,
            ),
        }
    )
