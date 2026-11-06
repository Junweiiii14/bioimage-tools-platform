"""Fixed editor commands executed only by the existing workspace storage owner."""

import base64
import csv
import io
from pathlib import Path
from uuid import uuid4

from platform_runtime.api import (
    IntegrityError,
    StateConflict,
    WorkflowValidationError,
    Workspace,
    compile_workflow,
    load_workflow_ledger,
    validate_workflow_result_selection,
)
from pydantic import ValidationError
from tool_contracts.api import (
    NodePosition,
    OutputManifest,
    WorkflowBatch,
    WorkflowBatchItem,
    WorkflowDefinition,
    WorkflowIssue,
    WorkflowLayout,
    canonical_module_json,
)

from bioimage_app.research_authoring import (
    bind_research_template,
    research_definition,
    research_modules,
)
from bioimage_app.workflow_authoring_models import (
    AuthoringCommand,
    AuthoringGraph,
    AuthoringModule,
    AuthoringOutput,
    AuthoringProject,
    AuthoringProjection,
    AuthoringRunNode,
    AuthoringSampleState,
    AuthoringSource,
)
from bioimage_app.workflow_batch_storage import WorkflowBatchStoreCommand, execute_batch_store
from bioimage_app.workflow_template import WorkflowTemplate, load_workflow_template

_TOOL = "workflow_authoring_v1"
_TITLES = {
    "nuclei-stardist-research": "固定 StarDist 核分割 · 研究",
    "bca-pierce25-research": "Pierce25 BCA 浓度 · 研究",
    "wb-verify-original": "原图预检",
    "wb-analyze-original": "WB 粗分析",
    "wb-publish-original": "发布表与曲线",
}
_LIMITS = {
    "nuclei-stardist-research": (
        "仅原始 uint8 灰度 TIFF；固定 StarDist 方法，参数锁定。模型由工具设置准备，科学适用性未验。"
    ),
    "bca-pierce25-research": (
        "原始 A562 长 CSV + 明确板记录；固定 Pierce25 / BCA API 0.1.1，参数锁定。"
        "partial 不等于零，LoQ 未知。"
    ),
    "wb-verify-original": "原始二维 uint8/uint16；保留位深、坐标与来源，不接收显示图。",
    "wb-analyze-original": "沿已有 WB 旧方法；无效、未检测、待复核与真实零分开，科学适用性未验。",
    "wb-publish-original": "发布节点共用一致报告画布；显示样式不改变定量。",
}


def load_authoring_project(store: Workspace, document_id: str) -> AuthoringProject:
    draft = store.load_draft(document_id)
    project = AuthoringProject.model_validate_json(store.read_asset(draft.asset), strict=True)
    if (draft.tool_id, draft.document_id, draft.revision) != (
        _TOOL,
        project.document_id,
        project.revision,
    ):
        raise StateConflict("Editor document identity differs from its saved revision")
    return project


def _save(store: Workspace, project: AuthoringProject, previous: int | None) -> None:
    store.save_draft(
        project.document_id,
        _TOOL,
        project.revision,
        project.model_dump_json().encode(),
        expected_previous_revision=previous,
    )


def _preflight(project: AuthoringProject) -> AuthoringProjection:
    primary = next(s.asset for s in project.sources if s.sample_id == project.graph.sample_id)
    assert primary is not None
    defaults = {
        node.module.module_id: node.parameters_json for node in reversed(project.seed.nodes)
    }
    issue: WorkflowIssue | None = None
    if project.tool != "wb":
        sample = next(s for s in project.sources if s.sample_id == project.graph.sample_id)
        modules = research_modules(project.tool, sample)
    else:
        from wb_tool.api import WBReportParameters

        from bioimage_app.wb_workflow_host import wb_workflow_modules

        seed_report = WBReportParameters.model_validate_json(defaults["wb-publish-original"])
        report_node = next(
            (
                node
                for node in project.graph.nodes
                if node.module.module_id == "wb-publish-original"
            ),
            None,
        )
        report = seed_report
        if report_node is not None:
            try:
                report = WBReportParameters.model_validate_json(report_node.parameters_json)
            except ValidationError as error:
                # The saved incomplete draft remains visible, but no plan is admitted.
                issue = WorkflowIssue(
                    code="parameters_invalid",
                    node_id=report_node.node_id,
                    message=str(error)[:1024],
                )
        modules = wb_workflow_modules(primary, report)
        defaults["wb-publish-original"] = report.model_dump_json()
    catalogue = tuple(
        AuthoringModule(
            title=_TITLES[host.registration.interface.module.module_id],
            interface=host.registration.interface,
            parameters_json=defaults[host.registration.interface.module.module_id],
            limits=_LIMITS[host.registration.interface.module.module_id],
        )
        for host in modules
    )
    if issue is not None:
        return AuthoringProjection(project=project, catalogue=catalogue, issues=(issue,))
    try:
        definition = WorkflowDefinition.model_validate(project.graph.model_dump(mode="python"))
    except ValidationError as error:
        return AuthoringProjection(
            project=project,
            catalogue=catalogue,
            issues=(WorkflowIssue(code="draft_incomplete", message=str(error)[:1024]),),
        )
    try:
        plan = compile_workflow(
            definition, tuple(m.registration for m in modules), modules[0].environment
        )
    except WorkflowValidationError as error:
        return AuthoringProjection(project=project, catalogue=catalogue, issues=error.issues)
    return AuthoringProjection(project=project, catalogue=catalogue, issues=(), plan=plan)


