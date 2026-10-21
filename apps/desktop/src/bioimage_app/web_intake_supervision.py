"""Guarded aggregate presentation and persisted batch display configuration."""

from typing import TYPE_CHECKING, Literal, cast

from wb_tool.api import (
    FigureRender,
    FigureSourcePath,
    IntakeGrid,
    WBIntakeOutputProject,
    WBJob,
    WBReply,
    intake_workflow_digest,
    revise_intake_grid,
)

from bioimage_app.storage import StorageCommand, StorageReply

if TYPE_CHECKING:
    from bioimage_app.web_bridge import WorkbenchBridge


def apply_supervision(bridge: "WorkbenchBridge", action: str, data: dict[str, object]) -> None:
    host = bridge.host
    project = host.view.project()
    generation, epoch = host.view.generation, bridge.session_epoch
    if (
        not isinstance(project, WBIntakeOutputProject)
        or data.get("projectId") != project.project_id
        or data.get("sessionEpoch") != epoch
        or data.get("workflowDigest") != intake_workflow_digest(project)
    ):
        raise ValueError("项目或执行状态已变化，请刷新后重试")

    def current() -> bool:
        return (
            not host.is_closing
            and not host.cancellation.is_set()
            and host.view.generation == generation
            and bridge.session_epoch == epoch
        )

    if action == "intake_grid_save":
        grid = IntakeGrid.model_validate(data.get("grid"))
        updated = revise_intake_grid(project, grid)
        host.save(
            transform=lambda saved: type(updated).model_validate(
                {
                    **dict(updated),
                    "revision": saved.revision,
                }
            ),
            install_guard=current,
            after=lambda: apply_supervision(
                bridge,
                "intake_grid_preview",
                {
                    "projectId": project.project_id,
                    "sessionEpoch": epoch,
                    "workflowDigest": intake_workflow_digest(
                        cast(WBIntakeOutputProject, host.view.project())
                    ),
                },
            ),
        )
        return

    figure_id = data.get("figureId")
    selected = next((e for e in project.intake_figures if e.figure_id == figure_id), None)
    destination = ""
    if action in {"intake_grid_export", "intake_single_export"}:
        from PySide6.QtWidgets import QFileDialog

        if action == "intake_single_export" and selected is None:
            raise ValueError("请选择已保存的Fig")
        destination, _ = QFileDialog.getSaveFileName(
            host,
            "导出显示拼图（不覆盖已有文件）",
            "all-figures.png" if selected is None else "figure.png",
            "PNG (*.png);;TIFF (*.tiff)",
        )
        if not destination or not current():
            return
    elif action != "intake_grid_preview":
        raise ValueError("未知拼图操作")
    assets = (
        [selected.image]
        if action == "intake_single_export" and selected
        else [e.image for e in project.intake_figures]
    )
    sources: list[FigureSourcePath] = []
    host.begin_operation()

    def completed(reply: WBReply) -> None:
        if not current():
            host.finish_operation("旧拼图回复未覆盖当前项目。")
        elif reply.error:
            host.fail_operation(reply.error)
        elif isinstance(reply.value, FigureRender):
            host.view.show_render(reply.value)
            host.finish_operation("全部Fig总图已显示；导出使用同一布局。")
        elif isinstance(reply.value, str):
            host.finish_operation("显示拼图已保存：" + reply.value)
        else:
            host.fail_operation("拼图返回无效结果")

    def next_asset() -> None:
        if not current():
            host.finish_operation("拼图操作已取消。")
            return
        if len(sources) == len(assets):
            host.submit_tool_job(
                WBJob(
                    cast(
                        Literal[
                            "intake_grid_preview", "intake_grid_export", "intake_single_export"
                        ],
                        action,
                    ),
                    document=project,
                    sources=tuple(sources),
                    destination=destination,
                    row_id=selected.figure_id if selected else "",
                    path=sources[0].path if action == "intake_single_export" and sources else "",
                    cancellation=host.cancellation,
                ),
                completed,
                accept_errors=True,
            )
            return
        asset = assets[len(sources)]

        def resolved(reply: StorageReply) -> None:
            if not current():
                host.finish_operation("旧拼图资产回复已忽略。")
                return
            if reply.error_code or not isinstance(reply.value, str):
                host.fail_operation(reply.message or "Fig资产不可读取")
                return
            sources.append(FigureSourcePath(asset.sha256, reply.value))
            next_asset()

        host.submit_storage_job(StorageCommand("asset", asset=asset), resolved, accept_errors=True)

    next_asset()
