"""Actual offline OCR + independent rectangular band areas + explicit automatic cell writes."""

from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from PIL import Image, ImageDraw, ImageFont
from pytest import MonkeyPatch
from wb_tool.api import (
    AnalysisCancelled,
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    LaneAnnotation,
    LaneROI,
    MeasurementBinding,
    OCRRecognition,
    TextBounds,
    TextToken,
    Worksheet,
    WorksheetColumn,
    WorksheetRow,
    analyze_annotations,
    export_worksheet,
    fill_worksheet,
    load_tiff,
    propose_worksheet,
    recognize_figure,
    suggest_figures,
)


def test_actual_ocr_and_automatic_table_values(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    import socket

    def offline(*args: object, **kwargs: object) -> None:
        raise AssertionError("Recognition must not connect to the network")

    monkeypatch.setattr(socket.socket, "connect", offline)
    image = Image.new("L", (1200, 500), 245)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=42)
    labels = (
        ("Fig 1A", 30, 20),
        ("AKT", 30, 150),
        ("GAPDH", 30, 320),
        ("Fig 2B", 650, 20),
        ("ERK1/2", 650, 150),
        ("beta-actin", 650, 320),
    )
    for text, x, y in labels:
        draw.text((x, y), text, font=font, fill=0)
    for x in (280, 380, 900, 1000):
        draw.rectangle((x, 165, x + 19, 185), fill=100)
        draw.rectangle((x, 335, x + 19, 355), fill=150)
    path = tmp_path / "fig-composite.tif"
    tifffile.imwrite(path, np.array(image))
    loaded = load_tiff(path)
    recognition = recognize_figure(str(path), loaded.sha256)
    figures = suggest_figures(recognition)
    assert [(figure.heading.text, [row.text for row in figure.rows]) for figure in figures] == [
        ("Fig 1A", ["AKT", "GAPDH"]),
        ("Fig 2B", ["ERK1/2", "beta-actin"]),
    ]
    lanes = tuple(
        LaneAnnotation(
            LaneROI(f"L{index}", x, 120, x + 20, 400),
            (
                BandAnnotation("top", BandBounds(40, 70)),
                BandAnnotation("bottom", BandBounds(210, 240)),
            ),
        )
        for index, x in enumerate((280, 380, 900, 1000))
    )
    result = analyze_annotations(loaded, AnalysisRequest(loaded.sha256, 0, "dark", lanes))
    worksheet = propose_worksheet(recognition, result)
    assert len(worksheet.rows) == 4 and len(worksheet.bindings) == 8
    assert all(
        cell.value is None and cell.status == "unconfirmed"
        for cell in fill_worksheet(worksheet, result)
    )
    confirmed = replace(
        worksheet, rows=tuple(replace(row, confirmed=True) for row in worksheet.rows)
    )
    cells = fill_worksheet(confirmed, result)
    # Rectangle contrast × 21 samples. Profile mean does not multiply by lane width.
    assert [cell.value for cell in cells] == [
        145 * 21,
        145 * 21,
        95 * 21,
        95 * 21,
        145 * 21,
        145 * 21,
        95 * 21,
        95 * 21,
    ]
    assert all(cell.status == "valid" for cell in cells)
    assert load_tiff(path).sha256 == loaded.sha256
    exported = Path(export_worksheet(confirmed, result, str(tmp_path / "results.xlsx")))
    with ZipFile(exported) as archive:
        assert archive.testzip() is None
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        namespace = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        assert [float(node.text or "nan") for node in sheet.findall(".//s:v", namespace)] == [
            3045.0,
            3045.0,
            1995.0,
            1995.0,
            3045.0,
            3045.0,
            1995.0,
            1995.0,
        ]
    before = exported.read_bytes()
    with pytest.raises(FileExistsError):
        export_worksheet(confirmed, result, str(exported))
    assert exported.read_bytes() == before


