"""Check declared API boundaries, including the real contracts/runtime/WB packages.

See docs/architecture.md; Import Linter also checks transitive dependencies.
"""

from __future__ import annotations

import ast
from pathlib import Path

MODULES: dict[str, tuple[str, frozenset[str]]] = {
    "tool_contracts": ("packages/tool_contracts/src", frozenset()),
    "platform_runtime": ("packages/platform_runtime/src", frozenset({"tool_contracts"})),
    "desktop_sdk": ("packages/desktop_sdk/src", frozenset({"tool_contracts"})),
    "imaging_core": ("packages/imaging_core/src", frozenset({"tool_contracts"})),
    "imaging_ui": (
        "packages/imaging_ui/src",
        frozenset({"imaging_core", "desktop_sdk", "tool_contracts"}),
    ),
    "wb_tool": (
        "tools/wb/src",
        frozenset({"tool_contracts", "imaging_core", "desktop_sdk", "imaging_ui"}),
    ),
}
GUI = {"PySide6", "PyQt6", "PyQt5", "tkinter"}
DOMAIN_IO = GUI | {"sqlite3", "subprocess", "multiprocessing", "logging"}


def violations(source: str, module: str, filename: str = "<source>") -> list[str]:
    """Return direct import violations, resolving relative imports before checking."""
    owner = module.split(".")[0]
    if owner not in MODULES:
        return [f"{filename}: unregistered source owner {owner}"]
    allowed = MODULES[owner][1]
    problems: list[str] = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        imports: list[str] = []
        line = 0
        if isinstance(node, ast.Import):
            line = node.lineno
            imports = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            line = node.lineno
            target = node.module or ""
            if node.level:
                parent = module.split(".")[: -node.level]
                target = ".".join([*parent, *([target] if target else [])])
            imports = [f"{target}.{alias.name}" for alias in node.names]
        elif isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Name) and func.id == "__import__") or (
                isinstance(func, ast.Attribute) and func.attr == "import_module"
            ):
                problems.append(f"{filename}:{node.lineno}: dynamic import outside app registry")
        for target in imports:
            dependency = target.split(".")[0]
            reason = ""
            if dependency in MODULES and dependency != owner:
                if dependency not in allowed:
                    reason = f"{owner} must not import {dependency}"
                elif not target.startswith(f"{dependency}.api") or (
                    len(target.split(".")) > 1 and target.split(".")[1] != "api"
                ):
                    reason = f"use {dependency}.api, not package internals"
            if (
                owner in {"tool_contracts", "platform_runtime", "imaging_core"}
                and dependency in GUI
            ):
                reason = f"{owner} must be independent of GUI"
            if owner == "tool_contracts" and dependency in {"numpy", "scipy", "sqlite3"}:
                reason = "contracts must not import numerical or storage implementations"
            if ".domain." in module:
                if dependency in DOMAIN_IO or target.startswith(
                    (f"{owner}.ui", f"{owner}.adapters", f"{owner}.application")
                ):
                    reason = "domain must not depend on UI, application or I/O"
                if dependency in MODULES and dependency not in {owner, "imaging_core"}:
                    reason = "domain may only use its own data and pure imaging API"
            if ".application." in module and (
                dependency in GUI or target.startswith((f"{owner}.ui", f"{owner}.adapters"))
            ):
                reason = "application must depend on ports, not UI or concrete adapters"
            if reason:
                problems.append(f"{filename}:{line}: {reason}")
    return problems


def check_repository(root: Path) -> tuple[int, list[str]]:
    count = 0
    errors: list[str] = []
    registered = {(root / folder).resolve() for folder, _ in MODULES.values()}
    for category in ("packages", "tools"):
        for folder in (root / category).glob("*/src"):
            if folder.resolve() not in registered:
                errors.append(f"{folder.relative_to(root)}: register package boundary before use")
    for owner, (folder, _) in MODULES.items():
        src = root / folder
        for path in src.rglob("*.py"):
            count += 1
            module = ".".join(path.relative_to(src).with_suffix("").parts)
            if module.split(".")[0] != owner:
                errors.append(f"{path.relative_to(root)}: source root must contain {owner}")
                continue
            errors.extend(violations(path.read_text(encoding="utf-8"), module, str(path)))
    return count, errors
