"""The module adapter preserves analytical answers and strict original-input semantics."""

import csv
import hashlib
import io
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import tifffile
from pydantic import ValidationError
from tool_contracts.api import (
    AssetRef,
    BoundAsset,
    ExecutionEvent,
    ExecutionIdentity,
    ExecutionRequest,
    OutputManifest,
    canonical_module_json,
)
from wb_tool.api import (
    AnalysisCancelled,
    AnalysisError,
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    ImageInputError,
    LaneAnnotation,
    LaneROI,
    WBModuleConversation,
    WBModuleStart,
    analyze_annotations,
    compare_wb_module,
    encode_module_frame,
    execute_wb_module,
    load_tiff,
    module_identity,
    prepare_wb_execution,
)


def frozen_request(tmp_path: Path, *, sixteen: bool = False) -> tuple[Path, ExecutionRequest]:
    path = tmp_path / "original.tif"
    profile = np.array([10, 20, 30, 20, 10], dtype=np.uint16 if sixteen else np.uint8)
    if sixteen:
        profile *= 100
    tifffile.imwrite(path, np.repeat(profile[:, None], 3, axis=1), metadata=None)
    image = load_tiff(path)
    asset = AssetRef(
        asset_id="original",
        relative_path="inputs/original.tif",
        sha256=image.sha256,
        size_bytes=path.stat().st_size,
    )
    planned = AnalysisRequest(
        image.sha256,
        7,
        "light",
        (
            LaneAnnotation(
                LaneROI("sample-1", 0, 0, 3, 5), (BandAnnotation("B", BandBounds(0, 4)),)
            ),
        ),
    )
    return path, prepare_wb_execution(asset, planned, "frozen-document")


@pytest.mark.parametrize("sixteen, expected", [(False, 40.0), (True, 4000.0)])
def test_real_module_preserves_analytical_area_and_input(
    tmp_path: Path, sixteen: bool, expected: float
) -> None:
    path, request = frozen_request(tmp_path, sixteen=sixteen)
    original = path.read_bytes()
    reopened = ExecutionRequest.model_validate_json(request.model_dump_json())
    result = execute_wb_module(load_tiff(path), reopened)
    band = result.lanes[0].bands[0]
    assert (band.status, band.signal) == ("valid", expected)
    assert result == analyze_annotations(load_tiff(path), result.request)
    assert result.algorithm_id == "profile_integral@1"
    assert result.request.revision == 7
    assert path.read_bytes() == original
    assert request.inputs[0].asset.sha256 == hashlib.sha256(original).hexdigest()


def test_module_rejects_changed_digest_role_revision_and_strategy(tmp_path: Path) -> None:
    path, request = frozen_request(tmp_path)
    image = load_tiff(path)
    bad_digest = request.model_copy(update={"parameters_sha256": "0" * 64})
    with pytest.raises(ValidationError, match="digest"):
        execute_wb_module(image, bad_digest)
    display = request.inputs[0].model_copy(update={"kind": "display_image"})
    with pytest.raises(ValidationError, match="roles"):
        execute_wb_module(image, request.model_copy(update={"inputs": (display,)}))
    with pytest.raises(AnalysisError, match="修订"):
        execute_wb_module(image, request.model_copy(update={"revision": 8}))
    planned = analyze_annotations(image, execute_wb_module(image, request).request).request
    with pytest.raises(AnalysisError, match="旧方法"):
        prepare_wb_execution(
            request.inputs[0].asset,
            replace(planned, geometry_policy="independent_lanes@1"),
            request.document_id,
        )
    changed = request.module.model_copy(update={"implementation_digest": "0" * 64})
    with pytest.raises(AnalysisError, match="实现"):
        execute_wb_module(image, request.model_copy(update={"module": changed}))


def test_module_keeps_invalid_null_separate_from_valid_zero(tmp_path: Path) -> None:
    path, request = frozen_request(tmp_path)
    image = load_tiff(path)
    planned = execute_wb_module(image, request).request
    bad = replace(
        planned,
        lanes=(LaneAnnotation(LaneROI("outside", 0, 0, 4, 5), planned.lanes[0].bands),),
    )
    result = execute_wb_module(
        image, prepare_wb_execution(request.inputs[0].asset, bad, request.document_id)
    )
    assert result.lanes[0].bands[0].status == "invalid"
    assert result.lanes[0].bands[0].signal is None
    assert result.lanes[0].reason
    with pytest.raises(AnalysisCancelled):
        execute_wb_module(image, request, cancelled=lambda: True)


