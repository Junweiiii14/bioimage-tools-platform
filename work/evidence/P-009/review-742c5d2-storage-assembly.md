# P009 storage assembly increment — product Accepted, artifact correction pending

Base:275560475d39426434416c74feeb0c2f259d1402
Head:742c5d26403b1509537ebe1cfd4cf6ba4b4e18ef
Increment:5e69b2f67eb0aeac7db81afee4033e021b8b1917..742c5d26403b1509537ebe1cfd4cf6ba4b4e18ef
Reviewer:/root/p002_independent_review

Product/assembly conclusion: Accepted. Existing default storage remains independent
of WB and NumPy; trusted authoring assembly supplies its fixed typed handler before
worker thread start. Commands still carry only immutable bytes and a fixed operation,
not callable/module names. Execution uses the same worker, Workspace, queue and
shutdown protocol. No new SQLite owner, dependency/gate exception or arbitrary loader.

The previous5e CI failure is real: both platforms failed the existing import-linter
contract before pytest/wheels. Earlier static review and installed smoke did not
prove static transitive purity. Historical acceptance does not convert that failed
CI into success. The implementation now fixes the actual dependency direction.

Actual independent commands on frozen742c (Windows11/Python3.12.14):
- uv run --locked --no-sync python -m pytest
  tests/test_async_storage.py::test_fifo_save_load_errors_and_shutdown
  tests/test_workflow_authoring_store.py::test_editor_runs_rebinds_and_reuses_style_on_same_storage
  -q --basetemp=.local/p009-independent-742c-owner
  exit0:2passed15.32s. QT_QPA_PLATFORM=offscreen, GPU flags--disable-gpu,
  TEMP/TMP=.local/p002-process-temp. Original FIFO assertions preserved; unconfigured
  authoring gives ValueError; actual handler calls all use one non-GUI thread;
  actual7runs and P1 wrong-output/origin rejection remain covered.
- uv run --locked --no-sync python -m tooling.import_contracts
  exit0:9kept0broken,269files/1900dependencies.
- git diff --check <base> <742c>
  exit1: original CI raw log ci-5e69b2f-failed.log has real trailing spaces
  (e.g.lines26,33,35). Do not record this exact artifact diff as passing.

Non-product evidence correction: preserve raw CI bytes losslessly as a binary gzip
with original+compressed SHA, rather than trim the original or weaken whitespace
rules. Parent is preparing this separate correction; it requires byte/hash review
on the final exact commit before extending the complete-candidate conclusion.

No full suite/repeated wheels/performance/visual run by reviewer. Original26f/64c
performance and64cwheel evidence retain exact source ownership; final current-head
mandatoryCI/wheels remain necessary. B012 untouched. No tracked source edits by
reviewer. This file is the allowed.local report only.
