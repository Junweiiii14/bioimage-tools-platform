"""OCR-only drafts and real process terminal identity/cancellation, without Qt."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import tifffile
from PIL import Image, ImageDraw, ImageFont
from tool_contracts.api import AssetRef
from wb_tool.api import (
    AcceptedFrame,
    AnalysisRequest,
    CancelledFrame,
    HelloFrame,
    LaneAnnotation,
    LaneROI,
    OCRConversation,
    OCRRequest,
    OCRResultFrame,
    OCRStartFrame,
    WBDocument,
    WBWorksheetDocument,
    encode_ocr_frame,
    load_tiff,
    ocr_protocol_schema,
    parse_ocr_frame,
    read_wb_document,
)


@pytest.fixture
def ocr_start(tmp_path: Path) -> OCRStartFrame:
    image = Image.new("L", (500, 250), 245)
    draw = ImageDraw.Draw(image)
    for text, y in (("1G", 20), ("AKT", 120)):
        draw.text((30, y), text, font=ImageFont.load_default(size=42), fill=0)
    path = tmp_path / "OCR.tif"
    tifffile.imwrite(path, np.array(image))
    return OCRStartFrame(
        protocol_version=1,
        kind="start",
        sequence=0,
        run_id="run",
        attempt_id="attempt",
        request_id="request",
        source_path=str(path),
        request=OCRRequest(source_sha256=load_tiff(path).sha256, revision=3),
    )


def test_actual_ocr_process_identity_stale_and_cancel(ocr_start: OCRStartFrame) -> None:
    command = [sys.executable, "-I", "-m", "bioimage_app", "--worker", "wb_ocr"]
    completed = subprocess.run(
        command, input=encode_ocr_frame(ocr_start), capture_output=True, timeout=30
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    lines = completed.stdout.splitlines()
    conversation = OCRConversation(ocr_start)
    frames = [conversation.accept(line) for line in lines]
    assert isinstance(frames[0], HelloFrame) and isinstance(frames[1], AcceptedFrame)
    result = frames[2]
    assert isinstance(result, OCRResultFrame)
    assert [token.text for token in result.result.tokens] == ["1G", "AKT"]
    assert result.revision == 3
    for corrupted in (
        replace(result.result, model_hashes=()),
        replace(result.result, preprocess_id="unknown"),
    ):
        with pytest.raises(ValueError):
            encode_ocr_frame(result.model_copy(update={"result": corrupted}))
    with pytest.raises(ValueError):
        conversation.accept(lines[-1])
    for altered in (
        result.model_copy(update={"revision": 4}),
        result.model_copy(update={"attempt_id": "another"}),
    ):
        gate = OCRConversation(ocr_start)
        gate.accept(lines[0])
        gate.accept(lines[1])
        with pytest.raises(ValueError):
            gate.accept(encode_ocr_frame(altered))
    gate = OCRConversation(ocr_start)
    gate.accept(lines[0])
    gate.accept(lines[1])
    cancel = gate.cancellation()
    with pytest.raises(ValueError):
        gate.accept(lines[2])
    cancelled = subprocess.run(
        command,
        input=encode_ocr_frame(ocr_start) + encode_ocr_frame(cancel),
        capture_output=True,
        timeout=30,
    )
    assert cancelled.returncode == 0
    assert isinstance(parse_ocr_frame(cancelled.stdout.splitlines()[-1]), CancelledFrame)


def test_ocr_strict_frames_and_schema(ocr_start: OCRStartFrame) -> None:
    raw = encode_ocr_frame(ocr_start)
    for invalid in (
        raw.replace(b'"revision":3', b'"revision":true'),
        raw.replace(b'"sequence":0', b'"sequence":false'),
        raw.replace(b'"kind":"start"', b'"kind":"start","kind":"start"'),
        raw.replace(b'"protocol_version":1', b'"protocol_version":2'),
    ):
        with pytest.raises(ValueError):
            parse_ocr_frame(invalid)
    root = Path(__file__).resolve().parents[3]
    assert (
        json.loads(
            (root / "docs/contracts/wb-ocr-worker-v1.schema.json").read_text(encoding="utf-8")
        )
        == ocr_protocol_schema()
    )


def test_ocr_only_document_and_legacy_compatibility() -> None:
    source = AssetRef(
        asset_id="source", relative_path="assets/source/input.tif", sha256="a" * 64, size_bytes=42
    )
    document = WBWorksheetDocument(source=source, revision=0)
    restored = read_wb_document(document.model_dump_json().encode())
    assert restored == document and restored.request is None
    legacy = WBDocument(
        source=source,
        request=AnalysisRequest(
            source.sha256, 2, "dark", (LaneAnnotation(LaneROI("L", 0, 0, 2, 4), ()),)
        ),
    )
    assert read_wb_document(legacy.model_dump_json().encode()) == legacy
    with pytest.raises(ValueError):
        WBWorksheetDocument(source=source, revision=0, request=legacy.request)
    root = Path(__file__).resolve().parents[3]
    assert (
        json.loads((root / "docs/contracts/wb-document-v2.schema.json").read_text(encoding="utf-8"))
        == WBWorksheetDocument.model_json_schema()
    )
