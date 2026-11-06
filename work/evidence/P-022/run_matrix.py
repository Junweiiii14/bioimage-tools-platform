"""One bounded author matrix, separate environments and persistent evidence."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
AREA = ROOT / ".local/p022-matrix-final"
AREA.mkdir(exist_ok=True)
WHEELS = AREA / "wheels"
BASE = ("tool-contracts", "platform-runtime", "bioimage-app")
ALL = (*BASE, "wb-tool", "nuclei-tool", "bca-tool")


def run(args, **kw):
    completed = subprocess.run(args, cwd=ROOT, **kw)
    if completed.returncode:
        raise RuntimeError((args, completed.returncode))


for package in ALL:
    run(["uv", "build", "--package", package, "--wheel", "--out-dir", str(WHEELS)])
built = {pkg: next(WHEELS.glob(pkg.replace("-", "_") + "-*.whl")) for pkg in ALL}
reports = {}
common = {
    "worker": str(ROOT.parent / "p015-research/worker-env/Scripts/python.exe"),
    "model": "C:/Users/70236/ResearchVault/Codex-Workbench/p014-research/models/2D_versatile_fluo",
    "image": str(ROOT.parent / "p014-research/evaluation-input/Ganglioneuroblastoma_10.tif"),
    "csv": str(ROOT / "tools/bca/examples/synthetic.csv"),
    "record": str(ROOT / "tools/bca/examples/record.json"),
}


def probe(name, python, **options):
    config = {**common, "name": "p022-v2-" + name, "output": str(AREA / name), **options}
    path = AREA / (name + ".json")
    path.write_text(json.dumps(config), encoding="utf-8")
    with (AREA / (name + ".log")).open("w", encoding="utf-8") as log:
        run(
            [str(python), "-I", str(ROOT / "work/evidence/P-022/desktop_probe.py"), str(path)],
            env={
                **os.environ,
                "PYTHONUTF8": "1",
                "QT_QPA_PLATFORM": "offscreen",
                "QTWEBENGINE_CHROMIUM_FLAGS": "--disable-gpu --disable-software-rasterizer",
            },
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    report = json.loads((AREA / name / "report.json").read_text(encoding="utf-8"))
    reports[name] = report
    print(name, "pass", flush=True)
    return report


for name, extras in [
    ("base", ()),
    ("wb", ("wb",)),
    ("nuclei", ("nuclei",)),
    ("bca", ("bca",)),
    ("all", ("wb", "nuclei", "bca")),
]:
    env = AREA / (name + "-env")
    run(["uv", "venv", "--python", sys.executable, str(env)])
    python = env / "Scripts/python.exe"
    run(
        [
            "uv",
            "sync",
            "--locked",
            "--package",
            "bioimage-app",
            "--no-dev",
            "--no-install-workspace",
            *[arg for extra in extras for arg in ("--extra", extra)],
        ],
        env={
            **{k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"},
            "UV_PROJECT_ENVIRONMENT": str(env),
        },
    )
    run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            "--no-deps",
            *[str(built[pkg]) for pkg in (*BASE, *(key + "-tool" for key in extras))],
        ]
    )
    bytes_ = sum(p.stat().st_size for p in env.rglob("*") if p.is_file())
    result = probe(
        name, python, run_tools=list(extras), **({"toggle": "wb"} if name == "all" else {})
    )
    result["environment_logical_bytes"] = bytes_
    if extras:
        probe(name + "-reopen", python, reopen=result["runs"])
    if name == "nuclei":
        probe("model-missing", python, worker="", model="", missing_model=True)
    if name == "all":
        probe(
            "disabled",
            python,
            disabled=["wb"],
            run_tools=["bca"],
            unavailable_history=[result["runs"][0]],
        )
        run(["uv", "pip", "uninstall", "--python", str(python), "wb-tool"])
        probe(
            "removed",
            python,
            run_tools=["bca"],
            reopen=[result["runs"][1]],
            unavailable_history=[result["runs"][0]],
        )
(AREA / "matrix.json").write_text(
    json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
)
