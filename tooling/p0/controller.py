"""Asynchronous Qt process adapter; final status requires process termination."""

from __future__ import annotations

import site
import sys
import time
import uuid
from pathlib import Path
from typing import Literal

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal

from tooling.p0.protocol import Decoder, Frame, Sequence, encode


def command() -> list[str]:
    if "__compiled__" in globals():
        return [str(Path(sys.argv[0]).resolve()), "--worker"]
    entry = str(Path(__file__).resolve().parents[2] / "p0_probe.py")
    if sys.platform == "win32" and sys.prefix != sys.base_prefix:
        # uv/venv's Windows redirector creates an extra child. Start the real interpreter
        # with this venv's package paths so QProcess owns the actual worker process.
        bootstrap = (
            f"import sys,site,runpy;sys.path[:0]={site.getsitepackages()!r};"
            f"sys.path.insert(0,{str(Path(entry).parent)!r});"
            f"sys.argv=[{entry!r},'--worker'];runpy.run_path({entry!r},run_name='__main__')"
        )
        return [str(Path(sys.base_prefix) / "python.exe"), "-c", bootstrap]
    return [sys.executable, entry, "--worker"]


class Controller(QObject):
    changed = Signal(str)
    ended = Signal()

    def __init__(
        self, parent: QObject | None = None, worker_command: list[str] | None = None
    ) -> None:
        super().__init__(parent)
        self.worker_command = worker_command or command()
        self.process: QProcess | None = None
        self.history: list[dict[str, object]] = []
        self.decoder = Decoder()
        self.sequence = Sequence("")
        self.terminal: Frame | None = None
        self.frames: list[Frame] = []
        self.cancel_at: float | None = None
        self.ack_ms: float | None = None
        self.started = 0.0
        self.forced = False
        self.failure = ""
        self.stderr = b""
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.timeout.connect(self.kill)

    @property
    def busy(self) -> bool:
        return self.process is not None

    def start(
        self,
        paths: list[Path],
        mode: Literal["normal", "crash", "stubborn"] = "normal",
        passes: int = 3,
    ) -> None:
        if self.busy:
            raise RuntimeError("Only one P0 job may run")
        request = Frame(
            run_id=str(uuid.uuid4()),
            seq=0,
            kind="run",
            paths=[str(p.resolve()) for p in paths],
            mode=mode,
            passes=passes,
        )
        self.decoder = Decoder()
        self.sequence = Sequence(request.run_id)
        self.terminal = None
        self.frames = []
        self.cancel_at = self.ack_ms = None
        self.forced = False
        self.failure = ""
        self.stderr = b""
        self.started = time.perf_counter()
        proc = QProcess(self)
        self.process = proc
        env = QProcessEnvironment.systemEnvironment()
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            env.insert(name, "1")
        proc.setProcessEnvironment(env)
        proc.readyReadStandardOutput.connect(self.read_output)
        proc.readyReadStandardError.connect(self.read_error)
        proc.finished.connect(self.finished)
        proc.errorOccurred.connect(self.process_error)
        proc.started.connect(lambda: proc.write(encode(request)))
        program, *arguments = self.worker_command
        proc.start(program, arguments)
        self.timeout.start(300_000)
        self.changed.emit("运行中")

    def read_output(self) -> None:
        proc = self.process
        if proc is None:
            return
        try:
            for frame in self.decoder.feed(bytes(proc.readAllStandardOutput().data())):
                if not self.sequence.accept(frame):
                    continue
                self.frames.append(frame)
                if frame.kind == "ack" and self.cancel_at is not None:
                    self.ack_ms = (time.perf_counter() - self.cancel_at) * 1000
                if frame.kind in {"result", "error", "cancelled"}:
                    if self.terminal is not None:
                        raise ValueError("Duplicate terminal frame")
                    self.terminal = frame
                if frame.kind == "progress":
                    self.changed.emit(f"运行中：已完成 {frame.completed} 张")
        except (ValueError, UnicodeError) as exc:
            self.failure = str(exc)
            proc.kill()

    def read_error(self) -> None:
        if self.process is not None:
            self.stderr = (self.stderr + self.process.readAllStandardError().data())[-8192:]

    def cancel(self) -> None:
        if self.process is None or self.cancel_at is not None:
            return
        self.cancel_at = time.perf_counter()
        self.process.write(encode(Frame(run_id=self.sequence.run_id, seq=1, kind="cancel")))
        self.timeout.start(5000)
        self.changed.emit("取消中：等待进程退出")

    def kill(self) -> None:
        if self.process is not None:
            self.forced = True
            if self.cancel_at is None:
                self.failure = "300 second task timeout"
            self.process.kill()  # P0 worker creates threads only; no descendant processes.

    def process_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self.failure = "Worker failed to start"
            self.finished(-1, QProcess.ExitStatus.CrashExit)

    def finished(self, code: int, status: QProcess.ExitStatus) -> None:
        if self.process is None:
            return
        self.read_output()
        self.read_error()
        self.timeout.stop()
        try:
            self.decoder.finish()
        except ValueError as exc:
            self.failure = str(exc)
        now = time.perf_counter()
        outcome = "failed"
        if self.cancel_at is not None and not self.failure:
            outcome = "cancelled"
        elif (
            not self.failure
            and code == 0
            and status == QProcess.ExitStatus.NormalExit
            and self.terminal is not None
            and self.terminal.kind == "result"
        ):
            outcome = "succeeded"
        self.history.append(
            {
                "run_id": self.sequence.run_id,
                "outcome": outcome,
                "exit_code": code,
                "elapsed_seconds": now - self.started,
                "forced": self.forced,
                "cancel_ack_ms": self.ack_ms,
                "cancel_stop_ms": None if self.cancel_at is None else (now - self.cancel_at) * 1000,
                "error": self.failure,
                "stderr": self.stderr.decode("utf-8", errors="replace"),
                "frames": [f.model_dump() for f in self.frames],
            }
        )
        self.process.deleteLater()
        self.process = None
        self.changed.emit(
            {
                "failed": "失败（窗口仍可用）",
                "succeeded": "完成",
                "cancelled": "已取消（进程已退出）",
            }[outcome]
        )
        self.ended.emit()
