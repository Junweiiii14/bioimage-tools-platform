"""Explicit instrument intake plans, without inferred labels or quantitative operations."""

import json
from collections import Counter
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Literal, cast

from pydantic import Field, SerializerFunctionWrapHandler, model_serializer, model_validator
from tool_contracts.api import AssetRef

from wb_tool.application.discovery import ExportDiscovery, ExportSelection
from wb_tool.application.document import DocumentIO
from wb_tool.application.fig_quant import WBPartitionProject
from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.intake_grouping import (
    IntakeAcquisitionGroup,
    IntakeGrouping,
    acquisition_key,
)


def _label(value: str) -> None:
    if not value.strip() or any(character in value for character in "\r\n\x00"):
        raise ValueError("Fig 与蛋白名称必须是非空单行文字")


class IntakeFigure(DocumentIO):
    figure_id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=120)
    lane_count: int = Field(ge=1, le=96)

    @model_validator(mode="after")
    def valid_label(self) -> "IntakeFigure":
        _label(self.label)
        return self


class IntakeProtein(DocumentIO):
    protein_id: str = Field(min_length=1, max_length=80)
    figure_id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def valid_label(self) -> "IntakeProtein":
        _label(self.label)
        return self


class IntakeSource(DocumentIO):
    source_id: str = Field(min_length=1, max_length=80)
    asset: AssetRef
    original_name: str = Field(min_length=1, max_length=260)
    relative_path: str = Field(min_length=1, max_length=4096)
    width: int = Field(ge=1, le=100000)
    height: int = Field(ge=1, le=100000)
    bit_depth: Literal[8, 16]

    @model_validator(mode="after")
    def original_path(self) -> "IntakeSource":
        path = PurePosixPath(self.relative_path)
        if (
            path.is_absolute()
            or any(part in ("", ".", "..") for part in self.relative_path.split("/"))
            or any(character in self.relative_path for character in "\\:\x00\r\n")
            or path.name != self.original_name
        ):
            raise ValueError("仪器来源需保留匹配原名的安全相对路径，不能包含绝对路径或越界段")
        return self


class IntakeAssignment(DocumentIO):
    protein_id: str = Field(min_length=1, max_length=80)
    source_id: str = Field(min_length=1, max_length=80)
    reuse_confirmed: bool = False


def grouping_plan(
    grouping: IntakeGrouping,
) -> tuple[tuple[IntakeFigure, ...], tuple[IntakeProtein, ...], tuple[IntakeAssignment, ...]]:
    """Derive only complete rows; the incomplete draft remains the sole editing authority."""
    figures: list[IntakeFigure] = []
    proteins: list[IntakeProtein] = []
    assignments: list[IntakeAssignment] = []
    for figure in grouping.figures:
        if not figure.label.strip() or figure.lane_count is None:
            continue
        ready = [
            group
            for group in grouping.groups
            if group.figure_id == figure.figure_id
            and group.protein_label.strip()
            and group.selected_source_id is not None
        ]
        if not ready:
            continue
        figures.append(
            IntakeFigure(
                figure_id=figure.figure_id, label=figure.label, lane_count=figure.lane_count
            )
        )
        for group in ready:
            proteins.append(
                IntakeProtein(
                    protein_id=group.group_id, figure_id=figure.figure_id, label=group.protein_label
                )
            )
            assignments.append(
                IntakeAssignment(
                    protein_id=group.group_id,
                    source_id=cast(str, group.selected_source_id),
                    reuse_confirmed=group.reuse_confirmed,
                )
            )
    return tuple(figures), tuple(proteins), tuple(assignments)


