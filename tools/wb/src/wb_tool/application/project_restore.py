"""Portable historical evidence, distinct from observed local process/run records."""

from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator
from tool_contracts.api import AssetRef, RunRecord

from wb_tool.application.crop_suggestions import WBReviewProject
from wb_tool.application.document import DocumentIO
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_analysis import LoadedProjectResult, WBAnalysisProject
from wb_tool.application.project_normalization import WBNormalizedProject
from wb_tool.application.project_ocr import LoadedProjectOCR, WBProjectOCR


class ArchiveSource(DocumentIO):
    archive: AssetRef
    project_id: str
    revision: int = Field(ge=0)
    format_version: Literal[1, 2]


class ImportedRun(DocumentIO):
    run: RunRecord
    archive_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    request: AssetRef | None = None
    result: AssetRef | None = None
    error: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def consistent(self) -> "ImportedRun":
        if self.run.state not in ("succeeded", "failed", "cancelled", "interrupted"):
            raise ValueError("归档历史仅能引用终态")
        if not self.error and (self.request is None or (self.run.result and self.result is None)):
            raise ValueError("历史证据缺失须保留原因")
        for local, original in ((self.request, self.run.request), (self.result, self.run.result)):
            if local is not None and (
                original is None
                or (local.sha256, local.size_bytes) != (original.sha256, original.size_bytes)
            ):
                raise ValueError("复制的历史资产不对应原声明")
        return self


class WBRestoredProject(WBNormalizedProject):
    schema_version: int = Field(default=6, ge=6, le=6)
    archive_sources: tuple[ArchiveSource, ...] = Field(min_length=1, max_length=8)
    imported_runs: tuple[ImportedRun, ...] = Field(default=(), max_length=4096)

    @model_validator(mode="after")
    def origin_identity(self) -> "WBRestoredProject":
        sources = {s.archive.sha256 for s in self.archive_sources}
        if len(sources) != len(self.archive_sources) or any(
            s.project_id != self.project_id or s.revision > self.revision
            for s in self.archive_sources
        ):
            raise ValueError("归档来源身份/修订不一致或重复")
        if len({r.run.run_id for r in self.imported_runs}) != len(self.imported_runs):
            raise ValueError("历史运行身份重复")
        current = [p.run for p in self.analyses if p.run]
        if self.ocr and self.ocr.run:
            current.append(self.ocr.run)
        for item in self.imported_runs:
            if item.archive_sha256 not in sources or item.run.document_id != self.project_id:
                raise ValueError("历史运行不属于记录的项目来源")
            if any(r.run_id == item.run.run_id and r != item.run for r in current):
                raise ValueError("当前运行与同身份历史声明不一致")
        return self


def with_archive_history(
    project: WBFigureProject, sources: tuple[ArchiveSource, ...], runs: tuple[ImportedRun, ...]
) -> WBRestoredProject:
    if isinstance(project, WBRestoredProject):
        fields = {name: getattr(project, name) for name in type(project).model_fields}
        fields.update(archive_sources=sources, imported_runs=runs)
        return type(project).model_validate(fields)
    return WBRestoredProject(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        rows=project.rows,
        figure_order=project.figure_order,
        template=project.template,
        suggestions=project.suggestions if isinstance(project, WBReviewProject) else (),
        analyses=project.analyses if isinstance(project, WBAnalysisProject) else (),
        ocr=project.ocr if isinstance(project, WBProjectOCR) else None,
        normalizations=project.normalizations if isinstance(project, WBNormalizedProject) else (),
        archive_sources=sources,
        imported_runs=runs,
    )


def imported_run(project: WBFigureProject, run: RunRecord) -> ImportedRun | None:
    if isinstance(project, WBRestoredProject):
        return next((item for item in project.imported_runs if item.run == run), None)
    return None


def project_assets(project: WBFigureProject, *, history: bool = True) -> tuple[AssetRef, ...]:
    from wb_tool.application.instrument_intake import WBIntakeProject

    assets = [row.source for row in project.rows if row.source]
    if isinstance(project, WBIntakeProject):
        assets.extend(source.asset for source in project.intake.sources)
    if project.template.font:
        assets.append(project.template.font)
    if isinstance(project, WBProjectOCR) and project.ocr:
        assets.append(project.ocr.source)
    if history and isinstance(project, WBRestoredProject):
        assets.extend(source.archive for source in project.archive_sources)
        for item in project.imported_runs:
            assets.extend(asset for asset in (item.request, item.result) if asset)
    unique = {asset.sha256: asset for asset in assets}
    if any(unique[asset.sha256].size_bytes != asset.size_bytes for asset in assets):
        raise ValueError("同一来源SHA对应不同字节数")
    return tuple(unique.values())


