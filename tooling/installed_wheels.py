"""Build the WB wheel, install without dependencies, test outside the source tree."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bioimage-wheel-") as temporary:
        folder = Path(temporary)
        wheel_dir = folder / "wheels"
        environment = folder / "environment"
        commands = [
            ["uv", "build", "--package", "wb-tool", "--wheel", "--out-dir", str(wheel_dir)],
            ["uv", "venv", "--python", sys.executable, str(environment)],
        ]
        for command in commands:
            code = subprocess.run(command, cwd=ROOT, check=False).returncode
            if code:
                return code
        wheels = list(wheel_dir.glob("wb_tool-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected exactly one built WB wheel")
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        code = subprocess.run(
            ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheels[0])],
            cwd=folder,
            check=False,
        ).returncode
        if code:
            return code
        script = """
import sys
from pathlib import Path
from wb_tool.api import BandBounds, Baseline, integrate_profile
import wb_tool.api
assert Path(wb_tool.api.__file__).is_relative_to(Path(sys.prefix))
assert integrate_profile([10., 20., 10.], BandBounds(0, 2)).signal == 10.
assert integrate_profile([8., 8.], BandBounds(0, 1), Baseline(0, 0)).signal == 8.
assert not any(name.startswith(('PySide6', 'numpy', 'sqlite3')) for name in sys.modules)
print('Isolated installed WB wheel: numerical API passed, no GUI/numerical/storage dependencies')
"""
        return subprocess.run([str(python), "-I", "-c", script], cwd=folder, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
