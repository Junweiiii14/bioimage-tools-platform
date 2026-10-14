"""Build product wheels and exercise separate installed tool/runtime environments."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def installed_check(folder: Path, package: str, wheels: list[Path], script: str) -> int:
    environment = folder / package
    code = subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment)], cwd=ROOT, check=False
    ).returncode
    if code:
        return code
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    code = subprocess.run(
        [
            "uv",
            "sync",
            "--locked",
            "--package",
            package,
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
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            "--no-deps",
            *(str(wheel) for wheel in wheels),
        ],
        cwd=folder,
        check=False,
    ).returncode
    if code:
        return code
    return subprocess.run([str(python), "-I", "-c", script], cwd=folder, check=False).returncode


WB_SCRIPT = """
import sys
from pathlib import Path
from wb_tool.api import (
    AnalysisRequest, BandAnnotation, BandBounds, Baseline, LaneAnnotation, LaneROI,
    analyze_annotations, compute_lane_profiles, integrate_profile, load_tiff,
    StartFrame, WorkerConversation, encode_worker_frame, ResultFrame,
)
import numpy as np
import tifffile
import subprocess
import wb_tool.api
assert Path(wb_tool.api.__file__).is_relative_to(Path(sys.prefix))
assert integrate_profile([10., 20., 10.], BandBounds(0, 2)).signal == 10.
assert integrate_profile([8., 8.], BandBounds(0, 1), Baseline(0, 0)).signal == 8.
pixels = np.array([[245], [235], [245]], dtype=np.uint8)
assert compute_lane_profiles(pixels, LaneROI('L', 0, 0, 1, 3), 'dark').quantitative == (10.,20.,10.)
tifffile.imwrite('analytic.tif', pixels)
image = load_tiff('analytic.tif')
lane = LaneAnnotation(LaneROI('L', 0, 0, 1, 3), (BandAnnotation('B', BandBounds(0, 2)),))
request = AnalysisRequest(image.sha256, 7, 'dark', (lane,))
result = analyze_annotations(image, request)
assert result.lanes[0].bands[0].signal == 10 and result.request.revision == 7
start = StartFrame(protocol_version=1, kind='start', sequence=0, run_id='r',
                  attempt_id='a', request_id='q', source_path=str(Path('analytic.tif').resolve()),
                  request=request)
worker = subprocess.run([sys.executable, '-I', '-m', 'wb_tool.worker'],
                        input=encode_worker_frame(start), capture_output=True, timeout=30)
assert worker.returncode == 0, worker.stderr
frames = worker.stdout.splitlines()
assert len(frames) == 3
session = WorkerConversation(start)
received = [session.accept(data) for data in frames]
assert isinstance(received[-1], ResultFrame)
assert received[-1].result.lanes[0].bands[0].signal == 10
assert not any(name.startswith(('PySide6', 'sqlite3')) for name in sys.modules)
print('Isolated WB wheel: TIFF/manual analysis and real worker passed; no GUI/storage dependencies')
"""

RUNTIME_SCRIPT = """
import importlib.util
import os
import sys
import subprocess
from pathlib import Path
from hashlib import sha256
from platform_runtime.api import Workspace
from tool_contracts.api import ProcessExitReceipt
import platform_runtime.api
import tool_contracts.api
assert Path(platform_runtime.api.__file__).is_relative_to(Path(sys.prefix))
assert Path(tool_contracts.api.__file__).is_relative_to(Path(sys.prefix))
assert importlib.util.find_spec('wb_tool') is None
assert importlib.util.find_spec('numpy') is None
source = Path('asset.bin')
source.write_bytes(b'immutable input')
with Workspace.create('installed-workspace') as store:
    ref = store.import_asset(source, sha256(source.read_bytes()).hexdigest())
    assert store.read_asset(ref) == b'immutable input'
    store.save_draft('D', 'probe', 0, b'{}', expected_previous_revision=None)
    run = store.prepare_run('D')
    child = subprocess.Popen([sys.executable, '-I', '-c', 'pass'])
    store.start_run(run.run_id, child.pid)
    code = child.wait(timeout=10)
    completed = store.commit_result(run.run_id,
        ProcessExitReceipt(run_id=run.run_id, pid=child.pid, exit_code=code), b'{}')
    assert completed.state == 'succeeded'
with Workspace.open('installed-workspace') as store:
    assert store.get_run(run.run_id) == completed
assert not any(name.startswith(('wb_tool', 'PySide6', 'numpy')) for name in sys.modules)
print('Isolated runtime/contracts wheels: immutable input, run commit/reopen; no tool/GUI/numerics')
"""


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bioimage-wheel-") as temporary:
        folder = Path(temporary)
        wheel_dir = folder / "wheels"
        packages = ("wb-tool", "tool-contracts", "platform-runtime")
        built: dict[str, Path] = {}
        for package in packages:
            code = subprocess.run(
                ["uv", "build", "--package", package, "--wheel", "--out-dir", str(wheel_dir)],
                cwd=ROOT,
                check=False,
            ).returncode
            if code:
                return code
            wheels = list(wheel_dir.glob(package.replace("-", "_") + "-*.whl"))
            if len(wheels) != 1:
                raise RuntimeError(f"Expected one built wheel for {package}")
            built[package] = wheels[0]
        for package, wheels, script in (
            (
                "platform-runtime",
                [built["tool-contracts"], built["platform-runtime"]],
                RUNTIME_SCRIPT,
            ),
            ("wb-tool", [built["wb-tool"]], WB_SCRIPT),
        ):
            code = installed_check(folder, package, wheels, script)
            if code:
                return code
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
