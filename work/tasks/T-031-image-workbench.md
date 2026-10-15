# T-031 Image review workbench

Status: implemented; coordinator integration and independent review pending.
Base: a802b0f. Branch: codex/t031-image-workbench.
User approved T-028 proposal; scoped to WB workbench, direct manipulation and corresponding tests.

## Implemented
- Three visible modes: 图像复核 / 拼图 / 结果. show_section remains compatible, contextual tabs hidden from main navigation.
- Central source image plus expandable editable curve; contextual review reasons and advanced parameters; source names distinct from unknown protein.
- Actual curve boundary/baseline mouse handles and keyboard edits, crop keyboard movement/resizing, local undo/redo. Draft edits invalidate valid results, retain only same-lane verified profile evidence. Endpoint baseline mode stays unchanged when editing only bounds.
- Current crop confirmation never acknowledges measurement quality. Needs-attention filter keeps non-valid scientific states.
- Single package export plus disclosed individual formats; legacy command signals preserved.

## Validation
- uv sync --locked --all-groups: exit 0; isolated worktree environment.
- pyright: exit 0 (before final presentation-only edits); Ruff focused files exit 0.
- 29 focused UI tests: exit 0 / 25.43 s (workflow, image output, source canvas, evidence, three new manipulation tests).
- 16 existing project measurements tests: exit 0 / 41.59 s; real worker, OCR, normalization and reopen included.
- Initial combined UI+measurements run stalled after 11 cases without a stack; only its verified pytest child was terminated. Cause UNKNOWN. Separate faulthandler-enabled rerun passed; this does not establish root cause.
- Actual synthetic source/curve screenshot captured .local/t031-workbench.png, inspected. Root owns final integrated theme/motion and real-resource screenshots.
- Existing assertions updated for approved mode mapping, disclosed export controls, active shared source canvas and hidden advanced parameters. Final host menu expectation (5 actions, save now in menu) follows coordinator change and requires integrated verification; base host still has 4.

## Interfaces / limitations
- New view.undo_review()/redo_review(); plot focus selects curve history, otherwise crop history.
- Existing show_section source/analysis opens source workspace, analysis expands curve; layout/template mode 1; OCR/normalization/export mode 2.
- curve history scoped to currently loaded plan; source crop history stays within project. No scientific algorithm/schema/default changes.
- Full legacy panels retained. Root owns autosave/recompute scheduling, project entry, theme/motion, documentation/handoff, and commit-bound independent review.

## Independent review follow-up — 2026-10-16
- Fixed history loss during the host's 700 ms autosave and subsequent recomputation. Per-row history is retained only for matching source/geometry/polarity and matching current annotations; project switches clear it. Raw profile cache is bounded to the current source/geometry, never restores an effective numerical result.
- Same-project set_project now preserves selected source by row/source identity, original raster, current lane, and review focus. It does not emit source_requested during the host's busy callback. Different project/source clears selection and raster.
- Added public refresh_attention() for the host after verified cells install; it updates filter/list without asynchronous reselection.
- Source filenames use middle elision and full tooltip; template form uses vertical labels and wrapping instead of horizontal clipping. Root handles contextual panel titles/return actions.
- Regression executes the real 700 ms autosave, waits for a new worker run, verifies nonzero selected lane, canvas, no source request, keyboard focus, surviving undo and invalid effective values after undo. Foreign-project reset tested on an unattached view; directly injecting a foreign document into an open host workspace is not a valid host switching sequence and initially caused teardown-save failure in the test, corrected without changing production host guards.
- Final follow-up validation: 19 workbench/evidence/workflow tests passed in 14.23 s; Pyright 0 errors. Prior run exposed lane reset in show_plan and child-focus restore ordering; both fixed and covered. Root performs final commit-bound independent review and integrated visual capture.

## Reopen / preview result-table regression — 2026-10-16
- A real restored copy of the delivered ZIP showed 10 source rows / 51 result cells after reopen, then zero cells after entering template and automatically composing. Preview pixels were present; this was actual presentation invalidation, not capture timing. Original inputs and completed outputs were not changed.
- Root delegated figure_window.py for this bounded fix. Successful save now reconstructs result tables from verified runs before invoking its follow-up callback. This covers preview, manual save and metadata-only autosave without retaining stale cached values. Existing generation/cancel/close guards remain.
- Same real ZIP probe after fix retains 51 cells through automatic preview. Probe lives under .local and works on a newly restored copy.
- New regression reopens a saved project, enters template, checks preview and export view numerical values, then changes only a protein label and waits for actual autosave; current labels and exact values remain visible. Its crop-height fixture is 40 px because the previous 10 px numerical fixture correctly cannot fit a 24 px display label; no renderer guard or numeric expectation was relaxed.
- Post-fix validation: workbench + project measurements 21 passed / 52.44 s; archive restore + project archive export + direct figure image + template I/O 29 passed / 31.11 s; Pyright 0 errors and Ruff pass. The coordinator's earlier full 559-test run predates this final host fix and must not be represented as a full run of this commit.

## Save-refresh cancellation boundary — 2026-10-16
- Independent review reproduced schema-8 save -> project table -> derived table clearing a cancellation at the second phase and launching an export/recognition follow-up. Both completion callbacks now guard cancellation/closing before any phase transition or follow-up. Cancel also stops pending derived-table refresh timers. Explicit fresh refresh remains available.
- Added actual asynchronous storage/background regression for cancellation in both phases, pending refresh timer suppression, and successful explicit refresh after cancellation. No scientific expectations or gate tolerances changed.
- Related workbench/measurements/cancellation tests: 23 passed / 50.46 s before final pending-timer and explicit-refresh assertions; final expanded cancellation tests: 2 passed / 4.34 s. Ruff passed. Final Pyright recorded after protected test-state setup moved to monkeypatch.
