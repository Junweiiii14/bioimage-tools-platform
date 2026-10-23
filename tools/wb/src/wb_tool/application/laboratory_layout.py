"""Explicit display segments; measurement row identities and original pixel geometry stay intact."""

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Literal, cast

from pydantic import Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from wb_tool.application.document import DocumentIO
from wb_tool.application.figure_project import (
    FigureLayout,
    FigurePlacement,
    FigureRow,
    WBFigureProject,
)
from wb_tool.application.project_restore import ArchiveSource, WBRestoredProject
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI


class FigureLayoutStyle(DocumentIO):
    schema_version: int = Field(default=1, ge=1, le=1)
    display_policy: Literal["native_samples@1", "standard_lane_ratio@1"] = "native_samples@1"
    lane_unit: int = Field(default=120, ge=5, le=1200, multiple_of=5)
    heading_size: int = Field(default=26, ge=8, le=128)
    segment_gap: int = Field(default=8, ge=2, le=500)
    label_alignment: Literal["left", "right"] = "right"
    flow: Literal["rows", "columns"] = "columns"


class DisplayFrame(DocumentIO):
    sampling_policy: Literal["within_roi@1", "within_source@2"] = "within_roi@1"
    center_x: float
    center_y: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    angle_degrees: float = Field(ge=-30, le=30)

    @model_serializer(mode="wrap")
    def preserve_legacy_shape(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        result = cast(dict[str, object], handler(self))
        if self.sampling_policy == "within_roi@1":
            result.pop("sampling_policy", None)
        return result

    def corners(self) -> tuple[tuple[float, float], ...]:
        angle = radians(self.angle_degrees)
        c, s = cos(angle), sin(angle)
        return tuple(
            (self.center_x + c * x - s * y, self.center_y + s * x + c * y)
            for x, y in (
                (-self.width / 2, -self.height / 2),
                (self.width / 2, -self.height / 2),
                (self.width / 2, self.height / 2),
                (-self.width / 2, self.height / 2),
            )
        )


class FigureSlice(DocumentIO):
    display_frame: DisplayFrame | None = None
    row_id: str = Field(min_length=1, max_length=80)
    figure: str = Field(min_length=1, max_length=120)
    line: int = Field(ge=1, le=512)
    position: int = Field(ge=1, le=96)
    first_lane: int = Field(ge=1, le=96)
    last_lane: int = Field(ge=1, le=96)

    @model_validator(mode="after")
    def ordered(self) -> "FigureSlice":
        if self.first_lane > self.last_lane:
            raise ValueError("分段泳道起点不能大于终点")
        return self


class FigureColumn(DocumentIO):
    figure: str = Field(min_length=1, max_length=120)
    column: int = Field(ge=1, le=12)


class FigureComposition(DocumentIO):
    schema_version: int = Field(default=1, ge=1, le=1)
    slices: tuple[FigureSlice, ...] = Field(default=(), max_length=4096)
    columns: tuple[FigureColumn, ...] = Field(default=(), max_length=512)


class WBLayoutProject(WBRestoredProject):
    schema_version: int = Field(default=7, ge=7, le=7)
    archive_sources: tuple[ArchiveSource, ...] = Field(default=(), max_length=8)
    layout_style: FigureLayoutStyle = Field(default_factory=FigureLayoutStyle)
    composition: FigureComposition = Field(default_factory=FigureComposition)

    def crop_height_for(self, row: FigureRow) -> int:
        return row.roi.y1 - row.roi.y0 if row.roi else self.template.crop_height


def initial_composition(project: WBFigureProject) -> FigureComposition:
    counts: dict[str, int] = {}
    slices: list[FigureSlice] = []
    for row in project.rows:
        counts[row.figure] = counts.get(row.figure, 0) + 1
        slices.append(
            FigureSlice(
                row_id=row.row_id,
                figure=row.figure,
                line=counts[row.figure],
                position=1,
                first_lane=1,
                last_lane=row.lane_count,
            )
        )
    return FigureComposition(
        slices=tuple(slices),
        columns=tuple(
            FigureColumn(figure=name, column=index % project.template.columns + 1)
            for index, name in enumerate(project.figure_order)
        ),
    )


def ordered_quant_rows(project: WBFigureProject) -> tuple[FigureRow, ...]:
    """One measurement row per source row, in the current Fig/display order.

    Segment wrapping never duplicates a biological row. Missing compositions retain
    original row order; unmatched rows follow explicitly positioned rows of their Fig.
    """
    segments = project.composition.slices if isinstance(project, WBLayoutProject) else ()
    positions: dict[str, tuple[int, int]] = {}
    figures = {row.row_id: row.figure for row in project.rows}
    for segment in segments:
        if figures.get(segment.row_id) == segment.figure:
            position = (segment.line, segment.position)
            positions[segment.row_id] = min(positions.get(segment.row_id, position), position)
    original = {row.row_id: index for index, row in enumerate(project.rows)}
    return tuple(
        row
        for figure in project.figure_order
        for row in sorted(
            (row for row in project.rows if row.figure == figure),
            key=lambda row: (*positions.get(row.row_id, (513, 97)), original[row.row_id]),
        )
    )


def preserve_automatic_composition(
    project: WBLayoutProject, row_id: str, *, geometry_changed: bool = False
) -> FigureComposition:
    """Preserve layout; only a single whole-row segment may adapt to a changed N."""
    if not project.composition.slices:
        return initial_composition(project)
    row = next(row for row in project.rows if row.row_id == row_id)
    composition = project.composition.model_copy(
        update={
            "slices": tuple(
                s.model_copy(update={"display_frame": None})
                if s.row_id == row_id and geometry_changed
                else s
                for s in project.composition.slices
            )
        }
    )
    # Appending sources preserves the old composition until their automatic jobs run.
    # Add placeholders only for the current new row or still-unlocated pending rows.
    # A previously located row missing from the layout remains a validation error.
    slices = list(composition.slices)
    positioned = {segment.row_id for segment in slices}
    for pending in project.rows:
        if pending.row_id in positioned or (pending.row_id != row_id and pending.roi is not None):
            continue
        line = (
            max((segment.line for segment in slices if segment.figure == pending.figure), default=0)
            + 1
        )
        slices.append(
            FigureSlice(
                row_id=pending.row_id,
                figure=pending.figure,
                line=line,
                position=1,
                first_lane=1,
                last_lane=pending.lane_count,
            )
        )
    columns = list(composition.columns)
    known_figures = {column.figure for column in columns}
    for index, figure in enumerate(project.figure_order):
        if figure not in known_figures:
            columns.append(FigureColumn(figure=figure, column=index % project.template.columns + 1))
    composition = composition.model_copy(
        update={"slices": tuple(slices), "columns": tuple(columns)}
    )
    segments = [segment for segment in composition.slices if segment.row_id == row_id]
    if len(segments) == 1 and segments[0].first_lane == 1:
        composition = composition.model_copy(
            update={
                "slices": tuple(
                    s.model_copy(update={"last_lane": row.lane_count}) if s.row_id == row_id else s
                    for s in composition.slices
                )
            }
        )
    candidate = project.model_copy(update={"composition": composition})
    try:
        _groups(candidate, require_review=False, allow_unlocated=True)
    except ValueError as exc:
        raise ValueError(
            f"已有拼图分段与新泳道数不兼容，请先调整该行分段；未重置其它版式：{exc}"
        ) from exc
    return composition


def with_figure_layout(
    project: WBFigureProject,
    composition: FigureComposition,
    style: FigureLayoutStyle | None = None,
) -> WBLayoutProject:
    fields = {name: getattr(project, name) for name in type(project).model_fields}
    fields.update(
        schema_version=project.schema_version if isinstance(project, WBLayoutProject) else 7,
        composition=composition,
    )
    if style is not None:
        fields["layout_style"] = style
    cls = type(project) if isinstance(project, WBLayoutProject) else WBLayoutProject
    return cls.model_validate(fields)


@dataclass(frozen=True)
class SegmentPlacement:
    segment: FigureSlice
    row: FigureRow
    roi: LaneROI | None
    output_box: tuple[int, int, int, int]


@dataclass(frozen=True)
class LinePlacement:
    figure: str
    line: int
    label: str
    label_x: int
    label_y: float
    height: int
    segments: tuple[SegmentPlacement, ...]


@dataclass(frozen=True)
class LaboratoryLayout(FigureLayout):
    lines: tuple[LinePlacement, ...]


def _groups(
    project: WBLayoutProject, require_review: bool, *, allow_unlocated: bool = False
) -> dict[str, list[list[FigureSlice]]]:
    from wb_tool.application.automatic import row_is_ready

    if not project.rows:
        raise ValueError("项目还没有原图行")
    rows = {row.row_id: row for row in project.rows}
    used: dict[str, list[int]] = {key: [] for key in rows}
    groups: dict[str, dict[int, list[FigureSlice]]] = {}
    for segment in project.composition.slices:
        row = rows.get(segment.row_id)
        if row is None or row.figure != segment.figure:
            raise ValueError("版式原图行/Fig已改变，请重建或修正版式")
        if require_review and not row_is_ready(project, row):
            raise ValueError(f"{row.figure} / {row.protein} 尚未审核")
        if (
            row.source
            and (row.roi is not None or not allow_unlocated)
            and (row.roi is None or not 2 <= project.crop_height_for(row) <= 4096)
        ):
            raise ValueError(f"{row.protein} 需要2..4096像素高的原图ROI")
        frame = segment.display_frame
        if frame is not None:
            if segment.first_lane != 1 or segment.last_lane != row.lane_count:
                raise ValueError("旋转显示框仅允许完整原图行，不能用于分段泳道")
            roi = row.roi
            if row.source is None or roi is None:
                raise ValueError("旋转显示框需要实际原图ROI")
            source_frame = frame.sampling_policy == "within_source@2"
            if any(
                x < (0 if source_frame else max(0, roi.x0)) - 1e-7
                or x > (row.width if source_frame else min(row.width, roi.x1)) + 1e-7
                or y < (0 if source_frame else max(0, roi.y0)) - 1e-7
                or y > (row.height if source_frame else min(row.height, roi.y1)) + 1e-7
                for x, y in frame.corners()
            ):
                raise ValueError("旋转显示框超出其已声明采样边界")
        groups.setdefault(segment.figure, {}).setdefault(segment.line, []).append(segment)
    ordered: dict[str, list[list[FigureSlice]]] = {}
    for figure, lines in groups.items():
        ordered[figure] = []
        for number in sorted(lines):
            parts = sorted(lines[number], key=lambda s: s.position)
            if [s.position for s in parts] != list(range(1, len(parts) + 1)):
                raise ValueError(f"{figure} 第{number}显示行的段位置须从1连续且不重复")
            if len({rows[s.row_id].protein for s in parts}) != 1:
                raise ValueError(f"{figure} 第{number}显示行的蛋白名称不一致，请明确校正")
            for s in parts:
                used[s.row_id].extend(range(s.first_lane, s.last_lane + 1))
            ordered[figure].append(parts)
    if set(groups) != set(project.figure_order) or any(
        used[row.row_id] != list(range(1, row.lane_count + 1)) for row in project.rows
    ):
        raise ValueError("版式须保留每原图行全部1..N泳道一次及原顺序，不能遗漏/重复/重排")
    return ordered


def _roi(row: FigureRow, segment: FigureSlice) -> LaneROI | None:
    if row.roi is None:
        return None
    lanes = fixed_lane_grid(row.roi, row.lane_count)
    return LaneROI(
        row.row_id,
        lanes[segment.first_lane - 1].x0,
        row.roi.y0,
        lanes[segment.last_lane - 1].x1,
        row.roi.y1,
    )


def figure_uses_standard_display(project: WBLayoutProject, figure: str) -> bool:
    """Explicit frames affect their Fig, preserving other native figures."""
    return project.layout_style.display_policy == "standard_lane_ratio@1" or any(
        s.figure == figure and s.display_frame is not None for s in project.composition.slices
    )


def plan_laboratory_layout(
    project: WBLayoutProject,
    *,
    require_review: bool = True,
) -> LaboratoryLayout:
    groups = _groups(project, require_review)
    rows = {row.row_id: row for row in project.rows}
    template, style = project.template, project.layout_style
    dimensions: dict[str, tuple[list[int], list[int], int, int]] = {}
    for figure, lines in groups.items():
        standard = figure_uses_standard_display(project, figure)
        count = len(lines[0])
        if any(len(line) != count for line in lines):
            raise ValueError(f"{figure} 各显示行段数不同，请补齐明确缺图位")
        widths: list[int] = []
        for column in range(count):
            parts = [line[column] for line in lines]
            spans = {s.last_lane - s.first_lane + 1 for s in parts}
            crops = [_roi(rows[s.row_id], s) for s in parts]
            actual = {roi.width for roi in crops if roi}
            if len(spans) != 1 or (not standard and len(actual) != 1):
                raise ValueError(f"{figure} 第{column + 1}段须有原图且各行宽度/N一致；不会拉伸")
            widths.append(next(iter(spans)) * style.lane_unit if standard else next(iter(actual)))
        heights = [
            style.lane_unit * 4 // 5
            if standard
            else max(project.crop_height_for(rows[s.row_id]) for s in line)
            for line in lines
        ]
        width = template.label_width + sum(w + 2 * template.border for w in widths)
        width += (count - 1) * style.segment_gap
        height = style.heading_size + template.row_gap
        height += sum(h + 2 * template.border + template.row_gap for h in heights)
        dimensions[figure] = (widths, heights, width, height)
    columns = {entry.figure: entry.column for entry in project.composition.columns}
    if len(columns) != len(project.composition.columns) or set(columns) != set(groups):
        raise ValueError("Fig列配置须完整且不重复")
    if any(column > template.columns for column in columns.values()):
        raise ValueError("Fig列号超过模板列数，请调整列号或增加列数")
    positions: dict[str, tuple[int, int]] = {}
    if style.flow == "columns":
        column_widths: dict[int, int] = {}
        for figure, column in columns.items():
            column_widths[column] = max(column_widths.get(column, 0), dimensions[figure][2])
        if set(column_widths) != set(range(1, max(column_widths) + 1)):
            raise ValueError("Fig列号须从1连续，不能隐含空列")
        xs: dict[int, int] = {}
        x = template.margin
        for column in sorted(column_widths):
            xs[column] = x
            x += column_widths[column] + template.figure_gap
        ys = dict.fromkeys(column_widths, template.margin)
        for figure in project.figure_order:
            column = columns[figure]
            positions[figure] = (xs[column], ys[column])
            ys[column] += dimensions[figure][3] + template.figure_gap
    else:
        x = y = bottom = template.margin
        for index, figure in enumerate(project.figure_order):
            if index and index % template.columns == 0:
                x, y = template.margin, bottom + template.figure_gap
            positions[figure] = x, y
            x += dimensions[figure][2] + template.figure_gap
            bottom = max(bottom, y + dimensions[figure][3])
    width = max(positions[f][0] + dimensions[f][2] for f in groups) + template.margin
    height = max(positions[f][1] + dimensions[f][3] for f in groups) + template.margin
    if width * height > 32_000_000 or max(width, height) > 32768:
        raise ValueError("拼图超出3200万像素/32768边长预算，请拆分项目")
    panels: list[FigurePlacement] = []
    result: list[LinePlacement] = []
    for figure in project.figure_order:
        standard = figure_uses_standard_display(project, figure)
        widths, heights, panel_width, _ = dimensions[figure]
        x, y = positions[figure]
        panels.append(
            FigurePlacement(
                figure,
                x,
                y,
                panel_width,
                tuple(rows[s.row_id] for line in groups[figure] for s in line),
            )
        )
        y += style.heading_size + template.row_gap
        for parts, line_height in zip(groups[figure], heights, strict=True):
            segment_x = x + (template.label_width if template.label_side == "left" else 0)
            label_start = (
                x if template.label_side == "left" else x + panel_width - template.label_width
            )
            label_x = label_start + (
                template.label_width - 12 if style.label_alignment == "right" else 8
            )
            placed: list[SegmentPlacement] = []
            for segment, segment_width in zip(parts, widths, strict=True):
                row = rows[segment.row_id]
                h = line_height if standard else project.crop_height_for(row)
                x0, y0 = segment_x + template.border, y + template.border + (line_height - h) // 2
                placed.append(
                    SegmentPlacement(
                        segment, row, _roi(row, segment), (x0, y0, x0 + segment_width, y0 + h)
                    )
                )
                segment_x += segment_width + 2 * template.border + style.segment_gap
            result.append(
                LinePlacement(
                    figure,
                    parts[0].line,
                    rows[parts[0].row_id].protein,
                    label_x,
                    y + template.border + line_height / 2,
                    line_height,
                    tuple(placed),
                )
            )
            y += line_height + 2 * template.border + template.row_gap
    return LaboratoryLayout(width, height, tuple(panels), tuple(result))
