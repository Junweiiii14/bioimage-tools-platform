"""Acquisition drafts retain incomplete user choices without inventing executable rows."""

import re
from pathlib import PurePosixPath
from typing import cast

from pydantic import Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from wb_tool.application.document import DocumentIO


def acquisition_key(relative_path: str) -> str:
    """Keep directory and acquisition identifier; a protein label alone never joins batches."""
    path = PurePosixPath(relative_path)
    stem = re.sub(r"\s*\([123]\)$", "", path.stem)
    stem = re.sub(r"_(merge|sample|white)_?\(16bit\)$", "", stem, flags=re.I)
    return (path.parent / stem).as_posix()


def draft_label(value: str) -> None:
    if any(character in value for character in "\r\n\x00"):
        raise ValueError("名称须为单行文字")


class IntakeDraftFigure(DocumentIO):
    figure_id: str = Field(min_length=1, max_length=80)
    label: str = Field(default="", max_length=120)
    lane_count: int | None = Field(default=None, ge=1, le=96)

    @model_validator(mode="after")
    def valid_label(self) -> "IntakeDraftFigure":
        draft_label(self.label)
        return self


class IntakeAcquisitionGroup(DocumentIO):
    group_id: str = Field(min_length=1, max_length=80)
    source_ids: tuple[str, ...] = Field(min_length=1, max_length=512)
    figure_id: str | None = Field(default=None, min_length=1, max_length=80)
    protein_label: str = Field(default="", max_length=120)
    selected_source_id: str | None = Field(default=None, min_length=1, max_length=80)
    region_index: int | None = Field(default=None, ge=0, le=7)
    reuse_confirmed: bool = False

    @model_validator(mode="after")
    def membership(self) -> "IntakeAcquisitionGroup":
        draft_label(self.protein_label)
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("采集组内来源重复")
        if self.selected_source_id is not None and self.selected_source_id not in self.source_ids:
            raise ValueError("裁剪原图必须属于当前采集组")
        if self.region_index is not None and self.selected_source_id is None:
            raise ValueError("目标候选必须绑定已选择的原图")
        return self


class IntakeSequenceProtein(DocumentIO):
    entry_id: str = Field(min_length=1, max_length=80)
    figure_id: str = Field(min_length=1, max_length=80)
    label: str = Field(default="", max_length=120)

    @model_validator(mode="after")
    def valid_label(self) -> "IntakeSequenceProtein":
        draft_label(self.label)
        return self


class IntakeGrouping(DocumentIO):
    schema_version: int = Field(default=1, ge=1, le=2)
    figures: tuple[IntakeDraftFigure, ...] = Field(default=(), max_length=512)
    groups: tuple[IntakeAcquisitionGroup, ...] = Field(default=(), max_length=512)
    sequence: tuple[IntakeSequenceProtein, ...] | None = Field(default=None, max_length=512)
    excluded_group_ids: tuple[str, ...] = Field(default=(), max_length=512)

    @model_serializer(mode="wrap")
    def serialize_grouping(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        fields = cast(dict[str, object], handler(self))
        if self.schema_version == 1:
            fields.pop("sequence", None)
            fields.pop("excluded_group_ids", None)
        return fields

    @model_validator(mode="after")
    def identities(self) -> "IntakeGrouping":
        figures = {figure.figure_id for figure in self.figures}
        source_ids = [source_id for group in self.groups for source_id in group.source_ids]
        if (
            len(figures) != len(self.figures)
            or len({group.group_id for group in self.groups}) != len(self.groups)
            or len(set(source_ids)) != len(source_ids)
        ):
            raise ValueError("Fig、采集组或来源身份重复")
        if any(
            group.figure_id is not None and group.figure_id not in figures for group in self.groups
        ):
            raise ValueError("采集组所属Fig不存在")
        labels = [figure.label.casefold() for figure in self.figures if figure.label.strip()]
        if len(labels) != len(set(labels)):
            raise ValueError("Fig显示名不能重复")
        if self.schema_version == 1:
            if self.sequence is not None or self.excluded_group_ids:
                raise ValueError("蛋白顺序配置必须使用采集组格式v2")
            return self
        if self.sequence is None:
            raise ValueError("顺序草稿必须保留蛋白顺序配置")
        if len({p.entry_id for p in self.sequence}) != len(self.sequence) or any(
            p.figure_id not in figures for p in self.sequence
        ):
            raise ValueError("顺序蛋白身份重复或所属Fig不存在")
        ordered = tuple(
            p for f in self.figures for p in self.sequence if p.figure_id == f.figure_id
        )
        if ordered != self.sequence:
            raise ValueError("蛋白顺序必须遵循顶部Fig顺序")
        entries = [p for p in self.sequence if p.label.strip()]
        for index, group in enumerate(self.groups):
            entry = entries[index] if index < len(entries) else None
            if (group.figure_id, group.protein_label) != (
                entry.figure_id if entry else None,
                entry.label.strip() if entry else "",
            ):
                raise ValueError("采集组对应必须匹配Fig蛋白顺序投影")
        unused = {g.group_id for g in self.groups if g.figure_id is None}
        if len(set(self.excluded_group_ids)) != len(self.excluded_group_ids) or not set(
            self.excluded_group_ids
        ).issubset(unused):
            raise ValueError("仅能明确排除未分配的采集组")
        return self


def configure_intake_sequence(
    grouping: IntakeGrouping,
    figures: tuple[IntakeDraftFigure, ...],
    sequence: tuple[IntakeSequenceProtein, ...],
    *,
    excluded_group_ids: tuple[str, ...] = (),
) -> IntakeGrouping:
    """Project ordered names onto stable acquisition identities, retaining source choices."""
    if any(p.figure_id not in {f.figure_id for f in figures} for p in sequence):
        raise ValueError("顺序蛋白所属Fig不存在")
    sequence = tuple(p for f in figures for p in sequence if p.figure_id == f.figure_id)
    entries = [p for p in sequence if p.label.strip()]
    groups: list[IntakeAcquisitionGroup] = []
    for index, group in enumerate(grouping.groups):
        entry = entries[index] if index < len(entries) else None
        figure_id = entry.figure_id if entry else None
        label = entry.label.strip() if entry else ""
        changed = group.figure_id != figure_id
        groups.append(
            IntakeAcquisitionGroup.model_validate(
                {
                    **dict(group),
                    "figure_id": figure_id,
                    "protein_label": label,
                    "region_index": None if changed else group.region_index,
                }
            )
        )
    return IntakeGrouping(
        schema_version=2,
        figures=figures,
        groups=tuple(groups),
        sequence=sequence,
        excluded_group_ids=excluded_group_ids,
    )


def validate_intake_sequence(grouping: IntakeGrouping) -> None:
    if grouping.schema_version != 2:
        return
    entries = [p for p in grouping.sequence or () if p.label.strip()]
    if len(entries) > len(grouping.groups):
        raise ValueError(f"蛋白条目缺少{len(entries) - len(grouping.groups)}个采集组")
    for figure in grouping.figures:
        if not any(p.figure_id == figure.figure_id for p in entries):
            raise ValueError(f"{figure.label or '未命名Fig'}至少需要一个蛋白名称")
        if not figure.label.strip() or figure.lane_count is None:
            raise ValueError("请填写每个Fig名称与Fig级N")
    unused = {g.group_id for g in grouping.groups if g.figure_id is None}
    if unused != set(grouping.excluded_group_ids):
        raise ValueError(f"请明确确认{len(unused)}个剩余采集组不纳入本次")
