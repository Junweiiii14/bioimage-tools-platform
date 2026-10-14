"""The actual WB worker runs from a stored input and cannot overwrite a newer draft."""

import json
import sys
from pathlib import Path

import numpy as np
import tifffile
from bioimage_app.api import (
    AsyncStorage,
    RunCompletion,
    RunSession,
    StorageCommand,
    StorageReply,
    create_wb_codec,
)
from platform_runtime.api import Workspace
from pytestqt.qtbot import QtBot
from tool_contracts.api import AssetRef, RunRecord
from wb_tool.api import (
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    LaneAnnotation,
    LaneROI,
    StartFrame,
    encode_worker_frame,
    load_tiff,
    parse_worker_frame,
)


def test_actual_wb_host_commit_reopen(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "original.tif"
    tifffile.imwrite(source, np.array([[245], [235], [245]], dtype=np.uint8))
    image = load_tiff(source)
    storage = AsyncStorage()
    replies: list[StorageReply] = []
    completions: list[RunCompletion] = []
    storage.replied.connect(replies.append)

    def call(command: StorageCommand) -> StorageReply:
        request_id = storage.submit(command)
        qtbot.waitUntil(
            lambda: any(reply.request_id == request_id for reply in replies), timeout=10000
        )
        reply = next(reply for reply in replies if reply.request_id == request_id)
        assert reply.error_code is None, reply
        return reply

    try:
        call(StorageCommand("create", path=str(tmp_path / "workspace")))
        imported = call(StorageCommand("import", path=str(source), source_sha256=image.sha256))
        assert isinstance(imported.value, AssetRef)
        asset_path = call(StorageCommand("asset", asset=imported.value))
        assert isinstance(asset_path.value, str)
        request = AnalysisRequest(
            image.sha256,
            0,
            "dark",
            (LaneAnnotation(LaneROI("L", 0, 0, 1, 3), (BandAnnotation("B", BandBounds(0, 2)),)),),
        )
        draft = StartFrame(
            protocol_version=1,
            kind="start",
            sequence=0,
            run_id="draft",
            attempt_id="draft",
            request_id="draft",
            source_path=asset_path.value,
            request=request,
        )
        call(
            StorageCommand(
                "save",
                document_id="D",
                tool_id="wb",
                revision=0,
                data=encode_worker_frame(draft).strip(),
            )
        )
        prepared = call(StorageCommand("prepare", document_id="D"))
        assert isinstance(prepared.value, RunRecord)
        run = prepared.value
        frozen = parse_worker_frame(prepared.data)
        assert isinstance(frozen, StartFrame)
        start = frozen.model_copy(
            update={"run_id": run.run_id, "attempt_id": "A", "request_id": "Q"}
        )
        source.write_bytes(b"externally changed original after immutable import")
        session = RunSession(storage, run, create_wb_codec(start))
        session.completed.connect(completions.append)
        session.start(
            (sys.executable, "-I", "-m", "wb_tool.worker"),
            str(tmp_path),
            encode_worker_frame(start),
        )
        call(
            StorageCommand(
                "save",
                document_id="D",
                tool_id="wb",
                revision=1,
                previous_revision=0,
                data=b'{"new":true}',
            )
        )
        qtbot.waitUntil(lambda: bool(completions), timeout=15000)
        assert completions[0].error == ""
        assert completions[0].record is not None and completions[0].record.state == "succeeded"
    finally:
        with qtbot.waitSignal(storage.closed, timeout=10000):
            storage.shutdown()
    with Workspace.open(tmp_path / "workspace") as store:
        completed = store.get_run(run.run_id)
        assert completed.result is not None
        document = json.loads(store.read_asset(completed.result))
        assert document["request"]["revision"] == 0
        assert document["lanes"][0]["bands"][0]["measurement"]["signal"] == 10
        assert store.load_draft("D").revision == 1
