"""Bounded, manual Linux evidence for the unchanged web-host shutdown case."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "tests/test_web_bridge.py::test_local_page_channel_and_drain"
PREFIX = [
    "test_idle_publish_and_progress_do_not_rebuild_project_snapshot",
    "test_folder_report_is_visible_and_only_current_variant_can_be_added",
    "test_folder_report_cannot_cross_project_or_workspace",
    "test_web_adapter_real_import_output_and_original_coordinates",
    "test_web_adapter_rejects_unknown_busy_and_oversize",
]


def _parent(pid: int) -> int:
    # comm may contain spaces or parentheses; fields after its last ')' are fixed.
    return int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[1])


def observe(command: list[str], *, seconds: int) -> tuple[int, bool, str]:
    if sys.platform != "linux":
        raise RuntimeError("Linux only")
    debugger = shutil.which("gdb")
    if debugger is None:
        raise RuntimeError("Native debugger unavailable")
    with tempfile.TemporaryDirectory(prefix="bioimage-native-case-") as temporary:
        directory = Path(temporary)
        pid_file = directory / "owned.json"
        log_file = directory / "native.log"
        env = dict(
            os.environ, BIOIMAGE_NATIVE_PID_FILE=str(pid_file), BIOIMAGE_NATIVE_DIAGNOSTIC="1"
        )
        with log_file.open("wb") as output:
            child = subprocess.Popen(
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
                    str(ROOT / "tooling/native_owned_pid.gdb"),
                    "-x",
                    str(ROOT / "tooling/native_crash.gdb"),
                    "--args",
                    *command,
                ],
                cwd=ROOT,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            expired = False
            try:
                try:
                    child.wait(timeout=seconds)
                except subprocess.TimeoutExpired:
                    expired = True
                    owned = json.loads(pid_file.read_text())
                    inferior = int(owned["inferior"])
                    if (
                        owned["debugger"] != child.pid
                        or _parent(child.pid) != os.getpid()
                        or _parent(inferior) != child.pid
                    ):
                        raise RuntimeError("Owned inferior ancestry no longer matches") from None
                    print(f"OWNED_WATCHDOG debugger={child.pid} inferior={inferior}", flush=True)
                    os.kill(inferior, signal.SIGINT)
                    try:
                        child.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        print("NATIVE_CAPTURE_GRACE_EXPIRED", flush=True)
            finally:
                if child.poll() is None:
                    if os.getpgid(child.pid) != child.pid:
                        raise RuntimeError("Owned debugger process group no longer matches")
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                transcript = log_file.read_text(errors="replace")
                print(transcript, end="", flush=True)
                print(
                    f"NATIVE_CASE debugger_exit={child.returncode} deadline={expired}", flush=True
                )
        return child.returncode, expired, transcript


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("control", "target", "prefix"), required=True)
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("Linux only")
    if args.case == "control":
        command = [
            sys.executable,
            "-I",
            "-c",
            (
                "import os,signal,time; "
                "signal.signal(signal.SIGINT, lambda *_: os._exit(17)); "
                "print('EXTERNAL_CANCEL_READY',flush=True); time.sleep(60)"
            ),
        ]
        code, expired, transcript = observe(command, seconds=2)
        return (
            0
            if code == 17
            and expired
            and all(
                marker in transcript
                for marker in (
                    "EXTERNAL_CANCEL_READY",
                    "NATIVE_CANCEL signal=SIGINT",
                    "NATIVE_CAPTURE_COMPLETE signal=SIGINT",
                    "truncated=0",
                )
            )
            else 1
        )
    cases = [TARGET]
    if args.case == "prefix":
        cases = [f"tests/test_web_bridge.py::{name}" for name in PREFIX] + cases
    code, expired, _ = observe([sys.executable, "-m", "pytest", *cases], seconds=90)
    # A deadline can never become success even if SIGINT is caught and exits zero.
    return 124 if expired else code


if __name__ == "__main__":
    raise SystemExit(main())