def _inputs(store: Workspace, command: AuthoringCommand) -> tuple[AuthoringSource, ...]:
    if command.tool != "wb":
        if command.validation_cases or len(command.source_paths) != 1:
            raise ValueError("研究流程每次绑定一个真实输入；BCA 还需对应板记录")
        path = command.source_paths[0]
        if command.tool == "bca":
            from bca_tool.api import read_plate

            from bioimage_app.bca_cli import import_sources as import_bca_sources

            if not command.record_path:
                raise ValueError("BCA 需要明确的板记录 JSON")
            asset, record = import_bca_sources(
                store, path, command.record_path, read_plate(path, command.record_path)
            )
            # Each newly bound plate is a distinct editor input, even with reused plate IDs.
            sample_id = uuid4().hex
            asset = asset.model_copy(update={"sample_id": sample_id})
            record = record.model_copy(update={"sample_id": sample_id})
        else:
            from nuclei_tool.api import read_nuclei_input

            from bioimage_app.nuclei_cli import import_source as import_nuclei_source

            asset, record = (
                import_nuclei_source(store, path, uuid4().hex, read_nuclei_input(path)),
                None,
            )
        return (
            AuthoringSource(
                sample_id=asset.sample_id, label=Path(path).name, asset=asset, record=record
            ),
        )
    from wb_tool.api import wb_validation_input

    from bioimage_app.workflow_input import import_wb_workflow_source

    result: list[AuthoringSource] = []
    for supplied in command.validation_cases or command.source_paths:
        sample_id = uuid4().hex
        label = supplied if command.validation_cases else Path(supplied).name
        try:
            source = import_wb_workflow_source(
                store,
                wb_validation_input(supplied) if command.validation_cases else supplied,
                sample_id=sample_id,
            )
        except (ValueError, FileNotFoundError, PermissionError, IntegrityError) as error:
            result.append(
                AuthoringSource(
                    sample_id=sample_id,
                    label=label,
                    reason=str(error)[:1024] or type(error).__name__,
                )
            )
        else:
            result.append(AuthoringSource(sample_id=sample_id, label=label, asset=source))
    return tuple(result)


def _initialize(store: Workspace, command: AuthoringCommand) -> AuthoringProject:
    sources = _inputs(store, command)
    primary = next((s.asset for s in sources if s.asset is not None), None)
    if primary is None:
        raise ValueError("没有可用原图：" + "; ".join(s.reason for s in sources))
    if command.template_path:
        with Path(command.template_path).open("rb") as stream:
            template = load_workflow_template(stream.read(1048577).decode("utf-8"))
        if command.tool == "wb":
            from bioimage_app.wb_workflow_host import bind_wb_workflow_template

            definition, _plan = bind_wb_workflow_template(template.definition, primary)
        else:
            definition, _plan = bind_research_template(
                template.definition, sources[0], command.tool
            )
        layout = template.layout
    elif command.tool != "wb":
        definition = research_definition(command.tool, sources[0])
        layout = WorkflowLayout(
            positions=(NodePosition(node_id=definition.nodes[0].node_id, x=40.0, y=40.0),)
        )
    else:
        from wb_tool.api import LaneROI, load_tiff, suggest_analysis_for_crop, wb_validation_input

        from bioimage_app.wb_workflow_host import build_wb_workflow

        if command.validation_cases:
            request = wb_validation_input(command.validation_cases[0]).request
        else:
            assert command.lane_count is not None
            image = load_tiff(store.asset_path(primary.payload))
            height, width = image.pixels.shape
            request = suggest_analysis_for_crop(
                image,
                crop=LaneROI("original", x0=0, y0=0, x1=width, y1=height),
                lane_count=command.lane_count,
                revision=0,
                polarity=command.polarity,
            )
        definition, _plan = build_wb_workflow(primary, request)
        layout = WorkflowLayout(
            positions=tuple(
                NodePosition(node_id=node.node_id, x=float(index * 300), y=40.0)
                for index, node in enumerate(definition.nodes)
            )
        )
    return AuthoringProject(
        schema_version=2,
        tool=command.tool,
        document_id=command.document_id,
        graph=AuthoringGraph.model_validate(definition.model_dump(mode="python")),
        layout=layout,
        sources=sources,
        seed=definition,
    )


