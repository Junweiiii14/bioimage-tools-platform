# T-023 independent code review

- Reviewer: `/root/frontend_audit`, read-only product reviewer; did not author the product changes.
- Base: `45e19854aefdc38dbe7def69b54f993d92de87f2`.
- Reviewed product HEAD: `0d9aad94c8bd7a93f34a24163af4fabe8d017d56`.
- Workspace: `C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform`.
- Date: 2026-10-15.

## Result

No actionable correctness findings in the reviewed diff. This conclusion is bound to the HEAD above; subsequent relevant product edits require renewed review.

Reviewed the desktop host/theme change, workflow/source selection, compact and full lane editors, evidence preview and summary, and profile rendering against the existing application contracts.

- Compact fields write to the existing lane table; programmatic synchronization uses `textEdited` and `_syncing` to avoid feedback edits. Excluded slots retain their disabled inclusion control. Source selection validates incomplete parameter drafts and preserves the previous selection on failure.
- Source switching clears the previous raster before loading the next. Both view and evidence panel check source SHA. Overlay ROIs retain original half-open pixel coordinates; only display labels change. Geometry/review mismatch withdraws the old plan and overlay while leaving unchanged source pixels available. Incomplete annotation text remains editable through the existing validation boundary.
- Curve data remains gated by exact request equality and uses the existing verified quantitative profile. New axes, labels and baseline drawing do not modify requests, scientific values or image pixels.
- Summary cells come from existing verified `ProjectTableCell` records and are invalidated after edits. `None` remains a dash and true zero remains zero; exclusion is not represented as a valid zero.
- Host cancellation, save, async work and export implementations are unchanged in this diff. Existing signal routes and busy-state ownership remain in place; the toolbar changes retain the existing command buttons as action owners.

## Independent validation

Command: `uv run --locked --no-sync python -m pytest tests/test_evidence_ui.py tests/test_workflow_ui.py -q`

Exit code: **0**. Result: **15 passed in 8.13s**.

Environment: Windows 11 `10.0.26200`, Python `3.12.14` (MSC v.1944, AMD64), PySide6 `6.12.0`, repository locked environment. HEAD was independently checked after the test run and matched the reviewed commit. Other dirty files observed were handoff/design-review records, not product sources.

Coverage includes bidirectional editor state, incomplete parameter/source-switch preservation, excluded slots, original-coordinate overlays, delayed preview rejection on missing sources, true-zero versus exclusion summaries, evidence layout at 1440×900 and 1100×780, and geometry edits withdrawing stale evidence without source reselection.

## Limits

This review did not run the full gate suite, clean-machine installation, real laboratory-image validation, or broad DPI/performance testing. It does not assert migration of the old WBQuant auto-peak, curve-drag, or next-group behavior. No product files were changed by this review.
