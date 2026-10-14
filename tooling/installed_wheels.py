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
            [
                "uv",
                "sync",
                "--locked",
                "--package",
                "wb-tool",
                "--no-dev",
                "--no-install-workspace",
            ],
            cwd=ROOT,
            env={
                **{key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"},
                "UV_PROJECT_ENVIRONMENT": str(environment),
            },
            check=False,
        ).returncode
        if code:
            return code
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
from wb_tool.api import BandBounds, Baseline, LaneROI, compute_lane_profiles, integrate_profile
import numpy as np
import wb_tool.api
assert Path(wb_tool.api.__file__).is_relative_to(Path(sys.prefix))
assert integrate_profile([10., 20., 10.], BandBounds(0, 2)).signal == 10.
assert integrate_profile([8., 8.], BandBounds(0, 1), Baseline(0, 0)).signal == 8.
pixels = np.array([[245], [235], [245]], dtype=np.uint8)
assert compute_lane_profiles(pixels, LaneROI('L', 0, 0, 1, 3), 'dark').quantitative == (10.,20.,10.)
assert not any(name.startswith(('PySide6', 'sqlite3')) for name in sys.modules)
print('Isolated WB wheel: numerical/profile APIs passed; no GUI/storage dependencies')
"""
        return subprocess.run([str(python), "-I", "-c", script], cwd=folder, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
