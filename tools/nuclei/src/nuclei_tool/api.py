"""Public research interface. Import does not load TensorFlow, models, or files."""

from nuclei_tool.adapters.input import NucleiInput, read_nuclei_input
from nuclei_tool.adapters.protocol import (
    NucleiConversation,
    NucleiStart,
    encode_frame,
    execution_identity,
)
from nuclei_tool.adapters.registration import nuclei_module_spec, research_environment, verify_model
from nuclei_tool.application.contracts import NucleiParameters
from nuclei_tool.domain.method import method_description

__all__ = [
    "NucleiInput",
    "NucleiParameters",
    "NucleiStart",
    "NucleiConversation",
    "read_nuclei_input",
    "nuclei_module_spec",
    "research_environment",
    "verify_model",
    "method_description",
    "execution_identity",
    "encode_frame",
]
