"""Return reviewed display strips and original-sample crops beside the original.

The desktop supplies a locally selected origin, never an archive destination.
Each file is independently verified and published without replacement. A receipt
is published last; errors explicitly retain and name any files already published.
"""

import json
import os
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import file_digest
from pathlib import Path
from uuid import uuid4

from wb_tool.adapters.crop_export import export_crop
from wb_tool.adapters.figure_image_export import publish_rendered_image
from wb_tool.adapters.laboratory_figure import render_display_segment
from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.crop import CropRequest
from wb_tool.application.crop_return import ReturnedCrop
from wb_tool.application.figure_project import FigureRender, WBFigureProject
from wb_tool.application.laboratory_layout import (
    FigureColumn,
    FigureComposition,
    WBLayoutProject,
    initial_composition,
    plan_laboratory_layout,
    with_figure_layout,
)


def return_reviewed_crop(
    project: WBFigureProject,
    row_id: str,
    original_path: str,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> ReturnedCrop:
    def check_cancel() -> None:
        if cancelled():
            raise ValueError("裁图回存已取消")

    check_cancel()
    source = Path(original_path).absolute()
    if any(p.is_symlink() or p.is_junction() for p in (source, *source.parents)):
        raise ValueError("原图路径不能经过符号链接或junction")
    row = next((r for r in project.rows if r.row_id == row_id), None)
    if row is None or not row.reviewed or row.source is None or row.roi is None:
        raise ValueError("请先审核当前原图裁剪")
    original = load_tiff(source)
    if (
        original.sha256 != row.source.sha256
        or source.stat().st_size != row.source.size_bytes
        or original.pixels.shape != (row.height, row.width)
        or original.bit_depth != row.bit_depth
    ):
        raise ValueError("原位置文件已改变，未回存；请选择与项目一致的原图")
    # Preserve each current segment/frame, without requiring unrelated rows to
    # be reviewed or loading labels/fonts. Normalize only temporary layout slots.
    layout = (
        project
        if isinstance(project, WBLayoutProject)
        else with_figure_layout(project, initial_composition(project))
    )
    composition = layout.composition if layout.composition.slices else initial_composition(layout)
    segments = sorted(
        (s for s in composition.slices if s.row_id == row_id),
        key=lambda s: (s.line, s.position),
    )
    subset = layout.model_copy(
        update={
            "rows": (row,),
            "figure_order": (row.figure,),
            "composition": FigureComposition(
                slices=tuple(
                    s.model_copy(update={"line": 1, "position": i})
                    for i, s in enumerate(segments, 1)
                ),
                columns=(FigureColumn(figure=row.figure, column=1),),
            ),
        }
    )
    planned = plan_laboratory_layout(subset)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    stem = source.stem[:64].rstrip(". ") or "source"
    prefix = source.parent / f"{stem}_WB裁图_{stamp}_{uuid4().hex[:12]}"
    published: list[str] = []
    records: list[dict[str, object]] = []
    receipt = Path(str(prefix) + "_记录.json")
    stage = source.parent / (".wb-return-" + uuid4().hex + ".tmp")
    try:
        for index, placed in enumerate((s for line in planned.lines for s in line.segments), 1):
            check_cancel()
            roi = placed.roi
            if roi is None:
                raise ValueError("裁图分段缺少原图坐标")
            x0, y0, x1, y1 = placed.output_box
            width, height = x1 - x0, y1 - y0
            placed = replace(placed, output_box=(0, 0, width, height))
            record: dict[str, object] = {
                "operation": "reviewed_crop_display@1",
                "purpose": "display_only_not_quantitative",
                "project_id": project.project_id,
                "revision": project.revision,
                "row_id": row_id,
                "source_sha256": row.source.sha256,
                "segment": index,
                "first_lane": placed.segment.first_lane,
                "last_lane": placed.segment.last_lane,
            }
            image = render_display_segment(
                original,
                placed,
                record,
                resample=layout.layout_style.display_policy == "standard_lane_ratio@1",
            )
            display_path = str(prefix) + f"_{index:02d}_显示.png"
            rendered = FigureRender(width, height, image.tobytes(), json.dumps(record))
            published.append(
                publish_rendered_image(
                    rendered, project.template.dpi, display_path, cancelled=cancelled
                )
            )
            raw_path = str(prefix) + f"_{index:02d}_原值.tiff"
            published.append(
                export_crop(
                    str(source),
                    CropRequest(row.source.sha256, project.revision, roi),
                    raw_path,
                    cancelled=cancelled,
                )
            )
            records.append(record)
        check_cancel()
        with source.open("rb") as stream:
            if file_digest(stream, "sha256").hexdigest() != row.source.sha256:
                raise ValueError("回存期间原位置文件改变，未发布完成记录")
        outputs: list[dict[str, str]] = []
        for path in published:
            with Path(path).open("rb") as stream:
                outputs.append(
                    {
                        "filename": Path(path).name,
                        "sha256": file_digest(stream, "sha256").hexdigest(),
                    }
                )
        data = json.dumps(
            {
                "operation": "reviewed_crop_return@1",
                "source_sha256": row.source.sha256,
                "project_id": project.project_id,
                "revision": project.revision,
                "row_id": row_id,
                "files": outputs,
                "display_segments": records,
            },
            ensure_ascii=True,
        ).encode("utf-8")
        with stage.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if stage.read_bytes() != data:
            raise ValueError("完成记录写后核验失败")
        check_cancel()
        if os.name == "nt":
            os.rename(stage, receipt)
        else:
            os.link(stage, receipt)
        return ReturnedCrop(row_id, project.revision, tuple(published), str(receipt))
    except (OSError, ValueError) as error:
        details = "；已生成文件保留：" + "、".join(published) if published else "；未发布文件"
        raise ValueError(f"裁图回存未完成：{error}{details}") from error
    finally:
        if stage.exists():
            stage.unlink()
