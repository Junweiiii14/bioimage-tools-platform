"""Immutable contracts for local assets, document revisions and host-owned runs."""

import hashlib
import json
import re
from typing import Annotated, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
NonNegative = Annotated[int, Field(ge=0)]
RunState = Literal[
    "prepared",
    "running",
    "cancelling",
    "committing",
    "succeeded",
    "cancelled",
    "failed",
    "interrupted",
]


def validate_relative_path(value: str) -> str:
    devices = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    parts = value.split("/")
    if (
        not value
        or not re.fullmatch(r"[A-Za-z0-9._/-]+", value)
        or any(
            part in ("", ".", "..") or part.endswith(".") or part.split(".")[0].upper() in devices
            for part in parts
        )
    ):
        raise ValueError("资产路径须为无越界、控制字符或 Windows 别名的规范相对路径")
    return value


class FrozenContract(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid", allow_inf_nan=False)


class WorkspaceFormat(FrozenContract):
    format: Literal["bioimage-workspace"]
    version: Annotated[int, Field(ge=1, le=1)]
    workspace_id: Identifier


class AssetRef(FrozenContract):
    asset_id: Identifier
    relative_path: Annotated[str, Field(pattern=r"^[A-Za-z0-9._/-]+$", max_length=512)]
    sha256: Digest
    size_bytes: NonNegative
    schema_version: Annotated[int, Field(ge=1, le=1)] = 1

    @field_validator("relative_path")
    @classmethod
    def relative_file(cls, value: str) -> str:
        return validate_relative_path(value)


class DocumentRevision(FrozenContract):
    document_id: Identifier
    tool_id: Identifier
    revision: NonNegative


class DraftSnapshot(DocumentRevision):
    asset: AssetRef


class RunRecord(DocumentRevision):
    run_id: Identifier
    state: RunState
    request: AssetRef
    pid: Annotated[int, Field(gt=0)] | None = None
    result: AssetRef | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def consistent_terminal(self) -> Self:
        if (self.state == "succeeded") != (self.result is not None):
            raise ValueError("只有已提交成功的运行可以引用结果")
        if self.state in ("failed", "interrupted") and not self.reason:
            raise ValueError("失败或中断必须保留原因")
        if self.state in ("running", "committing", "succeeded") and self.pid is None:
            raise ValueError("已启动运行必须记录进程身份")
        return self


class ProcessExitReceipt(FrozenContract):
    run_id: Identifier
    pid: NonNegative
    exit_code: int | None

    @model_validator(mode="after")
    def observed_exit(self) -> Self:
        if (self.pid == 0) != (self.exit_code is None):
            raise ValueError("未启动回执使用 pid=0/code=None；启动进程须有实际退出码")
        return self


class RecoveryReport(FrozenContract):
    interrupted_run_ids: tuple[str, ...] = ()
    quarantined_paths: tuple[str, ...] = ()
    orphan_paths: tuple[str, ...] = ()


def storage_contract_schema() -> dict[str, object]:
    return {
        model.__name__: model.model_json_schema()
        for model in (
            WorkspaceFormat,
            DocumentRevision,
            AssetRef,
            DraftSnapshot,
            RunRecord,
            ProcessExitReceipt,
            RecoveryReport,
        )
    }


__all__ = [
    "WorkspaceFormat",
    "DocumentRevision",
    "AssetRef",
    "DraftSnapshot",
    "RunRecord",
    "RunState",
    "ProcessExitReceipt",
    "RecoveryReport",
    "storage_contract_schema",
    "validate_relative_path",
]


# Module envelopes evolve independently from storage_contract_schema()/AssetRef v1.
VersionOne = Annotated[int, Field(ge=1, le=1)]
ShortText = Annotated[str, Field(min_length=1, max_length=128)]
AssetKind = Literal["raw_image", "display_image", "typed_table", "run_manifest", "analysis_result"]


def canonical_module_json(value: str) -> str:
    """Canonical bounded JSON object; duplicate keys/nonfinite numbers are never accepted."""

    def object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = item
        return result

    def constant(_value: str) -> object:
        raise ValueError("Nonfinite JSON number")

    if len(value.encode("utf-8")) > 1024 * 1024:
        raise ValueError("Module JSON exceeds its byte budget")
    try:
        parsed: object = json.loads(value, object_pairs_hook=object_pairs, parse_constant=constant)
        if not isinstance(parsed, dict):
            raise ValueError("Module payload must be a JSON object")
        pending: list[tuple[object, int]] = [(parsed, 0)]
        while pending:
            item, depth = pending.pop()
            if depth > 32:
                raise ValueError("Module JSON nesting exceeds 32 levels")
            if isinstance(item, dict):
                pending.extend(
                    (child, depth + 1) for child in cast(dict[str, object], item).values()
                )
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in cast(list[object], item))
        return json.dumps(
            parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
    except RecursionError as exc:
        raise ValueError("Module JSON nesting exceeds parser capacity") from exc


class ModulePort(FrozenContract):
    name: Identifier
    kind: AssetKind
    filename: Annotated[str, Field(max_length=128)] = ""

    @field_validator("filename")
    @classmethod
    def simple_output_name(cls, value: str) -> str:
        if value:
            validate_relative_path(value)
            if "/" in value:
                raise ValueError("An output port uses a simple filename")
        return value


class ModuleSpec(FrozenContract):
    schema_version: VersionOne = 1
    module_id: Identifier
    module_version: ShortText
    method_version: ShortText
    implementation_digest: Digest
    input_ports: Annotated[tuple[ModulePort, ...], Field(min_length=1, max_length=8)]
    output_ports: Annotated[tuple[ModulePort, ...], Field(min_length=1, max_length=16)]
    parameters_schema: Annotated[str, Field(min_length=2, max_length=65536)]

    @model_validator(mode="after")
    def unique_ports(self) -> Self:
        for ports in (self.input_ports, self.output_ports):
            if len({port.name for port in ports}) != len(ports):
                raise ValueError("Duplicate module port")
        if any(port.filename for port in self.input_ports):
            raise ValueError("Input ports do not dictate source filenames")
        if any(not port.filename for port in self.output_ports) or len(
            {port.filename for port in self.output_ports}
        ) != len(self.output_ports):
            raise ValueError("Output ports need distinct filenames")
        canonical_module_json(self.parameters_schema)
        return self


class BoundAsset(FrozenContract):
    port: Identifier
    kind: AssetKind
    asset: AssetRef


class RuntimeVersion(FrozenContract):
    name: Identifier
    version: ShortText


class ExecutionRequest(FrozenContract):
    schema_version: VersionOne = 1
    request_id: Identifier
    execution_id: Identifier
    node_id: Identifier
    attempt_id: Identifier
    document_id: Identifier
    revision: NonNegative
    module: ModuleSpec
    inputs: Annotated[tuple[BoundAsset, ...], Field(min_length=1, max_length=8)]
    parameters_json: Annotated[str, Field(min_length=2, max_length=1048576)]
    parameters_sha256: Digest
    environment: Annotated[tuple[RuntimeVersion, ...], Field(min_length=1, max_length=32)]

    @model_validator(mode="after")
    def frozen_binding(self) -> Self:
        expected = {port.name: port.kind for port in self.module.input_ports}
        actual = {item.port: item.kind for item in self.inputs}
        if actual != expected or len(actual) != len(self.inputs):
            raise ValueError("Input ports and scientific roles must match the module")
        if len({item.name for item in self.environment}) != len(self.environment):
            raise ValueError("Duplicate runtime component")
        if canonical_module_json(self.parameters_json) != self.parameters_json:
            raise ValueError("Parameters must be frozen as canonical JSON")
        if (
            hashlib.sha256(self.parameters_json.encode("utf-8")).hexdigest()
            != self.parameters_sha256
        ):
            raise ValueError("Frozen parameters digest mismatch")
        return self


class OutputManifest(FrozenContract):
    schema_version: VersionOne = 1
    run_id: Identifier
    request: ExecutionRequest
    publication: Literal["candidate", "committed"]
    outputs: Annotated[tuple[BoundAsset, ...], Field(min_length=1, max_length=16)]
    quality: Literal["complete", "issues"]
    summary_json: Annotated[str, Field(min_length=2, max_length=65536)]

    @model_validator(mode="after")
    def required_outputs(self) -> Self:
        expected = {port.name: port for port in self.request.module.output_ports}
        actual = {item.port: item for item in self.outputs}
        if set(actual) != set(expected) or len(actual) != len(self.outputs):
            raise ValueError("Manifest must contain every required output exactly once")
        if len({item.asset.asset_id for item in self.outputs}) != len(self.outputs):
            raise ValueError("Each output requires a distinct physical asset")
        for name, item in actual.items():
            if item.kind != expected[name].kind or item.asset.size_bytes == 0:
                raise ValueError("Output role or size is invalid")
            if (
                self.publication == "candidate"
                and item.asset.relative_path != expected[name].filename
            ):
                raise ValueError("Candidate output filename differs from its frozen port")
        if canonical_module_json(self.summary_json) != self.summary_json:
            raise ValueError("Output summary must be canonical JSON")
        return self


class ExecutionIdentity(FrozenContract):
    run_id: Identifier
    request_id: Identifier
    execution_id: Identifier
    node_id: Identifier
    attempt_id: Identifier
    document_id: Identifier
    revision: NonNegative


class ExecutionEvent(FrozenContract):
    protocol_version: VersionOne = 1
    kind: Literal["hello", "accepted", "result", "failure", "cancelled"]
    sequence: Annotated[int, Field(ge=0, le=2)]
    identity: ExecutionIdentity | None = None
    manifest: OutputManifest | None = None
    reason: Annotated[str, Field(max_length=1024)] = ""

    @model_validator(mode="after")
    def event_shape(self) -> Self:
        expected_sequence = 0 if self.kind == "hello" else 1 if self.kind == "accepted" else 2
        if self.sequence != expected_sequence or (self.kind == "hello") != (self.identity is None):
            raise ValueError("Event sequence/identity mismatch")
        if (self.kind == "result") != (self.manifest is not None):
            raise ValueError("Only a result event contains a candidate manifest")
        if (self.kind == "failure") != bool(self.reason):
            raise ValueError("Only failure carries a mandatory reason")
        if self.manifest is not None:
            request = self.manifest.request
            identity = ExecutionIdentity(
                run_id=self.manifest.run_id,
                request_id=request.request_id,
                execution_id=request.execution_id,
                node_id=request.node_id,
                attempt_id=request.attempt_id,
                document_id=request.document_id,
                revision=request.revision,
            )
            if self.manifest.publication != "candidate" or identity != self.identity:
                raise ValueError("Result event must bind the same uncommitted attempt")
        return self


__all__ += [
    "ModulePort",
    "ModuleSpec",
    "BoundAsset",
    "RuntimeVersion",
    "ExecutionRequest",
    "OutputManifest",
    "ExecutionIdentity",
    "ExecutionEvent",
    "canonical_module_json",
]
