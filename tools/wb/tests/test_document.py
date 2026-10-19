"""Portable source identity and strict versioned JSON drafts."""

import json
from pathlib import Path

import pytest
from tool_contracts.api import AssetRef
from wb_tool.api import AnalysisRequest, LaneAnnotation, LaneROI, WBDocument


def test_document_roundtrip_and_wrong_source() -> None:
    source = AssetRef(
        asset_id="A", relative_path="assets/A/input.tif", sha256="a" * 64, size_bytes=42
    )
    request = AnalysisRequest("a" * 64, 2, "dark", (LaneAnnotation(LaneROI("L", 0, 0, 2, 4), ()),))
    document = WBDocument(source=source, request=request)
    assert WBDocument.from_bytes(document.model_dump_json().encode()) == document
    with pytest.raises(ValueError):
        WBDocument(source=source.model_copy(update={"sha256": "b" * 64}), request=request)
    data = document.model_dump_json().encode()
    for bad in (
        data.replace(b'"schema_version":1', b'"schema_version":2'),
        data.replace(b'"revision":2', b'"revision":true'),
        data.replace(b'"schema_version":1', b'"schema_version":true'),
        data.replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1'),
    ):
        with pytest.raises(ValueError):
            WBDocument.from_bytes(bad)


def test_document_schema_does_not_drift() -> None:
    root = Path(__file__).resolve().parents[3]
    assert (
        json.loads((root / "docs/contracts/wb-document-v1.schema.json").read_text(encoding="utf-8"))
        == WBDocument.model_json_schema()
    )
