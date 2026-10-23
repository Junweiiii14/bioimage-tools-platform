"""Incremental, owned WB delivery directories and verified final portable snapshots."""

import json
import os
from collections.abc import Callable
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import cast
from uuid import uuid4

from tool_contracts.api import AssetRef

from wb_tool.application.figure_project import FigureRender, FigureSourcePath
from wb_tool.application.instrument_intake import WBIntakeProject, intake_digest
from wb_tool.application.intake_crop import WBIntakeCropProject
from wb_tool.application.intake_delivery import (
    IntakeDeliveryPlan,
    IntakeDeliveryReceipt,
    IntakeDeliveryRow,
    delivery_component,
    plan_intake_delivery,
    prepare_intake_delivery,
)
from wb_tool.application.intake_output import IntakeOutputPreparation, WBIntakeOutputProject
from wb_tool.application.intake_workflow import IntakeWorkflowTicket
from wb_tool.application.project_archive import ArchiveRunEvidence

OWNER = ".wb-delivery.json"


def _json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")


def _check(cancelled: Callable[[], bool]) -> None:
    if cancelled():
        raise ValueError("项目文件整理已取消，已发布文件保留")


def _safe(path: Path) -> None:
    if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
        raise ValueError("项目交付路径不能经过链接或junction")
    # Keep generated components short and bound the native path limit. Actual
    # filesystem failures remain explicit rather than truncating a destination.
    if len(str(path).encode("utf-16-le")) // 2 > 32760:
        raise ValueError("项目交付路径过长，请选择较短的输出父目录")


def _path(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative).parts
    if (
        not parts
        or PurePosixPath(relative).is_absolute()
        or any(p in {".", ".."} or "\\" in p or ":" in p for p in parts)
    ):
        raise ValueError("项目交付相对路径非法")
    path = root.joinpath(*parts)
    _safe(path)
    return path


def _identity(path: Path, cancelled: Callable[[], bool] = lambda: False) -> tuple[str, int]:
    _safe(path)
    if not path.is_file():
        raise ValueError("交付成员不是普通文件")
    digest = sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            _check(cancelled)
            digest.update(block)
    return digest.hexdigest(), path.stat().st_size


def select_intake_delivery(
    project: WBIntakeProject,
    *,
    workspace_path: str,
    output_parent: str,
    cancelled: Callable[[], bool] = lambda: False,
) -> WBIntakeProject:
    """Worker-only read phase: reuse an owned unsealed generation or propose a new one."""
    _check(cancelled)
    state = project.intake.delivery
    if (
        state is not None
        and os.path.normcase(str(Path(state.workspace_path).absolute()))
        == os.path.normcase(str(Path(workspace_path).absolute()))
        and os.path.normcase(str(Path(state.output_parent).absolute()))
        == os.path.normcase(str(Path(output_parent).absolute()))
        and state.plan_digest == plan_intake_delivery(project).digest
    ):
        root = _path(Path(state.output_parent).absolute(), state.directory_name)
        if not root.exists() or (
            root.is_dir()
            and not (root / "index.json").exists()
            and (root / OWNER).is_file()
            and (root / OWNER).read_bytes() == _owner(project)
            and _current_crop_records(project, root, cancelled)
        ):
            return project
    return prepare_intake_delivery(
        project, workspace_path=workspace_path, output_parent=output_parent, delivery_id=uuid4().hex
    )


def _render_digest(project: WBIntakeCropProject, row_id: str) -> str:
    from wb_tool.application.laboratory_layout import initial_composition

    composition = (
        project.composition if project.composition.slices else initial_composition(project)
    )
    row = next(r for r in project.rows if r.row_id == row_id)
    return sha256(
        _json(
            {
                "row": row.model_dump(mode="json"),
                "template": project.template.model_dump(mode="json"),
                "style": project.layout_style.model_dump(mode="json"),
                "slices": [
                    s.model_dump(mode="json") for s in composition.slices if s.row_id == row_id
                ],
            }
        )
    ).hexdigest()


