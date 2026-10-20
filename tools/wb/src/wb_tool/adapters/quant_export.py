"""WBQuant-style Signal tables; audit evidence remains a separate sheet/file."""

import csv
from collections.abc import Callable
from io import BytesIO, StringIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from wb_tool.adapters.project_export import project_table_rows
from wb_tool.adapters.worksheet_export import NS, Cell, publish_table_bytes, two_sheet_xlsx_bytes
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.laboratory_layout import ordered_quant_rows
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    WBAnalysisProject,
    fill_project_table,
)


def _current_results(
    project: WBFigureProject, results: tuple[LoadedProjectResult, ...]
) -> tuple[LoadedProjectResult, ...]:
    cells = fill_project_table(project, results)
    ready = {
        c.row_id
        for c in cells
        if c.status in ("valid", "quality_review", "excluded", "not_detected", "invalid")
    }
    plans = (
        {p.row_id: p for p in project.analyses} if isinstance(project, WBAnalysisProject) else {}
    )
    return tuple(
        r
        for r in results
        if r.row_id in ready
        and (p := plans.get(r.row_id))
        and p.run
        and p.run.result
        and r.run_id == p.run.run_id
        and r.asset_sha256 == p.run.result.sha256
        and r.result.request == p.request
    )


def wbquant_table_rows(
    project: WBFigureProject, results: tuple[LoadedProjectResult, ...]
) -> tuple[tuple[Cell, ...], ...]:
    """All included Signals, sorted top-to-bottom within each lane (including warnings).

    A warning is not promoted to valid status: the main table is a raw Signal view,
    just like WBQuant; detailed statuses and provenance remain in the audit sheet.
    Failed/stale/unverified runs never supply numbers.
    """
    available = {r.row_id: r.result for r in _current_results(project, results)}
    count = max((r.lane_count for r in project.rows), default=0)
    rows: list[tuple[Cell, ...]] = [
        ("组序", "组名", "条带", *(f"泳道 {n}" for n in range(1, count + 1)))
    ]
    for group_index, figure in enumerate(project.figure_order, 1):
        for row in (r for r in ordered_quant_rows(project) if r.figure == figure):
            result = available.get(row.row_id)
            signals: list[list[float | None]] = []
            if result:
                for lane in result.lanes:
                    # Detection persists original peak order, including invalid empty slots.
                    # Sorting bounds would move an invalid (None) peak ahead of earlier peaks.
                    bands = [b for b in lane.bands if b.annotation.included]
                    if any("manually_added@1" in b.annotation.detection_notes for b in bands):
                        bands.sort(
                            key=lambda b: (
                                b.annotation.bounds.left if b.annotation.bounds else 100000
                            )
                        )
                    signals.append([b.measurement.signal if b.measurement else None for b in bands])
            height = max((len(v) for v in signals), default=1)
            for number in range(max(1, height)):
                label = row.protein if height == 1 else f"{row.protein} · {number + 1}"
                rows.append(
                    (
                        f"第 {group_index} 组",
                        figure,
                        label,
                        *(
                            signals[i][number]
                            if i < len(signals) and number < len(signals[i])
                            else None
                            for i in range(count)
                        ),
                    )
                )
    return tuple(rows)


def wbquant_csv_bytes(project: WBFigureProject, results: tuple[LoadedProjectResult, ...]) -> bytes:
    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    for row in wbquant_table_rows(project, results):
        writer.writerow(
            [
                ""
                if value is None
                else f"{value:.2f}"
                if isinstance(value, float)
                else (
                    "text:" + value
                    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "text:"))
                    else value
                )
                for value in row
            ]
        )
    return stream.getvalue().encode("utf-8-sig")


