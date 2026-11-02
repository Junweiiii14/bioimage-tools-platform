"""Journal component tests with actual Workspace/child-exit facts, not a graph executor."""

import hashlib
import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from platform_runtime.api import (
    ModuleRegistration,
    StateConflict,
    Workspace,
    abandon_workflow_intent,
    associate_workflow_run,
    begin_workflow_attempt,
    compile_workflow,
    control_workflow,
    create_workflow_ledger,
    finish_workflow_attempt,
    load_workflow_ledger,
    next_workflow_node,
    record_workflow_run_started,
    record_workflow_worker_event,
    reuse_workflow_result,
    workflow_ledger_json,
)
from pydantic import ValidationError
from tool_contracts.api import (
    AssetRef,
    BoundAsset,
    ExecutionEvent,
    ExecutionIdentity,
    ExecutionRequest,
    ModulePort,
    ModuleSpec,
    OutputManifest,
    PortTypeBinding,
    ProcessExitReceipt,
    RunRecord,
    RuntimeVersion,
    ScientificAsset,
    ScientificPort,
    ScientificType,
    TableColumn,
    TableMetadata,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowInput,
    WorkflowLedger,
    WorkflowModule,
    WorkflowNode,
    WorkflowOutput,
)


@pytest.fixture
def children() -> Iterator[list[subprocess.Popen[bytes]]]:
    owned: list[subprocess.Popen[bytes]] = []
    try:
        yield owned
    finally:
        for child in owned:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=10)


def fixture(store: Workspace, folder: Path) -> tuple[WorkflowLedger, AssetRef]:
    original = folder / "literal.json"
    original.write_bytes(b'{"value":0.0,"status":"valid"}')
    ref = store.import_asset(original, hashlib.sha256(original.read_bytes()).hexdigest())
    table = TableMetadata(
        row_entity="literal",
        columns=(
            TableColumn(
                name="value", dtype="float64", unit="count", nullable=True, state_column="status"
            ),
            TableColumn(name="status", dtype="string", unit=None, nullable=False),
        ),
    )
    description = ScientificType(kind="typed_table", unit="count", table=table)
    scientific = ScientificAsset(
        payload=ref,
        sample_id="sample",
        description=description,
        producing_method=None,
        parameters_sha256=None,
    )
    module = ModuleSpec(
        module_id="journal_probe",
        module_version="1",
        method_version="literal@1",
        implementation_digest="a" * 64,
        parameters_schema='{"type":"object"}',
        input_ports=(ModulePort(name="source", kind="typed_table"),),
        output_ports=(ModulePort(name="result", kind="typed_table", filename="result.json"),),
    )
    interface = WorkflowModule(
        module=module,
        input_ports=(
            ScientificPort(
                name="source", kind="typed_table", quantitative=True, unit="count", table=table
            ),
        ),
        output_ports=(PortTypeBinding(port="result", description=description),),
    )

    def parameters(raw: str) -> None:
        if json.loads(raw) != {}:
            raise ValueError("Probe parameters must be empty")

    registration = ModuleRegistration(
        interface=interface,
        parameters_schema=module.parameters_schema,
        validate_parameters=parameters,
    )
    definition = WorkflowDefinition(
        workflow_id="journal",
        workflow_version="1",
        revision=0,
        title="Storage component probe",
        sample_id="sample",
        nodes=tuple(
            WorkflowNode(node_id=name, module=module, parameters_json="{}") for name in ("A", "B")
        ),
        inputs=(WorkflowInput(node_id="A", port="source", asset=scientific),),
        edges=(
            WorkflowEdge(
                source_node="A", source_port="result", target_node="B", target_port="source"
            ),
        ),
        outputs=(WorkflowOutput(name="table", node_id="B", port="result"),),
    )
    plan = compile_workflow(
        definition, (registration,), (RuntimeVersion(name="fixture", version="1"),)
    )
    return create_workflow_ledger(plan, uuid4().hex), ref


