"""Project values and explicit provenance, using the existing literal OOXML writer."""

from pathlib import Path

from wb_tool.adapters.worksheet_export import Cell, publish_xlsx, two_sheet_xlsx_bytes
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_analysis import LoadedProjectResult, fill_project_table


def project_xlsx_bytes(project: WBFigureProject, results: tuple[LoadedProjectResult, ...]) -> bytes:
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
    return two_sheet_xlsx_bytes(tuple(rows), tuple(audit))


def export_project_table(
    project: WBFigureProject, results: tuple[LoadedProjectResult, ...], destination: str | Path
) -> Path:
    return publish_xlsx(project_xlsx_bytes(project, results), destination)
