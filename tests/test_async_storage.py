"""Real event-loop/SQLite ownership, FIFO, failure and shutdown behavior."""

import subprocess
import sys
from pathlib import Path
from threading import Event

from bioimage_app.api import AsyncStorage, StorageCommand, StorageReply
from platform_runtime.api import Workspace
from PySide6.QtCore import QThread, QTimer
from pytest import LogCaptureFixture, MonkeyPatch
from pytestqt.qtbot import QtBot
from tool_contracts.api import DraftSnapshot, ProcessExitReceipt, RunRecord


def test_storage_trace_orders_each_request_without_private_content(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch, caplog: LogCaptureFixture
) -> None:
    secret = "private-exception-and-document-sentinel"
    original = Workspace.create

    def fail_create(root: str | Path) -> Workspace:
        raise ValueError(secret)

    port = AsyncStorage()
    replies: list[StorageReply] = []
    port.replied.connect(replies.append)
    requests: list[str] = []
    try:
        monkeypatch.setattr(Workspace, "create", fail_create)
        requests.append(port.submit(StorageCommand("create", path=str(tmp_path / "private-path"))))
        qtbot.waitUntil(lambda: len(replies) == 1)
        assert replies[0].error_code == "ValueError" and replies[0].message == secret
        monkeypatch.setattr(Workspace, "create", original)
        requests.append(port.submit(StorageCommand("create", path=str(tmp_path / "private-path"))))
        requests.append(
            port.submit(
                StorageCommand(
                    "save",
                    document_id="private-document",
                    tool_id="probe",
                    revision=0,
                    data=('{"secret":"' + secret + '"}').encode(),
                )
            )
        )
        qtbot.waitUntil(lambda: len(replies) == 3)
        assert all(reply.error_code is None for reply in replies[1:])
    finally:
        with qtbot.waitSignal(port.closed, timeout=10000):
            port.shutdown()
    messages = [
        record.getMessage() for record in caplog.records if record.name == "bioimage_app.storage"
    ]
    for request in requests:
        phases = [
            message.split("phase=", 1)[1].split()[0]
            for message in messages
            if f"request={request} " in message
        ]
        assert phases == ["enqueue", "execute-start", "execute-end", "reply-emit", "deliver"]
    text = "\n".join(messages)
    assert "outcome=error" in text and "outcome=ok" in text
    assert "monotonic_ns=" in text and "native_thread=" in text
    assert all(
        value not in text
        for value in (secret, str(tmp_path), "private-path", "private-document", '"secret"')
    )


