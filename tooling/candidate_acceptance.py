"""Read a candidate's provenance, then explicitly run its synthetic diagnostics.

Standard library only: an installed private Python can execute this file with -I.
This command never installs, upgrades, uninstalls or publishes a distribution.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, cast

Json = dict[str, Any]
SOURCE_PATHS = ("apps", "packages", "tools", "tooling", "pyproject.toml", "uv.lock", "dev.py")
PACKAGES = {
    "bioimage_app": "apps/desktop/src/bioimage_app/",
    "platform_runtime": "packages/platform_runtime/src/platform_runtime/",
    "tool_contracts": "packages/tool_contracts/src/tool_contracts/",
    "wb_tool": "tools/wb/src/wb_tool/",
}
DIAGNOSTICS = ("--verify-installation", "--verify-supervision-installation")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def document(path: Path) -> Json:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return cast(Json, value)


def member(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if (
        not name
        or "\\" in name
        or ":" in name
        or relative.is_absolute()
        or any(part in {".", ".."} for part in name.split("/"))
        or relative.as_posix() != name
    ):
        raise ValueError(f"Unsafe manifest path: {name}")
    path = root / relative
    for part in (root, *path.parents, path):
        if part.is_symlink() or part.is_junction():
            raise ValueError(f"Redirected manifest path: {name}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Manifest path escapes payload: {name}")
    return path


def verify_file(path: Path, expected: str, size: int | None = None) -> None:
    if re.fullmatch(r"[0-9a-f]{64}", expected) is None or digest(path) != expected:
        raise ValueError(f"SHA256 mismatch: {path}")
    if size is not None and path.stat().st_size != size:
        raise ValueError(f"Size mismatch: {path}")


def verify_payload(
    root: Path, manifest: Json, *, installed: bool, allow_generated_caches: bool = False
) -> Json:
    payload_path = member(root, "payload-files.json")
    verify_file(payload_path, manifest["payload_manifest_sha256"])
    payload = document(payload_path)
    if (
        type(payload.get("schema")) is not int
        or payload.get("schema") != 1
        or payload.get("commit") != manifest["commit"]
    ):
        raise ValueError("Payload commit/schema mismatch")
    files = cast(dict[str, Json], payload["files"])
    if not files or len({name.casefold() for name in files}) != len(files):
        raise ValueError("Empty or case-ambiguous payload")
    for name, entry in files.items():
        verify_file(member(root, name), entry["sha256"], entry["size"])
    extras: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        member(root, relative)
        if not path.is_file() or relative in {*files, "build-manifest.json", "payload-files.json"}:
            continue
        if installed and re.fullmatch(r"unins[0-9]+\.(exe|dat|msg)", relative):
            extras.append(relative)
        elif allow_generated_caches and "/__pycache__/" in relative and relative.endswith(".pyc"):
            # CPython may create caches during installed execution; their bytes are not certified.
            extras.append(relative)
        else:
            raise ValueError(f"Unexpected payload file: {relative}")
    return {"verified_files": len(files), "unverified_installer_or_cache_files": extras}


def verify_source(root: Path, manifest: Json, source_repo: Path) -> Json:
    commit = manifest["commit"]
    # Reproduce Git's committed export attributes, including *.cmd eol=crlf.
    # A blob hash alone is not the expected byte sequence of git archive.
    raw = subprocess.check_output(
        ["git", "-C", str(source_repo), "archive", "--format=zip", commit, *SOURCE_PATHS]
    )
    expected: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as reference:
        if sum(info.file_size for info in reference.infolist()) > 512 * 1024 * 1024:
            raise ValueError("Reference source archive exceeds verification budget")
        for info in reference.infolist():
            if not info.is_dir():
                if info.file_size > 32 * 1024 * 1024:
                    raise ValueError("Reference source member exceeds verification budget")
                expected[info.filename] = reference.read(info)
    if not expected:
        raise ValueError("Source commit has no product files")
    checked = 0
    normalized_text: list[str] = []
    with zipfile.ZipFile(member(root, "source-code.zip")) as archive:
        entries = [info for info in archive.infolist() if not info.is_dir()]
        names = [info.filename for info in entries]
        if len(set(names)) != len(names) or set(names) != set(expected):
            raise ValueError("Source archive member set differs from committed source")
        if archive.comment.decode("ascii").strip() != commit:
            raise ValueError("Source archive commit comment mismatch")
        if sum(info.file_size for info in entries) > 512 * 1024 * 1024:
            raise ValueError("Source archive exceeds verification budget")
        for info in entries:
            if info.file_size > 32 * 1024 * 1024:
                raise ValueError("Source archive member exceeds verification budget")
            data = archive.read(info)
            if data != expected[info.filename]:
                raise ValueError(f"Source archive differs from Git: {info.filename}")
            for package, prefix in PACKAGES.items():
                if info.filename.startswith(prefix):
                    relative = (
                        f"runtime/Lib/site-packages/{package}/" + info.filename[len(prefix) :]
                    )
                    shipped = member(root, relative)
                    if shipped.is_file():
                        shipped_bytes = shipped.read_bytes()
                        if shipped_bytes != data:
                            if shipped.suffix not in {
                                ".py",
                                ".js",
                                ".css",
                                ".html",
                                ".json",
                                ".txt",
                            } or shipped_bytes.replace(b"\r\n", b"\n") != data.replace(
                                b"\r\n", b"\n"
                            ):
                                raise ValueError(f"Installed source differs from Git: {relative}")
                            normalized_text.append(relative)
                        checked += 1
                    else:
                        raise ValueError(f"Product source/resource missing: {relative}")
        for name, key in (("uv.lock", "uv_lock_sha256"),):
            if hashlib.sha256(archive.read(name)).hexdigest() != manifest[key]:
                raise ValueError(f"Archived {name} identity mismatch")
        lock_hash = hashlib.sha256(archive.read("tooling/toolchain-lock.json")).hexdigest()
        if lock_hash != manifest["toolchain"]["toolchain_lock_sha256"]:
            raise ValueError("Archived toolchain lock identity mismatch")
    return {
        "commit": commit,
        "git_verified_source_files": len(expected),
        "shipped_source_files": checked,
        "crlf_only_source_differences": normalized_text,
        "reference_archive_sha256": hashlib.sha256(raw).hexdigest(),
    }


def verify_candidate(
    candidate: Path,
    installer: Path,
    installer_sha256: str,
    source_commit: str,
    source_repo: Path,
    installed_root: Path | None = None,
) -> Json:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("An exact 40-character source commit is required")
    manifest = document(candidate / "build-manifest.json")
    if type(manifest.get("schema")) is not int or manifest["schema"] not in {1, 2}:
        raise ValueError("Unsupported build manifest schema")
    if (
        manifest.get("commit") != source_commit
        or type(manifest.get("installer_exit")) is not int
        or type(manifest.get("compile_exit")) is not int
        or manifest.get("installer_exit") != 0
        or manifest.get("compile_exit") != 0
    ):
        raise ValueError("Candidate source/installer completion mismatch")
    if manifest.get("build_inputs_contract") != "verified-runtime-inputs@1":
        raise ValueError("Candidate lacks verified build-input contract")
    artifact = manifest["artifacts"][installer.name]
    if artifact["sha256"] != installer_sha256:
        raise ValueError("Installer differs from independently selected SHA256")
    verify_file(installer, installer_sha256, artifact["size"])
    root = installed_root or candidate / "app"
    embedded = document(member(root, "build-manifest.json"))
    before_installer = {
        k: v for k, v in manifest.items() if k not in {"artifacts", "installer_exit"}
    }
    if embedded != before_installer:
        raise ValueError("Bundled manifest differs from final candidate manifest")
    payload = verify_payload(root, manifest, installed=installed_root is not None)
    executable = manifest.get("executable") or (
        "BioImageWB.exe"
        if manifest.get("release_channel") == "wb-laboratory"
        else "BioImageWB-Candidate.exe"
    )
    verify_file(member(root, executable), manifest["launcher_sha256"])
    verify_file(member(root, "runtime/python.exe"), manifest["runtime_python_sha256"])
    source = verify_source(root, manifest, source_repo)
    return {
        "manifest": manifest,
        "manifest_sha256": digest(candidate / "build-manifest.json"),
        "installer_sha256": installer_sha256,
        "root": str(root.resolve()),
        "payload": payload,
        "source": source,
        "state": "supplied-installation-directory" if installed_root else "candidate-directory",
    }


def require_disposable(manifest: Json) -> None:
    identifier = manifest.get("acceptance_id", "")
    if not isinstance(identifier, str) or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", identifier) is None:
        raise ValueError("Diagnostics require a disposable acceptance identity")
    expected = {
        "distribution_id": f"BioImageTools.WB.Acceptance.{identifier}",
        "release_channel": f"wb-acceptance-{identifier}",
        "settings_namespace": f"Acceptance-{identifier}",
        "executable": "BioImageWB-Acceptance.exe",
        "default_install_directory": f"Programs/BioImage WB 验收 {identifier}",
        "shortcut_name": f"BioImage WB 验收 {identifier}",
        "user_data_removal": False,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("Disposable installation identity is inconsistent")


def process(
    arguments: list[str], directory: Path, name: str, timeout: float, env: dict[str, str]
) -> Json:
    started = time.monotonic()
    with (
        (directory / f"{name}.stdout").open("xb") as stdout,
        (directory / f"{name}.stderr").open("xb") as stderr,
    ):
        child = subprocess.Popen(arguments, cwd=directory, env=env, stdout=stdout, stderr=stderr)
        timed_out = False
        try:
            code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            # This is the owned native launcher; its Job Object closes its own descendants.
            child.kill()
            code = child.wait(timeout=15)
    return {
        "arguments": arguments,
        "pid": child.pid,
        "exit_code": code,
        "timed_out": timed_out,
        "elapsed": time.monotonic() - started,
    }


def worker_has_exited(pid: int) -> bool:
    if sys.platform != "win32":
        raise ValueError("Windows worker exit observation is unavailable")
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x00100000, False, pid)
    if not handle:
        if ctypes.get_last_error() == 87:  # PID no longer exists.
            return True
        raise OSError(ctypes.get_last_error(), "Cannot observe diagnostic worker exit")
    try:
        return kernel.WaitForSingleObject(handle, 0) == 0
    finally:
        kernel.CloseHandle(handle)


def run_diagnostics(verified: Json, directory: Path, report: Json) -> None:
    manifest = verified["manifest"]
    require_disposable(manifest)
    root = Path(verified["root"])
    env = dict(os.environ)
    for key in (
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "QT_PLUGIN_PATH",
        "BIOIMAGE_RELEASE_CHANNEL",
    ):
        env.pop(key, None)
    env.update(QT_QPA_PLATFORM="offscreen", QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu")
    if sys.platform == "win32":
        system_root = Path(os.environ["SYSTEMROOT"])
        env["PATH"] = str(system_root / "System32")
        env["QT_QPA_FONTDIR"] = str(system_root / "Fonts")
    python = member(root, "runtime/python.exe")
    probe = (
        "import importlib,json,sys; "
        f"names={list(PACKAGES)!r}; "
        "print(json.dumps({'executable':sys.executable,'isolated':bool(sys.flags.isolated),"
        "'modules':{n:importlib.import_module(n).__file__ for n in names}}))"
    )
    outcome = process([str(python), "-I", "-B", "-c", probe], directory, "module-probe", 30, env)
    report["processes"].append(outcome)
    if outcome["exit_code"] != 0 or outcome["timed_out"]:
        raise ValueError("Private runtime module probe failed")
    identity = document(directory / "module-probe.stdout")
    if (
        Path(identity["executable"]).resolve() != python.resolve()
        or identity["isolated"] is not True
    ):
        raise ValueError("Module probe did not use the isolated private runtime")
    for name in PACKAGES:
        expected = root / "runtime/Lib/site-packages" / name / "__init__.py"
        if Path(identity["modules"][name]).resolve() != expected.resolve():
            raise ValueError(f"Module loaded outside installed payload: {name}")
    report["runtime_identity"] = identity
    for index, flag in enumerate(DIAGNOSTICS):
        name = f"diagnostic-{index}"
        diagnostic_path = directory / f"{name}.json"
        outcome = process(
            [str(member(root, manifest["executable"])), flag, str(diagnostic_path)],
            directory,
            name,
            180,
            env,
        )
        report["processes"].append(outcome)
        if outcome["exit_code"] != 0 or outcome["timed_out"]:
            raise ValueError(f"{flag} did not exit normally")
        data = document(diagnostic_path)
        if data.get("phase") != "passed" or data.get("errors") != [] or not data.get("checks"):
            raise ValueError(f"{flag} diagnostic report did not pass")
        if index == 1 and (
            data.get("diagnostic") != "supervision_installed@1"
            or data.get("isolated_imports") is not True
            or data.get("release_channel") != manifest["release_channel"]
            or Path(data.get("runtime_executable", "")).resolve() != python.resolve()
            or Path(data.get("package_file", "")).resolve()
            != (
                root / "runtime/Lib/site-packages/bioimage_app/installation_check_sequence.py"
            ).resolve()
        ):
            raise ValueError("Installed diagnostic module/channel provenance mismatch")
        workers = data.get("worker_pids", [])
        if index == 1 and (not workers or any(type(pid) is not int or pid <= 0 for pid in workers)):
            raise ValueError("Installed diagnostic lacks valid worker identities")
        if any(not worker_has_exited(pid) for pid in workers):
            raise ValueError("A reported worker remains active; no unrelated process was stopped")
        report["diagnostics"].append(
            {
                "report": diagnostic_path.name,
                "sha256": digest(diagnostic_path),
                "checks": data["checks"],
                "worker_pids": workers,
                "reported_workers_exited": True,
            }
        )
    report["payload_after_diagnostics"] = verify_payload(
        root, manifest, installed=True, allow_generated_caches=True
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--installer", required=True, type=Path)
    parser.add_argument("--installer-sha256", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--installed-root", type=Path)
    parser.add_argument("--report-directory", required=True, type=Path)
    parser.add_argument("--previous-report", type=Path)
    request: Json = {}
    request_evidence: Json | None = None
    actual = sys.argv[1:] if argv is None else argv
    if len(actual) == 2 and actual[0] == "--request-file":
        request_path = Path(actual[1])
        request = document(request_path)
        request_evidence = {"path": str(request_path.resolve()), "sha256": digest(request_path)}
        actual = [request["command"]]
        for key in (
            "candidate",
            "installer",
            "installer_sha256",
            "source_commit",
            "source_repo",
            "installed_root",
            "report_directory",
            "previous_report",
        ):
            if request.get(key):
                actual += ["--" + key.replace("_", "-"), str(request[key])]
    args = parser.parse_args(actual)
    directory = args.report_directory.resolve()
    for protected in (args.candidate, args.installed_root):
        if protected and directory.is_relative_to(protected.resolve()):
            raise ValueError("Reports must be outside candidate and installation directories")
    # Never replace a failed or completed report. Retrying always names a new directory.
    directory.mkdir(parents=True, exist_ok=False)
    report: Json = {
        "schema": 1,
        "phase": "running",
        "command": args.command,
        "environment": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "verifier_python": sys.version,
            "powershell": request.get("powershell"),
        },
        "source_commit": args.source_commit,
        "verifier_sha256": digest(Path(__file__)),
        "request": request_evidence,
        "processes": [],
        "diagnostics": [],
        "limitations": (
            "Synthetic engineering checks; clean Win10, physical DPI/input/GPU, external office "
            "apps and independent scientific holdout remain unverified. "
            "No install/upgrade/uninstall or publication is performed."
        ),
    }
    report_path = directory / "acceptance.json"
    with report_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    try:
        if args.previous_report:
            previous = document(args.previous_report)
            report["previous_report"] = {
                "path": str(args.previous_report.resolve()),
                "sha256": digest(args.previous_report),
                "phase": previous.get("phase"),
            }
        report["verified"] = verify_candidate(
            args.candidate,
            args.installer,
            args.installer_sha256,
            args.source_commit,
            args.source_repo,
            args.installed_root,
        )
        if args.command == "run":
            run_diagnostics(report["verified"], directory, report)
        report["phase"] = "passed"
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
        zipfile.BadZipFile,
        AttributeError,
    ) as error:
        report["phase"] = "failed"
        report["error"] = f"{type(error).__name__}: {error}"
    with report_path.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"{report['phase']}: {directory / 'acceptance.json'}", flush=True)
    return 0 if report["phase"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