def _edit(project: AuthoringProject, command: AuthoringCommand) -> AuthoringProject:
    assert command.graph is not None and command.layout is not None
    graph = command.graph
    if (graph.workflow_id, graph.sample_id, graph.workflow_version) != (
        project.graph.workflow_id,
        project.graph.sample_id,
        project.graph.workflow_version,
    ):
        raise ValueError("Editing cannot replace workflow/source identity; bind inputs explicitly")
    computational = graph.model_dump(exclude={"revision", "title"}) != project.graph.model_dump(
        exclude={"revision", "title"}
    )
    graph = graph.model_copy(update={"revision": project.graph.revision + int(computational)})
    return project.model_copy(
        update={
            "schema_version": 2,
            "graph": graph,
            "layout": command.layout,
            "revision": project.revision + 1,
        }
    )


def _freeze(
    store: Workspace, project: AuthoringProject, definition: WorkflowDefinition
) -> WorkflowBatch:
    old: dict[str, str] = {}
    documents = {d.document_id for d in store.list_documents()}
    if project.last_batch_id:
        previous = execute_batch_store(
            store, WorkflowBatchStoreCommand("load", project.last_batch_id)
        )
        if previous.state in ("running", "pausing", "paused", "cancelling"):
            raise StateConflict("当前批次尚未结束，请先继续或取消，再运行新修订")
        old = {
            item.sample_id: item.execution_id
            for item in previous.items
            if item.execution_id in documents
        }
    items: list[WorkflowBatchItem] = []
    for sample in project.sources:
        plan = None
        reason = sample.reason
        if sample.asset is not None:
            try:
                if project.tool == "wb":
                    from bioimage_app.wb_workflow_host import bind_wb_workflow_template

                    _bound, plan = bind_wb_workflow_template(definition, sample.asset)
                else:
                    _bound, plan = bind_research_template(definition, sample, project.tool)
            except ValueError as error:
                reason = str(error)[:1024]
        items.append(
            WorkflowBatchItem(
                sample_id=sample.sample_id,
                execution_id=uuid4().hex,
                plan=plan,
                cache_execution_id=old.get(sample.sample_id),
                state="pending" if plan is not None else "failed",
                reason=reason or None,
            )
        )
    batch = WorkflowBatch(batch_id=uuid4().hex, items=tuple(items))
    # Durable batch identity precedes any process dispatch. If the following editor
    # CAS fails this remains a discoverable, unstarted batch, never a fake success.
    return execute_batch_store(
        store, WorkflowBatchStoreCommand("create", batch.batch_id, batch=batch)
    )


def _run_mapping(projection: AuthoringProjection, batch: WorkflowBatch | None) -> dict[str, object]:
    if batch is None:
        return {"batch": None, "execution_nodes": (), "samples": (), "matches_run": False}
    plan = next((item.plan for item in batch.items if item.plan is not None), None)
    nodes = (
        tuple(
            AuthoringRunNode(
                node_id=node.node_id,
                module_id=node.interface.module.module_id,
                title=_TITLES[node.interface.module.module_id],
            )
            for node in plan.nodes
        )
        if plan
        else ()
    )
    labels = {source.sample_id: source.label for source in projection.project.sources}
    samples = tuple(
        AuthoringSampleState(
            sample_id=sample.sample_id,
            label=labels.get(sample.sample_id, f"批次输入 {index + 1}"),
            state=sample.state,
            reason=sample.reason or "",
        )
        for index, sample in enumerate(batch.items)
    )
    matching = (
        plan is not None
        and projection.plan is not None
        and (
            tuple((node.node_id, node.computation_key) for node in plan.nodes)
            == tuple((node.node_id, node.computation_key) for node in projection.plan.nodes)
        )
    )
    return {"batch": batch, "execution_nodes": nodes, "samples": samples, "matches_run": matching}


