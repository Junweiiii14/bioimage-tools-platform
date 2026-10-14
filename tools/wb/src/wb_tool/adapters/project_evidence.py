"""Re-read immutable run assets before exporting values; isolate invalid evidence by run."""

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from tool_contracts.api import AssetRef

from wb_tool.application.crop_suggestions import read_figure_project
from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_analysis import (
    LoadedProjectResult,
    WBAnalysisProject,
    read_project_result,
)
from wb_tool.application.project_archive import ArchiveRunEvidence, project_runs
from wb_tool.application.project_ocr import LoadedProjectOCR, WBProjectOCR, read_project_ocr_result


@dataclass(frozen=True)
class VerifiedProjectEvidence:
    results: tuple[LoadedProjectResult, ...]
    ocr: LoadedProjectOCR | None
    records: tuple[dict[str, object], ...]


def _read(path: str, asset: AssetRef, limit: int) -> bytes:
    if not path or asset.size_bytes > limit:
        raise ValueError("运行资产路径缺失或超过读取预算")
    with Path(path).open("rb") as file:
        data = file.read(limit + 1)
    if len(data) != asset.size_bytes or sha256(data).hexdigest() != asset.sha256:
        raise ValueError("运行资产字节数或SHA256不一致")
    return data


def verify_project_evidence(
    project: WBFigureProject,
    evidence: tuple[ArchiveRunEvidence, ...],
    *,
    cancelled: Callable[[], bool] = lambda: False,
    write: Callable[[str, bytes, str], None] = lambda name, data, role: None,
) -> VerifiedProjectEvidence:
    supplied = {e.run.run_id: e for e in evidence}
    if len(supplied) != len(evidence):
        raise ValueError("重复提供运行证据")
    results: list[LoadedProjectResult] = []
    loaded_ocr: LoadedProjectOCR | None = None
    records: list[dict[str, object]] = []
    loaded_size = 0
    plans = (
        {p.run.run_id: p for p in project.analyses if p.run}
        if isinstance(project, WBAnalysisProject)
        else {}
    )
    for index, run in enumerate(project_runs(project), 1):
        if cancelled():
            raise ValueError("结果证据校验已取消")
        prefix = f"runs/{index:04d}"
        record: dict[str, object] = {
            "run_id": run.run_id,
            "state": run.state,
            "record": prefix + "/run.json",
            "request": None,
            "result": None,
            "verification": "unavailable",
            "reason": "",
        }
        records.append(record)
        write(prefix + "/run.json", run.model_dump_json().encode(), "declared_run_record")
        entry = supplied.get(run.run_id)
        result: LoadedProjectResult | LoadedProjectOCR | None = None
        request_data, result_data = b"", b""
        try:
            if entry is None or entry.run != run:
                raise ValueError("未提供与工作区匹配的运行证据")
            if entry.error:
                raise ValueError(entry.error)
            request_data = _read(entry.request_path, run.request, 16 * 1024 * 1024)
            frozen = read_figure_project(request_data)
            if frozen.project_id != run.document_id or frozen.revision != run.revision:
                raise ValueError("冻结请求项目/修订不匹配")
            plan = plans.get(run.run_id)
            if plan:
                old = (
                    next((p for p in frozen.analyses if p.row_id == plan.row_id), None)
                    if isinstance(frozen, WBAnalysisProject)
                    else None
                )
                if old is None or old.request != plan.request:
                    raise ValueError("冻结请求不对应当前定量运行")
            elif not (
                isinstance(frozen, WBProjectOCR)
                and frozen.ocr
                and isinstance(project, WBProjectOCR)
                and project.ocr
                and frozen.ocr.source == project.ocr.source
            ):
                raise ValueError("冻结请求不对应OCR来源")
            if run.result is not None:
                if loaded_size + run.result.size_bytes > 64 * 1024 * 1024:
                    raise ValueError("已载入结果超过64MiB预算，未导出该结果数值")
                result_data = _read(entry.result_path, run.result, 8 * 1024 * 1024)
                if plan:
                    result = read_project_result(plan, result_data)
                elif isinstance(project, WBProjectOCR):
                    result = read_project_ocr_result(project, run, result_data)
                    if project.ocr is None or result.recognition != project.ocr.recognition:
                        raise ValueError("保存的OCR识别副本与资产不一致")
                loaded_size += len(result_data)
        except (ValueError, OSError, TypeError) as error:
            record["reason"] = str(error)
            continue
        # Only verified bytes are included. Writing failures abort the whole publication.
        write(prefix + "/request.json", request_data, "frozen_project_request")
        record["request"] = prefix + "/request.json"
        record["verification"] = "verified_result" if result else "terminal_without_result"
        record["reason"] = run.reason or ""
        if result_data:
            write(prefix + "/result.json", result_data, "original_result_asset")
            record["result"] = prefix + "/result.json"
        if isinstance(result, LoadedProjectResult):
            results.append(result)
        elif isinstance(result, LoadedProjectOCR):
            loaded_ocr = result
    return VerifiedProjectEvidence(tuple(results), loaded_ocr, tuple(records))
