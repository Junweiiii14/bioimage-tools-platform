"""Fixed manifest slots and reviewable source geometry, separate from measurements."""

from dataclasses import replace
from math import cos, isfinite, radians, sin
from typing import Literal, cast

from pydantic import (
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)
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

COMMON_GEOMETRY = frozenset({"source_common_band_geometry@1", "guided_common_band_geometry@1"})
PROMINENT_GEOMETRY = frozenset(
    {"source_prominent_band_geometry@1", "guided_prominent_band_geometry@1"}
)
ROW_GEOMETRY = COMMON_GEOMETRY | PROMINENT_GEOMETRY
AUTOMATIC_POLICIES = frozenset({"intake_crop@2", "intake_crop@3", "intake_crop@4", "intake_crop@5"})


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


class IntakeWidthCalibration(DocumentIO):
    """A frozen, explicitly reviewed original-coordinate width, not a preview."""

    source_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    source_revision: int = Field(ge=0)
    lane_count: int = Field(ge=1, le=96)
    roi: LaneROI
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)

    @model_validator(mode="after")
    def original_ratio(self) -> "IntakeWidthCalibration":
        if (
            self.roi.x1 > self.image_width
            or self.roi.y1 > self.image_height
            or self.roi.width < 2 * self.lane_count
            or abs(self.roi.width / self.lane_count * 0.8 - (self.roi.y1 - self.roi.y0)) > 1
        ):
            raise ValueError("槽宽校准须为原图中已确认的5N:4范围")
        return self


class IntakeFixedGrid(DocumentIO):
    policy: Literal["fixed_n_frame@1", "fixed_n_frame@2"] = "fixed_n_frame@1"
    sampling_policy: Literal["source_axis_partition@1", "source_axis_partition@2"] = (
        "source_axis_partition@1"
    )
    lane_width_pixels: float = Field(ge=2)
    width_basis: Literal["source_row_estimate", "reviewed_source_roi"]
    calibration: IntakeWidthCalibration | None = None
    source_estimate: CropDetection | None = None
    sampling_limits: tuple[LaneROI, ...] = Field(default=(), max_length=96)
    review_positions: tuple[int, ...] = Field(default=(), max_length=96)

    @model_validator(mode="after")
    def provenance(self) -> "IntakeFixedGrid":
        if (self.width_basis == "reviewed_source_roi") != (self.calibration is not None):
            raise ValueError("固定槽宽须保留真实来源，不能把估计冒充人工校准")
        if (
            self.calibration is not None
            and abs(
                self.lane_width_pixels - self.calibration.roi.width / self.calibration.lane_count
            )
            > 1e-7
        ):
            raise ValueError("固定槽宽与原图校准不符")
        return self


def intake_crop_companion_assets(
    project: "WBIntakeCropProject", row_id: str
) -> tuple[AssetRef, ...]:
    source_id = next(
        (a.source_id for a in project.intake.assignments if a.protein_id == row_id), None
    )
    if source_id is None:
        return ()
    group = (
        next((g for g in project.intake.grouping.groups if g.selected_source_id == source_id), None)
        if project.intake.grouping
        else None
    )
    if group is None or len(group.source_ids) != 3:
        return ()
    peers = tuple(s for s in project.intake.sources if s.source_id in group.source_ids)
    if len(peers) != 3 or len({(s.width, s.height) for s in peers}) != 1:
        return ()
    return tuple(s.asset for s in peers if s.source_id != source_id)


