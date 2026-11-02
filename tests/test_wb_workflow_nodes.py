"""Actual three-node worker chain using shared RunSession and immutable Workspace."""

import csv
import hashlib
import io
import json
import sys
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
from bioimage_app.api import (
    AsyncStorage,
    RunCompletion,
    RunSession,
    StorageCommand,
    StorageReply,
    create_wb_workflow_codec,
)
from bioimage_app.workflow_environment import workflow_runtime_environment
from PIL import Image
from platform_runtime.api import Workspace
from pydantic import TypeAdapter
from pytestqt.qtbot import QtBot
from tool_contracts.api import (
    AssetRef,
    BoundAsset,
    CoordinateFrame,
    ExecutionRequest,
    ImageMetadata,
    OutputManifest,
    RunRecord,
    canonical_module_json,
)
from wb_tool.api import (
    AnalysisRequest,
    AnalysisResult,
    VerifyOriginalParameters,
    WBReportParameters,
    WBWorkflowStart,
    WorkflowInputPath,
    analyze_annotations,
    encode_wb_workflow_frame,
    execute_wb_workflow_node,
    load_tiff,
    module_identity,
    wb_validation_input,
    wb_workflow_environment,
    wb_workflow_spec,
)


@pytest.mark.parametrize(
    "case, expected, status",
    [
        ("triangle_u8", 40.0, "valid"),
        ("triangle_u16", 4000.0, "valid"),
        ("flat_zero", 0.0, "valid"),
        ("invalid_roi", None, "invalid"),
        ("dtype_limits", None, "quality_review"),
    ],
)
def test_actual_original_validation_analysis_publish_nodes(
    qtbot: QtBot,
    tmp_path: Path,
    case: str,
    expected: float | None,
    status: str,
) -> None:
    original = wb_validation_input(case)
    source_file = tmp_path / "original.tif"
    source_file.write_bytes(original.source_bytes)
    source_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
    loaded = load_tiff(source_file)
    description = ImageMetadata(
        dtype="uint16" if loaded.pixels.dtype.itemsize == 2 else "uint8",
        axes=("y", "x"),
        shape=loaded.pixels.shape,
        acquisition_bit_depth=None,
        acquisition_range=None,
        acquisition_range_source=None,
        frame=CoordinateFrame(
            frame_id="original_pixels",
            origin_asset_sha256=source_hash,
            physical_pixel_size_yx=None,
            physical_unit=None,
        ),
    )
    port = AsyncStorage()
    replies: list[StorageReply] = []
    port.replied.connect(replies.append)

    def call(command: StorageCommand) -> StorageReply:
        request_id = port.submit(command)
        qtbot.waitUntil(
            lambda: any(reply.request_id == request_id for reply in replies), timeout=15000
        )
        reply = next(reply for reply in replies if reply.request_id == request_id)
        assert reply.error_code is None, reply
        return reply

    workspace = tmp_path / "workspace"
    manifests: list[OutputManifest] = []
    physical: list[RunRecord] = []
    environment = workflow_runtime_environment(wb_workflow_environment())
    execution = uuid4().hex
    try:
        call(StorageCommand("create", path=str(workspace)))
        ref = call(StorageCommand("import", path=str(source_file), source_sha256=source_hash)).value
        assert isinstance(ref, AssetRef)
        bindings = (BoundAsset(port="source", kind="raw_image", asset=ref),)
        for index, module_id in enumerate(
            ("wb-verify-original", "wb-analyze-original", "wb-publish-original")
        ):
            if index == 0:
                parameters = VerifyOriginalParameters(image=description).model_dump_json()
            elif index == 1:
                parameters = TypeAdapter(AnalysisRequest).dump_json(original.request).decode()
                bindings = (
                    *bindings,
                    BoundAsset(
                        port="validation", kind="run_manifest", asset=manifests[0].outputs[0].asset
                    ),
                )
            else:
                parameters = WBReportParameters(expected_rows=1).model_dump_json()
                bindings = manifests[1].outputs
            parameters = canonical_module_json(parameters)
            req = ExecutionRequest(
                request_id=uuid4().hex,
                execution_id=execution,
                node_id=f"node_{index}",
                attempt_id=uuid4().hex,
                document_id=uuid4().hex,
                revision=0,
                module=wb_workflow_spec(module_id),
                inputs=bindings,
                parameters_json=parameters,
                parameters_sha256=hashlib.sha256(parameters.encode()).hexdigest(),
                environment=environment,
            )
            call(
                StorageCommand(
                    "save",
                    document_id=req.document_id,
                    tool_id=module_id,
                    revision=0,
                    data=req.model_dump_json().encode(),
                )
            )
            prepared = call(StorageCommand("prepare", document_id=req.document_id)).value
            assert isinstance(prepared, RunRecord)
            paths: list[WorkflowInputPath] = []
            for bound in req.inputs:
                actual_path = call(StorageCommand("asset", asset=bound.asset)).value
                assert isinstance(actual_path, str)
                paths.append(WorkflowInputPath(port=bound.port, path=actual_path))
            output = tmp_path / f"staging_{index}"
            start = WBWorkflowStart(
                identity=module_identity(prepared.run_id, req),
                request=req,
                inputs=tuple(paths),
                output_directory=str(output),
            )
            completions: list[RunCompletion] = []
            session = RunSession(
                port,
                prepared,
                create_wb_workflow_codec(start),
                module_request=req,
                module_output_directory=str(output),
            )
            session.completed.connect(completions.append)
            session.start(
                (sys.executable, "-I", "-m", "bioimage_app", "--worker", "wb_workflow"),
                str(tmp_path),
                encode_wb_workflow_frame(start),
            )
            qtbot.waitUntil(lambda completions=completions: bool(completions), timeout=30000)
            completion = completions[0]
            assert completion.error == "" and completion.record is not None, completion
            assert completion.record.state == "succeeded", completion
            assert completion.outcome.pid > 0 and completion.outcome.exit_code == 0
            assert completion.record.pid == completion.outcome.pid
            result = completion.record.result
            assert result is not None
            manifest = OutputManifest.model_validate_json(
                call(StorageCommand("read", asset=result)).data
            )
            manifests.append(manifest)
            physical.append(completion.record)
    finally:
        with qtbot.waitSignal(port.closed, timeout=10000):
            port.shutdown()
    with Workspace.open(workspace) as store:
        assert tuple(store.get_run(run.run_id) for run in physical) == tuple(physical)
        assert len(store.list_runs()) == 3 and len({run.run_id for run in physical}) == 3
        outputs = {item.port: item.asset for item in manifests[-1].outputs}
        rows = list(
            csv.DictReader(
                io.StringIO(store.read_asset(outputs["measurements"]).decode("utf-8-sig"))
            )
        )
        assert rows[0]["status"] == "text:" + status
        assert (float(rows[0]["value"]) if rows[0]["value"] else None) == expected
        curves = json.loads(store.read_asset(outputs["curves"]))
        assert curves["source_sha256"] == source_hash and len(curves["profiles"]) == 1
        assert curves["profiles"][0]["x_origin"] == 0 and curves["profiles"][0]["x_step"] == 1
        assert curves["bit_depth"] == (16 if loaded.pixels.dtype.itemsize == 2 else 8)
        assert curves["profiles"][0]["raw"] == (
            [float(item) for item in loaded.pixels[:, 0]] if status != "invalid" else None
        )
        with Image.open(io.BytesIO(store.read_asset(outputs["report"]))) as report:
            assert report.mode == "L" and report.size == (1200, 168)
            report.load()
        assert hashlib.sha256(source_file.read_bytes()).hexdigest() == source_hash


