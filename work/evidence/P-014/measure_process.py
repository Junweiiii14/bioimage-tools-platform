"""Measure an isolated child process tree; output directories must be new."""

import argparse
import json
import os
import platform
import subprocess
import time
from pathlib import Path

import psutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("record", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.root.resolve()
    args.record.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.update(
        APPDATA=str(root / "appdata"),
        LOCALAPPDATA=str(root / "localappdata"),
        TEMP=str(root / "temp"),
        TMP=str(root / "temp"),
        PROCESSOR_ARCHITECTURE=platform.machine(),
    )
    peak, samples, pids = 0, 0, set()
    start = time.perf_counter()
    with (
        (args.record / "stdout.txt").open("xb") as stdout,
        (args.record / "stderr.txt").open("xb") as stderr,
    ):
        child = subprocess.Popen(
            args.command,
            env=env,
            stdout=stdout,
            stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        process = psutil.Process(child.pid)
        while child.poll() is None:
            rss = 0
            try:
                members = [process, *process.children(recursive=True)]
            except psutil.NoSuchProcess:
                members = []
            for member in members:
                try:
                    rss += member.memory_info().rss
                    pids.add(member.pid)
                except psutil.NoSuchProcess:
                    pass
            peak = max(peak, rss)
            samples += 1
            time.sleep(0.05)
        code = child.wait()
    report = dict(
        command=args.command,
        exit_code=code,
        wall_seconds=time.perf_counter() - start,
        sampled_tree_peak_rss_bytes=peak,
        sample_interval_seconds=0.05,
        samples=samples,
        observed_pids=sorted(pids),
        memory_definition="Maximum sampled sum of live process-tree RSS; may miss brief peaks; "
        "shared pages may be counted more than once. Observer excluded.",
    )
    (args.record / "process.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report), flush=True)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