def automatic_intake_crop_allowed(evidence: "IntakeCropEvidence") -> bool:
    """Versioned geometry only; never infer loading, identity or valid signal."""
    detection = evidence.detection
    if (
        detection is None
        or detection.algorithm_id
        not in {
            "source_signal_geometry@1",
            "instrument_guided_geometry@1",
            "source_signal_geometry@2",
            "instrument_guided_geometry@2",
            "source_common_band_geometry@1",
            "guided_common_band_geometry@1",
            "source_prominent_band_geometry@1",
            "guided_prominent_band_geometry@1",
        }
        or not {
            "signal_orientation_fit@1",
            "signal_orientation_fit@2",
            "signal_orientation_fit@3",
            "unrotated_complete_geometry@1",
        }.intersection(detection.flags)
        or len(detection.candidates) != 1
        or evidence.selected_index != 0
        or evidence.geometry_policy != detection.algorithm_id
    ):
        return False
    candidate = detection.candidates[0]
    fixed_width = "fixed_width_grid@1" in detection.flags
    common = detection.algorithm_id in ROW_GEOMETRY
    if (
        common
        and (
            "prominent_band_row@1"
            if detection.algorithm_id in PROMINENT_GEOMETRY
            else "common_band_row@1"
        )
        not in detection.flags
    ):
        return False
    if detection.algorithm_id.endswith("@2") or common:
        grid = evidence.fixed_grid
        frame = candidate.display_frame
        if (
            grid is None
            or frame is None
            or (
                grid.policy != "fixed_n_frame@2" or "fixed_n_frame@2" not in detection.flags
                if detection.algorithm_id in PROMINENT_GEOMETRY
                else grid.policy != "fixed_n_frame@1" or "fixed_n_frame@1" not in detection.flags
            )
            or grid.sampling_policy not in detection.flags
            or len(grid.sampling_limits) != evidence.lane_count
            or abs(frame.width - evidence.lane_count * grid.lane_width_pixels) > 1e-7
            or (
                "prominent_envelope_frame@1" not in detection.flags
                if detection.algorithm_id in PROMINENT_GEOMETRY
                else abs(frame.height - 0.8 * grid.lane_width_pixels) > 1e-7
            )
        ):
            return False
        if fixed_width and grid.width_basis == "source_row_estimate":
            estimate = grid.source_estimate
            if (
                estimate is None
                or estimate.algorithm_id != "source_geometry@2"
                or len(estimate.candidates) != 1
                or estimate.settings.lane_count != evidence.lane_count
                or (estimate.width, estimate.height) != (detection.width, detection.height)
                or (seed := estimate.candidates[0].display_frame) is None
            ):
                return False
            delta = grid.lane_width_pixels - seed.width / evidence.lane_count
            if delta < -1e-7 or delta > seed.width / evidence.lane_count**2 * 0.5 + 1e-7:
                return False
            if delta > 1e-7 and "source_width_refined@1" not in detection.flags:
                return False
        if (calibration := grid.calibration) is not None and (
            calibration.source_sha256 != evidence.source_sha256
            or calibration.source_revision > evidence.source_revision
            or calibration.lane_count != evidence.lane_count
            or (calibration.image_width, calibration.image_height)
            != (detection.width, detection.height)
        ):
            return False
    if (
        detection.algorithm_id == "instrument_guided_geometry@2"
        and "registered_signal_pair@1" not in detection.flags
    ):
        return False
    if detection.algorithm_id.endswith("@2") and (
        (
            not fixed_width
            and (
                candidate.possible_empty_lanes
                or set(candidate.detected_lanes) | set(candidate.weak_lanes)
                != set(range(1, evidence.lane_count + 1))
            )
        )
        or (
            "unrotated_complete_geometry@1" in detection.flags
            and (candidate.display_frame is None or candidate.display_frame.angle_degrees != 0)
        )
    ):
        return False
    return bool(
        evidence.crop == replace(candidate.roi, lane_id=evidence.row_id)
        and detection.settings.lane_count == evidence.lane_count
        and len(candidate.lane_rois) == evidence.lane_count
        and tuple(s.roi for s in evidence.slots)
        == tuple(
            replace(r, lane_id=s.slot_id)
            for s, r in zip(evidence.slots, candidate.lane_rois, strict=True)
        )
        and candidate.display_frame is not None
        and candidate.display_frame.width > 0
        and candidate.display_frame.height > 0
        and all(
            isfinite(value)
            for value in (
                candidate.display_frame.center_x,
                candidate.display_frame.center_y,
                candidate.display_frame.width,
                candidate.display_frame.height,
                candidate.display_frame.angle_degrees,
            )
        )
        and abs(candidate.display_frame.angle_degrees) <= (30 if common else 10)
        and all(
            candidate.roi.x0 - 1e-7 <= x <= candidate.roi.x1 + 1e-7
            and candidate.roi.y0 - 1e-7 <= y <= candidate.roi.y1 + 1e-7
            for x, y in (
                (
                    candidate.display_frame.center_x
                    + cos(radians(candidate.display_frame.angle_degrees)) * u
                    - sin(radians(candidate.display_frame.angle_degrees)) * v,
                    candidate.display_frame.center_y
                    + sin(radians(candidate.display_frame.angle_degrees)) * u
                    + cos(radians(candidate.display_frame.angle_degrees)) * v,
                )
                for u in (-candidate.display_frame.width / 2, candidate.display_frame.width / 2)
                for v in (-candidate.display_frame.height / 2, candidate.display_frame.height / 2)
            )
        )
    )


