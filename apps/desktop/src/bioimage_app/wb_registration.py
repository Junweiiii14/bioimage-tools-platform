"""Explicit WB protocol registration; generic host owns no experimental formula."""

from pydantic import TypeAdapter
from wb_tool.api import (
    AcceptedFrame,
    AnalysisResult,
    CancelledFrame,
    FailureFrame,
    HelloFrame,
    OCRConversation,
    OCRRecognition,
    OCRResultFrame,
    OCRStartFrame,
    ResultFrame,
    StartFrame,
    WBModuleConversation,
    WBModuleStart,
    WorkerConversation,
    encode_module_frame,
    encode_ocr_frame,
    encode_worker_frame,
)

from bioimage_app.process import ProcessEvent


class WBModuleProcessCodec:
    def __init__(self, start: WBModuleStart) -> None:
        self._conversation = WBModuleConversation(start)

    def accept(self, data: bytes) -> ProcessEvent:
        event = self._conversation.accept(data)
        return ProcessEvent(
            event.kind,
            event.manifest.model_dump_json().encode("utf-8") if event.manifest is not None else b"",
            event.reason,
            "module_manifest",
        )

    def cancellation(self) -> bytes:
        return encode_module_frame(self._conversation.cancellation())


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


class OCRProcessCodec:
    def __init__(self, start: OCRStartFrame) -> None:
        self._conversation = OCRConversation(start)
        self._result_adapter = TypeAdapter(OCRRecognition)

    def accept(self, data: bytes) -> ProcessEvent:
        frame = self._conversation.accept(data)
        if isinstance(frame, HelloFrame):
            return ProcessEvent("hello")
        if isinstance(frame, AcceptedFrame):
            return ProcessEvent("accepted")
        if isinstance(frame, OCRResultFrame):
            return ProcessEvent("result", self._result_adapter.dump_json(frame.result))
        if isinstance(frame, FailureFrame):
            return ProcessEvent("failure", reason=frame.code + ":" + frame.message)
        if isinstance(frame, CancelledFrame):
            return ProcessEvent("cancelled")
        raise ValueError("Unexpected OCR frame")

    def cancellation(self) -> bytes:
        return encode_ocr_frame(self._conversation.cancellation())
