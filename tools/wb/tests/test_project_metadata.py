"""Literal workbook boundaries, exact source matching, and atomic/stale metadata edits."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from struct import unpack_from
from zipfile import ZIP_BZIP2, ZIP_DEFLATED, ZipFile

import pytest
from tool_contracts.api import AssetRef
from wb_tool.api import (
    FigureRow,
    LaneROI,
    MetadataCell,
    MetadataSheet,
    WBFigureProject,
    apply_metadata,
    filename_metadata,
    preview_metadata,
    read_metadata_file,
)


def project() -> WBFigureProject:
    rows = tuple(
        FigureRow(
            row_id=f"r{i}",
            source=AssetRef(
                asset_id=f"a{i}", relative_path=f"inputs/{i}", sha256=str(i) * 64, size_bytes=10
            ),
            filename="same.tiff" if i < 2 else "Fig2_AKT_3.tif",
            width=30,
            height=40,
            bit_depth=16,
            figure="Fig1",
            protein="AKT",
            lane_count=3,
            empty_lanes=(2,),
            notes="kept",
            roi=LaneROI(f"r{i}", 0, 5, 30, 25),
            reviewed=True,
        )
        for i in range(3)
    )
    return WBFigureProject(project_id="project", rows=rows, figure_order=("Fig1",))


def sheet(*rows: tuple[str, ...]) -> MetadataSheet:
    return MetadataSheet(
        "metadata", tuple(tuple(MetadataCell(value) for value in row) for row in rows)
    )


def test_exact_keys_duplicate_names_and_manual_disambiguation() -> None:
    p = project()
    preview = preview_metadata(
        p,
        sheet(
            ("file", "protein"), ("same.tiff", "p-AKT"), ("Same.tiff", "B"), ("missing.tif", "C")
        ),
        0,
        "filename",
        0,
        (("protein", 1),),
    )
    assert preview.entries[0].candidates == ("r0", "r1")
    assert not any(e.target_id for e in preview.entries)
    with pytest.raises(ValueError, match="明确关联"):
        apply_metadata(p, preview, preview.entries[:1], ("protein",))
    updated = apply_metadata(
        p, preview, (replace(preview.entries[0], target_id="r1"),), ("protein",)
    )
    assert updated.rows[0] == p.rows[0]
    assert updated.rows[1].protein == "p-AKT" and updated.rows[1].reviewed
    assert updated.rows[1].source == p.rows[1].source and updated.rows[1].roi == p.rows[1].roi
    assert p.rows[1].protein == "AKT"


def test_duplicate_input_and_duplicate_destination_are_not_first_match_wins() -> None:
    p = project()
    preview = preview_metadata(
        p, sheet(("row", "N"), ("r0", "2"), ("r0", "3")), 0, "row_id", 0, (("lane_count", 1),)
    )
    assert all(not e.target_id and "重复" in e.issue for e in preview.entries)
    with pytest.raises(ValueError, match="不同"):
        apply_metadata(
            p, preview, tuple(replace(e, target_id="r0") for e in preview.entries), ("lane_count",)
        )


def test_blank_clear_selected_fields_order_and_project_name() -> None:
    p = project()
    data = sheet(
        ("row", "N", "empty", "notes", "order", "project", "fig"),
        ("r0", "", "无", "[]", "2", "experiment", "Fig2"),
        ("r2", "3.0", "", "", "1", "experiment", "Fig2"),
    )
    fields = ("lane_count", "empty_lanes", "notes", "order", "project_name", "figure")
    preview = preview_metadata(
        p, data, 0, "row_id", 0, tuple((field, i + 1) for i, field in enumerate(fields))
    )
    changed = apply_metadata(p, preview, preview.entries, fields)
    assert [r.row_id for r in changed.rows] == ["r2", "r1", "r0"]
    assert changed.rows[1] == p.rows[1]
    assert changed.rows[2].empty_lanes == () and not changed.rows[2].reviewed
    assert changed.rows[2].notes == "" and changed.rows[2].lane_count == 3
    assert changed.rows[0].empty_lanes == (2,) and changed.rows[0].reviewed
    assert changed.rows[0].notes == "kept"
    assert changed.name == "experiment" and changed.figure_order == ("Fig1", "Fig2")
    labels_only = apply_metadata(p, preview, preview.entries, ("figure",))
    assert all(row.reviewed for row in labels_only.rows)
    assert labels_only.name == p.name


@pytest.mark.parametrize(
    "n,empty",
    [
        ("0", ""),
        ("NaN", ""),
        ("2.5", ""),
        ("97", ""),
        ("1", ""),
        ("3", "0"),
        ("3", "2,2"),
        ("3", "4"),
    ],
)
def test_invalid_last_row_is_atomic(n: str, empty: str) -> None:
    p = project()
    before = p.model_dump_json()
    preview = preview_metadata(
        p,
        sheet(("row", "N", "empty", "protein"), ("r0", "3", "无", "new"), ("r1", n, empty, "new")),
        0,
        "row_id",
        0,
        (("lane_count", 1), ("empty_lanes", 2), ("protein", 3)),
    )
    with pytest.raises(ValueError):
        apply_metadata(p, preview, preview.entries, ("lane_count", "empty_lanes", "protein"))
    assert p.model_dump_json() == before


def test_stale_preview_missing_mapping_and_conflicting_project_names() -> None:
    p = project()
    table = sheet(("row", "name"), ("r0", "first"), ("r1", "second"))
    preview = preview_metadata(p, table, 0, "row_id", 0, (("project_name", 1),))
    with pytest.raises(ValueError, match="已修改"):
        apply_metadata(
            p.model_copy(update={"name": "edited"}), preview, preview.entries, ("project_name",)
        )
    with pytest.raises(ValueError, match="一个实验项目"):
        apply_metadata(p, preview, preview.entries, ("project_name",))
    for columns in ((), (("protein", -1),), (("protein", 0),), (("protein", 2),)):
        with pytest.raises(ValueError):
            preview_metadata(p, table, 0, "row_id", 0, columns)


def test_filename_literal_rule_matches_full_stem_and_keeps_unmatched_explicit() -> None:
    p = project()
    proposal = filename_metadata(p, ("r0", "r2"), "_", ("figure", "protein", "lane_count"))
    assert "分段数" in proposal.entries[0].issue
    changed = apply_metadata(p, proposal, proposal.entries[1:], ("figure", "protein", "lane_count"))
    assert changed.rows[2].figure == "Fig2" and changed.rows[2].lane_count == 3
    assert changed.rows[2].reviewed
    with pytest.raises(ValueError):
        filename_metadata(p, ("r2",), "", ("protein",))
    with pytest.raises(ValueError):
        filename_metadata(p, ("r2",), "_", ("protein", "protein"))


def write_book(
    path: Path,
    cells: str,
    extra_xml: str = "",
    *,
    extras: dict[str, str] | None = None,
    compression: int = ZIP_DEFLATED,
) -> None:
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    with ZipFile(path, "w", compression=compression) as z:
        z.writestr(
            "xl/workbook.xml",
            f'<workbook xmlns="{ns}" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="元信息" sheetId="1" r:id="r1"/></sheets></workbook>',
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="r2" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/sharedStrings" Target="sharedStrings.xml"/></Relationships>',
        )
        z.writestr(
            "xl/sharedStrings.xml",
            f'<sst xmlns="{ns}"><si><t>原图名称</t></si><si><r><t>蛋</t></r><r><t>白</t></r>'
            '<rPh sb="0" eb="1"><t>phonetic</t></rPh></si></sst>',
        )
        z.writestr(
            "xl/worksheets/sheet1.xml",
            f'<worksheet xmlns="{ns}"><sheetData>{cells}</sheetData>{extra_xml}</worksheet>',
        )
        for name, content in (extras or {}).items():
            z.writestr(name, content)


def test_xlsx_literals_formula_cache_array_merge_and_errors(tmp_path: Path) -> None:
    source = tmp_path / "input.xlsx"
    write_book(
        source,
        '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
        '<row r="2"><c r="A2" t="inlineStr"><is><t>same.tiff</t></is></c>'
        '<c r="B2"><f t="array" ref="B2:B3">1+1</f><v>2</v></c></row>'
        '<row r="3"><c r="B3"><v>2</v></c><c r="C3" t="e"><v>#REF!</v></c></row>'
        '<row r="4"><c r="A4" t="inlineStr"><is><t>literal</t></is></c></row>',
        '<mergeCells><mergeCell ref="A4:B4"/></mergeCells>',
    )
    before = source.read_bytes()
    book = read_metadata_file(source)
    assert book.sha256 == sha256(before).hexdigest() and source.read_bytes() == before
    assert book.sheets[0].rows[0][:2] == (MetadataCell("原图名称"), MetadataCell("蛋白"))
    assert book.sheets[0].rows[1][0].text == "same.tiff"
    for r, c in ((1, 1), (2, 1), (2, 2), (3, 0), (3, 1)):
        assert book.sheets[0].rows[r][c].error
    assert book.sheets[0].rows[1][1].text == "" and book.sheets[0].rows[2][1].text == ""
    preview = preview_metadata(project(), book.sheets[0], 0, "filename", 0, (("protein", 1),))
    with pytest.raises(ValueError, match="公式"):
        apply_metadata(
            project(), preview, (replace(preview.entries[0], target_id="r0"),), ("protein",)
        )


@pytest.mark.parametrize(
    "cells,extra",
    [
        ('<row><c r="BM1"><v>1</v></c></row>', {}),
        ('<row><c r="A1026"><v>1</v></c></row>', {}),
        ('<row><c r="A1" t="s"><v>-1</v></c></row>', {}),
        ('<row><c r="A1"/><c r="A1"/></row>', {}),
        ("", {"xl/vbaProject.bin": "macro"}),
        ("", {"xl/externalLinks/externalLink1.xml": "external"}),
    ],
)
def test_xlsx_invalid_or_active_content_rejected(
    tmp_path: Path, cells: str, extra: dict[str, str]
) -> None:
    source = tmp_path / "bad.xlsx"
    write_book(source, cells, extras=extra)
    with pytest.raises(ValueError):
        read_metadata_file(source)


def test_bad_xml_zip_compression_cancel_and_csv_limits(tmp_path: Path) -> None:
    path = tmp_path / "bad.xlsx"
    path.write_bytes(b"not a zip")
    with pytest.raises(ValueError):
        read_metadata_file(path)
    write_book(path, "", compression=ZIP_BZIP2)
    with pytest.raises(ValueError, match="压缩"):
        read_metadata_file(path)
    write_book(path, '<!DOCTYPE x [<!ENTITY e "bad">]>')
    with pytest.raises(ValueError, match="声明"):
        read_metadata_file(path)
    csv_path = tmp_path / "metadata.csv"
    csv_path.write_text('\ufeffrow_id,蛋白,N\nr0,"p,AKT",0\nr1,=1+1,\n', encoding="utf-8")
    book = read_metadata_file(csv_path)
    assert book.sheets[0].rows[1] == (MetadataCell("r0"), MetadataCell("p,AKT"), MetadataCell("0"))
    assert book.sheets[0].rows[2][1].error and book.sheets[0].rows[2][2].text == ""
    with pytest.raises(ValueError, match="取消"):
        read_metadata_file(csv_path, cancelled=lambda: True)
    for text in ('"unterminated', "x" * 2001, "a\n" * 1026, ",".join("x" for _ in range(65))):
        csv_path.write_text(text, encoding="utf-8")
        with pytest.raises(ValueError):
            read_metadata_file(csv_path)


def test_embedded_images_are_not_decoded_and_range_expansion_stays_bounded(tmp_path: Path) -> None:
    path = tmp_path / "images.xlsx"
    write_book(
        path,
        '<row><c r="A1"><v>3</v></c></row>',
        extras={"xl/media/ignored.tiff": "x" * (33 * 1024 * 1024)},
    )
    assert read_metadata_file(path).sheets[0].rows[0][0].text == "3"
    assert not (tmp_path / "xl").exists()
    write_book(
        path,
        "",
        '<mergeCells><mergeCell ref="A1:BL1025"/><mergeCell ref="A1:BL1025"/></mergeCells>',
    )
    with pytest.raises(ValueError, match="累计"):
        read_metadata_file(path)


def test_corrupt_deflate_stream_reports_a_read_error(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.xlsx"
    write_book(path, '<row><c r="A1"><v>3</v></c></row>')
    with ZipFile(path) as archive:
        offset = archive.getinfo("xl/workbook.xml").header_offset
    raw = bytearray(path.read_bytes())
    name_size, extra_size = unpack_from("<HH", raw, offset + 26)
    start = offset + 30 + name_size + extra_size
    raw[start] = 255  # Reserved DEFLATE block type; no plausible cached value is returned.
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="无法读取"):
        read_metadata_file(path)
