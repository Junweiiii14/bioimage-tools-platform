"""Versioned multi-source row plans; no rendered pixel can become a measurement source."""

from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator
from tool_contracts.api import AssetRef

from wb_tool.application.document import DocumentIO
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI


class FigureTemplate(DocumentIO):
    schema_version: int = Field(default=1, ge=1, le=1)
    name: str = Field(default="实验室行式模板", min_length=1, max_length=120)
    font: AssetRef | None = None
    font_size: int = Field(default=18, ge=8, le=96)
    label_width: int = Field(default=150, ge=30, le=1000)
    label_side: Literal["left", "right"] = "left"
    crop_height: int = Field(default=60, ge=2, le=4096)
    row_gap: int = Field(default=10, ge=2, le=500)
    figure_gap: int = Field(default=40, ge=2, le=1000)
    margin: int = Field(default=24, ge=2, le=1000)
    border: int = Field(default=1, ge=1, le=10)
    columns: int = Field(default=3, ge=1, le=12)
    dpi: int = Field(default=300, ge=72, le=1200)
    display_mapping: Literal["bt601_uint16_div257@1"] = "bt601_uint16_div257@1"


class FigureRow(DocumentIO):
    row_id: str = Field(min_length=1, max_length=80)
    source: AssetRef | None = None
    filename: str = Field(default="缺图", max_length=260)
    width: int = Field(default=0, ge=0, le=100000)
    height: int = Field(default=0, ge=0, le=100000)
    bit_depth: Literal[0, 8, 16] = 0
    figure: str = Field(default="Fig1", min_length=1, max_length=120)
    protein: str = Field(default="待填写", min_length=1, max_length=120)
    lane_count: int = Field(default=6, ge=1, le=96)
    empty_lanes: tuple[int, ...] = ()
    roi: LaneROI | None = None
    reviewed: bool = False
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def coherent(self) -> "FigureRow":
        if any(
            "\n" in name or "\r" in name or not name.strip() for name in (self.figure, self.protein)
        ):
            raise ValueError("Fig 与蛋白标签必须为非空单行文字")
        if len(set(self.empty_lanes)) != len(self.empty_lanes) or any(
            not 1 <= lane <= self.lane_count for lane in self.empty_lanes
        ):
            raise ValueError("空泳道编号必须唯一且位于 1..N，空位不会删除")
        if self.source is None:
            if self.roi is not None or self.width or self.height or self.bit_depth:
                raise ValueError("缺图占位不能携带裁剪或伪造原图尺寸")
        else:
            if not self.width or not self.height or not self.bit_depth:
                raise ValueError("原图必须有尺寸和位深")
            if self.roi is not None:
                if self.roi.lane_id != self.row_id:
                    raise ValueError("整行裁剪身份不一致")
                if self.roi.x1 > self.width or self.roi.y1 > self.height:
                    raise ValueError("整行裁剪超出原图")
                fixed_lane_grid(self.roi, self.lane_count)
            elif self.reviewed:
                raise ValueError("有原图的行须先确定裁剪范围再确认")
        return self

    def quantitative_lanes(self) -> tuple[LaneROI, ...]:
        if not self.reviewed or self.source is None or self.roi is None:
            raise ValueError("定量需要已审核的原图行，缺图不能转为零值")
        return fixed_lane_grid(self.roi, self.lane_count)


class WBFigureProject(DocumentIO):
    document_type: Literal["wb_figure_project"] = "wb_figure_project"
    schema_version: int = Field(default=1, ge=1, le=1)
    project_id: str = Field(min_length=1, max_length=80)
    name: str = Field(default="WB 项目", min_length=1, max_length=160)
    revision: int = Field(default=0, ge=0)
    rows: tuple[FigureRow, ...] = Field(default=(), max_length=512)
    figure_order: tuple[str, ...] = ()
    template: FigureTemplate = Field(default_factory=FigureTemplate)

    @model_validator(mode="after")
    def identities(self) -> "WBFigureProject":
        if len({row.row_id for row in self.rows}) != len(self.rows):
            raise ValueError("行身份重复；重复蛋白名应使用不同的行身份")
        if len(set(self.figure_order)) != len(self.figure_order) or set(self.figure_order) != {
            row.figure for row in self.rows
        }:
            raise ValueError("Fig 排序必须恰好包含全部分组")
        return self


@dataclass(frozen=True)
class FigurePlacement:
    figure: str
    x: int
    y: int
    width: int
    rows: tuple[FigureRow, ...]


@dataclass(frozen=True)
class FigureLayout:
    width: int
    height: int
    placements: tuple[FigurePlacement, ...]


def plan_figure_layout(project: WBFigureProject, *, require_review: bool = True) -> FigureLayout:
    """Use original crop sizes, never stretch rows to make different lanes look aligned."""
    if not project.rows:
        raise ValueError("项目还没有行")
    template = project.template
    x = y = template.margin
    bottom = y
    maximum_x = x
    placements: list[FigurePlacement] = []
    for index, name in enumerate(project.figure_order):
        rows = tuple(row for row in project.rows if row.figure == name)
        if require_review and any(not row.reviewed for row in rows):
            raise ValueError(f"{name} 仍有未审核行")
        if len({row.lane_count for row in rows}) != 1:
            raise ValueError(f"{name} 各行泳道数不同，请核对实验信息")
        widths: set[int] = set()
        for row in rows:
            if row.source is not None:
                if row.roi is None:
                    raise ValueError(f"{row.protein} 尚未框选整行范围")
                if row.roi.y1 - row.roi.y0 != template.crop_height:
                    raise ValueError(f"{row.protein} 裁剪高度应为 {template.crop_height} 原图像素")
                widths.add(row.roi.width)
        if len(widths) != 1:
            raise ValueError(f"{name} 需要至少一张原图且各行宽度一致；不能静默拉伸对齐")
        width = next(iter(widths))
        if index and index % template.columns == 0:
            x, y = template.margin, bottom + template.figure_gap
        placements.append(FigurePlacement(name, x, y, width, rows))
        panel_height = (
            template.font_size
            + template.row_gap
            + len(rows) * (template.crop_height + template.row_gap + 2 * template.border)
        )
        bottom = max(bottom, y + panel_height)
        x += template.label_width + width + 2 * template.border + template.figure_gap
        maximum_x = max(maximum_x, x - template.figure_gap)
    width, height = maximum_x + template.margin, bottom + template.margin
    if width * height > 32_000_000 or max(width, height) > 32768:
        raise ValueError("拼图超出 3200 万像素/32768 边长预算，请拆分项目或增加列数")
    return FigureLayout(width, height, tuple(placements))


@dataclass(frozen=True)
class FigureRender:
    width: int
    height: int
    rgb: bytes
    manifest_json: str


@dataclass(frozen=True)
class FigureSourcePath:
    sha256: str
    path: str
