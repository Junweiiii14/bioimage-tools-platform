"""Small command entry point for repository governance; no product orchestration."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from tooling.policy import check

ROOT = Path(__file__).resolve().parent


def run_module(*args: str) -> int:
    print("RUN", sys.executable, "-m", *args, flush=True)
    environment = os.environ.copy()
    if args[0] in {"pytest", "tooling.installed_wheels"}:
        environment["QT_QPA_PLATFORM"] = "offscreen"
    return subprocess.run(
        [sys.executable, "-m", *args], cwd=ROOT, env=environment, check=False
    ).returncode


def doctor() -> int:
    packages = ["ruff", "pyright", "pytest", "import-linter", "hypothesis", "pre-commit"]
    versions: dict[str, str] = {}
    for name in packages:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "MISSING"
    result = {
        "python": platform.python_version(),
        "expected_python": (ROOT / ".python-version").read_text().strip(),
        "platform": platform.platform(),
        "packages": versions,
        "product_status": "wb-workbench-development; validation status is task-specific",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int("MISSING" in versions.values() or result["python"] != result["expected_python"])


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "context":
        from tooling.rule_context import main as context_main

        return context_main(["load", *sys.argv[2:]])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["doctor", "policy", "check", "smoke-env", "audit", "context"]
    )
    parser.add_argument("--all", action="store_true", help="run all currently implemented checks")
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor()
    if args.command == "smoke-env":
        return run_module("tooling.smoke_environment")
    if args.command == "audit":
        return run_module("pip_audit", "--local", "--progress-spinner", "off")
    errors = check(ROOT)
    for error in errors:
        print("ERROR", error)
    if errors or args.command == "policy":
        return int(bool(errors))
    for command in [
        ("ruff", "check", "."),
        ("ruff", "format", "--check", "."),
        ("pyright",),
        ("tooling.import_contracts",),
        ("pytest", "-q"),
        ("tooling.installed_wheels",),
    ]:
        code = run_module(*command)
        if code:
            return code
    print("Governance and automated probe checks passed; desktop/package evidence is separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
