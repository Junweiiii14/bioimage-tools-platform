"""Reject untrusted build inputs before execution and enforce actual wheel hashes."""

import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest

from tooling import build_runtime_candidate as builder
from tooling import runtime_integrity as integrity


@pytest.fixture
def tool_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict[str, Path]]:
    paths = {
        "uv": tmp_path / "uv.exe",
        "gcc": tmp_path / "mingw64/bin/gcc.exe",
        "windres": tmp_path / "mingw64/bin/windres.exe",
        "iscc": tmp_path / "inno/ISCC.exe",
    }
    for name, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    python = tmp_path / "python"
    python.mkdir()
    (python / "python.exe").write_bytes(b"python")
    (python / "Lib").mkdir()
    (python / "Lib/pathlib.py").write_bytes(b"frozen standard library")
    (paths["gcc"].parent.parent / "support.a").write_bytes(b"frozen compiler support")
    support = paths["iscc"].parent / "ISCmplr.dll"
    support.write_bytes(b"frozen Inno engine")
    lock = tmp_path / "tooling/toolchain-lock.json"
    lock.parent.mkdir()
    lock.write_text(
        json.dumps(
            {
                "python": "3.12.14",
                "runtime_candidate": {
                    "schema": 1,
                    "tools": {
                        name: {
                            "sha256": integrity.digest(path),
                            "arguments": [],
                            "version_pattern": "locked-version",
                            "source": "test fixture",
                        }
                        for name, path in paths.items()
                    },
                    "python_runtime": {
                        "tree": integrity.tree_identity(python, integrity.runtime_member),
                        "source": "fixture",
                    },
                    "compiler_runtime": {
                        "tree": integrity.tree_identity(paths["gcc"].parent.parent)
                    },
                    "inno_runtime": {"files": {"ISCmplr.dll": integrity.digest(support)}},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(integrity.sys, "platform", "win32")
    monkeypatch.setattr(integrity.sys, "base_prefix", str(python))
    monkeypatch.setattr(integrity.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(integrity.platform, "python_version", lambda: "3.12.14")

    def uv_path(_name: str) -> str:
        return str(paths["uv"])

    monkeypatch.setattr(integrity.shutil, "which", uv_path)
    return lock, paths


@pytest.mark.parametrize("name", ["uv", "gcc", "windres", "iscc"])
def test_tool_hash_mismatch_never_executes_a_version_probe(
    tool_inputs: tuple[Path, dict[str, Path]], monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    lock, paths = tool_inputs
    paths[name].write_bytes(b"untrusted replacement")
    called: list[str] = []

    def probe(*_args: object, **_kwargs: object) -> None:
        called.append("probe")

    monkeypatch.setattr(integrity, "_probe", probe)
    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        integrity.verify_toolchain(lock, gcc=paths["gcc"], iscc=paths["iscc"])
    assert called == []


@pytest.mark.parametrize(
    "member", ["python/Lib/pathlib.py", "mingw64/support.a", "inno/ISCmplr.dll"]
)
def test_changed_tool_support_is_rejected(
    tool_inputs: tuple[Path, dict[str, Path]], member: str
) -> None:
    lock, paths = tool_inputs
    (lock.parent.parent / member).write_bytes(b"changed support")
    with pytest.raises(RuntimeError, match="differs|mismatch"):
        integrity.verify_toolchain(lock, gcc=paths["gcc"], iscc=paths["iscc"])


def test_verified_identity_records_exact_tools_runtime_and_lock(
    tool_inputs: tuple[Path, dict[str, Path]], monkeypatch: pytest.MonkeyPatch
) -> None:
    lock, paths = tool_inputs

    def probe(*_args: object, **_kwargs: object) -> str:
        return "locked-version"

    monkeypatch.setattr(integrity, "_probe", probe)
    verified = integrity.verify_toolchain(lock, gcc=paths["gcc"], iscc=paths["iscc"])
    assert verified.gcc == paths["gcc"]
    assert verified.uv == paths["uv"]
    assert verified.identity["toolchain_lock_sha256"] == integrity.digest(lock)
    assert set(verified.identity) == {
        "uv",
        "gcc",
        "windres",
        "iscc",
        "python",
        "gcc_runtime",
        "inno_runtime",
        "toolchain_lock_sha256",
    }


@pytest.mark.parametrize("code,stdout", [(0, "wrong-version"), (1, "locked-version")])
def test_matching_digest_does_not_excuse_wrong_version_or_failed_probe(
    tool_inputs: tuple[Path, dict[str, Path]],
    monkeypatch: pytest.MonkeyPatch,
    code: int,
    stdout: str,
) -> None:
    lock, paths = tool_inputs

    def run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], code, stdout, "")

    monkeypatch.setattr(
        integrity.subprocess,
        "run",
        run,
    )
    with pytest.raises(RuntimeError, match="version/exit"):
        integrity.verify_toolchain(lock, gcc=paths["gcc"], iscc=paths["iscc"])


def test_builder_rejects_untrusted_tools_before_creating_output(
    tool_inputs: tuple[Path, dict[str, Path]], monkeypatch: pytest.MonkeyPatch
) -> None:
    lock, paths = tool_inputs
    paths["gcc"].write_bytes(b"untrusted compiler")
    monkeypatch.setattr(builder, "ROOT", lock.parent.parent)
    monkeypatch.setattr(
        sys, "argv", ["builder", "--iscc", str(paths["iscc"]), "--gcc", str(paths["gcc"])]
    )

    def git(arguments: list[str], **_kwargs: Any) -> bytes | str:
        return b"" if arguments[1] == "status" else "a" * 40

    def unexpected_copy(*_args: Any, **_kwargs: Any) -> None:
        pytest.fail("Runtime copy was reached before tool validation")

    monkeypatch.setattr(builder.subprocess, "check_output", git)
    monkeypatch.setattr(builder.shutil, "copytree", unexpected_copy)
    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        builder.main()
    assert not (lock.parent.parent / ".local/releases").exists()


def make_wheels(path: Path) -> None:
    path.mkdir()
    for product in integrity.PRODUCTS:
        name = product.replace("-", "_")
        with zipfile.ZipFile(path / f"{name}-1.0-py3-none-any.whl", "w") as archive:
            archive.writestr(f"{name}/__init__.py", "VALUE = 1\n")
            metadata = f"{name}-1.0.dist-info"
            archive.writestr(
                f"{metadata}/METADATA", f"Metadata-Version: 2.1\nName: {product}\nVersion: 1.0\n"
            )
            archive.writestr(
                f"{metadata}/WHEEL",
                "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            )
            archive.writestr(f"{metadata}/RECORD", "")


def test_frozen_wheel_manifest_rejects_changed_missing_and_added_inputs(tmp_path: Path) -> None:
    wheels = tmp_path / "wheels"
    make_wheels(wheels)
    hashes = integrity.freeze_local_wheels(wheels, tmp_path / "requirements.txt")
    integrity.verify_local_wheels(wheels, hashes)
    wheel = next(wheels.glob("*.whl"))
    original = wheel.read_bytes()
    wheel.write_bytes(original + b"tampered")
    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        integrity.verify_local_wheels(wheels, hashes)
    wheel.unlink()
    with pytest.raises(RuntimeError, match="set changed"):
        integrity.verify_local_wheels(wheels, hashes)
    wheel.write_bytes(original)
    (wheels / "unexpected-1.0-py3-none-any.whl").write_bytes(b"extra")
    with pytest.raises(RuntimeError, match="set changed"):
        integrity.verify_local_wheels(wheels, hashes)


def test_real_uv_rejects_tampered_wheel_and_installs_locked_valid_wheels(tmp_path: Path) -> None:
    wheels = tmp_path / "wheels"
    make_wheels(wheels)
    requirements = tmp_path / "requirements.txt"
    integrity.freeze_local_wheels(wheels, requirements)
    wheel = next(wheels.glob("*.whl"))
    original = wheel.read_bytes()
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.comment = b"tampered but structurally valid ZIP"

    def install(target: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                sys.executable,
                "--target",
                str(tmp_path / target),
                "--no-deps",
                "--no-index",
                "--require-hashes",
                "--no-cache",
                "-r",
                str(requirements),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    failed = install("bad")
    assert failed.returncode != 0 and "Hash mismatch" in failed.stderr
    wheel.write_bytes(original)
    passed = install("good")
    assert passed.returncode == 0, passed.stderr
    assert len(list((tmp_path / "good").glob("*.dist-info"))) == 4


def test_payload_inventory_can_locate_exact_file_tampering(tmp_path: Path) -> None:
    (tmp_path / "original.txt").write_bytes(b"original")
    (tmp_path / "build-manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/build-manifest.json").write_text("{}", encoding="utf-8")
    first = integrity.payload_inventory(tmp_path)
    assert set(first) == {"original.txt", "assets/build-manifest.json"}
    (tmp_path / "original.txt").write_bytes(b"changed")
    assert integrity.payload_inventory(tmp_path) != first
