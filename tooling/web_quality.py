"""Run locked development-only web checks from the existing repository gate."""

import shutil
import subprocess
from pathlib import Path


def main() -> int:
    node = shutil.which("node")
    if node is None:
        print("Missing Node; install the version in .node-version, then npm ci --ignore-scripts")
        return 1
    root = Path(__file__).resolve().parents[1]
    return subprocess.run([node, "tooling/check_web.cjs"], cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
