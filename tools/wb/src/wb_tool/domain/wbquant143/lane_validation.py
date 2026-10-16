"""Geometry adaptation: preserve numeric detection for independently sized lanes."""
from .models import LaneROI

def validate_lanes(lanes, width, height):
    checked = list(lanes)
    for roi in checked:
        roi.validate(width, height)
    if not checked or len({r.lane_id for r in checked}) != len(checked):
        raise ValueError("unique lanes are required")
    return checked