def _outputs(
    store: Workspace, project: AuthoringProject, command: AuthoringCommand
) -> tuple[WorkflowBatch, tuple[AuthoringOutput, ...], str]:
    batch_id = command.batch_id or project.last_batch_id
    if not batch_id:
        raise ValueError("尚无已启动的工作流批次")
    batch = execute_batch_store(store, WorkflowBatchStoreCommand("load", batch_id))
    documents = {document.document_id for document in store.list_documents()}
    preview_sample = command.sample_id or next(
        (sample.sample_id for sample in batch.items if sample.state in ("succeeded", "issues")),
        batch.items[0].sample_id,
    )
    outputs: list[AuthoringOutput] = []
    opened = ""
    for sample in batch.items:
        if command.sample_id and sample.sample_id != command.sample_id:
            continue
        if sample.execution_id not in documents:
            continue
        child = load_workflow_ledger(
            store.read_asset(store.load_draft(sample.execution_id).asset).decode("utf-8")
        )
        if child.plan != sample.plan:
            raise StateConflict("Child results differ from the persisted frozen batch")
        for result in child.results:
            if command.node_id and result.node_id != command.node_id:
                continue
            run = store.get_run(result.run.run_id)
            if run.result is None:
                raise StateConflict("Selected run has no committed result manifest")
            manifest = OutputManifest.model_validate_json(store.read_asset(run.result))
            node = next(node for node in child.plan.nodes if node.node_id == result.node_id)
            validate_workflow_result_selection(child, node, result, run, manifest)
            if store.read_asset(run.request) != manifest.request.model_dump_json().encode():
                raise StateConflict("保存的请求与提交清单不一致")
            for bound in manifest.request.inputs:
                store.asset_path(bound.asset)
            for committed in result.outputs:
                store.asset_path(committed.asset)
            nuclei_display = None
            if node.interface.module.module_id == "nuclei-stardist-research":
                from nuclei_tool.api import present_nuclei_result, read_nuclei_input

                members = {item.port: item.asset for item in result.outputs}
                source = read_nuclei_input(str(store.asset_path(manifest.request.inputs[0].asset)))
                nuclei_display = present_nuclei_result(
                    source,
                    store.read_asset(members["labels"]),
                    store.read_asset(members["provenance"]),
                    manifest.request,
                )
            for output in result.outputs:
                if command.port and output.port != command.port:
                    continue
                text, preview = "", ""
                table: tuple[tuple[str, ...], ...] = ()
                table_rows = 0
                if command.operation == "open":
                    opened = str(store.asset_path(output.asset))
                elif nuclei_display is not None and output.port == "labels":
                    preview = "data:image/png;base64," + base64.b64encode(
                        nuclei_display.overlay_png
                    ).decode("ascii")
                    text = f"核数：{nuclei_display.count}；原坐标 uint32 实例标签；叠加图仅显示。"
                elif sample.sample_id == preview_sample and output.asset.size_bytes <= 262144:
                    data = store.read_asset(output.asset)
                    if output.kind == "display_image":
                        preview = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
                    else:
                        text = data.decode("utf-8-sig")
                        if output.kind == "typed_table" or (
                            node.interface.module.module_id == "bca-pierce25-research"
                            and output.port in ("wells", "samples")
                        ):
                            rows = tuple(tuple(row) for row in csv.reader(io.StringIO(text)))
                            table_rows = max(0, len(rows) - 1)
                            table = rows[:101]
                else:
                    store.asset_path(output.asset)
                outputs.append(
                    AuthoringOutput(
                        batch_id=batch_id,
                        sample_id=sample.sample_id,
                        node_id=result.node_id,
                        port=output.port,
                        kind=output.kind,
                        asset=output.asset,
                        text=text,
                        preview=preview,
                        table=table,
                        table_rows=table_rows,
                    )
                )
    if command.operation == "open" and not opened:
        raise ValueError("未找到该已提交成果，不能从调用方路径打开文件")
    return batch, tuple(outputs), opened


