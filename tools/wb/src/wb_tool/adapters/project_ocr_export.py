"""Literal OCR-labelled project values, including both recognition and measurement lineage."""

from collections.abc import Callable
from pathlib import Path

from wb_tool.adapters.csv_export import csv_bytes
from wb_tool.adapters.worksheet_export import Cell, publish_xlsx, two_sheet_xlsx_bytes
from wb_tool.application.project_analysis import LoadedProjectResult
from wb_tool.application.project_ocr import LoadedProjectOCR, WBProjectOCR, fill_project_ocr_table


def project_ocr_table_rows(
    project: WBProjectOCR,
    results: tuple[LoadedProjectResult, ...],
    loaded: LoadedProjectOCR | None,
) -> tuple[tuple[tuple[Cell, ...], ...], tuple[tuple[Cell, ...], ...]]:
    if project.ocr is None:
        raise ValueError("请先导入独立拼图")
    cells = fill_project_ocr_table(project, results, loaded)
    positions = {(c.row_id, c.lane_index): c.value for c in cells}
    count = max((r.link.lane_count if r.link else 1 for r in project.ocr.rows), default=1)
    rows: list[tuple[Cell, ...]] = [("Fig", "蛋白", *(f"泳道 {n}" for n in range(1, count + 1)))]
    rows.extend(
        (r.figure, r.protein, *(positions.get((r.row_id, n)) for n in range(1, count + 1)))
        for r in project.ocr.rows
    )
    links = {r.row_id: r.link for r in project.ocr.rows}
    audit: list[tuple[Cell, ...]] = [
        ("项目 ID", project.project_id),
        ("项目修订", project.revision),
        ("OCR源 SHA256", project.ocr.source.sha256),
        ("OCR运行 ID", project.ocr.run.run_id if project.ocr.run else ""),
        ("OCR引擎", project.ocr.recognition.engine_id if project.ocr.recognition else ""),
        ("算法 / 单位", "profile_integral@1 / intensity*pixel"),
        (
            "OCR行 ID",
            "Fig",
            "蛋白",
            "目标项目行 ID",
            "泳道序号",
            "原图 SHA256",
            "泳道 ID",
            "条带 ID",
            "定量修订",
            "定量运行 ID",
            "积分",
            "状态",
            "原因",
        ),
    ]
    for c in cells:
        link = links[c.row_id]
        audit.append(
            (
                c.row_id,
                c.figure,
                c.protein,
                link.target_row_id if link else "",
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
        )
    return tuple(rows), tuple(audit)


def project_ocr_csv_bytes(
    project: WBProjectOCR, results: tuple[LoadedProjectResult, ...], loaded: LoadedProjectOCR | None
) -> bytes:
    _, audit = project_ocr_table_rows(project, results, loaded)
    return csv_bytes(
        (tuple(row[0] for row in audit[:6]) + audit[6],)
        + tuple(tuple(row[1] for row in audit[:6]) + item for item in audit[7:])
    )


def export_project_ocr_table(
    project: WBProjectOCR,
    results: tuple[LoadedProjectResult, ...],
    loaded: LoadedProjectOCR | None,
    destination: str | Path,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> Path:
    if Path(destination).suffix.lower() == ".csv":
        from wb_tool.adapters.worksheet_export import publish_table_bytes

        return publish_table_bytes(
            project_ocr_csv_bytes(project, results, loaded),
            destination,
            ".csv",
            cancelled=cancelled,
        )
    return publish_xlsx(
        two_sheet_xlsx_bytes(*project_ocr_table_rows(project, results, loaded)),
        destination,
        cancelled=cancelled,
    )