def test_original_report_rejects_foreign_policy_before_creating_candidate(tmp_path: Path) -> None:
    # A deliberately altered in-memory fixture is not a real committed analysis run.
    original = wb_validation_input("triangle_u16")
    source = tmp_path / "original.tif"
    source.write_bytes(original.source_bytes)
    result = analyze_annotations(load_tiff(source), original.request)
    altered = replace(result, request=replace(result.request, quant_policy="wbquant_1_4_3@1"))
    payload = TypeAdapter(AnalysisResult).dump_json(altered)
    analysis = tmp_path / "foreign-analysis.json"
    analysis.write_bytes(payload)
    asset = AssetRef(
        asset_id="foreign_fixture",
        relative_path="analysis.json",
        sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
    )
    parameters = canonical_module_json(WBReportParameters(expected_rows=1).model_dump_json())
    req = ExecutionRequest(
        request_id="unit_request",
        execution_id="unit_execution",
        node_id="publish",
        attempt_id="unit_attempt",
        document_id="unit_document",
        revision=0,
        module=wb_workflow_spec("wb-publish-original"),
        inputs=(BoundAsset(port="analysis", kind="analysis_result", asset=asset),),
        parameters_json=parameters,
        parameters_sha256=hashlib.sha256(parameters.encode()).hexdigest(),
        environment=workflow_runtime_environment(wb_workflow_environment()),
    )
    output = tmp_path / "unpublished"
    start = WBWorkflowStart(
        identity=module_identity("unit_candidate_only", req),
        request=req,
        inputs=(WorkflowInputPath(port="analysis", path=str(analysis)),),
        output_directory=str(output),
    )
    with pytest.raises(ValueError, match="different analysis policy"):
        execute_wb_workflow_node(start)
    assert not output.exists()
