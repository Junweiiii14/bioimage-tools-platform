"""Folder selection keeps original acquisition paths and excludes known derived TIFFs."""

import json
from pathlib import Path

import numpy as np
import pytest
import tifffile
from wb_tool.adapters.automatic_export import discover_tiffs


def test_header_only_discovery_keeps_primary_and_reports_every_exclusion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    group = tmp_path / "1D"
    group.mkdir()
    for number in (1, 2, 3):
        tifffile.imwrite(
            group / f"ABCA9_100646_0_14_0_0 ({number}).tiff",
            np.full((20, 20), number, dtype=np.uint8),
        )
    for name, software in (
        ("montage.tif", "bioimage-wb figure_display@1"),
        ("approved-crop.tif", "bioimage-wb original_sample_crop@1"),
    ):
        tifffile.imwrite(group / name, np.ones((20, 20), dtype=np.uint8), software=software)
    broken = group / "broken.tif"
    broken.write_bytes(b"bad TIFF")

    def reject_pixel_read(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Discovery must not decode reference/derived image pixels")

    monkeypatch.setattr(tifffile.TiffPage, "asarray", reject_pixel_read)
    report = json.loads(discover_tiffs(str(tmp_path), with_report=True))
    assert report["policy"] == "folder_sources@1"
    assert {Path(path).name for path in report["paths"]} == {
        "ABCA9_100646_0_14_0_0 (1).tiff",
        "broken.tif",
    }
    assert {Path(item["path"]).name: item["reason"] for item in report["skipped"]} == {
        "ABCA9_100646_0_14_0_0 (2).tiff": "numbered_acquisition_variant",
        "ABCA9_100646_0_14_0_0 (3).tiff": "numbered_acquisition_variant",
        "montage.tif": "generated_display_or_crop",
        "approved-crop.tif": "generated_display_or_crop",
    }


def test_missing_primary_and_unrelated_numbered_images_are_kept(tmp_path: Path) -> None:
    names = ["ABCA9_100646_0_14_0_0 (2).tiff", "scan (1).tif", "scan (2).tif"]
    for name in names:
        tifffile.imwrite(tmp_path / name, np.ones((20, 20), dtype=np.uint8))
    paths = json.loads(discover_tiffs(str(tmp_path)))
    assert {Path(path).name for path in paths} == set(names)
