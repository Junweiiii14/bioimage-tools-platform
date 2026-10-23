"""Build the full, independently named Windows candidate and its per-user installer."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def icon(output: Path) -> None:
    from PIL import Image
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    source = ROOT / "apps/desktop/src/bioimage_app/web_ui/bioimage.svg"
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    QSvgRenderer(str(source)).render(painter)
    painter.end()
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    Image.frombytes("RGBA", (rgba.width(), rgba.height()), bytes(rgba.constBits())).save(
        output, format="ICO", sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)]
    )


def licenses(output: Path) -> None:
    output.mkdir()
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name", "unknown").replace("/", "_")
        for member in dist.files or ():
            if not any(
                part.lower().startswith(("license", "copying", "notice")) for part in member.parts
            ):
                continue
            original = Path(str(dist.locate_file(member)))
            if original.is_file() and original.stat().st_size <= 1024 * 1024:
                destination = output / name / member.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, destination)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.is_file():
        shutil.copyfile(python_license, output / "Python-LICENSE.txt")
    supplements = ROOT / "tooling/third_party_notices"
    provenance = supplements / "sources.json"
    for notice in json.loads(provenance.read_text(encoding="utf-8"))["licenses"]:
        name = notice["distribution"]
        if importlib.metadata.version(name) != notice["version"]:
            raise RuntimeError(f"Supplemental license version mismatch: {name}")
        source = supplements / notice["file"]
        if digest(source) != notice["sha256"]:
            raise RuntimeError(f"Supplemental license digest mismatch: {name}")
        destination = output / name / "UPSTREAM-LICENSE.txt"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    shutil.copyfile(provenance, output / "supplemental-sources.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iscc", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / ".local/releases")
    args = parser.parse_args()
    if sys.platform != "win32" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise RuntimeError("This installer targets Windows x64")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise RuntimeError("Commit the source before creating a traceable candidate")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    output = args.output.resolve() / ("candidate-" + commit[:12])
    output.mkdir(parents=True, exist_ok=False)
    app_icon = output / "bioimage.ico"
    icon(app_icon)
    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--mode=standalone",
        "--enable-plugin=pyside6",
        "--include-qt-plugins=sensible",
        "--include-package=bioimage_app",
        "--include-package=wb_tool",
        "--include-package=platform_runtime",
        "--include-package=tool_contracts",
        # RapidOCR selects its inference backend dynamically at runtime.
        "--include-package=rapidocr",
        "--include-package=onnxruntime",
        "--include-package-data=rapidocr",
        "--include-distribution-metadata=rapidocr",
        "--include-distribution-metadata=onnxruntime",
        "--nofollow-import-to=pytest,hypothesis,IPython,notebook,matplotlib,torch,paddle,tensorflow,openvino",
        "--mingw64",
        "--assume-yes-for-downloads",
        "--jobs=2",
        "--python-flag=isolated",
        "--windows-console-mode=hide",
        "--output-filename=BioImageWB-Candidate.exe",
        "--company-name=BioImage Tools",
        "--product-name=BioImage WB Candidate",
        "--file-version=0.14.0.47",
        f"--windows-icon-from-ico={app_icon}",
        f"--output-dir={output}",
        f"--report={output / 'compilation-report.xml'}",
        f"--include-data-dir={ROOT / 'apps/desktop/src/bioimage_app/web_ui'}=bioimage_app/web_ui",
        str(ROOT / "tooling/candidate_entry.py"),
    ]
    environment = dict(os.environ, PROCESSOR_ARCHITECTURE="AMD64")
    environment["NUITKA_CACHE_DIR"] = str(Path.home() / ".cache/bioimage-nuitka")
    started = time.monotonic()
    print("Building", output, flush=True)
    with (output / "build.log").open("w", encoding="utf-8") as stream:
        code = subprocess.run(
            command, cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=False
        ).returncode
    manifest: dict[str, object] = {
        "schema": 1,
        "commit": commit,
        "channel": "candidate",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "uv_lock_sha256": digest(ROOT / "uv.lock"),
        "command": command,
        "compile_exit": code,
        "elapsed_seconds": time.monotonic() - started,
    }
    manifest_path = output / "build-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if code:
        print("Compile failed:", output / "build.log", flush=True)
        return code
    dist = output / "candidate_entry.dist"
    shutil.copyfile(app_icon, dist / "bioimage.ico")
    licenses(dist / "third-party-licenses")
    subprocess.run(
        [
            "git",
            "archive",
            "--format=zip",
            f"--output={dist / 'source-code.zip'}",
            commit,
            "apps",
            "packages",
            "tools",
            "tooling",
            "pyproject.toml",
            "uv.lock",
            "dev.py",
        ],
        cwd=ROOT,
        check=True,
    )
    shutil.copyfile(manifest_path, dist / "build-manifest.json")
    installer_command = [
        str(args.iscc.resolve()),
        f"/DAppSource={dist}",
        f"/DBuildCommit={commit[:12]}",
        f"/DInstallerOutput={output}",
        str(ROOT / "tooling/windows_candidate.iss"),
    ]
    with (output / "installer.log").open("w", encoding="utf-8") as stream:
        code = subprocess.run(
            installer_command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False
        ).returncode
    manifest["installer_exit"] = code
    manifest["installer_command"] = installer_command
    manifest["artifacts"] = {
        p.name: {"sha256": digest(p), "size": p.stat().st_size} for p in output.glob("*-Setup.exe")
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(output, "installer exit", code, flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
