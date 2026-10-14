"""Dependency-free OOXML result export; names are literal strings and output is never replaced."""

import math
import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZIP_DEFLATED, ZipFile

from wb_tool.application.analysis import AnalysisResult
from wb_tool.application.worksheet import fill_worksheet
from wb_tool.domain.worksheet import Worksheet

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
Cell = str | float | int | None


def _column(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _sheet(rows: tuple[tuple[Cell, ...], ...]) -> bytes:
    if sum(len(row) for row in rows) > 200000:
        raise ValueError("导出表格超出单次预算")
    root = Element("worksheet", xmlns=NS)
    views = SubElement(root, "sheetViews")
    view = SubElement(views, "sheetView", workbookViewId="0")
    SubElement(view, "pane", xSplit="2", ySplit="1", topLeftCell="C2", state="frozen")
    columns = SubElement(root, "cols")
    width = max((len(row) for row in rows), default=1)
    if width > 16384:
        raise ValueError("导出列数超出 Excel 限制")
    for ci in range(width):
        SubElement(columns, "col", min=str(ci + 1), max=str(ci + 1), width="22", customWidth="1")
    data = SubElement(root, "sheetData")
    for ri, row in enumerate(rows, 1):
        record = SubElement(data, "row", r=str(ri))
        for ci, value in enumerate(row, 1):
            cell = SubElement(record, "c", r=f"{_column(ci)}{ri}")
            if value is None:
                continue
            if isinstance(value, str):
                if len(value.encode("utf-16-le")) // 2 > 32767 or any(
                    ord(char) < 32 and char not in "\t\n\r" for char in value
                ):
                    raise ValueError("表格文字超限或含非法 XML 控制符")
                cell.set("t", "inlineStr")
                text = SubElement(SubElement(cell, "is"), "t")
                text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                text.text = value
            else:
                if isinstance(value, bool) or not math.isfinite(value):
                    raise ValueError("表格数值必须有限且不能为布尔值")
                SubElement(cell, "v").text = str(value)
    return tostring(root, encoding="utf-8", xml_declaration=True)


def worksheet_xlsx_bytes(worksheet: Worksheet, result: AnalysisResult) -> bytes:
    cells = fill_worksheet(worksheet, result)
    values = {(cell.row_id, cell.column_id): cell.value for cell in cells}
    rows: list[tuple[Cell, ...]] = [("Fig", "行名", *(column.name for column in worksheet.columns))]
    for row in worksheet.rows:
        rows.append(
            (
                row.figure_name,
                row.row_name,
                *(values[(row.row_id, column.column_id)] for column in worksheet.columns),
            )
        )
    audit: list[tuple[Cell, ...]] = [
        ("来源 SHA256", result.request.source_sha256),
        ("草稿修订", result.request.revision),
        ("算法", result.algorithm_id),
        ("单位", "intensity*pixel"),
        ("行 ID", "列 ID", "状态", "原因"),
    ]
    audit.extend((cell.row_id, cell.column_id, cell.status, cell.reason) for cell in cells)
    types = Element("Types", xmlns="http://schemas.openxmlformats.org/package/2006/content-types")
    SubElement(
        types,
        "Default",
        Extension="rels",
        ContentType="application/vnd.openxmlformats-package.relationships+xml",
    )
    SubElement(types, "Default", Extension="xml", ContentType="application/xml")
    for name, content in (
        (
            "/xl/workbook.xml",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
        ),
        (
            "/xl/worksheets/sheet1.xml",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
        ),
        (
            "/xl/worksheets/sheet2.xml",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
        ),
    ):
        SubElement(types, "Override", PartName=name, ContentType=content)
    workbook = Element("workbook", xmlns=NS)
    sheets = SubElement(workbook, "sheets")
    for index, name in enumerate(("WB结果", "状态与来源"), 1):
        SubElement(
            sheets,
            "sheet",
            name=name,
            sheetId=str(index),
            attrib={f"{{{DOC_REL}}}id": f"rId{index}"},
        )
    relationships = Element("Relationships", xmlns=REL)
    SubElement(
        relationships,
        "Relationship",
        Id="rId1",
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        Target="xl/workbook.xml",
    )
    sheet_relationships = Element("Relationships", xmlns=REL)
    for index in (1, 2):
        SubElement(
            sheet_relationships,
            "Relationship",
            Id=f"rId{index}",
            Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
            Target=f"worksheets/sheet{index}.xml",
        )
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        for path, root in (
            ("[Content_Types].xml", types),
            ("_rels/.rels", relationships),
            ("xl/workbook.xml", workbook),
            ("xl/_rels/workbook.xml.rels", sheet_relationships),
        ):
            archive.writestr(path, tostring(root, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/worksheets/sheet1.xml", _sheet(tuple(rows)))
        archive.writestr("xl/worksheets/sheet2.xml", _sheet(tuple(audit)))
    return stream.getvalue()


def export_worksheet(worksheet: Worksheet, result: AnalysisResult, destination: str | Path) -> Path:
    data = worksheet_xlsx_bytes(worksheet, result)
    target = Path(destination).absolute()
    if target.suffix.lower() != ".xlsx":
        raise ValueError("请选择新的 .xlsx 文件")
    for parent in (target.parent, *target.parent.parents):
        if parent.is_symlink() or parent.is_junction():
            raise ValueError("导出目录不能经过符号链接或 junction")
    stage = target.parent / (".wb-export-" + uuid4().hex + ".tmp")
    try:
        with stage.open("xb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        # Atomic no-replace publication on NTFS and normal Linux filesystems.
        os.link(stage, target)
    finally:
        if stage.exists():
            stage.unlink()
    return target
