"""Versioned intake stage ledger; quantitative truth remains in existing run evidence."""

import json
from hashlib import sha256
from typing import Literal, cast

from pydantic import (
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from wb_tool.application.document import DocumentIO
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.instrument_intake import (
    WBIntakeProject,
    intake_computation_manifest,
    intake_digest,
    intake_project_rows,
    validate_intake_complete,
)
from wb_tool.application.intake_execution import build_intake_execution_plan

Stage = Literal["crop", "compose", "measure", "export"]
StepStatus = Literal[
    "pending", "running", "done", "needs_review", "failed", "cancelled", "interrupted"
]
StepOutcome = Literal["done", "needs_review", "failed", "cancelled"]


def _hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


class IntakeWorkflowStep(DocumentIO):
    model_config = ConfigDict(revalidate_instances="always")

    stage: Stage
    target_id: str = Field(min_length=1, max_length=80)
    status: StepStatus = "pending"
    attempt: int = Field(default=0, ge=0)
    claim_id: str = Field(default="", pattern="^(?:[0-9a-f]{64})?$")
    input_digest: str = Field(default="", pattern="^(?:[0-9a-f]{64})?$")
    reason: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def valid_status(self) -> "IntakeWorkflowStep":
        if self.status != "pending" and (
            self.attempt < 1 or not self.claim_id or not self.input_digest
        ):
            raise ValueError("非待处理阶段必须有实际尝试身份")
        if (
            self.status in {"needs_review", "failed", "cancelled", "interrupted"}
            and not self.reason
        ):
            raise ValueError("异常或取消阶段必须保留原因")
        return self


class IntakeWorkflowLedger(DocumentIO):
    model_config = ConfigDict(revalidate_instances="always")

    policy: Literal[
        "intake_workflow@1",
        "intake_workflow@2",
        "intake_workflow@3",
        "intake_workflow@4",
        "intake_workflow@5",
    ] = "intake_workflow@1"
    editing: bool = False
    intake_digest: str = Field(pattern="^[0-9a-f]{64}$")
    approved: bool = False
    cancel_requested: bool = False
    steps: tuple[IntakeWorkflowStep, ...] = Field(max_length=1537)

    @model_serializer(mode="wrap")
    def serialize_ledger(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        fields = cast(dict[str, object], handler(self))
        if self.policy == "intake_workflow@1":
            fields.pop("editing", None)
        return fields

    @model_validator(mode="after")
    def editing_is_explicit(self) -> "IntakeWorkflowLedger":
        if self.editing and (
            self.policy
            not in {
                "intake_workflow@2",
                "intake_workflow@3",
                "intake_workflow@4",
                "intake_workflow@5",
            }
            or self.approved
            or any(s.status == "running" for s in self.steps)
        ):
            raise ValueError("分组编辑必须使用版本2且不可同时确认或运行")
        return self


class IntakeWorkflowTicket(DocumentIO):
    project_id: str
    intake_digest: str
    stage: Stage
    target_id: str
    attempt: int
    claim_id: str
    input_digest: str


def _addresses(project: WBIntakeProject) -> tuple[tuple[Stage, str], ...]:
    crops: tuple[tuple[Stage, str], ...] = tuple(("crop", row.row_id) for row in project.rows)
    figures: tuple[tuple[Stage, str], ...] = tuple(
        (stage, fig.figure_id) for fig in project.intake.figures for stage in ("compose", "measure")
    )
    return (*crops, *figures, ("export", project.project_id))


class WBIntakeWorkflowProject(WBIntakeProject):
    schema_version: int = Field(default=11, ge=11, le=11)
    workflow: IntakeWorkflowLedger

    @model_validator(mode="after")
    def intake_projection(self) -> "WBIntakeWorkflowProject":
        # Override schema10's no-processing validator while retaining its identity projection.
        digest = intake_digest(self)
        if not self.workflow.editing:
            validate_intake_complete(self.intake)
        if self.workflow.intake_digest != digest or (
            not self.workflow.editing and self.intake.confirmed_digest != digest
        ):
            raise ValueError("执行快照必须绑定当前已确认清单；修改清单须创建新执行计划")
        expected = intake_project_rows(self.intake)
        mutable = {"roi", "reviewed", "empty_lanes", "notes"}
        if len(self.rows) != len(expected) or any(
            row.model_dump(exclude=mutable) != base.model_dump(exclude=mutable)
            for row, base in zip(self.rows, expected, strict=True)
        ):
            raise ValueError("执行行身份、名称、N或来源偏离已确认清单")
        if self.figure_order != tuple(dict.fromkeys(row.figure for row in expected)):
            raise ValueError("执行Fig顺序偏离已确认清单")
        if tuple((s.stage, s.target_id) for s in self.workflow.steps) != _addresses(self):
            raise ValueError("执行阶段必须完整对应清单，不能丢行或重复阶段")
        active = [s for s in self.workflow.steps if s.status == "running"]
        if len(active) > 1 or (active and not self.workflow.approved):
            raise ValueError("只允许一个已确认执行的活动阶段")
        statuses: dict[tuple[Stage, str], StepStatus] = {
            (s.stage, s.target_id): s.status for s in self.workflow.steps
        }
        for step in self.workflow.steps:
            if step.status == "running" and step.input_digest != _inputs_digest(self):
                raise ValueError("阶段输入已改变，不能接收旧执行回复")
            if step.status in {"running", "done"} and not _prerequisites(
                self, step, statuses, batch=step.status == "running"
            ):
                raise ValueError("执行阶段越过尚未就绪的裁剪、拼图或定量依赖")
        return self


def _prerequisites(
    project: WBIntakeWorkflowProject,
    step: IntakeWorkflowStep,
    statuses: dict[tuple[Stage, str], StepStatus],
    *,
    batch: bool = True,
) -> bool:
    if (
        batch
        and project.workflow.policy == "intake_workflow@5"
        and step.stage != "crop"
        and not _all_crops_committed(project)
    ):
        return False
    if batch and project.workflow.policy == "intake_workflow@3":
        order = {"crop": 0, "compose": 1, "measure": 2, "export": 3}
        if any(
            s.status != "done" and order[s.stage] < order[step.stage]
            for s in project.workflow.steps
        ):
            return False
    if step.stage == "crop":
        return True
    if step.stage == "compose":
        rows = [p for p in project.intake.proteins if p.figure_id == step.target_id]
        return bool(rows) and all(statuses["crop", row.protein_id] == "done" for row in rows)
    if step.stage == "measure":
        return statuses["compose", step.target_id] == "done"
    if batch and project.workflow.policy == "intake_workflow@4":
        # Publish an honest partial snapshot after every currently runnable group
        # has drained. A blocked Fig never suppresses another Fig's valid work.
        return not any(
            s.stage != "export"
            and (
                s.status == "running"
                or (s.status == "pending" and _prerequisites(project, s, statuses, batch=False))
            )
            for s in project.workflow.steps
        )
    return all(statuses["measure", f.figure_id] == "done" for f in project.intake.figures)


def _all_crops_committed(project: WBIntakeWorkflowProject) -> bool:
    # Import locally: crop evidence extends this ledger's schema. A done ledger
    # entry alone must never authorize downstream work without the saved asset.
    from wb_tool.application.intake_crop import WBIntakeCropProject

    if not isinstance(project, WBIntakeCropProject):
        return False
    crops = {e.row_id: e for e in project.intake_crops}
    steps = {(s.stage, s.target_id): s.status for s in project.workflow.steps}
    return bool(project.rows) and all(
        steps["crop", row.row_id] == "done"
        and (evidence := crops.get(row.row_id)) is not None
        and evidence.geometry_ready
        and evidence.raw_crop is not None
        and row.source is not None
        and evidence.source_sha256 == row.source.sha256
        and evidence.crop == row.roi
        for row in project.rows
    )


def adopt_intake_crop_barrier(
    project: WBIntakeWorkflowProject, *, expected_digest: str
) -> WBIntakeWorkflowProject:
    """Explicit continuation revision; reopening never rewrites legacy policy/history."""
    if expected_digest != intake_workflow_digest(project):
        raise ValueError("阶段输入已变化，请重新核对")
    if project.workflow.editing or any(s.status == "running" for s in project.workflow.steps):
        raise ValueError("请等待当前阶段退出并确认清单后采用整批裁剪规则")
    if project.workflow.policy != "intake_workflow@4" or all(
        s.status == "done" for s in project.workflow.steps
    ):
        return project
    return _replace_ledger(project, policy="intake_workflow@5", approved=False)


def require_intake_crop_barrier(project: WBIntakeWorkflowProject) -> None:
    """Check the v5 publication barrier before any new file or directory is created."""
    if project.workflow.policy == "intake_workflow@5":
        type(project).model_validate(dict(project))
        if not _all_crops_committed(project):
            raise ValueError("本批仍有未完成的原值裁剪，请先完成全部裁剪再输出")


def _replace_ledger(project: WBIntakeWorkflowProject, **changes: object) -> WBIntakeWorkflowProject:
    ledger = IntakeWorkflowLedger.model_validate({**dict(project.workflow), **changes})
    return type(project).model_validate({**dict(project), "workflow": ledger})


def prepare_intake_workflow(
    project: WBFigureProject,
    *,
    expected_digest: str,
    batch_stages: bool = False,
) -> WBIntakeWorkflowProject:
    plan = build_intake_execution_plan(project, expected_digest=expected_digest)
    if isinstance(project, WBIntakeWorkflowProject):
        return type(project).model_validate(dict(project))
    if not isinstance(project, WBIntakeProject):
        raise ValueError("执行计划需要仪器清单")
    return WBIntakeWorkflowProject.model_validate(
        {
            **dict(project),
            "schema_version": 11,
            "workflow": IntakeWorkflowLedger(
                policy="intake_workflow@5" if batch_stages else "intake_workflow@1",
                intake_digest=plan.intake_digest,
                steps=tuple(
                    IntakeWorkflowStep(stage=s, target_id=t) for s, t in _addresses(project)
                ),
            ),
        }
    )


def _inputs_digest(project: WBIntakeWorkflowProject) -> str:
    # Saving changes revision only. Executor outputs must be merged after finishing
    # the owned ticket against these frozen inputs, never into a running snapshot.
    fields = project.model_dump(mode="json", exclude={"workflow", "revision"})
    fields["intake"] = intake_computation_manifest(fields["intake"])
    return _hash(fields)


def intake_workflow_digest(project: WBIntakeWorkflowProject) -> str:
    type(project).model_validate(dict(project))
    return _hash((_inputs_digest(project), project.workflow.model_dump(mode="json")))


def approve_intake_workflow(
    project: WBIntakeWorkflowProject, *, expected_digest: str
) -> WBIntakeWorkflowProject:
    if project.workflow.editing:
        raise ValueError("请先保存并确认修改后的清单")
    if expected_digest != intake_workflow_digest(project):
        raise ValueError("执行摘要已变化，请重新核对")
    if any(s.status == "running" for s in project.workflow.steps):
        raise ValueError("阶段尚在运行，不能重新确认")
    return _replace_ledger(project, approved=True, cancel_requested=False)


def claim_intake_workflow_step(
    project: WBIntakeWorkflowProject, *, session_key: str, stage_filter: Stage | None = None
) -> tuple[WBIntakeWorkflowProject, IntakeWorkflowTicket | None]:
    type(project).model_validate(dict(project))
    if stage_filter not in {None, "crop", "compose", "measure", "export"}:
        raise ValueError("未知阶段过滤条件")
    if not session_key or len(session_key) > 160:
        raise ValueError("阶段执行需要明确会话身份")
    if not project.workflow.approved:
        raise ValueError("请先核对并确认执行摘要")
    if project.workflow.cancel_requested or any(
        s.status == "running" for s in project.workflow.steps
    ):
        return project, None
    if project.workflow.policy == "intake_workflow@3" and any(
        s.status in {"needs_review", "failed", "cancelled", "interrupted"}
        for s in project.workflow.steps
    ):
        return project, None
    statuses: dict[tuple[Stage, str], StepStatus] = {
        (s.stage, s.target_id): s.status for s in project.workflow.steps
    }
    pending = [
        s
        for s in project.workflow.steps
        if s.status == "pending"
        and (stage_filter is None or s.stage == stage_filter)
        and _prerequisites(project, s, statuses)
    ]
    if project.workflow.policy in {"intake_workflow@3", "intake_workflow@4", "intake_workflow@5"}:
        order = {"crop": 0, "compose": 1, "measure": 2, "export": 3}
        pending.sort(key=lambda s: order[s.stage])
    else:
        # Preserve the original ready-Fig priority for existing ledgers.
        pending.sort(key=lambda s: s.stage == "crop")
    if not pending:
        return project, None
    step = pending[0]
    input_digest = _inputs_digest(project)
    claim_id = _hash((session_key, input_digest, step.stage, step.target_id, step.attempt + 1))
    active = step.model_copy(
        update={
            "status": "running",
            "attempt": step.attempt + 1,
            "claim_id": claim_id,
            "input_digest": input_digest,
            "reason": "",
        }
    )
    updated = _replace_ledger(
        project, steps=tuple(active if s == step else s for s in project.workflow.steps)
    )
    return updated, IntakeWorkflowTicket(
        project_id=project.project_id,
        intake_digest=project.workflow.intake_digest,
        stage=step.stage,
        target_id=step.target_id,
        attempt=active.attempt,
        claim_id=claim_id,
        input_digest=input_digest,
    )


def request_intake_workflow_cancel(project: WBIntakeWorkflowProject) -> WBIntakeWorkflowProject:
    """Record intent; only a later owned executor callback can finish the running step."""
    return _replace_ledger(project, cancel_requested=True)


def finish_intake_workflow_step(
    project: WBIntakeWorkflowProject,
    ticket: IntakeWorkflowTicket,
    outcome: StepOutcome,
    *,
    reason: str = "",
) -> WBIntakeWorkflowProject:
    return _replace_ledger(
        project, steps=completed_intake_steps(project, ticket, outcome, reason=reason)
    )


def completed_intake_steps(
    project: WBIntakeWorkflowProject,
    ticket: IntakeWorkflowTicket,
    outcome: StepOutcome,
    *,
    reason: str = "",
) -> tuple[IntakeWorkflowStep, ...]:
    """Validate frozen inputs before atomically merging a terminal state and its outputs."""
    if outcome not in {"done", "needs_review", "failed", "cancelled"}:
        raise ValueError("执行器只能返回明确阶段终态")
    active = validate_intake_workflow_ticket(project, ticket)
    if project.workflow.cancel_requested:
        outcome, reason = "cancelled", "取消已由执行器确认；已完成结果保留"
    finished = IntakeWorkflowStep.model_validate(
        {**dict(active), "status": outcome, "reason": reason}
    )
    return tuple(finished if s == active else s for s in project.workflow.steps)


def validate_intake_workflow_ticket(
    project: WBIntakeWorkflowProject, ticket: IntakeWorkflowTicket
) -> IntakeWorkflowStep:
    """Verify ownership before a side effect as well as when accepting its reply."""
    type(project).model_validate(dict(project))
    active = next((s for s in project.workflow.steps if s.status == "running"), None)
    if (
        active is None
        or ticket.project_id != project.project_id
        or ticket.intake_digest != project.workflow.intake_digest
        or ticket.input_digest != _inputs_digest(project)
        or (ticket.stage, ticket.target_id, ticket.attempt, ticket.claim_id)
        != (active.stage, active.target_id, active.attempt, active.claim_id)
    ):
        raise ValueError("阶段回复已过期或身份不一致")
    return active


def recover_intake_workflow(project: WBIntakeWorkflowProject) -> WBIntakeWorkflowProject:
    steps = tuple(
        s.model_copy(update={"status": "interrupted", "reason": "上次执行未完整提交，请核对后重试"})
        if s.status == "running"
        else s
        for s in project.workflow.steps
    )
    return _replace_ledger(project, steps=steps, approved=False, cancel_requested=False)


def retry_intake_workflow_step(
    project: WBIntakeWorkflowProject, stage: Stage, target_id: str, *, expected_digest: str
) -> WBIntakeWorkflowProject:
    if expected_digest != intake_workflow_digest(project):
        raise ValueError("异常清单已变化，请刷新后重试")
    if any(s.status == "running" for s in project.workflow.steps):
        raise ValueError("请等待当前阶段退出后再重试")
    selected = next(
        (s for s in project.workflow.steps if (s.stage, s.target_id) == (stage, target_id)), None
    )
    if selected is None or selected.status not in {
        "failed",
        "needs_review",
        "cancelled",
        "interrupted",
    }:
        raise ValueError("只能重试明确未完成的阶段")
    figures = {p.protein_id: p.figure_id for p in project.intake.proteins}
    affected_fig = figures[target_id] if stage == "crop" else target_id
    reset = {(stage, target_id), ("export", project.project_id)}
    if stage == "crop":
        reset.update({("compose", affected_fig), ("measure", affected_fig)})
    elif stage == "compose":
        reset.add(("measure", affected_fig))
    steps = tuple(
        s.model_copy(update={"status": "pending", "reason": ""})
        if (s.stage, s.target_id) in reset
        else s
        for s in project.workflow.steps
    )
    return _replace_ledger(project, steps=steps, approved=False, cancel_requested=False)


def intake_workflow_snapshot(project: WBIntakeWorkflowProject) -> dict[str, object]:
    from wb_tool.application.intake_output import WBIntakeOutputProject

    return {
        **project.workflow.model_dump(mode="json"),
        "digest": intake_workflow_digest(project),
        "stages_finished": all(s.status == "done" for s in project.workflow.steps),
        "ready_count": sum(s.status == "done" for s in project.workflow.steps),
        "crop_barrier_ready": _all_crops_committed(project),
        "pending_ready": 0
        if project.workflow.editing
        or (
            project.workflow.policy == "intake_workflow@3"
            and any(
                s.status in {"needs_review", "failed", "cancelled", "interrupted"}
                for s in project.workflow.steps
            )
        )
        else sum(
            s.status == "pending"
            and (s.stage != "export" or isinstance(project, WBIntakeOutputProject))
            and _prerequisites(
                project, s, {(p.stage, p.target_id): p.status for p in project.workflow.steps}
            )
            for s in project.workflow.steps
        ),
    }


def return_to_intake_editing(project: WBIntakeWorkflowProject) -> WBIntakeProject:
    """Undo only an unused preparation; executed revisions require a new execution snapshot."""
    type(project).model_validate(dict(project))
    if any(s.attempt for s in project.workflow.steps):
        raise ValueError("已有执行尝试；请保留当前修订，不可删除阶段历史")
    fields = dict(project)
    fields.pop("workflow")
    fields.pop("intake_crops", None)
    fields.pop("intake_figures", None)
    fields.pop("intake_outputs", None)
    fields["schema_version"] = 10
    return WBIntakeProject.model_validate(fields)
