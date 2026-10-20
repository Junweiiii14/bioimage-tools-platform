"""Versioned human review receipts bound to current group parameters and runs."""

import hashlib
import json
from dataclasses import asdict, replace

from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.project_analysis import WBAnalysisProject, analysis_is_current

_PREFIX = "quant_group_review@1:"


def _receipt(project: WBFigureProject, figure: str) -> str | None:
    if not isinstance(project, WBAnalysisProject):
        return None
    rows = [r for r in project.rows if r.figure == figure]
    plans = {p.row_id: p for p in project.analyses}
    evidence: list[object] = []
    if not rows:
        return None
    for row in rows:
        plan = plans.get(row.row_id)
        if (
            plan is None
            or not analysis_is_current(project, plan)
            or plan.run is None
            or plan.run.state != "succeeded"
            or plan.run.result is None
        ):
            return None
        evidence.append(
            [
                row.row_id,
                row.figure,
                row.protein,
                asdict(replace(plan.request, revision=0)),
                plan.run.run_id,
                plan.run.result.sha256,
            ]
        )
    raw = json.dumps(evidence, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()
    return _PREFIX + hashlib.sha256(raw).hexdigest()


def quant_group_reviewed(project: WBFigureProject, figure: str) -> bool:
    token = _receipt(project, figure)
    return token is not None and all(
        token in row.notes.splitlines() for row in project.rows if row.figure == figure
    )


def confirm_quant_group(project: WBFigureProject, figure: str) -> WBFigureProject:
    """Record human review, never promote measured quality or crop readiness."""
    token = _receipt(project, figure)
    if token is None:
        raise ValueError("本组尚有未完成或已过期的计算，请完成后再审核")
    rows: list[FigureRow] = []
    for row in project.rows:
        if row.figure == figure:
            notes = [s for s in row.notes.splitlines() if not s.startswith(_PREFIX)]
            fields = {key: getattr(row, key) for key in type(row).model_fields}
            fields["notes"] = "\n".join([*notes, token])
            row = type(row).model_validate(fields)
        rows.append(row)
    fields = {key: getattr(project, key) for key in type(project).model_fields}
    fields["rows"] = tuple(rows)
    return type(project).model_validate(fields)
