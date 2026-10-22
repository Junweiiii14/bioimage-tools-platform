"""Export the visible wide table without changing archive table v1 semantics."""

from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal, localcontext
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from wb_tool.adapters.csv_export import csv_bytes
from wb_tool.adapters.project_export import project_table_rows
from wb_tool.adapters.worksheet_export import NS, publish_table_bytes, two_sheet_xlsx_bytes
from wb_tool.application.intake_output import WBIntakeOutputProject, fill_intake_table
from wb_tool.application.intake_result_table import intake_visible_table
from wb_tool.application.project_analysis import LoadedProjectResult


def _display_number(value: float) -> str:
    # Intl.NumberFormat's default halfExpand rounds decimal ties away from zero.
    # Python .2f instead rounds the binary float with ties-to-even.
    number = Decimal(str(value))
    with localcontext() as context:
        context.prec = max(32, number.adjusted() + 4)
        rounded = number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(rounded, ",f").rstrip("0").rstrip(".")


def intake_table_bytes(
    project: WBIntakeOutputProject, results: tuple[LoadedProjectResult, ...], *, csv: bool = False
) -> bytes:
    table = intake_visible_table(
        project, tuple(i.cell for i in fill_intake_table(project, results))
    )
    marks = set(table.quality)
    if csv:
        # CSV has no number styles. Use the same two-decimal display and quality suffix.
        rows = tuple(
            tuple(
                "—"
                if v is None
                else (_display_number(v) + ("*" if (ri, ci) in marks else ""))
                if isinstance(v, float)
                else v
                for ci, v in enumerate(row)
            )
            for ri, row in enumerate(table.rows)
        )
        return csv_bytes((table.headers, *rows))
    rows = tuple(tuple("—" if v is None else v for v in row) for row in table.rows)
    _, audit = project_table_rows(project, results)
    audit += (("主表视图", "intake_visible_table@1", "原始灰度积分，非归一化有效信号"),)
    original = two_sheet_xlsx_bytes((table.headers, *rows), audit)
    output = BytesIO()
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    type_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    with ZipFile(BytesIO(original)) as source, ZipFile(output, "w", ZIP_DEFLATED) as target:
        for name in source.namelist():
            data = source.read(name)
            if name == "xl/worksheets/sheet1.xml":
                root = ET.fromstring(data)
                for ri, row in enumerate(root.findall(f"{{{NS}}}sheetData/{{{NS}}}row")):
                    for ci, cell in enumerate(row):
                        cell.set(
                            "s",
                            "1"
                            if ri == 0
                            else "3"
                            if (ri - 1, ci) in marks
                            else "2"
                            if cell.find(f"{{{NS}}}v") is not None
                            else "0",
                        )
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            elif name == "xl/_rels/workbook.xml.rels":
                root = ET.fromstring(data)
                ET.SubElement(
                    root,
                    f"{{{rel_ns}}}Relationship",
                    Id="rId3",
                    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
                    Target="styles.xml",
                )
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            elif name == "[Content_Types].xml":
                root = ET.fromstring(data)
                ET.SubElement(
                    root,
                    f"{{{type_ns}}}Override",
                    PartName="/xl/styles.xml",
                    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml",
                )
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            target.writestr(name, data)
        target.writestr(
            "xl/styles.xml",
            f'''<styleSheet xmlns="{NS}">
<numFmts count="2">
<numFmt numFmtId="164" formatCode='#,##0.##'/>
<numFmt numFmtId="165" formatCode='#,##0.##&quot;*&quot;'/>
</numFmts>
<fonts count="2">
<font>
<sz val="11"/>
<name val="Calibri"/>
</font>
<font>
<b/>
<sz val="11"/>
<name val="Calibri"/>
</font>
</fonts>
<fills count="3">
<fill>
<patternFill patternType="none"/>
</fill>
<fill>
<patternFill patternType="gray125"/>
</fill>
<fill>
<patternFill patternType="solid">
<fgColor rgb="FFE9EEE6"/>
<bgColor indexed="64"/>
</patternFill>
</fill>
</fills>
<borders count="1">
<border/>
</borders>
<cellStyleXfs count="1">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
</cellStyleXfs>
<cellXfs count="4">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" applyFont="1" applyFill="1"/>
<xf numFmtId="164" fontId="0" fillId="0" borderId="0" applyNumberFormat="1">
<alignment horizontal="right"/>
</xf>
<xf numFmtId="165" fontId="0" fillId="0" borderId="0" applyNumberFormat="1">
<alignment horizontal="right"/>
</xf>
</cellXfs>
</styleSheet>''',
        )
    return output.getvalue()


def export_intake_table(
    project: WBIntakeOutputProject,
    results: tuple[LoadedProjectResult, ...],
    destination: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> Path:
    suffix = Path(destination).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise ValueError("请选择新的 .xlsx 或 .csv 文件")
    return publish_table_bytes(
        intake_table_bytes(project, results, csv=suffix == ".csv"),
        destination,
        suffix,
        cancelled=cancelled,
    )
