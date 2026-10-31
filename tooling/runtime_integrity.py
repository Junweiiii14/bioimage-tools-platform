"""Fail-closed inputs for the Windows runtime builder; no downloads or trust-on-first-use."""

import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

PRODUCTS = ("tool-contracts", "platform-runtime", "wb-tool", "bioimage-app")


def digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"Expected a regular input file: {path}")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def runtime_member(path: Path) -> bool:
    """Exclude only generated caches, third-party site and uv management markers."""
    return (
        not {"site-packages", "__pycache__"}.intersection(path.parts)
        and path.suffix != ".pyc"
        and path.as_posix() not in {"BUILD", "Lib/EXTERNALLY-MANAGED"}
    )


def tree_identity(
    root: Path, include: Callable[[Path], bool] = lambda _: True
) -> dict[str, object]:
    files: dict[str, str] = {}
    for member in root.rglob("*"):
        relative = member.relative_to(root)
        if not include(relative):
            continue
        if member.is_symlink() or member.is_junction():
            raise RuntimeError(f"Tool/runtime tree contains a redirected path: {relative}")
        if member.is_file():
            files[relative.as_posix()] = digest(member)
    payload = "".join(f"{name}\0{files[name]}\n" for name in sorted(files)).encode("utf-8")
    return {"files": len(files), "tree_sha256": hashlib.sha256(payload).hexdigest()}


def verify_file(path: Path, expected: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or digest(path) != expected:
        raise RuntimeError(f"Tool or artifact SHA256 mismatch: {path}")


def _probe(path: Path, arguments: list[str], expected: str, *, stdin: str | None = None) -> str:
    result = subprocess.run(
        [str(path), *arguments],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    output = result.stdout + result.stderr
    # Inno's deliberately aborted stdin compilation only reveals its engine version.
    code = 2 if stdin is not None else 0
    if result.returncode != code or not re.search(expected, output, flags=re.MULTILINE):
        raise RuntimeError(f"Unexpected tool version/exit status: {path.name}")
    return next(line.strip() for line in output.splitlines() if re.search(expected, line))


@dataclass(frozen=True)
class VerifiedToolchain:
    uv: Path
    gcc: Path
    windres: Path
    iscc: Path
    identity: dict[str, object]
    python_tree: dict[str, object]


def verify_toolchain(lock_path: Path, *, gcc: Path, iscc: Path) -> VerifiedToolchain:
    lock = cast(dict[str, Any], json.loads(lock_path.read_text(encoding="utf-8")))
    policy = lock["runtime_candidate"]
    if policy["schema"] != 1 or sys.platform != "win32" or platform.machine().lower() != "amd64":
        raise RuntimeError("The locked runtime builder requires Windows x64")
    if platform.python_version() != lock["python"]:
        raise RuntimeError("Build Python version differs from toolchain-lock.json")
    found_uv = shutil.which("uv")
    if found_uv is None:
        raise RuntimeError("The locked uv executable is missing")
    paths = {
        "uv": Path(found_uv),
        "gcc": gcc,
        "windres": gcc.with_name("windres.exe"),
        "iscc": iscc,
    }
    paths = {name: path.absolute() for name, path in paths.items()}
    # Validate every binary before executing even a --version command.
    for name, path in paths.items():
        verify_file(path, policy["tools"][name]["sha256"])
    base = Path(sys.base_prefix)
    python_identity = tree_identity(base, runtime_member)
    if python_identity != policy["python_runtime"]["tree"]:
        raise RuntimeError("Python runtime differs from the verified official archive")
    compiler_identity = tree_identity(paths["gcc"].parent.parent)
    if compiler_identity != policy["compiler_runtime"]["tree"]:
        raise RuntimeError("GCC runtime differs from the verified official archive")
    for name, expected in policy["inno_runtime"]["files"].items():
        verify_file(paths["iscc"].parent / name, expected)
    identity: dict[str, object] = {}
    for name, path in paths.items():
        spec = policy["tools"][name]
        actual = _probe(path, spec["arguments"], spec["version_pattern"], stdin=spec.get("stdin"))
        identity[name] = {
            "path": str(path),
            "sha256": spec["sha256"],
            "version": actual,
            "source": spec["source"],
        }
    identity["python"] = {
        "version": platform.python_version(),
        "path": str(base),
        "source": policy["python_runtime"]["source"],
        **python_identity,
        "python_exe_sha256": digest(base / "python.exe"),
    }
    identity["gcc_runtime"] = compiler_identity
    identity["inno_runtime"] = policy["inno_runtime"]
    identity["toolchain_lock_sha256"] = digest(lock_path)
    return VerifiedToolchain(
        uv=paths["uv"],
        gcc=paths["gcc"],
        windres=paths["windres"],
        iscc=paths["iscc"],
        identity=identity,
        python_tree=python_identity,
    )


def freeze_local_wheels(wheels: Path, requirements: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    products: set[str] = set()
    for wheel in sorted(wheels.glob("*.whl")):
        name = wheel.name.split("-")[0].replace("_", "-")
        if name not in PRODUCTS or name in products:
            raise RuntimeError("Expected exactly one wheel for each of the four product packages")
        products.add(name)
        hashes[wheel.name] = digest(wheel)
    if products != set(PRODUCTS):
        raise RuntimeError("A product wheel is missing")
    with requirements.open("x", encoding="utf-8", newline="\n") as stream:
        for name, checksum in hashes.items():
            stream.write(f"{(wheels / name).resolve().as_uri()} --hash=sha256:{checksum}\n")
    return hashes


def verify_local_wheels(wheels: Path, hashes: dict[str, str]) -> None:
    if {p.name for p in wheels.glob("*.whl")} != set(hashes):
        raise RuntimeError("Product wheel set changed after its manifest was frozen")
    for name, expected in hashes.items():
        if Path(name).name != name:
            raise RuntimeError("Invalid wheel manifest member")
        verify_file(wheels / name, expected)


def payload_inventory(root: Path) -> dict[str, dict[str, object]]:
    """Manifest companions are excluded to avoid self-referential hashes."""
    files: dict[str, dict[str, object]] = {}
    for member in sorted(root.rglob("*")):
        relative = member.relative_to(root).as_posix()
        if member.is_symlink() or member.is_junction():
            raise RuntimeError(f"Payload contains a redirected path: {relative}")
        if member.is_file() and relative not in {"build-manifest.json", "payload-files.json"}:
            files[relative] = {"sha256": digest(member), "size": member.stat().st_size}
    return files