def request(ledger: WorkflowLedger, source: AssetRef) -> ExecutionRequest:
    node = next_workflow_node(ledger)
    assert node is not None
    bound = ledger.results[-1].outputs[0].asset if ledger.results else source
    return ExecutionRequest(
        request_id=uuid4().hex,
        execution_id=ledger.execution_id,
        node_id=node.node_id,
        attempt_id=uuid4().hex,
        document_id=uuid4().hex,
        revision=ledger.plan.revision,
        module=node.interface.module,
        inputs=(BoundAsset(port="source", kind="typed_table", asset=bound),),
        parameters_json="{}",
        parameters_sha256=hashlib.sha256(b"{}").hexdigest(),
        environment=node.environment,
    )


def identity(run: RunRecord, req: ExecutionRequest) -> ExecutionIdentity:
    return ExecutionIdentity(
        run_id=run.run_id,
        request_id=req.request_id,
        execution_id=req.execution_id,
        node_id=req.node_id,
        attempt_id=req.attempt_id,
        document_id=req.document_id,
        revision=req.revision,
    )


def prepared(
    store: Workspace, ledger: WorkflowLedger, req: ExecutionRequest
) -> tuple[WorkflowLedger, RunRecord]:
    ledger = begin_workflow_attempt(ledger, req)
    store.save_draft(
        req.document_id,
        req.module.module_id,
        req.revision,
        req.model_dump_json().encode(),
        expected_previous_revision=None,
    )
    run = store.prepare_run(req.document_id)
    return associate_workflow_run(ledger, req.attempt_id, run), run


def started(
    store: Workspace,
    ledger: WorkflowLedger,
    req: ExecutionRequest,
    run: RunRecord,
    children: list[subprocess.Popen[bytes]],
    code: int = 0,
) -> tuple[WorkflowLedger, RunRecord, subprocess.Popen[bytes]]:
    # The child waits for authorization. Tests do not pretend this literal fixture is a new worker.
    child = subprocess.Popen(
        [sys.executable, "-I", "-c", f"import sys;sys.stdin.buffer.read(1);sys.exit({code})"],
        stdin=subprocess.PIPE,
    )
    children.append(child)
    ledger = record_workflow_worker_event(
        ledger, req.attempt_id, ExecutionEvent(kind="hello", sequence=0)
    )
    run = store.start_run(run.run_id, child.pid)
    ledger = record_workflow_run_started(ledger, req.attempt_id, run)
    ledger = record_workflow_worker_event(
        ledger,
        req.attempt_id,
        ExecutionEvent(kind="accepted", sequence=1, identity=identity(run, req)),
    )
    return ledger, run, child


def candidate(folder: Path, req: ExecutionRequest, run: RunRecord) -> tuple[OutputManifest, Path]:
    output = folder / (req.attempt_id + ".json")
    output.write_bytes(b'{"value":0.0,"status":"valid"}')
    ref = AssetRef(
        asset_id=uuid4().hex,
        relative_path="result.json",
        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        size_bytes=output.stat().st_size,
    )
    return OutputManifest(
        run_id=run.run_id,
        request=req,
        publication="candidate",
        outputs=(BoundAsset(port="result", kind="typed_table", asset=ref),),
        quality="complete",
        summary_json="{}",
    ), output


def committed(
    store: Workspace,
    manifest: OutputManifest,
    output: Path,
    run: RunRecord,
    child: subprocess.Popen[bytes],
) -> tuple[RunRecord, OutputManifest]:
    child.communicate(b"x", timeout=10)
    assert child.returncode == 0
    ref = store.import_asset(output, hashlib.sha256(output.read_bytes()).hexdigest())
    actual = manifest.model_copy(
        update={
            "publication": "committed",
            "outputs": (BoundAsset(port="result", kind="typed_table", asset=ref),),
        }
    )
    run = store.commit_result(
        run.run_id,
        ProcessExitReceipt(run_id=run.run_id, pid=child.pid, exit_code=0),
        actual.model_dump_json().encode(),
    )
    return run, actual


