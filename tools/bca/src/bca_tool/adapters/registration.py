"""Fixed module identity and installed runtime, without import-time I/O."""

import hashlib
from importlib.metadata import version
from pathlib import Path

from tool_contracts.api import ModulePort, ModuleSpec, RuntimeVersion

from bca_tool.domain.plate import METHOD


def bca_module_spec() -> ModuleSpec:
    digest = hashlib.sha256()
    root = Path(__file__).parents[1]
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return ModuleSpec(
        module_id="bca-pierce25-research",
        module_version="0.1.1",
        method_version=METHOD,
        implementation_digest=digest.hexdigest(),
        input_ports=(
            ModulePort(name="source", kind="analysis_result"),
            ModulePort(name="record", kind="run_manifest"),
        ),
        output_ports=(
            ModulePort(name="wells", kind="analysis_result", filename="wells.csv"),
            ModulePort(name="samples", kind="analysis_result", filename="samples.csv"),
            ModulePort(name="provenance", kind="run_manifest", filename="provenance.json"),
        ),
        parameters_schema='{"additionalProperties":false,"properties":{},"type":"object"}',
    )


def research_environment() -> tuple[RuntimeVersion, ...]:
    if version("numpy") != "2.5.4":
        raise ValueError("environment_mismatch: fixed NumPy 2.5.4 required")
    return tuple(
        RuntimeVersion(name=n, version=version(n)) for n in ("numpy", "bca-tool", "tool-contracts")
    )
