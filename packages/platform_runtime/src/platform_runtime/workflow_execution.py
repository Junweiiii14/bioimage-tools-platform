"""Pure journal transitions. The host must persist a transition before acting on it.

RunRecord/manifest arguments must come from the owned storage service and file admission;
these functions neither observe a process nor certify bytes by constructing a model.
"""

import hashlib
import json
from typing import cast

from tool_contracts.api import (
    ExecutionEvent,
    ExecutionIdentity,
    ExecutionPlan,
    ExecutionRequest,
    OutputManifest,
    PlannedNode,
    RunRecord,
    WorkflowAttempt,
    WorkflowJournalEvent,
    WorkflowLedger,
    WorkflowNodeResult,
    canonical_module_json,
)

from platform_runtime.workspace import StateConflict


def _valid(ledger: WorkflowLedger) -> WorkflowLedger:
    return WorkflowLedger.model_validate(ledger.model_dump(mode="python"))


def workflow_ledger_json(ledger: WorkflowLedger) -> str:
    valid = _valid(ledger)
    # The journal has its own v1 document budget. Do not raise the old module/frame limit.
    encoded = json.dumps(
        valid.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if len(encoded.encode("utf-8")) > 16 * 1024 * 1024:
        raise ValueError("Workflow journal exceeds the 16MiB storage document budget")
    return encoded


def load_workflow_ledger(raw: str) -> WorkflowLedger:
    if len(raw.encode("utf-8")) > 16 * 1024 * 1024:
        raise ValueError("Workflow journal exceeds the 16MiB storage document budget")

    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate journal JSON key")
            result[key] = value
        return result

    def nonfinite(_value: str) -> object:
        raise ValueError("Nonfinite journal JSON")

    try:
        data: object = json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
        pending = [(data, 0)]
        while pending:
            item, depth = pending.pop()
            if depth > 32:
                raise ValueError("Workflow journal nesting exceeds 32 levels")
            if isinstance(item, dict):
                pending.extend(
                    (value, depth + 1) for value in cast(dict[str, object], item).values()
                )
            elif isinstance(item, list):
                pending.extend((value, depth + 1) for value in cast(list[object], item))
        # JSON-mode is needed for the explicitly frozen tuple fields, not coercive Python input.
        clean = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        return WorkflowLedger.model_validate_json(clean, strict=True)
    except RecursionError as error:
        raise ValueError("Workflow journal nesting exceeds parser capacity") from error


def _advance(
    ledger: WorkflowLedger, event: WorkflowJournalEvent, **changes: object
) -> WorkflowLedger:
    if event.sequence != len(ledger.events) + 1:
        raise StateConflict("Host event sequence changed")
    event = event.model_copy(update={"state": changes.get("state", ledger.state)})
    changed = ledger.model_copy(
        update={**changes, "revision": ledger.revision + 1, "events": (*ledger.events, event)}
    )
    result = _valid(changed)
    workflow_ledger_json(result)
    return result


def _event(ledger: WorkflowLedger, kind: str, **fields: object) -> WorkflowJournalEvent:
    return WorkflowJournalEvent.model_validate(
        {"sequence": len(ledger.events) + 1, "kind": kind, "state": ledger.state, **fields}
    )


def _reserve(ledger: WorkflowLedger) -> None:
    if len(ledger.events) >= 4080:
        raise StateConflict("Journal capacity reserved for the active attempt and terminal state")


def create_workflow_ledger(plan: ExecutionPlan, execution_id: str) -> WorkflowLedger:
    plan = ExecutionPlan.model_validate(plan.model_dump(mode="python"))
    canonical_module_json(plan.model_dump_json())
    ledger = WorkflowLedger(
        execution_id=execution_id,
        plan=plan,
        revision=0,
        state="running",
        events=(WorkflowJournalEvent(sequence=1, kind="created", state="running"),),
    )
    workflow_ledger_json(ledger)
    return ledger


def next_workflow_node(ledger: WorkflowLedger) -> PlannedNode | None:
    ledger = _valid(ledger)
    if ledger.state != "running" or ledger.active_attempt is not None:
        return None
    return ledger.plan.nodes[len(ledger.results)]


def _inputs(ledger: WorkflowLedger, node: PlannedNode) -> dict[str, object]:
    selected = {item.node_id: item for item in ledger.results}
    result: dict[str, object] = {}
    for item in node.inputs:
        if item.asset is not None:
            result[item.port] = item.asset.payload
        else:
            upstream = selected.get(item.source_node or "")
            if upstream is None or upstream.computation_key != item.source_key:
                raise StateConflict("Upstream node has no matching committed result")
            output = next(
                (value for value in upstream.outputs if value.port == item.source_port), None
            )
            if output is None:
                raise StateConflict("Upstream committed output port is missing")
            result[item.port] = output.asset
    return result


def _request_matches(ledger: WorkflowLedger, node: PlannedNode, request: ExecutionRequest) -> None:
    if (request.module, request.parameters_json, request.environment) != (
        node.interface.module,
        node.parameters_json,
        node.environment,
    ):
        raise StateConflict("Request changed the frozen module/parameters/environment")
    if {item.port: item.asset for item in request.inputs} != _inputs(ledger, node):
        raise StateConflict("Request changed the resolved immutable input references")


def begin_workflow_attempt(ledger: WorkflowLedger, request: ExecutionRequest) -> WorkflowLedger:
    ledger = _valid(ledger)
    request = ExecutionRequest.model_validate(request.model_dump(mode="python"))
    node = next_workflow_node(ledger)
    if node is None:
        raise StateConflict("Workflow cannot dispatch another node")
    _reserve(ledger)
    if len(ledger.attempts) >= 256:
        raise StateConflict("Workflow attempt budget exhausted")
    if (request.execution_id, request.node_id, request.revision) != (
        ledger.execution_id,
        node.node_id,
        ledger.plan.revision,
    ):
        raise StateConflict("Request does not belong to this frozen workflow generation")
    _request_matches(ledger, node, request)
    attempt = WorkflowAttempt(
        node_id=node.node_id,
        attempt_id=request.attempt_id,
        request_id=request.request_id,
        document_id=request.document_id,
        revision=request.revision,
        computation_key=node.computation_key,
        request_sha256=hashlib.sha256(request.model_dump_json().encode()).hexdigest(),
    )
    return _advance(
        ledger,
        _event(ledger, "intent", node_id=node.node_id, attempt_id=attempt.attempt_id),
        attempts=(*ledger.attempts, attempt),
    )


def _active(ledger: WorkflowLedger, attempt_id: str) -> WorkflowAttempt:
    attempt = ledger.active_attempt
    if attempt is None or attempt.attempt_id != attempt_id:
        raise StateConflict("Attempt is stale or no longer active")
    return attempt


def _replace(ledger: WorkflowLedger, attempt: WorkflowAttempt) -> tuple[WorkflowAttempt, ...]:
    return tuple(
        attempt if item.attempt_id == attempt.attempt_id else item for item in ledger.attempts
    )


def _run_matches(attempt: WorkflowAttempt, run: RunRecord) -> None:
    if (
        (run.document_id, run.revision, run.request.sha256)
        != (attempt.document_id, attempt.revision, attempt.request_sha256)
        or attempt.run is not None
        and attempt.run.run_id != run.run_id
    ):
        raise StateConflict("Storage run differs from the durable attempt intent")


def associate_workflow_run(
    ledger: WorkflowLedger, attempt_id: str, run: RunRecord
) -> WorkflowLedger:
    ledger = _valid(ledger)
    run = RunRecord.model_validate(run.model_dump(mode="python"))
    attempt = _active(ledger, attempt_id)
    _run_matches(attempt, run)
    if attempt.run is not None or run.state != "prepared":
        raise StateConflict("Only a newly prepared real storage run can be associated")
    return _advance(
        ledger,
        _event(
            ledger, "prepared", node_id=attempt.node_id, attempt_id=attempt_id, run_id=run.run_id
        ),
        attempts=_replace(ledger, attempt.model_copy(update={"run": run})),
    )


def record_workflow_run_started(
    ledger: WorkflowLedger, attempt_id: str, run: RunRecord
) -> WorkflowLedger:
    ledger = _valid(ledger)
    run = RunRecord.model_validate(run.model_dump(mode="python"))
    attempt = _active(ledger, attempt_id)
    _run_matches(attempt, run)
    if attempt.run is None or attempt.run.state != "prepared" or run.state != "running":
        raise StateConflict("Start needs the persisted PID transition of the associated run")
    return _advance(
        ledger,
        _event(
            ledger, "started", node_id=attempt.node_id, attempt_id=attempt_id, run_id=run.run_id
        ),
        attempts=_replace(ledger, attempt.model_copy(update={"run": run})),
    )


def record_workflow_worker_event(
    ledger: WorkflowLedger, attempt_id: str, event: ExecutionEvent
) -> WorkflowLedger:
    ledger = _valid(ledger)
    event = ExecutionEvent.model_validate(event.model_dump(mode="python"))
    attempt = _active(ledger, attempt_id)
    if attempt.run is None or event.sequence != attempt.worker_sequence + 1:
        raise StateConflict("Worker sequence is duplicate, late or has no associated run")
    expected = ExecutionIdentity(
        run_id=attempt.run.run_id,
        request_id=attempt.request_id,
        execution_id=ledger.execution_id,
        node_id=attempt.node_id,
        attempt_id=attempt.attempt_id,
        document_id=attempt.document_id,
        revision=attempt.revision,
    )
    if event.kind != "hello" and event.identity != expected:
        raise StateConflict("Worker event belongs to another run/node/attempt/generation")
    if event.sequence > 0 and attempt.run.state not in ("running", "cancelling", "committing"):
        raise StateConflict("Worker request was not authorized after PID persistence")
    if (
        event.manifest is not None
        and hashlib.sha256(event.manifest.request.model_dump_json().encode()).hexdigest()
        != attempt.request_sha256
    ):
        raise StateConflict("Worker result changed the frozen request")
    kind = (
        "worker_hello"
        if event.kind == "hello"
        else ("worker_accepted" if event.kind == "accepted" else "worker_terminal")
    )
    changed = attempt.model_copy(
        update={
            "worker_sequence": event.sequence,
            "worker_terminal": event.kind if event.sequence == 2 else None,
        }
    )
    return _advance(
        ledger,
        _event(
            ledger, kind, node_id=attempt.node_id, attempt_id=attempt_id, run_id=attempt.run.run_id
        ),
        attempts=_replace(ledger, changed),
    )


def _admit_result(
    ledger: WorkflowLedger, node: PlannedNode, run: RunRecord, manifest: OutputManifest
) -> None:
    if (
        run.state != "succeeded"
        or manifest.publication != "committed"
        or manifest.run_id != run.run_id
    ):
        raise StateConflict("Only a committed successful storage result can be selected")
    request = manifest.request
    if (
        run.result is None
        or run.result.sha256 != hashlib.sha256(manifest.model_dump_json().encode()).hexdigest()
    ):
        raise StateConflict("Selected manifest differs from the committed result asset")
    if (run.document_id, run.revision, run.tool_id, run.request.sha256) != (
        request.document_id,
        request.revision,
        request.module.module_id,
        hashlib.sha256(request.model_dump_json().encode()).hexdigest(),
    ):
        raise StateConflict("Committed result request differs from its real storage run")
    _request_matches(ledger, node, request)


def finish_workflow_attempt(
    ledger: WorkflowLedger,
    attempt_id: str,
    run: RunRecord,
    manifest: OutputManifest | None = None,
    *,
    recovered: bool = False,
) -> WorkflowLedger:
    ledger = _valid(ledger)
    run = RunRecord.model_validate(run.model_dump(mode="python"))
    prior = next((item for item in ledger.attempts if item.attempt_id == attempt_id), None)
    if prior is not None and not prior.active and prior.run == run:
        if run.state == "succeeded":
            selected = next(
                (item for item in ledger.results if item.node_id == prior.node_id), None
            )
            if selected is None or selected.run != run or manifest is None:
                raise StateConflict("Duplicate completion has no matching committed selection")
            manifest = OutputManifest.model_validate(manifest.model_dump(mode="python"))
            node = next(item for item in ledger.plan.nodes if item.node_id == prior.node_id)
            _admit_result(ledger, node, run, manifest)
        elif manifest is not None:
            raise StateConflict("Failed/cancelled runs do not select a result manifest")
        return ledger
    attempt = _active(ledger, attempt_id)
    _run_matches(attempt, run)
    if run.state not in ("succeeded", "failed", "interrupted", "cancelled"):
        raise StateConflict("A candidate/active process is not a terminal storage fact")
    if not recovered and attempt.run is None:
        raise StateConflict("Unassociated terminal runs require explicit recovery reconciliation")
    changed = attempt.model_copy(update={"run": run})
    fields: dict[str, object] = {"attempts": _replace(ledger, changed)}
    if run.state == "succeeded":
        if manifest is None or not recovered and attempt.worker_terminal != "result":
            raise StateConflict(
                "Success needs the worker result and committed manifest, not only a PID"
            )
        manifest = OutputManifest.model_validate(manifest.model_dump(mode="python"))
        node = ledger.plan.nodes[len(ledger.results)]
        _admit_result(ledger, node, run, manifest)
        if (
            manifest.request.execution_id,
            manifest.request.node_id,
            manifest.request.attempt_id,
            manifest.request.request_id,
        ) != (ledger.execution_id, attempt.node_id, attempt_id, attempt.request_id):
            raise StateConflict("Completion belongs to another workflow attempt")
        result = WorkflowNodeResult(
            node_id=node.node_id,
            computation_key=node.computation_key,
            run=run,
            outputs=manifest.outputs,
            quality=manifest.quality,
            source_execution_id=ledger.execution_id,
            source_node_id=node.node_id,
            source_attempt_id=attempt_id,
            reused=False,
        )
        results = (*ledger.results, result)
        state = (
            "succeeded"
            if len(results) == len(ledger.plan.nodes)
            else (
                "paused"
                if ledger.state == "pausing"
                else "cancelled"
                if ledger.state == "cancelling"
                else "running"
            )
        )
        fields.update(results=results, state=state, reason=None)
        kind = "recovered" if recovered else "committed"
    else:
        if manifest is not None:
            raise StateConflict("Failed/cancelled runs do not select a result manifest")
        fields.update(state=run.state, reason=(run.reason or "Node process " + run.state)[:1024])
        kind = run.state
    return _advance(
        ledger,
        _event(ledger, kind, node_id=attempt.node_id, attempt_id=attempt_id, run_id=run.run_id),
        **fields,
    )


def reuse_workflow_result(
    ledger: WorkflowLedger, source: WorkflowNodeResult, run: RunRecord, manifest: OutputManifest
) -> WorkflowLedger:
    """Caller loads source from a persisted ledger and checks bytes/current admission."""
    ledger = _valid(ledger)
    source = WorkflowNodeResult.model_validate(source.model_dump(mode="python"))
    run = RunRecord.model_validate(run.model_dump(mode="python"))
    manifest = OutputManifest.model_validate(manifest.model_dump(mode="python"))
    node = next_workflow_node(ledger)
    if node is None:
        raise StateConflict("Workflow cannot reuse a result at this boundary")
    _reserve(ledger)
    if source.computation_key != node.computation_key:
        raise StateConflict("Cached scientific computation key differs from the frozen node")
    if (source.run, source.outputs, source.quality) != (run, manifest.outputs, manifest.quality):
        raise StateConflict("Cached selection differs from its real committed result")
    if (source.source_execution_id, source.source_node_id, source.source_attempt_id) != (
        manifest.request.execution_id,
        manifest.request.node_id,
        manifest.request.attempt_id,
    ):
        raise StateConflict("Cached selection changed the original execution identity")
    _admit_result(ledger, node, run, manifest)
    request = manifest.request
    result = WorkflowNodeResult(
        node_id=node.node_id,
        computation_key=node.computation_key,
        run=run,
        outputs=manifest.outputs,
        quality=manifest.quality,
        source_execution_id=request.execution_id,
        source_node_id=request.node_id,
        source_attempt_id=request.attempt_id,
        reused=True,
    )
    results = (*ledger.results, result)
    return _advance(
        ledger,
        _event(ledger, "reused", node_id=node.node_id, run_id=run.run_id),
        results=results,
        state="succeeded" if len(results) == len(ledger.plan.nodes) else "running",
    )


def control_workflow(ledger: WorkflowLedger, action: str, command_id: str) -> WorkflowLedger:
    ledger = _valid(ledger)
    kind = {"pause": "pausing", "resume": "resumed", "cancel": "cancelling"}.get(action)
    if kind is None:
        raise ValueError("Unknown workflow control")
    prior = next((event for event in ledger.events if event.command_id == command_id), None)
    if prior is not None:
        if prior.message != action:
            raise StateConflict("Idempotency key was already used by a different control")
        return ledger
    if ledger.state == "succeeded":
        return ledger
    _reserve(ledger)
    if ledger.control_count >= 128 or action != "cancel" and ledger.control_count >= 127:
        raise StateConflict("Workflow control budget exhausted; final slot is reserved for cancel")
    active = ledger.active_attempt is not None
    if action == "pause" and ledger.state in ("running", "pausing", "paused"):
        state = "pausing" if active else "paused"
    elif action == "cancel" and ledger.state in ("running", "pausing", "paused", "cancelling"):
        state = "cancelling" if active else "cancelled"
    elif action == "resume" and ledger.state in ("paused", "failed", "interrupted") and not active:
        state = "running"
    else:
        raise StateConflict("Workflow control is not valid at this execution boundary")
    return _advance(
        ledger,
        _event(ledger, kind, command_id=command_id, message=action),
        state=state,
        reason=None,
        control_count=ledger.control_count + 1,
    )


def abandon_workflow_intent(ledger: WorkflowLedger, attempt_id: str, reason: str) -> WorkflowLedger:
    ledger = _valid(ledger)
    attempt = _active(ledger, attempt_id)
    if attempt.run is not None or not reason:
        raise StateConflict("Only an intent with no created run may be abandoned")
    changed = attempt.model_copy(update={"abandoned_reason": reason})
    return _advance(
        ledger,
        _event(
            ledger,
            "abandoned",
            node_id=attempt.node_id,
            attempt_id=attempt_id,
            message=reason[:256],
        ),
        attempts=_replace(ledger, changed),
        state="cancelled" if ledger.state == "cancelling" else "failed",
        reason=reason[:1024],
    )
