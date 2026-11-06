"""Public fixed-method API. No files, processes or computations at import time."""

from bca_tool.adapters.input import PlateInput, PlateRecord, read_plate
from bca_tool.adapters.protocol import BcaConversation, BcaStart, encode_frame, execution_identity
from bca_tool.adapters.registration import bca_module_spec, research_environment
from bca_tool.domain.plate import METHOD, PlateResult, SampleResult, Well, WellResult, analyze_plate

__all__ = [
    "PlateInput",
    "PlateRecord",
    "read_plate",
    "BcaConversation",
    "BcaStart",
    "encode_frame",
    "execution_identity",
    "bca_module_spec",
    "research_environment",
    "METHOD",
    "PlateResult",
    "SampleResult",
    "Well",
    "WellResult",
    "analyze_plate",
]
