"""One-job NDJSON worker. No GUI, database writes, or application terminal commit."""

import os
import sys
from threading import Event, Lock, Thread

from pydantic import ValidationError

from wb_tool.adapters.tiff_input import ImageInputError, load_tiff
from wb_tool.application.analysis import AnalysisCancelled, AnalysisError, analyze_annotations
from wb_tool.application.worker_protocol import (
    MAX_FRAME_BYTES,
    AcceptedFrame,
    CancelFrame,
    CancelledFrame,
    FailureFrame,
    FrameSizeError,
    HelloFrame,
    ProtocolErrorFrame,
    ResultFrame,
    StartFrame,
    WorkerFrame,
    encode_worker_frame,
    parse_worker_frame,
)


class LineReader:
    """Unbuffered OS reads avoid a daemon retaining stdin's buffered lock at exit."""

    def __init__(self, descriptor: int) -> None:
        self.descriptor = descriptor
        self.buffer = bytearray()

    def read(self) -> bytes | None:
        while True:
            newline = self.buffer.find(b"\n")
            if newline >= 0:
                if newline > MAX_FRAME_BYTES:
                    raise ValueError("帧超过上限")
                line = bytes(self.buffer[:newline])
                del self.buffer[: newline + 1]
                return line
            if len(self.buffer) > MAX_FRAME_BYTES:
                raise ValueError("帧超过上限")
            chunk = os.read(self.descriptor, 8192)
            if not chunk:
                if self.buffer:
                    raise ValueError("消息缺少终止换行")
                return None
            self.buffer.extend(chunk)


def emit(frame: WorkerFrame) -> None:
    sys.stdout.buffer.write(encode_worker_frame(frame))
    sys.stdout.buffer.flush()


def main() -> int:
    emit(HelloFrame(protocol_version=1, kind="hello", sequence=0))
    reader = LineReader(sys.stdin.fileno())
    try:
        line = reader.read()
        if line is None:
            raise ValueError("缺少分析请求")
        start = parse_worker_frame(line)
        if not isinstance(start, StartFrame):
            raise ValueError("首帧必须为 start")
    except (ValueError, ValidationError) as exc:
        emit(
            ProtocolErrorFrame(
                protocol_version=1, kind="protocol_error", sequence=1, message="分析请求协议无效"
            )
        )
        print(type(exc).__name__, file=sys.stderr)
        return 2
    identity = dict(run_id=start.run_id, attempt_id=start.attempt_id, request_id=start.request_id)
    cancelled = Event()
    invalid = Event()
    terminal_lock = Lock()

    def listen() -> None:
        seen_cancel = False
        try:
            while (control_line := reader.read()) is not None:
                control = parse_worker_frame(control_line)
                with terminal_lock:
                    if (
                        not isinstance(control, CancelFrame)
                        or seen_cancel
                        or (control.run_id, control.attempt_id, control.request_id)
                        != (start.run_id, start.attempt_id, start.request_id)
                    ):
                        invalid.set()
                        return
                    seen_cancel = True
                    cancelled.set()
        except (OSError, ValueError, ValidationError):
            with terminal_lock:
                invalid.set()

    def stop_requested() -> bool:
        return cancelled.is_set() or invalid.is_set()

    Thread(target=listen, name="wb-cancel-listener", daemon=True).start()
    emit(AcceptedFrame(protocol_version=1, kind="accepted", sequence=1, **identity))
    response: WorkerFrame
    try:
        if stop_requested():
            raise AnalysisCancelled()
        image = load_tiff(start.source_path)
        result = analyze_annotations(image, start.request, cancelled=stop_requested)
        response = ResultFrame(
            protocol_version=1, kind="result", sequence=2, result=result, **identity
        )
    except AnalysisCancelled:
        response = CancelledFrame(protocol_version=1, kind="cancelled", sequence=2, **identity)
    except ImageInputError:
        response = FailureFrame(
            protocol_version=1,
            kind="failure",
            sequence=2,
            code="input_invalid",
            message="图像读取失败，请检查格式及文件",
            **identity,
        )
    except AnalysisError:
        response = FailureFrame(
            protocol_version=1,
            kind="failure",
            sequence=2,
            code="analysis_invalid",
            message="图像来源或分析请求不一致",
            **identity,
        )
    with terminal_lock:
        if invalid.is_set():
            response = FailureFrame(
                protocol_version=1,
                kind="failure",
                sequence=2,
                code="protocol_invalid",
                message="取消消息协议或身份无效",
                **identity,
            )
        elif cancelled.is_set():
            response = CancelledFrame(protocol_version=1, kind="cancelled", sequence=2, **identity)
        try:
            emit(response)
        except FrameSizeError:
            emit(
                FailureFrame(
                    protocol_version=1,
                    kind="failure",
                    sequence=2,
                    code="result_too_large",
                    message="结果超过当前帧容量，须缩小分析批次",
                    **identity,
                )
            )
            return 2
    return 0 if isinstance(response, ResultFrame | CancelledFrame) else 2


if __name__ == "__main__":
    raise SystemExit(main())
