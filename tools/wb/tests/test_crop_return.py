"""Source-folder publication preserves raw values and existing outputs on failure."""

import json
from hashlib import sha256
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import tifffile
from numpy.typing import NDArray
from PIL import Image
from wb_tool.adapters import crop_return
from wb_tool.api import (
    DisplayFrame,
    FigureLayoutStyle,
    export_figure_image,
    initial_composition,
    return_reviewed_crop,
    with_figure_layout,
)

from tools.wb.tests.test_figure_project import sample
from tools.wb.tests.test_laboratory_layout import laboratory


def read_pixels(path: str | Path) -> NDArray[np.uint16]:
    with tifffile.TiffFile(path) as image:
        page = image.pages[0]
        assert isinstance(page, tifffile.TiffPage)
        return cast(NDArray[np.uint16], page.asarray())


def test_returned_strips_are_beside_source_with_raw_values_and_receipt(tmp_path: Path) -> None:
    project, paths = sample(tmp_path)
    source = Path(paths[0].path)
    original = source.read_bytes()
    old_result = tmp_path / "old-result.png"
    old_result.write_bytes(b"OLD RESULT")
    first = return_reviewed_crop(project, "r0", str(source))
    second = return_reviewed_crop(project, "r0", str(source))
    assert set(first.files).isdisjoint(second.files)
    assert all(Path(p).parent == source.parent for p in (*first.files, first.receipt))
    assert original == source.read_bytes() and old_result.read_bytes() == b"OLD RESULT"
    with Image.open(first.files[0]) as image:
        np.testing.assert_array_equal(
            np.asarray(image)[:, :, 0], (read_pixels(source)[5:25, :] // 257).astype(np.uint8)
        )
        assert image.size == (36, 20)
        metadata = json.loads(image.info["wb_provenance"])
        assert metadata["purpose"] == "display_only_not_quantitative"
    raw = read_pixels(first.files[1])
    np.testing.assert_array_equal(raw, read_pixels(source)[5:25, :])
    assert raw.dtype == np.uint16
    receipt = json.loads(Path(first.receipt).read_bytes())
    assert receipt["source_sha256"] == sha256(original).hexdigest()
    assert receipt["revision"] == project.revision and receipt["row_id"] == "r0"
    for file in receipt["files"]:
        assert sha256((source.parent / file["filename"]).read_bytes()).hexdigest() == file["sha256"]


def test_split_lanes_return_separate_strips_without_dropping_or_reordering(tmp_path: Path) -> None:
    project, paths = laboratory(tmp_path)
    result = return_reviewed_crop(project, "r0", paths[0].path)
    raw = [read_pixels(p) for p in result.files if p.endswith(".tiff")]
    assert len(raw) == 2 and len(result.files) == 4
    np.testing.assert_array_equal(np.concatenate(raw, axis=1), read_pixels(paths[0].path)[5:35])
    assert [
        r["first_lane"] for r in json.loads(Path(result.receipt).read_bytes())["display_segments"]
    ] == [1, 2]


def test_rotated_return_matches_current_montage_display_and_keeps_raw_rect(tmp_path: Path) -> None:
    base, paths = sample(tmp_path)
    composition = initial_composition(base)
    frame = DisplayFrame(center_x=18, center_y=15, width=24, height=8, angle_degrees=4)
    composition = composition.model_copy(
        update={
            "slices": tuple(
                s.model_copy(update={"display_frame": frame}) if s.row_id == "r0" else s
                for s in composition.slices
            )
        }
    )
    project = with_figure_layout(
        base, composition, FigureLayoutStyle(display_policy="standard_lane_ratio@1")
    )
    result = return_reviewed_crop(project, "r0", paths[0].path)
    montage_path = str(tmp_path / "montage.png")
    export_figure_image(project, paths, montage_path)
    with Image.open(montage_path) as montage, Image.open(result.files[0]) as strip:
        metadata = json.loads(montage.info["wb_provenance"])
        record = next(r for r in metadata["rows"] if r["row_id"] == "r0")
        assert strip.size == (360, 96)
        assert strip.tobytes() == montage.crop(tuple(record["output_box"])).tobytes()
        assert json.loads(strip.info["wb_provenance"])["display_frame"] == frame.model_dump()
    np.testing.assert_array_equal(read_pixels(result.files[1]), read_pixels(paths[0].path)[5:25])


def test_partial_failure_keeps_named_files_and_does_not_claim_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, paths = sample(tmp_path)
    before = Path(paths[0].path).read_bytes()

    def fail(*args: object, **kwargs: object) -> str:
        raise OSError("disk full")

    monkeypatch.setattr(crop_return, "export_crop", fail)
    with pytest.raises(ValueError, match="已生成文件保留") as error:
        return_reviewed_crop(project, "r0", paths[0].path)
    files = list(tmp_path.glob("*_WB裁图_*"))
    assert len(files) == 1 and files[0].suffix == ".png"
    assert str(files[0]) in str(error.value)
    assert not list(tmp_path.glob("*_记录.json")) and not list(tmp_path.glob(".wb-*"))
    assert Path(paths[0].path).read_bytes() == before


def test_cancel_and_changed_origin_publish_nothing(tmp_path: Path) -> None:
    project, paths = sample(tmp_path)
    with pytest.raises(ValueError, match="取消"):
        return_reviewed_crop(project, "r0", paths[0].path, cancelled=lambda: True)
    with pytest.raises(ValueError, match="原位置文件已改变"):
        return_reviewed_crop(project, "r0", paths[1].path)
    unreviewed = project.model_copy(
        update={"rows": tuple(r.model_copy(update={"reviewed": False}) for r in project.rows)}
    )
    with pytest.raises(ValueError, match="先审核"):
        return_reviewed_crop(unreviewed, "r0", paths[0].path)
    assert not list(tmp_path.glob("*_WB裁图_*"))


def test_cancel_after_display_retains_partial_output_without_completion(tmp_path: Path) -> None:
    project, paths = sample(tmp_path)
    with pytest.raises(ValueError, match="已生成文件保留"):
        return_reviewed_crop(
            project,
            "r0",
            paths[0].path,
            cancelled=lambda: bool(list(tmp_path.glob("*_显示.png"))),
        )
    files = list(tmp_path.glob("*_WB裁图_*"))
    assert len(files) == 1 and files[0].suffix == ".png"
    assert not list(tmp_path.glob(".wb-*"))
