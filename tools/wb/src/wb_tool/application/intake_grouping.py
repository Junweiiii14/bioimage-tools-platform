"""Acquisition drafts retain incomplete user choices without inventing executable rows."""

import re
from pathlib import PurePosixPath

from pydantic import Field, model_validator

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


class IntakeGrouping(DocumentIO):
    schema_version: int = Field(default=1, ge=1, le=1)
    figures: tuple[IntakeDraftFigure, ...] = Field(default=(), max_length=512)
    groups: tuple[IntakeAcquisitionGroup, ...] = Field(default=(), max_length=512)

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
        return self
