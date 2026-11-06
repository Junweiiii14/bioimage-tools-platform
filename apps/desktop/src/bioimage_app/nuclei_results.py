"""Background-only loading/export of the existing committed workflow artifacts."""

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from nuclei_tool.api import NucleiDisplay, present_nuclei_result, read_nuclei_input
from platform_runtime.api import (
    Workspace,
    load_workflow_ledger,
    validate_workflow_result_selection,
)
from tool_contracts.api import OutputManifest


@dataclass(frozen=True)
class NucleiResult:
    workspace: str
    execution_id: str
    run_id: str
    source_sha256: str
    display: NucleiDisplay
    labels: bytes
    provenance: bytes


def read_result(workspace: str) -> NucleiResult:
    with Workspace.open(workspace) as store:
        journals = [d for d in store.list_documents() if d.tool_id == "workflow_journal_v1"]
        if len(journals) != 1:
            raise ValueError("请选择单图核分割项目目录")
        draft = journals[0]
        ledger = load_workflow_ledger(store.read_asset(draft.asset).decode("utf-8"))
        if (ledger.execution_id, ledger.revision) != (draft.document_id, draft.revision):
            raise ValueError("运行记录与保存的项目身份不一致")
        if ledger.state != "succeeded" or len(ledger.results) != 1 or len(ledger.plan.nodes) != 1:
            raise ValueError("该项目没有已完成的单图结果；可选择原图重试")
        result = ledger.results[0]
        run = store.get_run(result.run.run_id)
        if run.result is None:
            raise ValueError("结果尚未完整提交")
        manifest = OutputManifest.model_validate_json(store.read_asset(run.result))
        validate_workflow_result_selection(ledger, ledger.plan.nodes[0], result, run, manifest)
        if store.read_asset(run.request) != manifest.request.model_dump_json().encode():
            raise ValueError("保存的请求与结果不一致")
        if len(manifest.request.inputs) != 1:
            raise ValueError("该结果不是单图核分割结果")
        source = read_nuclei_input(str(store.asset_path(manifest.request.inputs[0].asset)))
        outputs = {item.port: item.asset for item in result.outputs}
        if set(outputs) != {"labels", "provenance"}:
            raise ValueError("核分割结果资产不完整")
        labels = store.read_asset(outputs["labels"])
        provenance = store.read_asset(outputs["provenance"])
        display = present_nuclei_result(source, labels, provenance, manifest.request)
        return NucleiResult(
            workspace, ledger.execution_id, run.run_id, source.sha256, display, labels, provenance
        )


def export_result(result: NucleiResult, parent: str) -> str:
    """Publish a new directory only when every member is written; never reuse old files."""
    root = Path(parent).resolve()
    workspace = Path(result.workspace).resolve()
    if root == workspace or root.is_relative_to(workspace):
        raise ValueError("请选择项目目录之外的导出位置，以保留项目原始资产")
    suffix = uuid4().hex[:12]
    staging = root / (".nuclei-export-" + suffix)
    destination = root / ("核分割结果-" + suffix)
    staging.mkdir()
    table = io.StringIO(newline="")
    writer = csv.writer(table)
    writer.writerow(["nuclei_count", "source_sha256", "execution_id", "run_id", "method", "status"])
    writer.writerow(
        [
            result.display.count,
            result.source_sha256,
            result.execution_id,
            result.run_id,
            "stardist-fluo-p014@1",
            "research_not_scientifically_admitted",
        ]
    )
    members = {
        "count.csv": table.getvalue().encode("utf-8-sig"),
        "original-display.png": result.display.original_png,
        "outlines-display.png": result.display.overlay_png,
        "labels.npy": result.labels,
        "provenance.json": result.provenance,
        "README.txt": (
            "研究结果，科学适用性尚待独立验证。\n"
            "两个 PNG 仅用于显示；labels.npy 为原像素坐标 uint32 实例 ID，0 为背景。\n"
            "核数与来源见 count.csv，完整方法与请求见 provenance.json。\n"
        ).encode(),
        "export.json": json.dumps(
            {
                "schema_version": 1,
                "execution_id": result.execution_id,
                "run_id": result.run_id,
                "source_sha256": result.source_sha256,
            },
            ensure_ascii=False,
        ).encode("utf-8"),
    }
    for name, data in members.items():
        with (staging / name).open("xb") as stream:
            stream.write(data)
    staging.rename(destination)
    return str(destination)
