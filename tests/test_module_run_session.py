"""Real worker, observed exit, immutable output admission, and reopened Workspace."""

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.api import (
    AsyncStorage,
    ProcessEvent,
    RunCompletion,
    RunSession,
    StorageCommand,
    StorageReply,
    create_wb_module_codec,
)
from platform_runtime.api import Workspace
from pytestqt.qtbot import QtBot
from tool_contracts.api import AssetRef, OutputManifest, RunRecord
from wb_tool.api import (
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    LaneAnnotation,
    LaneROI,
    WBModuleStart,
    encode_module_frame,
    module_identity,
    prepare_wb_execution,
)


@pytest.mark.parametrize(
    "mode",
    [
        "success",
        "nonzero_after_manifest",
        "missing_output",
        "changed_output",
        "cancel",
        "missing_binding",
        "hard_link",
    ],
)
def test_module_run_commits_only_verified_real_success(
    qtbot: QtBot, tmp_path: Path, mode: str
) -> None:
    source = tmp_path / "original.tif"
    tifffile.imwrite(
        source,
        np.repeat(np.array([1000, 2000, 3000, 2000, 1000], dtype=np.uint16)[:, None], 3, axis=1),
        metadata=None,
    )
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    workspace = tmp_path / "workspace"
    output = tmp_path / "v0-compare"
    storage = AsyncStorage()
    replies: list[StorageReply] = []
    completions: list[RunCompletion] = []
    storage.replied.connect(replies.append)

    def call(command: StorageCommand) -> StorageReply:
        request_id = storage.submit(command)
        qtbot.waitUntil(lambda: any(r.request_id == request_id for r in replies), timeout=10000)
        reply = next(r for r in replies if r.request_id == request_id)
        assert reply.error_code is None, reply
        return reply

    try:
        call(StorageCommand("create", path=str(workspace)))
        imported = call(StorageCommand("import", path=str(source), source_sha256=digest)).value
        assert isinstance(imported, AssetRef)
        planned = AnalysisRequest(
            digest,
            0,
            "light",
            (
                LaneAnnotation(
                    LaneROI("sample", 0, 0, 3, 5), (BandAnnotation("band", BandBounds(0, 4)),)
                ),
            ),
        )
        request = prepare_wb_execution(imported, planned, "comparison")
        call(
            StorageCommand(
                "save",
                document_id=request.document_id,
                tool_id="wb-v0-compare",
                revision=0,
                data=request.model_dump_json().encode(),
            )
        )
        prepared = call(StorageCommand("prepare", document_id=request.document_id)).value
        assert isinstance(prepared, RunRecord)
        source_path = call(StorageCommand("asset", asset=imported)).value
        assert isinstance(source_path, str)
        start = WBModuleStart(
            identity=module_identity(prepared.run_id, request),
            request=request,
            source_path=source_path,
            output_directory=str(output),
        )
        session = RunSession(
            storage,
            prepared,
            create_wb_module_codec(start),
            module_request=None if mode == "missing_binding" else request,
            module_output_directory="" if mode == "missing_binding" else str(output),
        )
        session.completed.connect(completions.append)
        if mode == "cancel":

            def cancel(event: ProcessEvent) -> None:
                if event.kind == "accepted":
                    session.cancel()

            session.received.connect(cancel)
        tail = {
            "success": "sys.exit(code)",
            "missing_binding": "sys.exit(code)",
            "hard_link": (
                "p=Path(sys.argv[1]) / 'measurements.csv'; "
                "alias=p.parent.parent / 'outside.csv'; p.rename(alias); "
                "p.hardlink_to(alias); sys.exit(code)"
            ),
            "cancel": "sys.exit(code)",
            "nonzero_after_manifest": "sys.exit(7)",
            "missing_output": "(Path(sys.argv[1]) / 'measurements.csv').unlink(); sys.exit(code)",
            "changed_output": (
                "p=Path(sys.argv[1]) / 'measurements.csv'; "
                "p.write_bytes(b'X' * p.stat().st_size); sys.exit(code)"
            ),
        }[mode]
        script = (
            "import sys; from pathlib import Path; from wb_tool.api import run_wb_module_worker; "
            "code=run_wb_module_worker(); " + tail
        )
        session.start(
            (sys.executable, "-c", script, str(output)), str(tmp_path), encode_module_frame(start)
        )
        qtbot.waitUntil(lambda: bool(completions), timeout=30000)
        completion = completions[0]
        assert completion.error == "" and completion.record is not None
        assert completion.outcome.pid > 0
        expected = (
            "succeeded" if mode == "success" else "cancelled" if mode == "cancel" else "failed"
        )
        assert completion.record.state == expected
        if mode == "nonzero_after_manifest":
            assert completion.outcome.exit_code == 7
            assert (
                completion.outcome.terminal is not None
                and completion.outcome.terminal.kind == "result"
            )
        if mode != "success":
            assert completion.record.result is None
        if mode == "missing_binding":
            assert completion.record.reason == "module_publication_binding_missing"
        if mode in ("missing_output", "changed_output", "hard_link"):
            assert completion.record.reason and "module_output_invalid" in completion.record.reason
    finally:
        with qtbot.waitSignal(storage.closed, timeout=10000):
            storage.shutdown()
    with Workspace.open(workspace) as reopened:
        run = reopened.get_run(prepared.run_id)
        assert run == completion.record
        if mode == "success":
            assert run.result is not None
            manifest = OutputManifest.model_validate_json(reopened.read_asset(run.result))
            assert manifest.publication == "committed" and manifest.request == request
            outputs = {item.port: item.asset for item in manifest.outputs}
            table = list(
                csv.DictReader(
                    io.StringIO(reopened.read_asset(outputs["measurements"]).decode("utf-8-sig"))
                )
            )
            differences = list(
                csv.DictReader(
                    io.StringIO(reopened.read_asset(outputs["differences"]).decode("utf-8-sig"))
                )
            )
            assert len(table) == len(differences) == 1
            assert table[0]["value"] == "4000.0"
            assert differences[0]["difference"] == "0.0"
            provenance = json.loads(reopened.read_asset(outputs["provenance"]))
            assert provenance["run_id"] == run.run_id
            assert provenance["request"]["inputs"][0]["asset"]["sha256"] == digest
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
