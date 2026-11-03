"""Explicit WB sample bindings; bad inputs retain individual failure records."""

from pathlib import Path
from typing import Literal, Self
from uuid import uuid4

from platform_runtime.api import (
    IntegrityError,
    Workspace,
    execution_plan_definition,
    workflow_definition_json,
)
from pydantic import BaseModel, ConfigDict, Field, model_validator
from tool_contracts.api import WorkflowBatch, WorkflowBatchItem, WorkflowDefinition
from wb_tool.api import WBModuleInput, read_wb_module_input, wb_validation_input

from bioimage_app.wb_workflow_host import bind_wb_workflow_template, build_wb_workflow
from bioimage_app.workflow_batch_storage import WorkflowBatchStoreCommand, execute_batch_store
from bioimage_app.workflow_input import import_wb_workflow_source


class WBWorkflowBatchInput(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    sample_id: str
    source: str = ""
    parameters: str = ""
    validation: Literal[
        "", "triangle_u8", "triangle_u16", "flat_zero", "invalid_roi", "dtype_limits"
    ] = ""

    @model_validator(mode="after")
    def explicit_source(self) -> Self:
        if bool(self.source) == bool(self.validation):
            raise ValueError("Choose either a real source or an explicit synthetic validation")
        if self.validation and self.parameters:
            raise ValueError("Synthetic validation carries its own analytical parameters")
        return self


class WBWorkflowBatchInputs(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    format: Literal["wb_workflow_batch@1"] = "wb_workflow_batch@1"
    samples: tuple[WBWorkflowBatchInput, ...] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def unique_samples(self) -> Self:
        if len({sample.sample_id for sample in self.samples}) != len(self.samples):
            raise ValueError("Duplicate input sample identity")
        return self


def prepare_wb_batch_workspace(
    workspace: Path,
    inputs: WBWorkflowBatchInputs,
    *,
    relative_to: Path,
    layout: str | None = None,
    template: WorkflowDefinition | None = None,
    template_out: Path | None = None,
) -> WorkflowBatch:
    items: list[WorkflowBatchItem] = []
    exported: WorkflowDefinition | None = None
    with Workspace.create(workspace) as store:
        for sample in inputs.samples:
            execution_id = uuid4().hex
            try:
                if template is not None and sample.parameters:
                    raise ValueError(
                        "Template parameters cannot be mixed with per-sample parameter files"
                    )
                if sample.validation:
                    supplied: WBModuleInput | str = wb_validation_input(sample.validation)
                elif template is not None:
                    supplied = str(relative_to / sample.source)
                else:
                    if not sample.parameters:
                        raise ValueError("Real sources require explicit AnalysisRequest parameters")
                    supplied = read_wb_module_input(
                        str(relative_to / sample.source), str(relative_to / sample.parameters)
                    )
                source = import_wb_workflow_source(store, supplied, sample.sample_id)
                if template is None:
                    assert isinstance(supplied, WBModuleInput)
                    definition, plan = build_wb_workflow(
                        source, supplied.request, layout=layout or "comfortable"
                    )
                else:
                    definition, plan = bind_wb_workflow_template(template, source, layout=layout)
                if exported is None:
                    exported = definition
                item = WorkflowBatchItem(
                    sample_id=sample.sample_id, execution_id=execution_id, plan=plan
                )
            except (ValueError, FileNotFoundError, PermissionError, IntegrityError) as error:
                item = WorkflowBatchItem(
                    sample_id=sample.sample_id,
                    execution_id=execution_id,
                    plan=None,
                    state="failed",
                    reason=(type(error).__name__ + ": " + str(error))[:1024],
                )
            items.append(item)
    batch = WorkflowBatch(batch_id=uuid4().hex, items=tuple(items))
    if template_out is not None:
        if exported is None:
            raise ValueError("No usable workflow is available to export as a template")
        with template_out.open("x", encoding="utf-8") as stream:
            stream.write(workflow_definition_json(exported))
    return batch


def prepare_wb_batch_rerun(
    workspace: Path,
    batch_id: str,
    *,
    layout: str | None = None,
    template: WorkflowDefinition | None = None,
    template_out: Path | None = None,
) -> WorkflowBatch:
    items: list[WorkflowBatchItem] = []
    exported: WorkflowDefinition | None = None
    with Workspace.open(workspace) as store:
        previous = execute_batch_store(store, WorkflowBatchStoreCommand("load", batch_id))
        documents = {draft.document_id for draft in store.list_documents()}
        for old in previous.items:
            execution_id = uuid4().hex
            if old.plan is None:
                items.append(
                    WorkflowBatchItem(
                        sample_id=old.sample_id,
                        execution_id=execution_id,
                        plan=None,
                        state="failed",
                        reason=old.reason,
                    )
                )
                continue
            roots = tuple(
                p.asset for node in old.plan.nodes for p in node.inputs if p.asset is not None
            )
            if not roots or any(r != roots[0] or r.description.kind != "raw_image" for r in roots):
                raise ValueError("WB batch rerun requires one unambiguous original per sample")
            definition, plan = bind_wb_workflow_template(
                template if template is not None else execution_plan_definition(old.plan),
                roots[0],
                layout=layout,
            )
            if exported is None:
                exported = definition
            items.append(
                WorkflowBatchItem(
                    sample_id=old.sample_id,
                    execution_id=execution_id,
                    plan=plan,
                    cache_execution_id=old.execution_id if old.execution_id in documents else None,
                )
            )
    batch = WorkflowBatch(batch_id=uuid4().hex, items=tuple(items))
    if template_out is not None:
        if exported is None:
            raise ValueError("No usable frozen graph is available to export")
        with template_out.open("x", encoding="utf-8") as stream:
            stream.write(workflow_definition_json(exported))
    return batch
