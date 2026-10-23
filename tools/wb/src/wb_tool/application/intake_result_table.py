"""Visible result-table projection; committed raw Signal is independent of review."""

from dataclasses import dataclass

from wb_tool.application.instrument_intake import WBIntakeProject
from wb_tool.application.project_analysis import ProjectTableCell


@dataclass(frozen=True)
class IntakeVisibleTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[str | float | None, ...], ...]
    quality: tuple[tuple[int, int], ...]


def intake_visible_table(
    project: WBIntakeProject, cells: tuple[ProjectTableCell, ...], *, figure_id: str = ""
) -> IntakeVisibleTable:
    if figure_id and not any(f.figure_id == figure_id for f in project.intake.figures):
        raise ValueError("结果表Fig身份不存在")
    count = max(
        (f.lane_count for f in project.intake.figures if not figure_id or f.figure_id == figure_id),
        default=0,
    )
    figures = {f.figure_id: f for f in project.intake.figures}
    by_position = {(c.row_id, c.lane_index): c for c in cells}
    counts: dict[str, tuple[int, int]] = {}
    for cell in cells:
        present, warnings = counts.get(cell.row_id, (0, 0))
        counts[cell.row_id] = present + 1, warnings + (cell.status != "valid")
    rows: list[tuple[str | float | None, ...]] = []
    quality: list[tuple[int, int]] = []
    proteins = tuple(
        p for p in project.intake.proteins if not figure_id or p.figure_id == figure_id
    )
    for ri, protein in enumerate(proteins):
        figure = figures[protein.figure_id]
        present, warnings = counts.get(protein.protein_id, (0, 0))
        status = (
            "已完成"
            if present == figure.lane_count and not warnings
            else f"{warnings} 项需查看"
            if warnings
            else "待计算"
        )
        numbers: list[float | None] = []
        for lane in range(1, count + 1):
            cell = by_position.get((protein.protein_id, lane))
            number = cell.raw_integral if cell else None
            numbers.append(number)
            if number is not None and cell and cell.status != "valid":
                quality.append((ri, lane + 1))
        rows.append((figure.label, protein.label, *numbers, status))
    return IntakeVisibleTable(
        ("Fig", "蛋白", *(f"泳道 {n}" for n in range(1, count + 1)), "状态"),
        tuple(rows),
        tuple(quality),
    )
