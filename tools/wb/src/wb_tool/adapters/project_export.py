"""Project values and explicit provenance, using the existing literal OOXML writer."""

from collections.abc import Callable
from pathlib import Path

from wb_tool.adapters.csv_export import csv_bytes
from wb_tool.adapters.worksheet_export import Cell, publish_xlsx, two_sheet_xlsx_bytes
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_analysis import LoadedProjectResult, fill_project_table
from wb_tool.application.project_restore import WBRestoredProject


def project_table_rows(
    project: WBFigureProject, results: tuple[LoadedProjectResult, ...]
) -> tuple[tuple[tuple[Cell, ...], ...], tuple[tuple[Cell, ...], ...]]:
    cells = fill_project_table(project, results)
    by_position = {(c.row_id, c.lane_index): c for c in cells}
    count = max((r.lane_count for r in project.rows), default=0)
    rows: list[tuple[Cell, ...]] = [("Fig", "蛋白", *(f"泳道 {n}" for n in range(1, count + 1)))]
    for figure in project.figure_order:
        for row in (r for r in project.rows if r.figure == figure):
            rows.append(
                (
                    row.figure,
                    row.protein,
                    *(
                        by_position[(row.row_id, n)].value if n <= row.lane_count else None
                        for n in range(1, count + 1)
                    ),
                )
            )
    audit: list[tuple[Cell, ...]] = [
        ("项目 ID", project.project_id),
        ("项目修订", project.revision),
        ("算法", "profile_integral@1"),
        ("单位", "intensity*pixel"),
        (
            "行 ID",
            "Fig",
            "蛋白",
            "泳道序号",
            "原图 SHA256",
            "泳道 ID",
            "条带 ID",
            "请求修订",
            "运行 ID",
            "积分",
            "状态",
            "原因",
        ),
    ]
    audit.extend(
        (
            c.row_id,
            c.figure,
            c.protein,
            c.lane_index,
            c.source_sha256,
            c.lane_id,
            c.band_id,
            c.request_revision,
            c.run_id,
            c.value,
            c.status,
            c.reason,
        )
        for c in cells
    )
    if isinstance(project, WBRestoredProject):
        audit[4] += ("运行来源", "来源归档SHA256")
        for index, cell in enumerate(cells, 5):
            audit[index] += (cell.evidence_origin, cell.archive_sha256)
    return tuple(rows), tuple(audit)


def project_xlsx_bytes(project: WBFigureProject, results: tuple[LoadedProjectResult, ...]) -> bytes:
    return two_sheet_xlsx_bytes(*project_table_rows(project, results))


def project_csv_bytes(project: WBFigureProject, results: tuple[LoadedProjectResult, ...]) -> bytes:
    _, audit = project_table_rows(project, results)
    return csv_bytes(
        (("项目 ID", "项目修订", "算法", "单位", *audit[4]),)
        + tuple(
            (project.project_id, project.revision, "profile_integral@1", "intensity*pixel", *row)
            for row in audit[5:]
        )
    )


def export_project_table(
    project: WBFigureProject,
    results: tuple[LoadedProjectResult, ...],
    destination: str | Path,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> Path:
    if Path(destination).suffix.lower() == ".csv":
        from wb_tool.adapters.worksheet_export import publish_table_bytes

        return publish_table_bytes(
            project_csv_bytes(project, results), destination, ".csv", cancelled=cancelled
        )
    return publish_xlsx(project_xlsx_bytes(project, results), destination, cancelled=cancelled)
