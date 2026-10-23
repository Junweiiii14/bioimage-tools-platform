"""Fixed 5N:4 local frames and disjoint original-coordinate sampling rectangles.

The oriented display frame and the axis-aligned sampling rectangles have
different purposes. No rotated or resized array is a quantitative input.
"""

from math import ceil, cos, floor, isfinite, radians, sin

from wb_tool.domain.crop_detection import OrientedCrop
from wb_tool.domain.lanes import LaneROI

Point = tuple[float, float]


def _clip_x(polygon: list[Point], edge: float, *, keep_right: bool) -> list[Point]:
    result: list[Point] = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1], strict=True):
        inside_a = a[0] >= edge if keep_right else a[0] <= edge
        inside_b = b[0] >= edge if keep_right else b[0] <= edge
        if inside_a != inside_b:
            fraction = (edge - a[0]) / (b[0] - a[0])
            result.append((edge, a[1] + fraction * (b[1] - a[1])))
        if inside_b:
            result.append(b)
    return result


def fixed_lane_frame(
    lane_count: int,
    lane_width: float,
    center_x: float,
    center_y: float,
    angle_degrees: float,
    image_width: int,
    image_height: int,
    *,
    max_angle: float = 10,
    frame_height: float | None = None,
) -> tuple[OrientedCrop, LaneROI, tuple[LaneROI, ...]]:
    """Construct known-N geometry without counting separate signal components.

    Width is in original pixels. Internal sampling boundaries are the local
    grid's centre-line projections; first/last slots absorb the outer bounding
    margins. Sampling rectangles cover their own portion's vertical extent,
    never overlap in X, and are not claimed to equal rotated polygons.
    """
    if type(lane_count) is not int or not 1 <= lane_count <= 96:
        raise ValueError("固定网格泳道数须为1–96")
    if any(type(v) is not int or v < 1 for v in (image_width, image_height)):
        raise ValueError("固定网格原图尺寸须为正整数")
    if not all(isfinite(v) for v in (lane_width, center_x, center_y, angle_degrees)):
        raise ValueError("固定网格几何必须有限")
    if not isfinite(max_angle) or not 0 < max_angle <= 30:
        raise ValueError("固定网格角度策略须在0至30度内")
    if lane_width < 2 or abs(angle_degrees) > max_angle:
        raise ValueError("固定网格槽宽不足或角度超出小角度范围")
    if frame_height is not None and (not isfinite(frame_height) or frame_height <= 0):
        raise ValueError("固定网格显示高度须为有限正数")
    width = lane_count * lane_width
    height = lane_width * 0.8 if frame_height is None else frame_height
    c, s = cos(radians(angle_degrees)), sin(radians(angle_degrees))
    polygon = [
        (center_x + c * u - s * v, center_y + s * u + c * v)
        for u, v in (
            (-width / 2, -height / 2),
            (width / 2, -height / 2),
            (width / 2, height / 2),
            (-width / 2, height / 2),
        )
    ]
    # Small floating roundoff at an exactly integral boundary is not an extra
    # source pixel. Fractional widths otherwise retain their full outer extent.
    x0, x1 = floor(min(x for x, _ in polygon) + 1e-9), ceil(max(x for x, _ in polygon) - 1e-9)
    y0, y1 = floor(min(y for _, y in polygon) + 1e-9), ceil(max(y for _, y in polygon) - 1e-9)
    if not (0 <= x0 < x1 <= image_width and 0 <= y0 < y1 <= image_height):
        raise ValueError("固定网格超出原图，不截短已知槽位")
    crop = LaneROI("candidate", x0, y0, x1, y1)
    edges = [
        x0,
        *(
            floor(center_x + (i - lane_count / 2) * lane_width * c + 0.5)
            for i in range(1, lane_count)
        ),
        x1,
    ]
    lanes: list[LaneROI] = []
    for i, (left, right) in enumerate(zip(edges, edges[1:], strict=False), 1):
        if left >= right:
            raise ValueError("原图整数边界无法容纳全部固定槽位")
        part = _clip_x(_clip_x(polygon, left, keep_right=True), right, keep_right=False)
        if not part:
            raise ValueError("固定网格分区为空")
        top = max(y0, floor(min(y for _, y in part) + 1e-9))
        bottom = min(y1, ceil(max(y for _, y in part) - 1e-9))
        lanes.append(LaneROI(f"lane-{i}", left, top, right, bottom))
    return OrientedCrop(center_x, center_y, width, height, angle_degrees), crop, tuple(lanes)
