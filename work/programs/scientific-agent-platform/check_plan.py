"""Read-only plan integrity check; never grants execution or scientific approval."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = Path("work/programs/scientific-agent-platform/registry.json")
STATES = {"planned", "in_progress", "in_review", "blocked", "done"}


def path_in(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path outside root: {value}")
    if not path.is_file():
        raise ValueError(f"Missing file: {value}")
    return path


def acyclic(graph: dict[str, list[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node not in graph:
            raise ValueError(f"Unknown dependency: {node}")
        if node in visiting:
            raise ValueError(f"Dependency cycle: {node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def check(root: Path, redirected: bool = False) -> dict:
    registry = json.loads(path_in(root, str(REGISTRY)).read_text(encoding="utf-8-sig"))
    if registry["schema_version"] != 1:
        raise ValueError("Unknown registry schema")
    authority = registry.get("task_execution_root", ".")
    if authority != ".":
        if redirected:
            raise ValueError("Multiple state-authority redirects; repair pointer")
        target = Path(authority)
        if not target.is_absolute():
            raise ValueError("Transferred execution root must be absolute")
        result = check(target, redirected=True)
        result["source_plan_root"] = str(root)
        return result
    path_in(root, registry["plan_path"])
    work_packages = registry["work_packages"]
    wp_graph = {x["id"]: x["depends_on"] for x in work_packages}
    if len(wp_graph) != len(work_packages):
        raise ValueError("Duplicate work package ID")
    acyclic(wp_graph)
    tasks: dict[str, dict] = {}
    for entry in registry["tasks"]:
        if entry["id"] in tasks:
            raise ValueError(f"Duplicate task ID: {entry['id']}")
        content = path_in(root, entry["path"]).read_text(encoding="utf-8-sig")
        blocks = re.findall(r"<!-- PROGRAM_TASK_META (.*?) -->", content)
        if len(blocks) != 1:
            raise ValueError(f"Expected one task metadata block: {entry['id']}")
        metadata = json.loads(blocks[0])
        if metadata["id"] != entry["id"] or metadata["status"] not in STATES:
            raise ValueError(f"Invalid task metadata: {entry['id']}")
        if metadata["work_package"] not in wp_graph:
            raise ValueError(f"Unknown work package for {entry['id']}")
        if metadata["status"] in {"in_progress", "in_review", "done"}:
            execution = Path(metadata.get("execution_root", ""))
            if (
                not execution.is_absolute()
                or not isinstance(metadata.get("owner"), str)
                or not metadata["owner"].strip()
                or re.fullmatch(r"[0-9a-f]{40}", metadata.get("base_commit") or "") is None
            ):
                raise ValueError(f"Missing execution identity: {entry['id']}")
        if (
            metadata["status"] in {"in_review", "done"}
            and re.fullmatch(r"[0-9a-f]{40}", metadata.get("head_commit") or "") is None
        ):
            raise ValueError(f"Missing reviewed commit: {entry['id']}")
        tasks[entry["id"]] = metadata
    acyclic({key: value["depends_on"] for key, value in tasks.items()})
    for key, value in tasks.items():
        if value["status"] in {"in_progress", "in_review", "done"} and any(
            tasks[dep]["status"] != "done" for dep in value["depends_on"]
        ):
            raise ValueError(f"Active task has incomplete dependency: {key}")
    listed: list[str] = []
    for package in work_packages:
        for task_id in package["task_ids"]:
            if task_id not in tasks or tasks[task_id]["work_package"] != package["id"]:
                raise ValueError(f"Invalid task/work-package relation: {task_id}")
            listed.append(task_id)
    if len(listed) != len(set(listed)) or set(listed) != set(tasks):
        raise ValueError("Every task must be listed in exactly one work package")
    candidates = [
        key
        for key, value in tasks.items()
        if value["status"] == "planned"
        and all(tasks[d]["status"] == "done" for d in value["depends_on"])
    ]
    return {
        "result": "pass",
        "execution_root": str(root),
        "work_packages": len(work_packages),
        "task_states": {key: value["status"] for key, value in tasks.items()},
        "dependency_candidates": candidates,
        "limitations": (
            "Structural check only. Candidates are not permission, implementation, "
            "scientific admission, or user acceptance."
        ),
    }


if __name__ == "__main__":
    try:
        print(json.dumps(check(ROOT), ensure_ascii=False, indent=2))
    except (KeyError, ValueError, OSError, TypeError) as error:
        print(f"Plan check failed: {error}", file=sys.stderr)
        sys.exit(1)
