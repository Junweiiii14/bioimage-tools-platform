"""Cancellable instrument import; scientific identities are assigned by the user."""

import os
from hashlib import sha256
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING
from uuid import uuid4

from PySide6.QtCore import QThread
from tool_contracts.api import AssetRef
from wb_tool.api import (
    ExportDiscovery,
    FigureSourcePath,
    IntakeSource,
    PreviewRaster,
    WBIntakeProject,
    WBJob,
    WBReply,
    install_export_discovery,
    intake_digest,
    intake_needs_reference_discovery,
    register_intake_source,
)

from bioimage_app.project_entry import collect_source_images
from bioimage_app.storage import StorageCommand, StorageReply

if TYPE_CHECKING:
    from bioimage_app.figure_window import FigureProjectWindow


class InstrumentFolderJob(QThread):
    def __init__(self, root: Path, cancellation: Event) -> None:
        super().__init__()
        self.root = root
        self.cancellation = cancellation
        self.paths: tuple[Path, ...] = ()
        self.error = ""

    def run(self) -> None:
        try:
            self.paths = collect_source_images([self.root], self.cancellation)
        except (OSError, ValueError) as error:
            self.error = str(error)


class InstrumentIntakeSession:
    def __init__(self, host: "FigureProjectWindow") -> None:
        self.host = host
        self.issues: list[str] = []
        self._scan_job: InstrumentFolderJob | None = None
        self.group_preview: tuple[str, PreviewRaster] | None = None

    @property
    def scanning(self) -> bool:
        return self._scan_job is not None

    def preview_source(self, source_id: str, expected_digest: str) -> None:
        """One bounded original-source display preview; never installed as a thumbnail or ROI."""
        host = self.host
        project = host.view.project()
        if host.operation_busy or host.is_closing:
            return
        if not isinstance(project, WBIntakeProject) or intake_digest(project) != expected_digest:
            raise ValueError("当前原图池已变化")
        source = next((s for s in project.intake.sources if s.source_id == source_id), None)
        if source is None:
            raise ValueError("原图来源不存在")
        generation, identity = host.view.generation, (host.workspace_path, project.project_id)
        host.begin_operation()

        def current() -> bool:
            return (
                not host.is_closing
                and not host.cancellation.is_set()
                and host.view.generation == generation
                and identity == (host.workspace_path, host.view.project_identity)
            )

        def previewed(reply: WBReply) -> None:
            if not current():
                host.finish_operation("旧图像预览未安装。")
                return
            raster = reply.value
            if reply.error or not isinstance(raster, PreviewRaster):
                host.fail_operation(reply.error or "图像预览返回无效结果")
                return
            if (
                (raster.sha256, raster.width, raster.height, raster.bit_depth)
                != (source.asset.sha256, source.width, source.height, source.bit_depth)
                or not (1 <= raster.preview_width <= 2048 and 1 <= raster.preview_height <= 2048)
                or len(raster.pixels) != raster.preview_width * raster.preview_height
            ):
                host.fail_operation("图像预览与原始来源不匹配")
                return
            self.group_preview = source_id, raster
            host.finish_operation("原图显示预览已加载，原始像素保持。")

        def resolved(reply: StorageReply) -> None:
            if not current():
                host.finish_operation("旧图像预览请求已停止。")
            elif reply.error_code or not isinstance(reply.value, str):
                host.fail_operation(reply.message or "原图资产无法解析")
            else:
                host.submit_tool_job(
                    WBJob("preview", path=reply.value, preview_edge=2048),
                    previewed,
                    accept_errors=True,
                )

        host.submit_storage_job(
            StorageCommand("asset", asset=source.asset), resolved, accept_errors=True
        )

    def discover(self, expected_digest: str) -> None:
        """Resolve immutable assets off the GUI thread and install only a current reply."""
        host = self.host
        project = host.view.project()
        if host.operation_busy or host.is_closing or not host.workspace_path:
            return
        if not isinstance(project, WBIntakeProject) or project.schema_version != 10:
            raise ValueError("请先返回仪器清单再识别原图")
        if not project.intake.sources or intake_digest(project) != expected_digest:
            raise ValueError("原图池已变化，请刷新后识别")
        generation, identity = host.view.generation, (host.workspace_path, project.project_id)
        pending = list({s.asset.sha256: s.asset for s in project.intake.sources}.values())
        sources: list[FigureSourcePath] = []
        host.begin_operation()

        def current() -> bool:
            return (
                not host.is_closing
                and not host.cancellation.is_set()
                and host.view.generation == generation
                and identity == (host.workspace_path, host.view.project_identity)
            )

        def next_source() -> None:
            if not current():
                host.finish_operation("识别已停止，当前清单保留。")
                return
            if pending:
                asset = pending.pop(0)

                def resolved(reply: StorageReply) -> None:
                    if not current():
                        host.finish_operation("旧识别回复未安装。")
                    elif reply.error_code or not isinstance(reply.value, str):
                        host.fail_operation(reply.message or "原图资产无法解析")
                    else:
                        sources.append(FigureSourcePath(asset.sha256, reply.value))
                        next_source()

                host.submit_storage_job(
                    StorageCommand("asset", asset=asset), resolved, accept_errors=True
                )
                return
            host.submit_tool_job(
                WBJob(
                    "intake_discover",
                    document=project,
                    sources=tuple(sources),
                    cancellation=host.cancellation,
                ),
                completed,
                accept_errors=True,
            )

        def completed(reply: WBReply) -> None:
            if not current():
                host.finish_operation("旧识别回复未安装，当前草稿保留。")
                return
            if reply.error or not isinstance(reply.value, bytes):
                host.fail_operation(reply.error or "识别返回无效结果")
                return
            try:
                discovery = ExportDiscovery.from_bytes(reply.value)
            except ValueError as error:
                host.fail_operation(str(error))
                return
            host.end_phase()

            def install(active: object) -> WBIntakeProject:
                if not isinstance(active, WBIntakeProject):
                    raise ValueError("当前项目已改变")
                return install_export_discovery(active, discovery, expected_digest=expected_digest)

            host.save(transform=install, install_guard=current)

        next_source()

    def import_folder(self, root: Path) -> None:
        host = self.host
        if host.operation_busy or host.is_closing or not host.workspace_path:
            return
        if not isinstance(host.view.project(), WBIntakeProject):
            raise ValueError("请从首页新建仪器导入项目")
        host.begin_operation()
        job = InstrumentFolderJob(root, host.cancellation)
        self._scan_job = job

        def scanned() -> None:
            self._scan_job = None
            job.deleteLater()
            if host.is_closing or host.cancellation.is_set():
                host.finish_operation("文件夹扫描已取消。")
            elif job.error:
                host.fail_operation(job.error)
            else:
                host.end_phase()
                self.import_paths(job.paths, root)

        job.finished.connect(scanned)
        job.start()

    def import_paths(self, paths: tuple[Path, ...], root: Path | tuple[Path, ...]) -> None:
        host = self.host
        if host.operation_busy or host.is_closing or not host.workspace_path:
            return
        project = host.view.project()
        if not isinstance(project, WBIntakeProject):
            raise ValueError("当前项目不是仪器导入清单")
        roots = (root,) if isinstance(root, Path) else root
        selected_roots = sorted(
            {p.resolve() for p in roots}, key=lambda p: len(p.parts), reverse=True
        )
        pending: list[tuple[Path, Path]] = []
        for path in paths:
            resolved = path.resolve()
            source_root = next((r for r in selected_roots if resolved.is_relative_to(r)), None)
            if source_root is None or resolved == source_root:
                raise ValueError("原图不属于所选导入文件夹，请重新核对来源")
            pending.append((resolved, source_root))
        host.begin_operation()
        identity = (host.workspace_path, project.project_id)
        generation = host.view.generation
        self.issues = []
        imported_count = skipped = 0

        def current() -> bool:
            return (
                not host.is_closing
                and not host.cancellation.is_set()
                and generation == host.view.generation
                and identity == (host.workspace_path, host.view.project_identity)
            )

        def next_image() -> None:
            nonlocal skipped
            if not current() or not pending:
                completed = current()
                suffix = (
                    "已取消；已导入项保留。" if not current() else "请填写 Fig 清单并分配原图。"
                )
                host.finish_operation(
                    f"原图导入：{imported_count} 张，重复 {skipped} 张，"
                    f"失败 {len(self.issues)} 张。" + suffix
                )
                if completed and imported_count:

                    def classify_new_pool() -> None:
                        active = host.view.project()
                        if (
                            not host.is_closing
                            and not host.cancellation.is_set()
                            and identity == (host.workspace_path, host.view.project_identity)
                            and isinstance(active, WBIntakeProject)
                            and intake_needs_reference_discovery(active)
                        ):
                            self.discover(intake_digest(active))

                    host.save(after=classify_new_pool)
                return
            project = host.view.project()
            if not isinstance(project, WBIntakeProject):
                host.finish_operation("项目已改变，导入停止。")
                return
            if len(project.intake.sources) >= 512:
                self.issues.append(f"已达 512 张上限，另有 {len(pending)} 张未导入")
                pending.clear()
                next_image()
                return
            path, source_root = pending.pop(0)
            root_key = sha256(os.path.normcase(str(source_root)).encode("utf-8")).hexdigest()[:16]
            namespace = f"{source_root.name or 'root'}~batch2-{root_key}"
            relative = namespace + "/" + path.relative_to(source_root).as_posix()
            host.view.status.setText(f"正在读取 {relative}；剩余 {len(pending)} 张")

            def previewed(reply: WBReply) -> None:
                nonlocal skipped
                if not current():
                    next_image()
                    return
                if not isinstance(reply.value, PreviewRaster):
                    self.issues.append(f"{relative}：{reply.error or '无法读取图像'}")
                    next_image()
                    return
                raster = reply.value
                if (
                    not 1 <= raster.preview_width <= 128
                    or not 1 <= raster.preview_height <= 128
                    or len(raster.pixels) != raster.preview_width * raster.preview_height
                ):
                    self.issues.append(f"{relative}：缩略图超出 128 像素预算或数据不完整")
                    next_image()
                    return
                project = host.view.project()
                if not isinstance(project, WBIntakeProject):
                    next_image()
                    return
                selected_path = os.path.normcase(str(path.absolute()))
                if any(
                    source.asset.sha256 == raster.sha256
                    and os.path.normcase(
                        host.source_origins.lookup(
                            host.workspace_path,
                            project.project_id,
                            source.source_id,
                            source.asset.sha256,
                        )
                    )
                    == selected_path
                    for source in project.intake.sources
                ):
                    skipped += 1
                    next_image()
                    return

                def imported(reply: StorageReply) -> None:
                    if not current():
                        next_image()
                        return
                    if not isinstance(reply.value, AssetRef):
                        self.issues.append(f"{relative}：{reply.message or '资产导入失败'}")
                        next_image()
                        return
                    asset = reply.value

                    def resolved(reply: StorageReply) -> None:
                        nonlocal generation, imported_count
                        if not current():
                            next_image()
                            return
                        if not isinstance(reply.value, str):
                            self.issues.append(f"{relative}：{reply.message or '资产解析失败'}")
                            next_image()
                            return
                        project = host.view.project()
                        if not isinstance(project, WBIntakeProject):
                            next_image()
                            return
                        try:
                            source = IntakeSource(
                                source_id=uuid4().hex,
                                asset=asset,
                                original_name=path.name,
                                relative_path=relative,
                                width=raster.width,
                                height=raster.height,
                                bit_depth=16 if raster.bit_depth == 16 else 8,
                            )
                            updated = register_intake_source(
                                project, source, expected_digest=intake_digest(project)
                            )
                        except ValueError as error:
                            self.issues.append(f"{relative}：{error}")
                            next_image()
                            return
                        host.remember_source_path(asset, reply.value)
                        host.view.set_project(updated)
                        host.view.generation += 1
                        generation = host.view.generation
                        host.view.install_thumbnail(raster)
                        host.source_origins.remember(
                            host.workspace_path,
                            project.project_id,
                            source.source_id,
                            source.asset.sha256,
                            str(path),
                        )
                        imported_count += 1
                        next_image()

                    host.submit_storage_job(
                        StorageCommand("asset", asset=asset), resolved, accept_errors=True
                    )

                host.submit_storage_job(
                    StorageCommand("import", path=str(path), source_sha256=raster.sha256),
                    imported,
                    accept_errors=True,
                )

            host.submit_tool_job(
                WBJob("preview", path=str(path), preview_edge=128), previewed, accept_errors=True
            )

        next_image()
