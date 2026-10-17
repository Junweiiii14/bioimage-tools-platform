"""Explicit WB protocol registration; generic host owns no experimental formula."""

from pydantic import TypeAdapter
from wb_tool.api import (
    AcceptedFrame,
    AnalysisResult,
    CancelledFrame,
    FailureFrame,
    HelloFrame,
    ResultFrame,
    StartFrame,
    WorkerConversation,
    encode_worker_frame,
)

from bioimage_app.process import ProcessEvent


class WBProcessCodec:
    def __init__(self, start: StartFrame) -> None:
        self._conversation = WorkerConversation(start)
        self._result_adapter = TypeAdapter(AnalysisResult)

    def accept(self, data: bytes) -> ProcessEvent:
        frame = self._conversation.accept(data)
        if isinstance(frame, HelloFrame):
            return ProcessEvent("hello")
        if isinstance(frame, AcceptedFrame):
            return ProcessEvent("accepted")
        if isinstance(frame, ResultFrame):
            return ProcessEvent("result", self._result_adapter.dump_json(frame.result))
        if isinstance(frame, FailureFrame):
            return ProcessEvent("failure", reason=frame.code + ":" + frame.message)
        if isinstance(frame, CancelledFrame):
            return ProcessEvent("cancelled")
        raise ValueError("Unexpected worker frame")

    def cancellation(self) -> bytes:
        return encode_worker_frame(self._conversation.cancellation())
