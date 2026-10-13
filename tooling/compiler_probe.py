"""Install Nuitka's supported compiler if needed and compile a non-product probe."""

from __future__ import annotations

import os
import subprocess
import sys
import sysconfig
from pathlib import Path


def main() -> int:
    if sysconfig.get_platform() != "win-amd64":
        print("This compiler probe is defined only for Windows x64")
        return 2
    root = Path(__file__).resolve().parents[1]
    folder = root / ".local/compiler-probe"
    folder.mkdir(parents=True, exist_ok=True)
    source = folder / "probe.py"
    source.write_text('print("bioimage-compiler-ok")\n', encoding="utf-8")
    environment = os.environ.copy()
    # Codex may omit this Windows variable; SCons expects it even on a verified x64 host.
    environment.setdefault("PROCESSOR_ARCHITECTURE", "AMD64")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "nuitka",
            "--mingw64",
            "--assume-yes-for-downloads",
            "--jobs=2",
            f"--output-dir={folder}",
            str(source),
        ],
        cwd=root,
        env=environment,
        check=False,
    )
    if result.returncode:
        return result.returncode
    probe = subprocess.run(
        [str(folder / "probe.exe")], capture_output=True, text=True, timeout=30, check=False
    )
    print(probe.stdout.strip())
    if probe.returncode or probe.stdout.strip() != "bioimage-compiler-ok":
        print(probe.stderr)
        return 1
    print("Compiler probe passed; this is not a standalone Qt product validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