def test_slow_storage_leaves_gui_event_loop_responsive(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    entered = Event()
    release = Event()
    original = Workspace.load_draft
    owner_threads: list[QThread] = []

    def slow_load(store: Workspace, document_id: str, revision: int | None = None) -> DraftSnapshot:
        owner_threads.append(QThread.currentThread())
        entered.set()
        if not release.wait(5):
            raise ValueError("test barrier expired")
        return original(store, document_id, revision)

    monkeypatch.setattr(Workspace, "load_draft", slow_load)
    port = AsyncStorage()
    replies: list[StorageReply] = []
    port.replied.connect(replies.append)
    port.submit(StorageCommand("create", path=str(tmp_path / "responsive")))
    port.submit(StorageCommand("save", document_id="D", tool_id="probe", revision=0, data=b"{}"))
    port.submit(StorageCommand("load", document_id="D"))
    ticks: list[int] = []
    timer = QTimer()
    timer.setInterval(10)
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start()
    try:
        qtbot.waitUntil(entered.is_set)
        baseline = len(ticks)
        qtbot.waitUntil(lambda: len(ticks) >= baseline + 3)
        assert len(replies) == 2
        assert owner_threads[0] != port.thread()
    finally:
        release.set()
        timer.stop()
        with qtbot.waitSignal(port.closed, timeout=10000):
            port.shutdown()
    assert replies[2].data == b"{}"


def test_fifo_save_load_errors_and_shutdown(qtbot: QtBot, tmp_path: Path) -> None:
    port = AsyncStorage()
    replies: list[StorageReply] = []
    callback_threads: list[QThread] = []

    def received(reply: StorageReply) -> None:
        replies.append(reply)
        callback_threads.append(QThread.currentThread())

    port.replied.connect(received)
    closed: list[bool] = []
    port.closed.connect(lambda: closed.append(True))
    create = port.submit(StorageCommand("create", path=str(tmp_path / "workspace")))
    save = port.submit(
        StorageCommand("save", document_id="D", tool_id="probe", revision=0, data=b'{"v":1}')
    )
    invalid = port.submit(
        StorageCommand(
            "save",
            document_id="D",
            tool_id="probe",
            revision=1,
            previous_revision=9,
            data=b'{"v":2}',
        )
    )
    load = port.submit(StorageCommand("load", document_id="D"))
    port.shutdown()
    qtbot.waitUntil(lambda: bool(closed), timeout=10000)
    assert [reply.request_id for reply in replies[:4]] == [create, save, invalid, load]
    assert isinstance(replies[1].value, DraftSnapshot)
    assert replies[2].error_code == "StateConflict"
    assert replies[3].data == b'{"v":1}'
    assert replies[3].error_code is None
    assert all(thread == port.thread() for thread in callback_threads)
    with Workspace.open(tmp_path / "workspace") as store:
        assert store.load_draft("D").revision == 0


def test_queue_budget_and_failed_open_can_retry(qtbot: QtBot, tmp_path: Path) -> None:
    import pytest

    port = AsyncStorage(max_pending=1)
    replies: list[StorageReply] = []
    port.replied.connect(replies.append)
    port.submit(StorageCommand("open", path=str(tmp_path / "missing")))
    with pytest.raises(RuntimeError, match="full"):
        port.submit(StorageCommand("documents"))
    qtbot.waitUntil(lambda: len(replies) == 1)
    assert replies[0].error_code == "WorkspaceError"
    port.submit(StorageCommand("create", path=str(tmp_path / "valid")))
    qtbot.waitUntil(lambda: len(replies) == 2)
    assert replies[1].error_code is None
    with qtbot.waitSignal(port.closed, timeout=10000):
        port.shutdown()
    with pytest.raises(RuntimeError, match="closing"):
        port.submit(StorageCommand("documents"))


def test_run_commit_and_reopen_through_storage_port(qtbot: QtBot, tmp_path: Path) -> None:
    port = AsyncStorage()
    replies: list[StorageReply] = []
    port.replied.connect(replies.append)

    def call(command: StorageCommand) -> StorageReply:
        request_id = port.submit(command)
        qtbot.waitUntil(
            lambda: any(reply.request_id == request_id for reply in replies), timeout=10000
        )
        reply = next(reply for reply in replies if reply.request_id == request_id)
        assert reply.error_code is None, reply
        return reply

    try:
        call(StorageCommand("create", path=str(tmp_path / "run-store")))
        call(StorageCommand("save", document_id="D", tool_id="probe", revision=0, data=b"{}"))
        prepared = call(StorageCommand("prepare", document_id="D"))
        assert isinstance(prepared.value, RunRecord)
        assert prepared.data == b"{}"
        run_id = prepared.value.run_id
        child = subprocess.Popen([sys.executable, "-I", "-c", "pass"])
        call(StorageCommand("start", run_id=run_id, pid=child.pid))
        receipt = ProcessExitReceipt(run_id=run_id, pid=child.pid, exit_code=child.wait(timeout=10))
        completed = call(StorageCommand("commit", run_id=run_id, receipt=receipt, data=b'{"v":7}'))
        assert isinstance(completed.value, RunRecord)
        assert completed.value.state == "succeeded"
    finally:
        with qtbot.waitSignal(port.closed, timeout=10000):
            port.shutdown()
    with Workspace.open(tmp_path / "run-store") as store:
        assert store.get_run(run_id) == completed.value


def test_import_bytes_is_immutable_validated_and_off_gui_thread(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    from hashlib import sha256

    from tool_contracts.api import AssetRef

    port = AsyncStorage()
    replies: list[StorageReply] = []
    port.replied.connect(replies.append)
    threads: list[QThread] = []
    original = Workspace.import_asset

    def observed(store: Workspace, path: str | Path, digest: str) -> AssetRef:
        threads.append(QThread.currentThread())
        return original(store, path, digest)

    monkeypatch.setattr(Workspace, "import_asset", observed)
    try:
        port.submit(StorageCommand("create", path=str(tmp_path / "workspace")))
        qtbot.waitUntil(lambda: len(replies) == 1)
        data = b"immutable generated binary"
        digest = sha256(data).hexdigest()
        for command in (
            StorageCommand("import_bytes", path="figure.png", data=data, source_sha256=digest),
            StorageCommand(
                "import_bytes", path="../../outside.png", data=data, source_sha256=digest
            ),
            StorageCommand("import_bytes", path="figure.png", data=data, source_sha256="0" * 64),
        ):
            port.submit(command)
        qtbot.waitUntil(lambda: len(replies) == 4)
        asset = replies[1].value
        assert isinstance(asset, AssetRef) and asset.sha256 == digest
        assert replies[2].error_code == replies[3].error_code == "ValueError"
        assert threads and all(thread != port.thread() for thread in threads)
        assert (tmp_path / "workspace" / asset.relative_path).read_bytes() == data
        port.submit(StorageCommand("read", asset=asset))
        qtbot.waitUntil(lambda: len(replies) == 5)
        assert replies[4].data == data
    finally:
        with qtbot.waitSignal(port.closed, timeout=10000):
            port.shutdown()
