"""Explicit metadata proposals; matching and atomic edits never infer experimental identity."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Literal

from wb_tool.application.figure_project import FigureRow, WBFigureProject

MetadataKey = Literal["row_id", "sha256", "filename"]
METADATA_FIELDS = (
    "project_name",
    "figure",
    "protein",
    "lane_count",
    "empty_lanes",
    "order",
    "notes",
)
METADATA_LABELS = ("实验项目", "Fig", "蛋白", "N", "空泳道", "排列顺序", "备注")


@dataclass(frozen=True)
class MetadataCell:
    text: str = ""
    error: str = ""


@dataclass(frozen=True)
class MetadataSheet:
    name: str
    rows: tuple[tuple[MetadataCell, ...], ...]


@dataclass(frozen=True)
class MetadataBook:
    sha256: str
    sheets: tuple[MetadataSheet, ...]


@dataclass(frozen=True)
class MetadataEntry:
    line: int
    key: str
    candidates: tuple[str, ...]
    target_id: str
    values: tuple[tuple[str, MetadataCell], ...]
    issue: str = ""


@dataclass(frozen=True)
class MetadataPreview:
    project_digest: str
    source: str
    entries: tuple[MetadataEntry, ...]


def metadata_digest(project: WBFigureProject) -> str:
    return sha256(project.model_dump_json().encode("utf-8")).hexdigest()


def preview_metadata(
    project: WBFigureProject,
    sheet: MetadataSheet,
    header_row: int,
    key_kind: MetadataKey,
    key_column: int,
    columns: tuple[tuple[str, int], ...],
    *,
    source: str = "",
) -> MetadataPreview:
    """Indices are zero based. Exact, case-sensitive keys; ambiguous matches stay unbound."""
    if key_kind not in ("row_id", "sha256", "filename"):
        raise ValueError("请选择行 ID、完整 SHA256 或完整文件名作为匹配键")
    if not 0 <= header_row < len(sheet.rows) or len(sheet.rows) > 1025:
        raise ValueError("表头行不存在或超过 1024 条记录")
    width = len(sheet.rows[header_row])
    fields = tuple(field for field, _ in columns)
    indices = (key_column, *(index for _, index in columns))
    if (
        not columns
        or len(set(fields)) != len(fields)
        or any(field not in METADATA_FIELDS for field in fields)
        or len(set(indices)) != len(indices)
        or any(not 0 <= index < width for index in indices)
    ):
        raise ValueError("请选择互不重复的匹配列与元信息列")
    if any(sheet.rows[header_row][index].error for index in indices):
        raise ValueError("所选表头含公式、合并或无效单元格")
    lookup: dict[str, list[str]] = {}
    for row in project.rows:
        key = (
            row.row_id
            if key_kind == "row_id"
            else (row.source.sha256 if row.source else "")
            if key_kind == "sha256"
            else row.filename
        )
        if key:
            lookup.setdefault(key, []).append(row.row_id)
    entries: list[MetadataEntry] = []
    seen: dict[str, int] = {}
    for line, cells in enumerate(sheet.rows[header_row + 1 :], header_row + 2):

        def cell(index: int, cells: tuple[MetadataCell, ...] = cells) -> MetadataCell:
            return cells[index] if index < len(cells) else MetadataCell()

        values = tuple((field, cell(index)) for field, index in columns)
        key_cell = cell(key_column)
        if (
            not key_cell.text
            and not key_cell.error
            and not any(c.text or c.error for _, c in values)
        ):
            continue
        key = key_cell.text.strip()
        candidates = tuple(lookup.get(key, ())) if not key_cell.error else ()
        issue = key_cell.error or ("匹配键为空" if not key else "")
        if not issue:
            issue = (
                "未匹配原图行"
                if not candidates
                else "匹配到多行，请明确选择"
                if len(candidates) > 1
                else ""
            )
        seen[key] = seen.get(key, 0) + 1
        entries.append(
            MetadataEntry(
                line, key, candidates, candidates[0] if len(candidates) == 1 else "", values, issue
            )
        )
    entries = [
        MetadataEntry(
            e.line,
            e.key,
            e.candidates,
            "" if seen[e.key] > 1 else e.target_id,
            e.values,
            "输入键重复，请逐条选择并检查目标" if seen[e.key] > 1 else e.issue,
        )
        for e in entries
    ]
    return MetadataPreview(metadata_digest(project), source or sheet.name, tuple(entries))


def filename_metadata(
    project: WBFigureProject,
    row_ids: tuple[str, ...],
    separator: str,
    fields: tuple[str, ...],
) -> MetadataPreview:
    """Split the complete stem using a literal separator; empty field positions are ignored."""
    if not separator or len(separator) > 8 or not fields or len(fields) > 20:
        raise ValueError("请指定 1–8 字符分隔符和 1–20 个字段位置")
    active = tuple(f for f in fields if f)
    if (
        not active
        or len(set(active)) != len(active)
        or any(f not in METADATA_FIELDS for f in active)
    ):
        raise ValueError("文件名字段须有效且不重复；忽略位置留空")
    if (
        not row_ids
        or len(set(row_ids)) != len(row_ids)
        or not set(row_ids) <= {r.row_id for r in project.rows}
    ):
        raise ValueError("请先选择当前项目中的原图行")
    entries: list[MetadataEntry] = []
    for row in project.rows:
        if row.row_id not in row_ids:
            continue
        parts = row.filename.rsplit(".", 1)[0].split(separator)
        issue = "文件名分段数与规则不符，请手动填写" if len(parts) != len(fields) else ""
        values = tuple(
            (field, MetadataCell(parts[i] if not issue else ""))
            for i, field in enumerate(fields)
            if field
        )
        entries.append(
            MetadataEntry(len(entries) + 1, row.filename, (row.row_id,), row.row_id, values, issue)
        )
    return MetadataPreview(metadata_digest(project), "文件名分段提取", tuple(entries))


def metadata_integer(text: str, maximum: int) -> int:
    try:
        value = Decimal(text)
        if not value.is_finite() or value != value.to_integral_value() or not 1 <= value <= maximum:
            raise ValueError(f"整数必须位于 1..{maximum}")
        return int(value)
    except InvalidOperation as error:
        raise ValueError(f"需要 1..{maximum} 的整数") from error


def apply_metadata(
    project: WBFigureProject,
    preview: MetadataPreview,
    selected: tuple[MetadataEntry, ...],
    fields: tuple[str, ...],
) -> WBFigureProject:
    """Apply the explicitly selected, possibly corrected preview atomically to the frozen draft."""
    return type(project).model_validate(metadata_proposal(project, preview, selected, fields))


def metadata_proposal(
    project: WBFigureProject,
    preview: MetadataPreview,
    selected: tuple[MetadataEntry, ...],
    fields: tuple[str, ...],
) -> dict[str, object]:
    """Compute validated row values; the caller owns schema-specific identity reconciliation."""
    if metadata_digest(project) != preview.project_digest:
        raise ValueError("项目已修改，请重新生成元信息预览")
    if (
        not selected
        or len(selected) > 512
        or not fields
        or len(set(fields)) != len(fields)
        or any(f not in METADATA_FIELDS for f in fields)
    ):
        raise ValueError("请选择要应用的行和字段（最多 512 行）")
    identities = {r.row_id: r for r in project.rows}
    targets = tuple(e.target_id for e in selected)
    if len(set(targets)) != len(targets) or any(t not in identities for t in targets):
        raise ValueError("所选记录必须明确关联不同的项目行")
    changed: dict[str, FigureRow] = {}
    orders: dict[str, int] = {}
    names: set[str] = set()
    for entry in selected:
        row = identities[entry.target_id]
        data = dict(row)
        if len(dict(entry.values)) != len(entry.values):
            raise ValueError("元信息字段重复")
        for field, cell in entry.values:
            if field not in fields:
                continue
            if cell.error:
                raise ValueError(f"第 {entry.line} 行 {field}：{cell.error}，请填写明确值")
            value = cell.text.strip()
            if len(value) > 2000:
                raise ValueError("元信息单元格超过 2000 字符")
            if not value:
                continue  # Empty cells never erase a value or become numeric zero.
            if field == "project_name":
                names.add(value)
            elif field == "order":
                orders[row.row_id] = metadata_integer(value, 512)
            elif field == "lane_count":
                data[field] = metadata_integer(value, 96)
            elif field == "empty_lanes":
                data[field] = (
                    ()
                    if value in ("无", "-", "[]")
                    else tuple(
                        metadata_integer(v.strip(), 96) for v in value.replace("，", ",").split(",")
                    )
                )
            elif field == "notes":
                data[field] = "" if value == "[]" else value
            else:
                data[field] = value
        if data["lane_count"] != row.lane_count or data["empty_lanes"] != row.empty_lanes:
            data["reviewed"] = False
        changed[row.row_id] = FigureRow.model_validate(data)
    if len(names) > 1:
        raise ValueError("一个项目只能有一个实验项目名称，请拆分或修正")
    rows = [changed.get(row.row_id, row) for row in project.rows]
    if "order" in fields:
        if set(orders) != set(targets) or len(set(orders.values())) != len(orders):
            raise ValueError("排序须为每条所选行提供互不重复的 1..512 整数")
        ordered = iter(sorted(changed.values(), key=lambda row: orders[row.row_id]))
        rows = [next(ordered) if row.row_id in changed else row for row in rows]
    groups = tuple(dict.fromkeys(row.figure for row in rows))
    order = tuple(f for f in project.figure_order if f in groups)
    order += tuple(f for f in groups if f not in order)
    data = dict(project)
    data.update(
        rows=tuple(rows), figure_order=order, name=next(iter(names)) if names else project.name
    )
    return data
