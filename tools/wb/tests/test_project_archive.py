"""Portable bytes, explicit missing states and independently expected triangle values."""

import csv
import json
from collections.abc import Callable
from dataclasses import replace
from hashlib import sha256
from io import BytesIO, StringIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
import tifffile
from pydantic import TypeAdapter
from tool_contracts.api import RunRecord
from wb_tool.adapters.csv_export import csv_bytes
from wb_tool.adapters.project_evidence import verify_project_evidence
from wb_tool.api import (
    AnalysisResult,
    ArchiveRunEvidence,
    FigureSourcePath,
    OCRRecognition,
    ProjectOCRState,
    SamplePair,
    bind_project_ocr_row,
    export_figure_bundle,
    export_project_normalization,
    export_project_ocr_table,
    export_project_table,
    install_project_recognition,
    make_normalization_plan,
    project_with_normalizations,
    project_with_ocr,
    read_project_ocr_result,
)

from tools.wb.tests.test_project_analysis import asset, complete, configured, recognized_project


def csv_rows(data: bytes) -> list[dict[str, str]]:
    return [
        {k: v.removeprefix("text:") for k, v in row.items()}
        for row in csv.DictReader(StringIO(data.decode("utf-8-sig"), newline=""))
    ]


def bundle(tmp_path: Path):
    project, paths = configured(tmp_path)
    project = project.model_copy(
        update={
            "rows": project.rows[:2],
            "figure_order": ("Fig1",),
            "template": project.template.model_copy(update={"font_size": 8}),
        }
    )
    frozen = project.model_dump_json().encode()
    project, results = complete(project, paths)
    sources = tuple(
        FigureSourcePath(row.source.sha256, str(path))
        for row, path in zip(project.rows, paths, strict=True)
        if row.source
    )
    evidence: list[ArchiveRunEvidence] = []
    for plan, loaded in zip(project.analyses, results, strict=True):
        assert plan.run and plan.run.result
        request = tmp_path / (plan.row_id + "-request.json")
        result = tmp_path / (plan.row_id + "-result.json")
        request.write_bytes(frozen)
        result.write_bytes(TypeAdapter(AnalysisResult).dump_json(loaded.result))
        evidence.append(ArchiveRunEvidence(plan.run, str(request), str(result)))
    # Reuse controlled synthetic OCR tokens/model identities, never a real lab label.
    other = tmp_path / "recognition"
    other.mkdir()
    _, _, sample, _ = recognized_project(other)
    composite = tmp_path / "composite.tif"
    composite.write_bytes(b"composite")
    project = project_with_ocr(
        project,
        ProjectOCRState(
            source=asset(b"composite", "ocr-source"),
            filename="composite.tif",
            width=1000,
            height=500,
        ),
    )
    ocr_request = project.model_dump_json().encode()
    raw = TypeAdapter(OCRRecognition).dump_json(sample.recognition)
    run = RunRecord(
        document_id=project.project_id,
        tool_id="wb-figure",
        revision=project.revision,
        run_id="ocr",
        state="succeeded",
        request=asset(ocr_request, "ocr-request"),
        pid=123,
        result=asset(raw, "ocr-result"),
    )
    loaded_ocr = read_project_ocr_result(project, run, raw)
    project = install_project_recognition(project, loaded_ocr)
    assert project.ocr
    for row, target in zip(project.ocr.rows, project.rows, strict=True):
        project = bind_project_ocr_row(project, row.row_id, target.row_id)
    assert project.ocr
    rows = tuple(row.model_copy(update={"confirmed": True}) for row in project.ocr.rows)
    project = project_with_ocr(project, project.ocr.model_copy(update={"rows": rows}))
    request_path, result_path = tmp_path / "ocr-request.json", tmp_path / "ocr-result.json"
    request_path.write_bytes(ocr_request)
    result_path.write_bytes(raw)
    evidence.append(ArchiveRunEvidence(run, str(request_path), str(result_path)))
    sources += (FigureSourcePath(sample.recognition.source_sha256, str(composite)),)
    plan = make_normalization_plan(project, "row0", "row1", "housekeeping")
    plan = plan.model_copy(
        update={
            "confirmed": True,
            "control_mode": "single_control",
            "pairs": (
                SamplePair(
                    target_lane=1, reference_lane=1, sample='=control,"\nvalue', control=True
                ),
                SamplePair(target_lane=2, included=False),
                SamplePair(target_lane=3, reference_lane=2, sample="zero"),
            ),
        }
    )
    normalized = project_with_normalizations(project, (plan,))
    return normalized, sources, tuple(evidence), results, loaded_ocr