def execute_authoring_store(
    store: Workspace,
    raw: bytes,
    *,
    nuclei_configuration: tuple[str, str] = ("", ""),
    unavailable_tools: dict[str, str] | None = None,
) -> AuthoringProjection:
    if len(raw) > 1048576:
        raise ValueError("Editor command exceeds the 1MiB input budget")
    command = AuthoringCommand.model_validate_json(
        canonical_module_json(raw.decode("utf-8")), strict=True
    )
    unavailable_tools = unavailable_tools or {}
    if command.operation == "initialize":
        if command.tool in unavailable_tools:
            raise ValueError(unavailable_tools[command.tool] + "；请准备工具后重启。")
        project = _initialize(store, command)
        _save(store, project, None)
        return _preflight(project).model_copy(update={"operation": command.operation})
    project = load_authoring_project(store, command.document_id)
    if project.tool in unavailable_tools:
        raise ValueError(
            unavailable_tools[project.tool] + "；此历史项目不可执行，原图和成果保持原样。"
        )
    if (
        command.operation in ("save", "freeze", "bind")
        and command.previous_revision != project.revision
    ):
        raise StateConflict("Editor CAS revision changed; keep the current unsaved draft")
    if command.operation == "load":
        batch = (
            execute_batch_store(store, WorkflowBatchStoreCommand("load", project.last_batch_id))
            if project.last_batch_id
            else None
        )
        projection = _preflight(project)
        return projection.model_copy(
            update={"operation": command.operation, **_run_mapping(projection, batch)}
        )
    if command.operation in ("save", "freeze"):
        updated = _edit(project, command)
        projection = _preflight(updated)
        batch = None
        if command.operation == "freeze" and projection.plan is not None:
            if updated.tool == "nuclei":
                from nuclei_tool.api import verify_model

                worker, model = nuclei_configuration
                nodes = ", ".join(n.node_id + "/source" for n in updated.graph.nodes)
                if not worker or not Path(worker).is_file() or not model:
                    raise ValueError(
                        nodes + "：核分割运行环境未配置，请在首页核分割工具设置中准备环境与模型，"
                        "再重开工作流"
                    )
                try:
                    verify_model(model)
                except (ValueError, OSError) as error:
                    raise ValueError(nodes + ": " + str(error)) from error
            definition = WorkflowDefinition.model_validate(updated.graph.model_dump(mode="python"))
            batch = _freeze(store, updated, definition)
            updated = updated.model_copy(update={"last_batch_id": batch.batch_id})
        elif command.operation == "save" and updated.last_batch_id:
            batch = execute_batch_store(
                store, WorkflowBatchStoreCommand("load", updated.last_batch_id)
            )
        _save(store, updated, project.revision)
        return projection.model_copy(
            update={
                "operation": command.operation,
                "project": updated,
                **_run_mapping(projection, batch),
            }
        )
    if command.operation == "bind":
        command = command.model_copy(update={"tool": project.tool})
        sources = _inputs(store, command)
        primary = next((s.asset for s in sources if s.asset is not None), None)
        if primary is None:
            raise ValueError("没有可绑定的原图：" + "; ".join(s.reason for s in sources))
        definition = WorkflowDefinition.model_validate(project.graph.model_dump(mode="python"))
        if project.tool == "wb":
            from bioimage_app.wb_workflow_host import bind_wb_workflow_template

            bound, _plan = bind_wb_workflow_template(definition, primary)
            seed, _seed_plan = bind_wb_workflow_template(project.seed, primary)
        else:
            bound, _plan = bind_research_template(definition, sources[0], project.tool)
            seed, _seed_plan = bind_research_template(project.seed, sources[0], project.tool)
        updated = project.model_copy(
            update={
                "schema_version": 2,
                "revision": project.revision + 1,
                "graph": AuthoringGraph.model_validate(bound.model_dump(mode="python")),
                "seed": seed,
                "sources": sources,
            }
        )
        _save(store, updated, project.revision)
        return _preflight(updated).model_copy(update={"operation": command.operation})
    projection = _preflight(project)
    if command.operation == "export":
        if projection.issues:
            raise ValueError("流程仍有预检问题，先修正后再保存可运行实验室模板")
        definition = WorkflowDefinition.model_validate(project.graph.model_dump(mode="python"))
        with Path(command.destination).open("x", encoding="utf-8") as stream:
            stream.write(
                WorkflowTemplate(definition=definition, layout=project.layout).model_dump_json()
            )
        return projection.model_copy(update={"operation": command.operation})
    batch, outputs, opened = _outputs(store, project, command)
    return projection.model_copy(
        update={
            "operation": command.operation,
            **_run_mapping(projection, batch),
            "outputs": outputs,
            "opened_path": opened,
        }
    )
