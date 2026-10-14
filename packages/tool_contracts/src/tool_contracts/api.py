"""Immutable contracts for local assets, document revisions and host-owned runs."""

import re
from typing import Annotated, Literal, Self

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
