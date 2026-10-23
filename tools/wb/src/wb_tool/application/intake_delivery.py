"""Versioned delivery location and deterministic human-readable paths; no filesystem I/O."""

import json
import re
import unicodedata
from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Literal

from pydantic import Field, model_validator

from wb_tool.application.document import DocumentIO

if TYPE_CHECKING:
    from wb_tool.application.instrument_intake import WBIntakeProject


class IntakeDeliveryState(DocumentIO):
    policy: Literal["intake_delivery@1"] = "intake_delivery@1"
    legacy_schema_version: int = Field(ge=1, le=4)
    output_parent: str = Field(min_length=1, max_length=32768)
    workspace_path: str = Field(min_length=1, max_length=32768)
    delivery_id: str = Field(pattern="^[0-9a-f]{32}$")
    plan_digest: str = Field(pattern="^[0-9a-f]{64}$")
    directory_name: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def safe_directory(self) -> "IntakeDeliveryState":
        if (
            any(c in self.directory_name for c in '<>:"/\\|?*')
            or any(ord(c) < 32 for c in self.directory_name)
            or self.directory_name.endswith((".", " "))
        ):
            raise ValueError("交付目录名必须是单个安全目录")
        for path in (self.output_parent, self.workspace_path):
            if "\x00" in path or not (
                PureWindowsPath(path).is_absolute() or PurePosixPath(path).is_absolute()
            ):
                raise ValueError("项目交付与工作区位置必须是绝对路径")
        return self


@dataclass(frozen=True)
class IntakeDeliveryRow:
    row_id: str
    figure_id: str
    label: str
    directory: str
    source_ids: tuple[str, ...]
    selected_source_id: str


@dataclass(frozen=True)
class IntakeDeliveryFigure:
    figure_id: str
    label: str
    directory: str


@dataclass(frozen=True)
class IntakeDeliveryPlan:
    digest: str
    figures: tuple[IntakeDeliveryFigure, ...]
    rows: tuple[IntakeDeliveryRow, ...]
    unassigned_source_ids: tuple[str, ...]


@dataclass(frozen=True)
class IntakeDeliveryReceipt:
    project_id: str
    delivery_id: str
    plan_digest: str
    destination: str
    row_id: str = ""
    files: tuple[str, ...] = ()


def delivery_component(label: str, identity: str, *, limit: int = 24) -> str:
    """Bound UTF-16 length, preserve readable labels and disambiguate every identity."""
    label = unicodedata.normalize("NFC", label)
    label = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", label).strip(" .") or "未命名"
    prefix = label.split(".", 1)[0].casefold()
    if prefix in {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(10)),
        *(f"lpt{i}" for i in range(10)),
    }:
        label = "_" + label
    while len(label.encode("utf-16-le")) // 2 > limit:
        label = label[:-1]
    return label.rstrip(" .") + "_" + sha256(identity.encode()).hexdigest()[:8]


def plan_intake_delivery(project: "WBIntakeProject") -> IntakeDeliveryPlan:
    figures = tuple(
        IntakeDeliveryFigure(
            f.figure_id,
            f.label,
            f"Fig组/{i:02d}_" + delivery_component(f.label, f.figure_id, limit=14),
        )
        for i, f in enumerate(project.intake.figures, 1)
    )
    directories = {f.figure_id: f.directory for f in figures}
    grouping = project.intake.grouping
    groups = {g.group_id: g for g in grouping.groups} if grouping else {}
    bindings = {a.protein_id: a.source_id for a in project.intake.assignments}
    counters: dict[str, int] = {}
    rows: list[IntakeDeliveryRow] = []
    assigned: set[str] = set()
    for protein in project.intake.proteins:
        counters[protein.figure_id] = counters.get(protein.figure_id, 0) + 1
        selected = bindings.get(protein.protein_id, "")
        group = groups.get(protein.protein_id)
        ids = group.source_ids if group else ((selected,) if selected else ())
        assigned.update(ids)
        directory = (
            directories[protein.figure_id]
            + f"/{counters[protein.figure_id]:02d}_"
            + delivery_component(protein.label, protein.protein_id, limit=14)
        )
        rows.append(
            IntakeDeliveryRow(
                protein.protein_id, protein.figure_id, protein.label, directory, ids, selected
            )
        )
    unassigned = tuple(s.source_id for s in project.intake.sources if s.source_id not in assigned)
    payload = {
        "project": project.project_id,
        "name": project.name,
        "figures": [(f.figure_id, f.label, f.lane_count) for f in project.intake.figures],
        "rows": [
            (r.row_id, r.figure_id, r.label, r.source_ids, r.selected_source_id) for r in rows
        ],
        "sources": [
            (s.source_id, s.original_name, s.relative_path, s.asset.sha256, s.asset.size_bytes)
            for s in project.intake.sources
        ],
    }
    digest = sha256(json.dumps(payload, ensure_ascii=True, sort_keys=True).encode()).hexdigest()
    return IntakeDeliveryPlan(digest, figures, tuple(rows), unassigned)


def prepare_intake_delivery(
    project: "WBIntakeProject", *, output_parent: str, workspace_path: str, delivery_id: str
) -> "WBIntakeProject":
    """Persist before scheduling I/O; a new ID always denotes a new immutable generation."""
    from wb_tool.application.instrument_intake import IntakeManifest
    from wb_tool.application.intake_workflow import WBIntakeWorkflowProject

    if isinstance(project, WBIntakeWorkflowProject) and any(
        s.status == "running" for s in project.workflow.steps
    ):
        raise ValueError("活动阶段不能更换交付目录")
    plan = plan_intake_delivery(project)
    state = IntakeDeliveryState(
        legacy_schema_version=project.intake.delivery.legacy_schema_version
        if project.intake.delivery
        else project.intake.schema_version,
        output_parent=output_parent,
        workspace_path=workspace_path,
        delivery_id=delivery_id,
        plan_digest=plan.digest,
        directory_name=delivery_component(project.name, project.project_id, limit=20)
        + "_"
        + delivery_id[:12],
    )
    manifest = IntakeManifest.model_validate(
        {**dict(project.intake), "schema_version": 5, "delivery": state}
    )
    return type(project).model_validate({**dict(project), "intake": manifest})
