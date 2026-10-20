"""Read verified sources once and propose acquisition roles and signal regions."""

import re
from collections.abc import Callable
from hashlib import sha256

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.discovery import ExportDiscovery, ExportObservation, SignalRegion
from wb_tool.application.figure_project import FigureSourcePath
from wb_tool.application.instrument_intake import WBIntakeProject
from wb_tool.application.intake_grouping import acquisition_key as export_group
from wb_tool.domain.export_detection import ExportFeatures, guided_signal_regions, inspect_export


def discover_exports(
    project: WBIntakeProject,
    sources: tuple[FigureSourcePath, ...],
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> ExportDiscovery:
    paths = {item.sha256: item.path for item in sources}
    records: list[ExportObservation] = []
    features: dict[str, ExportFeatures] = {}
    for source in project.intake.sources:
        if cancelled():
            raise ValueError("仪器图片识别已取消，未提交建议")
        group = export_group(source.relative_path)
        group_id = sha256(group.encode()).hexdigest()[:24]
        try:
            image = load_tiff(paths[source.asset.sha256])
            if (image.sha256, image.pixels.shape, image.bit_depth) != (
                source.asset.sha256,
                (source.height, source.width),
                source.bit_depth,
            ):
                raise ValueError("来源摘要、尺寸或位深改变")
            feature = inspect_export(image.pixels)
            features[source.source_id] = feature
            name = source.original_name.casefold()
            long_name = bool(re.search(r"_\d{6}", name))
            if not long_name and source.width / source.height >= 1.8:
                role, reasons = "reference", ("横向成品外观；需逐图核验，不作为定量原图",)
            elif feature.bright_background:
                role, reasons = "signal", ("亮背景暗信号外观；来源角色仍需确认",)
            else:
                role, reasons = "unknown", ("暗背景膜片；需比较同组白光与合并图",)
            if image.conversion is not None:
                reasons = (*reasons, "RGB按既有输入契约转换灰度；保留原始彩色来源")
            regions = tuple(
                SignalRegion(x0=x0, y0=y0, x1=x1, y1=y1, lane_counts=counts, angle_degrees=angle)
                for x0, y0, x1, y1, counts, angle in feature.regions
            )
            records.append(
                ExportObservation(
                    source_id=source.source_id,
                    sha256=image.sha256,
                    group_id=group_id,
                    role=role,
                    reasons=reasons,
                    regions=regions if role == "signal" else (),
                )
            )
        except (ValueError, OSError, KeyError) as error:
            records.append(
                ExportObservation(
                    source_id=source.source_id,
                    sha256=source.asset.sha256,
                    group_id=group_id,
                    role="unknown",
                    error=str(error)[:4096],
                    reasons=("读取失败，不作为有效零值",),
                )
            )
    # A numbered variant alone never determines its role. Compare signal-free
    # membrane texture only within a complete, equal-sized acquisition triple.
    for record in tuple(records):
        peers = [r for r in records if r.group_id == record.group_id and not r.error]
        dark = [r for r in peers if r.role == "unknown" and r.source_id in features]
        sizes = {
            (s.width, s.height)
            for s in project.intake.sources
            if s.source_id in {p.source_id for p in peers}
        }
        if len(peers) != 3 or len(dark) != 2 or len(sizes) != 1:
            continue
        a, b = sorted(dark, key=lambda r: features[r.source_id].texture)
        low, high = features[a.source_id].texture, features[b.source_id].texture
        if high - low < 0.03:
            continue
        for item, role in ((a, "white"), (b, "merge")):
            index = next(i for i, r in enumerate(records) if r.source_id == item.source_id)
            records[index] = ExportObservation.model_validate(
                {
                    **dict(item),
                    "role": role,
                    "reasons": ("同组三联等尺寸，膜内纹理对比建议；需确认",),
                }
            )
    for record in tuple(records):
        if cancelled():
            raise ValueError("仪器图片识别已取消，未提交建议")
        if record.role != "signal" or record.error:
            continue
        guides = [r for r in records if r.group_id == record.group_id and r.role == "white"]
        if len(guides) != 1:
            continue
        try:
            signal = load_tiff(paths[record.sha256])
            guide = load_tiff(paths[guides[0].sha256])
            if signal.sha256 != record.sha256 or guide.sha256 != guides[0].sha256:
                raise ValueError("辅助定位期间来源改变")
            raw_regions = guided_signal_regions(signal.pixels, guide.pixels)
        except (ValueError, OSError):
            continue
        if raw_regions:
            regions = tuple(
                SignalRegion(x0=x0, y0=y0, x1=x1, y1=y1, lane_counts=counts, angle_degrees=angle)
                for x0, y0, x1, y1, counts, angle in raw_regions
            )
            index = next(i for i, r in enumerate(records) if r.source_id == record.source_id)
            records[index] = ExportObservation.model_validate(
                {
                    **dict(record),
                    "regions": regions,
                    "reasons": (
                        *record.reasons,
                        "同组等尺寸白光约束定位；坐标对应仅建议，需在信号原图复核",
                    ),
                }
            )
    if cancelled():
        raise ValueError("仪器图片识别已取消，未提交建议")
    return ExportDiscovery(observations=tuple(records))
