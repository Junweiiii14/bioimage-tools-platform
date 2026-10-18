"""Explicit labels group rows; ambiguous names do not invent experimental relationships."""

import pytest
from wb_tool.api import source_import_labels


@pytest.mark.parametrize("separator", ["/", "\\"])
def test_same_fig_folder_groups_distinct_acquisition_names(separator: str) -> None:
    first = source_import_labels(
        separator.join(["experiment", "1D", "ABCA9_100646_0_14_0_0 (1).tiff"])
    )
    second = source_import_labels(
        separator.join(["experiment", "1D", "β-actin_151934_0_34_0_0 (1).tiff"])
    )
    other = source_import_labels(
        separator.join(["experiment", "1F", "ABCA9_173116_0_13_0_0 (1).tiff"])
    )
    assert first.figure == second.figure == "1D"
    assert other.figure == "1F"
    assert (first.protein, second.protein) == ("ABCA9", "β-actin")
    assert first.policy == "literal_source_labels@1"


def test_explicit_filename_and_conflicting_folder() -> None:
    assert source_import_labels("inputs/Fig 2a_ABCA9_100646_0_14_0_0.tiff").figure == "2A"
    assert source_import_labels("2B/Fig2A_ABCA9_100646_0_14_0_0.tiff").figure is None


def test_unknown_names_do_not_use_ancestors_or_guess_protein() -> None:
    labels = source_import_labels("1D/unknown/scan.tif")
    assert labels.figure is None and labels.protein is None
    assert source_import_labels("10670059/scan.tif").figure is None
