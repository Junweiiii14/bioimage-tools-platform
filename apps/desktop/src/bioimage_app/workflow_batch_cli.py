"""Command-line adapter for the shared finite-batch controller."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from platform_runtime.api import (
    Workspace,
    WorkspaceError,
    load_workflow_ledger,
)
from PySide6.QtCore import QCoreApplication
from tool_contracts.api import canonical_module_json

from bioimage_app.wb_workflow_batch_input import (
    WBWorkflowBatchInput,
    WBWorkflowBatchInputs,
    prepare_wb_batch_rerun,
    prepare_wb_batch_workspace,
)
from bioimage_app.wb_workflow_host import wb_workflow_registry
from bioimage_app.workflow_batch_session import WorkflowBatchSession, WorkflowBatchStatus
from bioimage_app.workflow_template import load_workflow_template


def run_workflow_batch_cli(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Run a finite batch through the same workflow engine"
    )
    parser.add_argument("--workspace", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest")
    group.add_argument(
        "--validation",
        action="append",
        choices=("triangle_u8", "triangle_u16", "flat_zero", "invalid_roi", "dtype_limits"),
    )
    group.add_argument("--resume", metavar="BATCH_ID")
    group.add_argument("--rerun", metavar="BATCH_ID")
    parser.add_argument("--template")
    parser.add_argument("--template-out")
    parser.add_argument(
        "--layout",
        choices=("comfortable", "compact"),
    )
    args = parser.parse_args(arguments)
    if args.resume and (args.layout or args.template or args.template_out):
        parser.error("Use a new batch to adjust frozen plans")
    workspace = Path(args.workspace).resolve()
    batch = None
    try:
        if not args.resume:
            template = None
            if args.template:
                with Path(args.template).open("rb") as stream:
                    template = load_workflow_template(
                        stream.read(1048577).decode("utf-8")
                    ).definition
            if args.rerun:
                batch = prepare_wb_batch_rerun(
                    workspace,
                    args.rerun,
                    layout=args.layout,
                    template=template,
                    template_out=Path(args.template_out) if args.template_out else None,
                )
            else:
                if args.manifest:
                    manifest = Path(args.manifest).resolve()
                    with manifest.open("rb") as stream:
                        raw = stream.read(1048577)
                    inputs = WBWorkflowBatchInputs.model_validate_json(
                        canonical_module_json(raw.decode("utf-8")), strict=True
                    )
                    relative_to = manifest.parent
                else:
                    inputs = WBWorkflowBatchInputs(
                        samples=tuple(
                            WBWorkflowBatchInput(sample_id=f"sample_{i + 1}", validation=case)
                            for i, case in enumerate(args.validation)
                        )
                    )
                    relative_to = Path.cwd()
                batch = prepare_wb_batch_workspace(
                    workspace,
                    inputs,
                    relative_to=relative_to,
                    layout=args.layout,
                    template=template,
                    template_out=Path(args.template_out) if args.template_out else None,
                )
    except (ValueError, OSError, WorkspaceError) as error:
        print(json.dumps({"state": "input_failed", "error": str(error)}), file=sys.stderr)
        return 2
    app = QCoreApplication.instance() or QCoreApplication([sys.argv[0]])
    session = WorkflowBatchSession(wb_workflow_registry)
    final: WorkflowBatchStatus | None = None
    resumed = False

    def changed(status: WorkflowBatchStatus) -> None:
        nonlocal resumed
        print(json.dumps({"kind": "progress", **asdict(status)}), flush=True)
        if args.resume and not resumed and status.phase == "awaiting_resume":
            resumed = session.resume()

    def completed(_status: WorkflowBatchStatus) -> None:
        session.close()

    def finished(status: WorkflowBatchStatus) -> None:
        nonlocal final
        final = status
        app.quit()

    session.changed.connect(changed)
    session.completed.connect(completed)
    session.finished.connect(finished)
    if args.resume:
        session.reopen(str(workspace), args.resume)
    else:
        assert batch is not None
        session.start(str(workspace), batch)
    app.exec()
    assert final is not None
    samples: list[dict[str, object]] = []
    try:
        with Workspace.open(workspace) as store:
            actual = session.batch
            if actual is not None:
                for item in actual.items:
                    outputs: dict[str, str] = {}
                    if item.child_revision is not None:
                        child = load_workflow_ledger(
                            store.read_asset(store.load_draft(item.execution_id).asset).decode()
                        )
                        selected = {result.node_id: result for result in child.results}
                        for output in child.plan.outputs:
                            if output.node_id in selected:
                                ref = next(
                                    p.asset
                                    for p in selected[output.node_id].outputs
                                    if p.port == output.port
                                )
                                outputs[output.name] = str(store.asset_path(ref))
                    samples.append(
                        {
                            "sample_id": item.sample_id,
                            "state": item.state,
                            "execution_id": item.execution_id,
                            "reason": item.reason,
                            "outputs": outputs,
                        }
                    )
    except (ValueError, OSError, WorkspaceError) as error:
        print(json.dumps({"state": "verification_failed", "error": str(error)}), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {"kind": "finished", **asdict(final), "workspace": str(workspace), "samples": samples}
        ),
        flush=True,
    )
    return (0 if final.state == "completed" else 1) if not final.message else 2
