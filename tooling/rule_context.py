"""Print applicable rules and reject missing, stale or incomplete PR context receipts.

A receipt proves the loader ran for a set of rule bytes, not model comprehension.
Only the standard library and Git are needed, including in a fresh CI checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import TypedDict, cast

CORE = (
    "AGENTS.md",
    "docs/module-map.md",
    "docs/architecture.md",
    "docs/coding-standards.md",
    "docs/ai-workflow.md",
    "docs/research-protocol.md",
    "docs/runbooks/rule-enforcement.md",
)
RECOVERY = (
    "AGENT_HANDOFF.md",
    ".agent-handoff/snapshot.md",
    ".agent-handoff/risks.md",
    ".agent-handoff/backlog.md",
)
ROOT = Path(__file__).resolve().parents[1]


class Receipt(TypedDict):
    schema: int
    task: str
    base_commit: str
    scopes: list[str]
    rules: dict[str, str]
    base_rules: dict[str, str]


class IntegrationContext(TypedDict):
    schema: int
    task: str
    base_commit: str
    source_head: str
    historical_receipts: dict[str, str]


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def revision(root: Path, ref: str) -> str:
    return git(root, "rev-parse", "--verify", ref + "^{commit}").decode().strip()


def paths(root: Path, ref: str | None) -> list[str]:
    data = (
        git(root, "ls-tree", "-rz", "--name-only", ref)
        if ref
        else git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    )
    return sorted(set(data.decode("utf-8").split("\0")) - {""})


def read(root: Path, path: str, ref: str | None) -> bytes:
    if ref:
        return git(root, "show", f"{ref}:{path}")
    file = root / path
    if not file.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Rule path escapes repository: {path}")
    return file.read_bytes()


def normalized(path: str) -> str:
    if not path or "\\" in path or ":" in path or path.startswith("/"):
        raise ValueError(f"Scope must be a repository-relative POSIX path: {path}")
    if ".." in PurePosixPath(path).parts:
        raise ValueError(f"Parent traversal is forbidden: {path}")
    return PurePosixPath(path).as_posix()


def covers(scope: str, path: str) -> bool:
    return scope == "." or path == scope or path.startswith(scope + "/")


def parse_scopes(value: object) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError("Receipt needs nonempty scopes")
    result: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str):
            raise ValueError("Each scope must be a string")
        result.append(normalized(item))
    return result


def selected_rules(root: Path, scopes: list[str], ref: str | None) -> list[str]:
    inventory = paths(root, ref)
    required: set[str] = set(CORE)
    # Include both instructions and overrides: shadowing must not silently remove rules.
    for path in inventory:
        p = PurePosixPath(path)
        if p.name not in {"AGENTS.md", "AGENTS.override.md"} or path.startswith(".agents/"):
            continue
        parent = p.parent.as_posix()
        if any(covers(parent, scope) or covers(scope, parent) for scope in scopes):
            required.add(path)
    for path in required:
        if path not in inventory:
            raise ValueError(f"Required rule file is missing: {path}")
    return sorted(required)


def fingerprints(root: Path, names: list[str], ref: str | None) -> dict[str, str]:
    # Newline normalization makes a working tree receipt portable to Git/CI LF bytes.
    return {
        name: hashlib.sha256(read(root, name, ref).replace(b"\r\n", b"\n")).hexdigest()
        for name in names
    }


def base_fingerprints(root: Path, scopes: list[str], base: str) -> dict[str, str]:
    # During the one-time bootstrap the old main may not contain the new core docs.
    inventory = paths(root, base)
    names = [p for p in CORE if p in inventory]
    names += [
        p
        for p in inventory
        if PurePosixPath(p).name in {"AGENTS.md", "AGENTS.override.md"}
        and not p.startswith(".agents/")
        and any(
            covers(PurePosixPath(p).parent.as_posix(), s)
            or covers(s, PurePosixPath(p).parent.as_posix())
            for s in scopes
        )
    ]
    return fingerprints(root, sorted(set(names)), base)


def make_receipt(root: Path, task: str, scopes: list[str], base: str) -> Receipt:
    if not re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]+", task):
        raise ValueError("Task ID must look like F-002 or T-001")
    scopes = sorted({normalized(s) for s in scopes})
    if not scopes:
        raise ValueError("At least one explicit scope is required")
    base = revision(root, base)
    return {
        "schema": 1,
        "task": task,
        "base_commit": base,
        "scopes": scopes,
        "rules": fingerprints(root, selected_rules(root, scopes, None), None),
        "base_rules": base_fingerprints(root, scopes, base),
    }


def changed_paths(root: Path, base: str, head: str) -> list[str]:
    return (
        git(root, "diff", "--name-only", "--no-renames", "-z", base, head).decode().split("\0")[:-1]
    )


def receipt_paths(names: list[str]) -> list[str]:
    return [
        p
        for p in names
        if re.fullmatch(r"work/evidence/[A-Z][A-Z0-9]*-[0-9]+/rules-context.json", p)
    ]


def check_receipt(root: Path, path: str, base: str, head: str, changed: list[str]) -> None:
    raw = json.loads(read(root, path, head))
    if not isinstance(raw, dict):
        raise ValueError("Receipt must be an object")
    receipt = cast(Receipt, raw)
    if receipt["schema"] != 1 or receipt["base_commit"] != base:
        raise ValueError("Receipt schema/base is stale; refresh after updating from main")
    task = receipt["task"]
    if task != PurePosixPath(path).parent.name:
        raise ValueError("Receipt task does not match its directory")
    scopes = parse_scopes(receipt["scopes"])
    uncovered = [p for p in changed if not any(covers(s, p) for s in scopes)]
    if uncovered:
        raise ValueError("Changed files outside loaded scope: " + ", ".join(uncovered))
    task_files = [p for p in paths(root, head) if p.startswith(f"work/tasks/{task}-")]
    if not task_files:
        raise ValueError("Task document is missing")
    expected = fingerprints(root, selected_rules(root, scopes, head), head)
    if receipt["rules"] != expected:
        raise ValueError("Head rules changed or nested rules were omitted; reload context")
    if receipt["base_rules"] != base_fingerprints(root, scopes, base):
        raise ValueError("Base rules were not loaded correctly")


def require_ancestor(root: Path, ancestor: str, head: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", ancestor):
        raise ValueError("Integration sources must be exact commit IDs")
    if subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, head],
        capture_output=True,
        check=False,
    ).returncode:
        raise ValueError("Integration source is not an ancestor of its recorded head")


def check_historical(root: Path, path: str, source: str, source_head: str, head: str) -> None:
    require_ancestor(root, source, source_head)
    if read(root, path, head) != read(root, path, source):
        raise ValueError("Historical receipt differs from its immutable source")
    raw = json.loads(read(root, path, source))
    if not isinstance(raw, dict):
        raise ValueError("Historical receipt must be an object")
    original_base = cast(dict[str, object], raw)["base_commit"]
    if not isinstance(original_base, str):
        raise ValueError("Historical receipt base must be a commit ID")
    require_ancestor(root, original_base, source)
    # Historical scopes describe an old rule-loading event, not the current PR's coverage.
    # Full coverage of this PR remains mandatory on its one current receipt below.
    check_receipt(root, path, original_base, source, [])


def make_integration_context(root: Path, task: str, base: str) -> IntegrationContext:
    base, source_head = revision(root, base), revision(root, "HEAD")
    current = f"work/evidence/{task}/rules-context.json"
    historical: dict[str, str] = {}
    for path in receipt_paths(changed_paths(root, base, source_head)):
        if path == current:
            continue
        if read(root, path, None).replace(b"\r\n", b"\n") != read(root, path, source_head):
            raise ValueError("Commit and verify historical receipt updates before integration")
        source = git(root, "log", "-1", "--format=%H", source_head, "--", path).decode().strip()
        check_historical(root, path, source, source_head, source_head)
        historical[path] = source
    return {
        "schema": 1,
        "task": task,
        "base_commit": base,
        "source_head": source_head,
        "historical_receipts": historical,
    }


def validate(root: Path, base: str, head: str) -> list[str]:
    base, head = revision(root, base), revision(root, head)
    changed = changed_paths(root, base, head)
    receipts = receipt_paths(changed)
    manifests = [
        p
        for p in changed
        if re.fullmatch(r"work/evidence/[A-Z][A-Z0-9]*-[0-9]+/integration-context.json", p)
    ]
    try:
        if not manifests:
            if len(receipts) != 1:
                raise ValueError(
                    "PR needs exactly one changed rules-context.json; "
                    "use an explicit integration context for preserved historical receipts"
                )
            check_receipt(root, receipts[0], base, head, changed)
        else:
            if len(manifests) != 1:
                raise ValueError("Integration needs exactly one changed integration context")
            raw = json.loads(read(root, manifests[0], head))
            if not isinstance(raw, dict):
                raise ValueError("Integration context must be an object")
            integration = cast(IntegrationContext, raw)
            task = PurePosixPath(manifests[0]).parent.name
            if (
                integration["schema"] != 1
                or integration["base_commit"] != base
                or integration["task"] != task
            ):
                raise ValueError("Integration context task/schema/base does not match this PR")
            current = f"work/evidence/{task}/rules-context.json"
            if current not in receipts:
                raise ValueError("Integration current receipt must be changed in this PR")
            historical_raw = cast(dict[str, object], raw)["historical_receipts"]
            if not isinstance(historical_raw, dict):
                raise ValueError("Integration historical receipts must be an object")
            historical = cast(dict[str, str], historical_raw)
            if set(historical) != set(receipts) - {current}:
                raise ValueError("Integration must list every extra historical receipt exactly")
            source_head = integration["source_head"]
            require_ancestor(root, source_head, head)
            if source_head == head:
                raise ValueError("Integration source head must precede its current receipt commit")
            for path, source in historical.items():
                check_historical(root, path, source, source_head, head)
            check_receipt(root, current, base, head, changed)
    except (KeyError, TypeError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        return [str(exc)]
    return []


def main(argv: list[str] | None = None) -> int:
    configure_output = getattr(sys.stdout, "reconfigure", None)
    if callable(configure_output):
        configure_output(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    load = sub.add_parser("load")
    load.add_argument("--task", required=True)
    load.add_argument("--scope", action="append", required=True)
    load.add_argument("--base", default="origin/main")
    load.add_argument("--record", action="store_true")
    load.add_argument(
        "--integration",
        action="store_true",
        help="explicitly verify and retain historical receipts",
    )
    verify = sub.add_parser("check")
    verify.add_argument("--base", required=True)
    verify.add_argument("--head", default="HEAD")
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            errors = validate(ROOT, args.base, args.head)
            for error in errors:
                print("ERROR", error)
            if not errors:
                print("Rule context receipt matches this PR's base, scope and rule versions")
            return int(bool(errors))
        receipt = make_receipt(ROOT, args.task, args.scope, args.base)
        integration = (
            make_integration_context(ROOT, args.task, args.base) if args.integration else None
        )
        task_files = [p for p in paths(ROOT, None) if p.startswith(f"work/tasks/{args.task}-")]
        if not task_files:
            raise ValueError("Create the task document before recording context")
        for name in [*receipt["rules"], *RECOVERY, *task_files]:
            print(f"\n--- {name} ---\n{read(ROOT, name, None).decode('utf-8')}")
        for name, digest in receipt["base_rules"].items():
            if receipt["rules"].get(name) != digest:
                previous = read(ROOT, name, receipt["base_commit"]).decode("utf-8")
                print(f"\n--- BASE {name} ---\n{previous}")
        if args.record:
            output = ROOT / "work/evidence" / args.task / "rules-context.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"\nRecorded {output.relative_to(ROOT)}")
            if integration is not None:
                integration_output = output.with_name("integration-context.json")
                integration_output.write_text(
                    json.dumps(integration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                print(f"Recorded {integration_output.relative_to(ROOT)}")
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print("ERROR", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
