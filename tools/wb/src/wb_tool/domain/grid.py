"""Geometry-only lane subdivision. Blank lanes are never removed or intensity matched."""

from wb_tool.domain.lanes import LaneROI

GRID_ALGORITHM = "fixed_count_integer_partition@1"


def fixed_lane_grid(
    region: LaneROI, count: int, *, exclude_left: int = 0, exclude_right: int = 0
) -> tuple[LaneROI, ...]:
    """Partition the remaining half-open width, with at most one pixel width difference."""
    if type(count) is not int or not 1 <= count <= 96:
        raise ValueError("泳道数量须为 1–96")
    if any(type(value) is not int or value < 0 for value in (exclude_left, exclude_right)):
        raise ValueError("左右排除宽度须为非负整数像素")
    left, right = region.x0 + exclude_left, region.x1 - exclude_right
    width = right - left
    if width < count:
        raise ValueError("排除 Marker 后区域太窄，每条泳道至少需要一个像素")
    return tuple(
        LaneROI(
            f"{region.lane_id}:{index + 1:02d}",
            left + index * width // count,
            region.y0,
            left + (index + 1) * width // count,
            region.y1,
        )
        for index in range(count)
    )