def _current_crop_records(
    project: WBIntakeProject, root: Path, cancelled: Callable[[], bool]
) -> bool:
    """A changed crop/display recipe needs a new directory; completed files are immutable."""
    for row in plan_intake_delivery(project).rows:
        _check(cancelled)
        record = _path(root, row.directory + "/裁剪与来源记录.json")
        if not record.exists():
            continue
        if not isinstance(project, WBIntakeCropProject) or record.stat().st_size > 1024**2:
            return False
        evidence = next((e for e in project.intake_crops if e.row_id == row.row_id), None)
        if (
            evidence is None
            or evidence.raw_crop is None
            or not any(
                s.stage == "crop" and s.target_id == row.row_id and s.status == "done"
                for s in project.workflow.steps
            )
        ):
            return False
        try:
            data: object = json.loads(record.read_bytes())
        except (OSError, ValueError):
            return False
        if not isinstance(data, dict):
            return False
        fields = cast(dict[str, object], data)
        if fields.get("raw_crop_sha256") != evidence.raw_crop.sha256 or fields.get(
            "render_digest"
        ) != _render_digest(project, row.row_id):
            return False
    return True


def _publish_file(
    source: Path, target: Path, digest: str, size: int, cancelled: Callable[[], bool]
) -> None:
    """Idempotent only for exactly matching bytes; never replace user or old output files."""
    from wb_tool.adapters.intake_output import copy_intake_output_asset

    _safe(target)
    _check(cancelled)
    if target.exists():
        if _identity(target) != (digest, size):
            raise FileExistsError("已有交付文件内容不同，请创建新版本：" + str(target))
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = target.parent / (".delivery-" + uuid4().hex)
    try:
        copy_intake_output_asset(
            str(source),
            stage,
            AssetRef(
                asset_id="delivery", relative_path="assets/member", sha256=digest, size_bytes=size
            ),
            cancelled,
        )
        _check(cancelled)
        if os.name == "nt":
            os.rename(stage, target)
        else:
            os.link(stage, target)
    finally:
        stage.unlink(missing_ok=True)


def _bytes(root: Path, relative: str, value: bytes, cancelled: Callable[[], bool]) -> None:
    target = _path(root, relative)
    _check(cancelled)
    if target.exists():
        if target.read_bytes() != value:
            raise FileExistsError("交付记录已有不同版本，请创建新目录：" + relative)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a fully written file. The temporary path belongs to this call.
    with TemporaryDirectory(prefix=".delivery-record-", dir=target.parent) as temporary:
        source = Path(temporary) / "record"
        source.write_bytes(value)
        _publish_file(source, target, sha256(value).hexdigest(), len(value), cancelled)


def _context(
    project: WBIntakeProject, workspace_path: str, *, require_parent: bool = True
) -> tuple[Path, IntakeDeliveryPlan]:
    if not project.intake.confirmed_digest or project.intake.confirmed_digest != intake_digest(
        project
    ):
        raise ValueError("请先确认Fig名称、蛋白名称与来源分组")
    state = project.intake.delivery
    if state is None:
        raise ValueError("请先保存命名项目交付配置")
    if os.path.normcase(str(Path(workspace_path).absolute())) != os.path.normcase(
        str(Path(state.workspace_path).absolute())
    ):
        raise ValueError("项目已迁移，请为当前工作区创建新的交付目录")
    plan = plan_intake_delivery(project)
    if plan.digest != state.plan_digest:
        raise ValueError("名称或分组已变化，请创建新的项目交付版本")
    parent = Path(state.output_parent).absolute()
    _safe(parent)
    if require_parent and not parent.is_dir():
        raise ValueError("项目输出父目录不存在")
    root = _path(parent, state.directory_name)
    return root, plan


def _owner(project: WBIntakeProject) -> bytes:
    assert project.intake.delivery is not None
    return _json(
        {
            "policy": "intake_delivery@1",
            "project_id": project.project_id,
            "delivery": project.intake.delivery.model_dump(mode="json"),
        }
    )


def _open_root(
    project: WBIntakeProject, workspace_path: str, cancelled: Callable[[], bool]
) -> tuple[Path, IntakeDeliveryPlan]:
    _check(cancelled)
    root, plan = _context(project, workspace_path, require_parent=False)
    parent = root.parent
    if not parent.is_dir():
        if parent != Path(workspace_path).absolute() / "outputs":
            raise ValueError("项目输出父目录不存在")
        _check(cancelled)
        parent.mkdir(exist_ok=True)
    if root.exists():
        _safe(root / OWNER)
        if (
            not root.is_dir()
            or not (root / OWNER).is_file()
            or (root / OWNER).read_bytes() != _owner(project)
        ):
            raise ValueError("目标目录不属于本次交付，不能接管或写入")
        if (root / "index.json").exists():
            raise ValueError("该交付版本已封存，请创建新版本")
    else:
        root.mkdir()
        _bytes(root, OWNER, _owner(project), cancelled)
    return root, plan


