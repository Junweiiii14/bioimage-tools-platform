# T075 independent delta review — e8b034e

- Reviewer: independent child agent t075_adapter_review.
- Reviewed head: e8b034e970f687e47929987e5f2e800531d7b70f.
- Delta base: edafe65e1451ecf2e5cb695f9f6b33ddfda2e49e; original product base remains T074 0376f23ccbf8b8047d532ec7708a1fa85581c087.
- HEAD matched and tracked worktree was clean at initial review. No product/specification files were modified by the reviewer; only this ignored report was written.
- Verdict: ACCEPTED for this scoped code delta. No actionable new P1/P2 identified. This is not installation, visual, CI, scientific or publication acceptance.

## Reviewed correction

- web_advanced.py:233–239 parses the operation before context validation and exempts only read-only open from the generation equality check. Project identity and session epoch checks still apply. Busy/closing guards still apply. Every other command, including all writes, must match the current view generation.
- The open branch validates the requested tool, emits a current snapshot and returns before any project mutation/save path. Its updated generation is carried by the returned advanced snapshot. Thus an advanced save receipt arriving before the main periodic snapshot no longer makes the next same-project read invalid, without granting a stale draft permission to write.
- advanced.js:71 now shows escaped failure text and a reload action directly in the loading panel, where advanced-status does not yet exist. The failure receive path clears pending before enabling another request. The existing reload handler guards remember against absent data/draft and sends open with the selected section, so the loading-only retry has a valid route.
- Existing request-id/session checks and the panel ownership guard remain unchanged. Reading the latest snapshot still merges a retained dirty draft with its original baseline and current project values; scalar conflicts remain explicit and writes still use the new snapshot generation only after the existing merge/choice flow.
- No scientific calculation, schema, ROI, source asset, history, CAS transaction or save-success criterion is changed by this delta.

## Concurrent template path

The reviewed integration flow changes a local template scalar, installs a concurrent different host value, publishes its new generation, reopens the tool, requires conflict presentation and an explicit local choice, then saves. This path passed in the independent run below. No deterministic missing handler or bypass was identified in the inspected flow.

The previously reported single timeout after simulated template concurrency remains unresolved evidence: it lacked failure context and was not reproduced here. A busy response can now be displayed and retried rather than remaining in a loading-only panel, but this is not evidence that busy was the cause of that prior timeout. Do not erase or label that event root-caused based on repeated successful runs. The added test failure diagnostics provide host revision, busy, state revision, response/error and drawer text for a future recurrence.

## Actual commands and results

Workdir: C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform.

- git rev-parse HEAD; git status --short; git log -3 --oneline: exit 0, exact reviewed head and clean tracked tree.
- git diff --stat edafe65..e8b034e; targeted git diff on web_advanced.py, advanced.js, tests/test_workbench_advanced.py, revision contract and task record, plus rg/Get-Content reads of command/receive/status/open/reload/merge and drawer ownership: exit 0. Design-record changes were identified in the commit inventory but are not a rendered visual acceptance.
- git diff --check edafe65..e8b034e: exit 0.
- PowerShell: $env:QTWEBENGINE_CHROMIUM_FLAGS='--disable-gpu'; uv run --locked --no-sync pytest tests/test_workbench_advanced.py -q
  - Exit 0: 2 passed in 8.66s.
  - Includes real save/reopen/import/export chains, explicit forced stale main state before opening OCR, stale-generation write rejection, visible loading failure/retry control, late-response panel ownership, and concurrent template conflict resolution.
  - The loading retry control's presence is asserted; its handler was reviewed. The injected unavailable tool name remains deliberately invalid, so that particular test does not claim successful recovery by clicking retry on the invalid name.
  - Root conftest uses offscreen Qt; this review command disables GPU. QtWebEngine emitted repeated SharedImageManager::ProduceMemory non-existent-mailbox diagnostics near shutdown. The process still exited 0 and both tests passed. These diagnostics are retained here and are not claimed to be explained, harmless in every environment, or proof of hardware rendering stability.
- Runtime is the same reviewed Windows 11 x64 / Python 3.12.14 / PySide6 6.12.0 environment used for the preceding scoped reviews; no dependency/lock change is part of this delta.

## Delivery limits

The accepted previous code-review conclusions continue to apply to unchanged paths. No full test suite, CI, new candidate installation, physical DPI/GPU assessment, final visual comparison or scientific holdout validation was run by this reviewer. The edafe candidate is not evidence for the changed e8b034e product; rebuild and current-head source/wheel/install resource comparison plus installed advanced-flow verification remain required. No merge/publication was performed or authorized by this report. Later relevant product changes require a new bound-commit review.
