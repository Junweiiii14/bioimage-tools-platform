"""Explicit package/environment fingerprints, evaluated only on request."""

import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from tool_contracts.api import ModulePort, ModuleSpec, RuntimeVersion, canonical_module_json

from nuclei_tool.application.contracts import NucleiParameters
from nuclei_tool.domain.method import METHOD_VERSION, MODEL_FILES, RESEARCH_VERSIONS
from nuclei_tool.domain.runtime import RUNTIME_VERSIONS


def nuclei_module_spec() -> ModuleSpec:
    digest = hashlib.sha256()
    root = Path(__file__).parents[1]
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return ModuleSpec(
        module_id="nuclei-stardist-research",
        module_version="0.1.0",
        method_version=METHOD_VERSION,
        implementation_digest=digest.hexdigest(),
        input_ports=(ModulePort(name="source", kind="raw_image"),),
        output_ports=(
            ModulePort(name="labels", kind="analysis_result", filename="labels.npy"),
            ModulePort(name="provenance", kind="run_manifest", filename="provenance.json"),
        ),
        parameters_schema=canonical_module_json(json.dumps(NucleiParameters.model_json_schema())),
    )


def research_environment() -> tuple[RuntimeVersion, ...]:
    frozen = hashlib.sha256(
        canonical_module_json(json.dumps(RUNTIME_VERSIONS)).encode()
    ).hexdigest()
    return (RuntimeVersion(name="research_runtime_sha256", version=frozen),) + tuple(
        RuntimeVersion(name=name, version=value) for name, value in RESEARCH_VERSIONS.items()
    )


def verify_research_environment() -> None:
    for name, expected in RUNTIME_VERSIONS.items():
        if version(name) != expected:
            raise ValueError(f"environment_mismatch: {name} requires {expected}")


def verify_model(directory: str) -> None:
    root = Path(directory)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("model_missing: prepare the fixed P014 model directory explicitly")
    for name, expected in MODEL_FILES.items():
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"model_missing: prepare and verify {name}; no automatic download")
        if path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("model_budget: member exceeds 16 MiB")
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(f"model_digest_mismatch: {name}")