def test_missing_excluded_zero_and_wrong_source_remain_distinct(tmp_path: Path) -> None:
    path = tmp_path / "flat.tif"
    tifffile.imwrite(path, np.full((4, 2), 100, dtype=np.uint8))
    loaded = load_tiff(path)
    lane = LaneAnnotation(
        LaneROI("L", 0, 0, 2, 4),
        (
            BandAnnotation("zero", BandBounds(0, 3)),
            BandAnnotation("excluded", BandBounds(0, 3), included=False),
        ),
    )
    result = analyze_annotations(loaded, AnalysisRequest(loaded.sha256, 0, "dark", (lane,)))
    rows = tuple(
        WorksheetRow(name, "F", "Fig 1A", name, True)
        for name in ("zero", "excluded", "missing", "unbound")
    )
    bindings = tuple(
        MeasurementBinding("F", name, "C", "L", name) for name in ("zero", "excluded", "missing")
    )
    worksheet = Worksheet(loaded.sha256, rows, (WorksheetColumn("C", "control"),), bindings)
    cells = fill_worksheet(worksheet, result)
    assert [(cell.status, cell.value) for cell in cells] == [
        ("valid", 0.0),
        ("excluded", None),
        ("missing_measurement", None),
        ("unbound", None),
    ]
    with pytest.raises(ValueError, match="来源"):
        fill_worksheet(replace(worksheet, source_sha256="a" * 64), result)
    with pytest.raises(ValueError, match="跨 Fig"):
        replace(worksheet, bindings=(replace(bindings[0], figure_id="another"),))
    renamed = replace(worksheet, rows=tuple(replace(row, row_name="=1+2") for row in rows))
    exported = export_worksheet(renamed, result, str(tmp_path / "literal.xlsx"))
    with ZipFile(exported) as archive:
        text = archive.read("xl/worksheets/sheet1.xml").decode()
        assert "=1+2" in text and "<f>" not in text
        assert 'r="C4" />' in text and "<v>0.0</v>" in text


def test_layout_preserves_unrecognized_names_and_single_figure() -> None:
    tokens = (
        TextToken("title", "Fig 3C", TextBounds(10, 10, 100, 40), 0.9),
        TextToken("row", "unexpected-Protein", TextBounds(20, 80, 200, 100), 0.55),
    )
    recognition = OCRRecognition("a" * 64, 400, 300, tokens, "fixture", ())
    figures = suggest_figures(recognition)
    assert len(figures) == 1 and not figures[0].confirmed
    assert figures[0].rows[0].text == "unexpected-Protein"
    assert suggest_figures(replace(recognition, tokens=(tokens[1],))) == ()


def test_short_figures_drifted_titles_and_sample_headers() -> None:
    tokens = (
        TextToken("F1", "1G", TextBounds(80, 10, 120, 40), 1.0),
        TextToken("sample", "Control", TextBounds(320, 40, 410, 130), 1.0),
        TextToken("R1", "TARGET", TextBounds(130, 160, 270, 190), 1.0),
        TextToken("R2", "GAPDH", TextBounds(135, 260, 270, 290), 1.0),
        TextToken("F2", "2B", TextBounds(2, 400, 42, 430), 1.0),
        TextToken("R3", "Unknown", TextBounds(130, 560, 270, 590), 0.6),
        TextToken("R4", "Unknown", TextBounds(670, 560, 810, 590), 0.6),
        TextToken("group", "Treatment", TextBounds(350, 460, 520, 490), 1.0),
    )
    recognition = OCRRecognition("a" * 64, 1200, 800, tokens, "fixture", ())
    figures = suggest_figures(recognition)
    assert [figure.heading.text for figure in figures] == ["1G", "2B"]
    assert [[token.token_id for token in figure.rows] for figure in figures] == [
        ["R1", "R2"],
        ["R3", "R4"],
    ]
    assert len(recognition.tokens) == 8  # Candidate filtering never erases OCR evidence.


def test_cancellation_before_model_or_image_load() -> None:
    with pytest.raises(AnalysisCancelled):
        recognize_figure("does-not-exist.tif", "a" * 64, cancelled=lambda: True)


@pytest.mark.parametrize("corrupted", [False, True])
def test_models_are_verified_before_engine_or_input(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    corrupted: bool,
) -> None:
    import rapidocr

    models = tmp_path / "models"
    models.mkdir()
    if corrupted:
        (models / "PP-OCRv6_det_small.onnx").write_bytes(b"not the pinned model")
    monkeypatch.setattr(rapidocr, "__file__", str(tmp_path / "__init__.py"))

    def forbidden_engine(*args: object, **kwargs: object) -> None:
        raise AssertionError("Must fail before engine initialization or automatic download")

    monkeypatch.setattr(rapidocr, "RapidOCR", forbidden_engine)
    with pytest.raises(ValueError, match="OCR 模型"):
        recognize_figure("never-read.tif", "a" * 64)
