"""Explicit assembly of WB project review, immutable asset storage and background rendering."""

from collections.abc import Callable
from pathlib import Path
from threading import Event
from uuid import uuid4

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolBar,
)
from tool_contracts.api import AssetRef, DraftSnapshot
from wb_tool.api import (
    ArchiveRunEvidence,
    CropSuggestion,
    FigurePNG,
    FigureRender,
    FigureRow,
    FigureSourcePath,
    LoadedProjectOCR,
    LoadedProjectResult,
    MetadataBook,
    PreviewRaster,
    ProjectDerivedTables,
    ProjectOCRState,
    ProjectTableSnapshot,
    RestoredProjectResults,
    WBAnalysisProject,
    WBFigureProject,
    WBJob,
    WBProjectOCR,
    WBReply,
    WBRestoredProject,
    WBReviewProject,
    create_figure_project_view,
    create_wb_background,
    prepare_project_analyses,
    project_assets,
    project_with_ocr,
    record_crop_suggestion,
)

from bioimage_app.project_archive import ProjectArchiveSession
from bioimage_app.project_measurements import ProjectBatchCompletion, ProjectMeasurementSession
from bioimage_app.project_ocr import ProjectOCRCompletion, ProjectOCRSession
from bioimage_app.project_restore import ArchiveRestoreJob, ArchiveRestoreResult
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply


