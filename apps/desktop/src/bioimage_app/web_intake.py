"""Typed command boundary for the instrument planning page."""

import json
import math
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from wb_tool.api import (
    ExportSelection,
    IntakeAssignment,
    IntakeFigure,
    IntakeGrouping,
    IntakeProtein,
    LaneROI,
    WBFigureProject,
    WBIntakeCropProject,
    WBIntakeFigureProject,
    WBIntakeOutputProject,
    WBIntakeProject,
    WBIntakeWorkflowProject,
    WBJob,
    WBReply,
    accept_export_selections,
    adopt_intake_crop_barrier,
    assign_intake_sources,
    begin_intake_group_revision,
    confirm_intake,
    confirm_intake_group_revision,
    continue_intake_sequence,
    intake_digest,
    intake_workflow_digest,
    prepare_intake_sequence,
    replace_intake_plan,
    require_intake_crop_barrier,
    retry_intake_workflow_step,
    return_to_intake_editing,
    review_intake_crop,
    revise_completed_intake_crop,
    revise_intake_grouping,
    save_intake_grouping,
)

if TYPE_CHECKING:
    from bioimage_app.web_bridge import WorkbenchBridge


def _display_angle(data: dict[str, object]) -> float | None:
    value = data.get("displayAngle")
    if value is None:
        return None
    if type(value) not in (int, float) or not isinstance(value, (int, float)):
        raise ValueError("显示纠偏角度须为数值")
    angle = float(value)
    if not math.isfinite(angle) or abs(angle) > 30:
        raise ValueError("显示纠偏角度须为 -30 至 30 度")
    return angle


