# P009 independent review — Request changes

Base: 275560475d39426434416c74feeb0c2f259d1402
Head: 26f4470bc62b4cf20b7727704739cd223835c7e6
Reviewer: /root/p002_independent_review (non-author)
Repository: C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0
Environment: Windows 11 / Python 3.12.14; targeted tests QT_QPA_PLATFORM=offscreen,
QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu; TEMP/TMP=.local/p002-process-temp.

## P1: selected journal outputs are not bound to the actual committed manifest

Location: apps/desktop/src/bioimage_app/workflow_authoring_store.py:333-335.
The display/open boundary checks the actual RunRecord and verifies output asset
bytes, but trusts WorkflowNodeResult.outputs without comparing it to that run's
OutputManifest. A valid selected asset is not proof that this run committed it.

Confirmed using a NEW independent copy of the CLOSED historical failed-measurement
workspace, not the current formal directory or any historical original:
.local/p009-independent-26f-selection

The original successful run, original manifest and original output bytes remained
unchanged. A separate CSV (value9999) was imported through Workspace.import_asset.
A new child-journal draft was saved through Workspace.save_draft with matching new
revision/event sequence, changing only the publisher's selected measurements
binding to that unrelated asset. The journal remains strictly model-valid; the
stored RunRecord still equals the original selected run. execute_authoring_store
results returned9999 and open returned that imported CSV path. That asset is absent
from the actual committed OutputManifest. Original committed value was4000.
Run b35cba2a1e39487dba6663a232f93db8; substituted asset8aa5c3d42f54425fbdb336519abbf961.
The inline Python counterexample exited0, confirming fail-open at both entry points.

Minimal correction: validate the selected run/output/quality and source execution,
node and attempt against the actual committed manifest before projecting/opening.
The existing pure reuse_workflow_result contract already makes these comparisons
(platform_runtime/workflow_execution.py:422-428), and _admit_result binds manifest
and request hashes/run identity. A shared small read/selection admission function
for these two real consumers is appropriate; no new framework is needed. Reused
results must retain source_* origin: do not require manifest.request.node_id or
execution_id to equal the current reused node/execution.

Replay on the persisted counterexample: open its Workspace; find the authoring
project document and completed WorkflowBatch; call execute_authoring_store with
AuthoringCommand(operation='results', document_id=editor, batch_id=batch.batch_id).
Current candidate returns the unrelated9999 CSV. The corrected entry should reject
with a storage/provenance conflict before publishing outputs or opening a path.

## Explicitly withdrawn static hypothesis

Simply corrupting run.result is ALREADY rejected: Workspace.get_run internally
verifies the result asset (workspace.py:501). Probe copy
.local/p009-independent-26f-manifest exited1 with IntegrityError. This was a rejected
hypothesis, not another product finding. It must not be conflated with the valid
but incorrectly selected-output counterexample above.

## Actual independent checks

- uv run --locked --no-sync python -m pytest tests/test_workflow_authoring_store.py
  tests/test_workflow_authoring_session.py tests/test_workflow_authoring_bridge.py
  -q --basetemp=.local/p009-independent-26f-targeted
  exit0: 10 passed in34.06s. Frozen HEAD remained26f; no tracked dirty files.
- git diff --check <base> <head>: exit0.
- Actual Workspace selected-output negative probe: exit0, fail-open confirmed.
- Native results statistics check: exit0 after correcting the review script's own
  initial p50 assumption (the initial probe exit1 incorrectly expected a lower
  order statistic; the tool correctly uses statistics.median). Independently
  recomputed all12 UI feedback/settled groups and4 control distributions; counts,
  raw order, median, nearest-rank p95/max all match. Each has5warmup+30formal.
- All35 controls have real PID/run identity; resume uses a different real run;
  every terminal is cancelled/closed and editor_store_retained is true.

## Formal measurement boundaries

Read-only source .local/p009-perf-frozen-26f4470/results.json binds this exact HEAD.
Normal node p95 forest74.8, ember94.4, iris136.8, neutral148.9ms; upper64 node
p95 82.5-99.6ms. Preview feedback p95 331.6-345.1ms. Preserve ordinary100ms
reference overruns. Pause ack44.95ms and cancel ack35.86ms are separate from
pause boundary1665.82ms and cancel-to-batch-closed429.68ms. Settled endpoints are
separate. No physical display latency, science, target fleet, whole-process-tree
memory or user acceptance is proved. Memory remains per-process snapshots/high
watermarks, not aggregate worker-tree peak; no inferred root cause.

## Remaining scope

Read static task/contracts, models/store/session/bridge, JS graph/forms/receipt
handling, window shutdown, external-storage batch path, shared template loader,
installed-wheel changes and measurement tooling. No removed old wheel assertions
or changed WB formula/default/schema/lock was identified. Default CLI still owns
its storage; editor batch uses its external owner. Pending freeze cancellation and
close were covered by the targeted tests. No full suite or repeated wheels run by
this reviewer. No second visual loop performed. Earlier visual scoped ship remains
narrow. B012 untracked planning files untouched. Only this .local report and new
owned probe copies were written. Product acceptance is withheld until P1 corrected
and relevant negative/cached-origin cases verified on a new exact candidate.
