"""Typed command boundary for the instrument planning page."""

from typing import TYPE_CHECKING, cast

from wb_tool.api import (
    IntakeAssignment,
    IntakeFigure,
    IntakeProtein,
    WBFigureProject,
    WBIntakeProject,
    WBIntakeWorkflowProject,
    WBJob,
    WBReply,
    assign_intake_sources,
    confirm_intake,
    intake_digest,
    replace_intake_plan,
    return_to_intake_editing,
)

if TYPE_CHECKING:
    from bioimage_app.web_bridge import WorkbenchBridge


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

            host.save(transform=install)

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
    if action == "intake_edit":
        if not isinstance(project, WBIntakeWorkflowProject) or intake_digest(project) != digest:
            raise ValueError("当前没有匹配的执行计划")

        def edit(current: WBFigureProject) -> WBIntakeProject:
            if not isinstance(current, WBIntakeWorkflowProject) or intake_digest(current) != digest:
                raise ValueError("执行计划已改变")
            return return_to_intake_editing(current)

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
