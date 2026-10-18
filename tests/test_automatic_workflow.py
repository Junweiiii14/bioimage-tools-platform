"""Real desktop import-to-publication with no injected ROI, lane count or result."""

import json
from collections.abc import Iterator
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pytest
import tifffile
from bioimage_app.api import create_figure_project_window
from bioimage_app.figure_window import FigureProjectWindow
from pytestqt.qtbot import QtBot
from wb_tool.api import WBAutomaticProject, read_figure_project


@pytest.fixture
def automatic_window(qtbot: QtBot, tmp_path: Path) -> Iterator[FigureProjectWindow]:
    window = create_figure_project_window()
    window.show()
    window.open_workspace(str(tmp_path / "workspace"), create=True)
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=15000)
    yield window
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=20000)


def make_sources(root: Path) -> tuple[Path, Path]:
    root.mkdir()
    blank = root / "00-blank.tif"
    bands = root / "01-bands.tif"
    image = np.full((180, 360), 50000, dtype=np.uint16)
    tifffile.imwrite(blank, image)
    for x in (60, 120, 180, 240, 300):
        image[70:85, x - 17 : x + 17] = 15000
    tifffile.imwrite(bands, image)
    return blank, bands


def test_directory_import_detect_compute_export_and_reopen(
    qtbot: QtBot, tmp_path: Path, automatic_window: FigureProjectWindow
) -> None:
    window = automatic_window
    make_sources(tmp_path / "inputs")
    (tmp_path / "inputs" / "broken.tif").write_bytes(b"invalid TIFF")
    window.automatic.import_directory(str(tmp_path / "inputs"))
    qtbot.waitUntil(
        lambda: bool(window.automatic.last_output_path) or "操作失败" in window.view.status.text(),
        timeout=40000,
    )
    assert window.automatic.last_output_path, window.view.status.text()
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=15000)
    output = Path(window.automatic.last_output_path)
    assert window.output_button.isEnabled()
    project = window.view.project()
    assert isinstance(project, WBAutomaticProject)
    assert len(project.rows) == 2
    assert not any(r.reviewed for r in project.rows)
    assert project.rows[0].roi is None
    assert project.rows[1].lane_count == 5 and project.rows[1].roi is not None
    assert len(project.analyses) == 1 and project.analyses[0].run is not None
    assert project.analyses[0].run.state == "succeeded"
    assert window.view.analysis.summary.rowCount() == 5
    summary_status = window.view.analysis.summary.item(0, 2)
    summary_integral = window.view.analysis.summary.item(0, 3)
    assert summary_status is not None and summary_status.text() != "待计算"
    assert summary_integral is not None and summary_integral.text() != "—"
    assert (output / "measurements.xlsx").is_file()
    assert (output / "figure.png").is_file()
    assert (output / "figure.tif").is_file()
    with ZipFile(output / "project.zip") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["unrendered_rows"][0]["row_id"] == project.rows[0].row_id
        for row in manifest["rows"]:
            if row.get("crop_file"):
                assert row["crop_file"] == "crops/0002.tif"
                assert row["crop_file"] in archive.namelist()
        saved = read_figure_project(archive.read("project.json"))
        assert isinstance(saved, WBAutomaticProject) and saved.automatic_rows
    status = json.loads((output / "status.json").read_text(encoding="utf-8"))
    assert status["rendered_source_count"] == 1
    assert any("broken.tif" in error for error in status["processing_errors"])
    assert all(lane["value"] is None for lane in status["rows"][0]["lanes"])
    document_id = project.project_id
    window.load_document(document_id)
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=15000)
    reopened = window.view.project()
    assert isinstance(reopened, WBAutomaticProject)
    assert reopened.automatic_rows == project.automatic_rows
    assert window.view.table.currentRow() == 1
    assert window.view.analysis.summary.rowCount() == 5
    assert window.view.canvas.image_rect().width() > 0


def test_explicit_fig_folder_groups_acquisition_rows(
    qtbot: QtBot, tmp_path: Path, automatic_window: FigureProjectWindow
) -> None:
    group = tmp_path / "1D"
    group.mkdir()
    paths = []
    for offset, protein in enumerate(("ABCA9", "β-actin")):
        image = np.full((180, 360), 50000, dtype=np.uint16)
        image[0, 0] -= offset  # Distinct source identities with the same measured geometry.
        for x in (60, 120, 180, 240, 300):
            image[70:85, x - 17 : x + 17] = 15000
        source = group / f"{protein}_100646_0_14_0_0 (1).tiff"
        tifffile.imwrite(source, image)
        paths.append(str(source))
    window = automatic_window
    window.import_images(tuple(paths), automatic=True)
    qtbot.waitUntil(
        lambda: bool(window.automatic.last_output_path) or "操作失败" in window.view.status.text(),
        timeout=40000,
    )
    assert window.automatic.last_output_path, window.view.status.text()
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=15000)
    project = window.view.project()
    assert project.figure_order == ("1D",)
    assert [(row.figure, row.protein) for row in project.rows] == [
        ("1D", "ABCA9"),
        ("1D", "β-actin"),
    ]
    assert project.template.font is not None
    saved = read_figure_project(
        (Path(window.automatic.last_output_path) / "project.json").read_bytes()
    )
    assert saved.figure_order == project.figure_order
    assert saved.template.font == project.template.font


def test_close_during_directory_discovery_drains_resources(
    qtbot: QtBot, tmp_path: Path, automatic_window: FigureProjectWindow
) -> None:
    window = automatic_window
    make_sources(tmp_path / "inputs")
    window.automatic.import_directory(str(tmp_path / "inputs"))
    window.close()
    qtbot.waitUntil(lambda: window.resources_closed, timeout=15000)


def test_cancel_stops_automatic_pipeline_and_closes(
    qtbot: QtBot, tmp_path: Path, automatic_window: FigureProjectWindow
) -> None:
    window = automatic_window
    paths = make_sources(tmp_path / "inputs")
    window.import_images(tuple(map(str, paths)), automatic=True)
    window.cancel()
    qtbot.waitUntil(lambda: not window.operation_busy, timeout=15000)
    assert not window.automatic.last_output_path
    assert not (Path(window.workspace_path) / "outputs").exists()


def test_output_directory_error_is_visible(
    automatic_window: FigureProjectWindow,
) -> None:
    window = automatic_window
    (Path(window.workspace_path) / "outputs").write_text("occupied", encoding="utf-8")
    window.automatic.publish_default()
    assert "无法创建输出目录" in window.view.status.text()
    assert not window.operation_busy
