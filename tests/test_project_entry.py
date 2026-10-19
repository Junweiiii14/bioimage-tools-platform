"""Entry preparation protects originals and avoids empty or recursive project imports."""

from pathlib import Path
from threading import Event

import pytest
from bioimage_app.project_entry import allocate_project_path, collect_source_images


def test_discovery_deduplicates_and_excludes_owned_outputs(tmp_path: Path) -> None:
    source = tmp_path / "原图"
    source.mkdir()
    first = source / "a.TIFF"
    first.write_bytes(b"original")
    (source / "notes.txt").write_text("notes")
    output = source / "outputs"
    output.mkdir()
    (output / "figure.tif").write_bytes(b"display")
    workspace = source / "old-project"
    workspace.mkdir()
    (workspace / "workspace.json").write_text("{}")
    (workspace / "asset.tif").write_bytes(b"snapshot")
    assert collect_source_images([source, first], Event()) == (first.resolve(),)
    with pytest.raises(ValueError, match="未找到"):
        collect_source_images([output / "figure.tif"], Event())


def test_empty_and_cancel_do_not_allocate_project(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="未找到"):
        collect_source_images([tmp_path], Event())
    cancelled = Event()
    cancelled.set()
    with pytest.raises(InterruptedError):
        collect_source_images([tmp_path], cancelled)
    assert list(tmp_path.iterdir()) == []


def test_file_limit_is_failure_not_silent_truncation(tmp_path: Path) -> None:
    for n in range(513):
        (tmp_path / f"{n}.tif").touch()
    with pytest.raises(ValueError, match="512"):
        collect_source_images([tmp_path], Event())


def test_allocation_does_not_create_or_overwrite_workspace(tmp_path: Path) -> None:
    parent = tmp_path / "projects"
    first = allocate_project_path(parent, "a/b:实验")
    first.mkdir()
    evidence = first / "existing.txt"
    evidence.write_text("preserve")
    second = allocate_project_path(parent, "a/b:实验")
    assert second.parent == parent
    assert second != first and not second.exists()
    assert evidence.read_text() == "preserve"
    assert "/" not in second.name and ":" not in second.name