def _source_name(original_name: str, source_id: str) -> str:
    return (
        delivery_component(Path(original_name).stem, source_id, limit=12)
        + Path(original_name).suffix.lower()
    )


def _coordinate_sources(project: WBIntakeCropProject, row: IntakeDeliveryRow) -> set[str]:
    """Only byte identity or an explicitly registered signal pair proves shared coordinates."""
    evidence = next(e for e in project.intake_crops if e.row_id == row.row_id)
    selected = next(s for s in project.intake.sources if s.source_id == row.selected_source_id)
    allowed = {
        s.source_id
        for s in project.intake.sources
        if s.source_id in row.source_ids and s.asset.sha256 == selected.asset.sha256
    }
    detection = evidence.detection
    if (
        detection is not None
        and evidence.geometry_policy
        in {"instrument_guided_geometry@2", "guided_common_band_geometry@1"}
        and "registered_signal_pair@1" in detection.flags
        and "group_signal_coordinates_unverified" not in detection.flags
    ):
        group = [s for s in project.intake.sources if s.source_id in row.source_ids]
        declared = {
            f.split(":", 1)[1] for f in detection.flags if f.startswith("verified_group_sha256:")
        }
        guide = {f.split(":", 1)[1] for f in detection.flags if f.startswith("guide_sha256:")}
        if (
            len(group) == 3
            and len(guide) == 1
            and declared == {s.asset.sha256 for s in group}
            and len({(s.width, s.height) for s in group}) == 1
        ):
            allowed.update(s.source_id for s in group if s.asset.sha256 not in guide)
    return allowed