def test_serial_pause_boundary_and_real_committed_result(
    tmp_path: Path, children: list[subprocess.Popen[bytes]]
) -> None:
    with Workspace.create(tmp_path / "workspace") as store:
        ledger, source = fixture(store, tmp_path)
        req = request(ledger, source)
        ledger, run = prepared(store, ledger, req)
        ledger, run, child = started(store, ledger, req, run, children)
        paused = control_workflow(ledger, "pause", "pause_1")
        assert paused.state == "pausing" and next_workflow_node(paused) is None
        assert control_workflow(paused, "pause", "pause_1") == paused
        manifest, output = candidate(tmp_path, req, run)
        paused = record_workflow_worker_event(
            paused,
            req.attempt_id,
            ExecutionEvent(
                kind="result", sequence=2, identity=identity(run, req), manifest=manifest
            ),
        )
        assert paused.state == "pausing" and not paused.results
        run, actual = committed(store, manifest, output, run, child)
        paused = finish_workflow_attempt(paused, req.attempt_id, run, actual)
        assert paused.state == "paused" and paused.results[0].run.pid == child.pid
        assert paused.events[-1].state == "paused"
        assert next_workflow_node(paused) is None
        ledger = control_workflow(paused, "resume", "resume_1")
        node = next_workflow_node(ledger)
        assert node is not None and node.node_id == "B"
        assert load_workflow_ledger(workflow_ledger_json(ledger)) == ledger
        req = request(ledger, source)
        ledger, run = prepared(store, ledger, req)
        ledger, run, child = started(store, ledger, req, run, children)
        manifest, output = candidate(tmp_path, req, run)
        ledger = record_workflow_worker_event(
            ledger,
            req.attempt_id,
            ExecutionEvent(
                kind="result", sequence=2, identity=identity(run, req), manifest=manifest
            ),
        )
        run, actual = committed(store, manifest, output, run, child)
        complete = finish_workflow_attempt(ledger, req.attempt_id, run, actual)
        assert complete.state == "succeeded" and len(complete.results) == 2
        assert next_workflow_node(complete) is None
        assert control_workflow(complete, "cancel", "already_committed") == complete


def test_candidate_then_nonzero_exit_cannot_be_selected(
    tmp_path: Path, children: list[subprocess.Popen[bytes]]
) -> None:
    with Workspace.create(tmp_path / "workspace") as store:
        ledger, source = fixture(store, tmp_path)
        req = request(ledger, source)
        ledger, run = prepared(store, ledger, req)
        ledger, run, child = started(store, ledger, req, run, children, code=7)
        manifest, _ = candidate(tmp_path, req, run)
        ledger = record_workflow_worker_event(
            ledger,
            req.attempt_id,
            ExecutionEvent(
                kind="result", sequence=2, identity=identity(run, req), manifest=manifest
            ),
        )
        child.communicate(b"x", timeout=10)
        assert child.returncode == 7
        failed = store.finish_failure(
            run.run_id,
            ProcessExitReceipt(run_id=run.run_id, pid=child.pid, exit_code=7),
            reason="real_nonzero_exit",
        )
        ledger = finish_workflow_attempt(ledger, req.attempt_id, failed)
        assert ledger.state == "failed" and not ledger.results
        assert ledger.attempts[0].worker_terminal == "result"
        assert ledger.attempts[0].run is not None and ledger.attempts[0].run.result is None
        restarted = control_workflow(ledger, "resume", "retry")
        fresh = request(restarted, source)
        assert fresh.attempt_id != req.attempt_id and fresh.document_id != req.document_id


