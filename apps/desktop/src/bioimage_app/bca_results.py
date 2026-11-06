"""Read and export verified BCA commits without recomputing historical values."""

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from platform_runtime.api import Workspace, load_workflow_ledger

from bioimage_app.bca_cli import verified_outputs


@dataclass(frozen=True)
class BcaResult:
    workspace: str
    execution_id: str
    run_id: str
    source_sha256: str
    members: dict[str, bytes]

    def table(self, name: str) -> list[dict[str, str]]:
        return list(csv.DictReader(io.StringIO(self.members[name].decode("utf-8-sig"))))


def read_result(workspace: str) -> BcaResult:
    with Workspace.open(workspace) as store:
        journals = [d for d in store.list_documents() if d.tool_id == "workflow_journal_v1"]
        if len(journals) != 1:
            raise ValueError("请选择单板 BCA 项目目录")
        draft = journals[0]
        ledger = load_workflow_ledger(store.read_asset(draft.asset).decode())
        if (ledger.execution_id, ledger.revision) != (draft.document_id, draft.revision):
            raise ValueError("运行记录与项目身份不一致")
        if ledger.state != "succeeded":
            raise ValueError("该项目没有完整提交的 BCA 结果")
    paths = verified_outputs(Path(workspace), ledger)
    source = next(item.asset for item in ledger.plan.nodes[0].inputs if item.port == "source")
    assert source is not None
    return BcaResult(
        workspace,
        ledger.execution_id,
        ledger.results[0].run.run_id,
        source.payload.sha256,
        {name: Path(path).read_bytes() for name, path in paths.items()},
    )


def export_result(result: BcaResult, parent: str) -> str:
    # Recheck storage at export time too; never publish a stale in-memory success.
    result = read_result(result.workspace)
    root, workspace = Path(parent).resolve(), Path(result.workspace).resolve()
    if root == workspace or root.is_relative_to(workspace):
        raise ValueError("请选择项目目录之外的导出位置")
    suffix = uuid4().hex[:12]
    staging, destination = root / (".bca-export-" + suffix), root / ("BCA结果-" + suffix)
    staging.mkdir()
    members = {
        "wells.csv": result.members["wells"],
        "samples.csv": result.members["samples"],
        "provenance.json": result.members["provenance"],
    }
    members["export.json"] = json.dumps(
        {
            "execution_id": result.execution_id,
            "run_id": result.run_id,
            "source_sha256": result.source_sha256,
        }
    ).encode()
    for name, data in members.items():
        with (staging / name).open("xb") as stream:
            stream.write(data)
    staging.rename(destination)
    return str(destination)
