"""Hand-computable ratios, explicit controls and finite-range failure boundaries."""

from sys import float_info

import pytest
from wb_tool.domain.normalization import control_mean, signal_ratio


def test_hand_computable_two_controls_preserve_individual_variation_and_zero() -> None:
    ratios = tuple(signal_ratio(t, r) for t, r in ((20, 10), (60, 20), (0, 5)))
    assert ratios == (2, 3, 0)
    mean = control_mean(ratios[:2])
    assert mean == 2.5
    assert tuple(signal_ratio(q, mean) for q in ratios) == (0.8, 1.2, 0)
    assert tuple(signal_ratio(q, ratios[0]) for q in ratios) == (1, 1.5, 0)


@pytest.mark.parametrize(
    "target,reference",
    [
        (1.0, 0.0),
        (1.0, -1.0),
        (-1.0, 1.0),
        (float("nan"), 1.0),
        (1.0, float("inf")),
        (True, 1.0),
        (1.0, False),
        (1e308, 1e-308),
        (1e-308, 1e308),
    ],
)
def test_bad_or_unrepresentable_ratios_never_become_zero(target: float, reference: float) -> None:
    with pytest.raises(ValueError):
        signal_ratio(target, reference)


def test_control_mean_avoids_intermediate_overflow_and_rejects_empty_bad_or_all_zero() -> None:
    assert control_mean((float_info.max, float_info.max)) == float_info.max
    assert control_mean((5e-324, 5e-324)) == 5e-324
    for values in ((), (0.0,), (float("nan"), 1.0), (-1.0, 2.0), (True, 2.0)):
        with pytest.raises(ValueError):
            control_mean(values)