def test_commit_before_journal_association_reconciles_idempotently(
    tmp_path: Path, children: list[subprocess.Popen[bytes]]
) -> None:
    workspace = tmp_path / "workspace"
    with Workspace.create(workspace) as store:
        ledger, source = fixture(store, tmp_path)
        req = request(ledger, source)

        def persist(value: WorkflowLedger) -> WorkflowLedger:
            store.save_draft(
                "journal",
                "workflow",
                value.revision,
                workflow_ledger_json(value).encode(),
                expected_previous_revision=value.revision - 1 if value.revision else None,
            )
            return value

        ledger = persist(ledger)
        ledger = persist(begin_workflow_attempt(ledger, req))
        store.save_draft(
            req.document_id,
            req.module.module_id,
            0,
            req.model_dump_json().encode(),
            expected_previous_revision=None,
        )
        run = store.prepare_run(req.document_id)
        ledger = persist(associate_workflow_run(ledger, req.attempt_id, run))
        child = subprocess.Popen(
            [sys.executable, "-I", "-c", "import sys;sys.stdin.buffer.read(1)"],
            stdin=subprocess.PIPE,
        )
        children.append(child)
        ledger = persist(
            record_workflow_worker_event(
                ledger, req.attempt_id, ExecutionEvent(kind="hello", sequence=0)
            )
        )
        run = store.start_run(run.run_id, child.pid)
        ledger = persist(record_workflow_run_started(ledger, req.attempt_id, run))
        ledger = persist(
            record_workflow_worker_event(
                ledger,
                req.attempt_id,
                ExecutionEvent(kind="accepted", sequence=1, identity=identity(run, req)),
            )
        )
        # The last durable journal deliberately lacks the terminal-frame/result association.
        manifest, output = candidate(tmp_path, req, run)
        succeeded, actual = committed(store, manifest, output, run, child)
    with Workspace.open(workspace) as store:
        restored = load_workflow_ledger(
            store.read_asset(store.load_draft("journal").asset).decode()
        )
        observed = store.get_run(succeeded.run_id)
        assert observed == succeeded and observed.result is not None
        actual = OutputManifest.model_validate_json(store.read_asset(observed.result))
        recovered = finish_workflow_attempt(
            restored, req.attempt_id, observed, actual, recovered=True
        )
        assert recovered.results[0].run == observed and recovered.attempts[0].worker_sequence == 1
        assert (
            finish_workflow_attempt(recovered, req.attempt_id, observed, actual, recovered=True)
            == recovered
        )
        assert len(store.list_runs()) == 1  # No fabricated retry/run/PID to repair the journal.
        altered = actual.model_copy(update={"quality": "issues"})
        with pytest.raises(StateConflict, match="committed result asset"):
            finish_workflow_attempt(recovered, req.attempt_id, observed, altered, recovered=True)


def test_cache_references_original_run_without_creating_attempt(
    tmp_path: Path, children: list[subprocess.Popen[bytes]]
) -> None:
    with Workspace.create(tmp_path / "workspace") as store:
        ledger, source = fixture(store, tmp_path)
        req = request(ledger, source)
        ledger, run = prepared(store, ledger, req)
        ledger, run, child = started(store, ledger, req, run, children)
        manifest, output = candidate(tmp_path, req, run)
        ledger = record_workflow_worker_event(
            ledger,
            req.attempt_id,
            ExecutionEvent(
                kind="result", sequence=2, identity=identity(run, req), manifest=manifest
            ),
        )
        run, actual = committed(store, manifest, output, run, child)
        ledger = finish_workflow_attempt(ledger, req.attempt_id, run, actual)
        cached = ledger.results[0]
        another = create_workflow_ledger(ledger.plan, "second_execution")
        selected = reuse_workflow_result(another, cached, run, actual)
        assert not selected.attempts and selected.results[0].run == run
        assert (
            selected.results[0].reused
            and selected.results[0].source_execution_id == req.execution_id
        )
        assert len(store.list_runs()) == 1
        with pytest.raises(StateConflict, match="computation key"):
            reuse_workflow_result(selected, cached, run, actual)
        # A cache candidate with different scientific provenance cannot be admitted
        # solely because its old request binds the same file/parameters/environment.
        changed = cached.model_copy(update={"computation_key": "b" * 64})
        with pytest.raises(StateConflict, match="computation key"):
            reuse_workflow_result(another, changed, run, actual)


