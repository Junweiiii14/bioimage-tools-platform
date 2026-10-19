"""Assemble a local validation bundle; never publish a release or overwrite a directory."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import sys
from pathlib import Path
from typing import cast

from tooling.p0.build import sha


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--qt-licenses", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    destination: Path = args.destination.resolve()
    build: Path = args.build.resolve()
    if not (build / "p0_probe.dist/BioimageP0.exe").is_file():
        raise FileNotFoundError("Standalone executable is missing")
    manifest = cast(dict[str, object], json.loads((build / "manifest.json").read_text("utf-8")))
    if manifest.get("exit_code") != 0:
        raise ValueError("Cannot assemble a failed build")
    expected = cast(dict[str, str], manifest["artifacts"])
    actual = {
        p.relative_to(build).as_posix(): sha(p)
        for p in sorted((build / "p0_probe.dist").rglob("*"))
        if p.is_file()
    }
    if not expected or actual != expected:
        raise ValueError("Build artifacts differ from the recorded manifest")
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copytree(build / "p0_probe.dist", destination / "app")
    copied_app = {
        "p0_probe.dist/" + p.relative_to(destination / "app").as_posix(): sha(p)
        for p in sorted((destination / "app").rglob("*"))
        if p.is_file()
    }
    if copied_app != expected:
        raise ValueError("Copied application failed hash verification")
    shutil.copytree(args.fixtures, destination / "fixtures")
    shutil.copy2(build / "manifest.json", destination / "build-manifest.json")
    shutil.copytree(args.qt_licenses, destination / "licenses/Qt-upstream")
    # Include notices from the locked environment. This is an intentionally conservative
    # inventory, not a claim that every installed development dependency is shipped.
    packages: list[dict[str, object]] = []
    for distribution in sorted(importlib.metadata.distributions(), key=lambda d: d.name.lower()):
        copied: list[str] = []
        for file in distribution.files or []:
            parts = str(file).lower()
            if not any(word in parts for word in ("license", "copying", "notice")):
                continue
            source = Path(str(distribution.locate_file(file)))
            if not source.is_file():
                continue
            relative = Path(str(file))
            if relative.is_absolute() or ".." in relative.parts:
                continue
            target = destination / "licenses" / distribution.name / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target.relative_to(destination).as_posix())
        packages.append(
            {
                "name": distribution.name,
                "version": distribution.version,
                "declared_license": distribution.metadata.get("License-Expression")
                or distribution.metadata.get("License"),
                "notice_files": copied,
            }
        )
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.is_file():
        shutil.copy2(python_license, destination / "licenses/Python-LICENSE.txt")
    (destination / "environment-inventory.json").write_text(
        json.dumps(
            {"scope": "locked build environment; not a minimal binary SBOM", "packages": packages},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (destination / "Start-P0.cmd").write_text(
        '@echo off\nsetlocal\nstart "" "%~dp0app\\BioimageP0.exe" '
        '--fixtures "%~dp0fixtures" --evidence "%~dp0evidence"\n',
        encoding="ascii",
    )
    (destination / "README.txt").write_text(
        "Bioimage P0 本机技术验证便携包\n\n"
        "解压后双击 Start-P0.cmd。保留 app 与 fixtures 目录。记录写入 evidence。\n"
        "依次载入三类合成样本，拖动红色 ROI；运行批次、取消、模拟 worker 崩溃，"
        "再运行验证恢复，最后保存验证记录。\n"
        "这是技术原型，不包含 WB 科学分析。完整 P0 仍需无 Python 的干净 Windows 验收。\n"
        "本包不安装依赖、不改注册表、不自动联网。仅本机验证使用，"
        "未签名，未作为公开 release 发布。\n\n"
        "第三方说明：Qt/PySide6 为可替换的独立动态库，原始许可证文本在 licenses。"
        "PySide/Qt 源码：https://code.qt.io/cgit/pyside/pyside-setup.git/?h=v6.12.0 与 "
        "https://code.qt.io/cgit/qt/qtbase.git/?h=v6.12.0 。\n"
        "Qt 官方声明：https://doc.qt.io/qt-6/licensing.html 。"
        "环境清单保守包含构建环境依赖，不是精简二进制 SBOM；正式对外发行前另行完成依赖声明审查。\n",
        encoding="utf-8",
    )
    inventory = {
        p.relative_to(destination).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)}
        for p in sorted(destination.rglob("*"))
        if p.is_file()
    }
    (destination / "bundle-manifest.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(destination)


if __name__ == "__main__":
    main()
