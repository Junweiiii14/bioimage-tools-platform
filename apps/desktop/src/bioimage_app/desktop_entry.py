"""One normal workbench entry; native compatibility tools require explicit options."""

import argparse
from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow

DesktopMode = Literal["workbench", "legacy-platform", "legacy-figure", "legacy-manual"]


def desktop_mode(arguments: list[str]) -> DesktopMode:
    parser = argparse.ArgumentParser(description="BioImage · WB 工作台")
    parser.set_defaults(mode="workbench")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--web-workbench",
        "--figure-project",
        "--platform",
        dest="mode",
        action="store_const",
        const="workbench",
        help="打开当前 WB 工作台（默认）；兼容已有项目启动参数",
    )
    for option, mode, title in (
        ("--legacy-platform", "legacy-platform", "旧平台"),
        ("--legacy-figure-project", "legacy-figure", "旧项目窗口"),
    ):
        modes.add_argument(
            option, dest="mode", action="store_const", const=mode, help=f"兼容诊断：{title}"
        )
    modes.add_argument(
        "--legacy-wb-manual",
        "--wb-manual",
        dest="mode",
        action="store_const",
        const="legacy-manual",
        help="兼容诊断：旧单图窗口；--wb-manual 为历史参数",
    )
    return cast(DesktopMode, parser.parse_args(arguments).mode)


def create_desktop_window(mode: DesktopMode) -> "QMainWindow":
    if mode == "workbench":
        from bioimage_app.web_window import WebWorkbenchWindow

        return WebWorkbenchWindow()
    window: QMainWindow
    if mode == "legacy-platform":
        from bioimage_app.platform_window import PlatformWindow

        window = PlatformWindow()
    elif mode == "legacy-figure":
        from bioimage_app.figure_window import FigureProjectWindow

        window = FigureProjectWindow()
    elif mode == "legacy-manual":
        from bioimage_app.wb_window import WBWindow

        window = WBWindow()
    else:
        raise ValueError("未知桌面入口")
    window.setWindowTitle("兼容工具（旧版） · " + window.windowTitle())
    return window
