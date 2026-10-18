"""Background Fig recognition/planning; measurement remains in normal workers."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from wb_tool.adapters.ocr import recognize_figure
from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.automatic import AutomaticRowEvidence, WBAutomaticProject
from wb_tool.application.fig_quant import WBPartitionProject
from wb_tool.application.figure_project import FigureRow, WBFigureProject
from wb_tool.application.project_analysis import ProjectRowAnalysis, WBAnalysisProject
from wb_tool.application.standalone_quant import ManualQuantTarget, explicit_lane_request
from wb_tool.domain.automatic import AutoWBSettings
from wb_tool.domain.fig_partition import partition_sheet


def prepare_fig_quantification(
    path: str | Path,
    project: WBFigureProject,
    source_row_id: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> WBPartitionProject:
    source = next((row for row in project.rows if row.row_id == source_row_id), None)
    if source is None or source.source is None:
        raise ValueError("原图不可用")
    previous = project.partition_sources if isinstance(project, WBPartitionProject) else ()
    if len(previous) >= 32 or any(e.source_sha256 == source.source.sha256 for e in previous):
        raise ValueError("该原图已切分或达到32张拼图预算；请修改已有组")
    if cancelled():
        raise ValueError("Fig识别已取消")
    image = load_tiff(path)
    if image.sha256 != source.source.sha256:
        raise ValueError("原图摘要已改变")
    recognition = recognize_figure(path, image.sha256, cancelled=cancelled)
    proposals = partition_sheet(image.pixels, recognition)
    # A pristine import placeholder can be replaced with its child rows. Existing
    # manual plans/results remain referenced and never get overwritten by detection.
    plans = project.analyses if isinstance(project, WBAnalysisProject) else ()
    replace_placeholder = source.roi is None and not any(p.row_id == source.row_id for p in plans)
    rows = [row for row in project.rows if row.row_id != source.row_id or not replace_placeholder]
    conflicts = {r.figure for r in rows} & {p.figure for p in proposals}
    if conflicts:
        raise ValueError("分组名称与已有结果重复，请先改名：" + "、".join(sorted(conflicts)))
    evidence = list(project.automatic_rows) if isinstance(project, WBAutomaticProject) else []
    for proposal in proposals:
        if cancelled():
            raise ValueError("Fig识别已取消")
        row_id = "fig-" + uuid4().hex
        crop = replace(proposal.crop, lane_id=row_id)
        row = FigureRow(
            row_id=row_id,
            source=source.source,
            filename=source.filename,
            width=source.width,
            height=source.height,
            bit_depth=source.bit_depth,
            figure=proposal.figure,
            protein=proposal.protein,
            lane_count=len(proposal.lanes) or 1,
            roi=crop,
            notes="; ".join(proposal.warnings),
        )
        rows.append(row)
        if not proposal.lanes:
            continue
        extended = crop.y1 - crop.y0 > 2 * max(lane.width for lane in proposal.lanes)
        mode = (
            "smear"
            if proposal.protein.strip().upper() in {"UB", "UBIQUITIN"}
            or ("missing_protein_label" in proposal.warnings and extended)
            else "peaks"
        )
        target = ManualQuantTarget(
            image.sha256,
            project.revision,
            crop,
            len(proposal.lanes),
            "dark",
            lane_rois=proposal.lanes,
            measurement_mode=mode,
        )
        try:
            request = explicit_lane_request(image, target, cancelled=cancelled)
        except ValueError:
            if cancelled():
                raise ValueError("Fig识别已取消") from None
            rows[-1] = row.model_copy(
                update={"notes": row.notes + "; quant_planning_failed;use_manual_lanes"}
            )
            continue
        plans += (ProjectRowAnalysis(row_id=row_id, crop=crop, request=request),)
        evidence.append(
            AutomaticRowEvidence(
                row_id=row_id,
                source_sha256=image.sha256,
                source_revision=project.revision,
                crop=crop,
                lane_count=len(proposal.lanes),
                request=request,
                settings=AutoWBSettings(
                    lane_count=len(proposal.lanes),
                    crop_height=crop.y1 - crop.y0,
                    quant_policy="wbquant_1_4_3@1",
                ),
                warnings=proposal.warnings,
                algorithm_id="fig_partition@1",
            )
        )
    fields = {key: getattr(project, key) for key in type(project).model_fields}
    fields.update(
        schema_version=9,
        rows=tuple(rows),
        figure_order=tuple(dict.fromkeys(row.figure for row in rows)),
        analyses=plans,
        automatic_rows=tuple(evidence),
        partition_sources=(*previous, recognition),
    )
    if cancelled():
        raise ValueError("Fig识别已取消")
    return WBPartitionProject.model_validate(fields)
