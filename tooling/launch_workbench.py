"""Verify this checkout before dispatching its installed desktop entry.

Run with Python -I: neither the caller's working directory nor PYTHONPATH may
select another checkout. This source launcher does not repair environments or
fall back to an older installed product when verification fails.
"""

import importlib.util
import json
import runpy
import sys
from pathlib import Path


def verify_checkout(root: Path) -> dict[str, str]:
    expected = (root / "apps/desktop/src/bioimage_app").resolve()
    spec = importlib.util.find_spec("bioimage_app")
    if (
        spec is None
        or spec.origin is None
        or Path(spec.origin).resolve() != expected / "__init__.py"
    ):
        raise RuntimeError(
            "启动已停止：当前环境加载的程序不是此开发目录。"
            "请在当前目录执行 uv sync --locked --all-groups 后重试；不要切换到历史目录。"
        )
    assets = expected / "web_ui"
    for name in ("index.html", "app.js", "manual_quant.js", "styles.css"):
        if not (assets / name).is_file():
            raise RuntimeError(f"启动已停止：当前工作台文件缺失（{name}）。请恢复当前版本文件。")
    return {"checkout": str(root.resolve()), "module": str(expected), "interface": str(assets)}


def main() -> int:
    if not sys.flags.isolated:
        print("启动已停止：请使用 Start-BioImage.ps1，以隔离模式启动当前工作台。", file=sys.stderr)
        return 2
    try:
        identity = verify_checkout(Path(__file__).resolve().parents[1])
    except (RuntimeError, OSError, ImportError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    if sys.argv[1:] == ["--verify-launch"]:
        print(json.dumps(identity, ensure_ascii=True))
        return 0
    sys.argv[0] = "bioimage_app"
    runpy.run_module("bioimage_app", run_name="__main__", alter_sys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
