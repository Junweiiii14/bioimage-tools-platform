"""Real QObject destruction must finish on the owner before publishing closure."""

from pathlib import Path
from threading import Event
from typing import cast

from bioimage_app.process import ProcessCodec, ProcessEvent, ProcessOutcome, ProcessRunner
from bioimage_app.project_restore import ArchiveRestoreJob, ArchiveRestoreResult
from bioimage_app.storage import AsyncStorage, StorageCommand
from PySide6.QtCore import QObject, Qt, QThread, Slot
from pytest import mark
from pytestqt.qtbot import QtBot
from shiboken6 import isValid
from wb_tool.api import WBJob
from wb_tool.ui.background import WBBackground


class DestructionProbe(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.threads: list[QThread] = []

    @Slot()
    def record(self) -> None:
        self.threads.append(QThread.currentThread())


def owned_worker(owner: QObject, attribute: str) -> QObject:
    """Inspect the actual private worker without adding a product debug API."""
    return cast(QObject, getattr(owner, attribute))


@mark.parametrize("kind", ["storage", "wb"])
def test_worker_is_destroyed_on_owner_after_drain(qtbot: QtBot, kind: str) -> None:
    port = AsyncStorage() if kind == "storage" else WBBackground()
    worker = owned_worker(port, "_worker" if kind == "storage" else "_work")
    thread = port.findChild(QThread)
    assert thread is not None
    probe = DestructionProbe()
    worker.destroyed.connect(probe.record, Qt.ConnectionType.DirectConnection)
    replies: list[object] = []
    closed: list[tuple[bool, bool, int]] = []
    port.replied.connect(replies.append)
    port.closed.connect(lambda: closed.append((isValid(worker), thread.isRunning(), len(replies))))
    try:
        if isinstance(port, AsyncStorage):
            port.submit(StorageCommand("documents"))  # Explicit failed reply, no workspace open.
        else:
            port.submit(WBJob("preview", path="missing-retirement-probe.tiff"))
        port.shutdown()
        port.shutdown()
        qtbot.waitUntil(lambda: bool(closed), timeout=10000)
        assert probe.threads == [port.thread()]
        assert closed == [(False, False, 2 if kind == "storage" else 1)]
        assert not thread.isRunning() and not isValid(worker)
    finally:
        if not closed:
            port.shutdown()
            qtbot.waitUntil(lambda: bool(closed), timeout=10000)


class UnusedCodec(ProcessCodec):
    def accept(self, frame: bytes, /) -> ProcessEvent:
        raise ValueError("A missing executable cannot produce protocol frames")

    def cancellation(self) -> bytes:
        return b"cancel\n"


def test_failed_process_destroys_decoder_before_outcome(qtbot: QtBot, tmp_path: Path) -> None:
    runner = ProcessRunner(UnusedCodec())
    decoder = owned_worker(runner, "_decoder")
    thread = runner.findChild(QThread)
    assert thread is not None
    probe = DestructionProbe()
    decoder.destroyed.connect(probe.record, Qt.ConnectionType.DirectConnection)
    outcomes: list[ProcessOutcome] = []
    observed: list[tuple[bool, bool]] = []
    runner.finished.connect(outcomes.append)
    runner.finished.connect(lambda: observed.append((isValid(decoder), thread.isRunning())))
    runner.start((str(tmp_path / "missing-worker.exe"),), str(tmp_path), b"request\n")
    qtbot.waitUntil(lambda: bool(outcomes), timeout=10000)
    assert probe.threads == [runner.thread()]
    assert observed == [(False, False)]
    assert outcomes[0].error == "worker_start_failed"


def test_failed_restore_destroys_worker_before_outcome(qtbot: QtBot, tmp_path: Path) -> None:
    owner = QObject()
    job = ArchiveRestoreJob(
        str(tmp_path / "missing.zip"), str(tmp_path / "new-workspace"), Event(), owner
    )
    worker = owned_worker(job, "_worker")
    thread = job.findChild(QThread)
    assert thread is not None
    probe = DestructionProbe()
    worker.destroyed.connect(probe.record, Qt.ConnectionType.DirectConnection)
    outcomes: list[ArchiveRestoreResult] = []
    observed: list[tuple[bool, bool]] = []
    job.finished.connect(outcomes.append)
    job.finished.connect(lambda: observed.append((isValid(worker), thread.isRunning())))
    job.start()
    qtbot.waitUntil(lambda: bool(outcomes), timeout=10000)
    assert probe.threads == [job.thread()]
    assert observed == [(False, False)] and outcomes[0].error
    assert not (tmp_path / "new-workspace").exists()
