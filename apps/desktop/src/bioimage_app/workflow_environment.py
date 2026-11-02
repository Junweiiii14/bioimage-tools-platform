"""Actual installed generic runtime identity; call only off the GUI thread."""

import hashlib
from importlib.metadata import version
from pathlib import Path

import platform_runtime.api
import tool_contracts.api
from tool_contracts.api import RuntimeVersion


def workflow_runtime_source_digest() -> str:
    roots = (
        ("tool_contracts", Path(tool_contracts.api.__file__).resolve().parent),
        ("platform_runtime", Path(platform_runtime.api.__file__).resolve().parent),
        ("bioimage_app", Path(__file__).resolve().parent),
    )
    digest = hashlib.sha256(b"workflow-host-installed-python-lf@1\0")
    for name, root in roots:
        files = sorted(root.rglob("*.py"))
        if not files:
            raise ValueError("Installed host source identity is unavailable")
        for source in files:
            if source.is_symlink() or not source.resolve().is_relative_to(root):
                raise ValueError("Installed host source escapes its package")
            digest.update((name + "/" + source.relative_to(root).as_posix()).encode() + b"\0")
            digest.update(source.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()


def workflow_runtime_environment(base: tuple[RuntimeVersion, ...]) -> tuple[RuntimeVersion, ...]:
    values = {item.name: item.version for item in base}
    if len(values) != len(base) or "host_runtime_source" in values:
        raise ValueError("Duplicate or caller-supplied host source identity")
    values["host_runtime_source"] = workflow_runtime_source_digest()
    for name in ("platform-runtime", "bioimage-app", "PySide6", "shiboken6"):
        if name in values:
            raise ValueError("Caller supplied a host runtime dependency identity")
        values[name] = version(name)
    return tuple(RuntimeVersion(name=name, version=value) for name, value in sorted(values.items()))