def _row_crops(
    project: WBIntakeCropProject,
    row: IntakeDeliveryRow,
    paths: dict[str, str],
    root: Path,
    cancelled: Callable[[], bool],
) -> None:
    from wb_tool.adapters.crop_export import export_crop
    from wb_tool.adapters.figure_image_export import publish_rendered_image
    from wb_tool.adapters.laboratory_figure import render_display_segment
    from wb_tool.adapters.tiff_input import load_tiff
    from wb_tool.application.crop import CropRequest
    from wb_tool.application.laboratory_layout import (
        FigureColumn,
        FigureComposition,
        WBLayoutProject,
        figure_uses_standard_display,
        initial_composition,
        plan_laboratory_layout,
    )

    evidence = next((e for e in project.intake_crops if e.row_id == row.row_id), None)
    if (
        evidence is None
        or evidence.raw_crop is None
        or evidence.crop is None
        or not any(
            s.stage == "crop" and s.target_id == row.row_id and s.status == "done"
            for s in project.workflow.steps
        )
    ):
        raise ValueError("裁剪尚未真实提交，不能归入已完成裁图")
    raw = evidence.raw_crop
    if raw.sha256 not in paths:
        raise ValueError("已提交原值裁剪资产缺失")
    name = delivery_component(row.label, row.row_id, limit=12)
    _publish_file(
        Path(paths[raw.sha256]),
        _path(root, row.directory + "/原值裁剪/" + name + "_原值.tiff"),
        raw.sha256,
        raw.size_bytes,
        cancelled,
    )
    selected = next(r for r in project.rows if r.row_id == row.row_id)
    assert selected.source is not None
    composition = (
        project.composition if project.composition.slices else initial_composition(project)
    )
    projection = WBLayoutProject(
        project_id=project.project_id,
        rows=(selected,),
        figure_order=(selected.figure,),
        template=project.template,
        layout_style=project.layout_style,
        composition=FigureComposition(
            slices=tuple(s for s in composition.slices if s.row_id == row.row_id),
            columns=(FigureColumn(figure=selected.figure, column=1),),
        ),
    )
    layout = plan_laboratory_layout(projection, require_review=False)
    original = load_tiff(paths[selected.source.sha256])
    if original.sha256 != selected.source.sha256:
        raise ValueError("展示裁剪来源摘要不一致")
    with TemporaryDirectory(prefix="wb-delivery-crop-") as temporary:
        for i, placed in enumerate((s for line in layout.lines for s in line.segments), 1):
            _check(cancelled)
            x0, y0, x1, y1 = placed.output_box
            record: dict[str, object] = {
                "operation": "intake_delivery_display@1",
                "purpose": "display_only_not_quantitative",
                "row_id": row.row_id,
                "source_sha256": selected.source.sha256,
            }
            image = render_display_segment(
                original,
                replace(placed, output_box=(0, 0, x1 - x0, y1 - y0)),
                record,
                resample=figure_uses_standard_display(projection, selected.figure),
            )
            rendered = FigureRender(
                image.width, image.height, image.tobytes(), _json(record).decode()
            )
            for suffix in (".png", ".tiff"):
                file = Path(temporary) / (f"display-{i}" + suffix)
                # TIFF ASCII tags require escaped JSON. Keep PNG's existing UTF-8
                # bytes so a failed TIFF publication can resume its owned directory.
                encoded = (
                    replace(
                        rendered,
                        manifest_json=json.dumps(
                            record, ensure_ascii=True, sort_keys=True, allow_nan=False
                        ),
                    )
                    if suffix == ".tiff"
                    else rendered
                )
                publish_rendered_image(
                    encoded, project.template.dpi, str(file), cancelled=cancelled
                )
                digest, size = _identity(file)
                _publish_file(
                    file,
                    _path(root, row.directory + "/展示图片/" + name + f"_展示-{i:02d}" + suffix),
                    digest,
                    size,
                    cancelled,
                )
        allowed = _coordinate_sources(project, row)
        counterparts: list[dict[str, object]] = []
        for source_id in row.source_ids:
            source = next(s for s in project.intake.sources if s.source_id == source_id)
            if source_id == row.selected_source_id:
                continue
            status = "坐标未确认，保留原图，未生成对应裁图"
            if source_id in allowed:
                file = Path(temporary) / (sha256(source_id.encode()).hexdigest() + ".tiff")
                export_crop(
                    paths[source.asset.sha256],
                    CropRequest(source.asset.sha256, 0, evidence.crop),
                    str(file),
                    cancelled=cancelled,
                )
                digest, size = _identity(file)
                _publish_file(
                    file,
                    _path(
                        root,
                        row.directory
                        + "/原值裁剪/"
                        + _source_name(source.original_name, source.source_id)
                        + "_对应.tiff",
                    ),
                    digest,
                    size,
                    cancelled,
                )
                status = "同坐标证据通过，已生成对应原值裁剪"
            counterparts.append(
                {"source_id": source_id, "sha256": source.asset.sha256, "status": status}
            )
    _bytes(
        root,
        row.directory + "/裁剪与来源记录.json",
        _json(
            {
                "row_id": row.row_id,
                "source_sha256": selected.source.sha256,
                "raw_crop_sha256": raw.sha256,
                "render_digest": _render_digest(project, row.row_id),
                "roi": asdict(evidence.crop),
                "display_slices": [
                    s.model_dump(mode="json") for s in projection.composition.slices
                ],
                "companions": counterparts,
            }
        ),
        cancelled,
    )


