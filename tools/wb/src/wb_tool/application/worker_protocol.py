"""Strict, versioned wire envelope; stdlib dataclass fields remain canonical."""

import json
from collections.abc import Callable
from math import isfinite
from typing import Annotated, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

from wb_tool.application.analysis import AnalysisRequest, AnalysisResult

MAX_FRAME_BYTES = 4 * 1024 * 1024
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")]


class FrameSizeError(ValueError):
    """A bounded protocol message exceeds the allowed payload size."""


class WireModel(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", allow_inf_nan=False)
    protocol_version: Literal[1]

    @property
    def kind_name(self) -> str:
        value: object = getattr(self, "kind", None)
        if not isinstance(value, str):
            raise ValueError("消息缺少合法 kind")
        return value

    @field_validator("protocol_version", "sequence", mode="before", check_fields=False)
    @classmethod
    def integer_tag(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("版本及序号必须为整数，不接受布尔值")
        return value


class HelloFrame(WireModel):
    kind: Literal["hello"]
    sequence: Literal[0]
    max_frame_bytes: Literal[4194304] = MAX_FRAME_BYTES


class IdentifiedFrame(WireModel):
    run_id: Identifier
    attempt_id: Identifier
    request_id: Identifier


class StartFrame(IdentifiedFrame):
    kind: Literal["start"]
    sequence: Literal[0]
    source_path: Annotated[str, Field(min_length=1, max_length=32768)]
    request: AnalysisRequest


class CancelFrame(IdentifiedFrame):
    kind: Literal["cancel"]
    sequence: Literal[1]


class AcceptedFrame(IdentifiedFrame):
    kind: Literal["accepted"]
    sequence: Literal[1]


class ResultFrame(IdentifiedFrame):
    kind: Literal["result"]
    sequence: Literal[2]
    result: AnalysisResult

    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        result = self.result
        if type(result.schema_version) is not int:
            raise ValueError("结果 schema 版本必须为整数")
        if result.bit_depth not in (8, 16) or len(result.lanes) != len(result.request.lanes):
            raise ValueError("结果位深或泳道数量不一致")
        maximum = (1 << result.bit_depth) - 1
        for lane, planned in zip(result.lanes, result.request.lanes, strict=True):
            if lane.roi != planned.roi or tuple(b.annotation for b in lane.bands) != planned.bands:
                raise ValueError("结果泳道或条带标注与请求不一致")
            profiles = lane.profiles
            if profiles is None:
                if not lane.reason or any(
                    b.status not in ("invalid", "excluded") for b in lane.bands
                ):
                    raise ValueError("无剖面的泳道须保留失败原因")
            else:
                if (
                    profiles.roi != lane.roi
                    or profiles.polarity != result.request.polarity
                    or profiles.dtype_max != maximum
                    or len(profiles.raw) != lane.roi.y1 - lane.roi.y0
                    or len(profiles.quantitative) != len(profiles.raw)
                ):
                    raise ValueError("结果剖面坐标/极性/尺寸不一致")
                if any(
                    not isfinite(v) or not 0 <= v <= maximum
                    for v in (*profiles.raw, *profiles.quantitative)
                ):
                    raise ValueError("结果剖面包含无效强度")
                expected = (
                    tuple(maximum - v for v in profiles.raw)
                    if profiles.polarity == "dark"
                    else profiles.raw
                )
                if profiles.quantitative != expected:
                    raise ValueError("定量剖面与原始均值及极性不一致")
            for band in lane.bands:
                measured = band.measurement
                if band.status in ("valid", "quality_review"):
                    if measured is None or profiles is None or not band.annotation.included:
                        raise ValueError("有效或待复核条带须有原始测量与剖面")
                    if (
                        measured.bounds != band.annotation.bounds
                        or measured.bounds.right >= len(profiles.raw)
                        or not isfinite(measured.signal)
                        or measured.signal < 0
                    ):
                        raise ValueError("测量边界或信号不一致")
                    if band.annotation.baseline is not None and (
                        measured.baseline != band.annotation.baseline
                        or measured.baseline_source != "manual"
                    ):
                        raise ValueError("人工基线与请求不一致")
                    if band.annotation.baseline is None and measured.baseline_source != "endpoints":
                        raise ValueError("自动端点基线来源不一致")
                    if max(measured.baseline.left_value, measured.baseline.right_value) > maximum:
                        raise ValueError("结果基线超出位深范围")
                    if band.annotation.baseline is None and (
                        measured.baseline.left_value != profiles.quantitative[measured.bounds.left]
                        or measured.baseline.right_value
                        != profiles.quantitative[measured.bounds.right]
                    ):
                        raise ValueError("结果端点基线与原始剖面不一致")
                    if band.status == "valid" and band.quality_flags:
                        raise ValueError("待处理质量提示不能冒充有效结果")
                    if band.status == "quality_review" and (
                        not band.quality_flags or not band.reason
                    ):
                        raise ValueError("待复核结果须有提示及原因")
                elif measured is not None or not band.reason:
                    raise ValueError("缺失/失败/排除结果不能携带测量，且须有原因")
                if band.status == "excluded" and band.annotation.included:
                    raise ValueError("排除状态与标注不符")
                if band.status == "not_detected" and band.annotation.bounds is not None:
                    raise ValueError("未检出状态不能携带条带边界")
                if not band.annotation.included and band.status != "excluded":
                    raise ValueError("排除条带不能被恢复为其他状态")
                allowed_flags = {"dtype_min_present", "dtype_max_present"}
                if result.request.quant_policy == "peak_envelope@1":
                    allowed_flags.update(
                        {
                            "boundary_review:background_at_roi_edge",
                            "boundary_review:unequal_or_overlapping_peak_support",
                        }
                    )
                if result.request.quant_policy in ("background_support@1", "anchored_background@1"):
                    allowed_flags.update(
                        {
                            "boundary_review:insufficient_background_support",
                            "boundary_review:multiple_signal_regions",
                        }
                    )
                if any(flag not in allowed_flags for flag in band.quality_flags):
                    raise ValueError("未知质量提示")
        return self


class FailureFrame(IdentifiedFrame):
    kind: Literal["failure"]
    sequence: Literal[2]
    code: Literal["input_invalid", "analysis_invalid", "protocol_invalid", "result_too_large"]
    message: Annotated[str, Field(min_length=1, max_length=1024)]


class CancelledFrame(IdentifiedFrame):
    kind: Literal["cancelled"]
    sequence: Literal[2]


class ProtocolErrorFrame(WireModel):
    kind: Literal["protocol_error"]
    sequence: Literal[1]
    message: Annotated[str, Field(min_length=1, max_length=1024)]


WorkerFrame = Annotated[
    HelloFrame
    | StartFrame
    | CancelFrame
    | AcceptedFrame
    | ResultFrame
    | FailureFrame
    | CancelledFrame
    | ProtocolErrorFrame,
    Field(discriminator="kind"),
]
_FRAMES = TypeAdapter(WorkerFrame)


def unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    values: dict[str, object] = {}
    for key, value in pairs:
        if key in values:
            raise ValueError("JSON 不能包含重复字段")
        values[key] = value
    return values


def parse_worker_frame(data: bytes) -> WorkerFrame:
    if len(data) > MAX_FRAME_BYTES:
        raise FrameSizeError("消息超过协议帧上限")
    raw = cast(object, json.loads(data, object_pairs_hook=unique_json_object))
    if isinstance(raw, dict):
        result = cast(dict[str, object], raw).get("result")
        if isinstance(result, dict):
            tag = cast(dict[str, object], result).get("schema_version", 1)
            if type(tag) is not int:
                raise ValueError("结果 schema 版本不能为布尔值")
    return _FRAMES.validate_json(data, strict=True, extra="forbid")


def encode_worker_frame(frame: WorkerFrame) -> bytes:
    data = frame.model_dump_json().encode("utf-8")
    # Revalidate constructed instances too; nested result objects must not bypass checks.
    parse_worker_frame(data)
    return data + b"\n"


def worker_protocol_schema() -> dict[str, object]:
    return _FRAMES.json_schema()


class WireConversation:
    """Host-side identity/order gate, without claiming persistence or process termination."""

    def __init__(
        self,
        start: IdentifiedFrame,
        parser: Callable[[bytes], WireModel],
        matches: Callable[[WireModel], bool],
    ) -> None:
        self.start = start
        self._parser = parser
        self._matches = matches
        self.stage = 0
        self.cancel_pending = False

    def cancellation(self) -> CancelFrame:
        if self.stage != 2 or self.cancel_pending:
            raise ValueError("当前会话不能发送重复或过期取消")
        self.cancel_pending = True
        return CancelFrame(
            protocol_version=1,
            kind="cancel",
            sequence=1,
            run_id=self.start.run_id,
            attempt_id=self.start.attempt_id,
            request_id=self.start.request_id,
        )

    def accept(self, data: bytes) -> WireModel:
        frame = self._parser(data)
        if self.stage == 0 and isinstance(frame, HelloFrame):
            self.stage = 1
            return frame
        if self.stage == 1 and isinstance(frame, ProtocolErrorFrame):
            self.stage = 3
            return frame
        if not isinstance(frame, IdentifiedFrame) or (
            frame.run_id,
            frame.attempt_id,
            frame.request_id,
        ) != (self.start.run_id, self.start.attempt_id, self.start.request_id):
            raise ValueError("消息身份不属于当前 run/attempt/request")
        if self.stage == 1 and isinstance(frame, AcceptedFrame):
            self.stage = 2
            return frame
        if self.stage == 2 and frame.kind_name in ("result", "failure", "cancelled"):
            if isinstance(frame, CancelledFrame) and not self.cancel_pending:
                raise ValueError("未请求取消的会话不能接受取消确认")
            if frame.kind_name == "result" and (self.cancel_pending or not self._matches(frame)):
                raise ValueError("取消后的结果或过期草稿结果不得接受")
            self.stage = 3
            return frame
        raise ValueError("消息乱序、重复或会话已经结束")


class WorkerConversation(WireConversation):
    def __init__(self, start: StartFrame) -> None:
        def matches(frame: WireModel) -> bool:
            return isinstance(frame, ResultFrame) and frame.result.request == start.request

        super().__init__(start, parse_worker_frame, matches)

    def accept(self, data: bytes) -> WorkerFrame:
        return cast(WorkerFrame, super().accept(data))
