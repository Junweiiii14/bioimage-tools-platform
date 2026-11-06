"""Research templates retain scientific inputs and use the existing real worker."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import tifffile
from bioimage_app.workflow_authoring_store import execute_authoring_store
from platform_runtime.api import Workspace
from tool_contracts.api import WorkflowEdge

from tests.test_workflow_authoring_store import payload

EXAMPLES = Path(__file__).parents[1] / "tools/bca/examples"


def plate_at(root: Path, name: str) -> tuple[str, str]:
    source, record = root / f"{name}.csv", root / f"{name}.json"
    source.write_bytes(
        (EXAMPLES / "synthetic.csv").read_bytes().replace(b",S1,", f",{name},".encode())
    )
    metadata = json.loads((EXAMPLES / "record.json").read_text(encoding="utf-8"))
    metadata["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    record.write_text(json.dumps(metadata), encoding="utf-8")
    return str(source), str(record)


@pytest.mark.parametrize("tool", ["nuclei", "bca"])
def test_research_template_rebind_and_invalid_connections(tmp_path: Path, tool: str) -> None:
    if tool == "bca":
        source, record = plate_at(tmp_path, "first")
        other, other_record = plate_at(tmp_path, "second")
    else:
        source, other = str(tmp_path / "first.tif"), str(tmp_path / "second.tif")
        tifffile.imwrite(source, np.zeros((20, 25), dtype=np.uint8))
        tifffile.imwrite(other, np.ones((21, 26), dtype=np.uint8))
        record = other_record = ""
    template = tmp_path / "template.json"
    with Workspace.create(tmp_path / "workspace") as store:
        first = execute_authoring_store(
            store,
            payload(
                "initialize",
                "editor",
                tool=tool,
                source_paths=(source,),
                record_path=record,
            ),
        )
        assert first.plan is not None and not first.issues
        assert first.project.schema_version == 2
        execute_authoring_store(store, payload("export", "editor", destination=str(template)))
        # Connect a result back to source: a real graph edit cannot bypass scientific checks.
        node = first.project.graph.nodes[0]
        second = node.model_copy(update={"node_id": "second"})
        bad = first.project.graph.model_copy(
            update={
                "nodes": (node, second),
                "edges": (
                    WorkflowEdge(
                        source_node=node.node_id,
                        source_port="provenance",
                        target_node="second",
                        target_port="source",
                    ),
                ),
            }
        )
        rejected = execute_authoring_store(
            store,
            payload(
                "save",
                "editor",
                previous_revision=0,
                graph=bad,
                layout=first.project.layout,
            ),
        )
        assert rejected.plan is None
        assert any(i.node_id == "second" for i in rejected.issues)
        if tool == "nuclei":
            with pytest.raises(ValueError, match="运行环境未配置"):
                execute_authoring_store(
                    store,
                    payload(
                        "freeze",
                        "editor",
                        previous_revision=1,
                        graph=first.project.graph,
                        layout=first.project.layout,
                    ),
                )
    with Workspace.create(tmp_path / "reused") as store:
        reused = execute_authoring_store(
            store,
            payload(
                "initialize",
                "editor",
                tool=tool,
                source_paths=(other,),
                record_path=other_record,
                template_path=str(template),
            ),
        )
        assert reused.plan is not None and not reused.issues
        assert reused.project.sources[0].asset != first.project.sources[0].asset
        assert reused.project.layout == first.project.layout
        if tool == "bca":
            assert reused.project.sources[0].record != first.project.sources[0].record
        loaded = execute_authoring_store(store, payload("load", "editor"))
        assert loaded.project == reused.project


def test_bca_requires_matching_explicit_record(tmp_path: Path) -> None:
    source, _record = plate_at(tmp_path, "new")
    with Workspace.create(tmp_path / "workspace") as store, pytest.raises(ValueError):
        execute_authoring_store(
            store,
            payload(
                "initialize",
                "editor",
                tool="bca",
                source_paths=(source,),
                record_path=str(EXAMPLES / "record.json"),
            ),
        )


def test_legacy_editor_is_read_only_until_explicit_save(tmp_path: Path) -> None:
    with Workspace.create(tmp_path / "workspace") as store:
        created = execute_authoring_store(
            store, payload("initialize", "editor", validation_cases=("triangle_u8",))
        )
        legacy = created.project.model_dump(mode="json")
        legacy["document_id"] = "legacy"
        legacy["schema_version"] = 1
        legacy.pop("tool")
        for source in legacy["sources"]:
            source.pop("record")
        raw = json.dumps(legacy).encode()
        store.save_draft("legacy", "workflow_authoring_v1", 0, raw, expected_previous_revision=None)
        loaded = execute_authoring_store(store, payload("load", "legacy"))
        assert loaded.project.schema_version == 1 and loaded.project.tool == "wb"
        assert store.read_asset(store.load_draft("legacy").asset) == raw
        saved = execute_authoring_store(
            store,
            payload(
                "save",
                "legacy",
                previous_revision=0,
                graph=loaded.project.graph,
                layout=loaded.project.layout,
            ),
        )
        assert saved.project.schema_version == 2
        assert saved.plan is not None and loaded.plan is not None
        assert saved.plan.nodes == loaded.plan.nodes