def materialize_intake_delivery(
    project: WBIntakeProject,
    sources: tuple[FigureSourcePath, ...],
    *,
    workspace_path: str,
    row_id: str = "",
    cancelled: Callable[[], bool] = lambda: False,
) -> IntakeDeliveryReceipt:
    """After configuration CAS create all groups; after crop CAS call with its stable row ID."""
    root, plan = _open_root(project, workspace_path, cancelled)
    paths = {p.sha256: p.path for p in sources}
    if len(paths) != len(sources):
        raise ValueError("交付来源路径摘要重复")
    if sum(s.asset.size_bytes for s in project.intake.sources) > 2 * 1024**3:
        raise ValueError("交付原始来源超过2GiB预算")
    mapping: list[dict[str, object]] = []
    by_id = {s.source_id: s for s in project.intake.sources}
    for figure in plan.figures:
        _path(root, figure.directory).mkdir(parents=True, exist_ok=True)
    for row in plan.rows:
        for directory in ("原始图片", "原值裁剪", "展示图片"):
            _path(root, row.directory + "/" + directory).mkdir(parents=True, exist_ok=True)
    placements = [
        (row.directory + "/原始图片", sid, row.row_id)
        for row in plan.rows
        for sid in row.source_ids
    ]
    placements += [("未分配来源", sid, "") for sid in plan.unassigned_source_ids]
    for directory, source_id, owner in placements:
        _check(cancelled)
        source = by_id[source_id]
        if source.asset.sha256 not in paths:
            raise ValueError("项目原始来源缺失：" + source.original_name)
        relative = directory + "/" + _source_name(source.original_name, source_id)
        _publish_file(
            Path(paths[source.asset.sha256]),
            _path(root, relative),
            source.asset.sha256,
            source.asset.size_bytes,
            cancelled,
        )
        mapping.append(
            {
                "row_id": owner,
                "source_id": source_id,
                "original_name": source.original_name,
                "original_relative_path": source.relative_path,
                "sha256": source.asset.sha256,
                "path": relative,
            }
        )
    _bytes(
        root,
        "记录/文件名对应表.json",
        _json(
            {
                "figures": [asdict(f) for f in plan.figures],
                "rows": [asdict(r) for r in plan.rows],
                "sources": mapping,
            }
        ),
        cancelled,
    )
    _bytes(
        root,
        "项目说明.txt",
        "本目录按Fig和蛋白保存完整项目。原值裁剪保留原像素；展示图经过显示变换。\n只有index.json完成核验后才是已封存快照；未完成项保留原因。恢复请在软件选择本目录或项目恢复.zip。\n".encode(),
        cancelled,
    )
    if row_id:
        row = next((r for r in plan.rows if r.row_id == row_id), None)
        if row is None or not isinstance(project, WBIntakeCropProject):
            raise ValueError("待归位裁剪不属于当前项目")
        _row_crops(project, row, paths, root, cancelled)
    elif isinstance(project, WBIntakeCropProject):
        completed = {
            s.target_id for s in project.workflow.steps if s.stage == "crop" and s.status == "done"
        }
        for row in plan.rows:
            if row.row_id in completed:
                _check(cancelled)
                _row_crops(project, row, paths, root, cancelled)
    assert project.intake.delivery is not None
    return IntakeDeliveryReceipt(
        project.project_id, project.intake.delivery.delivery_id, plan.digest, str(root), row_id
    )


def finalize_intake_delivery(
    project: WBIntakeOutputProject,
    sources: tuple[FigureSourcePath, ...],
    *,
    workspace_path: str,
    runs: tuple[ArchiveRunEvidence, ...] = (),
    ticket: IntakeWorkflowTicket | None = None,
    cancelled: Callable[[], bool] = lambda: False,
) -> IntakeOutputPreparation:
    """Reuse the standard archive verifier, then seal the already populated human directory."""
    from wb_tool.adapters.intake_output import export_intake_outputs
    from wb_tool.adapters.intake_table_export import intake_table_bytes
    from wb_tool.adapters.project_evidence import verify_project_evidence
    from wb_tool.application.instrument_intake import intake_digest
    from wb_tool.application.intake_execution import build_intake_execution_plan
    from wb_tool.application.project_archive import project_runs

    materialize_intake_delivery(
        project, sources, workspace_path=workspace_path, cancelled=cancelled
    )
    root, plan = _context(project, workspace_path)
    with TemporaryDirectory(prefix="wb-delivery-final-") as temporary:
        legacy = Path(temporary) / "snapshot"
        prepared = export_intake_outputs(
            project, sources, str(legacy), runs=runs, ticket=ticket, cancelled=cancelled
        )
        # Reuse the standard export's frozen copies, never race external run files again.
        frozen = tuple(
            ArchiveRunEvidence(
                run,
                str(legacy / "runs" / f"{i:04d}" / "request.json"),
                str(legacy / "runs" / f"{i:04d}" / "result.json"),
            )
            for i, run in enumerate(project_runs(project), 1)
        )
        verified = verify_project_evidence(project, frozen, cancelled=cancelled)
        files: list[tuple[str, str]] = [
            ("all-figures.png", "完整拼图.png"),
            ("all-figures.tiff", "完整拼图.tiff"),
            ("measurements.csv", "灰度汇总.csv"),
            ("measurements.xlsx", "灰度汇总.xlsx"),
            ("project.zip", "项目恢复.zip"),
        ]
        execution = build_intake_execution_plan(project, expected_digest=intake_digest(project))
        for figure in plan.figures:
            original = next(f for f in execution.figures if f.figure_id == figure.figure_id)
            name = delivery_component(figure.label, figure.figure_id, limit=12)
            for suffix in (".png", ".tiff"):
                files.append(
                    (
                        str(PurePosixPath(original.image_path).with_suffix(suffix)),
                        figure.directory + "/" + name + "_拼图" + suffix,
                    )
                )
            for suffix in (".csv", ".xlsx"):
                _bytes(
                    root,
                    figure.directory + "/" + name + "_灰度" + suffix,
                    intake_table_bytes(
                        project, verified.results, csv=suffix == ".csv", figure_id=figure.figure_id
                    ),
                    cancelled,
                )
        for name in (
            "project.json",
            "intake.json",
            "status.json",
            "measurement-audit.csv",
            "measurement-audit.xlsx",
            "all-figures-layout.json",
        ):
            files.append((name, "记录/" + name))
        for file in (legacy / "runs").rglob("*"):
            if file.is_file():
                files.append(
                    (
                        file.relative_to(legacy).as_posix(),
                        "记录/" + file.relative_to(legacy).as_posix(),
                    )
                )
        for source, target in files:
            _check(cancelled)
            file = legacy / source
            if file.is_file():
                digest, size = _identity(file)
                _publish_file(file, _path(root, target), digest, size, cancelled)
            elif prepared.complete or source in {
                "measurements.csv",
                "measurements.xlsx",
                "project.json",
                "status.json",
            }:
                raise ValueError("已核验快照成员在交付前缺失：" + source)
        members: list[dict[str, object]] = []
        for file in sorted(root.rglob("*")):
            _check(cancelled)
            _safe(file)
            if file.is_file():
                digest, size = _identity(file)
                members.append(
                    {
                        "path": file.relative_to(root).as_posix(),
                        "sha256": digest,
                        "size_bytes": size,
                    }
                )
                if len(members) > 10000:
                    raise ValueError("项目交付文件超过10000成员预算，未封存")
        data = _json(
            {
                "policy": "intake_output@1",
                "layout_policy": "intake_delivery@1",
                "table_policy": "intake_visible_table@1",
                "output_id": prepared.output_id,
                "project_id": project.project_id,
                "revision": project.revision,
                "input_digest": prepared.input_digest,
                "complete": prepared.complete,
                "errors": prepared.errors,
                "archive": "项目恢复.zip",
                "members": members,
            }
        )
        if len(data) > 16 * 1024**2:
            raise ValueError("项目交付索引超过16MiB预算")
        _bytes(root, "index.json", data, cancelled)
        return prepared.model_copy(
            update={
                "destination": str(root),
                "path": str(root / "index.json"),
                "sha256": sha256(data).hexdigest(),
                "size_bytes": len(data),
            }
        )


