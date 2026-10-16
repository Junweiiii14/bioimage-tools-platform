# T-039 WBQuant-compatible numerical supervision core

Status: implementing; parent T-037.
Scope: tools/wb numerical policies, independent lane geometry, grouped export, contracts.
Baseline: 5c4f376. Preserve legacy defaults; new web caller explicitly chooses policies.
Reference: user-specified WBQuant 1.4.3 MIT source, read only. No private TIFF committed.
Validation: pending; independent review by parent after commit.

## Implementation / validation

- Core commits d664684, ef17e6d; parent integration 88a4e46. Follow-up contains reference
  fixtures, schema snapshots, contracts and reviewer corrections.
- Separate original-package differential script: 5 synthetic cases passed; all 8
  specified-source Signals agree within 1e-10 at identical geometry. No source modified.
- `pytest test_quant_supervision.py`: 9 passed, exit 0.
- `pytest test_quant_supervision.py test_project_analysis.py test_automatic_wb.py test_analysis.py`:
  56 passed (before ninth added test), exit 0.
- Full WB run initially found 3 schema drift tests; refreshed additive default fields
  in v1/v2 document and v1 worker schemas (+26 each), no assertions removed.
- Full WB rerun reports 355 passed, but process exit 1 after Qt shutdown with no failure
  trace. This is not recorded as a successful full gate; parent must validate integrated tree.
- Scoped strict Pyright (9-test module and 4 new wrappers): 0 errors, exit 0; Ruff WB exit 0.
  Worktree Python runtime comes from coordinator venv; PYTHONPATH selects this tree's WB.
- A broad Pyright invocation with the shared editable installation produced duplicate-class
  path resolution errors in unchanged figure_project/laboratory_layout; integrated tree check
  remains authoritative. Local empty venv from an earlier missing-env hook run is untracked.
- Frozen third-party exclusions and explicit SciPy runtime dependency are explained in
  docs/contracts/wb-quant-supervision-v1.md, not silently weakening product checks.
- Independent review: parent/reference-audit identified invalid included peak removal and
  single-lane replan consensus; both corrected. Final product review owned by parent.

## Follow-up requested by parent: Fig-first supervision

- Public ordered_quant_rows shares display order with grouped export; split row appears once.
- Automatic recrop preserves custom composition; a whole-row N change updates only that row;
  incompatible multi-segment N change errors explicitly without resetting other layout.
- New test checks custom Fig columns/order, exported first-row numeric identity, recrop stability,
  single-row N adaptation, split-row rejection and fallback order. 36 related tests passed;
  latest supervision module 10 passed, exit 0. Ruff passed. No desktop files changed.
