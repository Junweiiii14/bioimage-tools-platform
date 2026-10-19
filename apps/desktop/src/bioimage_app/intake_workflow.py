"""Serial intake stages: immutable claims, tool jobs, asset import, then CAS installation."""

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from typing import TYPE_CHECKING
from uuid import uuid4

from tool_contracts.api import AssetRef
from wb_tool.api import (
    IntakeCropEvidence,
    IntakeCropFile,
    IntakeWorkflowTicket,
    WBFigureProject,
    WBIntakeCropProject,
    WBIntakeWorkflowProject,
    WBJob,
    WBReply,
    claim_intake_workflow_step,
    complete_intake_crop,
    fail_intake_crop,
    intake_workflow_digest,
    record_intake_crop_proposal,
    request_intake_workflow_cancel,
)

from bioimage_app.storage import StorageCommand, StorageReply

if TYPE_CHECKING:
    from bioimage_app.figure_window import FigureProjectWindow


class IntakeWorkflowSession:
    def __init__(self, host: "FigureProjectWindow") -> None:
        self.host = host
        self._key = ""
        self._cancelled = False
        self._temporary: TemporaryDirectory[str] | None = None
        self._temporary_root: Path | None = None

    def cancel(self) -> None:
        self._cancelled = True

    def start(self, expected_digest: str) -> None:
        host = self.host
        if host.operation_busy or host.is_closing:
            return
        project = host.view.project()
        if not isinstance(project, WBIntakeWorkflowProject):
            raise ValueError("请先准备并核对执行计划")
        if expected_digest != intake_workflow_digest(project):
            raise ValueError("执行摘要已改变，请刷新后重试")
        self._key, self._cancelled = uuid4().hex, False
        key, generation = self._key, host.view.generation
        host.begin_operation()

        def prepared(reply: WBReply) -> None:
            if self._obsolete(key, generation) or self._cancelled:
                host.finish_operation("裁剪准备已停止，当前草稿保留。")
            elif reply.error or not isinstance(reply.value, WBIntakeCropProject):
                host.fail_operation(reply.error or "裁剪执行快照无效")
            else:
                self._persist(reply.value, self._advance)

        host.submit_tool_job(
            WBJob(
                "intake_crop_prepare",
                document=project,
                data=expected_digest.encode("ascii"),
                cancellation=host.cancellation,
            ),
            prepared,
            accept_errors=True,
        )

    def _obsolete(self, key: str, generation: int) -> bool:
        return key != self._key or self.host.is_closing or self.host.view.generation != generation

    def _persist(
        self,
        updated: WBIntakeCropProject,
        after: Callable[[], None],
        *,
        terminal_cancel: bool = False,
    ) -> None:
        host = self.host
        current = host.view.project()
        if not isinstance(current, WBIntakeWorkflowProject):
            host.fail_operation("当前项目已切换，拒绝旧阶段回复")
            return
        digest, generation, key = intake_workflow_digest(current), host.view.generation, self._key
        host.end_phase()

        def install(saved: WBFigureProject) -> WBIntakeCropProject:
            if (
                not isinstance(saved, WBIntakeWorkflowProject)
                or intake_workflow_digest(saved) != digest
            ):
                raise ValueError("阶段输入已变化，旧回复不能覆盖草稿")
            return WBIntakeCropProject.model_validate({**dict(updated), "revision": saved.revision})

        host.save(
            after=after,
            transform=install,
            install_guard=lambda: (
                not self._obsolete(key, generation) and (terminal_cancel or not self._cancelled)
            ),
        )

    def _advance(self) -> None:
        host = self.host
        if self._cancelled or host.is_closing:
            host.finish_operation("已停止，已提交的裁剪与待处理槽位保留。")
            return
        project = host.view.project()
        if not isinstance(project, WBIntakeCropProject):
            host.fail_operation("缺少当前固定N裁剪项目")
            return
        try:
            active, ticket = claim_intake_workflow_step(
                project, session_key=self._key, stage_filter="crop"
            )
            if not isinstance(active, WBIntakeCropProject):
                raise ValueError("裁剪阶段返回无效快照")
            if ticket is None:
                pending = sum(
                    s.stage == "crop" and s.status != "done" for s in project.workflow.steps
                )
                host.finish_operation(
                    f"定位已保存；{pending} 行待复核或重试，原值裁剪完成后进入完整Fig拼图。"
                    if pending
                    else "原值裁剪已保存，等待完整Fig拼图；尚未生成定量结果。"
                )
                return
            self._persist(active, lambda: self._execute(ticket))
        except ValueError as error:
            host.fail_operation(str(error))

    def _execute(self, ticket: IntakeWorkflowTicket) -> None:
        host = self.host
        project = host.view.project()
        if not isinstance(project, WBIntakeCropProject) or self._cancelled or host.is_closing:
            host.finish_operation("裁剪已停止，阶段记录保留。")
            return
        generation, key = host.view.generation, self._key
        published: IntakeCropFile | None = None
        row = next(r for r in project.rows if r.row_id == ticket.target_id)
        if row.source is None:
            host.fail_operation("已分配行缺少原图资产")
            return
        host.begin_operation()
        host.view.status.setText(f"处理原图：{row.figure} / {row.protein}")

        def resolved(reply: StorageReply) -> None:
            if self._obsolete(key, generation):
                host.finish_operation("当前裁剪已停止，旧回复未安装。")
                return
            if reply.error_code or not isinstance(reply.value, str):
                self._finish(ticket, error=reply.message or "原图资产无法解析")
                return
            evidence = next((e for e in project.intake_crops if e.row_id == row.row_id), None)
            if evidence is not None and evidence.reviewed:
                try:
                    self._temporary = TemporaryDirectory(prefix="bioimage-intake-crop-")
                    self._temporary_root = Path(self._temporary.name).resolve()
                except OSError as error:
                    self._finish(ticket, error=str(error))
                    return
                job = WBJob(
                    "intake_crop_export",
                    path=reply.value,
                    document=project,
                    row_id=row.row_id,
                    data=ticket.model_dump_json().encode(),
                    cancellation=host.cancellation,
                    destination=str(self._temporary_root / "raw-crop.tiff"),
                )
            else:
                job = WBJob(
                    "intake_crop_propose",
                    path=reply.value,
                    document=project,
                    row_id=row.row_id,
                    cancellation=host.cancellation,
                )

            def completed(result: WBReply) -> None:
                nonlocal published
                if self._obsolete(key, generation):
                    if not self._cleanup():
                        return
                    host.finish_operation("当前裁剪已停止，旧回复未安装。")
                elif result.error:
                    if not self._cleanup():
                        return
                    self._finish(ticket, error=result.error)
                elif isinstance(result.value, IntakeCropEvidence):
                    self._finish(ticket, evidence=result.value)
                elif isinstance(result.value, IntakeCropFile) and self._temporary is not None:
                    if (
                        self._temporary_root is None
                        or Path(result.value.path) != self._temporary_root / "raw-crop.tiff"
                    ):
                        if self._cleanup():
                            self._finish(ticket, error="裁剪产物路径不属于当前尝试")
                        return
                    published = result.value
                    host.submit_storage_job(
                        StorageCommand(
                            "import", path=result.value.path, source_sha256=result.value.sha256
                        ),
                        imported,
                        accept_errors=True,
                    )
                else:
                    if not self._cleanup():
                        return
                    self._finish(ticket, error="裁剪执行器返回无效产物")

            host.submit_tool_job(job, completed, accept_errors=True)

        def imported(reply: StorageReply) -> None:
            if not self._cleanup():
                return
            if self._obsolete(key, generation):
                host.finish_operation("裁剪资产历史保留，旧回复未安装。")
            elif reply.error_code or not isinstance(reply.value, AssetRef):
                self._finish(ticket, error=reply.message or "原值裁剪资产导入失败")
            elif published is None or (reply.value.sha256, reply.value.size_bytes) != (
                published.sha256,
                published.size_bytes,
            ):
                self._finish(ticket, error="导入资产与当前裁剪产物摘要或字节数不一致")
            else:
                self._finish(ticket, asset=reply.value)

        host.submit_storage_job(
            StorageCommand("asset", asset=row.source), resolved, accept_errors=True
        )

    def _finish(
        self,
        ticket: IntakeWorkflowTicket,
        *,
        evidence: IntakeCropEvidence | None = None,
        asset: AssetRef | None = None,
        error: str = "",
    ) -> None:
        host = self.host
        project = host.view.project()
        if not isinstance(project, WBIntakeCropProject):
            host.fail_operation("裁剪项目已改变")
            return
        try:
            cancelled = self._cancelled or host.cancellation.is_set()
            if cancelled:
                marked = request_intake_workflow_cancel(project)
                if not isinstance(marked, WBIntakeCropProject):
                    raise ValueError("取消阶段项目类型无效")
                project = marked
            if error or cancelled:
                updated = fail_intake_crop(project, ticket, (error or "用户取消裁剪")[:2000])
            elif evidence is not None:
                updated = record_intake_crop_proposal(project, ticket, evidence)
            elif asset is not None:
                updated = complete_intake_crop(project, ticket, asset)
            else:
                raise ValueError("裁剪回复没有明确结果")
            self._persist(updated, self._advance, terminal_cancel=cancelled)
        except ValueError as problem:
            host.fail_operation(str(problem))

    def _cleanup(self) -> bool:
        try:
            if self._temporary is not None:
                path = Path(self._temporary.name).resolve()
                if path != self._temporary_root or path.parent != Path(gettempdir()).resolve():
                    raise ValueError("临时裁剪路径改变，拒绝清理")
                self._temporary.cleanup()
                self._temporary = None
                self._temporary_root = None
            return True
        except (OSError, ValueError) as error:
            self.host.fail_operation("临时裁剪清理未完成，保留阶段记录：" + str(error))
            return False
