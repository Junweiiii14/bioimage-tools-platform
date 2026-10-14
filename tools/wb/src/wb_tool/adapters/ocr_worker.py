"""OCR process reuses the proven transport; it never writes workspace or UI state."""

import sys
from contextlib import redirect_stdout
from threading import Event, Lock, Thread

from wb_tool.adapters.ocr import recognize_figure
from wb_tool.adapters.worker import LineReader
from wb_tool.application.analysis import AnalysisCancelled
from wb_tool.application.ocr_protocol import (
    OCRResultFrame,
    OCRStartFrame,
    encode_ocr_frame,
    parse_ocr_frame,
)
from wb_tool.application.worker_protocol import (
    AcceptedFrame,
    CancelFrame,
    CancelledFrame,
    FailureFrame,
    FrameSizeError,
    HelloFrame,
    ProtocolErrorFrame,
    WireModel,
)


def _emit(frame: WireModel) -> None:
    sys.stdout.buffer.write(encode_ocr_frame(frame))
    sys.stdout.buffer.flush()


def main() -> int:
    _emit(HelloFrame(protocol_version=1, kind="hello", sequence=0))
    reader = LineReader(sys.stdin.fileno())
    try:
        first = reader.read()
        if first is None:
            raise ValueError("Missing OCR request")
        start = parse_ocr_frame(first)
        if not isinstance(start, OCRStartFrame):
            raise ValueError("Expected OCR start")
    except ValueError:
        _emit(
            ProtocolErrorFrame(
                protocol_version=1, kind="protocol_error", sequence=1, message="OCR 请求协议无效"
            )
        )
        return 2
    identity = dict(run_id=start.run_id, attempt_id=start.attempt_id, request_id=start.request_id)
    cancelled, invalid = Event(), Event()
    lock = Lock()

    def listen() -> None:
        try:
            while (line := reader.read()) is not None:
                frame = parse_ocr_frame(line)
                with lock:
                    if (
                        not isinstance(frame, CancelFrame)
                        or cancelled.is_set()
                        or (frame.run_id, frame.attempt_id, frame.request_id)
                        != (start.run_id, start.attempt_id, start.request_id)
                    ):
                        invalid.set()
                        return
                    cancelled.set()
        except (ValueError, OSError):
            with lock:
                invalid.set()

    Thread(target=listen, name="ocr-cancel-listener", daemon=True).start()
    _emit(AcceptedFrame(protocol_version=1, kind="accepted", sequence=1, **identity))
    response: WireModel
    try:
        with redirect_stdout(sys.stderr):
            result = recognize_figure(
                start.source_path,
                start.request.source_sha256,
                cancelled=lambda: cancelled.is_set() or invalid.is_set(),
            )
        response = OCRResultFrame(
            protocol_version=1,
            kind="result",
            sequence=2,
            revision=start.request.revision,
            result=result,
            **identity,
        )
    except AnalysisCancelled:
        response = CancelledFrame(protocol_version=1, kind="cancelled", sequence=2, **identity)
    except (ValueError, OSError, ImportError) as error:
        print(type(error).__name__, file=sys.stderr)
        response = FailureFrame(
            protocol_version=1,
            kind="failure",
            sequence=2,
            code="analysis_invalid",
            message="OCR 识别失败，请检查安装与输入",
            **identity,
        )
    with lock:
        if invalid.is_set():
            response = FailureFrame(
                protocol_version=1,
                kind="failure",
                sequence=2,
                code="protocol_invalid",
                message="OCR 取消身份/协议无效",
                **identity,
            )
        elif cancelled.is_set():
            response = CancelledFrame(protocol_version=1, kind="cancelled", sequence=2, **identity)
        try:
            _emit(response)
        except FrameSizeError:
            _emit(
                FailureFrame(
                    protocol_version=1,
                    kind="failure",
                    sequence=2,
                    code="result_too_large",
                    message="OCR 结果超出帧容量",
                    **identity,
                )
            )
            return 2
    return 0 if isinstance(response, OCRResultFrame | CancelledFrame) else 2