def inspect_intake_delivery(path: str, *, cancelled: Callable[[], bool] = lambda: False) -> str:
    """Validate all declared members before returning the standard archive to the restore job."""
    root = Path(path).absolute()
    _check(cancelled)
    _safe(root)
    index = root / "index.json"
    _safe(index)
    if not index.is_file() or index.stat().st_size > 16 * 1024**2:
        raise ValueError("完整项目索引不存在或过大")
    payload: object = json.loads(index.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError("完整项目索引无效")
    data = cast(dict[str, object], payload)
    if data.get("policy") != "intake_output@1" or data.get("layout_policy") != "intake_delivery@1":
        raise ValueError("不支持此项目交付格式")
    records = data.get("members")
    if not isinstance(records, list) or len(cast(list[object], records)) > 10000:
        raise ValueError("交付成员清单无效或过大")
    seen: set[str] = set()
    for entry in cast(list[object], records):
        _check(cancelled)
        if not isinstance(entry, dict):
            raise ValueError("交付成员记录无效")
        record = cast(dict[str, object], entry)
        relative = record.get("path")
        if not isinstance(relative, str) or relative.casefold() in seen:
            raise ValueError("交付成员路径无效或重复")
        seen.add(relative.casefold())
        if _identity(_path(root, relative), cancelled) != (
            record.get("sha256"),
            record.get("size_bytes"),
        ):
            raise ValueError("项目交付成员摘要不一致：" + relative)
    archive = data.get("archive")
    if not isinstance(archive, str) or archive != "项目恢复.zip" or archive.casefold() not in seen:
        raise ValueError("项目恢复归档缺失，请查看部分输出说明")
    actual: set[str] = set()
    for file in root.rglob("*"):
        _check(cancelled)
        _safe(file)
        if file.is_file() and file != index:
            actual.add(file.relative_to(root).as_posix().casefold())
    if actual != seen:
        raise ValueError("项目交付目录成员集合与索引不一致")
    return str(_path(root, archive))
