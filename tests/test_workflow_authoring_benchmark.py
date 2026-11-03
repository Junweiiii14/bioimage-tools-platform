"""The standalone sampler must service Python storage slots, not starve them."""

from pathlib import Path

from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from PySide6.QtWidgets import QApplication

from tooling.benchmark_workflow_authoring import AsyncEventPump


def test_measurement_pump_delivers_storage_and_drains(qapp: QApplication, tmp_path: Path) -> None:
    port = AsyncStorage()
    replies: list[StorageReply] = []
    closed: list[bool] = []
    port.replied.connect(replies.append)
    port.closed.connect(lambda: closed.append(True))
    pump = AsyncEventPump()
    try:
        port.submit(StorageCommand("create", path=str(tmp_path / "workspace")))
        pump.waitUntil(lambda: bool(replies), timeout=5000)
        assert replies[0].error_code is None
        assert (tmp_path / "workspace" / "metadata.sqlite").is_file()
    finally:
        port.shutdown()
        pump.waitUntil(lambda: bool(closed), timeout=5000)
