"""Offline checks for source preservation and pinned skill provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TypedDict, cast

from tooling.boundaries import check_repository

PLAN = "生物图像工具平台与全AI长期迭代技术方案.pdf"
PLAN_SHA256 = "b1d20b1f9ecc08ca6d7531a1ca35cce33f8fec5f4a982f61d207ab3d0010de49"


class Skill(TypedDict):
    name: str
    repository: str
    commit: str
    source_path: str
    tree_sha256: str


class Manifest(TypedDict):
    skills: list[Skill]


def tree_digest(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*"), key=lambda item: item.relative_to(folder).as_posix()):
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(path.relative_to(folder).as_posix().encode("utf-8") + b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def check(root: Path) -> list[str]:
    errors: list[str] = []
    if hashlib.sha256((root / PLAN).read_bytes()).hexdigest() != PLAN_SHA256:
        errors.append("Initial PDF changed; preserve it and add a separately versioned revision")
    if (root / "AGENTS.md").stat().st_size > 8192:
        errors.append("AGENTS.md exceeds the 8 KiB project budget; move detail to linked docs")
    manifest = cast(
        Manifest, json.loads((root / "tooling/skills-lock.json").read_text(encoding="utf-8"))
    )
    skill_root = root / ".agents/skills"
    recorded = {skill["name"] for skill in manifest["skills"]}
    actual = {p.parent.name for p in skill_root.glob("*/SKILL.md")}
    if recorded != actual:
        errors.append("Skill inventory differs from tooling/skills-lock.json")
    for skill in manifest["skills"]:
        if tree_digest(skill_root / skill["name"]) != skill["tree_sha256"]:
            errors.append(f"Skill source changed without review: {skill['name']}")
        if len(skill["commit"]) != 40:
            errors.append(f"Skill must be pinned to a full commit: {skill['name']}")
    count, boundary_errors = check_repository(root)
    errors.extend(boundary_errors)
    print(f"Product boundary scan: {count} files; zero means product is not implemented")
    return errors
