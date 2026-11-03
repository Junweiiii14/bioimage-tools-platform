"""Real CLI input isolation and saved-graph binding to a different second batch."""

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

from platform_runtime.api import (
    Workspace,
    load_workflow_definition,
    load_workflow_ledger,
    workflow_definition_json,
)
from tool_contracts.api import (
    WorkflowEdge,
    WorkflowInput,
    WorkflowNode,
    WorkflowOutput,
    canonical_module_json,
)


class SampleReport(TypedDict):
    sample_id: str
    state: str
    execution_id: str
    reason: str | None
    outputs: dict[str, str]


class BatchReport(TypedDict):
    kind: str
    batch_id: str
    state: str
    succeeded: int
    issues: int
    failed: int
    samples: list[SampleReport]


def run_batch(workspace: Path, *arguments: str, expected: int = 0) -> BatchReport:
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "bioimage_app",
            "--workflow-batch",
            "--workspace",
            str(workspace),
            *arguments,
        ],
        capture_output=True,
        timeout=60,
    )
    assert process.returncode == expected, (process.stdout, process.stderr)
    report = cast(BatchReport, json.loads(process.stdout.splitlines()[-1]))
    assert report["kind"] == "finished"
    return report


def test_saved_branched_template_binds_second_raw_input_without_overwriting_first(
    tmp_path: Path,
) -> None:
    first_workspace = tmp_path / "first"
    template_path = tmp_path / "template.json"
    first = run_batch(
        first_workspace, "--validation", "triangle_u16", "--template-out", str(template_path)
    )
    first_table = Path(first["samples"][0]["outputs"]["measurements"])
    original_table = first_table.read_bytes()
    assert (
        list(csv.DictReader(original_table.decode("utf-8-sig").splitlines()))[0]["value"]
        == "4000.0"
    )
    definition = load_workflow_definition(template_path.read_text(encoding="utf-8"))
    analysis = next(n for n in definition.nodes if n.module.module_id == "wb-analyze-original")
    raw = json.loads(analysis.parameters_json)
    raw["polarity"] = "dark"
    alternate = analysis.model_copy(
        update={
            "node_id": "analysis_branch",
            "parameters_json": canonical_module_json(json.dumps(raw)),
        }
    )
    branched = definition.model_copy(
        update={
            "nodes": (*definition.nodes, alternate),
            "edges": (
                *definition.edges,
                WorkflowEdge(
                    source_node="verify",
                    source_port="validation",
                    target_node=alternate.node_id,
                    target_port="validation",
                ),
            ),
            "inputs": (
                *definition.inputs,
                WorkflowInput(
                    node_id=alternate.node_id, port="source", asset=definition.inputs[0].asset
                ),
            ),
            "outputs": (
                *definition.outputs,
                WorkflowOutput(
                    name="alternate_analysis", node_id=alternate.node_id, port="analysis"
                ),
            ),
        }
    )
    branch_path = tmp_path / "branched-template.json"
    branch_path.write_text(workflow_definition_json(branched), encoding="utf-8")
    second_workspace = tmp_path / "second"
    second = run_batch(
        second_workspace, "--validation", "triangle_u8", "--template", str(branch_path)
    )
    assert first["state"] == second["state"] == "completed"
    assert first["batch_id"] != second["batch_id"]
    sample = second["samples"][0]
    assert len(sample["outputs"]) == 5 and Path(sample["outputs"]["alternate_analysis"]).is_file()
    rows = list(
        csv.DictReader(
            Path(sample["outputs"]["measurements"]).read_text(encoding="utf-8-sig").splitlines()
        )
    )
    assert rows[0]["value"] == "40.0" and rows[0]["status"] == "text:valid"
    assert first_table.read_bytes() == original_table
    with Workspace.open(second_workspace) as store:
        child = load_workflow_ledger(
            store.read_asset(store.load_draft(sample["execution_id"]).asset).decode()
        )
        order = [attempt.node_id for attempt in child.attempts]
        assert len(order) == 4 and len(store.list_runs()) == 4
        for edge in branched.edges:
            assert order.index(edge.source_node) < order.index(edge.target_node)
        assert all(store.get_run(a.run.run_id).pid for a in child.attempts if a.run is not None)
        bound = next(i.asset for n in child.plan.nodes for i in n.inputs if i.asset is not None)
        assert bound.payload.sha256 != definition.inputs[0].asset.payload.sha256


