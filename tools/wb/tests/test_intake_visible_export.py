"""Independent expected Signals and literal OOXML values for the visible result table."""

import csv
from dataclasses import replace
from io import BytesIO, StringIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
from wb_tool.adapters.intake_table_export import export_intake_table, intake_table_bytes
from wb_tool.adapters.project_evidence import verify_project_evidence
from wb_tool.adapters.project_export import project_table_rows
from wb_tool.adapters.worksheet_export import NS
from wb_tool.api import fill_intake_table, intake_visible_table

from tools.wb.tests.test_intake_output import full_files


def test_unreviewed_raw_values_order_quality_and_missing_survive_export(tmp_path: Path) -> None:
    project, _, evidence = full_files(tmp_path)
    results = verify_project_evidence(project, evidence).results
    cells = tuple(i.cell for i in fill_intake_table(project, results))
    table = intake_visible_table(project, cells)
    legacy, _ = project_table_rows(project, results)
    # Reproduce the mismatch: visible raw Signal exists where the valid-value table is empty.
    warned = replace(cells[0], status="quality_review", value=None)
    warning_table = intake_visible_table(project, (warned, *cells[1:]))
    assert warning_table.rows[0][2] == 400.0 and (0, 2) in warning_table.quality
    assert any(v is None for row in legacy[1:] for v in row[2:])
    expected = [(400.0 * scale, 800.0 * scale, None) for scale in (1, 2, 3)]
    assert [row[2:-1] for row in table.rows] == expected
    assert table.headers == ("Fig", "蛋白", "泳道 1", "泳道 2", "泳道 3", "状态")
    data = intake_table_bytes(project, results)
    with ZipFile(BytesIO(data)) as book:
        sheet = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))
        records = sheet.findall(f"{{{NS}}}sheetData/{{{NS}}}row")
        for ri, values in enumerate(expected, 1):
            for ci, value in enumerate(values, 2):
                cell = records[ri][ci]
                if value is None:
                    assert cell.find(f"{{{NS}}}v") is None
                    assert cell.findtext(f"{{{NS}}}is/{{{NS}}}t") == "—"
                else:
                    assert float(cell.findtext(f"{{{NS}}}v", "nan")) == value
                    assert cell.get("s") == ("3" if (ri - 1, ci) in table.quality else "2")
        assert not sheet.findall(f".//{{{NS}}}f")
        styles = ET.fromstring(book.read("xl/styles.xml"))
        number_style = styles.find(f"{{{NS}}}numFmts/{{{NS}}}numFmt")
        assert number_style is not None and number_style.get("formatCode") == "#,##0.##"
        assert book.read("xl/worksheets/sheet2.xml")
    csv_rows = list(
        csv.reader(StringIO(intake_table_bytes(project, results, csv=True).decode("utf-8-sig")))
    )
    assert csv_rows[0] == list(table.headers)
    assert [row[4] for row in csv_rows[1:]] == ["text:—"] * 3
    assert csv_rows[1][2].removeprefix("text:").removesuffix("*") == "400"
    before = project.model_dump_json()
    destination = tmp_path / "visible.xlsx"
    assert export_intake_table(project, results, str(destination)) == destination
    with pytest.raises(FileExistsError):
        export_intake_table(project, results, str(destination))
    with pytest.raises(ValueError, match="取消"):
        export_intake_table(project, results, str(tmp_path / "cancel.xlsx"), cancelled=lambda: True)
    assert not (tmp_path / "cancel.xlsx").exists()
    assert project.model_dump_json() == before
    # An actual numeric zero survives; failed/missing evidence never manufactures one.
    zero = replace(cells[0], raw_integral=0.0)
    assert intake_visible_table(project, (zero, *cells[1:])).rows[0][2] == 0.0
    unavailable = intake_visible_table(
        project, tuple(i.cell for i in fill_intake_table(project, ()))
    )
    assert all(v is None for row in unavailable.rows for v in row[2:-1])


def test_visible_export_never_uses_tampered_result_evidence(tmp_path: Path) -> None:
    project, _, evidence = full_files(tmp_path)
    Path(evidence[0].result_path).write_bytes(b"tampered")
    checked = verify_project_evidence(project, evidence)
    table = intake_visible_table(
        project, tuple(i.cell for i in fill_intake_table(project, checked.results))
    )
    assert all(v is None for v in table.rows[0][2:-1])
    assert any(v is not None for row in table.rows[1:] for v in row[2:-1])
