"""Read-only P023 local payload/source/dependency audit, separate from native UI proof."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from tooling.candidate_acceptance import document, verify_payload, verify_source

parser = argparse.ArgumentParser()
parser.add_argument("candidate", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = args.candidate.resolve()
manifest = document(root / "build-manifest.json")
inventory_code = (
    "import importlib.metadata,json,sys;"
    "print(json.dumps({'executable':sys.executable,'path':sys.path,"
    "'distributions':sorted([(d.metadata['Name'],d.version) "
    "for d in importlib.metadata.distributions()])}))"
)
inventory = json.loads(
    subprocess.check_output([str(root / "runtime/python.exe"), "-I", "-c", inventory_code])
)
sizes = {}
for name, path in {
    "candidate": root,
    "private_runtime": root / "runtime",
    "source_archive": root / "source-code.zip",
    "external_nuclei_worker": Path("../p015-research/worker-env").resolve(),
    "external_nuclei_model": Path("../p014-research/models/2D_versatile_fluo").resolve(),
}.items():
    sizes[name] = {
        "path": str(path),
        "logical_bytes": sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
        if path.is_dir()
        else path.stat().st_size,
    }
result = {
    "manifest": manifest,
    "payload": verify_payload(root, manifest, installed=False, allow_generated_caches=True),
    "source": verify_source(root, manifest, Path.cwd()),
    "inventory": inventory,
    "sizes": sizes,
    "audit_python": sys.executable,
    "peak_memory": "not measured",
    "cold_cache_launch_time": "not measured",
}
args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"source": result["source"], "sizes": sizes}, ensure_ascii=False))
