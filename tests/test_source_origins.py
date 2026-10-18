"""Only locally selected source paths in the exact project can be reused."""

from pathlib import Path

from bioimage_app.source_origins import SourceOrigins
from PySide6.QtCore import QSettings


def test_origin_memory_is_local_and_bound_to_workspace_project_row_and_source(
    tmp_path: Path,
) -> None:
    file = str(tmp_path / "local.ini")
    origins = SourceOrigins(QSettings(file, QSettings.Format.IniFormat))
    original = str(tmp_path / "source.tiff")
    origins.remember("workspace-a", "project-a", "row-a", "sha-a", original)
    origins.settings.sync()
    reopened = SourceOrigins(QSettings(file, QSettings.Format.IniFormat))
    assert reopened.lookup("workspace-a", "project-a", "row-a", "sha-a") == original
    assert reopened.lookup("workspace-b", "project-a", "row-a", "sha-a") == ""
    assert reopened.lookup("workspace-a", "project-b", "row-a", "sha-a") == ""
    assert reopened.lookup("workspace-a", "project-a", "row-b", "sha-a") == ""
    assert reopened.lookup("workspace-a", "project-a", "row-a", "sha-b") == ""
