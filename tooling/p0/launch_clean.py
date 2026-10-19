"""Launch a relocated portable GUI with a minimal environment; NOT a clean Windows VM."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from tooling.p0.build import sha


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--scale", type=float, help="Qt multiplier on native DPR, not OS scale")
    args = parser.parse_args()
    bundle: Path = args.bundle.resolve()
    evidence: Path = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    executable = bundle / "app/BioimageP0.exe"
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper()
        in {
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "LOCALAPPDATA",
            "APPDATA",
            "COMSPEC",
            "PATHEXT",
            "PROCESSOR_ARCHITECTURE",
            "NUMBER_OF_PROCESSORS",
        }
    }
    windows = os.environ["SYSTEMROOT"]
    environment["PATH"] = str(Path(windows) / "System32") + os.pathsep + windows
    if args.scale is not None:
        environment["QT_SCALE_FACTOR"] = str(args.scale)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    command = [str(executable), "--fixtures", str(bundle / "fixtures"), "--evidence", str(evidence)]
    with (
        (evidence / f"launch-{stamp}.stdout").open("xb") as stdout,
        (evidence / f"launch-{stamp}.stderr").open("xb") as stderr,
    ):
        process = subprocess.Popen(
            command, cwd=bundle, env=environment, stdout=stdout, stderr=stderr
        )
    record = {
        "pid": process.pid,
        "command": command,
        "cwd": str(bundle),
        "environment": environment,
        "exe_sha256": sha(executable),
        "scope": "local host with minimal child environment; Python remains installed on host",
    }
    (evidence / f"launch-{stamp}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"pid": process.pid, "evidence": str(evidence)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