def test_worker_duplicate_wrong_identity_and_prepared_success_rejected(tmp_path: Path) -> None:
    with Workspace.create(tmp_path / "workspace") as store:
        ledger, source = fixture(store, tmp_path)
        req = request(ledger, source)
        ledger, run = prepared(store, ledger, req)
        with pytest.raises(StateConflict, match="terminal storage fact"):
            finish_workflow_attempt(ledger, req.attempt_id, run)
        accepted = ExecutionEvent(kind="accepted", sequence=1, identity=identity(run, req))
        with pytest.raises(StateConflict, match="sequence"):
            record_workflow_worker_event(ledger, req.attempt_id, accepted)
        ledger = record_workflow_worker_event(
            ledger, req.attempt_id, ExecutionEvent(kind="hello", sequence=0)
        )
        with pytest.raises(StateConflict, match="sequence"):
            record_workflow_worker_event(
                ledger, req.attempt_id, ExecutionEvent(kind="hello", sequence=0)
            )
        wrong = accepted.model_copy(
            update={"identity": identity(run, req).model_copy(update={"revision": 99})}
        )
        with pytest.raises(StateConflict, match="another run"):
            record_workflow_worker_event(ledger, req.attempt_id, wrong)


def test_cancel_before_process_start_and_abandoned_intent_are_not_fake_runs(tmp_path: Path) -> None:
    with Workspace.create(tmp_path / "workspace") as store:
        ledger, source = fixture(store, tmp_path)
        req = request(ledger, source)
        pending = begin_workflow_attempt(ledger, req)
        pending = control_workflow(pending, "cancel", "cancel_intent")
        abandoned = abandon_workflow_intent(pending, req.attempt_id, "cancelled_before_prepare")
        assert abandoned.state == "cancelled" and abandoned.attempts[0].run is None
        assert not store.list_runs()
        prepared_ledger, run = prepared(store, ledger, req)
        cancelling = control_workflow(prepared_ledger, "cancel", "cancel_before_start")
        store.request_cancel(run.run_id)
        final = store.finish_cancelled(
            run.run_id, ProcessExitReceipt(run_id=run.run_id, pid=0, exit_code=None)
        )
        cancelled = finish_workflow_attempt(cancelling, req.attempt_id, final)
        assert cancelled.state == "cancelled"
        assert cancelled.attempts[0].run is not None and cancelled.attempts[0].run.pid is None


def test_control_idempotency_and_finite_budget(tmp_path: Path) -> None:
    with Workspace.create(tmp_path / "workspace") as store:
        ledger, source = fixture(store, tmp_path)
        for index in range(126):
            ledger = control_workflow(
                ledger, "pause" if index % 2 == 0 else "resume", f"command_{index}"
            )
        assert ledger.control_count == 126 and ledger.state == "running"
        assert control_workflow(ledger, "pause", "command_0") == ledger
        with pytest.raises(StateConflict, match="different control"):
            control_workflow(ledger, "cancel", "command_0")
        req = request(ledger, source)
        ledger = begin_workflow_attempt(ledger, req)
        ledger = control_workflow(ledger, "pause", "last_pause")
        with pytest.raises(StateConflict, match="control budget"):
            control_workflow(ledger, "pause", "overflow")
        ledger = control_workflow(ledger, "cancel", "reserved_cancel")
        assert ledger.control_count == 128 and ledger.state == "cancelling"
        terminal = abandon_workflow_intent(ledger, req.attempt_id, "cancelled_before_prepare")
        assert terminal.state == "cancelled"


def test_saved_journal_rejects_schema_boolean_duplicates_and_tampered_sequence(
    tmp_path: Path,
) -> None:
    with Workspace.create(tmp_path / "workspace") as store:
        ledger, _ = fixture(store, tmp_path)
        for update in ({"revision": True}, {"schema_version": 2}, {"revision": 3}):
            with pytest.raises(ValidationError):
                WorkflowLedger.model_validate({**ledger.model_dump(mode="python"), **update})
        with pytest.raises(ValueError, match="Duplicate"):
            load_workflow_ledger('{"schema_version":1,"schema_version":2}')
        with pytest.raises(ValueError, match="Nonfinite"):
            load_workflow_ledger('{"x":NaN}')