class FigureProjectWindow(QMainWindow):
    closed = Signal()
    measurement_progress = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WB 自动化 · 多原图与 Fig 拼图项目")
        self.resize(1300, 950)
        self.view = create_figure_project_view()
        self.setCentralWidget(self.view)
        self._store = AsyncStorage(self)
        self._background = create_wb_background()
        self._storage_callbacks: dict[str, Callable[[StorageReply], None]] = {}
        self._storage_accept_errors: set[str] = set()
        self._wb_callbacks: dict[str, Callable[[WBReply], None]] = {}
        self._wb_accept_errors: set[str] = set()
        self._store.replied.connect(self._storage_reply)
        self._background.replied.connect(self._wb_reply)
        self._store.closed.connect(self._store_stopped)
        self._background.closed.connect(self._background_stopped)
        self._workspace = ""
        self._paths: dict[str, str] = {}
        self._saved_revision: int | None = None
        self._saved_generation = 0
        self._busy = False
        self._closing = False
        self._shutting = False
        self._store_closed = False
        self._background_closed = False
        self._cancellation = Event()
        self._measurement_session: ProjectMeasurementSession | None = None
        self._project_results: tuple[LoadedProjectResult, ...] = ()
        self._ocr_session: ProjectOCRSession | None = None
        self._loaded_ocr: LoadedProjectOCR | None = None
        self._archive_session: ProjectArchiveSession | None = None
        self._restore_job: ArchiveRestoreJob | None = None
        self._export_generation: int | None = None
        self._ocr_refresh_pending = False
        self._ocr_refresh_timer = QTimer(self)
        self._ocr_refresh_timer.setSingleShot(True)
        self._ocr_refresh_timer.timeout.connect(self.refresh_ocr_table)
        bar = QToolBar("项目")
        self.addToolBar(bar)
        self.create_button = QPushButton("新建项目工作区")
        self.open_button = QPushButton("打开项目工作区")
        self.restore_button = QPushButton("从 ZIP 恢复")
        self.import_button = QPushButton("批量导入 TIFF")
        self.save_button = QPushButton("保存项目")
        self.new_button = QPushButton("复用模板新建项目")
        self.cancel_button = QPushButton("取消当前任务")
        self.documents = QComboBox()
        self.documents.setMinimumWidth(240)
        for button in (
            self.create_button,
            self.open_button,
            self.restore_button,
            self.import_button,
            self.save_button,
            self.new_button,
            self.cancel_button,
            self.documents,
        ):
            bar.addWidget(button)
        self.create_button.clicked.connect(lambda: self._choose_workspace(True))
        self.open_button.clicked.connect(lambda: self._choose_workspace(False))
        self.restore_button.clicked.connect(self._choose_restore)
        self.import_button.clicked.connect(self._choose_import)
        self.save_button.clicked.connect(lambda: self.save())
        self.new_button.clicked.connect(self.new_project)
        self.cancel_button.clicked.connect(self.cancel)
        self.documents.activated.connect(self._choose_document)
        self.view.source_requested.connect(self.select_source)
        self.view.preview_requested.connect(lambda: self.compose())
        self.view.export_requested.connect(self._choose_export)
        self.view.image_export_requested.connect(self._choose_image_export)
        self.view.font_requested.connect(self._choose_font)
        self.view.detection_requested.connect(self.detect_crops)
        self.view.metadata.import_requested.connect(self._choose_metadata_import)
        self.view.metadata.thumbnails_requested.connect(self.load_thumbnails)
        self.view.analysis.run_requested.connect(self.analyze_project)
        self.view.analysis.refresh_requested.connect(self.refresh_project_table)
        self.view.analysis.export_requested.connect(self._choose_table_export)
        self.view.ocr.import_requested.connect(self._choose_ocr_import)
        self.view.ocr.run_requested.connect(self.recognize_project)
        self.view.ocr.compose_requested.connect(self.recognize_composed_figure)
        self.view.ocr.refresh_requested.connect(self.refresh_ocr_table)
        self.view.ocr.export_requested.connect(lambda: self._choose_table_export(True))
        self.view.normalization.refresh_requested.connect(self.refresh_ocr_table)
        self.view.normalization.export_requested.connect(self._choose_normalization_export)
        self.view.changed.connect(self._queue_ocr_refresh)
        self.view.changed.connect(self._cancel_stale_export)
        self._controls()

    def cancel(self) -> None:
        self._cancellation.set()
        if self._measurement_session:
            self._measurement_session.cancel()
        if self._ocr_session:
            self._ocr_session.cancel()

    def _choose_restore(self) -> None:
        source, _ = QFileDialog.getOpenFileName(self, "选择项目 ZIP 归档", "", "ZIP (*.zip)")
        if not source:
            return
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "输入新的工作区目录名",
            str(Path(source).with_suffix("")),
            "工作区目录 (*)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if destination:
            self.restore_archive(source, destination)

    def restore_archive(self, source: str, destination: str) -> None:
        if self._busy or self._workspace or self._closing:
            return
        self._start()
        self.view.status.setText("正在校验归档并恢复到新的工作区…")
        job = ArchiveRestoreJob(source, destination, self._cancellation, self)
        self._restore_job = job

        def finished(result: ArchiveRestoreResult) -> None:
            self._restore_job = None
            job.deleteLater()
            if self._closing:
                self._done("恢复任务已结束" + ("；新工作区已完整保存。" if result.path else "。"))
                return
            if result.error:
                self._error(result.error)
                return

            # Publication can win before cancellation. Open only after actual thread teardown.
            def opened(reply: StorageReply) -> None:
                self._workspace = result.path

                def listed(reply: StorageReply) -> None:
                    self._list_documents(reply)
                    if not self._closing:
                        self.load_document(result.project_id)

                self._storage(StorageCommand("documents"), listed)

            self._storage(StorageCommand("open", path=result.path), opened)

        job.finished.connect(finished)
        job.start()

    def _choose_metadata_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择元信息表", "", "Excel / CSV (*.xlsx *.csv)"
        )
        if path:
            self.import_metadata(path)

    def import_metadata(self, path: str) -> None:
        if self._busy or not self._workspace or self._closing:
            return
        generation = self.view.generation
        self._start()

        def parsed(reply: WBReply) -> None:
            if self._closing or self._cancellation.is_set() or generation != self.view.generation:
                self._done("元信息导入已取消或项目已修改；原预览保持。")
            elif reply.error or not isinstance(reply.value, MetadataBook):
                self._error(reply.error or "元信息读取结果无效")
            else:
                self.view.metadata.install_book(reply.value, Path(path).name)
                self._done("元信息表已读取，请在“批量元信息”选择列并预览。")

        self._wb(
            WBJob("metadata_read", path=path, cancellation=self._cancellation),
            parsed,
            accept_errors=True,
        )

    def load_thumbnails(self) -> None:
        if self._busy or not self._workspace or self._closing:
            return
        try:
            project = self.view.project()
        except ValueError as error:
            self._error(str(error))
            return
        generation = self.view.generation
        sources = {
            r.source.sha256: self._paths.get(r.source.sha256, "")
            for r in project.rows
            if r.source and not self.view.has_thumbnail(r.source.sha256)
        }
        pending = list(sources.items())
        errors: list[str] = []
        self._start()

        def next_image() -> None:
            if (
                self._closing
                or self._cancellation.is_set()
                or generation != self.view.generation
                or not pending
            ):
                message = f"缩略图加载结束；{len(errors)} 张失败。" + (
                    " " + "; ".join(errors[:3]) if errors else ""
                )
                self._done(message)
                return
            digest, path = pending.pop(0)
            self.view.status.setText(f"正在加载原图缩略图；剩余 {len(pending)} 张。")

            def received(reply: WBReply) -> None:
                if (
                    generation == self.view.generation
                    and not self._closing
                    and not self._cancellation.is_set()
                ):
                    if (
                        reply.error
                        or not isinstance(reply.value, PreviewRaster)
                        or reply.value.sha256 != digest
                    ):
                        errors.append(reply.error or "原图摘要不符")
                    else:
                        self.view.install_thumbnail(reply.value)
                next_image()

            self._wb(WBJob("preview", path=path, preview_edge=128), received, accept_errors=True)

        next_image()

    def _queue_ocr_refresh(self) -> None:
        self._ocr_refresh_pending = True
        self._ocr_refresh_timer.start(150)

    def refresh_ocr_table(self, message: str = "关联与归一化结果已刷新") -> None:
        if self._busy or not self._workspace or self._closing:
            return
        self._ocr_refresh_timer.stop()
        self._ocr_refresh_pending = False
        try:
            project = self.view.project()
            self.view.normalization.refresh_targets(project)
            if not isinstance(project, WBProjectOCR):
                return
            self.view.ocr.refresh_targets(project)
        except ValueError as error:
            self.view.status.setText(str(error))
            return
        generation = self.view.generation
        self._start()

        def filled(reply: WBReply) -> None:
            if generation == self.view.generation and isinstance(reply.value, ProjectDerivedTables):
                self.view.ocr.result_view.show_cells(reply.value.ocr_cells)
                self.view.normalization.result_view.show_snapshot(reply.value.normalization)
                self._done(message)
            else:
                self._done("项目已改变，未写入过期OCR关联表")

        self._wb(
            WBJob(
                "project_derived_tables",
                document=project,
                project_results=self._project_results,
                project_ocr_result=self._loaded_ocr,
            ),
            filled,
        )

    def _choose_ocr_import(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self, "导入独立拼图", "", "拼图 (*.tif *.tiff *.png)"
        )
        if source:
            self.import_ocr_image(source)

    def import_ocr_image(self, source: str) -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project()
        except ValueError as error:
            self._error(str(error))
            return
        generation = self.view.generation
        self._start()

        def previewed(reply: WBReply) -> None:
            if self._abort_ocr_import(generation):
                return
            if reply.error:
                self._error(reply.error)
                return
            if not isinstance(reply.value, PreviewRaster):
                self._error("拼图预览失败")
                return
            self._attach_ocr_source(
                project,
                generation,
                Path(source).name,
                StorageCommand("import", path=source, source_sha256=reply.value.sha256),
            )

        self._wb(WBJob("ocr_preview", path=source), previewed, accept_errors=True)

    def _abort_ocr_import(self, generation: int) -> bool:
        if self._closing or self._cancellation.is_set():
            self._done("拼图生成/导入已取消，之前关联保留")
            return True
        if generation != self.view.generation:
            self._done("项目已修改，未替换拼图或覆盖编辑")
            return True
        return False

    def _attach_ocr_source(
        self,
        project: WBFigureProject,
        generation: int,
        filename: str,
        command: StorageCommand,
        *,
        recognize: bool = False,
    ) -> None:
        if self._abort_ocr_import(generation):
            return

        def imported(response: StorageReply) -> None:
            if not isinstance(response.value, AssetRef):
                self._error("拼图资产无效")
                return
            asset = response.value
            if self._abort_ocr_import(generation):
                return

            def resolved(result: StorageReply) -> None:
                if not isinstance(result.value, str):
                    self._error("拼图资产路径无效")
                    return
                path = result.value

                def previewed(reply: WBReply) -> None:
                    if self._abort_ocr_import(generation):
                        return
                    if reply.error:
                        self._error(reply.error)
                        return
                    raster = reply.value
                    if not isinstance(raster, PreviewRaster) or raster.sha256 != asset.sha256:
                        self._error("拼图预览与已导入资产不一致")
                        return
                    self._paths[asset.sha256] = path
                    self._loaded_ocr = None
                    self.view.set_project(
                        project_with_ocr(
                            project,
                            ProjectOCRState(
                                source=asset,
                                filename=filename,
                                width=raster.width,
                                height=raster.height,
                            ),
                        )
                    )
                    self.view.generation += 1
                    self.view.ocr.set_preview(raster)
                    if recognize:
                        self._busy = False
                        self.recognize_project()
                    else:
                        self._done("拼图已导入；识别Fig/行名后逐行关联原图。")

                self._wb(WBJob("ocr_preview", path=path), previewed, accept_errors=True)

            self._storage(StorageCommand("asset", asset=asset), resolved)

        self._storage(command, imported)

    def recognize_composed_figure(self) -> None:
        if self._busy or not self._workspace:
            return

        def saved() -> None:
            if self._closing or self._cancellation.is_set():
                self._done("生成拼图已取消，之前关联保留")
                return
            project = self.view.project()
            generation = self.view.generation
            self._start()
            self.view.status.setText("正在生成完整拼图，随后识别Fig/行名…")

            def generated(reply: WBReply) -> None:
                if self._abort_ocr_import(generation):
                    return
                if reply.error:
                    self._error(reply.error)
                    return
                if not isinstance(reply.value, FigurePNG):
                    self._error("生成拼图无效")
                    return
                self._attach_ocr_source(
                    project,
                    generation,
                    f"composed-r{project.revision}.png",
                    StorageCommand(
                        "import_bytes",
                        path="figure.png",
                        data=reply.value.data,
                        source_sha256=reply.value.sha256,
                    ),
                    recognize=True,
                )

            self._wb(
                WBJob(
                    "figure_ocr",
                    document=project,
                    sources=tuple(FigureSourcePath(sha, path) for sha, path in self._paths.items()),
                    cancellation=self._cancellation,
                ),
                generated,
                accept_errors=True,
            )

        self.save(after=saved)

    def recognize_project(self) -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project()
            if not isinstance(project, WBProjectOCR) or project.ocr is None:
                raise ValueError("请先导入独立拼图")
        except ValueError as error:
            self._error(str(error))
            return

        def saved() -> None:
            if self._closing or self._cancellation.is_set():
                self._done("识别已取消，之前关联保留")
                return
            project = self.view.project()
            assert isinstance(project, WBProjectOCR)
            self._start_ocr(project)

        self.save(after=saved)

    def _start_ocr(
        self,
        project: WBProjectOCR,
        *,
        restore: bool = False,
        after: Callable[[], None] | None = None,
    ) -> None:
        ocr = project.ocr
        if ocr is None:
            self._error("请先导入独立拼图")
            return
        generation = self.view.generation
        self._start()
        session = ProjectOCRSession(self._store, self._background, self)
        self._ocr_session = session
        self.view.status.setText("正在校验已保存OCR…" if restore else "正在后台识别Fig/蛋白名…")

        def completed(completion: ProjectOCRCompletion) -> None:
            self._ocr_session = None
            session.deleteLater()
            if generation != self.view.generation:
                self._done("项目已修改，OCR结果仅保留在历史，未覆盖编辑。")
                return
            if restore:
                self._loaded_ocr = completion.loaded
                if completion.error:
                    self.view.ocr.note.setText("OCR结果不可用：" + completion.error)

                def previewed(reply: WBReply) -> None:
                    if isinstance(reply.value, PreviewRaster):
                        self.view.ocr.set_preview(reply.value)
                    self._busy = False
                    if after:
                        after()
                    else:
                        self._done("OCR原文已校验" if completion.loaded else "OCR原文未载入")

                self._wb(WBJob("ocr_preview", path=self._paths[ocr.source.sha256]), previewed)
            elif completion.loaded is None:
                self._busy = False
                message = "识别未更新，之前关联保留：" + (completion.error or completion.state)
                if self._closing:
                    self._done(message)
                else:
                    self.refresh_ocr_table(message)
            else:
                loaded = completion.loaded

                def installed(reply: WBReply) -> None:
                    if generation != self.view.generation:
                        self._done("项目已修改，OCR建议未覆盖编辑")
                        return
                    if not isinstance(reply.value, WBProjectOCR):
                        self._error("OCR建议生成失败")
                        return
                    self._loaded_ocr = loaded
                    self.view.set_project(reply.value)
                    self.view.generation += 1
                    self._busy = False

                    def saved() -> None:
                        if self._closing:
                            self._done("OCR识别已保存")
                        else:
                            self.refresh_ocr_table("OCR完成；请校正名称、关联原图并确认。")

                    self.save(after=saved)

                self._wb(
                    WBJob("project_ocr_install", document=project, project_ocr_result=loaded),
                    installed,
                )

        session.finished.connect(completed)
        session.start(project, self._workspace, restore=restore)
        if self._closing:
            session.cancel()

    def analyze_project(self, all_rows: bool = False) -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project()
            if not isinstance(project, WBAnalysisProject):
                raise ValueError("请先配置已审核行的定量")
            selected = self.view.selected_row()
            row_ids = tuple(
                p.row_id
                for p in project.analyses
                if all_rows or (selected and p.row_id == selected.row_id)
            )
            prepared = prepare_project_analyses(
                project, row_ids, 0 if self._saved_revision is None else self._saved_revision + 1
            )
            self.view.set_project(prepared)
            self.view.generation += 1
        except ValueError as error:
            self._error(str(error))
            return

        def saved() -> None:
            if self._closing or self._cancellation.is_set():
                self._done("计算已取消；标注已保存。")
                return
            current = self.view.project()
            assert isinstance(current, WBAnalysisProject)
            self._start_measurements(current, row_ids)

        self.save(after=saved)

    def _start_measurements(
        self, project: WBAnalysisProject, row_ids: tuple[str, ...], *, restore: bool = False
    ) -> None:
        generation = self.view.generation
        self._start()
        session = ProjectMeasurementSession(self._store, self._background, self)
        self._measurement_session = session
        session.progress.connect(self.view.status.setText)
        session.progress.connect(self.measurement_progress)

        def completed(completion: ProjectBatchCompletion) -> None:
            self._measurement_session = None
            session.deleteLater()
            if self.view.generation != generation:
                self._done("项目发生修改，运行已保留在历史，未覆盖当前标注。")
                return
            by_row = {r.row_id: r for r in (() if restore else self._project_results)}
            by_row.update({r.row_id: r for r in completion.results})
            retained: list[LoadedProjectResult] = []
            retained_bytes = 0
            overflow = False
            for plan in completion.project.analyses:
                cached = by_row.get(plan.row_id)
                if cached and plan.run and plan.run.result and cached.run_id == plan.run.run_id:
                    retained_bytes += plan.run.result.size_bytes
                    if retained_bytes <= 64 * 1024 * 1024:
                        retained.append(cached)
                    else:
                        overflow = True
            self._project_results = tuple(retained)
            message = (
                "结果已校验"
                if restore
                else (
                    "计算已取消；已完成行保留" if completion.cancelled else "计算结束，结果已提交"
                )
            )
            if completion.errors:
                message += "；" + "；".join(completion.errors[:3])
            if overflow:
                message += "；部分曲线超过 64 MiB 显示预算，结果仍保留在历史"
            self._busy = False
            if not restore:
                self.view.set_project(completion.project)
                self.view.generation += 1
                self.save(after=lambda: self.refresh_project_table(message))
            else:
                self.refresh_project_table(message)

        session.finished.connect(completed)
        session.start(project, row_ids, self._workspace, restore=restore)
        if self._closing:
            session.cancel()

    def refresh_project_table(self, message: str = "项目结果表已刷新") -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project()
        except ValueError as error:
            self._error(str(error))
            return
        generation = self.view.generation
        self._start()

        def filled(reply: WBReply) -> None:
            if self.view.generation != generation:
                self._done("项目已改变，请重新刷新结果表")
                return
            if not isinstance(reply.value, ProjectTableSnapshot):
                self._error("项目结果表无效")
                return
            self.view.install_results(self._project_results)
            self.view.analysis.show_cells(reply.value.cells)
            if isinstance(project, WBProjectOCR) and not self._closing:
                self._busy = False
                self.refresh_ocr_table(message)
            else:
                self._done(message)

        self._wb(
            WBJob("project_table", document=project, project_results=self._project_results), filled
        )

    def _choose_table_export(self, ocr: bool = False) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self, "导出新的项目结果表", "", "Excel (*.xlsx);;CSV（文字采用text:前缀） (*.csv)"
        )
        if destination:
            self.export_project_table(destination, ocr=ocr)

    def _choose_normalization_export(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self, "导出新的归一化结果", "", "Excel (*.xlsx);;CSV（文字采用text:前缀） (*.csv)"
        )
        if destination:
            self.export_project_table(destination, normalization=True)

    def export_project_table(
        self, destination: str, *, ocr: bool = False, normalization: bool = False
    ) -> None:
        if self._busy or not self._workspace:
            return

        def saved() -> None:
            project = self.view.project()
            self._start()
            self._export_with_evidence(
                WBJob(
                    "project_normalization_export"
                    if normalization
                    else ("project_ocr_export" if ocr else "project_export"),
                    document=project,
                    project_results=self._project_results,
                    project_ocr_result=self._loaded_ocr,
                    ocr_labels=bool(self.view.normalization.result_view.labels.currentIndex()),
                    destination=destination,
                    cancellation=self._cancellation,
                ),
                lambda reply: self._done("项目结果表已导出：" + str(reply.value)),
            )

        self.save(after=saved)

    def _cancel_stale_export(self) -> None:
        if self._export_generation is not None and self._export_generation != self.view.generation:
            self._cancellation.set()

    def _export_with_evidence(self, job: WBJob, callback: Callable[[WBReply], None]) -> None:
        from dataclasses import replace

        if not isinstance(job.document, WBFigureProject):
            self._error("缺少导出项目")
            return
        generation = self.view.generation
        self._export_generation = generation

        def collected(evidence: tuple[ArchiveRunEvidence, ...]) -> None:
            self._archive_session = None
            if self._cancellation.is_set() or self._closing or generation != self.view.generation:
                self._done("导出已取消，未发布输出")
                return

            def completed(reply: WBReply) -> None:
                if reply.error:
                    if self._cancellation.is_set():
                        self._done("导出已取消，未发布输出")
                    else:
                        self._error(reply.error)
                else:
                    callback(reply)

            self._wb(replace(job, archive_runs=evidence), completed, accept_errors=True)

        try:
            session = ProjectArchiveSession(
                self._store, job.document, self._cancellation, collected
            )
            self._archive_session = session
            session.start()
        except (ValueError, RuntimeError) as error:
            self._error(str(error))

    @property
    def resources_closed(self) -> bool:
        return self._store_closed and self._background_closed and self._restore_job is None

    def _controls(self) -> None:
        idle = not self._busy and not self._closing
        self.create_button.setEnabled(idle and not self._workspace)
        self.open_button.setEnabled(idle and not self._workspace)
        self.restore_button.setEnabled(idle and not self._workspace)
        self.import_button.setEnabled(idle and bool(self._workspace))
        self.save_button.setEnabled(idle and bool(self._workspace))
        self.new_button.setEnabled(idle and bool(self._workspace))
        self.documents.setEnabled(idle and bool(self._workspace))
        self.cancel_button.setEnabled(self._busy and not self._closing)
        self.view.setEnabled(idle and bool(self._workspace))

    def _start(self) -> None:
        self._busy = True
        self._cancellation.clear()
        self._controls()

    def _done(self, message: str) -> None:
        self._busy = False
        self._export_generation = None
        self.view.status.setText(message)
        self._controls()
        if self._closing:
            self._finish_close()
        elif self._ocr_refresh_pending:
            self._ocr_refresh_timer.start(0)

    def _error(self, message: str) -> None:
        self._ocr_refresh_timer.stop()
        self._ocr_refresh_pending = False
        self._closing = False
        self._done("操作失败：" + message)

    def _storage(
        self,
        command: StorageCommand,
        callback: Callable[[StorageReply], None],
        *,
        accept_errors: bool = False,
    ) -> None:
        try:
            request_id = self._store.submit(command)
            self._storage_callbacks[request_id] = callback
            if accept_errors:
                self._storage_accept_errors.add(request_id)
        except (ValueError, RuntimeError) as error:
            self._error(str(error))

    def _wb(
        self, job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        try:
            request_id = self._background.submit(job)
            self._wb_callbacks[request_id] = callback
            if accept_errors:
                self._wb_accept_errors.add(request_id)
        except (ValueError, RuntimeError) as error:
            self._error(str(error))

    def _storage_reply(self, reply: StorageReply) -> None:
        callback = self._storage_callbacks.pop(reply.request_id, None)
        accept_errors = reply.request_id in self._storage_accept_errors
        self._storage_accept_errors.discard(reply.request_id)
        if callback:
            if reply.error_code and not accept_errors:
                self._error(reply.message)
            else:
                callback(reply)

    def _wb_reply(self, reply: WBReply) -> None:
        callback = self._wb_callbacks.pop(reply.request_id, None)
        accept_errors = reply.request_id in self._wb_accept_errors
        self._wb_accept_errors.discard(reply.request_id)
        if callback:
            if reply.error and not accept_errors:
                self._error(reply.error)
            else:
                callback(reply)

    def detect_crops(self, all_rows: bool = False) -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project()
            if all_rows and self.view.suggestions.manual.isChecked():
                raise ValueError("手框膜范围只适用于当前行；批量检测请关闭该选项")
            selected = self.view.selected_row()
            rows = tuple(
                r
                for r in project.rows
                if r.source and (all_rows or (selected and r.row_id == selected.row_id))
            )
            if not rows:
                raise ValueError("请选择有原图的行")
            pending = [
                (r, self.view.suggestions.settings(r, project.template.crop_height)) for r in rows
            ]
        except ValueError as error:
            self._error(str(error))
            return
        generation = self.view.generation
        completed = failed = 0
        self._start()

        def finish() -> None:
            if self.view.generation != generation:
                self._done("候选结果已丢弃：检测期间项目发生了修改，请重新检测。")
                return
            if isinstance(project, WBReviewProject):
                self.view.install_suggestions(project)
            state = "已取消" if self._cancellation.is_set() else "已结束"
            self._done(
                f"候选检测{state}：完成 {completed} 行，失败 {failed} 行。"
                "建议已保留，选择候选并应用后仍须审核。"
            )

        def next_row() -> None:
            if not pending or self._cancellation.is_set() or self.view.generation != generation:
                finish()
                return
            row, settings = pending.pop(0)
            assert row.source is not None
            sha = row.source.sha256
            self.view.status.setText(
                f"正在检测 {row.filename}；剩余 {len(pending)} 行。"
                f"N={settings.lane_count}，高={settings.crop_height}"
            )

            def received(reply: WBReply) -> None:
                nonlocal project, completed, failed
                if self._cancellation.is_set():
                    finish()
                    return
                if self.view.generation != generation:
                    finish()
                    return
                if isinstance(reply.value, CropSuggestion):
                    suggestion = reply.value
                    if (
                        suggestion.row_id != row.row_id
                        or suggestion.source_sha256 != sha
                        or suggestion.settings != settings
                        or suggestion.source_revision != project.revision
                    ):
                        self._error("检测结果与请求身份不一致")
                        return
                    completed += 1
                else:
                    suggestion = CropSuggestion(
                        row_id=row.row_id,
                        source_sha256=sha,
                        source_revision=project.revision,
                        settings=settings,
                        error=(reply.error or "检测后台未返回结果")[:2000],
                    )
                    failed += 1
                project = record_crop_suggestion(project, suggestion)
                next_row()

            self._wb(
                WBJob(
                    "crop_suggest",
                    path=self._paths.get(sha, ""),
                    row_id=row.row_id,
                    source_sha256=sha,
                    revision=project.revision,
                    detection_settings=settings,
                    cancellation=self._cancellation,
                ),
                received,
                accept_errors=True,
            )

        next_row()

    def _choose_workspace(self, create: bool) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "选择新项目的空目录" if create else "打开项目工作区"
        )
        if path:
            self.open_workspace(path, create=create)

    def open_workspace(self, path: str, *, create: bool = False) -> None:
        if self._workspace or self._busy:
            return
        self._start()

        def opened(reply: StorageReply) -> None:
            self._workspace = path
            self._storage(StorageCommand("documents"), self._list_documents)

        self._storage(StorageCommand("create" if create else "open", path=path), opened)

    def _list_documents(self, reply: StorageReply) -> None:
        self.documents.clear()
        self.documents.addItem("选择已保存拼图项目", "")
        if isinstance(reply.value, tuple):
            for document in reply.value:
                if isinstance(document, DraftSnapshot) and document.tool_id == "wb-figure":
                    self.documents.addItem(document.document_id, document.document_id)
        self._done("项目工作区已就绪；批量导入原图或选择已保存项目。")

    def _choose_import(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择同一项目的原始 TIFF", "", "TIFF (*.tif *.tiff)"
        )
        if paths:
            self.import_images(tuple(paths))

    def new_project(self) -> None:
        if self._busy or not self._workspace:
            return

        def create() -> None:
            template = self.view.project().template
            project = WBFigureProject(project_id=uuid4().hex, template=template)
            self.view.set_project(project)
            self._project_results = ()
            self._loaded_ocr = None
            self.view.generation += 1
            self._saved_revision = None
            self.view.status.setText("已复用模板新建项目；导入下一批原图。")

        self.save(after=create)

    def import_images(self, paths: tuple[str, ...]) -> None:
        if self._busy or not self._workspace:
            return
        try:
            self.view.project()
        except ValueError as error:
            self._error(str(error))
            return
        self._start()
        pending = list(paths)
        duplicates = 0
        errors: list[str] = []
        generation = self.view.generation

        def next_image() -> None:
            if (
                not pending
                or self._cancellation.is_set()
                or self._closing
                or generation != self.view.generation
            ):
                self._done(
                    f"导入结束；跳过 {duplicates} 个重复原图，{len(errors)} 个失败。"
                    + ("; ".join(errors[:3]) if errors else "请填写名称并复核裁剪。")
                )
                return
            if len(self.view.project().rows) >= 512:
                self._done(f"项目已达 512 行；剩余 {len(pending)} 张未导入，请另建项目。")
                return
            path = pending.pop(0)
            self.view.status.setText(f"正在导入 {Path(path).name}；剩余 {len(pending)} 张")

            def previewed(reply: WBReply) -> None:
                nonlocal duplicates
                if generation != self.view.generation:
                    next_image()
                    return
                if not isinstance(reply.value, PreviewRaster):
                    errors.append(f"{Path(path).name}: {reply.error or '图像预览无效'}")
                    next_image()
                    return
                raster = reply.value
                current = self.view.project()
                if any(row.source and row.source.sha256 == raster.sha256 for row in current.rows):
                    duplicates += 1
                    next_image()
                    return

                def imported(reply: StorageReply) -> None:
                    if not isinstance(reply.value, AssetRef):
                        self._error("原图资产无效")
                        return
                    asset = reply.value

                    def resolved(reply: StorageReply) -> None:
                        nonlocal generation
                        if not isinstance(reply.value, str):
                            self._error("原图路径无效")
                            return
                        if generation != self.view.generation:
                            next_image()
                            return
                        self._paths[asset.sha256] = reply.value
                        row = FigureRow(
                            row_id=uuid4().hex,
                            source=asset,
                            filename=Path(path).name,
                            width=raster.width,
                            height=raster.height,
                            bit_depth=16 if raster.bit_depth == 16 else 8,
                            figure=current.figure_order[-1] if current.figure_order else "Fig1",
                        )
                        self.view.set_project(
                            current.model_copy(
                                update={
                                    "rows": (*current.rows, row),
                                    "figure_order": current.figure_order or ("Fig1",),
                                }
                            )
                        )
                        self.view.generation += 1
                        generation = self.view.generation
                        self.view.install_thumbnail(raster)
                        next_image()

                    self._storage(StorageCommand("asset", asset=asset), resolved)

                self._storage(
                    StorageCommand("import", path=path, source_sha256=raster.sha256), imported
                )

            self._wb(WBJob("preview", path=path, preview_edge=128), previewed, accept_errors=True)

        next_image()

    def select_source(self, row_id: str) -> None:
        if self._busy or self._closing:
            return
        try:
            row = next(r for r in self.view.project().rows if r.row_id == row_id)
        except (ValueError, StopIteration) as error:
            self._error(str(error))
            return
        asset = row.source
        if asset is None:
            self.view.canvas.set_image(PreviewRaster("", 0, 0, 0, 0, b"", 0, ()))
            self.view.canvas.set_lanes(())
            return
        self._start()

        def previewed(reply: WBReply) -> None:
            if not isinstance(reply.value, PreviewRaster) or reply.value.sha256 != asset.sha256:
                self._error("原图来源不一致")
                return
            self.view.set_source_preview(reply.value)
            self._done(
                f"{row.filename} · {row.width} × {row.height} · {row.bit_depth} 位；"
                "框选时请排除 Marker。"
            )

        self._wb(WBJob("preview", path=self._paths[asset.sha256]), previewed)

    def save(self, after: Callable[[], None] | None = None) -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project(
                0 if self._saved_revision is None else self._saved_revision + 1
            )
        except ValueError as error:
            self._error(str(error))
            return
        generation = self.view.generation
        self._start()

        def encoded(reply: WBReply) -> None:
            if not isinstance(reply.value, bytes):
                self._error("项目编码无效")
                return

            def saved(reply: StorageReply) -> None:
                self._saved_revision = project.revision
                self._saved_generation = generation
                if generation != self.view.generation:
                    self._done("旧修订已保存，当前编辑保留；请重新执行操作")
                    return
                self.view.set_project(project)
                if self.documents.findData(project.project_id) < 0:
                    self.documents.addItem(project.project_id, project.project_id)
                self._busy = False
                self._controls()
                self.view.status.setText("项目已保存，原图和模板可重新打开。")
                if after:
                    after()
                elif self._closing:
                    self._finish_close()

            self._storage(
                StorageCommand(
                    "save",
                    document_id=project.project_id,
                    tool_id="wb-figure",
                    revision=project.revision,
                    previous_revision=self._saved_revision,
                    data=reply.value,
                ),
                saved,
            )

        self._wb(WBJob("encode", document=project), encoded)

    def _choose_document(self, index: int) -> None:
        document_id = self.documents.itemData(index)
        if isinstance(document_id, str) and document_id:
            self.load_document(document_id)

    def load_document(self, document_id: str) -> None:
        if self._busy:
            return
        if (
            self.view.generation != self._saved_generation
            and QMessageBox.question(self, "未保存修改", "放弃当前未保存修改并切换项目？")
            != QMessageBox.StandardButton.Yes
        ):
            return
        self._start()

        def loaded(reply: StorageReply) -> None:
            def decoded(reply: WBReply) -> None:
                if not isinstance(reply.value, WBFigureProject):
                    self._error("项目文档无效")
                    return
                project = reply.value
                assets = {asset.sha256: asset for asset in project_assets(project)}
                primary = {asset.sha256 for asset in project_assets(project, history=False)}
                pending = list(assets.values())
                resolved_paths: dict[str, str] = {}

                def next_asset() -> None:
                    if not pending:
                        self._paths = resolved_paths
                        self.view.set_project(project)
                        self._saved_revision = project.revision
                        self._saved_generation = self.view.generation
                        self._project_results = ()
                        self._loaded_ocr = None
                        if isinstance(project, WBRestoredProject):
                            self._restore_project_evidence(project)
                        elif isinstance(project, WBAnalysisProject):
                            analysis_project = project

                            def measurements() -> None:
                                self._start_measurements(
                                    analysis_project,
                                    tuple(p.row_id for p in analysis_project.analyses),
                                    restore=True,
                                )

                            if isinstance(project, WBProjectOCR) and project.ocr is not None:
                                self._start_ocr(project, restore=True, after=measurements)
                            else:
                                measurements()
                        else:
                            self._done("项目已恢复，原图资产已校验。选择一行查看原图。")
                        return
                    asset = pending.pop(0)

                    def resolved(reply: StorageReply) -> None:
                        if reply.error_code and asset.sha256 not in primary:
                            next_asset()
                            return
                        if not isinstance(reply.value, str):
                            self._error("资产路径无效")
                            return
                        resolved_paths[asset.sha256] = reply.value
                        next_asset()

                    self._storage(
                        StorageCommand("asset", asset=asset),
                        resolved,
                        accept_errors=asset.sha256 not in primary,
                    )

                next_asset()

            self._wb(WBJob("figure_document", data=reply.data), decoded)

        self._storage(StorageCommand("load", document_id=document_id), loaded)

    def _restore_project_evidence(self, project: WBRestoredProject) -> None:
        def collected(evidence: tuple[ArchiveRunEvidence, ...]) -> None:
            self._archive_session = None
            if self._closing or self._cancellation.is_set():
                self._done("历史证据加载已取消；新工作区已保存。")
                return

            def verified(reply: WBReply) -> None:
                if self._closing or self._cancellation.is_set():
                    self._done("历史证据加载已取消。")
                elif reply.error or not isinstance(reply.value, RestoredProjectResults):
                    self._error(reply.error or "历史证据读取失败")
                else:
                    self._project_results, self._loaded_ocr = reply.value.results, reply.value.ocr
                    self._busy = False
                    self.refresh_project_table(
                        f"项目已恢复；{len(reply.value.errors)} 条运行证据不可用。"
                        "历史来源见结果表。"
                    )

            self._wb(
                WBJob(
                    "project_evidence",
                    document=project,
                    archive_runs=evidence,
                    cancellation=self._cancellation,
                ),
                verified,
                accept_errors=True,
            )

        session = ProjectArchiveSession(self._store, project, self._cancellation, collected)
        self._archive_session = session
        session.start()

    def _choose_export(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self, "导出新项目归档（原图、裁剪、拼图、结果与记录）", "", "ZIP (*.zip)"
        )
        if destination:
            self.compose(destination)

    def _choose_image_export(self) -> None:
        destination, selected = QFileDialog.getSaveFileName(
            self, "保存新的显示拼图", "", "TIFF (*.tif *.tiff);;PNG (*.png)"
        )
        if destination:
            if not Path(destination).suffix:
                destination += ".png" if selected.startswith("PNG") else ".tif"
            self.export_figure_image(destination)

    def export_figure_image(self, destination: str) -> None:
        if self._busy or not self._workspace or self._closing:
            return

        def saved() -> None:
            if self._closing or self._cancellation.is_set():
                self._done("成图导出已取消，未发布输出")
                return
            try:
                project = self.view.project()
            except ValueError as error:
                self._error(str(error))
                return
            self._start()
            self._export_generation = self.view.generation

            def completed(reply: WBReply) -> None:
                if reply.error:
                    if self._closing or self._cancellation.is_set():
                        self._done("成图导出已取消，未发布输出")
                    else:
                        self._error(reply.error)
                elif isinstance(reply.value, str):
                    self._done("显示拼图已保存：" + reply.value)
                else:
                    self._error("成图导出返回无效结果")

            self._wb(
                WBJob(
                    "figure_image_export",
                    document=project,
                    sources=tuple(FigureSourcePath(sha, path) for sha, path in self._paths.items()),
                    destination=destination,
                    cancellation=self._cancellation,
                ),
                completed,
                accept_errors=True,
            )

        self.save(after=saved)

    def compose(self, destination: str = "") -> None:
        if self._busy or not self._workspace:
            return

        # Persist the exact plan first so exported revision points to a recoverable draft.
        def run() -> None:
            try:
                project = self.view.project()
            except ValueError as error:
                self._error(str(error))
                return
            self._start()
            sources = tuple(FigureSourcePath(sha, path) for sha, path in self._paths.items())

            def completed(reply: WBReply) -> None:
                if isinstance(reply.value, FigureRender):
                    self.view.show_render(reply.value)
                    self._done("预览已生成；未审核行允许预览，正式导出须逐行确认。")
                elif isinstance(reply.value, str):
                    self._done("项目归档已保存（结果缺项见归档内状态表）：" + reply.value)
                else:
                    self._error("拼图结果无效")

            submit = self._export_with_evidence if destination else self._wb
            submit(
                WBJob(
                    "figure_export" if destination else "figure_preview",
                    document=project,
                    sources=sources,
                    destination=destination,
                    cancellation=self._cancellation,
                ),
                completed,
            )

        self.save(after=run)

    def _choose_font(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "导入支持标签文字的字体", "", "Fonts (*.ttf *.otf *.ttc)"
        )
        if path:
            self.import_font(path)

    def import_font(self, path: str) -> None:
        if self._busy:
            return
        try:
            project = self.view.project()
        except ValueError as error:
            self._error(str(error))
            return
        self._start()

        def fingerprinted(reply: WBReply) -> None:
            if not isinstance(reply.value, str):
                self._error("字体摘要无效")
                return

            def imported(reply: StorageReply) -> None:
                if not isinstance(reply.value, AssetRef):
                    self._error("字体资产无效")
                    return
                asset = reply.value

                def resolved(reply: StorageReply) -> None:
                    if not isinstance(reply.value, str):
                        self._error("字体路径无效")
                        return
                    self._paths[asset.sha256] = reply.value
                    self.view.set_project(
                        project.model_copy(
                            update={"template": project.template.model_copy(update={"font": asset})}
                        )
                    )
                    self.view.generation += 1
                    self._done("字体已导入，随项目保存。")

                self._storage(StorageCommand("asset", asset=asset), resolved)

            self._storage(StorageCommand("import", path=path, source_sha256=reply.value), imported)

        self._wb(WBJob("font_digest", path=path), fingerprinted)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.resources_closed:
            event.accept()
            return
        event.ignore()
        self._closing = True
        self.cancel()
        self._controls()
        if not self._busy:
            self._finish_close()

    def _finish_close(self) -> None:
        if self._shutting:
            return
        if self._workspace and self._saved_generation != self.view.generation:
            self.save()
            return
        self._shutting = True
        self._store.shutdown()
        self._background.shutdown()

    def _store_stopped(self) -> None:
        self._store_closed = True
        self._both_stopped()

    def _background_stopped(self) -> None:
        self._background_closed = True
        self._both_stopped()

    def _both_stopped(self) -> None:
        if self.resources_closed:
            self.closed.emit()
            self.close()
