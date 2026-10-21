"""Independent synthetic regressions for reliable geometry: guide marks."""

from pathlib import Path

import numpy as np
from wb_tool.api import (
    WBIntakeCropProject,
    automatic_intake_crop_allowed,
    claim_intake_workflow_step,
    propose_intake_crop,
)

from tools.wb.tests.test_reliable_geometry_registration import grouped_arrays


def test_real_signal_band_coinciding_with_guide_mark_is_not_erased(tmp_path: Path) -> None:
    yy, xx = np.mgrid[:240, :600]
    guide = np.full(xx.shape, 100, dtype=np.uint16)
    guide[(abs(xx - 300) < 150) & (abs(yy - 120) < 50)] = 50000
    for y in (95, 120):
        guide[(abs(xx - 180) < 16) & (abs(yy - y) < 8)] = 40000
    signal = np.full(xx.shape, 50000, dtype=np.uint16)
    merge = guide.copy()
    for x in (180, 230, 280):
        mask = (abs(xx - x) < 16) & (abs(yy - 120) < 8)
        signal[mask] = 8000
        merge[mask] = 8000
    p, sources, row_id = grouped_arrays(tmp_path, (signal, guide, merge))
    active, ticket = claim_intake_workflow_step(p, session_key="review-guide-mark")
    assert isinstance(active, WBIntakeCropProject)
    assert ticket
    evidence = propose_intake_crop(sources[0].path, active, row_id, sources=tuple(sources[1:]))
    allowed = automatic_intake_crop_allowed(evidence)
    assert not allowed