class IntakeManifest(DocumentIO):
    schema_version: int = Field(default=1, ge=1, le=3)
    discovery: ExportDiscovery | None = None
    grouping: IntakeGrouping | None = None
    figures: tuple[IntakeFigure, ...] = Field(default=(), max_length=512)
    proteins: tuple[IntakeProtein, ...] = Field(default=(), max_length=512)
    sources: tuple[IntakeSource, ...] = Field(default=(), max_length=512)
    assignments: tuple[IntakeAssignment, ...] = Field(default=(), max_length=512)
    confirmed_digest: str = Field(default="", pattern="^(?:[0-9a-f]{64})?$")

    @model_serializer(mode="wrap")
    def serialize_manifest(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        fields = cast(dict[str, object], handler(self))
        if self.schema_version == 1:
            fields.pop("discovery", None)
        if self.schema_version < 3:
            fields.pop("grouping", None)
        return fields

    @model_validator(mode="after")
    def identities(self) -> "IntakeManifest":
        figures = {figure.figure_id: figure for figure in self.figures}
        proteins = {protein.protein_id: protein for protein in self.proteins}
        sources = {source.source_id: source for source in self.sources}
        if self.schema_version == 1 and self.discovery is not None:
            raise ValueError("识别建议必须使用清单格式v2")
        if self.grouping is not None:
            if self.schema_version != 3:
                raise ValueError("采集组草稿必须使用清单格式v3")
            if any(
                sid not in sources for group in self.grouping.groups for sid in group.source_ids
            ):
                raise ValueError("采集组引用不存在的来源")
            expected = grouping_plan(self.grouping)
            if (self.figures, self.proteins, self.assignments) != expected:
                raise ValueError("执行清单必须匹配采集组草稿投影")
        if self.discovery is not None:
            for item in self.discovery.observations:
                source = sources.get(item.source_id)
                if source is None or source.asset.sha256 != item.sha256:
                    raise ValueError("识别建议不匹配当前原图来源")
                if any(r.x1 > source.width or r.y1 > source.height for r in item.regions):
                    raise ValueError("识别区域超出原图")
        if (
            len(figures) != len(self.figures)
            or len(proteins) != len(self.proteins)
            or len(sources) != len(self.sources)
        ):
            raise ValueError("Fig、蛋白或原图的稳定身份重复")
        if len({figure.label.casefold() for figure in self.figures}) != len(self.figures):
            raise ValueError("Fig 显示名不能重复；同名蛋白可以使用独立身份")
        if any(protein.figure_id not in figures for protein in self.proteins):
            raise ValueError("蛋白所属 Fig 不存在")
        if len({binding.protein_id for binding in self.assignments}) != len(self.assignments):
            raise ValueError("每个蛋白只能分配一个原图来源")
        if any(
            binding.protein_id not in proteins or binding.source_id not in sources
            for binding in self.assignments
        ):
            raise ValueError("分配引用不存在的蛋白或原图")
        content: dict[str, tuple[int, int, int, int]] = {}
        for source in self.sources:
            signature = source.width, source.height, source.bit_depth, source.asset.size_bytes
            if content.setdefault(source.asset.sha256, signature) != signature:
                raise ValueError("同一原图 SHA 的尺寸、位深或字节数不一致")
        counts = Counter(sources[binding.source_id].asset.sha256 for binding in self.assignments)
        if any(
            counts[sources[binding.source_id].asset.sha256] > 1 and not binding.reuse_confirmed
            for binding in self.assignments
        ):
            raise ValueError("同一原图内容用于多个蛋白须明确确认复用")
        return self


def intake_manifest_digest(project_id: str, manifest: IntakeManifest) -> str:
    data = {
        "project_id": project_id,
        "intake": manifest.model_dump(mode="json", exclude={"confirmed_digest"}),
    }
    return sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def intake_project_rows(manifest: IntakeManifest) -> tuple[FigureRow, ...]:
    figures = {figure.figure_id: figure for figure in manifest.figures}
    sources = {source.source_id: source for source in manifest.sources}
    bindings = {binding.protein_id: binding.source_id for binding in manifest.assignments}
    rows: list[FigureRow] = []
    for figure in manifest.figures:
        for protein in manifest.proteins:
            if protein.figure_id != figure.figure_id:
                continue
            source = sources.get(bindings.get(protein.protein_id, ""))
            rows.append(
                FigureRow(
                    row_id=protein.protein_id,
                    source=source.asset if source else None,
                    filename=source.original_name if source else "缺图",
                    width=source.width if source else 0,
                    height=source.height if source else 0,
                    bit_depth=source.bit_depth if source else 0,
                    figure=figures[protein.figure_id].label,
                    protein=protein.label,
                    lane_count=figures[protein.figure_id].lane_count,
                )
            )
    return tuple(rows)


def _has_processing(project: WBFigureProject) -> bool:
    return any(row.roi or row.reviewed or row.empty_lanes for row in project.rows) or any(
        getattr(project, field, None)
        for field in (
            "suggestions",
            "analyses",
            "ocr",
            "normalizations",
            "automatic_rows",
            "partition_sources",
            "imported_runs",
        )
    )


class WBIntakeProject(WBPartitionProject):
    schema_version: int = Field(default=10, ge=10, le=10)
    intake: IntakeManifest = Field(default_factory=IntakeManifest)

    @model_validator(mode="after")
    def intake_projection(self) -> "WBIntakeProject":
        if _has_processing(self):
            raise ValueError("当前仪器导入阶段不能携带裁剪、审核或定量结果；请保留原项目")
        expected = intake_project_rows(self.intake)
        order = tuple(dict.fromkeys(row.figure for row in expected))
        if self.rows != expected or self.figure_order != order:
            raise ValueError("项目行与仪器清单不一致；请通过清单修改名称和分配")
        if self.intake.confirmed_digest:
            if self.intake.confirmed_digest != intake_manifest_digest(self.project_id, self.intake):
                raise ValueError("仪器清单已改变，原确认已过期")
            validate_intake_complete(self.intake)
        return self


def validate_intake_complete(manifest: IntakeManifest) -> None:
    if manifest.grouping is not None:
        figures = {figure.figure_id: figure for figure in manifest.grouping.figures}
        for group in manifest.grouping.groups:
            if group.figure_id is None:
                if group.selected_source_id is not None:
                    raise ValueError("已选裁剪原图仍未归入Fig")
                continue
            figure = figures[group.figure_id]
            if not (
                figure.label.strip()
                and figure.lane_count is not None
                and group.protein_label.strip()
                and group.selected_source_id is not None
            ):
                raise ValueError("请补齐已归Fig采集组的蛋白、裁剪原图与Fig级N")
    assigned = {binding.protein_id for binding in manifest.assignments}
    if not manifest.figures or not manifest.proteins:
        raise ValueError("请先填写 Fig、蛋白和样本槽位数")
    if any(
        not any(protein.figure_id == figure.figure_id for protein in manifest.proteins)
        for figure in manifest.figures
    ):
        raise ValueError("每个 Fig 至少需要一个蛋白")
    if assigned != {protein.protein_id for protein in manifest.proteins}:
        raise ValueError("仍有蛋白未分配原图，请完成对应关系后确认")


def create_intake(project: WBFigureProject) -> WBIntakeProject:
    """Start only from an empty project; never migrate or overwrite existing results."""
    if isinstance(project, WBIntakeProject):
        return WBIntakeProject.model_validate(dict(project))
    if project.rows or _has_processing(project) or getattr(project, "archive_sources", ()):
        raise ValueError("仪器导入须新建空项目；已有原图、裁剪或历史结果不能静默转换")
    fields = dict(project)
    fields.update(schema_version=10, intake=IntakeManifest())
    return WBIntakeProject.model_validate(fields)


def intake_digest(project: WBIntakeProject) -> str:
    return intake_manifest_digest(project.project_id, project.intake)


def _current(project: WBIntakeProject, expected_digest: str) -> None:
    WBIntakeProject.model_validate(dict(project))
    if not expected_digest or intake_digest(project) != expected_digest:
        raise ValueError("仪器清单已修改，请刷新后重新分配或确认")


def _updated(project: WBIntakeProject, manifest: IntakeManifest) -> WBIntakeProject:
    rows = intake_project_rows(manifest)
    fields = dict(project)
    fields.update(
        intake=manifest, rows=rows, figure_order=tuple(dict.fromkeys(r.figure for r in rows))
    )
    return WBIntakeProject.model_validate(fields)


def replace_intake_plan(
    project: WBIntakeProject,
    figures: tuple[IntakeFigure, ...],
    proteins: tuple[IntakeProtein, ...],
    *,
    expected_digest: str,
) -> WBIntakeProject:
    """Replace the entire explicit plan atomically, preserving stable identities and sources."""
    _current(project, expected_digest)
    ids = {protein.protein_id for protein in proteins}
    if any(binding.protein_id not in ids for binding in project.intake.assignments):
        raise ValueError("删除已分配蛋白前请先明确解除对应关系")
    if figures == project.intake.figures and proteins == project.intake.proteins:
        return project
    fields = dict(project.intake)
    fields.update(figures=figures, proteins=proteins, confirmed_digest="")
    return _updated(project, IntakeManifest.model_validate(fields))


def register_intake_source(
    project: WBIntakeProject, source: IntakeSource, *, expected_digest: str
) -> WBIntakeProject:
    _current(project, expected_digest)
    previous = next((s for s in project.intake.sources if s.source_id == source.source_id), None)
    if previous is not None:
        if previous == source:
            return project
        raise ValueError("原图身份已存在，不能覆盖原始来源记录")
    fields = dict(project.intake)
    fields.update(sources=(*project.intake.sources, source), confirmed_digest="")
    return _updated(project, IntakeManifest.model_validate(fields))


def assign_intake_sources(
    project: WBIntakeProject,
    bindings: tuple[IntakeAssignment, ...],
    *,
    expected_digest: str,
    replace: bool = False,
    allow_reuse: bool = False,
) -> WBIntakeProject:
    _current(project, expected_digest)
    if not bindings or len({b.protein_id for b in bindings}) != len(bindings):
        raise ValueError("请选择互不重复的蛋白目标进行批量分配")
    proteins = {protein.protein_id for protein in project.intake.proteins}
    sources = {source.source_id: source for source in project.intake.sources}
    assigned = {binding.protein_id: binding for binding in project.intake.assignments}
    for binding in bindings:
        if binding.protein_id not in proteins or binding.source_id not in sources:
            raise ValueError("分配目标或原图不存在，请重新选择")
        previous = assigned.get(binding.protein_id)
        if previous and previous.source_id != binding.source_id and not replace:
            raise ValueError("蛋白已有原图；请明确选择重新分配")
        assigned[binding.protein_id] = IntakeAssignment(
            protein_id=binding.protein_id,
            source_id=binding.source_id,
            reuse_confirmed=bool(
                previous and previous.source_id == binding.source_id and previous.reuse_confirmed
            ),
        )
    counts = Counter(sources[binding.source_id].asset.sha256 for binding in assigned.values())
    for protein_id, binding in assigned.items():
        if counts[sources[binding.source_id].asset.sha256] > 1:
            if not allow_reuse and not binding.reuse_confirmed:
                raise ValueError("该原图内容已分配；如需用于多个蛋白，请明确确认复用")
            assigned[protein_id] = binding.model_copy(update={"reuse_confirmed": True})
    ordered = tuple(
        assigned[p.protein_id] for p in project.intake.proteins if p.protein_id in assigned
    )
    if ordered == project.intake.assignments:
        return project
    fields = dict(project.intake)
    fields.update(assignments=ordered, confirmed_digest="")
    return _updated(project, IntakeManifest.model_validate(fields))


def unassign_intake_sources(
    project: WBIntakeProject, protein_ids: tuple[str, ...], *, expected_digest: str
) -> WBIntakeProject:
    _current(project, expected_digest)
    assigned = {binding.protein_id for binding in project.intake.assignments}
    if (
        not protein_ids
        or len(set(protein_ids)) != len(protein_ids)
        or not set(protein_ids) <= assigned
    ):
        raise ValueError("请明确选择已分配的蛋白解除对应关系")
    fields = dict(project.intake)
    fields.update(
        assignments=tuple(b for b in project.intake.assignments if b.protein_id not in protein_ids),
        confirmed_digest="",
    )
    return _updated(project, IntakeManifest.model_validate(fields))


def confirm_intake(project: WBIntakeProject, *, expected_digest: str) -> WBIntakeProject:
    _current(project, expected_digest)
    validate_intake_complete(project.intake)
    fields = dict(project.intake)
    fields["confirmed_digest"] = intake_digest(project)
    return _updated(project, IntakeManifest.model_validate(fields))


def intake_snapshot(project: WBIntakeProject) -> dict[str, object]:
    """JSON-compatible presentation; no thumbnails, source pixels, sample order or OCR."""
    data: dict[str, object] = project.intake.model_dump(mode="json")
    data.update(
        digest=intake_digest(project),
        confirmed=bool(project.intake.confirmed_digest),
        project_id=project.project_id,
    )
    if project.intake.grouping is not None or not project.intake.proteins:
        data["grouped_draft"] = intake_grouping(project).model_dump(mode="json")
    return data


def intake_grouping(project: WBIntakeProject) -> IntakeGrouping:
    """Offer conservative filename/directory groups without decoding or choosing a source."""
    type(project).model_validate(dict(project))
    grouping = project.intake.grouping
    if grouping is None and project.intake.proteins:
        raise ValueError("旧行式项目保留原编辑入口，不能猜测采集组归属")
    groups = list(grouping.groups if grouping else ())
    included = {sid for group in groups for sid in group.source_ids}
    buckets: dict[str, list[str]] = {}
    for source in project.intake.sources:
        if source.source_id not in included:
            key = acquisition_key(source.relative_path)
            buckets.setdefault(key, []).append(source.source_id)
    for key, ids in buckets.items():
        group_id = "group-" + sha256((project.project_id + ":" + key).encode()).hexdigest()[:32]
        index = next((i for i, group in enumerate(groups) if group.group_id == group_id), None)
        if index is None:
            groups.append(IntakeAcquisitionGroup(group_id=group_id, source_ids=tuple(ids)))
        else:
            groups[index] = IntakeAcquisitionGroup.model_validate(
                {**dict(groups[index]), "source_ids": (*groups[index].source_ids, *ids)}
            )
    return IntakeGrouping(figures=grouping.figures if grouping else (), groups=tuple(groups))


def save_intake_grouping(
    project: WBIntakeProject,
    grouping: IntakeGrouping,
    *,
    expected_digest: str,
    allow_reuse: bool = False,
) -> WBIntakeProject:
    """Atomically persist incomplete choices and their validated execution projection."""
    _current(project, expected_digest)
    if project.schema_version != 10:
        raise ValueError("执行修订须先另存编辑副本，不能覆盖阶段历史")
    if project.intake.grouping is None and project.intake.proteins:
        raise ValueError("旧行式项目请沿用原编辑入口")
    grouping = IntakeGrouping.model_validate(dict(grouping))
    sources = {source.source_id: source for source in project.intake.sources}
    if {sid for group in grouping.groups for sid in group.source_ids} != sources.keys():
        raise ValueError("采集组草稿必须保留全部来源，包括未选择图像")
    previous = (
        {group.group_id: group for group in project.intake.grouping.groups}
        if project.intake.grouping
        else {}
    )
    figures = {figure.figure_id: figure for figure in grouping.figures}
    old_figures = (
        {figure.figure_id: figure for figure in project.intake.grouping.figures}
        if project.intake.grouping
        else {}
    )
    counts = Counter(
        sources[group.selected_source_id].asset.sha256
        for group in grouping.groups
        if group.selected_source_id is not None
    )
    groups: list[IntakeAcquisitionGroup] = []
    selections: list[ExportSelection] = []
    observations = (
        {item.source_id: item for item in project.intake.discovery.observations}
        if project.intake.discovery
        else {}
    )
    for group in grouping.groups:
        old = previous.get(group.group_id)
        region_index = group.region_index
        if old is not None and (
            old.selected_source_id != group.selected_source_id
            or (
                old_figures.get(old.figure_id or "")
                and figures.get(group.figure_id or "")
                and old_figures[cast(str, old.figure_id)].lane_count
                != figures[cast(str, group.figure_id)].lane_count
            )
        ):
            region_index = None
        reused = (
            group.selected_source_id is not None
            and counts[sources[group.selected_source_id].asset.sha256] > 1
        )
        confirmed_reuse = bool(
            reused
            and (
                allow_reuse
                or (
                    old
                    and old.selected_source_id == group.selected_source_id
                    and old.reuse_confirmed
                )
            )
        )
        if reused and not confirmed_reuse:
            raise ValueError("相同原图内容用于多个蛋白须明确确认复用")
        group = IntakeAcquisitionGroup.model_validate(
            {**dict(group), "region_index": region_index, "reuse_confirmed": confirmed_reuse}
        )
        groups.append(group)
        observation = observations.get(group.selected_source_id or "")
        if observation and (observation.role == "reference" or observation.error):
            raise ValueError("当前选择是参考成品或读取失败来源，请核对原图")
        if group.region_index is not None and (
            observation is None or group.region_index >= len(observation.regions)
        ):
            raise ValueError("目标区域不匹配当前原图建议")
        figure = figures.get(group.figure_id or "")
        if (
            observation
            and figure
            and figure.lane_count is not None
            and figure.label.strip()
            and group.protein_label.strip()
        ):
            selections.append(
                ExportSelection(
                    source_id=observation.source_id,
                    figure_label=figure.label,
                    protein_label=group.protein_label,
                    lane_count=figure.lane_count,
                    region_index=group.region_index,
                )
            )
    grouping = IntakeGrouping(figures=grouping.figures, groups=tuple(groups))
    if grouping == project.intake.grouping:
        return project
    figures_plan, proteins, bindings = grouping_plan(grouping)
    fields = dict(project.intake)
    fields.update(
        schema_version=3,
        grouping=grouping,
        figures=figures_plan,
        proteins=proteins,
        assignments=bindings,
        confirmed_digest="",
    )
    if project.intake.discovery is not None:
        fields["discovery"] = ExportDiscovery.model_validate(
            {**dict(project.intake.discovery), "selections": tuple(selections)}
        )
    return _updated(project, IntakeManifest.model_validate(fields))


def install_export_discovery(
    project: WBIntakeProject, discovery: ExportDiscovery, *, expected_digest: str
) -> WBIntakeProject:
    """Save unconfirmed observations without changing assignments, N or crop review."""
    _current(project, expected_digest)
    if project.schema_version != 10:
        raise ValueError("请先返回清单修改再识别来源")
    fields = dict(project.intake)
    fields.update(
        schema_version=max(2, project.intake.schema_version),
        discovery=discovery,
        confirmed_digest="",
    )
    return _updated(project, IntakeManifest.model_validate(fields))


def accept_export_selections(
    project: WBIntakeProject, selections: tuple[ExportSelection, ...], *, expected_digest: str
) -> WBIntakeProject:
    """Explicit consolidated confirmation starts a new plan, never replaces old rows."""
    _current(project, expected_digest)
    if project.schema_version != 10 or project.intake.figures or project.intake.assignments:
        raise ValueError("集中建立仅用于空清单；已有清单请使用原图分配入口")
    if project.intake.discovery is None or not selections:
        raise ValueError("请先识别原图并填写待确认项")
    discovery = ExportDiscovery.model_validate(
        {**dict(project.intake.discovery), "selections": selections}
    )
    figures: dict[str, IntakeFigure] = {}
    proteins: list[IntakeProtein] = []
    assignments: list[IntakeAssignment] = []
    for item in selections:
        figure_id = "fig-" + sha256(item.figure_label.casefold().encode()).hexdigest()[:24]
        figure = IntakeFigure(
            figure_id=figure_id, label=item.figure_label, lane_count=item.lane_count
        )
        if figure_id in figures and figures[figure_id] != figure:
            raise ValueError("同一Fig必须明确使用相同的名称和N")
        figures[figure_id] = figure
        protein_id = "row-" + sha256(item.source_id.encode()).hexdigest()[:24]
        proteins.append(
            IntakeProtein(protein_id=protein_id, figure_id=figure_id, label=item.protein_label)
        )
        assignments.append(IntakeAssignment(protein_id=protein_id, source_id=item.source_id))
    fields = dict(project.intake)
    fields.update(
        schema_version=2,
        discovery=discovery,
        figures=tuple(figures.values()),
        proteins=tuple(proteins),
        assignments=tuple(assignments),
        confirmed_digest="",
    )
    return _updated(project, IntakeManifest.model_validate(fields))
