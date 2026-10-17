"""Real subprocesses: crash recovery, cooperative and deadline-based cancellation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import tifffile
from pytestqt.qtbot import QtBot

from tooling.p0.controller import Controller


def fixture_image(directory: Path) -> Path:
    image = directory / "进程输入.tif"
    tifffile.imwrite(image, np.full((1024, 1024), 32768, dtype=np.uint16))
    return image


def test_worker_crash_success_and_cancel(qtbot: QtBot, tmp_path: Path) -> None:
    image = fixture_image(tmp_path)
    host = Controller()
    host.start([image], mode="crash")
    qtbot.waitUntil(lambda: not host.busy, timeout=20000)
    assert host.history[-1]["outcome"] == "failed"
    assert host.history[-1]["exit_code"] == 23
    host.start([image])
    qtbot.waitUntil(lambda: not host.busy, timeout=20000)
    assert host.history[-1]["outcome"] == "succeeded"
    assert host.frames[0].kind == "hello"
    assert "qt_imported=False" in host.frames[0].detail
    assert host.terminal is not None and host.terminal.completed == 1
    host.start([image] * 20, passes=200)
    qtbot.waitUntil(lambda: bool(host.frames), timeout=20000)
    host.cancel()
    qtbot.waitUntil(lambda: not host.busy, timeout=10000)
    assert host.history[-1]["outcome"] == "cancelled"
    assert host.history[-1]["forced"] is False
    assert host.history[-1]["cancel_ack_ms"] is not None


def test_stubborn_worker_is_reaped_after_grace(qtbot: QtBot, tmp_path: Path) -> None:
    host = Controller()
    host.start([fixture_image(tmp_path)], mode="stubborn")
    qtbot.waitUntil(lambda: bool(host.frames), timeout=20000)
    host.cancel()
    assert host.busy  # Cancellation request is not a terminal status.
    qtbot.waitUntil(lambda: not host.busy, timeout=10000)
    assert host.history[-1]["outcome"] == "cancelled"
    assert host.history[-1]["forced"] is True
    assert host.history[-1]["cancel_ack_ms"] is not None


def test_missing_input_is_failure(qtbot: QtBot, tmp_path: Path) -> None:
    host = Controller()
    host.start([tmp_path / "missing.tif"])
    qtbot.waitUntil(lambda: not host.busy, timeout=20000)
    assert host.history[-1]["outcome"] == "failed"
    assert host.terminal is not None and host.terminal.kind == "error"
