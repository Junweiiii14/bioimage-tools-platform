"""A single legacy WB module: immutable envelopes, unchanged scientific use case."""

from collections.abc import Callable

from pydantic import TypeAdapter
from tool_contracts.api import ExecutionRequest, canonical_module_json

from wb_tool.application.analysis import (
    AnalysisError,
    AnalysisRequest,
    AnalysisResult,
    QuantitativeImage,
    analyze_annotations,
)

MODULE_ID = "wb-legacy-analysis"
MODULE_VERSION = "1.0"
METHOD_VERSION = "profile_integral@1"


def legacy_module_parameters(request: AnalysisRequest) -> str:
    return canonical_module_json(TypeAdapter(AnalysisRequest).dump_json(request).decode("utf-8"))


def read_legacy_module_parameters(request: ExecutionRequest) -> AnalysisRequest:
    module = request.module
    if (module.module_id, module.module_version, module.method_version) != (
        MODULE_ID,
        MODULE_VERSION,
        METHOD_VERSION,
    ):
        raise AnalysisError("未知WB模块或方法版本")
    planned = TypeAdapter(AnalysisRequest).validate_json(
        request.parameters_json, strict=True, extra="forbid"
    )
    if (
        planned.geometry_policy != "fixed_grid@1"
        or planned.quant_policy != "legacy_bounds@1"
        or planned.revision != request.revision
        or len(request.inputs) != 1
        or request.inputs[0].port != "source"
        or request.inputs[0].kind != "raw_image"
        or planned.source_sha256 != request.inputs[0].asset.sha256
    ):
        raise AnalysisError("V0只接受绑定原图/修订的冻结旧方法参数")
    if not any(lane.bands for lane in planned.lanes):
        raise AnalysisError("对照至少需要一个条带，不能生成空差异表")
    return planned


def execute_legacy_module(
    image: QuantitativeImage,
    request: ExecutionRequest,
    *,
    cancelled: Callable[[], bool] | None = None,
) -> AnalysisResult:
    planned = read_legacy_module_parameters(request)
    return analyze_annotations(image, planned, cancelled=cancelled)