def test_original_loader_still_rejects_float_input(tmp_path: Path) -> None:
    path = tmp_path / "float.tif"
    tifffile.imwrite(path, np.ones((5, 3), dtype=np.float64))
    with pytest.raises(ImageInputError):
        load_tiff(path)


@pytest.mark.parametrize(
    "payload", ['{"x":1,"x":2}', '{"nested":{"x":1,"x":2}}', '{"x":NaN}', '{"x":1e999}', "[]"]
)
def test_module_json_rejects_ambiguous_or_nonfinite_payload(payload: str) -> None:
    with pytest.raises(ValueError):
        canonical_module_json(payload)


def test_manifest_cannot_omit_output_or_claim_published_worker_success(tmp_path: Path) -> None:
    _, request = frozen_request(tmp_path)
    outputs = tuple(
        BoundAsset(
            port=port.name,
            kind=port.kind,
            asset=AssetRef(
                asset_id=port.name,
                relative_path=port.filename,
                sha256="1" * 64,
                size_bytes=1,
            ),
        )
        for port in request.module.output_ports
    )
    manifest = OutputManifest(
        run_id="process-1",
        request=request,
        publication="candidate",
        outputs=outputs,
        quality="complete",
        summary_json="{}",
    )
    value = json.loads(manifest.model_dump_json())
    value["outputs"].pop()
    with pytest.raises(ValidationError, match="required output"):
        OutputManifest.model_validate_json(json.dumps(value))
    identity = ExecutionIdentity(
        run_id=manifest.run_id,
        request_id=request.request_id,
        execution_id=request.execution_id,
        node_id=request.node_id,
        attempt_id=request.attempt_id,
        document_id=request.document_id,
        revision=request.revision,
    )
    event = ExecutionEvent(kind="result", sequence=2, identity=identity, manifest=manifest)
    assert ExecutionEvent.model_validate_json(event.model_dump_json()) == event
    with pytest.raises(ValidationError, match="uncommitted"):
        ExecutionEvent(
            kind="result",
            sequence=2,
            identity=identity,
            manifest=manifest.model_copy(update={"publication": "committed"}),
        )
    with pytest.raises(ValidationError):
        ExecutionEvent.model_validate_json('{"protocol_version":true,"kind":"hello","sequence":0}')


def module_start(path: Path, request: ExecutionRequest, output: Path) -> WBModuleStart:
    return WBModuleStart(
        identity=module_identity("real-run", request),
        request=request,
        source_path=str(path.resolve()),
        output_directory=str(output.resolve()),
    )


