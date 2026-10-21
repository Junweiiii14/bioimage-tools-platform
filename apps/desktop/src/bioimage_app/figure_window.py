"""Explicit assembly of WB project review, immutable asset storage and background rendering."""

from collections.abc import Callable
from pathlib import Path
from threading import Event
from uuid import uuid4

from PySide6.QtCore import QSettings, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from tool_contracts.api import AssetRef, DraftSnapshot
from wb_tool.api import (
    ArchiveRunEvidence,
    CropSuggestion,
    FigurePNG,
    FigureRender,
    FigureRow,
    FigureSourcePath,
    LoadedFigureTemplate,
    LoadedProjectOCR,
    LoadedProjectResult,
    ManualQuantTarget,
    MetadataBook,
    PreviewRaster,
    ProjectDerivedTables,
    ProjectOCRState,
    ProjectTableSnapshot,
    RestoredProjectResults,
    ReturnedCrop,
    WBAnalysisProject,
    WBFigureProject,
    WBIntakeProject,
    WBIntakeWorkflowProject,
    WBJob,
    WBLayoutProject,
    WBProjectOCR,
    WBReply,
    WBRestoredProject,
    WBReviewProject,
    analysis_is_current,
    create_figure_project_view,
    create_intake,
    create_wb_background,
    initial_composition,
    prepare_project_analyses,
    prepare_workbench_revision,
    project_assets,
    project_with_ocr,
    record_crop_suggestion,
    recover_intake_workflow,
    source_import_labels,
    with_figure_layout,
    workbench_project_digest,
)

from bioimage_app.instrument_intake import InstrumentIntakeSession
from bioimage_app.intake_workflow import IntakeWorkflowSession
from bioimage_app.project_archive import ProjectArchiveSession
from bioimage_app.project_entry import default_project_parent
from bioimage_app.project_measurements import ProjectBatchCompletion, ProjectMeasurementSession
from bioimage_app.project_ocr import ProjectOCRCompletion, ProjectOCRSession
from bioimage_app.project_restore import ArchiveRestoreJob, ArchiveRestoreResult
from bioimage_app.project_start import ProjectSelectionJob
from bioimage_app.source_origins import SourceOrigins
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.workbench_motion import NavigationMotion, PanelReveal
from bioimage_app.workbench_style import apply_workbench_theme