def apply_intake_command(bridge: "WorkbenchBridge", action: str, data: dict[str, object]) -> None:
    host = bridge.host
    project = host.view.project()
    digest = data.get("digest")
    if (
        not isinstance(project, WBIntakeProject)
        or data.get("projectId") != project.project_id
        or type(data.get("sessionEpoch")) is not int
        or data.get("sessionEpoch") != bridge.session_epoch
        or not isinstance(digest, str)
    ):
        raise ValueError("当前导入项目已改变，请刷新后重试")
    if (
        isinstance(project, WBIntakeWorkflowProject)
        and project.workflow.editing
        and action
        not in {
            "intake_grouping",
            "intake_confirm",
            "intake_preview",
            "intake_sequence_start",
            "intake_choose_output",
        }
    ):
        raise ValueError("分组编辑中请先保存并确认清单，再继续执行")
    if action == "intake_choose_output":
        from PySide6.QtWidgets import QFileDialog

        if intake_digest(project) != digest:
            raise ValueError("项目已变化，请刷新后选择输出位置")
        parent = QFileDialog.getExistingDirectory(
            host,
            "选择本次结果保存位置（自动创建独立子目录）",
            host.intake_workflow.output_parent(project),
        )
        if parent:
            if not Path(parent).is_dir():
                raise ValueError("输出位置不是可用文件夹")
            host.intake_workflow.choose_output_parent(project, parent)
        return
    if action == "intake_sequence_start":
        raw, request_id = data.get("grouping"), data.get("requestId")
        if (
            not isinstance(raw, dict)
            or not isinstance(request_id, str)
            or not request_id
            or len(request_id) > 80
            or type(data.get("allowReuse", False)) is not bool
        ):
            raise ValueError("请提交当前顺序配置和启动请求身份")
        grouping = IntakeGrouping.model_validate_json(json.dumps(raw, ensure_ascii=False))
        if isinstance(project, WBIntakeWorkflowProject) and not project.workflow.editing:
            raise ValueError("已有执行计划请继续处理；修改顺序须先进入分组修订")
        generation, epoch = host.view.generation, bridge.session_epoch
        bridge.sequence_response = {
            "projectId": project.project_id,
            "epoch": epoch,
            "requestId": request_id,
            "status": "pending",
        }

        def compile_sequence(current: WBFigureProject) -> WBIntakeWorkflowProject:
            if not isinstance(current, WBIntakeProject):
                raise ValueError("当前导入项目已变化")
            return prepare_intake_sequence(
                current,
                grouping,
                expected_digest=digest,
                allow_reuse=data.get("allowReuse", False) is True,
            )

        def started() -> None:
            current = host.view.project()
            if (
                not isinstance(current, WBIntakeWorkflowProject)
                or bridge.session_epoch != epoch
                or host.is_closing
                or host.cancellation.is_set()
            ):
                return
            bridge.sequence_response = {**bridge.sequence_response, "status": "started"}
            host.intake_workflow.start(intake_workflow_digest(current))

        host.save(
            transform=compile_sequence,
            after=started,
            install_guard=lambda: (
                not host.is_closing
                and not host.cancellation.is_set()
                and host.view.generation == generation
                and bridge.session_epoch == epoch
            ),
        )
        return
    if action == "intake_discover":
        host.intake.discover(digest)
        return
    if action == "intake_preview":
        source_id = data.get("sourceId")
        if not isinstance(source_id, str):
            raise ValueError("请选择原图来源")
        host.intake.preview_source(source_id, digest)
        return
    if action == "intake_grouping":
        if (
            not isinstance(data.get("grouping"), dict)
            or type(data.get("allowReuse", False)) is not bool
        ):
            raise ValueError("请提交当前采集组草稿与明确复用选择")
        grouping = IntakeGrouping.model_validate_json(
            json.dumps(data["grouping"], ensure_ascii=False)
        )
        generation, epoch = host.view.generation, bridge.session_epoch

        def grouped(current: WBFigureProject) -> WBIntakeProject:
            if not isinstance(current, WBIntakeProject):
                raise ValueError("当前导入项目已改变")
            if isinstance(current, WBIntakeWorkflowProject):
                return revise_intake_grouping(
                    current,
                    grouping,
                    expected_digest=digest,
                    allow_reuse=data.get("allowReuse", False) is True,
                )
            return save_intake_grouping(
                current,
                grouping,
                expected_digest=digest,
                allow_reuse=data.get("allowReuse", False) is True,
            )

        host.save(
            transform=grouped,
            install_guard=lambda: (
                not host.is_closing
                and not host.cancellation.is_set()
                and host.view.generation == generation
                and bridge.session_epoch == epoch
            ),
        )
        return
    if isinstance(project, WBIntakeWorkflowProject) and project.workflow.editing:
        if action != "intake_confirm":
            raise ValueError("分组编辑中请先保存并确认清单，再继续执行")

        def confirm_revision(current: WBFigureProject) -> WBIntakeWorkflowProject:
            if not isinstance(current, WBIntakeWorkflowProject):
                raise ValueError("执行清单已改变")
            return confirm_intake_group_revision(current, expected_digest=digest)

        host.save(transform=confirm_revision)
        return
    if action == "intake_accept_discovery":
        selections = data.get("selections")
        if not isinstance(selections, list):
            raise ValueError("请填写原图、Fig、蛋白、N与目标候选")
        choices = tuple(
            ExportSelection.model_validate(item) for item in cast(list[object], selections)
        )

        def accept(current: WBFigureProject) -> WBIntakeProject:
            if not isinstance(current, WBIntakeProject):
                raise ValueError("导入项目已改变")
            return accept_export_selections(current, choices, expected_digest=digest)

        generation = host.view.generation
        host.save(
            transform=accept,
            install_guard=lambda: (
                not host.is_closing
                and not host.cancellation.is_set()
                and host.view.generation == generation
            ),
        )
        return
    if action == "intake_prepare":
        generation = host.view.generation
        host.begin_operation()

        def prepared(reply: WBReply) -> None:
            if host.is_closing or host.cancellation.is_set() or host.view.generation != generation:
                host.finish_operation("执行计划准备已停止，当前草稿保留。")
                return
            if reply.error or not isinstance(reply.value, WBIntakeWorkflowProject):
                host.fail_operation(reply.error or "执行计划返回无效结果")
                return
            snapshot = reply.value
            host.end_phase()

            def install(current: WBFigureProject) -> WBIntakeWorkflowProject:
                if (
                    not isinstance(current, WBIntakeProject)
                    or current.project_id != snapshot.project_id
                    or intake_digest(current) != digest
                ):
                    raise ValueError("清单已变化，执行计划不能覆盖当前草稿")
                return WBIntakeWorkflowProject.model_validate(
                    {**dict(snapshot), "revision": current.revision}
                )

            host.save(
                transform=install,
                install_guard=lambda: (
                    not host.is_closing
                    and not host.cancellation.is_set()
                    and host.view.generation == generation
                ),
            )

        host.submit_tool_job(
            WBJob(
                "intake_workflow_prepare",
                document=project,
                data=digest.encode("ascii"),
                cancellation=host.cancellation,
            ),
            prepared,
            accept_errors=True,
        )
        return
    if action == "intake_sequence_continue":
        workflow_digest = data.get("workflowDigest")
        if (
            not isinstance(project, WBIntakeCropProject)
            or not isinstance(workflow_digest, str)
            or intake_digest(project) != digest
        ):
            raise ValueError("请核对当前整批执行摘要")
        crop = None
        if data.get("roi") is not None:
            roi, row_id = data.get("roi"), data.get("rowId")
            if not isinstance(roi, dict) or not isinstance(row_id, str):
                raise ValueError("请在对应原图核对裁剪范围")
            fields = cast(dict[str, object], roi)
            values = tuple(fields.get(k) for k in ("x", "y", "width", "height"))
            if any(type(v) is not int for v in values):
                raise ValueError("裁剪范围须为原图整数像素")
            x, y, width, height = cast(tuple[int, int, int, int], values)
            crop = LaneROI(row_id, x, y, x + width, y + height)

        def resume(current: WBFigureProject) -> WBIntakeCropProject:
            if not isinstance(current, WBIntakeCropProject) or intake_digest(current) != digest:
                raise ValueError("当前输入已改变，修正草稿保留")
            return continue_intake_sequence(
                current,
                expected_digest=workflow_digest,
                crop=crop,
                display_angle=_display_angle(data),
                use_crop_barrier=data.get("cropBarrier") is True,
            )

        generation, epoch = host.view.generation, bridge.session_epoch
        host.save(
            transform=resume,
            after=lambda: host.intake_workflow.start(
                intake_workflow_digest(cast(WBIntakeWorkflowProject, host.view.project()))
            ),
            install_guard=lambda: (
                not host.is_closing
                and not host.cancellation.is_set()
                and host.view.generation == generation
                and bridge.session_epoch == epoch
            ),
        )
        return
    if action == "intake_run":
        workflow_digest = data.get("workflowDigest")
        if not isinstance(workflow_digest, str) or intake_digest(project) != digest:
            raise ValueError("请核对当前裁剪执行摘要")
        host.intake_workflow.start(workflow_digest)
        return
    if action == "intake_export":
        workflow_digest = data.get("workflowDigest")
        if not isinstance(workflow_digest, str) or intake_digest(project) != digest:
            raise ValueError("请核对当前输出快照摘要")
        host.intake_workflow.publish_snapshot(workflow_digest)
        return
    if action == "intake_export_table":
        if intake_digest(project) != digest or not isinstance(project, WBIntakeOutputProject):
            raise ValueError("结果表输入已变化，请重新核对")
        require_intake_crop_barrier(project)
        host.choose_intake_table_export()
        return
    if action == "intake_measurement_preview":
        figure_id = data.get("figureId")
        if (
            not isinstance(project, WBIntakeFigureProject)
            or not isinstance(figure_id, str)
            or intake_digest(project) != digest
        ):
            raise ValueError("请选择当前已保存的 Fig 图片")
        host.intake_workflow.presentation.request(project, figure_id)
        return
    if action == "intake_view_figure":
        workflow_digest, figure_id = data.get("workflowDigest"), data.get("figureId")
        if (
            not isinstance(project, WBIntakeFigureProject)
            or not isinstance(figure_id, str)
            or not isinstance(workflow_digest, str)
            or intake_digest(project) != digest
        ):
            raise ValueError("请选择当前清单中已保存的Fig")
        host.intake_workflow.show_figure(figure_id, workflow_digest)
        return
    if action in {
        "intake_crop_review",
        "intake_crop_revise",
        "intake_crop_retry",
        "intake_stage_retry",
    }:
        workflow_digest, row_id = (
            data.get("workflowDigest"),
            data.get("rowId", data.get("targetId")),
        )
        if not isinstance(project, WBIntakeCropProject) or not isinstance(row_id, str):
            raise ValueError("请选择当前固定N裁剪行")
        if (
            not isinstance(workflow_digest, str)
            or workflow_digest != intake_workflow_digest(project)
            or intake_digest(project) != digest
        ):
            raise ValueError("裁剪草稿已变化，请重新核对")
        if action in {"intake_crop_review", "intake_crop_revise"}:
            roi = data.get("roi")
            if not isinstance(roi, dict):
                raise ValueError("请在原图上明确框选裁剪范围")
            fields = cast(dict[str, object], roi)
            values = tuple(fields.get(k) for k in ("x", "y", "width", "height"))
            if any(type(v) is not int for v in values):
                raise ValueError("裁剪范围须为原图整数像素")
            x, y, width, height = cast(tuple[int, int, int, int], values)
            review = (
                revise_completed_intake_crop
                if action == "intake_crop_revise"
                else review_intake_crop
            )
            updated = review(
                project,
                row_id,
                LaneROI(row_id, x, y, x + width, y + height),
                expected_digest=workflow_digest,
                display_angle=_display_angle(data),
            )
        else:
            stage = data.get("stage") if action == "intake_stage_retry" else "crop"
            if stage not in {"crop", "compose", "measure", "export"}:
                raise ValueError("此阶段尚未接通重试")
            if stage == "export" and not isinstance(project, WBIntakeOutputProject):
                raise ValueError("此项目没有身份输出阶段")
            if stage != "crop" and not isinstance(project, WBIntakeFigureProject):
                raise ValueError("此项目没有完整Fig阶段")
            retry_project = (
                adopt_intake_crop_barrier(project, expected_digest=workflow_digest)
                if data.get("cropBarrier") is True
                else project
            )
            retried = retry_intake_workflow_step(
                retry_project,
                cast(Literal["crop", "compose", "measure", "export"], stage),
                row_id,
                expected_digest=intake_workflow_digest(retry_project),
            )
            if not isinstance(retried, WBIntakeCropProject):
                raise ValueError("固定N裁剪项目类型无效")
            updated = retried

        def install_review(current: WBFigureProject) -> WBIntakeCropProject:
            if (
                not isinstance(current, WBIntakeCropProject)
                or intake_workflow_digest(current) != workflow_digest
            ):
                raise ValueError("当前裁剪输入已改变，原草稿保留")
            return type(updated).model_validate({**dict(updated), "revision": current.revision})

        generation = host.view.generation
        host.save(
            transform=install_review,
            install_guard=lambda: (
                not host.is_closing
                and not host.cancellation.is_set()
                and host.view.generation == generation
            ),
        )
        return
    if action == "intake_edit":
        if not isinstance(project, WBIntakeWorkflowProject) or intake_digest(project) != digest:
            raise ValueError("当前没有匹配的执行计划")

        def edit(current: WBFigureProject) -> WBIntakeProject:
            if not isinstance(current, WBIntakeWorkflowProject) or intake_digest(current) != digest:
                raise ValueError("执行计划已改变")
            return (
                begin_intake_group_revision(current, expected_digest=digest)
                if current.intake.grouping is not None
                else return_to_intake_editing(current)
            )

        host.save(transform=edit)
        return
    if isinstance(project, WBIntakeWorkflowProject):
        raise ValueError("执行计划已准备，请先返回清单修改；执行历史不可删除")
    if action == "intake_plan":
        figures, proteins = data.get("figures"), data.get("proteins")
        if not isinstance(figures, list) or not isinstance(proteins, list):
            raise ValueError("请填写 Fig、蛋白名和槽位数清单")
        updated = replace_intake_plan(
            project,
            tuple(IntakeFigure.model_validate(item) for item in cast(list[object], figures)),
            tuple(IntakeProtein.model_validate(item) for item in cast(list[object], proteins)),
            expected_digest=digest,
        )
    elif action == "intake_assign":
        bindings = data.get("bindings")
        if not isinstance(bindings, list):
            raise ValueError("请选择原图与蛋白的对应关系")
        if any(type(data.get(key, False)) is not bool for key in ("replace", "allowReuse")):
            raise ValueError("重分配及复用需要明确确认")
        updated = assign_intake_sources(
            project,
            tuple(IntakeAssignment.model_validate(item) for item in cast(list[object], bindings)),
            expected_digest=digest,
            replace=data.get("replace", False) is True,
            allow_reuse=data.get("allowReuse", False) is True,
        )
    elif action == "intake_confirm":
        # Commit confirmation only after durable save succeeds.
        def confirmed(current: WBFigureProject) -> WBIntakeProject:
            if not isinstance(current, WBIntakeProject):
                raise ValueError("当前项目已改变")
            return confirm_intake(current, expected_digest=digest)

        host.save(transform=confirmed)
        return
    else:
        raise ValueError("未知导入清单操作")
    host.view.set_project(updated)
    host.view.generation += 1
    host.save()