def test_unified_archive_keeps_pixels_results_and_every_member_digest(tmp_path: Path) -> None:
    project, sources, evidence, results, ocr = bundle(tmp_path)
    target = tmp_path / "complete.zip"
    export_figure_bundle(project, sources, str(target), runs=evidence)
    with ZipFile(target) as archive:
        index = json.loads(archive.read("archive.json"))
        assert index["schema_version"] == 2 and index["revision"] == project.revision
        assert all(r["verification"] == "verified_result" for r in index["runs"])
        assert set(archive.namelist()) == {m["path"] for m in index["members"]} | {"archive.json"}
        for member in index["members"]:
            data = archive.read(member["path"])
            assert (
                len(data) == member["size_bytes"] and sha256(data).hexdigest() == member["sha256"]
            )
        for source in sources:
            assert archive.read("assets/" + source.sha256) == Path(source.path).read_bytes()
        with tifffile.TiffFile(sources[0].path) as tiff:
            original = tiff.asarray()
        with tifffile.TiffFile(BytesIO(archive.read("crops/0001.tif"))) as tiff:
            crop = tiff.asarray()
        assert crop.dtype == original.dtype and (crop == original[5:15, :]).all()
        for n, entry in enumerate(evidence, 1):
            assert archive.read(f"runs/{n:04d}/result.json") == Path(entry.result_path).read_bytes()
            assert (
                archive.read(f"runs/{n:04d}/request.json") == Path(entry.request_path).read_bytes()
            )
        values = csv_rows(archive.read("tables/source.csv"))
        assert [r["积分"] for r in values] == ["4000.0", "", "0.0", "8000.0", "16000.0", "0.0"]
        assert values[1]["状态"] == "excluded"
        assert [r["积分"] for r in csv_rows(archive.read("tables/ocr.csv"))] == [
            r["积分"] for r in values
        ]
        normalized = csv_rows(archive.read("tables/normalization.csv"))
        assert [r["目标/参照"] for r in normalized] == ["0.5", "", "0.0"]
        assert [r["相对值"] for r in normalized] == ["1.0", "", "0.0"]
        assert normalized[0]["样本"] == '=control,"\nvalue'
        exporters: tuple[tuple[str, Callable[[str], str]], ...] = (
            ("source", lambda p: export_project_table(project, results, p)),
            ("ocr", lambda p: export_project_ocr_table(project, results, ocr, p)),
            ("normalization", lambda p: export_project_normalization(project, results, ocr, p)),
        )
        for name, exporter in exporters:
            for extension in ("csv", "xlsx"):
                standalone = tmp_path / f"{name}.{extension}"
                exporter(str(standalone))
                if extension == "csv":
                    assert standalone.read_bytes() == archive.read(f"tables/{name}.csv")
                else:
                    with (
                        ZipFile(standalone) as left,
                        ZipFile(BytesIO(archive.read(f"tables/{name}.xlsx"))) as right,
                    ):
                        for sheet in (1, 2):
                            key = f"xl/worksheets/sheet{sheet}.xml"
                            assert left.read(key) == right.read(key)
                            assert not ET.fromstring(left.read(key)).findall(".//{*}f")


@pytest.mark.parametrize("fault", ["result", "request", "absent", "record", "ocr"])
def test_bad_run_evidence_never_fills_values_and_preserves_other_rows(
    tmp_path: Path, fault: str
) -> None:
    project, sources, runs, _, _ = bundle(tmp_path)
    if fault in ("result", "request", "ocr"):
        path = runs[-1].result_path if fault == "ocr" else getattr(runs[0], fault + "_path")
        Path(path).write_bytes(b"damaged")
    elif fault == "absent":
        runs = runs[1:]
    else:
        runs = (replace(runs[0], run=runs[0].run.model_copy(update={"pid": 999})), *runs[1:])
    target = tmp_path / "partial.zip"
    export_figure_bundle(project, sources, str(target), runs=runs)
    with ZipFile(target) as archive:
        index = json.loads(archive.read("archive.json"))
        bad = 2 if fault == "ocr" else 0
        assert index["runs"][bad]["verification"] == "unavailable"
        assert index["runs"][bad]["reason"] and index["runs"][bad]["result"] is None
        values = csv_rows(archive.read("tables/ocr.csv" if fault == "ocr" else "tables/source.csv"))
        assert all(r["积分"] == "" for r in values[:3])
        if fault != "ocr":
            assert [r["积分"] for r in values[3:]] == ["8000.0", "16000.0", "0.0"]
            assert all(
                r["目标/参照"] == "" for r in csv_rows(archive.read("tables/normalization.csv"))
            )


def test_stale_annotations_and_unprovided_evidence_remain_explicit(tmp_path: Path) -> None:
    project, _, runs, _, _ = bundle(tmp_path)
    first = project.rows[0].model_copy(update={"empty_lanes": ()})
    project = project.model_copy(update={"rows": (first, *project.rows[1:])})
    verified = verify_project_evidence(project, runs)
    target = tmp_path / "stale.csv"
    export_project_table(project, verified.results, str(target))
    rows = csv_rows(target.read_bytes())
    assert all(r["状态"] == "stale" and not r["积分"] for r in rows[:3])
    assert verify_project_evidence(project, ()).results == ()


