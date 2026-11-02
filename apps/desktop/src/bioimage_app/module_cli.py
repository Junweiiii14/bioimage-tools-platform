"""Headless QCoreApplication driver for the same durable comparison session as the UI."""

import argparse
import json
import sys

from PySide6.QtCore import QCoreApplication, QTimer

from bioimage_app.module_session import ComparisonSession


def run_comparison_cli(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(description="真实WB旧方法对照与Workspace持久化")
    if not arguments or arguments[0] not in ("--v0-compare", "--v0-open"):
        parser.error("缺少--v0-compare或--v0-open")
    operation = arguments[0]
    parser.add_argument("workspace", help="新对照工程目录，或需要重开的工程目录")
    parser.add_argument(
        "--case",
        default="triangle_u16",
        choices=(
            "triangle_u8",
            "triangle_u16",
            "flat_zero",
            "invalid_roi",
            "dtype_limits",
        ),
    )
    parser.add_argument("--source", default="", help="原始TIFF；须同时给--parameters")
    parser.add_argument("--parameters", default="", help="显式AnalysisRequest JSON文件")
    options = parser.parse_args(arguments[1:])
    if bool(options.source) != bool(options.parameters):
        parser.error("--source与--parameters必须一起提供")
    if operation == "--v0-open" and (options.source or options.parameters):
        parser.error("重开工程不接受新输入")
    if QCoreApplication.instance() is not None:
        raise RuntimeError("CLI入口需要独立事件循环；嵌入宿主请使用ComparisonSession")
    app = QCoreApplication(["BioImage WB V0 comparison"])
    session = ComparisonSession()
    result_code = 1

    def finished(payload: str) -> None:
        nonlocal result_code
        state = json.loads(payload)
        result_code = 0 if state["state"] == "succeeded" else 2
        sys.stdout.buffer.write(payload.encode("utf-8") + b"\n")
        sys.stdout.buffer.flush()
        app.quit()

    def start() -> None:
        if operation == "--v0-open":
            session.reopen(options.workspace)
        elif options.source:
            session.start_input(options.workspace, options.source, options.parameters)
        else:
            session.start_fixture(options.workspace, options.case)

    session.finished.connect(finished)
    QTimer.singleShot(0, start)
    app.exec()
    return result_code
