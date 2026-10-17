"""Contextual controls preserve explicit metadata, OCR and numerical configuration."""

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from pytestqt.qtbot import QtBot
from wb_tool.api import (
    FigureLayoutStyle,
    ProjectOCRRow,
    ProjectOCRState,
    initial_composition,
    make_normalization_plan,
    project_with_normalizations,
    project_with_ocr,
    with_figure_layout,
)
from wb_tool.ui.laboratory_layout import LaboratoryLayoutPanel
from wb_tool.ui.normalization import NormalizationPanel
from wb_tool.ui.project_metadata import ProjectMetadataPanel
from wb_tool.ui.project_ocr import ProjectOCRPanel

from tools.wb.tests.test_project_metadata import project


def test_metadata_preview_is_explicit_and_switching_method_invalidates_it(qtbot: QtBot) -> None:
    panel = ProjectMetadataPanel()
    qtbot.addWidget(panel)
    original = project()
    panel.common["protein"].setText("p-AKT")
    panel.build_preview("common", original, ("r0",))
    assert not panel.review.isHidden()
    assert panel.input_scroll.isHidden()
    panel.enabled["protein"].setChecked(True)
    panel.select_entries(True)
    updated = panel.apply(original)
    assert updated.rows[0].protein == "p-AKT"
    assert updated.rows[1:] == original.rows[1:]
    assert updated.rows[0].source == original.rows[0].source
    assert updated.rows[0].roi == original.rows[0].roi
    panel.method.setCurrentIndex(1)
    assert panel.preview is None and panel.review.isHidden()
    assert not panel.input_scroll.isHidden()


def test_compact_layout_edits_and_advanced_table_share_geometry(qtbot: QtBot) -> None:
    panel = LaboratoryLayoutPanel()
    qtbot.addWidget(panel)
    original = project()
    layout = with_figure_layout(original, initial_composition(original), FigureLayoutStyle())
    panel.restore(layout)
    assert panel.advanced.isHidden()
    panel.segment.setCurrentIndex(1)
    panel.segment_fields[3].setValue(2)
    assert panel.composition().slices[1].position == 2
    item = panel.table.item(1, 3)
    assert item is not None
    item.setText("3")
    assert panel.segment_fields[3].value() == 3
    panel.cut.setValue(1)
    panel.split_selected()
    parts = panel.composition().slices
    assert [(part.first_lane, part.last_lane) for part in parts if part.row_id == "r1"] == [
        (1, 1),
        (2, 3),
    ]
    assert original.rows == layout.rows


def test_ocr_context_keeps_manual_correction_and_explicit_binding(qtbot: QtBot) -> None:
    panel = ProjectOCRPanel()
    qtbot.addWidget(panel)
    original = project()
    assert panel.run_button.isHidden() and panel.labels_panel.isHidden()
    source = original.rows[0].source
    assert source is not None
    state = ProjectOCRState(
        source=source,
        filename="figure.png",
        width=30,
        height=40,
        rows=(ProjectOCRRow(row_id="label", figure="Fig1", protein="AKT", confirmed=True),),
    )
    panel.restore(project_with_ocr(original, state))
    panel.table.setCurrentCell(0, 0)
    assert not panel.labels_panel.isHidden()
    panel.target.setCurrentIndex(panel.target.findData("r0"))
    bound = QSignalSpy(panel.binding_requested)
    panel.bind_button.click()
    assert bound.count() == 1 and bound.at(0) == ["label", "r0"]
    protein = panel.table.item(0, 1)
    assert protein is not None
    protein.setText("corrected")
    current = panel.state()
    assert current is not None and not current.rows[0].confirmed
    panel.results_toggle.click()
    assert not panel.output_panel.isHidden() and panel.body.isHidden()
    panel.results_toggle.click()
    assert panel.state() == current


def test_normalization_stages_preserve_unconfirmed_pairing(qtbot: QtBot) -> None:
    panel = NormalizationPanel()
    qtbot.addWidget(panel)
    original = project()
    panel.restore(original.model_copy(update={"rows": ()}))
    assert not panel.create_button.isEnabled()
    assert "图像复核" in panel.requirements.text()
    plan = make_normalization_plan(original, "r0", "r1", "housekeeping")
    configured = project_with_normalizations(original, (plan,))
    panel.restore(configured)
    assert panel.stages.currentIndex() == 1
    assert panel.plans() == (plan,)
    assert all(pair.reference_lane is None for pair in panel.plans()[0].pairs)
    panel.confirmed.setChecked(True)
    sample = panel.pairs.item(0, 1)
    assert sample is not None
    sample.setText("sample-A")
    assert not panel.confirmed.isChecked()
    before = panel.plans()
    panel.stage_buttons[2].click()
    panel.stage_buttons[1].click()
    assert panel.plans() == before
    panel.stage_buttons[0].click()
    panel.kind.setCurrentIndex(panel.kind.findData("phospho_total"))
    assert panel.plans() == before  # Preparing a new relationship must not mutate this one.
    check = panel.pairs.item(0, 3)
    assert check is not None and check.checkState() == Qt.CheckState.Checked