def test_manifest_reports_missing_input_invalid_roi_and_real_zero_separately(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "inputs.json"
    manifest.write_text(
        json.dumps(
            {
                "format": "wb_workflow_batch@1",
                "samples": [
                    {"sample_id": "missing", "source": "missing.tif", "parameters": "missing.json"},
                    {"sample_id": "zero", "validation": "flat_zero"},
                    {"sample_id": "invalid", "validation": "invalid_roi"},
                ],
            }
        ),
        encoding="utf-8",
    )
    report = run_batch(tmp_path / "batch", "--manifest", str(manifest), expected=1)
    assert report["state"] == "completed_with_issues"
    assert (report["failed"], report["issues"], report["succeeded"]) == (1, 1, 1)
    missing, zero, invalid = report["samples"]
    assert missing["state"] == "failed" and missing["reason"] and not missing["outputs"]
    zero_row = list(
        csv.DictReader(
            Path(zero["outputs"]["measurements"]).read_text(encoding="utf-8-sig").splitlines()
        )
    )[0]
    invalid_row = list(
        csv.DictReader(
            Path(invalid["outputs"]["measurements"]).read_text(encoding="utf-8-sig").splitlines()
        )
    )[0]
    assert zero_row["value"] == "0.0" and zero_row["status"] == "text:valid"
    assert invalid_row["value"] == "" and invalid_row["status"] == "text:invalid"


def test_batch_rerun_reuses_dependencies_and_isolates_corrupt_cache(tmp_path: Path) -> None:
    workspace = tmp_path / "batch"
    template_path = tmp_path / "template.json"
    initial = run_batch(
        workspace,
        "--validation",
        "triangle_u16",
        "--validation",
        "triangle_u8",
        "--template-out",
        str(template_path),
    )
    original_tables = {
        sample["outputs"]["measurements"]: Path(sample["outputs"]["measurements"]).read_bytes()
        for sample in initial["samples"]
    }
    with Workspace.open(workspace) as store:
        original_runs = store.list_runs()
        assert len(original_runs) == 6
    styled = run_batch(workspace, "--rerun", initial["batch_id"], "--layout", "compact")
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 8
        for sample in styled["samples"]:
            child = load_workflow_ledger(
                store.read_asset(store.load_draft(sample["execution_id"]).asset).decode()
            )
            assert [result.reused for result in child.results] == [True, True, False]
            assert len(child.attempts) == 1
    definition = load_workflow_definition(template_path.read_text(encoding="utf-8"))
    edited_nodes: list[WorkflowNode] = []
    for node in definition.nodes:
        if node.module.module_id == "wb-analyze-original":
            parameters = json.loads(node.parameters_json)
            parameters["polarity"] = "dark"
            node = node.model_copy(
                update={"parameters_json": canonical_module_json(json.dumps(parameters))}
            )
        edited_nodes.append(node)
    edited = definition.model_copy(update={"nodes": tuple(edited_nodes)})
    edited_path = tmp_path / "dark-template.json"
    edited_path.write_text(workflow_definition_json(edited), encoding="utf-8")
    changed = run_batch(workspace, "--rerun", styled["batch_id"], "--template", str(edited_path))
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 12
        for sample in changed["samples"]:
            child = load_workflow_ledger(
                store.read_asset(store.load_draft(sample["execution_id"]).asset).decode()
            )
            assert [result.reused for result in child.results] == [True, False, False]
            assert len(child.attempts) == 2
        first_child = load_workflow_ledger(
            store.read_asset(store.load_draft(changed["samples"][0]["execution_id"]).asset).decode()
        )
        damaged = first_child.results[1].outputs[0].asset
        store.asset_path(damaged).write_bytes(b"owned synthetic damaged cache")
    rejected = run_batch(workspace, "--rerun", changed["batch_id"], expected=1)
    assert rejected["state"] == "completed_with_issues"
    assert rejected["samples"][0]["state"] == "failed" and rejected["samples"][0]["reason"]
    assert not rejected["samples"][0]["outputs"]
    assert rejected["samples"][1]["state"] == "succeeded"
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 12
    repaired = run_batch(workspace, "--rerun", rejected["batch_id"])
    assert repaired["state"] == "completed"
    with Workspace.open(workspace) as store:
        assert len(store.list_runs()) == 14
        assert tuple(store.get_run(run.run_id) for run in original_runs) == original_runs
        assert (workspace / damaged.relative_path).read_bytes() == b"owned synthetic damaged cache"
    for sample in repaired["samples"]:
        row = list(
            csv.DictReader(
                Path(sample["outputs"]["measurements"]).read_text(encoding="utf-8-sig").splitlines()
            )
        )[0]
        assert row["value"] == "0.0" and row["status"] == "text:valid"
    assert all(Path(path).read_bytes() == data for path, data in original_tables.items())
