"""Public host assembly API."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wb_tool.api import StartFrame

from bioimage_app.process import ProcessCodec, ProcessEvent, ProcessOutcome, ProcessRunner
from bioimage_app.run_session import RunCompletion, RunSession
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply

__all__ = [
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
]


def create_wb_codec(start: "StartFrame") -> ProcessCodec:
    """Lazy optional WB registration; generic host import does not load numeric libraries."""
    from bioimage_app.wb_registration import WBProcessCodec

    return WBProcessCodec(start)
