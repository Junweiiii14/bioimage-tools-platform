"""Build a traceable Windows standalone folder from a clean committed checkout."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> int:
    if sys.platform != "win32":
        raise RuntimeError("This P0 build recipe targets Windows x64")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise RuntimeError("Commit changes before building; source manifest must be reproducible")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    output = ROOT / ".local" / "p0" / f"build-{commit[:12]}"
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment["PROCESSOR_ARCHITECTURE"] = "AMD64"
    environment["NUITKA_CACHE_DIR"] = str(Path.home() / ".cache" / "bioimage-nuitka")
    args = [
        sys.executable,
        "-m",
        "nuitka",
        "--mode=standalone",
        "--enable-plugin=pyside6",
        "--include-qt-plugins=platforms,styles",
        "--include-module=scipy.ndimage",
        "--nofollow-import-to=pygments",
        # Explicit P0-only dependency scope, verified by the fixed workload. SciPy's
        # dynamic top-level imports otherwise pull unrelated experimental subpackages.
        "--nofollow-import-to=scipy.cluster,scipy.constants,scipy.datasets,scipy.differentiate",
        "--nofollow-import-to=scipy.fft,scipy.fftpack,scipy.integrate,scipy.interpolate",
        "--nofollow-import-to=scipy.io,scipy.odr,scipy.optimize,scipy.signal,scipy.sparse",
        "--nofollow-import-to=scipy.spatial,scipy.stats",
        "--mingw64",
        "--assume-yes-for-downloads",
        "--jobs=2",
        "--windows-console-mode=hide",
        "--output-filename=BioimageP0.exe",
        f"--output-dir={output}",
        f"--report={output / 'compilation-report.xml'}",
        str(ROOT / "p0_probe.py"),
    ]
    started = time.perf_counter()
    with (output / "build.log").open("w", encoding="utf-8") as stream:
        code = subprocess.run(
            args, cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=False
        ).returncode
    manifest: dict[str, object] = {
        "commit": commit,
        "uv_lock_sha256": sha(ROOT / "uv.lock"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("Nuitka", "PySide6", "numpy", "scipy", "tifffile", "pydantic")
        },
        "command": args,
        "exit_code": code,
        "elapsed_seconds": time.perf_counter() - started,
        "artifacts": {
            p.relative_to(output).as_posix(): sha(p)
            for p in sorted((output / "p0_probe.dist").rglob("*"))
            if p.is_file()
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(output, "exit", code, flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
