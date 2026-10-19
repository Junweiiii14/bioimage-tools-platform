"""Frozen host evidence for portable exports; never an imported local run receipt."""

from dataclasses import dataclass

from tool_contracts.api import RunRecord

from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_analysis import WBAnalysisProject
from wb_tool.application.project_ocr import WBProjectOCR


@dataclass(frozen=True)
class ArchiveRunEvidence:
    run: RunRecord
    request_path: str = ""
    result_path: str = ""
    error: str = ""


def project_runs(project: WBFigureProject) -> tuple[RunRecord, ...]:
    runs = (
        [p.run for p in project.analyses if p.run] if isinstance(project, WBAnalysisProject) else []
    )
    if isinstance(project, WBProjectOCR) and project.ocr and project.ocr.run:
        runs.append(project.ocr.run)
    if len({run.run_id for run in runs}) != len(runs):
        raise ValueError("项目运行引用重复，不能归档")
    return tuple(runs)
