"""Public host assembly API."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wb_tool.api import StartFrame

    from bioimage_app.figure_window import FigureProjectWindow as FigureProjectWindow
    from bioimage_app.wb_window import WBWindow as WBWindow

from bioimage_app.diagnostics import DesktopDiagnostics
from bioimage_app.process import ProcessCodec, ProcessEvent, ProcessOutcome, ProcessRunner
from bioimage_app.run_session import RunCompletion, RunSession
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply

__all__ = [
    "DesktopDiagnostics",
    "AsyncStorage",
    "StorageCommand",
    "StorageReply",
    "ProcessCodec",
    "ProcessEvent",
    "ProcessOutcome",
    "ProcessRunner",
    "create_wb_codec",
    "RunCompletion",
    "RunSession",
    "create_wb_window",
    "create_figure_project_window",
    "run_application",
]


def run_application() -> int:
    """Static desktop/worker dispatcher for the standalone application launcher."""
    from bioimage_app.__main__ import main

    return main()


def create_wb_codec(start: "StartFrame") -> ProcessCodec:
    """Lazy optional WB registration; generic host import does not load numeric libraries."""
    from bioimage_app.wb_registration import WBProcessCodec

    return WBProcessCodec(start)


def create_wb_window() -> "WBWindow":
    from bioimage_app.wb_window import WBWindow

    return WBWindow()


def create_figure_project_window() -> "FigureProjectWindow":
    from bioimage_app.figure_window import FigureProjectWindow

    return FigureProjectWindow()
