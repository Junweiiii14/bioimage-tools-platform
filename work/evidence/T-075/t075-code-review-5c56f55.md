# T075 independent delta review — 5c56f55

- Reviewer: independent child agent t075_adapter_review.
- Reviewed head: 5c56f5509e8ad9381420e26af059e9c60501ebbb.
- Delta base: e8b034e970f687e47929987e5f2e800531d7b70f. Product change is 5c60e82; the following 5c56f55 commit updates the recovery snapshot only. Original product baseline remains T074 0376f23ccbf8b8047d532ec7708a1fa85581c087.
- Initial and final HEAD checks matched; tracked worktree was clean. Only this ignored reviewer report was written; product/specification files were not modified.
- Verdict: ACCEPTED for this scoped code delta. No new actionable P1/P2 identified. Prior accepted review conclusions remain applicable to unchanged code. This is not installed-product, CI, scientific, visual or publication acceptance.

## Guard and read-only boundary

- web_advanced.py:233–250 still validates operation schema, project identity and session epoch before open. Generation remains mandatory for every command other than open.
- Closing is rejected before the read branch. A valid open selects one of the four named tools, emits the current snapshot and returns. Only this branch now bypasses operation_busy; all other commands reach the same strict busy rejection before their business handlers.
- Inspected snapshot, book_summary, preview_page and emit, plus FigureView.project and its OCR/normalization/analysis/layout getter paths. They construct/validate current immutable document values and serialize data; they do not install a project, increment generation, submit a worker, cancel a task, update ROI/scientific values, approve workflow stages or invoke save/CAS.
- There are limited transient adapter effects: the selected tool name and latest response are recorded, and an already-stale derived-table cache may be cleared when its evidence identity differs. These affect presentation cache only, not scientific/project/history state. A successful open does not replace the tracked waiting write operation.
- The current_draft_saved and advanced_evidence_identity properties are reads of host identity/generation/verified object identity. Metadata remains bounded by summary and preview pagination. No frontend resource changed in this delta.
- The resulting UI may let the user inspect or locally edit fields while the host works. The backend still refuses applying those edits while busy or after generation changes; the previous draft/conflict mechanisms are unchanged.

## Actual commands and results

Workdir: C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform.

- git rev-parse HEAD; git status --short; git log -4 --oneline: exit 0; exact reviewed head, clean tracked tree, expected product-plus-document commit sequence.
- git diff --stat e8b034e..5c56f55; targeted git diff on web_advanced.py, tests/test_workbench_advanced.py and the revision contract; rg/Get-Content reads of snapshot and underlying view getters: reviewed the narrow guard move and its read path. One initial getter search used the nonexistent filename project_normalization.py; rg located the actual normalization.py and its complete plans getter was read before drawing the conclusion.
- git diff --check e8b034e..5c56f55: exit 0.
- git diff --numstat e8b034e..5c56f55 -- apps/desktop/src/bioimage_app/web_ui: exit 0, no output; frontend bytes are unchanged in this delta.
- PowerShell: $env:QTWEBENGINE_CHROMIUM_FLAGS='--disable-gpu'; uv run --locked --no-sync pytest tests/test_workbench_advanced.py::test_web_advanced_save_reopen_and_import_receipts -q
  - Exit 0: 1 passed in 2.24s.
  - This bounded test includes the deterministic busy getter substitution: read-only open succeeds while a same-generation template write receives the busy failure. Existing stale-generation write rejection and save/reopen/import receipt checks also ran as part of this test.
  - Root conftest uses offscreen Qt. No full suite or redundant browser/visual run was performed because frontend behavior was not changed here.

## Evidence and delivery limits

The author supplied installed-reproduction evidence that the open failure carried the actual busy rejection while background source reading was active. This delta directly removes that rejection only for read-only inspection; the focused test verifies the same guard condition deterministically. This reviewer did not execute the new candidate installation or independently capture that prior installed trace. Earlier uninstrumented timeout evidence should remain recorded rather than being rewritten as an independently reproduced root-cause finding.

The third candidate still needs to be built and checked at the final head. Neither earlier candidate is accepted for this revised product. No new installed resource comparison, physical DPI/GPU/native lifecycle assessment, final visual comparison or scientific holdout evaluation was performed by this reviewer. No merge/publication was performed or authorized. Later relevant changes require review bound to their new commit.
