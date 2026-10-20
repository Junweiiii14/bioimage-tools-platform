"""Read-only candidate scan; textual reachability is not a runtime deletion proof."""

import ast
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[3]
tracked = subprocess.check_output(
    ["rg", "--files", "-g", "*.py", "-g", "*.json", "-g", "*.md"],
    cwd=root,
    text=True,
    encoding="utf-8",
).splitlines()
text = "\n".join(
    (root / path).read_text(encoding="utf-8-sig", errors="replace")
    for path in tracked
    if ".agents" not in Path(path).parts
)
bodies: dict[str, list[str]] = defaultdict(list)
single_reference: list[str] = []
private_count = 0
files = 0
for path in (root / "tools/wb/src/wb_tool").rglob("*.py"):
    if "ui" in path.parts or "wbquant143" in path.parts:
        continue
    files += 1
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        address = f"{path.relative_to(root).as_posix()}:{node.lineno}:{node.name}"
        if node.name.startswith("_"):
            private_count += 1
            if len(re.findall(r"\b" + re.escape(node.name) + r"\b", text)) == 1:
                single_reference.append(address)
        if node.end_lineno is None or node.end_lineno - node.lineno < 4:
            continue
        body = node.body
        if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            body = body[1:]
        key = ast.dump(ast.Module(body=body, type_ignores=[]), include_attributes=False)
        bodies[key].append(address)
print(
    json.dumps(
        {
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip(),
            "files": files,
            "private_top_level_functions": private_count,
            "single_textual_reference_candidates": single_reference,
            "identical_body_candidates": [group for group in bodies.values() if len(group) > 1],
            "limits": "No UI/vendor scan, name collisions can hide dead code, "
            "public/dynamic/compat "
            "consumers require separate review; no source is modified.",
        },
        ensure_ascii=False,
        indent=2,
    )
)
