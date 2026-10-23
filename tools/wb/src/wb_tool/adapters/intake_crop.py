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
from wb_tool.domain.common_band_geometry import detect_common_band_geometry
from wb_tool.domain.crop_detection import CropCandidate, CropDetection, CropDetectionSettings
from wb_tool.domain.export_detection import inspect_export
from wb_tool.domain.grid import fixed_lane_grid
from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.prominent_band_geometry import detect_prominent_band_geometry
from wb_tool.domain.reliable_geometry import ReliableDetection, detect_reliable_geometry


def _checked_geometry(
    image: LoadedTiff,
    guide: LoadedTiff,
    lane_count: int,
    target: LaneROI | None,
    cancelled: Callable[[], bool],
    *,
    registration_target: bool = False,
    lane_width: float | None = None,
) -> CropDetection:
    settings = AutoWBSettings(lane_count=lane_count, crop_policy="source_geometry@2")
    return detect_reliable_geometry(
        image.pixels,
        guide.pixels,
        settings,
        target=target,
        lane_width=lane_width,
        width_is_estimate=lane_width is not None,
        registration_target=registration_target,
        exclude_guide_marks=image.sha256 != guide.sha256,
        cancelled=cancelled,
    )


def _same_signal_coordinates(selected: CropDetection, peer: CropDetection) -> bool:
    if len(selected.candidates) != 1 or len(peer.candidates) != 1:
        return False
    a, b = selected.candidates[0].lane_rois, peer.candidates[0].lane_rois
    return len(a) == len(b) and all(
        abs((x.x0 + x.x1 - y.x0 - y.x1) / 2) <= max(2, min(x.width, y.width) * 0.25)
        and abs((x.y0 + x.y1 - y.y0 - y.y1) / 2) <= max(2, min(x.y1 - x.y0, y.y1 - y.y0) * 0.3)
        for x, y in zip(a, b, strict=True)
    )


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
    legacy = detection
    # Only an explicitly reviewed ROI of this very source is an exact pixel
    # calibration. Equal Fig names/dimensions alone are not a scale mapping.
    prior = next(
        (
            e
            for e in project.intake_crops
            if e.reviewed
            and e.row_id == row_id
            and e.crop is not None
            and e.source_sha256 == image.sha256
            and e.lane_count == row.lane_count
        ),
        None,
    )
    if prior is not None:
        # A reviewed grid includes its origin and boundaries, not just width.
        # Reanalysis cannot silently recenter it on asymmetric signal support.
        return prior
    width_estimate = (
        legacy if len(legacy.candidates) == 1 and legacy.candidates[0].display_frame else None
    )
    seed = width_estimate.candidates[0].display_frame if width_estimate else None
    lane_width = seed.width / row.lane_count if seed else None
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
    # Every new run uses the same independent gate, including N > 2 and images
    # where the historical detector returned no candidate. Old geometry is only
    # a retained manual proposal; it cannot short-circuit this validation.
    checked = _checked_geometry(
        image, image, row.lane_count, target, cancelled, lane_width=lane_width
    )
    detection = replace(
        checked,
        algorithm_id="source_signal_geometry@2",
        flags=(*checked.flags, "source_signal_contour"),
    )
    companions = intake_crop_companion_assets(project, row_id)
    common_guide = image
    verified_members: tuple[LoadedTiff, ...] = ()
    if (
        len(companions) == 2
        and sources
        and (not detection.candidates or inspect_export(image.pixels).bright_background)
    ):
        paths = {item.sha256: item.path for item in sources}
        members = [image]
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
            members.append(peer)
        dark = [
            (feature.texture, member)
            for member in members
            if not (feature := inspect_export(member.pixels)).bright_background
        ]
        dark.sort(key=lambda item: item[0])
        if len(dark) == 2 and dark[1][0] - dark[0][0] >= 0.03:
            guide, other = dark[0][1], dark[1][1]
            common_guide, verified_members = guide, tuple(members)
            detection = _checked_geometry(
                image, guide, row.lane_count, target, cancelled, lane_width=lane_width
            )
            peer = next(
                (member for member in members if member.sha256 not in {image.sha256, guide.sha256}),
                None,
            )
            if detection.candidates:
                corroborated = (
                    _checked_geometry(
                        peer,
                        guide,
                        row.lane_count,
                        target or detection.candidates[0].roi,
                        cancelled,
                        registration_target=target is None,
                        lane_width=lane_width,
                    )
                    if peer
                    else None
                )
                if corroborated is None or not _same_signal_coordinates(detection, corroborated):
                    detection = replace(
                        detection,
                        algorithm_id="export_signal_regions@1",
                        flags=(
                            *detection.flags,
                            "independent_validation_failed",
                            "group_signal_coordinates_unverified",
                        ),
                    )
                else:
                    detection = replace(
                        detection, flags=(*detection.flags, "registered_signal_pair@1")
                    )
            detection = replace(
                detection,
                flags=(
                    *detection.flags,
                    "guide_sha256:" + guide.sha256,
                    "guide_peer_sha256:" + other.sha256,
                    *("verified_group_sha256:" + member.sha256 for member in members),
                ),
            )
    if project.workflow.policy == "intake_workflow@5":
        # New batches always compare prominent source structure. An old detector
        # accepting a regular shadow must not bypass the new row ranking.
        prominent = detect_prominent_band_geometry(
            image.pixels,
            common_guide.pixels,
            AutoWBSettings(lane_count=row.lane_count, crop_policy="source_geometry@2"),
            target=target,
            cancelled=cancelled,
        )
        if verified_members:
            peer = next(
                (
                    m
                    for m in verified_members
                    if m.sha256 not in {image.sha256, common_guide.sha256}
                ),
                None,
            )
            corroborated = (
                detect_prominent_band_geometry(
                    peer.pixels,
                    common_guide.pixels,
                    AutoWBSettings(lane_count=row.lane_count, crop_policy="source_geometry@2"),
                    target=target,
                    cancelled=cancelled,
                )
                if peer and prominent.candidates
                else None
            )
            prominent = replace(
                prominent,
                algorithm_id="source_prominent_band_geometry@1"
                if common_guide.sha256 == image.sha256
                else "guided_prominent_band_geometry@1",
                flags=(
                    *prominent.flags,
                    "guide_sha256:" + common_guide.sha256,
                    *("verified_group_sha256:" + m.sha256 for m in verified_members),
                    "registered_signal_pair@1"
                    if corroborated and _same_signal_coordinates(prominent, corroborated)
                    else "companion_coordinates_unconfirmed",
                ),
            )
        if cancelled():
            raise ValueError("固定N定位已取消")
        return make_intake_crop_evidence(
            project,
            row_id,
            prominent,
            sampling_limits=prominent.sampling_limits,
            review_positions=prominent.review_positions,
        )
    # Preserve previously reliable geometry and its frozen v3 semantics. The
    # new common-band policy is independent evidence, not a success flag added
    # to a rejected old candidate. It deliberately ignores distant weak rows.
    if not detection.candidates or detection.algorithm_id not in {
        "source_signal_geometry@2",
        "instrument_guided_geometry@2",
    }:
        common = detect_common_band_geometry(
            image.pixels,
            common_guide.pixels,
            AutoWBSettings(lane_count=row.lane_count, crop_policy="source_geometry@2"),
            target=target,
            cancelled=cancelled,
        )
        if common.candidates:
            common = replace(
                common,
                algorithm_id="source_common_band_geometry@1"
                if common_guide.sha256 == image.sha256
                else "guided_common_band_geometry@1",
            )
            if verified_members:
                peer = next(
                    (
                        m
                        for m in verified_members
                        if m.sha256 not in {image.sha256, common_guide.sha256}
                    ),
                    None,
                )
                corroborated = (
                    detect_common_band_geometry(
                        peer.pixels,
                        common_guide.pixels,
                        AutoWBSettings(lane_count=row.lane_count, crop_policy="source_geometry@2"),
                        target=target,
                        cancelled=cancelled,
                    )
                    if peer
                    else None
                )
                common = replace(
                    common,
                    flags=(
                        *common.flags,
                        "guide_sha256:" + common_guide.sha256,
                        *("verified_group_sha256:" + m.sha256 for m in verified_members),
                        "registered_signal_pair@1"
                        if corroborated and _same_signal_coordinates(common, corroborated)
                        else "companion_coordinates_unconfirmed",
                    ),
                )
            detection = common
        elif not detection.candidates:
            detection = replace(detection, flags=(*detection.flags, *common.flags))
    if target is not None and not (
        detection.algorithm_id
        in {
            "source_signal_geometry@2",
            "instrument_guided_geometry@2",
            "source_common_band_geometry@1",
            "guided_common_band_geometry@1",
        }
        and detection.candidates
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
    if not detection.candidates and legacy.candidates:
        # Keep useful manual geometry and every failed independent check. The
        # legacy algorithm id deliberately cannot pass the automatic gate.
        detection = replace(
            legacy, flags=(*legacy.flags, "independent_validation_failed", *detection.flags)
        )
    if cancelled():
        raise ValueError("固定N定位已取消")
    return make_intake_crop_evidence(
        project,
        row_id,
        detection,
        width_estimate=width_estimate if "fixed_width_grid@1" in detection.flags else None,
        sampling_limits=detection.sampling_limits
        if isinstance(detection, ReliableDetection)
        else (),
        review_positions=detection.review_positions
        if isinstance(detection, ReliableDetection)
        else (),
    )


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
