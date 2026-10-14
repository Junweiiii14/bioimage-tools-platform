"""Write quantitative results into explicit worksheet cells; missing/failure stays missing."""

import math
from dataclasses import dataclass

from wb_tool.application.analysis import AnalysisResult
from wb_tool.domain.worksheet import (
    MeasurementBinding,
    OCRRecognition,
    Worksheet,
    WorksheetColumn,
    WorksheetRow,
    suggest_figures,
)


@dataclass(frozen=True)
class WorksheetCell:
    row_id: str
    column_id: str
    value: float | None
    status: str
    reason: str = ""


def fill_worksheet(worksheet: Worksheet, result: AnalysisResult) -> tuple[WorksheetCell, ...]:
    if worksheet.source_sha256 != result.request.source_sha256:
        raise ValueError("工作表不能写入其他来源的测量")
    measurements = {
        (lane.roi.lane_id, band.annotation.band_id): band
        for lane in result.lanes
        for band in lane.bands
    }
    bindings = {(binding.row_id, binding.column_id): binding for binding in worksheet.bindings}
    cells: list[WorksheetCell] = []
    for row in worksheet.rows:
        for column in worksheet.columns:
            binding = bindings.get((row.row_id, column.column_id))
            if not row.confirmed:
                cell = WorksheetCell(
                    row.row_id, column.column_id, None, "unconfirmed", "Fig/行名尚未确认"
                )
            elif binding is None:
                cell = WorksheetCell(
                    row.row_id, column.column_id, None, "unbound", "未关联泳道/条带"
                )
            else:
                band = measurements.get((binding.lane_id, binding.band_id))
                if band is None:
                    cell = WorksheetCell(
                        row.row_id, column.column_id, None, "missing_measurement", "对应测量不存在"
                    )
                else:
                    cell = WorksheetCell(
                        row.row_id, column.column_id, band.signal, band.status, band.reason or ""
                    )
            cells.append(cell)
    return tuple(cells)


def propose_worksheet(recognition: OCRRecognition, result: AnalysisResult) -> Worksheet:
    """Suggest spatial links; names and links remain unconfirmed until review."""
    if recognition.source_sha256 != result.request.source_sha256:
        raise ValueError("OCR 图与测量图来源不一致，需要显式跨图映射")
    figures = suggest_figures(recognition)
    rows: list[WorksheetRow] = []
    bindings: list[MeasurementBinding] = []
    maximum_columns = 0
    for figure in figures:
        rows.extend(
            WorksheetRow(token.token_id, figure.figure_id, figure.heading.text, token.text, False)
            for token in figure.rows
        )
        lanes = sorted(
            (
                lane
                for lane in result.lanes
                if figure.bounds.x0 <= (lane.roi.x0 + lane.roi.x1) / 2 < figure.bounds.x1
                and figure.bounds.y0 <= (lane.roi.y0 + lane.roi.y1) / 2 < figure.bounds.y1
            ),
            key=lambda lane: (lane.roi.x0, lane.roi.lane_id),
        )
        maximum_columns = max(maximum_columns, len(lanes))
        for column_index, lane in enumerate(lanes):
            candidates: dict[str, list[str]] = {}
            for band in lane.bands:
                bounds = band.annotation.bounds
                if bounds is None or not figure.rows:
                    continue
                center = lane.roi.y0 + (bounds.left + bounds.right) / 2
                distances = sorted(
                    (abs(center - (token.bounds.y0 + token.bounds.y1) / 2), token.token_id, token)
                    for token in figure.rows
                )
                distance, row_id, token = distances[0]
                if len(distances) > 1 and math.isclose(distance, distances[1][0], abs_tol=1.0):
                    continue
                if distance <= max(
                    (token.bounds.y1 - token.bounds.y0) * 1.5,
                    (figure.bounds.y1 - figure.bounds.y0) * 0.04,
                ):
                    candidates.setdefault(row_id, []).append(band.annotation.band_id)
            for row_id, band_ids in candidates.items():
                if len(band_ids) == 1:
                    bindings.append(
                        MeasurementBinding(
                            figure.figure_id,
                            row_id,
                            f"C{column_index + 1}",
                            lane.roi.lane_id,
                            band_ids[0],
                        )
                    )
    columns = tuple(
        WorksheetColumn(f"C{index + 1}", f"泳道 {index + 1}") for index in range(maximum_columns)
    )
    return Worksheet(
        recognition.source_sha256,
        tuple(rows),
        columns,
        tuple(bindings),
        layout_id="fig_heading_tracks_nearest_row@1",
    )
