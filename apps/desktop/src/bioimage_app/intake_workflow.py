"""Serial intake stages: immutable claims, tool jobs, asset import, then CAS installation."""

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from typing import TYPE_CHECKING
from uuid import uuid4

from tool_contracts.api import AssetRef
from wb_tool.api import (
    FigureRender,
    FigureSourcePath,
    IntakeCropEvidence,
    IntakeCropFile,
    IntakeFigurePreparation,
    IntakeWorkflowTicket,
    WBFigureProject,
    WBIntakeCropProject,
    WBIntakeFigureProject,
    WBIntakeWorkflowProject,
    WBJob,
    WBReply,
    claim_intake_workflow_step,
    complete_intake_crop,
    complete_intake_figure,
    complete_intake_measurement,
    fail_intake_crop,
    finish_intake_workflow_step,
    intake_workflow_digest,
    prepare_intake_measurement_revision,
    record_intake_crop_proposal,
    request_intake_workflow_cancel,
)

from bioimage_app.project_measurements import ProjectBatchCompletion
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

    def show_figure(self, figure_id: str, expected_digest: str) -> None:
        host = self.host
        project = host.view.project()
        if host.operation_busy or host.is_closing:
            return
        if not isinstance(
            project, WBIntakeFigureProject
        ) or expected_digest != intake_workflow_digest(project):
            raise ValueError("Fig显示输入已变化，请重新选择")
        evidence = next((e for e in project.intake_figures if e.figure_id == figure_id), None)
        if evidence is None:
            raise ValueError("当前Fig尚无已保存成图")
        self._key, self._cancelled = uuid4().hex, False
        key, generation = self._key, host.view.generation
        host.view.clear_render()
        host.begin_operation()
        host.view.status.setText("正在读取已保存的完整Fig…")
        index = next(i for i, r in enumerate(project.rows) if r.row_id == evidence.row_ids[0])
        host.view.table.setCurrentCell(index, 0)

        def loaded(reply: StorageReply) -> None:
            if self._obsolete(key, generation) or self._cancelled:
                host.finish_operation("Fig显示已停止，已保存图像保持。")
            elif reply.error_code or not isinstance(reply.value, str):
                host.fail_operation(reply.message or "Fig图像不可读取")
            else:
                host.submit_tool_job(
                    WBJob(
                        "intake_figure_preview",
                        document=project,
                        row_id=figure_id,
                        path=reply.value,
                        cancellation=host.cancellation,
                    ),
                    shown,
                    accept_errors=True,
                )

        def shown(reply: WBReply) -> None:
            if self._obsolete(key, generation) or self._cancelled or host.cancellation.is_set():
                host.finish_operation("旧Fig显示回复未安装。")
            elif reply.error or not isinstance(reply.value, FigureRender):
                host.fail_operation(reply.error or "Fig显示图像无效")
            else:
                host.view.show_render(reply.value)
                host.finish_operation("显示已保存的完整Fig；点击图块回到对应原图。")

        host.submit_storage_job(
            StorageCommand("asset", asset=evidence.image), loaded, accept_errors=True
        )

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
            return type(updated).model_validate({**dict(updated), "revision": saved.revision})

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
            active, ticket = claim_intake_workflow_step(project, session_key=self._key)
            if not isinstance(active, WBIntakeCropProject):
                raise ValueError("裁剪阶段返回无效快照")
            if ticket is None:
                pending = sum(
                    s.stage != "export" and s.status != "done" for s in project.workflow.steps
                )
                host.finish_operation(
                    f"阶段已保存；{pending} 项待复核或重试，其他完整Fig结果保留。"
                    if pending
                    else "原值裁剪已保存，等待完整Fig拼图；尚未生成定量结果。"
                )
                return
            if ticket.stage == "export":
                host.finish_operation("完整Fig与原像素运行已保存，等待结果输出；原图和历史保持。")
                return
            if ticket.stage == "measure":
                if not isinstance(project, WBIntakeFigureProject):
                    raise ValueError("缺少完整Fig定量项目")
                revised = prepare_intake_measurement_revision(
                    project, ticket.target_id, project.revision + 1
                )
                active, ticket = claim_intake_workflow_step(revised, session_key=self._key)
                if ticket is None or ticket.stage != "measure":
                    raise ValueError("测量修订准备后阶段身份改变")
            if not isinstance(active, WBIntakeCropProject):
                raise ValueError("阶段项目类型无效")
            self._persist(active, lambda: self._execute(ticket))
        except ValueError as error:
            host.fail_operation(str(error))

    def _execute(self, ticket: IntakeWorkflowTicket) -> None:
        host = self.host
        project = host.view.project()
        if not isinstance(project, WBIntakeCropProject) or self._cancelled or host.is_closing:
            host.finish_operation("裁剪已停止，阶段记录保留。")
            return
        if ticket.stage == "compose":
            self._compose(ticket)
            return
        if ticket.stage == "measure":
            self._measure(ticket)
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

    def _failed_stage(self, ticket: IntakeWorkflowTicket, message: str) -> None:
        host = self.host
        project = host.view.project()
        if not isinstance(project, WBIntakeFigureProject):
            host.fail_operation(message)
            return
        try:
            if self._cancelled or host.cancellation.is_set():
                marked = request_intake_workflow_cancel(project)
                if not isinstance(marked, WBIntakeFigureProject):
                    raise ValueError("当前阶段类型改变")
                project = marked
                self._cancelled = True
            updated = finish_intake_workflow_step(project, ticket, "failed", reason=message[:2000])
            if not isinstance(updated, WBIntakeFigureProject):
                raise ValueError("阶段终态无效")
            self._persist(updated, self._advance, terminal_cancel=self._cancelled)
        except ValueError as error:
            host.fail_operation(str(error))

    def _compose(self, ticket: IntakeWorkflowTicket) -> None:
        host = self.host
        project = host.view.project()
        if not isinstance(project, WBIntakeFigureProject):
            host.fail_operation("缺少当前完整Fig项目")
            return
        generation, key = host.view.generation, self._key
        rows = {r.row_id: r for r in project.rows}
        ids = [p.protein_id for p in project.intake.proteins if p.figure_id == ticket.target_id]
        assets = [rows[row_id].source for row_id in ids]
        if project.template.font is not None:
            assets.append(project.template.font)
        pending = list({a.sha256: a for a in assets if a is not None}.values())
        sources: list[FigureSourcePath] = []
        published: IntakeFigurePreparation | None = None
        host.begin_operation()

        def next_source() -> None:
            if self._obsolete(key, generation):
                host.finish_operation("旧Fig阶段回复未安装，已提交历史保留。")
                return
            if self._cancelled or host.cancellation.is_set():
                self._failed_stage(ticket, "Fig成图已取消")
                return
            if pending:
                asset = pending.pop(0)

                def resolved(reply: StorageReply) -> None:
                    if self._obsolete(key, generation):
                        host.finish_operation("旧Fig来源回复未安装。")
                    elif reply.error_code or not isinstance(reply.value, str):
                        self._failed_stage(ticket, reply.message or "Fig原图无法解析")
                    else:
                        sources.append(FigureSourcePath(asset.sha256, reply.value))
                        next_source()

                host.submit_storage_job(
                    StorageCommand("asset", asset=asset), resolved, accept_errors=True
                )
                return
            try:
                self._temporary = TemporaryDirectory(prefix="bioimage-intake-fig-")
                self._temporary_root = Path(self._temporary.name).resolve()
            except OSError as error:
                self._failed_stage(ticket, str(error))
                return
            host.submit_tool_job(
                WBJob(
                    "intake_figure_prepare",
                    document=project,
                    data=ticket.model_dump_json().encode(),
                    sources=tuple(sources),
                    destination=str(self._temporary_root / "figure.png"),
                    cancellation=host.cancellation,
                ),
                rendered,
                accept_errors=True,
            )

        def rendered(reply: WBReply) -> None:
            nonlocal published
            if self._obsolete(key, generation):
                if self._cleanup():
                    host.finish_operation("旧Fig图像回复未安装，历史保留。")
            elif reply.error or not isinstance(reply.value, IntakeFigurePreparation):
                if self._cleanup():
                    self._failed_stage(ticket, reply.error or "Fig成图产物无效")
            elif (
                self._temporary_root is None
                or Path(reply.value.path) != self._temporary_root / "figure.png"
            ):
                if self._cleanup():
                    self._failed_stage(ticket, "Fig成图路径不属于当前尝试")
            else:
                published = reply.value
                host.submit_storage_job(
                    StorageCommand("import", path=published.path, source_sha256=published.sha256),
                    imported,
                    accept_errors=True,
                )

        def imported(reply: StorageReply) -> None:
            if not self._cleanup():
                return
            if self._obsolete(key, generation):
                host.finish_operation("旧Fig资产回复未安装，历史保留。")
                return
            if reply.error_code or not isinstance(reply.value, AssetRef) or published is None:
                self._failed_stage(ticket, reply.message or "Fig成图资产导入失败")
                return
            current = host.view.project()
            if not isinstance(current, WBIntakeFigureProject):
                host.fail_operation("Fig项目已改变")
                return
            try:
                if self._cancelled or host.cancellation.is_set():
                    marked = request_intake_workflow_cancel(current)
                    if not isinstance(marked, WBIntakeFigureProject):
                        raise ValueError("取消Fig类型无效")
                    current = marked
                    self._cancelled = True
                updated = complete_intake_figure(current, ticket, published, reply.value)
                self._persist(updated, self._advance, terminal_cancel=self._cancelled)
            except ValueError as error:
                self._failed_stage(ticket, str(error))

        next_source()

    def _measure(self, ticket: IntakeWorkflowTicket) -> None:
        host = self.host
        project = host.view.project()
        if not isinstance(project, WBIntakeFigureProject):
            host.fail_operation("缺少当前Fig测量项目")
            return
        generation, key = host.view.generation, self._key
        row_ids = tuple(
            p.protein_id for p in project.intake.proteins if p.figure_id == ticket.target_id
        )
        host.begin_operation()
        try:
            session = host.create_measurement_session()
        except ValueError as error:
            self._failed_stage(ticket, str(error))
            return

        def completed(completion: ProjectBatchCompletion) -> None:
            host.retire_measurement_session(session)
            if self._obsolete(key, generation):
                host.finish_operation("旧Fig运行保留在历史，未覆盖当前项目。")
                return
            current = host.view.project()
            if not isinstance(current, WBIntakeFigureProject):
                host.fail_operation("Fig测量项目已改变")
                return
            try:
                if self._cancelled or completion.cancelled or host.cancellation.is_set():
                    marked = request_intake_workflow_cancel(current)
                    if not isinstance(marked, WBIntakeFigureProject):
                        raise ValueError("取消Fig测量类型无效")
                    current = marked
                    self._cancelled = True
                updated = complete_intake_measurement(
                    current,
                    ticket,
                    completion.committed,
                    completion.results,
                    error="；".join(completion.errors)[:2000],
                )

                def saved() -> None:
                    host.retain_project_results(completion.results)
                    if self._cancelled:
                        host.finish_operation("Fig测量已取消，已提交行和原图历史保留。")
                    else:
                        host.refresh_project_table("Fig运行已核验并保存。", after=self._advance)

                self._persist(updated, saved, terminal_cancel=self._cancelled)
            except ValueError as error:
                self._failed_stage(ticket, str(error))

        session.finished.connect(completed)
        session.start(project, row_ids, host.workspace_path, defer_install=True)
        if self._cancelled or host.is_closing:
            session.cancel()

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
