"""Assigned-source-only fixed N detection and verified original-sample export."""

from collections.abc import Callable
from dataclasses import replace
from hashlib import file_digest
from pathlib import Path

from wb_tool.adapters.crop_export import export_crop
from wb_tool.adapters.tiff_input import LoadedTiff, load_tiff
from wb_tool.application.crop import CropRequest
from wb_tool.application.figure_project import FigureSourcePath
from wb_tool.application.intake_crop import (
    IntakeCropEvidence,
    IntakeCropFile,
    WBIntakeCropProject,
    intake_crop_companion_assets,
    make_intake_crop_evidence,
)
from wb_tool.application.intake_workflow import (
    IntakeWorkflowTicket,
    validate_intake_workflow_ticket,
)
from wb_tool.domain.automatic import AutoWBSettings, detect_automatic_geometry
from wb_tool.domain.crop_detection import CropCandidate, CropDetection, CropDetectionSettings
from wb_tool.domain.export_detection import inspect_export
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.instrument_geometry import detect_instrument_geometry
from wb_tool.domain.lanes import LaneROI


def propose_intake_crop(
    path: str,
    project: WBIntakeCropProject,
    row_id: str,
    *,
    sources: tuple[FigureSourcePath, ...] = (),
    cancelled: Callable[[], bool] = lambda: False,
) -> IntakeCropEvidence:
    type(project).model_validate(dict(project))
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or row.source is None or cancelled():
        raise ValueError("原图未分配或定位已取消")
    image = load_tiff(path)
    if (image.sha256, image.pixels.shape, image.bit_depth) != (
        row.source.sha256,
        (row.height, row.width),
        row.bit_depth,
    ):
        raise ValueError("裁剪定位原图身份、尺寸或位深改变")
    detection = detect_automatic_geometry(
        image.pixels,
        AutoWBSettings(lane_count=row.lane_count, crop_policy="source_geometry@2"),
        cancelled=cancelled,
    )
    discovery = project.intake.discovery
    source_id = next(
        (b.source_id for b in project.intake.assignments if b.protein_id == row_id), None
    )
    source = next((s for s in project.intake.sources if s.source_id == source_id), None)
    selection = (
        next(
            (
                s
                for s in discovery.selections
                if source and s.source_id == source.source_id and s.lane_count == row.lane_count
            ),
            None,
        )
        if discovery
        else None
    )
    target = None
    if selection is not None and selection.region_index is not None and discovery is not None:
        observed = next(o for o in discovery.observations if o.source_id == selection.source_id)
        region = observed.regions[selection.region_index]
        target = LaneROI(row_id, region.x0, region.y0, region.x1, region.y1)
    companions = intake_crop_companion_assets(project, row_id)
    if not detection.candidates and len(companions) == 2 and sources:
        paths = {item.sha256: item.path for item in sources}
        dark: list[tuple[float, LoadedTiff]] = []
        for asset in companions:
            if cancelled():
                raise ValueError("辅助定位已取消")
            if asset.sha256 not in paths:
                raise ValueError("同组辅助定位资产缺失")
            peer = load_tiff(paths[asset.sha256])
            metadata = next(s for s in project.intake.sources if s.asset == asset)
            if (
                peer.sha256 != asset.sha256
                or peer.pixels.shape != image.pixels.shape
                or peer.bit_depth != metadata.bit_depth
                or peer.source.stat().st_size != asset.size_bytes
            ):
                raise ValueError("同组辅助定位资产身份或尺寸变化")
            feature = inspect_export(peer.pixels)
            if not feature.bright_background:
                dark.append((feature.texture, peer))
        dark.sort(key=lambda item: item[0])
        if len(dark) == 2 and dark[1][0] - dark[0][0] >= 0.03:
            guide, other = dark[0][1], dark[1][1]
            detection = detect_instrument_geometry(
                image.pixels,
                guide.pixels,
                AutoWBSettings(lane_count=row.lane_count, crop_policy="source_geometry@2"),
                target=target,
                cancelled=cancelled,
            )
            detection = replace(
                detection,
                flags=(
                    *detection.flags,
                    "guide_sha256:" + guide.sha256,
                    "guide_peer_sha256:" + other.sha256,
                ),
            )
    if target is not None and not (
        detection.algorithm_id == "instrument_guided_geometry@1" and detection.candidates
    ):
        roi = target
        lanes = fixed_lane_grid(roi, row.lane_count)
        flags = (
            "user_selected_target_candidate",
            "fixed_n_unreviewed",
            "axis_aligned_original_pixels",
        )
        candidate = CropCandidate(
            roi,
            (roi.y0 + roi.y1) // 2,
            (0.0,) * row.lane_count,
            (),
            tuple(range(1, row.lane_count + 1)),
            (),
            flags,
            lanes,
        )
        detection = CropDetection(
            CropDetectionSettings(row.lane_count, roi.y1 - roi.y0, "dark", left_marker=False),
            row.width,
            row.height,
            None,
            None,
            roi,
            (candidate,),
            flags,
            "export_signal_regions@1",
        )
    if cancelled():
        raise ValueError("固定N定位已取消")
    return make_intake_crop_evidence(project, row_id, detection)


def export_intake_crop(
    path: str,
    project: WBIntakeCropProject,
    row_id: str,
    destination: str,
    *,
    ticket: IntakeWorkflowTicket,
    cancelled: Callable[[], bool] = lambda: False,
) -> IntakeCropFile:
    validate_intake_workflow_ticket(project, ticket)
    if ticket.stage != "crop" or ticket.target_id != row_id:
        raise ValueError("原值裁剪必须属于当前活动裁剪票据")
    if project.workflow.cancel_requested or cancelled():
        raise ValueError("原值裁剪已取消，不发布新文件")
    evidence = next((e for e in project.intake_crops if e.row_id == row_id), None)
    if evidence is None or not evidence.geometry_ready or evidence.crop is None:
        raise ValueError("请先明确核对并审核原图裁剪范围")
    path_out = export_crop(
        path,
        CropRequest(evidence.source_sha256, project.revision, evidence.crop),
        destination,
        cancelled=cancelled,
    )
    target = Path(path_out)
    with target.open("rb") as stream:
        digest = file_digest(stream, "sha256").hexdigest()
    if cancelled():
        raise ValueError("原值裁剪已取消，临时产物不安装")
    return IntakeCropFile(path=path_out, sha256=digest, size_bytes=target.stat().st_size)
