"""Actual Qt host → immutable request → subprocess → host-owned terminal persistence."""

import subprocess
import sys
from pathlib import Path
from threading import Event

import pytest
from bioimage_app.api import (
    AsyncStorage,
    ProcessEvent,
    RunCompletion,
    RunSession,
    StorageCommand,
    StorageReply,
)
from platform_runtime.api import StateConflict, Workspace
from pytestqt.qtbot import QtBot
from tool_contracts.api import ProcessExitReceipt, RunRecord

from tests.test_process_runner import PREAMBLE, ProbeCodec


@pytest.mark.parametrize("mode", ["success", "cancel", "early_cancel", "crash", "start_failure"])
def test_persisted_run_lifecycle(qtbot: QtBot, tmp_path: Path, mode: str) -> None:
    storage = AsyncStorage()
    replies: list[StorageReply] = []
    storage.replied.connect(replies.append)

    def call(command: StorageCommand) -> StorageReply:
        request_id = storage.submit(command)
        qtbot.waitUntil(
            lambda: any(reply.request_id == request_id for reply in replies), timeout=10000
        )
        reply = next(reply for reply in replies if reply.request_id == request_id)
        assert reply.error_code is None, reply
        return reply

    completions: list[RunCompletion] = []
    try:
        call(StorageCommand("create", path=str(tmp_path / "session")))
        call(StorageCommand("save", document_id="D", tool_id="probe", revision=0, data=b"{}"))
        prepared = call(StorageCommand("prepare", document_id="D"))
        assert isinstance(prepared.value, RunRecord)
        run = prepared.value
        session = RunSession(storage, run, ProbeCodec())
        session.completed.connect(completions.append)
        if mode == "cancel":

            def cancel(event: ProcessEvent) -> None:
                if event.kind == "accepted":
                    session.cancel()

            session.received.connect(cancel)
        if mode == "early_cancel":
            session.cancel()
        tail = "print('accepted',flush=True); " + (
            "os._exit(9)"
            if mode == "crash"
            else "time.sleep(30)"
            if mode == "cancel"
            else "print('result',flush=True)"
        )
        command = (
            (str(tmp_path / "absent"),)
            if mode == "start_failure"
            else (
                sys.executable,
                "-I",
                "-c",
                PREAMBLE + tail,
            )
        )
        session.start(command, str(tmp_path), b"start\n")
        # A later draft must survive the old run's terminal commit unchanged.
        call(
            StorageCommand(
                "save",
                document_id="D",
                tool_id="probe",
                revision=1,
                previous_revision=0,
                data=b'{"new":true}',
            )
        )
        qtbot.waitUntil(lambda: bool(completions), timeout=15000)
        assert len(completions) == 1
        completed = completions[0]
        assert completed.error == "" and completed.record is not None
        expected = {
            "success": "succeeded",
            "cancel": "cancelled",
            "early_cancel": "cancelled",
            "crash": "interrupted",
            "start_failure": "interrupted",
        }[mode]
        assert completed.record.state == expected
        assert completed.record.revision == 0
        loaded = call(StorageCommand("load", document_id="D"))
        assert loaded.data == b'{"new":true}'
    finally:
        with qtbot.waitSignal(storage.closed, timeout=10000):
            storage.shutdown()
    with Workspace.open(tmp_path / "session") as store:
        assert store.get_run(run.run_id) == completed.record


def test_cancel_token_during_result_publication(tmp_path: Path) -> None:
    cancellation = Event()

    def fault(checkpoint: str) -> None:
        if checkpoint == "after_publish":
            cancellation.set()

    with Workspace.create(tmp_path / "race", fault_hook=fault) as store:
        store.save_draft("D", "probe", 0, b"{}", expected_previous_revision=None)
        run = store.prepare_run("D")
        child = subprocess.Popen([sys.executable, "-I", "-c", "pass"])
        store.start_run(run.run_id, child.pid)
        receipt = ProcessExitReceipt(
            run_id=run.run_id, pid=child.pid, exit_code=child.wait(timeout=10)
        )
        cancellation.clear()
        with pytest.raises(StateConflict, match="取消"):
            store.commit_result(
                run.run_id, receipt, b'{"result":10}', cancelled=cancellation.is_set
            )
        assert store.get_run(run.run_id).state == "cancelling"
        assert store.finish_cancelled(run.run_id, receipt).state == "cancelled"
