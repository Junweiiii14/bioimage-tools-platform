"""Fixed batch commands on the existing workspace-owning storage thread."""

from dataclasses import dataclass
from typing import Literal

from platform_runtime.api import StateConflict, Workspace
from tool_contracts.api import WorkflowBatch, WorkflowBatchControl

from bioimage_app.workflow_storage import WorkflowStoreCommand, execute_workflow_store


@dataclass(frozen=True)
class WorkflowBatchStoreCommand:
    operation: Literal["create", "load", "claim", "checkpoint", "input_failed", "control"]
    document_id: str
    expected_revision: int | None = None
    batch: WorkflowBatch | None = None
    action: Literal["pause", "resume", "cancel", ""] = ""
    command_id: str = ""
    reason: str = ""


def _settle(batch: WorkflowBatch) -> WorkflowBatch:
    if batch.current_index is None:
        state = (
            "cancelled"
            if batch.state == "cancelling" and any(i.state == "cancelled" for i in batch.items)
            else "completed"
            if all(i.state == "succeeded" for i in batch.items)
            else "completed_with_issues"
        )
        return batch.model_copy(update={"state": state})
    if batch.state == "pausing" and not any(i.state == "running" for i in batch.items):
        return batch.model_copy(update={"state": "paused"})
    return batch


def execute_batch_store(store: Workspace, command: WorkflowBatchStoreCommand) -> WorkflowBatch:
    if command.operation == "create":
        batch = command.batch
        if (
            batch is None
            or batch.batch_id != command.document_id
            or command.expected_revision is not None
        ):
            raise ValueError("Create requires one new finite batch")
        if batch.revision or batch.controls or batch.dispatches or batch.state != "running":
            raise ValueError("A new batch cannot carry previous execution state")
        if any(
            i.state not in ("pending", "failed") or i.child_revision is not None
            for i in batch.items
        ):
            raise ValueError("A new batch cannot claim completed children")
        changed = batch
    else:
        draft = store.load_draft(command.document_id)
        batch = WorkflowBatch.model_validate_json(store.read_asset(draft.asset), strict=True)
        if (draft.tool_id, draft.revision, draft.document_id) != (
            "workflow_batch_v1",
            batch.revision,
            batch.batch_id,
        ):
            raise StateConflict("Batch index identity differs from its document")
        if command.operation == "load":
            return batch
        if command.operation == "control":
            previous = next((c for c in batch.controls if c.command_id == command.command_id), None)
            if previous is not None:
                if previous.action != command.action:
                    raise StateConflict("Control identity was already used for another action")
                return batch
        if command.expected_revision != batch.revision:
            raise StateConflict("Batch CAS revision changed")
        if batch.state in ("completed", "completed_with_issues", "cancelled"):
            return batch
        changed = batch
        if command.operation == "control":
            if command.action not in ("pause", "resume", "cancel"):
                raise ValueError("Unknown batch control")
            limit = 128 if command.action == "cancel" else 127
            if len(batch.controls) >= limit:
                raise StateConflict("Batch control budget exhausted")
            control = WorkflowBatchControl(command_id=command.command_id, action=command.action)
            state = {"pause": "pausing", "resume": "running", "cancel": "cancelling"}[
                command.action
            ]
            if batch.state == "cancelling" and command.action != "cancel":
                raise StateConflict("Cancellation cannot be reversed")
            items = batch.items
            if command.action == "cancel":
                items = tuple(
                    item.model_copy(
                        update={"state": "cancelled", "reason": "cancelled_before_dispatch"}
                    )
                    if item.state == "pending"
                    else item
                    for item in items
                )
            changed = _settle(
                batch.model_copy(
                    update={"state": state, "items": items, "controls": (*batch.controls, control)}
                )
            )
        elif command.operation == "claim":
            index = batch.current_index
            if index is None:
                changed = _settle(batch)
            else:
                if batch.state not in ("running", "cancelling") or batch.dispatches >= 256:
                    raise StateConflict("Batch cannot dispatch another child")
                items = list(batch.items)
                items[index] = items[index].model_copy(update={"state": "running"})
                changed = batch.model_copy(
                    update={"items": tuple(items), "dispatches": batch.dispatches + 1}
                )
        elif command.operation in ("checkpoint", "input_failed"):
            index = batch.current_index
            if index is None or batch.items[index].state not in ("running", "paused"):
                raise StateConflict("No claimed child to checkpoint")
            item = batch.items[index]
            exists = any(d.document_id == item.execution_id for d in store.list_documents())
            if not exists:
                if batch.state != "cancelling" and not command.reason:
                    raise StateConflict("Child journal has not been created")
                updated = item.model_copy(
                    update={
                        "state": "cancelled" if batch.state == "cancelling" else "failed",
                        "reason": command.reason[:1024] or "cancelled_before_child_creation",
                    }
                )
            else:
                child = execute_workflow_store(
                    store, WorkflowStoreCommand("load", item.execution_id)
                )
                rejected_input = (
                    command.operation == "input_failed"
                    and bool(command.reason)
                    and child.active_attempt is None
                    and child.state == "running"
                )
                if child.plan != item.plan or (
                    child.state in ("running", "pausing", "cancelling") and not rejected_input
                ):
                    raise StateConflict("Child has no matching settled journal")
                state = (
                    "failed"
                    if rejected_input
                    else (
                        (
                            "issues"
                            if any(r.quality == "issues" for r in child.results)
                            else "succeeded"
                        )
                        if child.state == "succeeded"
                        else (
                            "paused"
                            if child.state == "paused"
                            else "cancelled"
                            if child.state == "cancelled"
                            else "failed"
                        )
                    )
                )
                updated = item.model_copy(
                    update={
                        "state": state,
                        "child_revision": child.revision,
                        "completed_nodes": len(child.results),
                        "reason": (child.reason or command.reason or child.state)[:1024]
                        if state in ("failed", "cancelled")
                        else None,
                    }
                )
            items = list(batch.items)
            items[index] = updated
            changed = _settle(batch.model_copy(update={"items": tuple(items)}))
        changed = changed.model_copy(update={"revision": batch.revision + 1})
    store.save_draft(
        changed.batch_id,
        "workflow_batch_v1",
        changed.revision,
        changed.model_dump_json().encode(),
        expected_previous_revision=command.expected_revision,
    )
    return changed
