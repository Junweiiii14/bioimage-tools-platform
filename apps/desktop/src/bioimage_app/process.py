"""One-shot Qt process owner with background protocol decoding and bounded channels."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Protocol

from PySide6.QtCore import QElapsedTimer, QObject, QProcess, Qt, QThread, QTimer, Signal, Slot

from bioimage_app.process_tree import OwnedProcessTree

MAX_FRAME = 4 * 1024 * 1024
MAX_STREAM = 8 * 1024 * 1024


@dataclass(frozen=True)
class ProcessEvent:
    kind: Literal["hello", "accepted", "result", "failure", "cancelled"]
    data: bytes = b""
    reason: str = ""


class ProcessCodec(Protocol):
    def accept(self, frame: bytes, /) -> ProcessEvent: ...
    def cancellation(self) -> bytes: ...


@dataclass(frozen=True)
class ProcessOutcome:
    pid: int
    exit_code: int | None
    terminal: ProcessEvent | None
    cancel_requested: bool
    error: str
    stderr_tail: bytes


class _Decoder(QObject):
    received = Signal(object)
    write = Signal(bytes)
    failed = Signal(str)
    drained = Signal()

    def __init__(self, codec: ProcessCodec) -> None:
        super().__init__()
        self._codec = codec
        self._buffer = b""
        self._total = 0
        self._frames = 0
        self._failed = False
        self._accepted = False
        self._cancel = False
        self._cancel_sent = False

    def _fail(self, reason: str) -> None:
        if not self._failed:
            self._failed = True
            self._buffer = b""
            self.failed.emit(reason)

    @Slot(bytes)
    def feed(self, chunk: bytes) -> None:
        if self._failed:
            return
        self._total += len(chunk)
        if self._total > MAX_STREAM:
            self._fail("worker_output_budget")
            return
        self._buffer += chunk
        while b"\n" in self._buffer:
            frame, self._buffer = self._buffer.split(b"\n", 1)
            frame = frame.removesuffix(b"\r")
            self._frames += 1
            if len(frame) > MAX_FRAME or self._frames > 8:
                self._fail("worker_frame_budget")
                return
            try:
                event = self._codec.accept(frame)
            except (ValueError, TypeError) as error:
                self._fail("worker_protocol_invalid:" + type(error).__name__)
                return
            if event.kind == "accepted":
                self._accepted = True
                self._send_cancel()
            self.received.emit(event)
        if len(self._buffer) > MAX_FRAME:
            self._fail("worker_frame_budget")

    def _send_cancel(self) -> None:
        if self._cancel and self._accepted and not self._cancel_sent and not self._failed:
            try:
                frame = self._codec.cancellation()
            except (ValueError, TypeError):
                self._fail("worker_cancel_protocol_invalid")
                return
            self._cancel_sent = True
            self.write.emit(frame)

    @Slot()
    def cancel(self) -> None:
        self._cancel = True
        self._send_cancel()

    @Slot()
    def eof(self) -> None:
        if self._buffer:
            self._fail("worker_truncated_frame")
        self.drained.emit()


class ProcessRunner(QObject):
    """Single use; keep alive through finished. Authorize request only after PID persistence.

    ``cancel`` is called after host cancellation is persisted. Outcome is a candidate,
    never a succeeded database record. It waits for OS exit, decoder and owned descendants.
    """

    started = Signal(int)
    received = Signal(object)
    finished = Signal(object)
    _chunk = Signal(bytes)
    _eof = Signal()
    _cancel = Signal()

    def __init__(self, codec: ProcessCodec, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._process = QProcess(self)
        if os.name != "nt":
            parameters = QProcess.UnixProcessParameters()
            parameters.flags = QProcess.UnixProcessFlag.CreateNewSession
            self._process.setUnixProcessParameters(parameters)
        self._thread = QThread(self)
        self._decoder = _Decoder(codec)
        self._decoder.moveToThread(self._thread)
        self._chunk.connect(self._decoder.feed, Qt.ConnectionType.QueuedConnection)
        self._eof.connect(self._decoder.eof, Qt.ConnectionType.QueuedConnection)
        self._cancel.connect(self._decoder.cancel, Qt.ConnectionType.QueuedConnection)
        self._decoder.received.connect(self._event, Qt.ConnectionType.QueuedConnection)
        self._decoder.write.connect(self._write, Qt.ConnectionType.QueuedConnection)
        self._decoder.failed.connect(self._fail, Qt.ConnectionType.QueuedConnection)
        self._decoder.drained.connect(self._thread.quit)
        self._thread.finished.connect(self._decoder.deleteLater)
        self._thread.finished.connect(self._decoder_stopped)
        self._process.started.connect(self._started)
        self._process.readyReadStandardOutput.connect(self._stdout)
        self._process.readyReadStandardError.connect(self._stderr)
        self._process.finished.connect(self._exited)
        self._process.errorOccurred.connect(self._process_error)
        self._force_timer = QTimer(self)
        self._force_timer.setSingleShot(True)
        self._force_timer.timeout.connect(self._force)
        self._tree_timer = QTimer(self)
        self._tree_timer.setInterval(25)
        self._tree_timer.timeout.connect(self._complete)
        self._pid = 0
        self._tree: OwnedProcessTree | None = None
        self._used = False
        self._exit_seen = False
        self._decoder_done = False
        self._exit_code: int | None = None
        self._terminal: ProcessEvent | None = None
        self._error = ""
        self._stderr_tail = b""
        self._total = 0
        self._hello = False
        self._request = b""
        self._permitted = False
        self._sent = False
        self._cancelled = False
        self._done = False
        self._exit_elapsed = QElapsedTimer()

    def start(self, command: tuple[str, ...], cwd: str, request: bytes) -> None:
        self._assert_owner()
        if (
            self._used
            or not command
            or not request
            or len(request) > MAX_FRAME
            or not request.endswith(b"\n")
            or request.count(b"\n") != 1
        ):
            raise ValueError("Expected a fresh runner and bounded request")
        self._used = True
        self._request = request
        self._process.setWorkingDirectory(cwd)
        self._thread.start()
        self._force_timer.start(15000)  # also bounds startup/PID registration/hello
        self._process.start(command[0], list(command[1:]))

    @Slot()
    def _started(self) -> None:
        self._pid = self._process.processId()
        try:
            self._tree = OwnedProcessTree(self._pid)
        except OSError:
            self._fail("process_tree_attachment_failed")
        self.started.emit(self._pid)

    def allow_request(self, persisted_pid: int) -> None:
        self._assert_owner()
        if self._permitted or self._pid <= 0 or persisted_pid != self._pid:
            raise ValueError("PID persistence does not match this process")
        self._permitted = True
        self._send_request()

    def _send_request(self) -> None:
        if (
            self._hello
            and self._permitted
            and not self._sent
            and not self._error
            and not self._cancelled
        ):
            self._sent = True
            self._force_timer.stop()
            self._write(self._request)

    @Slot(object)
    def _event(self, event: ProcessEvent) -> None:
        if event.kind == "hello":
            self._hello = True
            self._send_request()
        elif event.kind in ("result", "failure", "cancelled"):
            if self._terminal is not None:
                self._fail("worker_duplicate_terminal")
            self._terminal = event
        self.received.emit(event)

    @Slot(bytes)
    def _write(self, data: bytes) -> None:
        if self._exit_seen or self._error:
            return
        if len(data) > MAX_FRAME or self._process.write(data) != len(data):
            self._fail("worker_write_failed")

    @Slot()
    def _stdout(self) -> None:
        self._process.setReadChannel(QProcess.ProcessChannel.StandardOutput)
        while self._process.bytesAvailable():
            chunk = self._process.read(128 * 1024).data()
            self._total += len(chunk)
            if self._total <= MAX_STREAM and not self._error:
                self._chunk.emit(chunk)
            elif not self._error:
                self._fail("worker_output_budget")

    @Slot()
    def _stderr(self) -> None:
        self._process.setReadChannel(QProcess.ProcessChannel.StandardError)
        while self._process.bytesAvailable():
            self._stderr_tail = (self._stderr_tail + self._process.read(128 * 1024).data())[-65536:]

    def cancel(self, *, grace_ms: int = 5000) -> None:
        self._assert_owner()
        if type(grace_ms) is not int or not 1 <= grace_ms <= 60000:
            raise ValueError("Cancellation grace must be 1..60000 milliseconds")
        if self._done:
            return
        self._cancelled = True
        self._cancel.emit()
        self._force_timer.start(grace_ms)
        if not self._sent:
            self._force()

    def abort(self, reason: str) -> None:
        """Stop an owned process after a host-side error, without claiming cancellation."""
        self._assert_owner()
        self._fail(reason)

    def _assert_owner(self) -> None:
        if QThread.currentThread() != self.thread():
            raise RuntimeError("Process runner must be called from its owning GUI thread")

    @Slot(str)
    def _fail(self, reason: str) -> None:
        if not self._error:
            self._error = reason
        self._force()

    @Slot()
    def _force(self) -> None:
        self._force_timer.stop()
        if not self._cancelled and not self._error:
            self._error = "worker_timeout"
        try:
            if self._tree is not None:
                self._tree.terminate()
        except OSError:
            self._error = "process_tree_termination_failed"
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()

    @Slot(QProcess.ProcessError)
    def _process_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._error = "worker_start_failed"
            self._exited_without_process()
        elif error != QProcess.ProcessError.Crashed:
            self._fail("worker_transport_error")

    def _exited_without_process(self) -> None:
        self._exit_seen = True
        self._eof.emit()

    @Slot(int, QProcess.ExitStatus)
    def _exited(self, code: int, status: QProcess.ExitStatus) -> None:
        self._stdout()
        self._stderr()
        self._exit_seen = True
        self._exit_code = code
        self._exit_elapsed.start()
        if status == QProcess.ExitStatus.CrashExit and not self._cancelled:
            self._error = self._error or "worker_crashed"
        self._eof.emit()
        self._tree_timer.start()

    @Slot()
    def _decoder_stopped(self) -> None:
        if not self._thread.wait(0):
            QTimer.singleShot(1, self._decoder_stopped)
            return
        self._decoder_done = True
        self._complete()

    @Slot()
    def _complete(self) -> None:
        if self._done or not self._exit_seen or not self._decoder_done:
            return
        try:
            if self._tree is not None and not self._tree.empty():
                if self._exit_elapsed.isValid() and self._exit_elapsed.elapsed() < 250:
                    self._tree_timer.start()
                    return
                self._error = self._error or ("" if self._cancelled else "worker_left_descendants")
                self._tree.terminate()
                self._tree_timer.start()
                return
        except OSError:
            self._error = "process_tree_observation_failed"
            self._tree_timer.start()
            return
        self._done = True
        self._force_timer.stop()
        self._tree_timer.stop()
        if self._tree is not None:
            self._tree.close()
        if not self._cancelled and self._terminal is None:
            self._error = self._error or "worker_missing_terminal"
        self.finished.emit(
            ProcessOutcome(
                self._pid,
                self._exit_code,
                self._terminal,
                self._cancelled,
                self._error,
                self._stderr_tail,
            )
        )
