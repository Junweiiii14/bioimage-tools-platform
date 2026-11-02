"""Small licensed synthetic fixtures and bounded inputs for the V0 comparison host."""

import hashlib
import io
from pathlib import Path

import numpy as np
import tifffile
from pydantic import TypeAdapter

from wb_tool.application.analysis import AnalysisRequest, BandAnnotation, LaneAnnotation
from wb_tool.application.module_execution import WBModuleInput
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.quantify import BandBounds


def wb_validation_input(name: str) -> WBModuleInput:
    """Fixed analytical fixtures from P001; no user image or old output is copied."""
    cases = {
        "triangle_u8": ([10, 20, 30, 20, 10], False, 3),
        "triangle_u16": ([1000, 2000, 3000, 2000, 1000], True, 3),
        "flat_zero": ([1000, 1000, 1000, 1000, 1000], True, 3),
        "invalid_roi": ([1000, 2000, 3000, 2000, 1000], True, 4),
        "dtype_limits": ([0, 20, 30, 20, 0], False, 3),
    }
    if name not in cases:
        raise ValueError("未知验收样例")
    profile, sixteen, width = cases[name]
    pixels = np.repeat(
        np.array(profile, dtype=np.uint16 if sixteen else np.uint8)[:, None], 3, axis=1
    )
    stream = io.BytesIO()
    tifffile.imwrite(stream, pixels, metadata=None)
    data = stream.getvalue()
    return WBModuleInput(
        AnalysisRequest(
            hashlib.sha256(data).hexdigest(),
            0,
            "light",
            (
                LaneAnnotation(
                    LaneROI(name, 0, 0, width, 5), (BandAnnotation("signal", BandBounds(0, 4)),)
                ),
            ),
        ),
        source_bytes=data,
    )


def read_wb_module_input(source: str, parameters: str) -> WBModuleInput:
    """Read explicit legacy AnalysisRequest JSON; no ROI/polarity inference."""
    with Path(parameters).open("rb") as stream:
        data = stream.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError("参数文件超过1MiB预算")
    from tool_contracts.api import canonical_module_json

    request = TypeAdapter(AnalysisRequest).validate_json(
        canonical_module_json(data.decode("utf-8")),
        strict=True,
        extra="forbid",
    )
    path = Path(source).resolve(strict=True)
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != request.source_sha256:
            raise ValueError("原图与显式参数摘要不一致")
    return WBModuleInput(request, source_path=str(path))