def wbquant_xlsx_bytes(project: WBFigureProject, results: tuple[LoadedProjectResult, ...]) -> bytes:
    grouped = wbquant_table_rows(project, results)
    rows: list[tuple[Cell, ...]] = []
    ranges: list[tuple[int, int]] = []
    start = 1
    previous: Cell = None
    for row in grouped[1:]:
        if row[0] != previous:
            if previous is not None:
                ranges.append((start, len(rows)))
                rows.append(())
            start = len(rows) + 1
            rows.append((row[1], "条带", *grouped[0][3:]))
        rows.append((None, row[2], *row[3:]))
        previous = row[0]
    if rows:
        ranges.append((start, len(rows)))
    else:
        rows.append(("组名", "条带", *grouped[0][3:]))
    _, audit = project_table_rows(project, results)
    # Include every band status, not merely the legacy first target's summary.
    audit += (
        ("说明", "主表为WBQuant原始Signal，警告值不代表归一化有效信号"),
        ("原图行", "泳道", "条带", "状态", "原始Signal", "检测说明"),
    )
    audit += tuple(
        (
            r.row_id,
            lane.roi.lane_id,
            b.annotation.band_id,
            b.status,
            b.measurement.signal if b.measurement else None,
            "; ".join((*b.annotation.detection_notes, *b.quality_flags)),
        )
        for r in _current_results(project, results)
        for lane in r.result.lanes
        for b in lane.bands
    )
    original = two_sheet_xlsx_bytes(tuple(rows), audit)
    output = BytesIO()
    with ZipFile(BytesIO(original)) as source, ZipFile(output, "w", ZIP_DEFLATED) as target:
        for name in source.namelist():
            data = source.read(name)
            if name == "xl/workbook.xml":
                root = ET.fromstring(data)
                sheet = root.find(f"{{{NS}}}sheets/{{{NS}}}sheet")
                assert sheet is not None
                sheet.set("name", "灰度分析")
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            if name == "xl/worksheets/sheet1.xml":
                root = ET.fromstring(data)
                pane = root.find(f"{{{NS}}}sheetViews/{{{NS}}}sheetView/{{{NS}}}pane")
                assert pane is not None
                pane.attrib.clear()
                pane.attrib.update(
                    xSplit="2", topLeftCell="C1", activePane="topRight", state="frozen"
                )
                merges = ET.SubElement(root, f"{{{NS}}}mergeCells")
                for first, last in ranges:
                    if last > first:
                        for column in ("A",):
                            ET.SubElement(
                                merges, f"{{{NS}}}mergeCell", ref=f"{column}{first}:{column}{last}"
                            )
                for cell in root.iter(f"{{{NS}}}c"):
                    if (
                        cell.get("r", "")[0:1] not in ("A", "B")
                        and cell.find(f"{{{NS}}}v") is not None
                    ):
                        cell.set("s", "1")
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            if name == "[Content_Types].xml":
                root = ET.fromstring(data)
                ET.SubElement(
                    root,
                    "{http://schemas.openxmlformats.org/package/2006/content-types}Override",
                    PartName="/xl/styles.xml",
                    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml",
                )
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            if name == "xl/_rels/workbook.xml.rels":
                root = ET.fromstring(data)
                ET.SubElement(
                    root,
                    "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship",
                    Id="rId3",
                    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
                    Target="styles.xml",
                )
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            target.writestr(name, data)
        target.writestr(
            "xl/styles.xml",
            f'<styleSheet xmlns="{NS}"><fonts count="1"><font/></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border/></borders><cellStyleXfs count="1">'
            '<xf numFmtId="0"/></cellStyleXfs><cellXfs count="2">'
            '<xf numFmtId="0"/><xf numFmtId="2" applyNumberFormat="1"/>'
            "</cellXfs></styleSheet>",
        )
    return output.getvalue()


def export_wbquant_table(
    project: WBFigureProject,
    results: tuple[LoadedProjectResult, ...],
    destination: str | Path,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> Path:
    suffix = Path(destination).suffix.lower()
    if suffix not in (".csv", ".xlsx"):
        raise ValueError("请选择新的CSV或Excel文件")
    data = (
        wbquant_csv_bytes(project, results)
        if suffix == ".csv"
        else wbquant_xlsx_bytes(project, results)
    )
    return publish_table_bytes(data, destination, suffix, cancelled=cancelled)
