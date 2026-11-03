# P009 independent review — Accepted engineering candidate

Base: 275560475d39426434416c74feeb0c2f259d1402
Head: 64c02d94b0da1596ee9cb372d60e44b24cf23b33
Prior rejected candidate: 26f4470bc62b4cf20b7727704739cd223835c7e6
Reviewer: /root/p002_independent_review (non-author)
Repository: C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0

Conclusion: Accepted for the complete P009 engineering candidate in this exact
range. The confirmed P1 is fixed; no further blocking code finding was identified.
This does not declare all performance budgets met, M2/science/user/target-machine
acceptance complete, or required CI/wheels passed for a later source.

## P1 resolution and independent evidence

The previous display/open path trusted child journal output selection after checking
only actual RunRecord and asset bytes. A valid unrelated9999 CSV could be displayed
and opened as an original4000 run output. Initial Request changes and the persisted
counterexample are retained in .local/p009-review-26f4470.md and
.local/p009-independent-26f-selection. No old evidence was overwritten.

64c now reads the actual run.result manifest and calls the same public pure
validate_workflow_result_selection used by cache reuse. It checks computation key,
actual run, complete output bindings/quality, original source execution/node/attempt,
committed manifest and request hashes, and frozen module/parameters/resolved inputs.
The platform has no WB/Qt/I/O dependency added. App imports the public API.
Reused selections retain the original source identity, not the current execution
or node label. This is shared existing admission logic for two real consumers,
not an extra framework or repeated parsing of frozen models.

Independent replay on the ORIGINAL persisted counterexample (no draft/asset/run
changed by replay): execute_authoring_store results and open both raised
StateConflict: Selection differs from its real committed result. Inline Python
replay exit0. This is the exact input previously accepted by26f.

The earlier static manifest-corruption hypothesis remains explicitly WITHDRAWN:
Workspace.get_run already verifies run.result bytes. It is not a second finding.

## Actual checks

Windows11 / Python3.12.14. Targeted Qt tests used offscreen and --disable-gpu;
TEMP/TMP=.local/p002-process-temp. No product edits or concurrent source changes.

1. uv run --locked --no-sync python -m pytest
   tests/test_workflow_authoring_store.py::test_editor_runs_rebinds_and_reuses_style_on_same_storage
   tests/test_workflow_authoring_web.py::test_graph_editing_preflight_and_saved_reopen
   -q --basetemp=.local/p009-independent-64c-boundary
   exit0: 2 passed in17.73s.
   This includes7 actual runs, correct cached original-execution provenance,
   fresh/cached output and cached-origin rejection at both results/open, immutable
   original manifest, real Web add/wire/replace/delete with separate saved reopens.
2. Original persisted wrong-selection replay described above: exit0, both rejected.
3. git diff --check <base> <head>: exit0.
4. Independent results-only formal raw/distribution/identity checker: exit0.
   Count, warmup flags, raw order, median, nearest-rank p95/max match. All35 actual
   pause/cancel request PIDs match final serialized RunRecords; cancellation records
   are cancelled, terminal phase is closed and editor_store_retained is true.

Prior10 authoring store/session/bridge tests on frozen26f passed34.06s; that result
remains historical, not a claim of rerunning them on64c. Full suite and repeated
wheels were not run by this reviewer. The parent was notified that Qt tests ended
before its next installed-wheel run began. No extra visual review loop was run.

## Measurement source and limits

64c raw: .local/p009-perf-results-64c02d9/results.json, action=results, standard only.
Each of4 preview groups and neutral control group has5warmup+30formal. The default
all-action measurement protocol is unchanged. results action explicitly retains
pause/resume/cancel because phase=closed triggers an automatic results read.

Preview feedback p95 milliseconds: forest329.2, ember331.4, iris342.2, neutral340.4.
Settled p95:417.0/417.8/381.9/434.0. Preserve ordinary100ms reference overruns;
these are click-to-result observations, not physical scanout or an exact standalone
host-ready-to-preview measurement.

Pause ack37.73ms; pause safe boundary1522.75ms. Cancel ack37.99ms; cancel-to-batch-
closed388.80ms. Separate UI feedback p95 pause203.5ms/cancel212.4ms; settled
377.0/361.9ms. Do not combine p95 segments or call batch closed editor-service
closed. Final editor shutdown was cleanup verification, not35 service-close timings.

64c renderer working set/peak3,568,234,496 bytes; private3,471,998,976 bytes.
Host working set505,315,328 bytes; peak595,046,400 bytes. These are per-process
snapshots/high watermarks, not total-worker-tree peaks. High memory remains real,
with cause UNKNOWN; no GPU or previous failure root cause is inferred.

Unchanged node selection/upper64 measurements remain explicitly26f historical:
normal iris136.8/neutral148.9ms exceed ordinary100ms reference; other normal node
74.8/94.4ms and upper p95 range82.5-99.6ms. They are not64c remeasurements.
Historical normal renderer WS about3.93GB/peak4.13GB is retained, not superseded
by the narrower64c results protocol. Earlier26f full raw statistics were also
independently recomputed. Trusted/active/visible input guards are observer facts;
no target fleet, physicalDPI/IME, complete-frame scanout or independent scientific
accuracy claim follows.

## Scope retained

Full static review covered editor graph/schema forms, catalog/ports, CAS and
serial-aware draft receipts, freeze-before-dispatch, external-storage ownership,
load/reopen/control/shutdown, result-only asset opening, shared CLI/new+legacy
portable templates, graph layout/computation separation, WB formula/source
isolation, installed probes and native observer changes. Original assertions,
thresholds, schema, dependency locks and mandatory checks were not weakened.

B012 planning files remain untouched. Only allowed .local report/probe copies
were written. Accurate final CI, current installed-wheel result, user experience,
scientificS1, clean target/physicalDPI/GPU and remaining program tasks must retain
their own real status; this acceptance does not close them by implication.
