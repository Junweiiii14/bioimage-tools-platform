"""Literal, provenance-bearing ratios and relative values, with no replacement of prior exports."""

from collections.abc import Callable
from pathlib import Path

from wb_tool.adapters.csv_export import csv_bytes
from wb_tool.adapters.worksheet_export import Cell, publish_xlsx, two_sheet_xlsx_bytes
from wb_tool.application.project_analysis import LoadedProjectResult
from wb_tool.application.project_normalization import (
    WBNormalizedProject,
    fill_project_normalization,
)
from wb_tool.application.project_ocr import LoadedProjectOCR
from wb_tool.application.project_restore import WBRestoredProject, run_origin


def normalization_table_rows(
    project: WBNormalizedProject,
    results: tuple[LoadedProjectResult, ...],
    loaded: LoadedProjectOCR | None,
    *,
    ocr_labels: bool = False,
) -> tuple[tuple[tuple[Cell, ...], ...], tuple[tuple[Cell, ...], ...]]:
    if ocr_labels and project.ocr is None:
        raise ValueError("项目没有OCR行名")
    snapshot = fill_project_normalization(project, results, loaded)
    cells = snapshot.ocr_cells if ocr_labels else snapshot.cells
    rows: list[tuple[Cell, ...]] = [
        (
            "Fig",
            "蛋白",
            "样本",
            "目标泳道",
            "参照泳道",
            "对照",
            "目标积分",
            "参照积分",
            "目标/参照",
            "对照均值",
            "相对值",
            "比值状态",
            "比值原因",
            "相对值状态",
            "相对值原因",
        )
    ]
    audit: list[tuple[Cell, ...]] = [
        ("项目", project.project_id, "修订", project.revision),
        ("算法", "lane_reference_ratio@1", "比值/相对值为无量纲"),
        ("标签来源", "已配置的OCR关联行" if ocr_labels else "项目原图行"),
        ("OCR源", project.ocr.source.sha256 if ocr_labels and project.ocr else ""),
        (
            "OCR运行",
            project.ocr.run.run_id if ocr_labels and project.ocr and project.ocr.run else "",
        ),
        (
            "目标行",
            "参照行",
            "样本",
            "目标泳道",
            "参照泳道",
            "参照类型",
            "对照方式",
            "对照样本",
            "OCR行",
            "目标原图SHA",
            "目标运行",
            "目标修订",
            "目标lane",
            "目标band",
            "参照原图SHA",
            "参照运行",
            "参照修订",
            "参照lane",
            "参照band",
            "配置已确认",
            "目标裁剪x0,y0,x1,y1",
            "参照裁剪x0,y0,x1,y1",
            "备注",
        ),
    ]
    plans = {p.target.row_id: p for p in project.normalizations}
    for c in cells:
        rows.append(
            (
                c.figure,
                c.protein,
                c.sample,
                c.target_lane,
                c.reference_lane,
                "是" if c.control else "否",
                c.target.value if c.target else None,
                c.reference.value if c.reference else None,
                c.ratio,
                c.control_mean,
                c.relative,
                c.ratio_status,
                c.ratio_reason,
                c.relative_status,
                c.relative_reason,
            )
        )
        plan = plans[c.target_row_id]
        target, reference = c.target, c.reference
        audit.append(
            (
                c.target_row_id,
                c.reference_row_id,
                c.sample,
                c.target_lane,
                c.reference_lane,
                c.kind,
                c.control_mode,
                ", ".join(c.control_samples),
                c.ocr_row_id,
                target.source_sha256 if target else plan.target.source_sha256,
                target.run_id if target else "",
                target.request_revision if target else None,
                target.lane_id if target else "",
                target.band_id if target else "",
                reference.source_sha256 if reference else plan.reference.source_sha256,
                reference.run_id if reference else "",
                reference.request_revision if reference else None,
                reference.lane_id if reference else "",
                reference.band_id if reference else "",
                "是" if plan.confirmed else "否",
                ",".join(
                    str(v)
                    for v in (
                        plan.target.crop.x0,
                        plan.target.crop.y0,
                        plan.target.crop.x1,
                        plan.target.crop.y1,
                    )
                ),
                ",".join(
                    str(v)
                    for v in (
                        plan.reference.crop.x0,
                        plan.reference.crop.y0,
                        plan.reference.crop.x1,
                        plan.reference.crop.y1,
                    )
                ),
                plan.notes,
            )
        )
    if isinstance(project, WBRestoredProject):
        audit[5] += (
            "目标运行来源",
            "目标归档SHA256",
            "参照运行来源",
            "参照归档SHA256",
            "OCR运行来源",
            "OCR归档SHA256",
        )
        for index, cell in enumerate(cells, 6):
            audit[index] += (
                *run_origin(project, cell.target.run_id if cell.target else ""),
                *run_origin(project, cell.reference.run_id if cell.reference else ""),
                *run_origin(
                    project,
                    project.ocr.run.run_id
                    if ocr_labels and project.ocr and project.ocr.run
                    else "",
                ),
            )
    return tuple(rows), tuple(audit)


def normalization_csv_bytes(
    project: WBNormalizedProject,
    results: tuple[LoadedProjectResult, ...],
    loaded: LoadedProjectOCR | None,
    *,
    ocr_labels: bool = False,
) -> bytes:
    rows, audit = normalization_table_rows(project, results, loaded, ocr_labels=ocr_labels)
    prefix: tuple[Cell, ...] = (
        project.project_id,
        project.revision,
        "lane_reference_ratio@1",
        audit[2][1],
        audit[3][1],
        audit[4][1],
    )
    return csv_bytes(
        (
            (
                "项目 ID",
                "项目修订",
                "算法",
                "标签来源",
                "OCR源",
                "OCR运行",
                *rows[0],
                *("来源_" + str(value) for value in audit[5]),
            ),
        )
        + tuple(prefix + row + lineage for row, lineage in zip(rows[1:], audit[6:], strict=True))
    )


def export_project_normalization(
    project: WBNormalizedProject,
    results: tuple[LoadedProjectResult, ...],
    loaded: LoadedProjectOCR | None,
    destination: str | Path,
    *,
    ocr_labels: bool = False,
    cancelled: Callable[[], bool] = lambda: False,
) -> Path:
    if Path(destination).suffix.lower() == ".csv":
        from wb_tool.adapters.worksheet_export import publish_table_bytes

        return publish_table_bytes(
            normalization_csv_bytes(project, results, loaded, ocr_labels=ocr_labels),
            destination,
            ".csv",
            cancelled=cancelled,
        )
    return publish_xlsx(
        two_sheet_xlsx_bytes(
            *normalization_table_rows(project, results, loaded, ocr_labels=ocr_labels)
        ),
        destination,
        cancelled=cancelled,
    )