class FigureProjectWindow(QMainWindow):
    @property
    def project_results(self) -> tuple[LoadedProjectResult, ...]:
        """Verified immutable results for presentation adapters."""
        return self._project_results

    closed = Signal()
    workspace_opened = Signal(str)
    measurement_progress = Signal(str)
    intake_stage_committed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WB 自动化 · BioImage")
        self.resize(1440, 900)
        self.setObjectName("wbProjectWindow")
        self._apply_theme()
        self.view = create_figure_project_view()
        self.surface = QStackedWidget()
        self.surface.addWidget(self.view)
        self.setCentralWidget(self.surface)
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
        self.source_origins = SourceOrigins()
        self._paths: dict[str, str] = {}
        self._saved_revision: int | None = None
        self._saved_generation = 0
        self._save_on_close = True
        self._transition_pending = False
        self._busy = False
        self.operation_error = ""
        self.quant_progress: dict[str, object] = {}
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
        self._selection_job: ProjectSelectionJob | None = None
        self._pending_project_paths: list[Path] = []
        self._pending_project_automatic = True
        self._pending_project_intake = False
        self.intake = InstrumentIntakeSession(self)
        self.intake_workflow = IntakeWorkflowSession(self)
        self._auto_save = QTimer(self)
        self._auto_save.setSingleShot(True)
        self._auto_save.setInterval(700)
        self._auto_save.timeout.connect(self._save_idle_edits)
        self._export_generation: int | None = None
        self._ocr_refresh_pending = False
        self._ocr_refresh_timer = QTimer(self)
        self._ocr_refresh_timer.setSingleShot(True)
        self._ocr_refresh_timer.timeout.connect(self.refresh_ocr_table)
        bar = QToolBar("项目")
        bar.setMovable(False)
        self.addToolBar(bar)
        brand = QLabel("BioImage  /  WB")
        brand.setObjectName("appBrand")
        bar.addWidget(brand)
        self.create_button = QPushButton("选择 WB 原图并开始")
        self.open_button = QPushButton("打开已有项目")
        self.restore_button = QPushButton("从 ZIP 恢复")
        self.import_button = QPushButton("添加原图")
        self.save_button = QPushButton("保存项目")
        self.new_button = QPushButton("复用模板新建项目")
        self.cancel_button = QPushButton("取消处理")
        self.documents = QComboBox()
        self.documents.setMinimumWidth(160)
        self.documents.setParent(self)
        self.documents.hide()
        self.save_state = QLabel("尚未开始")
        self.save_state.setObjectName("saveState")
        bar.addWidget(self.save_state)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bar.addWidget(spacer)
        bar.addWidget(self.import_button)
        self.cancel_action = bar.addWidget(self.cancel_button)
        # Keep the existing buttons as command/state owners for host contracts and tests.
        self.project_menu = QMenu("项目", self)
        self.project_actions: list[tuple[QAction, QPushButton]] = []
        for button in (
            self.create_button,
            self.open_button,
            self.restore_button,
            self.new_button,
            self.save_button,
        ):
            button.setParent(self)
            button.hide()
            action = self.project_menu.addAction(button.text())
            action.triggered.connect(button.click)
            self.project_actions.append((action, button))
        self.project_menu_button = QToolButton()
        self.project_menu_button.setText("项目")
        self.project_menu_button.setMenu(self.project_menu)
        self.project_menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        bar.addWidget(self.project_menu_button)
        self.documents.setMaximumWidth(280)
        self.documents.setAccessibleName("当前工作区内的项目")
        self.export_button = QPushButton("查看结果")
        bar.addWidget(self.export_button)
        self.motion_settings = QSettings("BioImageTools", "Motion")
        self.motion = NavigationMotion(self.view.steps, self.motion_settings)
        self.panel_motion = [
            PanelReveal(panel, self.motion)
            for panel in (
                self.view.source_metadata,
                self.view.suggestions,
                self.view.analysis.advanced,
            )
        ]
        for text, shortcut, callback in (
            ("撤销图上调整", QKeySequence.StandardKey.Undo, self.view.undo_review),
            ("重做图上调整", QKeySequence.StandardKey.Redo, self.view.redo_review),
        ):
            action = self.project_menu.addAction(text)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
        self.reduce_motion_action = self.project_menu.addAction("减少动效")
        self.reduce_motion_action.setCheckable(True)
        self.reduce_motion_action.setChecked(self.motion.reduced())
        self.reduce_motion_action.toggled.connect(self._set_reduced_motion)
        self.task_progress = QProgressBar()
        self.task_progress.setObjectName("taskProgress")
        self.task_progress.setTextVisible(False)
        self.task_progress.setRange(0, 0)
        self.task_progress.setFixedWidth(72)
        self.progress_action = bar.addWidget(self.task_progress)
        self.welcome = QWidget()
        self.welcome.setObjectName("welcomePage")
        welcome_layout = QVBoxLayout(self.welcome)
        welcome_layout.setContentsMargins(48, 32, 48, 32)
        welcome_layout.setSpacing(12)
        title = QLabel("开始一个 WB 实验项目")
        title.setObjectName("welcomeTitle")
        welcome_layout.addWidget(title)
        description = QLabel("选择 WB 原图即可开始。项目文件夹由软件自动建立，原图保持不变。")
        description.setWordWrap(True)
        welcome_layout.addWidget(description)
        workflow = QLabel("选择原图   →   自动识别与测量   →   复核异常   →   导出结果")
        workflow.setObjectName("welcomeWorkflow")
        workflow.setWordWrap(True)
        welcome_layout.addWidget(workflow)
        welcome_layout.addSpacing(12)
        self.welcome_buttons: list[tuple[QPushButton, QPushButton]] = []
        for label, owner in (
            ("选择 WB 原图并开始…", self.create_button),
            ("打开已有项目…", self.open_button),
            ("从完整项目 ZIP 恢复…", self.restore_button),
        ):
            button = QPushButton(label)
            button.setMaximumWidth(300)
            button.clicked.connect(owner.click)
            welcome_layout.addWidget(button)
            self.welcome_buttons.append((button, owner))
        self.welcome_status = QLabel("选择原图开始新项目，或打开已有项目继续。")
        self.welcome_status.setWordWrap(True)
        welcome_layout.addWidget(self.welcome_status)
        self.retry_location_button = QPushButton("更换项目保存位置并重试…")
        self.retry_location_button.setMaximumWidth(300)
        self.retry_location_button.clicked.connect(self._retry_project_location)
        self.retry_location_button.hide()
        welcome_layout.addWidget(self.retry_location_button)
        welcome_layout.addStretch()
        self.surface.addWidget(self.welcome)
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
        self.view.template_export_requested.connect(self._choose_template_export)
        self.view.template_import_requested.connect(self._choose_template_import)
        self.view.detection_requested.connect(self.detect_crops)
        from bioimage_app.automatic_workflow import AutomaticWorkflow

        self.automatic = AutomaticWorkflow(self)
        self.output_button = QPushButton("打开结果文件夹")
        self.output_button.setEnabled(False)
        self.output_button.setParent(self)
        self.output_button.hide()
        self.output_action = self.project_menu.addAction("打开最近输出文件夹")
        self.output_action.setEnabled(False)
        self.output_action.triggered.connect(self.output_button.click)
        self.output_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.automatic.last_output_path))
        )
        self.view.output_folder_requested.connect(self.output_button.click)
        self.automatic.finished.connect(self._automatic_output_ready)
        self.export_button.clicked.connect(lambda: self.view.show_section("export"))
        self.view.automatic_requested.connect(self.automatic.analyze)
        self.view.automatic_export_requested.connect(self.automatic.choose_export)
        self.view.import_directory_requested.connect(self.automatic.choose_directory)
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
        self.view.changed.connect(self._schedule_save)
        self.view.steps.currentRowChanged.connect(self._mode_changed)
        self.view.changed.connect(self._cancel_stale_export)
        for widget in self.findChildren(QWidget):
            widget.setPalette(self.palette())
        self.view.status.setText("选择原图开始新项目，或打开已有项目继续。")
        self._controls()

    def _apply_theme(self) -> None:
        apply_workbench_theme(self)

    def _set_reduced_motion(self, reduced: bool) -> None:
        self.motion_settings.setValue("reduce_motion", reduced)
        self.motion.move()

    def _schedule_save(self) -> None:
        if self._workspace and not self._closing and not self._transition_pending:
            self.save_state.setText("待保存…")
            self._auto_save.start()

    def _save_idle_edits(self) -> None:
        if self._closing or self._transition_pending or not self._workspace:
            return
        if self._busy:
            self._auto_save.start()
            return
        if self.view.generation != self._saved_generation:
            self.save(after=self._refresh_edited_results)

    def _mode_changed(self, index: int) -> None:
        if index == 1:
            QTimer.singleShot(0, self._preview_if_needed)

    def _preview_if_needed(self) -> None:
        if self._busy or self._closing or not self._workspace:
            return
        if self.view.steps.currentRow() != 1 or not self.view.preview_label.full_pixmap.isNull():
            return
        try:
            project = self.view.project()
        except ValueError:
            return
        if any(row.roi for row in project.rows):
            self.compose()

    def _refresh_edited_results(self) -> None:
        """Recompute edited geometry or explicit bounds, never overwrite explicit bounds."""
        if self._busy or self._closing or self._cancellation.is_set():
            return
        project = self.view.project()
        plans = (
            {p.row_id: p for p in project.analyses}
            if isinstance(project, WBAnalysisProject)
            else {}
        )
        geometry = tuple(
            row.row_id
            for row in project.rows
            if row.source
            and row.roi
            and (
                row.row_id not in plans
                or plans[row.row_id].crop != row.roi
                or len(plans[row.row_id].request.lanes) != row.lane_count
                or plans[row.row_id].empty_lanes != row.empty_lanes
            )
        )
        if geometry:
            self.automatic.analyze(row_ids=geometry, publish_output=False)
            return
        edited = tuple(
            plan.row_id
            for plan in plans.values()
            if plan.run is None and analysis_is_current(project, plan)
        )
        if edited:
            self.analyze_project(row_ids=edited, after=self.compose)
        else:
            self._preview_if_needed()

    def _retry_project_location(self) -> None:
        parent = QFileDialog.getExistingDirectory(self, "选择项目保存位置（软件自动创建子文件夹）")
        if parent and self._pending_project_paths:
            self.start_project_from_images(
                self._pending_project_paths,
                Path(parent),
                automatic=self._pending_project_automatic,
                intake=self._pending_project_intake,
            )

    def start_project_from_images(
        self,
        paths: list[Path],
        project_parent: Path | None = None,
        *,
        automatic: bool = True,
        intake: bool = False,
    ) -> None:
        """Select originals first; decode before any workspace or recent entry is created."""
        if not paths or self._busy or self._workspace or self._closing:
            return
        if intake:
            automatic = False
        self._pending_project_paths = list(paths)
        self._pending_project_automatic = automatic
        self._pending_project_intake = intake
        self.retry_location_button.hide()
        self._start()
        self.view.status.setText("正在查找 WB 原图…")
        self.welcome_status.setText("正在查找 WB 原图…")
        job = ProjectSelectionJob(
            paths,
            project_parent or default_project_parent(),
            self._cancellation,
            automatic=automatic,
        )
        self._selection_job = job

        def scanned() -> None:
            selection = job.result
            self._selection_job = None
            job.deleteLater()
            if self._closing or self._cancellation.is_set():
                self._done("已取消，未创建项目。")
                return
            if selection.error or selection.destination is None:
                self.retry_location_button.show()
                self._error(selection.error or "未能准备项目保存位置")
                return
            pending = list(selection.paths)
            failures: list[str] = []

            def validate_next() -> None:
                if self._closing or self._cancellation.is_set():
                    self._done("已取消，未创建项目。")
                    return
                if not pending:
                    self._error("没有可读取的 WB 原图；未创建项目。" + "；".join(failures[:3]))
                    return
                source = pending.pop(0)
                self.welcome_status.setText(f"正在核验原图：{source.name}")

                def checked(reply: WBReply) -> None:
                    if self._closing or self._cancellation.is_set():
                        self._done("已取消，未创建项目。")
                        return
                    if not isinstance(reply.value, PreviewRaster):
                        failures.append(f"{source.name}：{reply.error or '无法读取'}")
                        validate_next()
                        return

                    def created(_reply: StorageReply) -> None:
                        self._workspace = str(selection.destination)
                        empty = WBFigureProject(project_id=uuid4().hex, name=selection.name)
                        self.view.set_project(create_intake(empty) if intake else empty)
                        self.automatic.discovery_report = selection.discovery_report
                        self.workspace_opened.emit(self._workspace)
                        self._busy = False
                        if self._closing or self._cancellation.is_set():
                            self._done("创建后已取消；项目可稍后继续。")
                            return
                        if intake:
                            self.intake.import_paths(
                                selection.paths,
                                tuple(
                                    p.resolve() if p.is_dir() else p.resolve().parent for p in paths
                                ),
                            )
                        else:
                            self.import_images(
                                tuple(str(p) for p in selection.paths), automatic=automatic
                            )

                    self._storage(
                        StorageCommand("create", path=str(selection.destination)), created
                    )

                self._wb(
                    WBJob("preview", path=str(source), preview_edge=128),
                    checked,
                    accept_errors=True,
                )

            validate_next()

        job.finished.connect(scanned)
        job.start()

    def cancel(self) -> None:
        self._auto_save.stop()
        self._cancellation.set()
        self._ocr_refresh_timer.stop()
        self._ocr_refresh_pending = False
        self.automatic.cancel()
        self.intake_workflow.cancel()
        if self._measurement_session:
            self._measurement_session.cancel()
        if self._ocr_session:
            self._ocr_session.cancel()

    def _automatic_output_ready(self, path: str) -> None:
        self.output_button.setEnabled(True)
        self.output_action.setEnabled(True)
        self.output_button.setToolTip(path)
        self.view.set_output_location(path)

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

    def import_metadata(
        self, path: str, *, received: Callable[[MetadataBook], None] | None = None
    ) -> None:
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
                if received is not None:
                    received(reply.value)
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
        originals = {row.source.sha256: row.source for row in project.rows if row.source}
        if isinstance(project, WBIntakeProject):
            originals.update(
                (source.asset.sha256, source.asset) for source in project.intake.sources
            )
        sources = {
            digest: self._paths.get(digest, "")
            for digest in originals
            if not self.view.has_thumbnail(digest)
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

    @property
    def current_draft_saved(self) -> bool:
        return self._saved_revision is not None and self.view.generation == self._saved_generation

    @property
    def advanced_evidence_identity(self) -> tuple[object, ...]:
        return (
            self.view.project().project_id,
            self.view.generation,
            id(self._project_results),
            id(self._loaded_ocr),
        )

    def read_advanced_tables(self, finished: Callable[[ProjectDerivedTables], None]) -> None:
        """Bounded background derivation for the web surface, using verified run objects."""
        if self._busy or not self._workspace or self._closing:
            raise ValueError("当前项目不可读取结果表")
        project = self.view.project()
        generation = self.view.generation
        self._start()

        def received(reply: WBReply) -> None:
            if self._closing or self._cancellation.is_set() or generation != self.view.generation:
                self._done("结果表读取已取消；当前编辑保留。")
            elif not isinstance(reply.value, ProjectDerivedTables):
                self._error(reply.error or "结果表读取失败")
            else:
                finished(reply.value)
                self._done("结果表已从已核验记录刷新。")

        self._wb(
            WBJob(
                "project_derived_tables",
                document=project,
                project_results=self._project_results,
                project_ocr_result=self._loaded_ocr,
                cancellation=self._cancellation,
            ),
            received,
            accept_errors=True,
        )

    def _queue_ocr_refresh(self) -> None:
        self._ocr_refresh_pending = True
        self._ocr_refresh_timer.start(150)

    def refresh_ocr_table(
        self, message: str = "关联与归一化结果已刷新", after: Callable[[], None] | None = None
    ) -> None:
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
            if self._closing or self._cancellation.is_set():
                self._done("结果表刷新已取消；后续操作未执行。")
                return
            if generation == self.view.generation and isinstance(reply.value, ProjectDerivedTables):
                self.view.ocr.result_view.show_cells(reply.value.ocr_cells)
                self.view.normalization.result_view.show_snapshot(reply.value.normalization)
                self._done(message)
                if after and not self._closing and not self._cancellation.is_set():
                    after()
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
        after: Callable[[], None] | None = None,
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
                            prepare_workbench_revision(
                                project, expected_digest=workbench_project_digest(project)
                            ),
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
                        self.recognize_project(after=after)
                    else:
                        self._done("拼图已导入；识别Fig/行名后逐行关联原图。")

                self._wb(WBJob("ocr_preview", path=path), previewed, accept_errors=True)

            self._storage(StorageCommand("asset", asset=asset), resolved)

        self._storage(command, imported)

    def recognize_composed_figure(self, *, after: Callable[[], None] | None = None) -> None:
        if self._busy or not self._workspace:
            return
        try:
            current = self.view.project()
            prepare_workbench_revision(current, expected_digest=workbench_project_digest(current))
        except ValueError as error:
            self._error(str(error))
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
                    after=after,
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

    def recognize_project(self, *, after: Callable[[], None] | None = None) -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project()
            if not isinstance(project, WBProjectOCR) or project.ocr is None:
                raise ValueError("请先导入独立拼图")
            prepare_workbench_revision(project, expected_digest=workbench_project_digest(project))
        except ValueError as error:
            self._error(str(error))
            return

        def saved() -> None:
            if self._closing or self._cancellation.is_set():
                self._done("识别已取消，之前关联保留")
                return
            project = self.view.project()
            assert isinstance(project, WBProjectOCR)
            self._start_ocr(project, after=after)

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
            if self._closing or self._cancellation.is_set():
                self._done("OCR已停止，之前关联保留；已提交运行仍保留在历史。")
                return
            if generation != self.view.generation:
                self._done("项目已修改，OCR结果仅保留在历史，未覆盖编辑。")
                return
            if restore:
                self._loaded_ocr = completion.loaded
                if completion.error:
                    self.view.ocr.note.setText("OCR结果不可用：" + completion.error)

                def previewed(reply: WBReply) -> None:
                    if (
                        self._closing
                        or self._cancellation.is_set()
                        or generation != self.view.generation
                    ):
                        self._done("OCR载入已停止，当前编辑保留。")
                        return
                    if isinstance(reply.value, PreviewRaster):
                        self.view.ocr.set_preview(reply.value)
                    self._busy = False
                    if after:
                        after()
                    else:
                        self._done("OCR原文已校验" if completion.loaded else "OCR原文未载入")

                self._wb(WBJob("ocr_preview", path=self._paths[ocr.source.sha256]), previewed)
            elif completion.loaded is None:
                message = "识别未更新，之前关联保留：" + (completion.error or completion.state)
                # Do not start a second operation that can erase this terminal failure.
                self._error(message)
            else:
                loaded = completion.loaded

                def installed(reply: WBReply) -> None:
                    if self._closing or self._cancellation.is_set():
                        self._done("OCR已停止，之前关联保留；已提交运行仍保留在历史。")
                        return
                    if generation != self.view.generation:
                        self._done("项目已修改，OCR建议未覆盖编辑")
                        return
                    if not isinstance(reply.value, WBProjectOCR):
                        self._error("OCR建议生成失败")
                        return
                    candidate = reply.value
                    self._busy = False

                    def saved() -> None:
                        self._loaded_ocr = loaded
                        if self._closing:
                            self._done("OCR识别已保存")
                        else:
                            self.refresh_ocr_table(
                                "OCR完成；请校正名称、关联原图并确认。", after=after
                            )

                    def install(current: WBFigureProject) -> WBProjectOCR:
                        if (
                            not isinstance(current, WBProjectOCR)
                            or current.project_id != project.project_id
                            or current.ocr != project.ocr
                        ):
                            raise ValueError("OCR来源或关联已改变，候选不能覆盖当前草稿")
                        return type(candidate).model_validate(
                            {**dict(candidate), "revision": current.revision}
                        )

                    self.save(
                        after=saved,
                        transform=install,
                        install_guard=lambda: (
                            not self._closing
                            and not self._cancellation.is_set()
                            and generation == self.view.generation
                        ),
                    )

                self._wb(
                    WBJob(
                        "project_ocr_install",
                        document=prepare_workbench_revision(
                            project, expected_digest=workbench_project_digest(project)
                        ),
                        project_ocr_result=loaded,
                    ),
                    installed,
                )

        def safely_completed(completion: ProjectOCRCompletion) -> None:
            try:
                completed(completion)
            except (ValueError, TypeError, OSError) as error:
                self._error(str(error))

        session.finished.connect(safely_completed)
        session.start(project, self._workspace, restore=restore)
        if self._closing:
            session.cancel()

    def analyze_fig_sheet(self, row_id: str) -> None:
        """Partition a sheet off-thread; measure each accepted row through durable runs."""
        if self._busy or self._closing or not self._workspace:
            return
        project = self.view.project()
        row = next((r for r in project.rows if r.row_id == row_id), None)
        path = self.source_paths.get(row.source.sha256) if row and row.source else None
        if path is None:
            raise ValueError("原图资产不可用")
        generation = self.view.generation
        old_ids = {r.row_id for r in project.rows}
        self._start()
        self.quant_progress = {"phase": "partition", "label": "识别 Fig、蛋白与泳道"}

        def prepared(reply: WBReply) -> None:
            from wb_tool.api import WBPartitionProject

            if self._closing or self._cancellation.is_set():
                self._done("Fig识别已取消；原项目保留")
                return
            if (
                generation != self.view.generation
                or self.view.project().project_id != project.project_id
            ):
                self._done("参数已改变，旧Fig识别未覆盖当前草稿")
                return
            if reply.error or not isinstance(reply.value, WBPartitionProject):
                self._error(reply.error or "Fig识别结果无效")
                return
            installed = reply.value
            self.view.set_project(installed)
            self.view.generation += 1
            first = next((i for i, r in enumerate(installed.rows) if r.row_id not in old_ids), 0)
            self.view.table.setCurrentCell(first, 0)
            self._busy = False
            ids = tuple(p.row_id for p in installed.analyses if p.row_id not in old_ids)
            if ids:
                self.analyze_project(row_ids=ids)
            else:
                self.save()
                self._done("Fig已分组，泳道定位不足，请手动框选")

        self._wb(
            WBJob(
                "quant_fig",
                path=path,
                document=project,
                row_id=row_id,
                cancellation=self._cancellation,
            ),
            prepared,
            accept_errors=True,
        )

    def analyze_manual_target(self, target: ManualQuantTarget) -> None:
        """Configure in the background, then use normal durable measurement runs."""
        if self._busy or self._closing or not self._workspace:
            return
        project = self.view.project()
        path = self.source_paths.get(target.source_sha256)
        if not path:
            raise ValueError("原图资产不可用，无法配置测量区域")
        generation = self.view.generation
        self._start()

        def configured(reply: WBReply) -> None:
            if self._closing or self._cancellation.is_set():
                self._done("独立灰度配置已取消；原项目和历史结果保留")
                return
            if (
                generation != self.view.generation
                or self.view.project().project_id != project.project_id
            ):
                self._done("项目或参数已改变，旧测量目标未覆盖当前编辑")
                return
            if reply.error or not isinstance(reply.value, WBAnalysisProject):
                self._error(reply.error or "测量目标配置结果无效")
                return
            if reply.value != project:
                self.view.set_project(reply.value)
                self.view.generation += 1
            self._project_results = tuple(
                item for item in self._project_results if item.row_id != target.roi.lane_id
            )
            self._busy = False
            self.analyze_project(row_ids=(target.roi.lane_id,))

        self._wb(
            WBJob(
                "quant_target",
                path=path,
                document=project,
                manual_target=target,
                cancellation=self._cancellation,
            ),
            configured,
            accept_errors=True,
        )

    def replan_quant_lane(self, row_id: str) -> None:
        """Re-detect changed lane geometry off the GUI thread, then commit measurements."""
        project = self.view.project()
        row = next((r for r in project.rows if r.row_id == row_id), None)
        if self.operation_busy or not row or not row.source:
            return
        path = self.source_paths.get(row.source.sha256)
        if not path:
            self._error("原图资产不可用，无法重新规划泳道")
            return
        generation = self.view.generation
        self._start()

        def replanned(reply: WBReply) -> None:
            if self._closing or self._cancellation.is_set():
                self._done("泳道调整已取消")
                return
            if generation != self.view.generation:
                self._done("参数已改变，旧的泳道规划未覆盖当前编辑")
                return
            if reply.error or not isinstance(reply.value, WBAnalysisProject):
                self._error(reply.error or "泳道规划结果无效")
                return
            self.view.set_project(reply.value)
            self.view.generation += 1
            self._busy = False
            self.analyze_project(row_ids=(row_id,))

        self._wb(
            WBJob(
                "quant_replan",
                path=path,
                document=project,
                row_id=row_id,
                cancellation=self._cancellation,
            ),
            replanned,
            accept_errors=True,
        )

    def analyze_project(
        self,
        all_rows: bool = False,
        *,
        row_ids: tuple[str, ...] | None = None,
        after: Callable[[], None] | None = None,
    ) -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project()
            if not isinstance(project, WBAnalysisProject):
                raise ValueError("请先配置已审核行的定量")
            selected = self.view.selected_row()
            row_ids = (
                row_ids
                if row_ids is not None
                else tuple(
                    p.row_id
                    for p in project.analyses
                    if all_rows or (selected and p.row_id == selected.row_id)
                )
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
            self._start_measurements(current, row_ids, after=after)

        self.save(after=saved)

    def reset_quant_group(self, row_id: str) -> None:
        if self._busy or self._closing or not self._workspace:
            return
        project = self.view.project()
        if not isinstance(project, WBAnalysisProject):
            raise ValueError("请先配置泳道")
        selected = next(r for r in project.rows if r.row_id == row_id)
        row_ids = tuple(r.row_id for r in project.rows if r.figure == selected.figure)
        generation = self.view.generation
        self._start()
        self.view.status.setText("重新规划本组完整峰边界…")
        self.quant_progress = {"phase": "planning", "label": "重新规划本组完整峰边界"}

        def prepared(reply: WBReply) -> None:
            if self._closing or self._cancellation.is_set():
                self._done("重新封底已取消；原参数保留")
                return
            if (
                generation != self.view.generation
                or project.project_id != self.view.project().project_id
            ):
                self._done("项目已改变，旧封底任务未覆盖当前草稿")
                return
            if reply.error or not isinstance(reply.value, WBAnalysisProject):
                self._error(reply.error or "封底结果无效")
                return
            self.view.set_project(reply.value)
            self.view.generation += 1
            self._busy = False
            self.analyze_project(row_ids=row_ids)

        self._wb(
            WBJob(
                "quant_group_reset",
                document=project,
                row_id=row_id,
                sources=tuple(FigureSourcePath(k, v) for k, v in self.source_paths.items()),
                cancellation=self._cancellation,
            ),
            prepared,
            accept_errors=True,
        )

    def _start_measurements(
        self,
        project: WBAnalysisProject,
        row_ids: tuple[str, ...],
        *,
        restore: bool = False,
        after: Callable[[], None] | None = None,
    ) -> None:
        generation = self.view.generation
        self._start()
        session = ProjectMeasurementSession(self._store, self._background, self)
        self._measurement_session = session
        session.progress.connect(self.view.status.setText)
        session.progress.connect(self.measurement_progress)
        session.counts.connect(self._quant_counts)

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
                message = (
                    (
                        "结果核验结束"
                        if restore
                        else (
                            "计算已取消；已完成行保留"
                            if completion.cancelled
                            else "计算结束，部分行未完成"
                        )
                    )
                    + "；"
                    + "；".join(completion.errors[:3])
                )
            if overflow:
                message += "；部分曲线超过 64 MiB 显示预算，结果仍保留在历史"
            self._busy = False
            if not restore:
                self.quant_progress = {
                    **self.quant_progress,
                    "phase": "save",
                    "cancelled": completion.cancelled,
                }
                self.view.set_project(completion.project)
                self.view.generation += 1
                self.save(
                    after=lambda: self.refresh_project_table(
                        message,
                        after=after if not completion.cancelled else None,
                    )
                )
            else:
                self.refresh_project_table(message, after=after)

        session.finished.connect(completed)
        session.start(project, row_ids, self._workspace, restore=restore)
        if self._closing:
            session.cancel()

    def _quant_counts(self, counts: dict[str, object]) -> None:
        self.quant_progress = counts

    def refresh_project_table(
        self, message: str = "项目结果表已刷新", after: Callable[[], None] | None = None
    ) -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project()
        except ValueError as error:
            self._error(str(error))
            return
        generation = self.view.generation
        self._start()
        self.quant_progress = {"phase": "save", "label": "核验已提交结果"}

        def filled(reply: WBReply) -> None:
            # A phase transition is part of the same operation: do not let the
            # derived-table phase's _start() clear a cancellation before after().
            if self._closing or self._cancellation.is_set():
                self._done("结果表刷新已取消；后续操作未执行。")
                return
            if self.view.generation != generation:
                self._done("项目已改变，请重新刷新结果表")
                return
            if not isinstance(reply.value, ProjectTableSnapshot):
                self._error("项目结果表无效")
                return
            self.view.install_results(self._project_results)
            self.view.analysis.show_cells(reply.value.cells)
            self.view.refresh_attention()
            if isinstance(project, WBProjectOCR) and not self._closing:
                self._busy = False
                self.refresh_ocr_table(message, after=after)
            else:
                self._done(message)
                if after and not self._closing and not self._cancellation.is_set():
                    after()

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
        self,
        destination: str,
        *,
        ocr: bool = False,
        normalization: bool = False,
        quant: bool = False,
        ocr_labels: bool | None = None,
    ) -> None:
        if self._busy or not self._workspace:
            return

        def saved() -> None:
            project = self.view.project()
            self._start()
            self._export_with_evidence(
                WBJob(
                    "quant_export"
                    if quant
                    else "project_normalization_export"
                    if normalization
                    else ("project_ocr_export" if ocr else "project_export"),
                    document=project,
                    project_results=self._project_results,
                    project_ocr_result=self._loaded_ocr,
                    ocr_labels=bool(self.view.normalization.result_view.labels.currentIndex())
                    if ocr_labels is None
                    else ocr_labels,
                    destination=destination,
                    cancellation=self._cancellation,
                ),
                lambda reply: self._done("项目结果表已导出：" + str(reply.value)),
            )

        self.save(after=saved)

    def _cancel_stale_export(self) -> None:
        if self._export_generation is not None and self._export_generation != self.view.generation:
            self._cancellation.set()

    def _export_with_evidence(
        self, job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        from dataclasses import replace

        if not isinstance(job.document, WBFigureProject):
            if accept_errors:
                callback(WBReply("", error="缺少导出项目"))
            else:
                self._error("缺少导出项目")
            return
        generation = self.view.generation
        self._export_generation = generation

        def collected(evidence: tuple[ArchiveRunEvidence, ...]) -> None:
            self._archive_session = None
            if self._cancellation.is_set() or self._closing or generation != self.view.generation:
                if accept_errors:
                    callback(WBReply("", error="导出已取消，未发布输出"))
                else:
                    self._done("导出已取消，未发布输出")
                return

            def completed(reply: WBReply) -> None:
                if reply.error and not accept_errors:
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
            if accept_errors:
                callback(WBReply("", error=str(error)))
            else:
                self._error(str(error))

    @property
    def workspace_path(self) -> str:
        return self._workspace

    @property
    def operation_busy(self) -> bool:
        return self._busy

    @property
    def is_closing(self) -> bool:
        return self._closing

    @property
    def cancellation(self) -> Event:
        return self._cancellation

    @property
    def source_paths(self) -> dict[str, str]:
        return dict(self._paths)

    def end_phase(self) -> None:
        self._busy = False

    def begin_operation(self) -> None:
        self._start()

    def finish_operation(self, message: str) -> None:
        self._done(message)

    def fail_operation(self, message: str) -> None:
        self._error(message)

    def submit_tool_job(
        self, job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        self._wb(job, callback, accept_errors=accept_errors)

    def submit_storage_job(
        self,
        command: StorageCommand,
        callback: Callable[[StorageReply], None],
        *,
        accept_errors: bool = False,
    ) -> None:
        self._storage(command, callback, accept_errors=accept_errors)

    def remember_source_path(self, asset: AssetRef, path: str) -> None:
        """Remember a path returned by the verified storage asset resolver."""
        self._paths[asset.sha256] = path

    def create_measurement_session(self) -> ProjectMeasurementSession:
        if self._measurement_session is not None:
            raise ValueError("当前测量尚未退出，不能重复创建")
        session = ProjectMeasurementSession(self._store, self._background, self)
        self._measurement_session = session
        session.progress.connect(self.view.status.setText)
        session.progress.connect(self.measurement_progress)
        session.counts.connect(self._quant_counts)
        return session

    def retire_measurement_session(self, session: ProjectMeasurementSession) -> None:
        if self._measurement_session is session:
            self._measurement_session = None
        session.deleteLater()

    def retain_project_results(self, results: tuple[LoadedProjectResult, ...]) -> None:
        project = self.view.project()
        if not isinstance(project, WBAnalysisProject):
            raise ValueError("结果需要当前项目定量请求")
        candidates = {r.row_id: r for r in (*self._project_results, *results)}
        retained: list[LoadedProjectResult] = []
        size = 0
        for plan in project.analyses:
            result = candidates.get(plan.row_id)
            if (
                result
                and plan.run
                and plan.run.result
                and (
                    result.run_id == plan.run.run_id
                    and result.asset_sha256 == plan.run.result.sha256
                )
            ):
                size += plan.run.result.size_bytes
                if size <= 64 * 1024 * 1024:
                    retained.append(result)
        self._project_results = tuple(retained)

    def submit_export_job(
        self, job: WBJob, callback: Callable[[WBReply], None], *, accept_errors: bool = False
    ) -> None:
        self._export_with_evidence(job, callback, accept_errors=accept_errors)

    @property
    def resources_closed(self) -> bool:
        return (
            self._store_closed
            and self._background_closed
            and self._restore_job is None
            and self._selection_job is None
            and not self.intake.scanning
        )

    @property
    def has_unsaved_changes(self) -> bool:
        return bool(self._workspace) and self.view.generation != self._saved_generation

    def pause_auto_save(self, paused: bool) -> None:
        self._transition_pending = paused
        if paused:
            self._auto_save.stop()
        elif self.has_unsaved_changes and not self._closing:
            self._auto_save.start()
        self._controls()

    def prepare_shutdown(self, *, save_changes: bool = True) -> None:
        """The visible shell has already resolved save/discard/cancel choices."""
        self._save_on_close = save_changes
        self.pause_auto_save(True)

    def _controls(self) -> None:
        idle = not self._busy and not self._closing and not self._transition_pending
        self.create_button.setEnabled(idle and not self._workspace)
        self.open_button.setEnabled(idle and not self._workspace)
        self.restore_button.setEnabled(idle and not self._workspace)
        self.import_button.setEnabled(idle and bool(self._workspace))
        self.save_button.setEnabled(idle and bool(self._workspace))
        self.new_button.setEnabled(idle and bool(self._workspace))
        self.documents.setEnabled(idle and bool(self._workspace))
        self.cancel_button.setEnabled(self._busy and not self._closing)
        self.cancel_action.setVisible(self._busy)
        self.progress_action.setVisible(self._busy)
        self.export_button.setEnabled(idle and bool(self._workspace))
        self.save_state.setText(
            "正在处理…"
            if self._busy
            else "有未保存修改"
            if self.view.generation != self._saved_generation
            else "已保存"
            if self._workspace
            else "尚未开始"
        )
        self.view.setEnabled(idle and bool(self._workspace))
        self.surface.setCurrentWidget(self.view if self._workspace else self.welcome)
        self.welcome_status.setText(
            "正在处理工作区，请稍候。" if self._busy else self.view.status.text()
        )
        for action, button in self.project_actions:
            action.setEnabled(button.isEnabled())
        for welcome_button, button in self.welcome_buttons:
            welcome_button.setEnabled(button.isEnabled())

    def _start(self) -> None:
        self.operation_error = ""
        self._busy = True
        self.quant_progress = {"phase": "working", "label": "后台处理中"}
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
        self.operation_error = message
        self._ocr_refresh_timer.stop()
        self._ocr_refresh_pending = False
        # A failed final save must leave the window open for recovery, never retry recursively.
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
                try:
                    callback(reply)
                except (ValueError, TypeError, OSError) as error:
                    self._error(str(error))

    def _wb_reply(self, reply: WBReply) -> None:
        callback = self._wb_callbacks.pop(reply.request_id, None)
        accept_errors = reply.request_id in self._wb_accept_errors
        self._wb_accept_errors.discard(reply.request_id)
        if callback:
            if reply.error and not accept_errors:
                self._error(reply.error)
            else:
                try:
                    callback(reply)
                except (ValueError, TypeError, OSError) as error:
                    self._error(str(error))

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
                (r, self.view.suggestions.settings(r, project.crop_height_for(r))) for r in rows
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
        if create:
            paths, _ = QFileDialog.getOpenFileNames(self, "选择 WB 原图", "", "TIFF (*.tif *.tiff)")
            if paths:
                self.start_project_from_images([Path(path) for path in paths])
            return
        path = QFileDialog.getExistingDirectory(self, "打开已有项目")
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
        self.workspace_opened.emit(self._workspace)

    def _choose_import(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择同一项目的原始 TIFF", "", "TIFF (*.tif *.tiff)"
        )
        if paths:
            self.import_images(tuple(paths), automatic=True)

    def new_project(self) -> None:
        if self._busy or not self._workspace:
            return

        def create() -> None:
            previous = self.view.project()
            template = previous.template
            project = WBFigureProject(project_id=uuid4().hex, template=template)
            if isinstance(previous, WBLayoutProject):
                project = with_figure_layout(
                    project, initial_composition(project), previous.layout_style
                )
            self.view.set_project(project)
            self._project_results = ()
            self._loaded_ocr = None
            self.view.generation += 1
            self._saved_revision = None
            self.view.status.setText("已复用模板新建项目；导入下一批原图。")

        self.save(after=create)

    def import_images(self, paths: tuple[str, ...], *, automatic: bool = False) -> None:
        if self._busy or not self._workspace:
            return
        try:
            if isinstance(self.view.project(), WBIntakeProject):
                raise ValueError("请使用仪器导入页的“添加原图文件夹”")
        except ValueError as error:
            self._error(str(error))
            return
        self._start()
        pending = list(paths)
        duplicates = 0
        errors: list[str] = []
        imported_ids: list[str] = []
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
                if (
                    automatic
                    and (imported_ids or errors)
                    and not self._cancellation.is_set()
                    and not self._closing
                ):
                    self._analyze_imported_rows(tuple(imported_ids), tuple(errors))
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
                        labels = source_import_labels(path) if automatic else None
                        row = FigureRow(
                            row_id=uuid4().hex,
                            source=asset,
                            filename=Path(path).name,
                            # Literal labels do not establish a control/sample pairing.
                            protein=labels.protein if labels and labels.protein else "Unassigned",
                            width=raster.width,
                            height=raster.height,
                            bit_depth=16 if raster.bit_depth == 16 else 8,
                            figure=(
                                labels.figure or f"Fig{len(current.rows) + 1}"
                                if labels
                                else f"Fig{len(current.rows) + 1}"
                                if automatic
                                else current.figure_order[-1]
                                if current.figure_order
                                else "Fig1"
                            ),
                        )
                        self.view.set_project(
                            current.model_copy(
                                update={
                                    "rows": (*current.rows, row),
                                    "figure_order": tuple(
                                        dict.fromkeys((*current.figure_order, row.figure))
                                    ),
                                }
                            )
                        )
                        self.view.generation += 1
                        generation = self.view.generation
                        self.source_origins.remember(
                            self._workspace, current.project_id, row.row_id, asset.sha256, path
                        )
                        self.view.install_thumbnail(raster)
                        imported_ids.append(row.row_id)
                        next_image()

                    self._storage(StorageCommand("asset", asset=asset), resolved)

                self._storage(
                    StorageCommand("import", path=path, source_sha256=raster.sha256), imported
                )

            self._wb(WBJob("preview", path=path, preview_edge=128), previewed, accept_errors=True)

        next_image()

    def return_selected_crop(self, *, locate: bool = False) -> None:
        if self._busy or self._closing or not self._workspace:
            return
        row = self.view.selected_row()
        if row is None or row.source is None or row.roi is None:
            raise ValueError("请先选定原图裁剪范围")
        project = self.view.project()
        source_sha = row.source.sha256
        source_path = (
            ""
            if locate
            else self.source_origins.lookup(
                self._workspace, project.project_id, row.row_id, source_sha
            )
        )
        if not source_path:
            source_path, _ = QFileDialog.getOpenFileName(
                self, "定位原图：核验后在其所在文件夹生成新裁图", "", "TIFF (*.tif *.tiff)"
            )
            if not source_path:
                return
        self._auto_save.stop()
        self.view.confirm_row(row.row_id)
        generation, workspace = self.view.generation, self._workspace

        def saved() -> None:
            current = self.view.project()
            if (
                self._closing
                or self._cancellation.is_set()
                or generation != self.view.generation
                or workspace != self._workspace
                or current.project_id != project.project_id
            ):
                return
            self._start()

            def returned(reply: WBReply) -> None:
                if reply.error or not isinstance(reply.value, ReturnedCrop):
                    message = reply.error or "裁图回存未返回核验记录"
                    if self._closing:
                        self._done(message)
                    else:
                        self._error(message)
                    return
                result = reply.value
                if (
                    self._closing
                    or generation != self.view.generation
                    or workspace != self._workspace
                    or self.view.project().project_id != project.project_id
                ):
                    self._done("旧裁图输出已保留；当前项目未替换")
                    return
                self.source_origins.remember(
                    workspace, project.project_id, row.row_id, source_sha, source_path
                )
                self._done(
                    f"裁图已核验并回存至 {Path(source_path).parent}；"
                    f"新增 {len(result.files)} 个图像和1份记录，原图与旧结果保留。"
                )

            self._wb(
                WBJob(
                    "return_crop",
                    path=source_path,
                    document=current,
                    row_id=row.row_id,
                    cancellation=self._cancellation,
                ),
                returned,
                accept_errors=True,
            )

        self.save(after=saved)

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
        preview = self.view.source_preview
        if preview is not None and preview.sha256 == asset.sha256:
            # Fig rows on the same sheet share one immutable display raster.
            self.view.set_source_preview(preview)
            return
        self._start()

        def previewed(reply: WBReply) -> None:
            if self._closing or self._cancellation.is_set():
                self._done("原图预览已停止")
                return
            if not isinstance(reply.value, PreviewRaster) or reply.value.sha256 != asset.sha256:
                self._error("原图来源不一致")
                return
            self.view.set_source_preview(reply.value)
            self._done(
                f"{row.filename} · {row.width} × {row.height} · {row.bit_depth} 位；"
                "框选时请排除 Marker。"
            )

        self._wb(WBJob("preview", path=self._paths[asset.sha256]), previewed, accept_errors=True)

    def select_initial_source(self) -> None:
        if self._closing or self._cancellation.is_set():
            return
        project = self.view.project()
        if project.rows:
            index = next((i for i, row in enumerate(project.rows) if row.roi), 0)
            if self.view.table.currentRow() != index:
                self.view.table.setCurrentCell(index, 0)
            else:
                self.select_source(project.rows[index].row_id)

    def save(
        self,
        after: Callable[[], None] | None = None,
        *,
        transform: Callable[[WBFigureProject], WBFigureProject] | None = None,
        install_guard: Callable[[], bool] | None = None,
    ) -> None:
        if self._busy or not self._workspace:
            return
        try:
            project = self.view.project(
                0 if self._saved_revision is None else self._saved_revision + 1
            )
            if transform is not None:
                project = transform(project)
        except ValueError as error:
            self._error(str(error))
            return
        generation = self.view.generation
        self._start()
        self.quant_progress = {"phase": "save", "label": "保存项目"}

        def encoded(reply: WBReply) -> None:
            if install_guard is not None and not install_guard():
                self._done("操作已停止；当前草稿保留，未提交新修订。")
                return
            if not isinstance(reply.value, bytes):
                self._error("项目编码无效")
                return

            def saved(reply: StorageReply) -> None:
                self._saved_revision = project.revision
                self._saved_generation = generation
                if install_guard is not None and not install_guard():
                    # CAS already committed. Retain that history and mark the
                    # current draft unsaved instead of installing a cancelled result.
                    self.view.generation += 1
                    self._done("新修订已写入历史；已停止安装，当前草稿保留，请保存或继续编辑。")
                    return
                if generation != self.view.generation:
                    self._done("旧修订已保存，当前编辑保留；请重新执行操作")
                    return
                self.view.set_project(project)
                if transform is not None:
                    self.view.generation += 1
                    self._saved_generation = self.view.generation
                if self.documents.findData(project.project_id) < 0:
                    self.documents.addItem(project.name, project.project_id)
                self._busy = False
                self._controls()
                self.view.status.setText("项目已保存，原图和模板可重新打开。")
                if self._closing:
                    self._finish_close()
                elif after and self._cancellation.is_set():
                    self._done("项目已保存；后续操作已取消。")
                else:
                    # set_project restores controls and intentionally invalidates
                    # result presentation. Rebuild from verified runs before any
                    # follow-up (including display-only compose), even when no
                    # scientific parameters changed.
                    if isinstance(project, WBIntakeProject):
                        self._done("导入清单已保存，可重新打开。")
                        if after:
                            after()
                    else:
                        self.refresh_project_table("项目已保存，结果表已核验。", after=after)

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

        self.submit_tool_job(WBJob("encode", document=project), encoded)

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
                interrupted = False
                if isinstance(project, WBIntakeWorkflowProject):
                    recovered = recover_intake_workflow(project)
                    interrupted = recovered != project
                    project = recovered
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
                        if isinstance(project, WBIntakeProject):

                            def intake_loaded() -> None:
                                current = self.view.project()
                                if isinstance(current, WBRestoredProject) and current.analyses:
                                    self._start()
                                    self._restore_project_evidence(
                                        current, after=self.load_thumbnails
                                    )
                                else:
                                    self.load_thumbnails()

                            self._done("导入清单已恢复，正在核验运行与缩略图。")
                            if interrupted:
                                self.view.generation += 1
                                self.save(after=intake_loaded)
                                return
                            intake_loaded()
                        elif isinstance(project, WBRestoredProject):
                            self._restore_project_evidence(project)
                        elif isinstance(project, WBAnalysisProject):
                            analysis_project = project

                            def measurements() -> None:
                                self._start_measurements(
                                    analysis_project,
                                    tuple(p.row_id for p in analysis_project.analyses),
                                    restore=True,
                                    after=self.select_initial_source,
                                )

                            if isinstance(project, WBProjectOCR) and project.ocr is not None:
                                self._start_ocr(project, restore=True, after=measurements)
                            else:
                                measurements()
                        else:
                            self._done("项目已恢复，原图资产已校验。选择一行查看原图。")
                            self.select_initial_source()
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

    def _restore_project_evidence(
        self, project: WBRestoredProject, *, after: Callable[[], None] | None = None
    ) -> None:
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
                        "历史来源见结果表。",
                        after=after or self.select_initial_source,
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
                    self._done(
                        "拼图已更新；可点击图片返回原图调整。"
                        if self.automatic.crop_policy == "lane_ratio@1"
                        else "预览已生成；未审核行允许预览，正式导出须逐行确认。"
                    )
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

    def _choose_template_export(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "保存新的模板文件",
            "",
            "WB 模板 (*.wbtemplate)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if destination:
            self.export_template(destination)

    def export_template(self, destination: str) -> None:
        if self._busy or not self._workspace or self._closing:
            return
        try:
            project = self.view.project()
        except ValueError as error:
            self._error(str(error))
            return
        generation = self.view.generation
        self._start()
        self._export_generation = generation

        def exported(reply: WBReply) -> None:
            if isinstance(reply.value, str) and not reply.error:
                self._done("模板文件已保存；只包含所选修订的排版设置和字体。")
            elif self._closing or self._cancellation.is_set() or generation != self.view.generation:
                self._done("模板导出已取消或项目已修改；当前编辑保留。")
            else:
                self._error(reply.error or "模板导出结果无效")

        self._wb(
            WBJob(
                "template_export",
                document=project,
                destination=destination,
                sources=tuple(FigureSourcePath(sha, path) for sha, path in self._paths.items()),
                cancellation=self._cancellation,
            ),
            exported,
            accept_errors=True,
        )

    def _choose_template_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "导入模板并新建项目", "", "WB 模板 (*.wbtemplate)"
        )
        if path:
            self.import_template(path)

    def import_template(self, path: str) -> None:
        if self._busy or not self._workspace or self._closing:
            return
        generation = self.view.generation
        self._start()

        def obsolete() -> bool:
            if self._closing or self._cancellation.is_set() or generation != self.view.generation:
                self._done("模板导入已取消或项目已修改；当前项目保持。")
                return True
            return False

        def parsed(reply: WBReply) -> None:
            if obsolete():
                return
            if reply.error or not isinstance(reply.value, LoadedFigureTemplate):
                self._error(reply.error or "模板读取结果无效")
                return
            loaded = reply.value

            def current_saved() -> None:
                if obsolete():
                    return
                self._busy = True
                self._controls()

                def install(asset: AssetRef | None = None, asset_path: str = "") -> None:
                    if obsolete():
                        return
                    template = loaded.spec.template.model_copy(update={"font": asset})
                    fresh: WBFigureProject = WBFigureProject(
                        project_id=uuid4().hex, template=template
                    )
                    if loaded.spec.layout_style is not None:
                        fresh = with_figure_layout(
                            fresh, initial_composition(fresh), loaded.spec.layout_style
                        )
                    self._paths = {asset.sha256: asset_path} if asset is not None else {}
                    self.view.set_project(fresh)
                    self.view.generation += 1
                    self._saved_revision = None
                    self._project_results = ()
                    self._loaded_ocr = None
                    self._done("模板已导入并新建空项目；原项目已保存，请导入本次实验的原图。")

                descriptor = loaded.spec.font
                if descriptor is None:
                    install()
                    return

                def imported(storage_reply: StorageReply) -> None:
                    if obsolete():
                        return
                    if storage_reply.error_code or not isinstance(storage_reply.value, AssetRef):
                        self._error(storage_reply.message or "模板字体导入失败")
                        return
                    asset = storage_reply.value

                    def resolved(storage_reply: StorageReply) -> None:
                        if obsolete():
                            return
                        if storage_reply.error_code or not isinstance(storage_reply.value, str):
                            self._error(storage_reply.message or "模板字体路径无效")
                            return
                        install(asset, storage_reply.value)

                    self._storage(
                        StorageCommand("asset", asset=asset), resolved, accept_errors=True
                    )

                self._storage(
                    StorageCommand(
                        "import_bytes",
                        path=descriptor.filename,
                        data=loaded.font_data,
                        source_sha256=descriptor.sha256,
                    ),
                    imported,
                    accept_errors=True,
                )

            # Save the previous experiment before replacing its draft with an empty project.
            self._busy = False
            self.save(after=current_saved)

        self._wb(
            WBJob("template_read", path=path, cancellation=self._cancellation),
            parsed,
            accept_errors=True,
        )

    def _choose_font(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "导入支持标签文字的字体", "", "Fonts (*.ttf *.otf *.ttc)"
        )
        if path:
            self.import_font(path)

    def _analyze_imported_rows(self, row_ids: tuple[str, ...], errors: tuple[str, ...]) -> None:
        project = self.view.project()

        def analyze() -> None:
            self.automatic.analyze(row_ids=row_ids, import_errors=errors)

        if project.template.font or not any(
            ord(char) > 255
            for label in (*project.figure_order, *(row.protein for row in project.rows))
            for char in label
        ):
            analyze()
            return
        generation = self.view.generation
        self._start()

        def selected(reply: WBReply) -> None:
            if generation != self.view.generation or self._closing or self._cancellation.is_set():
                self._done("标签字体选择已取消。")
                return
            if not isinstance(reply.value, str):
                self._error(reply.error or "标签字体路径无效")
                return
            self._done("已找到标签字体，正在保存到项目。")
            self.import_font(reply.value, finished=analyze)

        self._wb(WBJob("label_font", document=project), selected)

    def import_font(self, path: str, *, finished: Callable[[], None] | None = None) -> None:
        if self._busy:
            return
        try:
            project = self.view.project()
        except ValueError as error:
            self._error(str(error))
            return
        self._start()
        generation = self.view.generation

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
                    if (
                        generation != self.view.generation
                        or self._closing
                        or self._cancellation.is_set()
                    ):
                        self._done("字体导入已取消：当前项目已更改或正在关闭。")
                        return
                    if not isinstance(reply.value, str):
                        self._error("字体路径无效")
                        return
                    self._paths[asset.sha256] = reply.value
                    prepared = prepare_workbench_revision(
                        project,
                        expected_digest=workbench_project_digest(project),
                        impact="figures",
                    )
                    self.view.set_project(
                        type(prepared).model_validate(
                            {
                                **dict(prepared),
                                "template": project.template.model_copy(update={"font": asset}),
                            }
                        )
                    )
                    self.view.generation += 1
                    self._done("字体已导入，随项目保存。")
                    if finished is not None:
                        finished()

                self._storage(StorageCommand("asset", asset=asset), resolved)

            self._storage(StorageCommand("import", path=path, source_sha256=reply.value), imported)

        self._wb(WBJob("font_digest", path=path), fingerprinted)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.resources_closed:
            event.accept()
            return
        event.ignore()
        self._closing = True
        self._auto_save.stop()
        self.cancel()
        self._controls()
        if not self._busy:
            self._finish_close()

    def _finish_close(self) -> None:
        if self._shutting:
            return
        if (
            self._save_on_close
            and self._workspace
            and self._saved_generation != self.view.generation
        ):
            self.save()
            return
        self._shutting = True
        # Retire one owned port at a time. Moving the image worker back to
        # the GUI must finish before storage close emits its queued Python reply.
        if self._background_closed:
            self._store.shutdown()
        else:
            self._background.shutdown()

    def _store_stopped(self) -> None:
        self._store_closed = True
        self._both_stopped()

    def _background_stopped(self) -> None:
        self._background_closed = True
        if self._shutting:
            self._store.shutdown()
        self._both_stopped()

    def _both_stopped(self) -> None:
        if self.resources_closed:
            self.closed.emit()
            self.close()
