"""Installed-source identity and explicit registration for the legacy WB module."""

import hashlib
import json
import platform
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

from pydantic import TypeAdapter
from tool_contracts.api import (
    AssetRef,
    BoundAsset,
    ExecutionRequest,
    ModulePort,
    ModuleSpec,
    RuntimeVersion,
    canonical_module_json,
)

from wb_tool.application.analysis import (
    AnalysisError,
    AnalysisRequest,
    AnalysisResult,
    QuantitativeImage,
)
from wb_tool.application.module_execution import (
    METHOD_VERSION,
    MODULE_ID,
    MODULE_VERSION,
    execute_legacy_module,
    legacy_module_parameters,
    read_legacy_module_parameters,
)

# The admitted path is fixed_grid@1 / legacy_bounds@1 only. Other strategy modules
# are deliberately not admitted merely because AnalysisRequest can describe them.
_IMPLEMENTATION_FILES = (
    "module_worker.py",
    "adapters/module_worker.py",
    "adapters/module_protocol.py",
    "adapters/module_compare.py",
    "adapters/module_execution.py",
    "adapters/tiff_input.py",
    "application/module_execution.py",
    "application/analysis.py",
    "domain/lanes.py",
    "domain/quantify.py",
)


def wb_module_spec() -> ModuleSpec:
    """Read installed sources on explicit request, never while importing the package."""
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256(b"wb-implementation-source-lf@1\0")
    for relative in _IMPLEMENTATION_FILES:
        digest.update(relative.encode("ascii") + b"\0")
        digest.update((root / relative).read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return ModuleSpec(
        module_id=MODULE_ID,
        module_version=MODULE_VERSION,
        method_version=METHOD_VERSION,
        implementation_digest=digest.hexdigest(),
        input_ports=(ModulePort(name="source", kind="raw_image"),),
        output_ports=(
            ModulePort(name="measurements", kind="typed_table", filename="measurements.csv"),
            ModulePort(name="differences", kind="typed_table", filename="differences.csv"),
            ModulePort(name="provenance", kind="run_manifest", filename="run-manifest.json"),
            ModulePort(name="analysis", kind="analysis_result", filename="analysis.json"),
            ModulePort(name="baseline", kind="analysis_result", filename="baseline.json"),
        ),
        parameters_schema=canonical_module_json(
            json.dumps(TypeAdapter(AnalysisRequest).json_schema(), ensure_ascii=False)
        ),
    )


def wb_module_environment() -> tuple[RuntimeVersion, ...]:
    return (RuntimeVersion(name="python", version=platform.python_version()),) + tuple(
        RuntimeVersion(name=name, version=version(name))
        for name in ("wb-tool", "tool-contracts", "numpy", "tifffile", "pydantic")
    )


def prepare_wb_execution(
    source: AssetRef,
    planned: AnalysisRequest,
    document_id: str,
    *,
    execution_id: str | None = None,
) -> ExecutionRequest:
    parameters = legacy_module_parameters(planned)
    request = ExecutionRequest(
        request_id=uuid4().hex,
        execution_id=execution_id or uuid4().hex,
        node_id="analysis",
        attempt_id=uuid4().hex,
        document_id=document_id,
        revision=planned.revision,
        module=wb_module_spec(),
        inputs=(BoundAsset(port="source", kind="raw_image", asset=source),),
        parameters_json=parameters,
        parameters_sha256=hashlib.sha256(parameters.encode("utf-8")).hexdigest(),
        environment=wb_module_environment(),
    )
    read_legacy_module_parameters(request)
    return request


def execute_wb_module(
    image: QuantitativeImage,
    request: ExecutionRequest,
    *,
    cancelled: Callable[[], bool] | None = None,
) -> AnalysisResult:
    # Public callers may have used model_copy/update, which deliberately bypasses
    # Pydantic validation. Re-establish the frozen envelope at this boundary.
    request = ExecutionRequest.model_validate_json(request.model_dump_json())
    if request.module != wb_module_spec():
        raise AnalysisError("WB模块实现或端口声明已变化，须显式创建新请求")
    if request.environment != wb_module_environment():
        raise AnalysisError("运行环境与冻结请求不一致，须显式创建新请求")
    return execute_legacy_module(image, request, cancelled=cancelled)
