"""Opt-in GDB observation of one owned Linux child, including final native faults."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_with_native_debugger(command: list[str], *, cwd: Path, env: dict[str, str]) -> int:
    """Preserve normal exit codes and a nonzero exit when the child dies by signal."""
    if sys.platform != "linux":
        raise ValueError("Native debugger requires Linux")
    import resource

    debugger = shutil.which("gdb")
    if debugger is None:
        raise RuntimeError("Native debugger unavailable")
    previous = resource.getrlimit(resource.RLIMIT_CORE)
    resource.setrlimit(resource.RLIMIT_CORE, (0, previous[1]))
    try:
        code = subprocess.run(
            [
                debugger,
                "--batch",
                "-nx",
                "--return-child-result",
                "-iex",
                "set auto-load off",
                "-iex",
                "set debuginfod enabled off",
                "-x",
                str(ROOT / "tooling/native_crash.gdb"),
                "--args",
                *command,
            ],
            cwd=cwd,
            env=env,
            check=False,
        ).returncode
    finally:
        resource.setrlimit(resource.RLIMIT_CORE, previous)
    print(f"Observed debugger exit={code}", flush=True)
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    controls = {
        "zero": "raise SystemExit(0)",
        "seventeen": "raise SystemExit(17)",
        "fault": "import os,signal; os.kill(os.getpid(),signal.SIGSEGV)",
    }
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--probe", action="store_true")
    action.add_argument("--control", choices=controls)
    args = parser.parse_args()
    if args.control:
        return run_with_native_debugger(
            [sys.executable, "-I", "-c", controls[args.control]], cwd=ROOT, env=dict(os.environ)
        )
    for name, expected in (("zero", 0), ("seventeen", 17), ("fault", None)):
        result = subprocess.run(
            [sys.executable, "-m", "tooling.linux_native_run", "--control", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stdout, end="", flush=True)
        print(result.stderr, end="", file=sys.stderr, flush=True)
        if expected is not None:
            if result.returncode != expected:
                return 1
        elif result.returncode == 0 or any(
            marker not in result.stdout
            for marker in ("NATIVE_FAULT signal=SIGSEGV", "Program terminated with signal SIGSEGV")
        ):
            return 1
    print("Native debugger controls: exit0, exit17, SIGSEGV failure verified", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
