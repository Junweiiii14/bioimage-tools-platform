"""Tables and verifiable run evidence in the original-pixel figure archive."""

import json

from wb_tool.adapters.archive_io import ArchiveWriter
from wb_tool.adapters.csv_export import CSV_ENCODING
from wb_tool.adapters.normalization_export import normalization_csv_bytes, normalization_table_rows
from wb_tool.adapters.project_evidence import verify_project_evidence
from wb_tool.adapters.project_export import project_csv_bytes, project_xlsx_bytes
from wb_tool.adapters.project_ocr_export import project_ocr_csv_bytes, project_ocr_table_rows
from wb_tool.adapters.worksheet_export import two_sheet_xlsx_bytes
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_archive import ArchiveRunEvidence
from wb_tool.application.project_normalization import WBNormalizedProject
from wb_tool.application.project_ocr import WBProjectOCR


def write_project_results(
    project: WBFigureProject, evidence: tuple[ArchiveRunEvidence, ...], writer: ArchiveWriter
) -> dict[str, object]:
    verified = verify_project_evidence(
        project, evidence, cancelled=writer.cancelled, write=writer.data
    )
    results, ocr = verified.results, verified.ocr
    writer.data("tables/source.csv", project_csv_bytes(project, results), "source_result_csv")
    writer.data("tables/source.xlsx", project_xlsx_bytes(project, results), "source_result_xlsx")
    if isinstance(project, WBProjectOCR) and project.ocr:
        writer.data(
            "tables/ocr.csv", project_ocr_csv_bytes(project, results, ocr), "ocr_result_csv"
        )
        writer.data(
            "tables/ocr.xlsx",
            two_sheet_xlsx_bytes(*project_ocr_table_rows(project, results, ocr)),
            "ocr_result_xlsx",
        )
    if isinstance(project, WBNormalizedProject):
        for labels in (False, True) if project.ocr else (False,):
            name = "normalization_ocr" if labels else "normalization"
            writer.data(
                f"tables/{name}.csv",
                normalization_csv_bytes(project, results, ocr, ocr_labels=labels),
                "normalization_csv",
            )
            writer.data(
                f"tables/{name}.xlsx",
                two_sheet_xlsx_bytes(
                    *normalization_table_rows(project, results, ocr, ocr_labels=labels)
                ),
                "normalization_xlsx",
            )
    writer.data(
        "README.txt",
        (
            b"WB project archive v2\n"
            b"project.json: revision, labels, ROI, annotations, OCR links and normalization.\n"
            b"figure.png is display-only; crops/ and assets/ retain original samples.\n"
            b"CSV: UTF-8 BOM, comma and CRLF. Every text DATA cell starts with text:.\n"
            b"Remove one text: to recover text. Numbers have no prefix; blank means missing.\n"
            b"XLSX has literal text and numbers. Status/reason columns explain empty values.\n"
            b"runs/: verified original request/result bytes and declared historical run records.\n"
            b"archive.json: sizes/SHA256/roles/verification; missing evidence gives no values.\n"
            b"Hashes detect corruption, not authenticity. Records do not authorize local success.\n"
            b"No OCR model binaries are included; recognition records contain model identities.\n"
            b"The index excludes itself because a file cannot contain its own SHA256.\n"
        ),
        "archive_instructions",
    )
    return {
        "format": "wb_project_archive",
        "schema_version": 2,
        "project_id": project.project_id,
        "revision": project.revision,
        "csv_encoding": CSV_ENCODING,
        "runs": verified.records,
        "ocr": "present" if isinstance(project, WBProjectOCR) and project.ocr else "not_configured",
        "normalization": "configured"
        if isinstance(project, WBNormalizedProject) and project.normalizations
        else "not_configured",
        "trust": "portable_evidence_not_local_execution_receipt",
        "members": writer.members,
    }


def archive_index_bytes(index: dict[str, object]) -> bytes:
    return json.dumps(index, ensure_ascii=True, indent=2, allow_nan=False).encode()
