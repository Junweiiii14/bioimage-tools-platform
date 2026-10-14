"""Half-open lane geometry and original-intensity row means."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.quantify import QuantificationError

Polarity = Literal["dark", "light"]


@dataclass(frozen=True, slots=True)
class LaneROI:
    lane_id: str
    x0: int
    y0: int
    x1: int
    y1: int

    def __post_init__(self) -> None:
        if not self.lane_id.strip():
            raise QuantificationError("泳道身份不能为空")
        if any(type(value) is not int for value in (self.x0, self.y0, self.x1, self.y1)):
            raise QuantificationError("泳道坐标须为整数")
        if not (0 <= self.x0 < self.x1 and 0 <= self.y0 < self.y1):
            raise QuantificationError("泳道半开矩形须为非空且坐标非负")

    @property
    def width(self) -> int:
        return self.x1 - self.x0


@dataclass(frozen=True, slots=True)
class LaneProfiles:
    roi: LaneROI
    raw: tuple[float, ...]
    quantitative: tuple[float, ...]
    polarity: Polarity
    dtype_max: int


def compute_lane_profiles(
    pixels: NDArray[np.uint8 | np.uint16], roi: LaneROI, polarity: Polarity
) -> LaneProfiles:
    """Only unsigned 8/16-bit 2D quantitative pixels; no display transformations."""
    if pixels.ndim != 2 or pixels.dtype.kind != "u" or pixels.dtype.itemsize not in (1, 2):
        raise QuantificationError("定量图像须为二维 uint8 或 uint16")
    if polarity not in ("dark", "light"):
        raise QuantificationError("须显式选择 dark 或 light 条带极性")
    height, width = pixels.shape
    if roi.x1 > width or roi.y1 > height:
        raise QuantificationError("泳道矩形超出图像")
    means = pixels[roi.y0 : roi.y1, roi.x0 : roi.x1].mean(axis=1, dtype=np.float64)
    raw = tuple(float(value) for value in means)
    maximum = (1 << (pixels.dtype.itemsize * 8)) - 1
    quantitative = tuple(maximum - value for value in raw) if polarity == "dark" else raw
    return LaneProfiles(roi, raw, quantitative, polarity, maximum)
