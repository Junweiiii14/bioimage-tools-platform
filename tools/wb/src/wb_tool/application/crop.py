"""Immutable crop intent in original image coordinates; independent of display pixels."""

import re
from dataclasses import dataclass

from wb_tool.domain.lanes import LaneROI


@dataclass(frozen=True)
class CropRequest:
    source_sha256: str
    revision: int
    roi: LaneROI

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise ValueError("裁剪来源须为 SHA256")
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("裁剪修订须为非负整数")