class IntakeCropEvidence(DocumentIO):
    model_config = ConfigDict(revalidate_instances="always")
    policy: Literal[
        "intake_crop@1",
        "intake_crop@2",
        "intake_crop@3",
        "intake_crop@4",
        "intake_crop@5",
        "intake_crop_display_review@1",
    ] = "intake_crop@1"
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
    fixed_grid: IntakeFixedGrid | None = None
    geometry_policy: Literal[
        "source_geometry@2",
        "explicit_original_roi@1",
        "instrument_guided_geometry@1",
        "source_signal_geometry@1",
        "instrument_guided_geometry@2",
        "source_signal_geometry@2",
        "source_common_band_geometry@1",
        "guided_common_band_geometry@1",
        "source_prominent_band_geometry@1",
        "guided_prominent_band_geometry@1",
    ] = "source_geometry@2"

    @model_serializer(mode="wrap")
    def preserve_legacy_shape(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        result = cast(dict[str, object], handler(self))
        if self.fixed_grid is None:
            result.pop("fixed_grid", None)
        return result

    @property
    def geometry_ready(self) -> bool:
        """Accepted machine geometry remains distinct from human review."""
        return self.reviewed or self.policy in AUTOMATIC_POLICIES

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
            bounded_sampling = (
                self.fixed_grid is not None
                and self.fixed_grid.sampling_policy == "source_axis_partition@2"
                and (self.geometry_policy.endswith("@2") or self.geometry_policy in ROW_GEOMETRY)
            )
            first = self.slots[0].roi
            previous = first.x0 if bounded_sampling and first is not None else self.crop.x0
            if previous < self.crop.x0:
                raise ValueError("原值槽位不能超出裁剪范围")
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
            if not bounded_sampling and previous != self.crop.x1:
                raise ValueError("槽位不能丢失裁剪末端")
        if any((s.roi is None) != (s.signal == "unlocated") for s in self.slots):
            raise ValueError("未定位槽位不能伪装为信号状态")
        if (grid := self.fixed_grid) is not None:
            if tuple(sorted(set(grid.review_positions))) != grid.review_positions or any(
                type(i) is not int or not 1 <= i <= self.lane_count for i in grid.review_positions
            ):
                raise ValueError("局部信号复核必须绑定唯一的固定槽位")
            if grid.sampling_limits and (
                self.detection is None
                or len(grid.sampling_limits) != self.lane_count
                or any(
                    slot.roi is None
                    or (limit.x0, limit.x1) != (slot.roi.x0, slot.roi.x1)
                    or not limit.y0 <= slot.roi.y0 < slot.roi.y1 <= limit.y1
                    or limit.x1 > self.detection.width
                    or limit.y1 > self.detection.height
                    for slot, limit in zip(self.slots, grid.sampling_limits, strict=True)
                )
            ):
                raise ValueError("安全采样范围须绑定原图与完整槽位，不能截断目标")
        if self.raw_crop is not None and not self.geometry_ready:
            raise ValueError("未经明确审核不能发布原值裁剪")
        if self.policy == "intake_crop_display_review@1" and not self.reviewed:
            raise ValueError("显示角度复核须保留明确人工确认")
        if self.policy in AUTOMATIC_POLICIES and (
            self.reviewed
            or not automatic_intake_crop_allowed(self)
            or (self.policy == "intake_crop@3") != self.geometry_policy.endswith("@2")
            or (self.policy == "intake_crop@4") != (self.geometry_policy in COMMON_GEOMETRY)
            or (self.policy == "intake_crop@5") != (self.geometry_policy in PROMINENT_GEOMETRY)
        ):
            raise ValueError("自动采纳须有唯一完整原图几何，不能冒充人工审核")
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
            if evidence.policy in AUTOMATIC_POLICIES and (row.roi != evidence.crop or row.reviewed):
                raise ValueError("自动采纳几何须与原图行一致且保持未人工审核")
            if (
                evidence.policy in {"intake_crop@2", "intake_crop_display_review@1"}
                and evidence.detection is not None
                and evidence.detection.algorithm_id == "instrument_guided_geometry@1"
            ):
                companions = {
                    asset.sha256 for asset in intake_crop_companion_assets(self, row.row_id)
                }
                declared = {
                    flag.split(":", 1)[1]
                    for flag in evidence.detection.flags
                    if flag.startswith(("guide_sha256:", "guide_peer_sha256:"))
                }
                if len(companions) != 2 or declared != companions:
                    raise ValueError("辅助定位必须绑定同组全部已校验原图资产")
            if (
                evidence.policy
                in {
                    "intake_crop@3",
                    "intake_crop@4",
                    "intake_crop@5",
                    "intake_crop_display_review@1",
                }
                and evidence.detection is not None
                and evidence.geometry_policy
                in {
                    "instrument_guided_geometry@2",
                    "guided_common_band_geometry@1",
                    "guided_prominent_band_geometry@1",
                }
            ):
                companions = {
                    asset.sha256 for asset in intake_crop_companion_assets(self, row.row_id)
                }
                declared = {
                    flag.split(":", 1)[1]
                    for flag in evidence.detection.flags
                    if flag.startswith("verified_group_sha256:")
                }
                guides = {
                    flag.split(":", 1)[1]
                    for flag in evidence.detection.flags
                    if flag.startswith("guide_sha256:")
                }
                if (
                    len(companions) != 2
                    or declared != companions | {row.source.sha256}
                    or len(guides) != 1
                    or not guides <= companions
                ):
                    raise ValueError("辅助定位必须核验完整三图，且白光不能替代所选来源")
        evidence_by_row = {e.row_id: e for e in self.intake_crops}
        for step in self.workflow.steps:
            if step.stage in {"compose", "measure"} and step.status in {"running", "done"}:
                members = [p for p in self.intake.proteins if p.figure_id == step.target_id]
                if any(
                    (e := evidence_by_row.get(p.protein_id)) is None
                    or not e.geometry_ready
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
    project: WBIntakeCropProject,
    row_id: str,
    detection: CropDetection,
    *,
    width_calibration: IntakeWidthCalibration | None = None,
    width_estimate: CropDetection | None = None,
    sampling_limits: tuple[LaneROI, ...] = (),
    review_positions: tuple[int, ...] = (),
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
                "undetermined"
                if f"grid_signal_unresolved:{slot.position}" in detection.flags
                else "detected"
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
        fixed_grid=IntakeFixedGrid(
            policy="fixed_n_frame@2"
            if detection.algorithm_id in PROMINENT_GEOMETRY
            else "fixed_n_frame@1",
            sampling_policy=(
                "source_axis_partition@2"
                if "source_axis_partition@2" in detection.flags
                else "source_axis_partition@1"
            ),
            lane_width_pixels=candidate.display_frame.width / row.lane_count,
            width_basis="reviewed_source_roi"
            if width_calibration is not None
            else "source_row_estimate",
            calibration=width_calibration,
            source_estimate=width_estimate,
            sampling_limits=sampling_limits,
            review_positions=review_positions,
        )
        if candidate
        and candidate.display_frame
        and {"fixed_n_frame@1", "fixed_n_frame@2"}.intersection(detection.flags)
        else None,
        geometry_policy="source_prominent_band_geometry@1"
        if detection.algorithm_id == "source_prominent_band_geometry@1"
        else "guided_prominent_band_geometry@1"
        if detection.algorithm_id == "guided_prominent_band_geometry@1"
        else "source_common_band_geometry@1"
        if detection.algorithm_id == "source_common_band_geometry@1"
        else "guided_common_band_geometry@1"
        if detection.algorithm_id == "guided_common_band_geometry@1"
        else "source_signal_geometry@2"
        if detection.algorithm_id == "source_signal_geometry@2"
        else "instrument_guided_geometry@2"
        if detection.algorithm_id == "instrument_guided_geometry@2"
        else "source_signal_geometry@1"
        if detection.algorithm_id == "source_signal_geometry@1"
        else (
            "instrument_guided_geometry@1"
            if detection.algorithm_id == "instrument_guided_geometry@1"
            else "source_geometry@2"
        ),
        selected_index=0 if located else None,
        crop=replace(candidate.roi, lane_id=row_id) if located and candidate else None,
        slots=slots,
        reason="已保留定位范围；请处理独立校验未通过的原因：" + ";".join(detection.flags)
        if located and "independent_validation_failed" in detection.flags
        else "定位已就绪"
        if located
        and detection.algorithm_id
        in {
            "source_signal_geometry@1",
            "instrument_guided_geometry@1",
            "source_signal_geometry@2",
            "instrument_guided_geometry@2",
            "source_common_band_geometry@1",
            "guided_common_band_geometry@1",
            "source_prominent_band_geometry@1",
            "guided_prominent_band_geometry@1",
        }
        else "请核对裁剪范围"
        if located
        else "未取得完整固定N几何：" + ";".join(detection.flags),
    )


def review_intake_crop(
    project: WBIntakeCropProject,
    row_id: str,
    crop: LaneROI,
    *,
    expected_digest: str,
    display_angle: float | None = None,
) -> WBIntakeCropProject:
    """Explicitly confirm an original rectangle, then require a fresh owned crop attempt."""
    if project.workflow.editing:
        raise ValueError("分组编辑中不能同时修正裁剪")
    if expected_digest != intake_workflow_digest(project):
        raise ValueError("裁剪草稿已变化，请重新核对")
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or row.source is None or crop.lane_id != row_id:
        raise ValueError("裁剪行或来源不一致")
    previous = next((e for e in project.intake_crops if e.row_id == row_id), None)
    if previous is None:
        raise ValueError("请先取得该行定位状态，不能跳过失败/复核记录")
    display_only = display_angle is not None and crop == previous.crop and previous.geometry_ready
    step = next(s for s in project.workflow.steps if s.stage == "crop" and s.target_id == row_id)
    if step.status == "pending" and (
        display_only
        or (
            previous.reviewed
            and (previous.raw_crop is None or previous.policy == "intake_crop_display_review@1")
        )
    ):
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
    if display_only:
        # The original source-axis lane targets and background limits are part
        # of the quantitative input. A display edit must not replace them with
        # an equal-width grid or erase their original provenance/raw pixels.
        evidence = IntakeCropEvidence.model_validate(
            {
                **dict(previous),
                "policy": "intake_crop_display_review@1",
                "reviewed": True,
                "reason": "人工调整显示角度；原图范围、泳道及背景采样几何保持不变",
            }
        )
    else:
        identities = planned_intake_slots(project.project_id, row_id, row.lane_count)
        geometry = fixed_lane_grid(crop, row.lane_count)
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
    # An explicit angle edits display sampling only. New geometry drops stale
    # orientation; a same-geometry confirmation can retain its detected frame.
    existing = next((s.display_frame for s in reset.composition.slices if s.row_id == row_id), None)
    frame = existing if crop == previous.crop else None
    if display_angle is not None:
        from wb_tool.application.laboratory_layout import DisplayFrame

        if not isfinite(display_angle) or abs(display_angle) > 30:
            raise ValueError("显示纠偏角度须为 -30 至 30 度")
        # Rotation changes display sampling only. Keep a detected local frame's
        # dimensions when its original ROI is unchanged; never shrink silently.
        frame = DisplayFrame(
            sampling_policy="within_source@2",
            center_x=frame.center_x if frame else (crop.x0 + crop.x1) / 2,
            center_y=frame.center_y if frame else (crop.y0 + crop.y1) / 2,
            width=frame.width if frame else crop.width,
            height=frame.height if frame else crop.y1 - crop.y0,
            angle_degrees=display_angle,
        )
        if any(
            not (-1e-7 <= x <= row.width + 1e-7 and -1e-7 <= y <= row.height + 1e-7)
            for x, y in frame.corners()
        ):
            raise ValueError("旋转显示框超出原图，请移动或缩小范围")
    return type(project).model_validate(
        {
            **dict(reset),
            "rows": tuple(
                r.model_copy(update={"roi": crop, "reviewed": True}) if r.row_id == row_id else r
                for r in reset.rows
            ),
            "intake_crops": (*[e for e in project.intake_crops if e.row_id != row_id], evidence),
            "composition": reset.composition.model_copy(
                update={
                    "slices": tuple(
                        segment.model_copy(update={"display_frame": frame})
                        if segment.row_id == row_id
                        else segment
                        for segment in reset.composition.slices
                    )
                }
            ),
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


def accept_automatic_intake_crop(
    project: WBIntakeCropProject, ticket: IntakeWorkflowTicket, evidence: IntakeCropEvidence
) -> WBIntakeCropProject:
    """Retire detection's ticket, then freeze accepted geometry for a fresh export claim."""
    from wb_tool.application.intake_workflow import approve_intake_workflow
    from wb_tool.application.laboratory_layout import DisplayFrame

    if project.workflow.policy not in {
        "intake_workflow@3",
        "intake_workflow@4",
        "intake_workflow@5",
    } or not (automatic_intake_crop_allowed(evidence)):
        raise ValueError("自动定位仍需明确范围")
    calibration = evidence.fixed_grid.calibration if evidence.fixed_grid else None
    if calibration is not None and not any(
        old.reviewed
        and old.source_sha256 == calibration.source_sha256
        and old.source_revision == calibration.source_revision
        and old.lane_count == calibration.lane_count
        and old.crop == calibration.roi
        for old in project.intake_crops
    ):
        raise ValueError("槽宽校准缺少当前项目中明确审核的原图依据")
    recorded = record_intake_crop_proposal(project, ticket, evidence)
    if recorded.workflow.cancel_requested:
        return recorded
    reset = retry_intake_workflow_step(
        recorded, "crop", evidence.row_id, expected_digest=intake_workflow_digest(recorded)
    )
    accepted = IntakeCropEvidence.model_validate(
        {
            **dict(evidence),
            "policy": "intake_crop@5"
            if evidence.geometry_policy in PROMINENT_GEOMETRY
            else "intake_crop@4"
            if evidence.geometry_policy in COMMON_GEOMETRY
            else "intake_crop@3"
            if evidence.geometry_policy.endswith("@2")
            else "intake_crop@2",
            "reason": "已自动采纳完整定位",
        }
    )
    assert evidence.detection is not None
    frame = evidence.detection.candidates[0].display_frame
    assert frame is not None
    display = DisplayFrame(
        center_x=frame.center_x,
        center_y=frame.center_y,
        width=frame.width,
        height=frame.height,
        angle_degrees=frame.angle_degrees,
    )
    updated = type(project).model_validate(
        {
            **dict(reset),
            "rows": tuple(
                row.model_copy(update={"roi": evidence.crop, "reviewed": False})
                if row.row_id == evidence.row_id
                else row
                for row in reset.rows
            ),
            "intake_crops": tuple(
                accepted if item.row_id == evidence.row_id else item
                for item in recorded.intake_crops
            ),
            "composition": reset.composition.model_copy(
                update={
                    "slices": tuple(
                        segment.model_copy(update={"display_frame": display})
                        if segment.row_id == evidence.row_id
                        and segment.first_lane == 1
                        and segment.last_lane == evidence.lane_count
                        else segment
                        for segment in reset.composition.slices
                    )
                }
            ),
        }
    )
    approved = approve_intake_workflow(updated, expected_digest=intake_workflow_digest(updated))
    return type(project).model_validate(dict(approved))


def complete_intake_crop(
    project: WBIntakeCropProject, ticket: IntakeWorkflowTicket, raw_crop: AssetRef
) -> WBIntakeCropProject:
    evidence = next((e for e in project.intake_crops if e.row_id == ticket.target_id), None)
    if ticket.stage != "crop" or evidence is None or not evidence.geometry_ready:
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
