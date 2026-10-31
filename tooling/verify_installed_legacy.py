"""Prepare frozen synthetic legacy fixtures, then verify them using an isolated runtime.

Preparation needs the development test dependencies. Verification imports only installed
public product APIs and runs with ``<private python> -I -B <this file> verify ...``.
No user project, original image, installation file or existing report is overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast
from zipfile import ZipFile


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def contained(root: Path, relative: str) -> Path:
    path = root / relative
    if path.is_symlink() or path.is_junction() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Fixture path must stay inside its root")
    return path


def prepare(root: Path) -> None:
    # Reuse the existing independently frozen bb5601a goldens, not newly generated expectations.
    from tools.wb.tests.test_laboratory_compatibility import (
        LEGACY_MANIFEST_SHA256,
        LEGACY_RGB_SHA256,
        legacy_project,
    )

    root.mkdir(parents=True, exist_ok=False)
    versions: list[dict[str, object]] = []
    for version in range(1, 7):
        directory = root / str(version)
        directory.mkdir()
        project, sources = legacy_project(directory, version)
        raw = project.model_dump_json().encode()
        (directory / "project.json").write_bytes(raw)
        versions.append(
            {
                "version": version,
                "project": f"{version}/project.json",
                "project_sha256": digest(raw),
                "sources": [
                    {"sha256": item.sha256, "path": f"{version}/{Path(item.path).name}"}
                    for item in sources
                ],
                "rgb_sha256": LEGACY_RGB_SHA256,
                "manifest_sha256": LEGACY_MANIFEST_SHA256[version],
                "size": [356, 166],
            }
        )
    manifest = {
        "schema": 1,
        "synthetic": True,
        "golden_source": "tools/wb/tests/test_laboratory_compatibility.py; bb5601a renderer",
        "prepared_from_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], text=True
        ).strip(),
        "versions": versions,
    }
    (root / "fixtures.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(digest((root / "fixtures.json").read_bytes()))


def verify(
    root: Path,
    output: Path,
    runtime: Path,
    site: Path,
    fixtures_sha256: str,
    installation_root: Path | None,
) -> None:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ValueError("Use the explicitly selected private Python with -I -B")
    if Path(sys.executable).resolve() != runtime.resolve():
        raise ValueError("Unexpected Python runtime")
    protected = [root.resolve(), runtime.resolve().parent, site.resolve()]
    if installation_root is not None:
        installation_root = installation_root.resolve()
        if (
            runtime.resolve() != installation_root / "runtime/python.exe"
            or site.resolve() != installation_root / "runtime/Lib/site-packages"
        ):
            raise ValueError("Runtime/site-packages do not belong to the selected installation")
        protected.append(installation_root)
    if any(output.resolve().is_relative_to(path) for path in protected):
        raise ValueError("Reports must be outside fixtures, installation and product source")
    import wb_tool.api as api

    if Path(api.__file__).resolve() != (site / "wb_tool/api.py").resolve():
        raise ValueError("Product API did not load from the selected installed site-packages")
    fixtures_path = root / "fixtures.json"
    if digest(fixtures_path.read_bytes()) != fixtures_sha256:
        raise ValueError("Fixture manifest differs from the independently pinned SHA256")
    fixtures = json.loads(fixtures_path.read_bytes())
    if fixtures.get("schema") != 1 or fixtures.get("synthetic") is not True:
        raise ValueError("Expected frozen synthetic fixture manifest")
    if [item["version"] for item in fixtures["versions"]] != list(range(1, 7)):
        raise ValueError("All six frozen legacy versions are required")
    originals = {str(path): digest(path.read_bytes()) for path in root.rglob("*") if path.is_file()}
    output.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "schema": 1,
        "phase": "running",
        "scope": "installed-runtime" if installation_root is not None else "development-self-check",
        "installation_root": str(installation_root) if installation_root is not None else None,
        "verifier_sha256": digest(Path(__file__).read_bytes()),
        "runtime": sys.executable,
        "product_api": api.__file__,
        "isolated": True,
        "bytecode_writes": False,
        "fixture_manifest_sha256": digest(fixtures_path.read_bytes()),
        "prepared_from_commit": fixtures["prepared_from_commit"],
        "versions": [],
    }
    report_path = output / "legacy-verification.json"

    def save() -> None:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    save()
    try:
        for item in fixtures["versions"]:
            raw = contained(root, item["project"]).read_bytes()
            if digest(raw) != item["project_sha256"]:
                raise ValueError("Frozen project bytes changed")
            project = api.read_figure_project(raw)
            saved = project.model_dump_json().encode()
            reopened = api.read_figure_project(saved)
            if (
                type(reopened) is not type(project)
                or reopened != project
                or reopened.schema_version != item["version"]
                or b'"composition"' in saved
                or b'"layout_style"' in saved
            ):
                raise ValueError("Legacy save/reopen changed the project or schema")
            sources: list[api.FigureSourcePath] = []
            for source in item["sources"]:
                path = contained(root, source["path"])
                if digest(path.read_bytes()) != source["sha256"]:
                    raise ValueError("Synthetic original bytes changed")
                sources.append(api.FigureSourcePath(source["sha256"], str(path)))
            rendered = api.render_figure(reopened, tuple(sources))
            if (
                [rendered.width, rendered.height] != item["size"]
                or digest(rendered.rgb) != item["rgb_sha256"]
                or digest(rendered.manifest_json.encode()) != item["manifest_sha256"]
            ):
                raise ValueError("Legacy rendering differs from independent frozen goldens")
            directory = output / str(item["version"])
            directory.mkdir()
            (directory / "saved.json").write_bytes(saved)
            archive = directory / "legacy.zip"
            api.export_figure_bundle(reopened, tuple(sources), str(archive))
            if api.inspect_project_archive(str(archive)) != project:
                raise ValueError("Legacy archive changed project identity")
            with ZipFile(archive) as zipped:
                if (
                    zipped.read("manifest.json") != rendered.manifest_json.encode()
                    or api.read_figure_project(zipped.read("project.json")) != project
                ):
                    raise ValueError("Legacy archive changed its manifest/project")
            staged = api.stage_project_archive(str(archive), str(directory / "stage"))
            if (
                staged.project != project
                or Path(staged.archive_path).read_bytes() != archive.read_bytes()
            ):
                raise ValueError("Legacy restoration changed project/archive evidence")
            if len(staged.assets) != len({asset.sha256 for asset in staged.assets}) or {
                asset.sha256 for asset in staged.assets
            } != {source["sha256"] for source in item["sources"]}:
                raise ValueError("Restored source asset identities differ from frozen originals")
            restored_sources: list[api.FigureSourcePath] = []
            for asset in staged.assets:
                restored = Path(asset.path)
                if (
                    not restored.resolve().is_relative_to((directory / "stage").resolve())
                    or digest(restored.read_bytes()) != asset.sha256
                ):
                    raise ValueError("Restored source bytes differ from frozen originals")
                restored_sources.append(api.FigureSourcePath(asset.sha256, str(restored)))
            restored_render = api.render_figure(staged.project, tuple(restored_sources))
            if (
                digest(restored_render.rgb) != item["rgb_sha256"]
                or digest(restored_render.manifest_json.encode()) != item["manifest_sha256"]
            ):
                raise ValueError("Restored assets no longer render the frozen result")
            cast(list[dict[str, object]], report["versions"]).append(
                {
                    "version": item["version"],
                    "rgb_sha256": item["rgb_sha256"],
                    "manifest_sha256": item["manifest_sha256"],
                    "archive_sha256": digest(archive.read_bytes()),
                }
            )
            save()
        if originals != {
            str(path): digest(path.read_bytes()) for path in root.rglob("*") if path.is_file()
        }:
            raise ValueError("Fixture originals changed during verification")
        report.update(phase="passed", originals_unchanged=True)
    except Exception as error:
        report.update(phase="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--fixtures", type=Path, required=True)
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--fixtures", type=Path, required=True)
    verify_parser.add_argument("--output", type=Path, required=True)
    verify_parser.add_argument("--runtime", type=Path, required=True)
    verify_parser.add_argument("--site-packages", type=Path, required=True)
    verify_parser.add_argument("--fixtures-sha256", required=True)
    scope = verify_parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--installation-root", type=Path)
    scope.add_argument("--development-self-check", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.fixtures.resolve())
    else:
        verify(
            args.fixtures.resolve(),
            args.output.resolve(),
            args.runtime,
            args.site_packages,
            args.fixtures_sha256,
            args.installation_root,
        )


if __name__ == "__main__":
    main()
