"""Host orchestration only: tool-owned detection, committed runs, traceable publication."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog
from wb_tool.api import (
    FigureRender,
    FigureSourcePath,
    WBAnalysisProject,
    WBFigureProject,
    WBJob,
    WBReply,
)

if TYPE_CHECKING:
    from bioimage_app.figure_window import FigureProjectWindow


class AutomaticWorkflow(QObject):
    finished = Signal(str)

    def __init__(self, window: "FigureProjectWindow") -> None:
        super().__init__(window)
        self.window = window
        self.last_output_path = ""
        self.failures: tuple[str, ...] = ()
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def choose_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(self.window, "导入 WB 原图文件夹（包含子文件夹）")
        if path:
            self.import_directory(path)

    def import_directory(self, directory: str) -> None:
        # Discovery is bounded and performed in the existing background queue.
        window = self.window
        if window.operation_busy or not window.workspace_path:
            return
        window.begin_operation()

        def found(reply: WBReply) -> None:
            import json

            if window.is_closing or window.cancellation.is_set():
                window.finish_operation("文件夹导入已取消")
                return
            if reply.error:
                window.fail_operation(reply.error)
                return
            if not isinstance(reply.value, bytes):
                window.fail_operation("原图文件列表无效")
                return
            paths: object = json.loads(reply.value)
            if not isinstance(paths, list) or not all(
                isinstance(path, str) for path in cast(list[object], paths)
            ):
                window.fail_operation("原图文件列表无效")
                return
            window.end_phase()
            if paths:
                window.import_images(tuple(cast(list[str], paths)), automatic=True)
            else:
                window.finish_operation("文件夹内没有 TIFF 原图；请选择包含 .tif 或 .tiff 的目录。")

        window.submit_tool_job(
            WBJob("discover_tiffs", path=directory, cancellation=window.cancellation),
            found,
            accept_errors=True,
        )

    def analyze(
        self,
        *,
        row_ids: tuple[str, ...] = (),
        import_errors: tuple[str, ...] = (),
        publish_output: bool = True,
    ) -> None:
        window = self.window
        if window.operation_busy or window.is_closing or not window.workspace_path:
            return
        try:
            project = window.view.project()
        except ValueError as error:
            window.fail_operation(str(error))
            return
        pending = [
            r.row_id for r in project.rows if r.source and (not row_ids or r.row_id in row_ids)
        ]
        if not pending:
            if import_errors:
                self.failures = import_errors
                self.cancelled = False
                window.save(after=self.publish_default)
                return
            window.finish_operation("请先导入 TIFF 原图，再开始自动分析。")
            return
        generation = window.view.generation
        self.cancelled = False
        errors: list[str] = list(import_errors)
        detected_ids: list[str] = []
        window.begin_operation()

        def next_row() -> None:
            nonlocal project, generation
            if (
                window.is_closing
                or self.cancelled
                or window.cancellation.is_set()
                or window.view.generation != generation
            ):
                window.finish_operation("自动分析已停止；当前编辑和历史结果保留。")
                return
            if not pending:
                self.failures = tuple(errors)
                window.view.set_project(project)
                window.view.generation += 1
                window.end_phase()
                if isinstance(project, WBAnalysisProject) and detected_ids:
                    window.view.status.setText("定位完成，正在按原始像素计算；自动结果待复核。")
                    window.analyze_project(
                        row_ids=tuple(detected_ids),
                        after=self.publish_default if publish_output else window.compose,
                    )
                else:
                    window.save(after=self.publish_default if publish_output else window.compose)
                return
            row_id = pending.pop(0)
            row = next(r for r in project.rows if r.row_id == row_id)
            assert row.source is not None
            path = window.source_paths.get(row.source.sha256)
            if path is None:
                errors.append(f"{row.filename}：原图资产不可读取")
                next_row()
                return
            window.view.status.setText(
                f"自动识别泳道与条带：{row.filename} · 剩余 {len(pending)} 张"
            )

            def detected(reply: WBReply) -> None:
                nonlocal project
                if isinstance(reply.value, WBFigureProject):
                    project = reply.value
                    detected_ids.append(row_id)
                elif reply.error:
                    errors.append(f"{row.filename}：{reply.error}")
                    failed = row.model_copy(
                        update={"notes": ("自动识别未完成：" + reply.error)[:2000]}
                    )
                    project = project.model_copy(
                        update={
                            "rows": tuple(failed if r.row_id == row_id else r for r in project.rows)
                        }
                    )
                else:
                    errors.append(f"{row.filename}：自动识别返回无效结果")
                next_row()

            window.submit_tool_job(
                WBJob(
                    "automatic_row",
                    path=path,
                    document=project,
                    row_id=row_id,
                    source_sha256=row.source.sha256,
                    cancellation=window.cancellation,
                ),
                detected,
                accept_errors=True,
            )

        next_row()

    def publish_default(self) -> None:
        window = self.window
        if window.is_closing or window.cancellation.is_set() or self.cancelled:
            window.finish_operation("自动输出已取消；已完成的计算结果保留。")
            return
        parent = Path(window.workspace_path) / "outputs"
        try:
            parent.mkdir(exist_ok=True)
        except OSError as error:
            window.fail_operation(f"无法创建输出目录：{error}")
            return
        name = datetime.now().strftime("WB-%Y%m%d-%H%M%S-") + uuid4().hex[:6]
        self.export(str(parent / name))

    def choose_export(self) -> None:
        parent = QFileDialog.getExistingDirectory(self.window, "选择自动结果的保存位置")
        if parent:
            self.cancelled = False
            name = datetime.now().strftime("WB-%Y%m%d-%H%M%S-") + uuid4().hex[:6]
            self.export(str(Path(parent) / name))

    def export(self, destination: str) -> None:
        window = self.window
        if window.operation_busy or window.is_closing or not window.workspace_path:
            return

        def saved() -> None:
            if window.is_closing or window.cancellation.is_set() or self.cancelled:
                window.finish_operation("自动结果导出已取消")
                return
            project = window.view.project()
            generation = window.view.generation
            window.begin_operation()
            window.view.status.setText("正在生成拼图、结果表和来源归档…")

            def exported(reply: WBReply) -> None:
                if not isinstance(reply.value, str):
                    window.fail_operation("自动输出返回无效目录")
                    return
                self.last_output_path = reply.value
                message = "自动结果已导出（待复核）：" + reply.value
                if self.failures:
                    message += f"；{len(self.failures)} 张需处理，详见状态报告"

                def rendered(preview: WBReply) -> None:
                    if window.is_closing or self.cancelled or window.view.generation != generation:
                        window.finish_operation(
                            "结果已发布；后续预览已停止：" + self.last_output_path
                        )
                        return
                    if isinstance(preview.value, FigureRender):
                        window.view.show_render(preview.value)

                    def ready() -> None:
                        if window.is_closing or self.cancelled:
                            return
                        self.finished.emit(self.last_output_path)
                        index = next((i for i, row in enumerate(project.rows) if row.roi), 0)
                        if window.view.table.currentRow() != index:
                            window.view.table.setCurrentCell(index, 0)
                        elif project.rows:
                            window.select_source(project.rows[index].row_id)

                    window.end_phase()
                    window.refresh_project_table(message, after=ready)

                window.submit_tool_job(
                    WBJob(
                        "figure_preview",
                        document=project,
                        sources=tuple(
                            FigureSourcePath(sha, path) for sha, path in window.source_paths.items()
                        ),
                        cancellation=window.cancellation,
                    ),
                    rendered,
                    accept_errors=True,
                )

            window.submit_export_job(
                WBJob(
                    "automatic_export",
                    document=project,
                    destination=destination,
                    sources=tuple(
                        FigureSourcePath(sha, path) for sha, path in window.source_paths.items()
                    ),
                    cancellation=window.cancellation,
                    processing_errors=self.failures,
                ),
                exported,
            )

        window.save(after=saved)
