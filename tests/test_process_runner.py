"""Real Qt subprocess framing, cancellation, budgets and WB protocol integration."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.api import (
    ProcessEvent,
    ProcessOutcome,
    ProcessRunner,
    create_wb_codec,
)
from PySide6.QtCore import QTimer
from pytestqt.qtbot import QtBot
from wb_tool.api import (
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    LaneAnnotation,
    LaneROI,
    StartFrame,
    encode_worker_frame,
    load_tiff,
)


class ProbeCodec:
    def __init__(self) -> None:
        self.stage = 0

    def accept(self, frame: bytes) -> ProcessEvent:
        expected = (b"hello", b"accepted", b"result")
        if self.stage >= 3 or frame != expected[self.stage]:
            raise ValueError("Invalid probe sequence")
        event = (ProcessEvent("hello"), ProcessEvent("accepted"), ProcessEvent("result", b"{}"))[
            self.stage
        ]
        self.stage += 1
        return event

    def cancellation(self) -> bytes:
        if self.stage != 2:
            raise ValueError("Not accepted")
        return b"cancel\n"


PREAMBLE = "import sys,time,os; print('hello',flush=True); sys.stdin.buffer.readline(); "


def run_probe(qtbot: QtBot, tmp_path: Path, tail: str, *, cancel: bool = False) -> ProcessOutcome:
    runner = ProcessRunner(ProbeCodec())
    outcomes: list[ProcessOutcome] = []
    runner.finished.connect(outcomes.append)
    runner.started.connect(runner.allow_request)
    if cancel:

        def received(event: ProcessEvent) -> None:
            if event.kind == "accepted":
                runner.cancel(grace_ms=50)

        runner.received.connect(received)
    runner.start((sys.executable, "-I", "-c", PREAMBLE + tail), str(tmp_path), b"start\n")
    qtbot.waitUntil(lambda: bool(outcomes), timeout=15000)
    assert len(outcomes) == 1
    return outcomes[0]


def test_fragmented_frames_and_bounded_stderr(qtbot: QtBot, tmp_path: Path) -> None:
    result = run_probe(
        qtbot,
        tmp_path,
        "sys.stderr.write('x'*100000); sys.stderr.flush(); "
        "sys.stdout.write('acce'); sys.stdout.flush(); time.sleep(.03); "
        "sys.stdout.write('pted\\nresult\\n'); sys.stdout.flush()",
    )
    assert result.error == ""
    assert result.pid > 0 and result.exit_code == 0
    assert result.terminal == ProcessEvent("result", b"{}")
    assert len(result.stderr_tail) == 65536


@pytest.mark.parametrize(
    "tail,reason",
    [
        ("print('wrong',flush=True); time.sleep(10)", "worker_protocol_invalid"),
        ("sys.stdout.write('accepted\\nres'); sys.stdout.flush()", "worker_truncated_frame"),
        ("print('accepted',flush=True); os._exit(7)", "worker_missing_terminal"),
        (
            "sys.stdout.write('x'*(4*1024*1024+1)); sys.stdout.flush(); time.sleep(10)",
            "worker_frame_budget",
        ),
    ],
)
def test_rejects_invalid_output(qtbot: QtBot, tmp_path: Path, tail: str, reason: str) -> None:
    result = run_probe(qtbot, tmp_path, tail)
    assert result.error.startswith(reason)
    assert result.terminal is None


def test_force_cancel_owned_tree(qtbot: QtBot, tmp_path: Path) -> None:
    child_pid_path = tmp_path / "child.txt"
    # Descendant is created only after the host has attached the tree and sent the request.
    code = (
        "import subprocess; child=subprocess.Popen([sys.executable,'-I','-c',"
        "'import time; time.sleep(30)']); "
        f"open({str(child_pid_path)!r},'w').write(str(child.pid)); "
        "print('accepted',flush=True); time.sleep(30)"
    )
    result = run_probe(qtbot, tmp_path, code, cancel=True)
    assert result.cancel_requested and result.pid > 0
    assert result.error == ""
    assert child_pid_path.exists()
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x100000, False, int(child_pid_path.read_text()))
        if handle:
            try:
                assert kernel.WaitForSingleObject(handle, 0) == 0
            finally:
                kernel.CloseHandle(handle)


def test_failed_start_is_terminal_without_fake_pid(qtbot: QtBot, tmp_path: Path) -> None:
    runner = ProcessRunner(ProbeCodec())
    outcomes: list[ProcessOutcome] = []
    runner.finished.connect(outcomes.append)
    runner.start((str(tmp_path / "absent-executable"),), str(tmp_path), b"start\n")
    qtbot.waitUntil(lambda: bool(outcomes))
    assert outcomes[0].pid == 0 and outcomes[0].exit_code is None
    assert outcomes[0].error == "worker_start_failed"


def test_real_wb_worker_with_delayed_pid_permission(qtbot: QtBot, tmp_path: Path) -> None:
    path = tmp_path / "analytic.tif"
    tifffile.imwrite(path, np.array([[245], [235], [245]], dtype=np.uint8))
    image = load_tiff(path)
    request = AnalysisRequest(
        image.sha256,
        2,
        "dark",
        (LaneAnnotation(LaneROI("L", 0, 0, 1, 3), (BandAnnotation("B", BandBounds(0, 2)),)),),
    )
    start = StartFrame(
        protocol_version=1,
        kind="start",
        sequence=0,
        run_id="r",
        attempt_id="a",
        request_id="q",
        source_path=str(path),
        request=request,
    )
    runner = ProcessRunner(create_wb_codec(start))
    outcomes: list[ProcessOutcome] = []
    events: list[ProcessEvent] = []
    runner.received.connect(events.append)
    runner.finished.connect(outcomes.append)

    def permit(pid: int) -> None:
        QTimer.singleShot(150, lambda: runner.allow_request(pid))

    runner.started.connect(permit)
    runner.start(
        (sys.executable, "-I", "-m", "wb_tool.worker"), str(tmp_path), encode_worker_frame(start)
    )
    qtbot.waitUntil(lambda: bool(outcomes), timeout=15000)
    result = outcomes[0]
    assert result.error == "" and result.exit_code == 0
    assert [event.kind for event in events] == ["hello", "accepted", "result"]
    assert result.terminal is not None
    document = json.loads(result.terminal.data)
    assert document["request"]["revision"] == 2
    assert document["lanes"][0]["bands"][0]["measurement"]["signal"] == 10