@pytest.mark.parametrize("sixteen, expected", [(False, "40.0"), (True, "4000.0")])
def test_real_comparison_worker_generates_attributed_outputs(
    tmp_path: Path, sixteen: bool, expected: str
) -> None:
    path, request = frozen_request(tmp_path, sixteen=sixteen)
    original = path.read_bytes()
    start = module_start(path, request, tmp_path / "v0-compare")
    child = subprocess.Popen(
        [sys.executable, "-m", "wb_tool.module_worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = child.communicate(encode_module_frame(start), timeout=30)
    assert child.pid > 0 and child.returncode == 0, stderr.decode()
    conversation = WBModuleConversation(start)
    events = [conversation.accept(line) for line in stdout.splitlines()]
    assert [event.kind for event in events] == ["hello", "accepted", "result"]
    manifest = events[-1].manifest
    assert manifest is not None and manifest.publication == "candidate"
    assert manifest.quality == "complete"
    assert manifest.request == request
    for output in manifest.outputs:
        data = (tmp_path / "v0-compare" / output.asset.relative_path).read_bytes()
        assert len(data) == output.asset.size_bytes
        assert hashlib.sha256(data).hexdigest() == output.asset.sha256
    table = list(
        csv.DictReader(
            io.StringIO((tmp_path / "v0-compare/measurements.csv").read_text(encoding="utf-8-sig"))
        )
    )
    diff = list(
        csv.DictReader(
            io.StringIO((tmp_path / "v0-compare/differences.csv").read_text(encoding="utf-8-sig"))
        )
    )
    assert len(table) == len(diff) == 1
    assert table[0]["value"] == expected
    assert table[0]["status"] == "text:valid"
    assert table[0]["source_sha256"] == "text:" + request.inputs[0].asset.sha256
    assert diff[0]["baseline_value"] == diff[0]["module_value"] == expected
    assert diff[0]["difference"] == "0.0" and diff[0]["exact_match"] == "True"
    provenance = json.loads((tmp_path / "v0-compare/run-manifest.json").read_text(encoding="utf-8"))
    assert provenance["run_id"] == start.identity.run_id
    assert provenance["request"]["parameters_sha256"] == request.parameters_sha256
    assert provenance["summary"]["rows"] == 1
    assert path.read_bytes() == original


def test_comparison_preserves_invalid_null_and_never_overwrites(tmp_path: Path) -> None:
    path, request = frozen_request(tmp_path)
    planned = execute_wb_module(load_tiff(path), request).request
    bad = replace(
        planned, lanes=(LaneAnnotation(LaneROI("bad", 0, 0, 4, 5), planned.lanes[0].bands),)
    )
    request = prepare_wb_execution(request.inputs[0].asset, bad, request.document_id)
    start = module_start(path, request, tmp_path / "v0-compare")
    manifest = compare_wb_module(start)
    assert manifest.quality == "issues"
    table = list(
        csv.DictReader(
            (tmp_path / "v0-compare/measurements.csv").read_text(encoding="utf-8-sig").splitlines()
        )
    )
    diff = list(
        csv.DictReader(
            (tmp_path / "v0-compare/differences.csv").read_text(encoding="utf-8-sig").splitlines()
        )
    )
    assert table[0]["value"] == "" and table[0]["status"] == "text:invalid"
    assert table[0]["reason"] != "text:"
    assert diff[0]["difference"] == "" and diff[0]["numerically_comparable"] == "False"
    preserved = {p.name: p.read_bytes() for p in (tmp_path / "v0-compare").iterdir()}
    with pytest.raises(FileExistsError):
        compare_wb_module(start)
    assert preserved == {p.name: p.read_bytes() for p in (tmp_path / "v0-compare").iterdir()}
    with pytest.raises(AnalysisCancelled):
        compare_wb_module(
            start.model_copy(update={"output_directory": str(tmp_path / "cancelled")}),
            cancelled=lambda: True,
        )
    assert not (tmp_path / "cancelled").exists()


def test_comparison_worker_rejects_changed_original(tmp_path: Path) -> None:
    path, request = frozen_request(tmp_path)
    path.write_bytes(path.read_bytes() + b"changed")
    start = module_start(path, request, tmp_path / "v0-compare")
    child = subprocess.run(
        [sys.executable, "-m", "wb_tool.module_worker"],
        input=encode_module_frame(start),
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert child.returncode != 0
    conversation = WBModuleConversation(start)
    events = [conversation.accept(line) for line in child.stdout.splitlines()]
    assert [event.kind for event in events] == ["hello", "accepted", "failure"]
    assert events[-1].manifest is None and events[-1].reason
    assert not (tmp_path / "v0-compare").exists()


def test_module_conversation_rejects_wrong_order_identity_and_extra_events(tmp_path: Path) -> None:
    path, request = frozen_request(tmp_path)
    start = module_start(path, request, tmp_path / "v0-compare")
    conversation = WBModuleConversation(start)
    accepted = ExecutionEvent(kind="accepted", sequence=1, identity=start.identity)
    with pytest.raises(ValueError, match="order"):
        conversation.accept(encode_module_frame(accepted))
    conversation.accept(encode_module_frame(ExecutionEvent(kind="hello", sequence=0)))
    other = accepted.model_copy(
        update={"identity": start.identity.model_copy(update={"attempt_id": "other"})}
    )
    with pytest.raises(ValueError, match="another attempt"):
        conversation.accept(encode_module_frame(other))
    conversation.accept(encode_module_frame(accepted))
    assert conversation.cancellation().identity == start.identity
    with pytest.raises(ValueError, match="active attempt"):
        conversation.cancellation()
    done = ExecutionEvent(kind="cancelled", sequence=2, identity=start.identity)
    conversation.accept(encode_module_frame(done))
    with pytest.raises(ValueError, match="order"):
        conversation.accept(encode_module_frame(done))
    with pytest.raises(ValueError, match="nesting"):
        canonical_module_json('{"x":' + "[" * 2000 + "0" + "]" * 2000 + "}")