def run_origin(project: WBFigureProject, run_id: str) -> tuple[str, str]:
    if not isinstance(project, WBRestoredProject) or not run_id:
        return "", ""
    item = next((r for r in project.imported_runs if r.run.run_id == run_id), None)
    return ("归档历史证据", item.archive_sha256) if item else ("本机运行", "")


@dataclass(frozen=True)
class RestoredProjectResults:
    results: tuple[LoadedProjectResult, ...]
    ocr: LoadedProjectOCR | None
    errors: tuple[str, ...]


@dataclass(frozen=True)
class StagedArchiveAsset:
    sha256: str
    path: str


@dataclass(frozen=True)
class StagedArchiveRun:
    run: RunRecord
    request_sha256: str = ""
    result_sha256: str = ""
    error: str = ""


@dataclass(frozen=True)
class StagedProjectArchive:
    project: WBFigureProject
    archive_path: str
    archive_sha256: str
    assets: tuple[StagedArchiveAsset, ...]
    runs: tuple[StagedArchiveRun, ...]
    format_version: Literal[1, 2]


def restore_staged_project(
    staged: StagedProjectArchive, imported: tuple[AssetRef, ...], archive: AssetRef
) -> WBRestoredProject:
    if archive.sha256 != staged.archive_sha256:
        raise ValueError("导入ZIP资产摘要不一致")
    assets = {a.sha256: a for a in imported}

    def mapped(asset: AssetRef) -> AssetRef:
        replacement = assets.get(asset.sha256)
        if replacement is None or replacement.size_bytes != asset.size_bytes:
            raise ValueError("恢复资产映射缺失或字节数不同")
        return replacement

    project = staged.project
    rows = tuple(
        row.model_copy(update={"source": mapped(row.source)}) if row.source else row
        for row in project.rows
    )
    template = (
        project.template.model_copy(update={"font": mapped(project.template.font)})
        if project.template.font
        else project.template
    )
    changes: dict[str, object] = {"rows": rows, "template": template}
    from wb_tool.application.instrument_intake import IntakeManifest, WBIntakeProject, intake_digest

    if isinstance(project, WBIntakeProject):
        manifest_fields = dict(project.intake)
        manifest_fields.update(
            sources=tuple(
                source.model_copy(update={"asset": mapped(source.asset)})
                for source in project.intake.sources
            ),
            confirmed_digest="",
        )
        changes["intake"] = IntakeManifest.model_validate(manifest_fields)
        remapped = WBIntakeProject.model_validate({**dict(project), **changes})
        if project.intake.confirmed_digest:
            manifest_fields["confirmed_digest"] = intake_digest(remapped)
            changes["intake"] = IntakeManifest.model_validate(manifest_fields)
    if isinstance(project, WBProjectOCR) and project.ocr:
        changes["ocr"] = project.ocr.model_copy(update={"source": mapped(project.ocr.source)})
    sources: list[ArchiveSource] = []
    historical: dict[str, ImportedRun] = {}
    if isinstance(project, WBRestoredProject):
        sources.extend(
            s.model_copy(update={"archive": mapped(s.archive)}) for s in project.archive_sources
        )
        for item in project.imported_runs:
            historical[item.run.run_id] = item.model_copy(
                update={
                    "request": mapped(item.request) if item.request else None,
                    "result": mapped(item.result) if item.result else None,
                }
            )
    sources.append(
        ArchiveSource(
            archive=archive,
            project_id=project.project_id,
            revision=project.revision,
            format_version=staged.format_version,
        )
    )
    for record in staged.runs:
        historical[record.run.run_id] = ImportedRun(
            run=record.run,
            archive_sha256=archive.sha256,
            request=assets.get(record.request_sha256),
            result=assets.get(record.result_sha256),
            error=record.error,
        )
    return with_archive_history(
        project.model_copy(update=changes), tuple(sources), tuple(historical.values())
    )