@pytest.mark.parametrize(
    "label",
    [
        "=1+2",
        "+cmd",
        "-cmd",
        "@SUM(1)",
        "\t=1",
        "\r\n=1",
        "＝1",
        "text:value",
        '"a,b"\nβ',
        "00123",
        "",
    ],
)
def test_csv_text_is_reversible_and_numbers_are_numeric(label: str) -> None:
    data = csv_bytes((("label", "signal", "missing"), (label, 0.0, None)))
    assert data.startswith(b"\xef\xbb\xbf")
    raw = list(csv.reader(StringIO(data.decode("utf-8-sig")), quoting=csv.QUOTE_NONNUMERIC))
    assert raw[1] == ["text:" + label, 0.0, ""]
    assert csv_rows(data)[0] == {"label": label, "signal": "0.0", "missing": ""}


def test_cancel_at_publish_and_existing_output_leave_no_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from wb_tool.adapters import figure_export

    project, sources, runs, _, _ = bundle(tmp_path)
    target = tmp_path / "cancelled.zip"

    # Trigger cancellation after the index is built: all data members were already written.
    built = False
    from wb_tool.adapters.project_archive import archive_index_bytes as original

    def index_bytes(index: dict[str, object]) -> bytes:
        nonlocal built
        built = True
        return original(index)

    monkeypatch.setattr(figure_export, "archive_index_bytes", index_bytes)

    def cancelled() -> bool:
        return built

    with pytest.raises(ValueError, match="取消"):
        export_figure_bundle(project, sources, str(target), runs=runs, cancelled=cancelled)
    assert not target.exists() and not list(tmp_path.glob(".wb-figure-*.tmp"))
    target.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        export_figure_bundle(project, sources, str(target), runs=runs)
    assert target.read_bytes() == b"keep"


def test_csv_budget_invalid_numbers_cancel_and_no_overwrite(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="预算"):
        csv_bytes((("a",),) + ((1,),) * 200000)
    for value in (float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="数值"):
            csv_bytes((("a",), (value,)))
    project, _, _, results, _ = bundle(tmp_path)
    path = tmp_path / "cancel.csv"
    with pytest.raises(ValueError, match="取消"):
        export_project_table(project, results, str(path), cancelled=lambda: True)
    assert not path.exists() and not list(tmp_path.glob(".wb-export-*"))
    path.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        export_project_table(project, results, str(path))
    assert path.read_bytes() == b"keep"


def test_archive_member_budget_and_duplicate_are_enforced() -> None:
    from wb_tool.adapters.archive_io import ArchiveWriter

    with ZipFile(BytesIO(), "w") as archive:
        writer = ArchiveWriter(archive, lambda: False)
        writer.data("one", b"data", "test")
        with pytest.raises(ValueError, match="重复"):
            writer.data("one", b"data", "test")
        writer.total = 2 * 1024**3
        with pytest.raises(ValueError, match="预算"):
            writer.data("over-budget", b"x", "test")


def test_archive_index_is_also_subject_to_total_size_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from wb_tool.adapters.archive_io import ArchiveWriter

    project, sources, runs, _, _ = bundle(tmp_path)
    original = ArchiveWriter.data

    def near_capacity(writer: ArchiveWriter, name: str, data: bytes, role: str) -> None:
        if name == "archive.json":
            writer.total = 2 * 1024**3
        original(writer, name, data, role)

    monkeypatch.setattr(ArchiveWriter, "data", near_capacity)
    target = tmp_path / "large.zip"
    with pytest.raises(ValueError, match="预算"):
        export_figure_bundle(project, sources, str(target), runs=runs)
    assert not target.exists() and not list(tmp_path.glob(".wb-figure-*.tmp"))


@pytest.mark.parametrize("state", ["failed", "cancelled", "interrupted"])
def test_unsuccessful_runs_keep_terminal_state_without_valid_values(
    tmp_path: Path, state: str
) -> None:
    from wb_tool.api import project_with_analyses

    project, _, runs, _, _ = bundle(tmp_path)
    plan = project.analyses[0]
    assert plan.run
    run = plan.run.model_copy(update={"state": state, "result": None, "reason": "test terminal"})
    project = project_with_analyses(
        project, (plan.model_copy(update={"run": run}), *project.analyses[1:])
    )
    verified = verify_project_evidence(project, (replace(runs[0], run=run), *runs[1:]))
    assert verified.records[0]["verification"] == "terminal_without_result"
    target = tmp_path / "terminal.csv"
    export_project_table(project, verified.results, str(target))
    assert all(r["状态"] == state and not r["积分"] for r in csv_rows(target.read_bytes())[:3])
