"""Fixed workflow journal operations, executed only by the owned storage thread."""

import hashlib
from dataclasses import dataclass
from typing import Literal

from platform_runtime.api import (
    StateConflict,
    Workspace,
    abandon_workflow_intent,
    associate_workflow_run,
    begin_workflow_attempt,
    control_workflow,
    create_workflow_ledger,
    finish_workflow_attempt,
    load_workflow_ledger,
    record_workflow_run_started,
    record_workflow_worker_event,
    reuse_workflow_result,
    workflow_ledger_json,
)
from tool_contracts.api import (
    ExecutionEvent,
    ExecutionPlan,
    ExecutionRequest,
    OutputManifest,
    RunRecord,
    WorkflowLedger,
)


@dataclass(frozen=True)
class WorkflowStoreCommand:
    operation: Literal[
        "create",
        "load",
        "begin",
        "prepare",
        "started",
        "worker",
        "finish",
        "recover",
        "reuse",
        "control",
        "abandon",
    ]
    document_id: str
    expected_revision: int | None = None
    plan: ExecutionPlan | None = None
    request: ExecutionRequest | None = None
    event: ExecutionEvent | None = None
    action: str = ""
    command_id: str = ""
    reason: str = ""
    source_document_id: str = ""
    source_node_id: str = ""


def _load(store: Workspace, document_id: str) -> WorkflowLedger:
    draft = store.load_draft(document_id)
    if draft.tool_id != "workflow_journal_v1":
        raise StateConflict("Document is not a workflow journal")
    ledger = load_workflow_ledger(store.read_asset(draft.asset).decode("utf-8"))
    if (ledger.execution_id, ledger.revision) != (document_id, draft.revision):
        raise StateConflict("Journal identity/revision differs from its storage document")
    return ledger


def _manifest(store: Workspace, run: RunRecord) -> OutputManifest | None:
    # This is file admission, not proof that the current installed environment matches.
    # The session must verify its trusted registration/environment before dispatch/reuse.
    if run.state != "succeeded":
        return None
    if run.result is None:
        raise StateConflict("Successful run has no committed manifest")
    manifest = OutputManifest.model_validate_json(store.read_asset(run.result))
    if store.read_asset(run.request) != manifest.request.model_dump_json().encode():
        raise StateConflict("Stored request differs from committed manifest")
    for bound in (*manifest.request.inputs, *manifest.outputs):
        store.asset_path(bound.asset)
    return manifest


def _attempt_run(store: Workspace, ledger: WorkflowLedger) -> RunRecord | None:
    attempt = ledger.active_attempt
    if attempt is None:
        raise StateConflict("No active workflow attempt")
    if attempt.run is not None:
        return store.get_run(attempt.run.run_id)
    found = tuple(
        run
        for run in store.list_runs(attempt.document_id)
        if run.revision == attempt.revision and run.request.sha256 == attempt.request_sha256
    )
    if len(found) > 1:
        raise StateConflict("Attempt has ambiguous physical runs")
    return found[0] if found else None


def execute_workflow_store(store: Workspace, command: WorkflowStoreCommand) -> WorkflowLedger:
    """No caller RunRecord, manifest, arbitrary callback or module can become a storage fact."""
    if type(command) is not WorkflowStoreCommand:
        raise TypeError("Expected an immutable workflow storage command")
    if command.operation == "create":
        if command.plan is None or command.expected_revision is not None:
            raise ValueError("Create requires a frozen plan and no previous revision")
        changed = create_workflow_ledger(command.plan, command.document_id)
    else:
        ledger = _load(store, command.document_id)
        if command.operation == "load":
            return ledger
        if command.operation == "recover" and ledger.active_attempt is None:
            return ledger
        if command.operation == "control" and any(
            event.command_id == command.command_id for event in ledger.events
        ):
            # A lost reply may be retried with the original (now stale) CAS version.
            return control_workflow(ledger, command.action, command.command_id)
        if (
            type(command.expected_revision) is not int
            or command.expected_revision != ledger.revision
        ):
            raise StateConflict("Workflow journal CAS revision changed")
        active = ledger.active_attempt
        if command.operation == "control":
            changed = control_workflow(ledger, command.action, command.command_id)
        elif command.operation == "begin":
            if command.request is None or command.request.document_id == command.document_id:
                raise ValueError("Begin requires an independent node request document")
            changed = begin_workflow_attempt(ledger, command.request)
        elif command.operation == "reuse":
            previous = _load(store, command.source_document_id)
            selected = next(
                (item for item in previous.results if item.node_id == command.source_node_id), None
            )
            if selected is None:
                raise StateConflict("Source journal has no committed node result")
            run = store.get_run(selected.run.run_id)
            manifest = _manifest(store, run)
            if manifest is None:
                raise StateConflict("Cached run is no longer a committed result")
            changed = reuse_workflow_result(ledger, selected, run, manifest)
        elif active is None:
            raise StateConflict("Operation requires an active workflow attempt")
        elif command.operation == "prepare":
            req = command.request
            if (
                req is None
                or hashlib.sha256(req.model_dump_json().encode()).hexdigest()
                != active.request_sha256
            ):
                raise StateConflict("Prepare request differs from persisted dispatch intent")
            run = _attempt_run(store, ledger)
            if run is None:
                existing = next(
                    (
                        item
                        for item in store.list_documents()
                        if item.document_id == req.document_id
                    ),
                    None,
                )
                if existing is None:
                    store.save_draft(
                        req.document_id,
                        req.module.module_id,
                        req.revision,
                        req.model_dump_json().encode(),
                        expected_previous_revision=None,
                    )
                elif (existing.tool_id, existing.revision, store.read_asset(existing.asset)) != (
                    req.module.module_id,
                    req.revision,
                    req.model_dump_json().encode(),
                ):
                    raise StateConflict("Attempt document is already occupied")
                if store.list_runs(req.document_id):
                    raise StateConflict("Attempt document has a different physical run")
                run = store.prepare_run(req.document_id, req.revision)
            changed = associate_workflow_run(ledger, active.attempt_id, run)
        elif command.operation == "worker":
            if command.event is None:
                raise ValueError("Worker operation requires a decoded protocol event")
            changed = record_workflow_worker_event(ledger, active.attempt_id, command.event)
        elif command.operation == "abandon":
            if _attempt_run(store, ledger) is not None:
                raise StateConflict("Cannot abandon an intent with a physical run")
            changed = abandon_workflow_intent(ledger, active.attempt_id, command.reason)
        else:
            run = _attempt_run(store, ledger)
            if run is None and command.operation == "recover":
                changed = abandon_workflow_intent(
                    ledger, active.attempt_id, "interrupted_before_prepare"
                )
            elif run is None:
                raise StateConflict("Attempt has no physical run")
            elif command.operation == "started":
                changed = record_workflow_run_started(ledger, active.attempt_id, run)
            elif command.operation in ("finish", "recover"):
                changed = finish_workflow_attempt(
                    ledger,
                    active.attempt_id,
                    run,
                    _manifest(store, run),
                    recovered=command.operation == "recover",
                )
            else:
                raise ValueError("Unknown workflow storage operation")
        if changed == ledger:
            return ledger
    store.save_draft(
        command.document_id,
        "workflow_journal_v1",
        changed.revision,
        workflow_ledger_json(changed).encode(),
        expected_previous_revision=command.expected_revision,
    )
    return changed
