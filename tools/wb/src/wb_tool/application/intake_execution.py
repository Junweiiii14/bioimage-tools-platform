"""Pure, immutable plans derived from confirmed instrument manifests; no processing."""

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal

from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.instrument_intake import IntakeSource, WBIntakeProject, intake_digest


def _key(kind: str, *parts: object) -> str:
    payload = json.dumps(("intake_execution@1", kind, *parts), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IntakePlannedSlot:
    slot_id: str
    position: int  # One-based position within this protein row; never a sample identity.


def planned_intake_slots(project_id: str, row_id: str, count: int) -> tuple[IntakePlannedSlot, ...]:
    """One identity formula shared by planning and persisted geometry validation."""
    return tuple(
        IntakePlannedSlot(_key("slot", project_id, row_id, i), i) for i in range(1, count + 1)
    )


@dataclass(frozen=True)
class IntakePlannedRow:
    row_id: str
    figure_id: str
    label: str
    source: IntakeSource
    layout_row: int  # Zero-based position within the Fig; missing rows never collapse it.
    slots: tuple[IntakePlannedSlot, ...]
    geometry_key: str
    output_directory: str
    raw_crop_path: str
    display_crop_path: str


@dataclass(frozen=True)
class IntakePlannedFigure:
    figure_id: str
    label: str
    position: int
    lane_count: int
    output_directory: str
    image_path: str
    rows: tuple[IntakePlannedRow, ...]


@dataclass(frozen=True)
class IntakePlannedCell:
    figure_id: str
    row_id: str
    slot_id: str
    position: int
    source_sha256: str
    status: Literal["pending"] = "pending"
    value: None = None


@dataclass(frozen=True)
class IntakeExecutionPlan:
    project_id: str
    source_revision: int
    intake_digest: str
    plan_key: str
    figures: tuple[IntakePlannedFigure, ...]
    cells: tuple[IntakePlannedCell, ...]
    policy: Literal["intake_execution@1"] = "intake_execution@1"


def build_intake_execution_plan(
    project: WBFigureProject, *, expected_digest: str
) -> IntakeExecutionPlan:
    """Freeze identity/path/layout/table placeholders without OCR, geometry or I/O.

    The project remains schema10. Rebuild after reopening rather than accepting a
    saved plan as authoritative. Labels are metadata; safe paths use scoped IDs.
    """
    if not isinstance(project, WBIntakeProject):
        raise ValueError("执行计划需要已确认的仪器清单项目")
    checked = type(project).model_validate(dict(project))
    digest = intake_digest(checked)
    if not expected_digest or digest != expected_digest:
        raise ValueError("仪器清单已修改，请重新确认执行计划")
    if checked.intake.confirmed_digest != digest:
        raise ValueError("请先确认仪器清单与来源对应关系")
    manifest = checked.intake
    sources = {source.source_id: source for source in manifest.sources}
    bindings = {binding.protein_id: binding.source_id for binding in manifest.assignments}
    figures: list[IntakePlannedFigure] = []
    cells: list[IntakePlannedCell] = []
    for figure_index, figure in enumerate(manifest.figures):
        directory = "fig-" + _key("figure", checked.project_id, figure.figure_id)
        rows: list[IntakePlannedRow] = []
        for protein in manifest.proteins:
            if protein.figure_id != figure.figure_id:
                continue
            source = sources[bindings[protein.protein_id]]
            row_directory = (
                directory + "/row-" + _key("row", checked.project_id, protein.protein_id)
            )
            slots = planned_intake_slots(checked.project_id, protein.protein_id, figure.lane_count)
            geometry_key = _key(
                "geometry",
                checked.project_id,
                protein.protein_id,
                source.source_id,
                source.asset.sha256,
                source.width,
                source.height,
                source.bit_depth,
                figure.lane_count,
            )
            rows.append(
                IntakePlannedRow(
                    protein.protein_id,
                    figure.figure_id,
                    protein.label,
                    source,
                    len(rows),
                    slots,
                    geometry_key,
                    row_directory,
                    row_directory + "/raw-crop.tiff",
                    row_directory + "/display-crop.png",
                )
            )
            cells.extend(
                IntakePlannedCell(
                    figure.figure_id,
                    protein.protein_id,
                    slot.slot_id,
                    slot.position,
                    source.asset.sha256,
                )
                for slot in slots
            )
        figures.append(
            IntakePlannedFigure(
                figure.figure_id,
                figure.label,
                figure_index,
                figure.lane_count,
                directory,
                directory + "/figure.tiff",
                tuple(rows),
            )
        )
    return IntakeExecutionPlan(
        checked.project_id,
        checked.revision,
        digest,
        _key("plan", checked.project_id, digest),
        tuple(figures),
        tuple(cells),
    )
