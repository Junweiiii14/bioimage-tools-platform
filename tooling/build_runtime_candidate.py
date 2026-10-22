"""Package locked product wheels with the same private relocatable CPython runtime."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from tooling.build_candidate import ROOT, digest, icon, licenses


def run(arguments: list[str], *, log: Path | None = None) -> None:
    if log is None:
        subprocess.run(arguments, cwd=ROOT, check=True)
    else:
        with log.open("w", encoding="utf-8") as stream:
            subprocess.run(arguments, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iscc", required=True, type=Path)
    parser.add_argument("--gcc", required=True, type=Path)
    profiles = parser.add_mutually_exclusive_group()
    profiles.add_argument(
        "--execution-test", action="store_true", help="Build the isolated E7 test distribution"
    )
    profiles.add_argument(
        "--grouped-intake-test",
        action="store_true",
        help="Build the isolated grouped-intake test distribution",
    )
    profiles.add_argument(
        "--fig-sequence-test",
        action="store_true",
        help="Build the isolated Fig sequence automation test distribution",
    )
    profiles.add_argument(
        "--automatic-flow-test",
        action="store_true",
        help="Build the isolated automatic crop/gray/results test distribution",
    )
    profiles.add_argument(
        "--supervision-test", action="store_true", help="Build T074 supervision test"
    )
    profiles.add_argument(
        "--reliable-crop-test",
        action="store_true",
        help="Build the isolated fixed-grid crop and redesigned workbench test distribution",
    )
    profiles.add_argument(
        "--ui-system-test", action="store_true", help="Build isolated UI system candidate"
    )
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise RuntimeError("A committed, clean checkout is required")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    output = ROOT / ".local/releases" / ("runtime-" + commit[:12])
    output.mkdir(parents=True, exist_ok=False)
    dist = output / "app"
    runtime = dist / "runtime"
    base = Path(sys.base_prefix)
    shutil.copytree(
        base, runtime, ignore=shutil.ignore_patterns("site-packages", "__pycache__", "*.pyc")
    )
    site = runtime / "Lib/site-packages"
    site.mkdir(parents=True, exist_ok=True)
    if any(site.iterdir()):
        raise RuntimeError("Base runtime must not contain installed third-party distributions")
    requirements = output / "requirements.txt"
    run(
        [
            "uv",
            "export",
            "--locked",
            "--no-dev",
            "--no-editable",
            "--no-hashes",
            "--no-emit-workspace",
            "--output-file",
            str(requirements),
        ],
        log=output / "export.log",
    )
    wheels = output / "wheels"
    for name in ("tool-contracts", "platform-runtime", "wb-tool", "bioimage-app"):
        run(
            ["uv", "build", "--package", name, "--wheel", "--out-dir", str(wheels)],
            log=output / (name + ".log"),
        )
    run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(runtime / "python.exe"),
            "--target",
            str(site),
            "--only-binary=:all:",
            "-r",
            str(requirements),
            *(str(wheel) for wheel in wheels.glob("*.whl")),
        ],
        log=output / "dependencies.log",
    )
    # This product uses QtWidgets/WebEngineWidgets, not external QML modules or
    # development headers. Qt's QML debug object paths also exceed Inno's limit.
    for directory in ("qml", "include"):
        unused = site / "PySide6" / directory
        if not unused.resolve().is_relative_to(output.resolve()):
            raise RuntimeError("Unexpected dependency pruning path")
        if unused.exists():
            shutil.rmtree(unused)
    # The locked Qt wheel redistributes MSVC. Put that same runtime beside
    # python.exe too: OCR workers must not depend on Qt having been imported or
    # a system-wide Visual C++ installation. Never harvest DLLs from System32.
    redistributables = sorted((site / "PySide6").glob("*140*.dll"))
    required = {
        "msvcp140.dll",
        "msvcp140_1.dll",
        "msvcp140_2.dll",
        "vcruntime140.dll",
        "vcruntime140_1.dll",
    }
    if not required.issubset({path.name.lower() for path in redistributables}):
        raise RuntimeError("Locked Qt wheel is missing required MSVC redistributables")
    for library in redistributables:
        shutil.copyfile(library, runtime / library.name)
    distribution = (
        "windows_ui_system_test"
        if args.ui_system_test
        else "windows_supervision_test"
        if args.supervision_test
        else "windows_reliable_crop_test"
        if args.reliable_crop_test
        else "windows_automatic_flow_test"
        if args.automatic_flow_test
        else "windows_fig_sequence_test"
        if args.fig_sequence_test
        else "windows_grouped_intake_test"
        if args.grouped_intake_test
        else "windows_execution_test"
        if args.execution_test
        else "windows_test"
    )
    channel = (
        "wb-ui-system-test"
        if args.ui_system_test
        else "wb-supervision-test"
        if args.supervision_test
        else "wb-reliable-crop-test"
        if args.reliable_crop_test
        else "wb-automatic-flow-test"
        if args.automatic_flow_test
        else "wb-fig-sequence-test"
        if args.fig_sequence_test
        else "wb-grouped-intake-test"
        if args.grouped_intake_test
        else "wb-execution-test"
        if args.execution_test
        else "win10-test"
    )
    shutil.copyfile(ROOT / f"tooling/{distribution}_readme.txt", dist / "安装与使用说明.txt")
    shutil.copyfile(ROOT / f"tooling/{distribution}_selfcheck.ps1", dist / "selfcheck.ps1")
    shutil.copyfile(ROOT / "tooling/windows_test_selfcheck.cmd", dist / "测试版环境自检.cmd")
    # The lock's OCR wheel supplies models; verify bytes through the public API later.
    app_icon = dist / "bioimage.ico"
    icon(app_icon)
    resource = output / "candidate.rc"
    resource.write_text('1 ICON "' + app_icon.as_posix() + '"\n', encoding="utf-8")
    windres = args.gcc.with_name("windres.exe")
    resource_object = output / "icon.o"
    run([str(windres), str(resource), str(resource_object)])
    executable = dist / "BioImageWB-Candidate.exe"
    run(
        [
            str(args.gcc),
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-O2",
            "-municode",
            "-mwindows",
            "-static-libgcc",
            '-DRELEASE_CHANNEL=L"' + channel + '"',
            str(ROOT / "tooling/windows_candidate_launcher.c"),
            str(resource_object),
            "-o",
            str(executable),
            "-lshell32",
        ],
        log=output / "launcher.log",
    )
    licenses(dist / "third-party-licenses")
    run(
        [
            "git",
            "archive",
            "--format=zip",
            "--output=" + str(dist / "source-code.zip"),
            commit,
            "apps",
            "packages",
            "tools",
            "tooling",
            "pyproject.toml",
            "uv.lock",
            "dev.py",
        ]
    )
    manifest: dict[str, object] = {
        "schema": 1,
        "method": "private-cpython-locked-wheels",
        "commit": commit,
        "python": sys.version,
        "runtime_source": str(base),
        "uv_lock_sha256": digest(ROOT / "uv.lock"),
        "runtime_python_sha256": digest(runtime / "python.exe"),
        "launcher_sha256": digest(executable),
        "compile_exit": 0,
        "release_channel": "test-only",
        "minimum_windows": "10.0.17763",
        "architecture": "x86_64",
        "msvc_runtime": {p.name: digest(runtime / p.name) for p in redistributables},
        "wheels": {p.name: digest(p) for p in wheels.glob("*.whl")},
    }
    manifest_path = output / "build-manifest.json"
    if args.execution_test:
        manifest.update(
            schema=2,
            distribution_id="BioImageTools.WB.E7Test",
            release_channel="wb-execution-test",
            settings_namespace="E7Test",
            acceptance="candidate-only; clean Win10/DPI/scientific holdout pending",
        )
    elif args.ui_system_test:
        manifest.update(
            schema=2,
            distribution_id="BioImageTools.WB.UISystemTest",
            release_channel=channel,
            settings_namespace="UISystemTest",
            acceptance="candidate-only; clean Win10/DPI/scientific holdout pending",
        )
    elif args.supervision_test:
        manifest.update(
            schema=2,
            distribution_id="BioImageTools.WB.SupervisionTest",
            release_channel=channel,
            settings_namespace="SupervisionTest",
            acceptance="candidate-only; clean Win10/DPI/scientific holdout pending",
        )
    elif args.reliable_crop_test:
        manifest.update(
            schema=2,
            distribution_id="BioImageTools.WB.ReliableCropTest",
            release_channel=channel,
            settings_namespace="ReliableCropTest",
            acceptance="candidate-only; clean Win10/DPI/scientific holdout pending",
        )
    elif args.automatic_flow_test:
        manifest.update(
            schema=2,
            distribution_id="BioImageTools.WB.AutomaticFlowTest",
            release_channel=channel,
            settings_namespace="AutomaticFlowTest",
            acceptance="candidate-only; clean Win10/DPI/scientific holdout pending",
        )
    elif args.fig_sequence_test:
        manifest.update(
            schema=2,
            distribution_id="BioImageTools.WB.FigSequenceTest",
            release_channel=channel,
            settings_namespace="FigSequenceTest",
            acceptance="candidate-only; clean Win10/DPI/scientific holdout pending",
        )
    elif args.grouped_intake_test:
        manifest.update(
            schema=2,
            distribution_id="BioImageTools.WB.GroupedIntakeTest",
            release_channel=channel,
            settings_namespace="GroupedIntakeTest",
            acceptance="candidate-only; clean Win10/DPI/scientific holdout pending",
        )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    shutil.copyfile(manifest_path, dist / "build-manifest.json")
    run(
        [
            str(args.iscc.resolve()),
            "/DAppSource=" + str(dist),
            "/DBuildCommit=" + commit[:12],
            "/DInstallerOutput=" + str(output),
            str(ROOT / f"tooling/{distribution}.iss"),
        ],
        log=output / "installer.log",
    )
    manifest["installer_exit"] = 0
    manifest["artifacts"] = {
        p.name: {"sha256": digest(p), "size": p.stat().st_size} for p in output.glob("*-Setup.exe")
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(output, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
