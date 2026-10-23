"""Freeze and compare every shared frontend byte from source, wheel and installation."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree(root: Path) -> dict[str, str]:
    if not (root / "index.html").is_file():
        raise ValueError(f"Missing shared workbench: {root}")
    return {
        path.relative_to(root).as_posix(): digest(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--installed", type=Path)
    parser.add_argument("--captures", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = tree(args.source.resolve())
    comparisons: dict[str, object] = {}
    failed = False
    candidates: dict[str, dict[str, str]] = {}
    if args.wheel:
        prefix = "bioimage_app/web_ui/"
        with ZipFile(args.wheel) as archive:
            candidates["wheel"] = {
                name.removeprefix(prefix): digest(archive.read(name))
                for name in archive.namelist()
                if name.startswith(prefix) and not name.endswith("/")
            }
    if args.installed:
        candidates["installed"] = tree(args.installed.resolve())
    for label, values in candidates.items():
        missing = sorted(set(source) - set(values))
        extra = sorted(set(values) - set(source))
        changed = sorted(key for key in source.keys() & values.keys() if source[key] != values[key])
        equal = not (missing or extra or changed)
        failed |= not equal
        comparisons[label] = {
            "equal": equal,
            "missing": missing,
            "extra": extra,
            "changed": changed,
        }
    captures: dict[str, object] = {}
    for folder in args.captures:
        captures[str(folder)] = {
            p.name: digest(p.read_bytes())
            for p in sorted(folder.iterdir())
            if p.suffix in {".png", ".mp4", ".json"}
        }
    report = {
        "schema_version": 1,
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source": str(args.source.resolve()),
        "fixture": "index.html?preview=1; preview_adapter.js SHA256 included below",
        "defaults": {"theme": "forest", "density": "comfortable", "motion": "expressive"},
        "files": source,
        "comparisons": comparisons,
        "captures": captures,
        "passed": not failed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"files": len(source), "comparisons": comparisons, "passed": not failed}))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
