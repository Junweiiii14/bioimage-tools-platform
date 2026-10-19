# T-037 validation

Product baseline e8e5e21; final product 9be19b1 on codex/t037-quant-supervision.
Windows / Python 3.12 / locked environment. Full gate and final targeted regressions passed; static visual review ship.

## Implemented contract

Workflow: original crop → Fig composition/labels → Fig quantitative supervision → tables.
Group overview uses current rendered manifest sourceRoi/sourceLaneRange, never display pixels for integration.
Each lane displays separate source-protein profile segments. Segment gaps, labels and borders do not contribute.
Single-source lane geometry, bounds and baseline edits invalidate old evidence and recompute asynchronously.
Tables and group/side navigation share composition-aware stable row identities. Included invalid peaks retain empty slots.
Raw Signal and quality status remain separate. No mandatory per-image confirmation or native quantitative window.

WBQuant 1.4.3 MIT source frozen in domain/wbquant143. RGB integer BT601, inverted mean row profile,
linear baseline and positive trapezoidal integral, no width multiplier. Existing document defaults remain legacy.
Five original-package synthetic cases plus both specified real sources compared independently;
8 real Signals within 1e-10 for identical ROIs. Unequal 1px integer lane widths are a documented adaptation.

## Checks and failures retained

- Core initial 48 tests and later 56 related tests passed; final core 11 supervision tests exit0.
- New host/bridge integration first 7 tests passed; expanded Fig-group test passed exit0.
- First full check stopped at domain pathlib import boundary. Corrected pure string identity; no rule weakening.
- Second full check: 592 passed / 1 failed in516.25s; existing-project append had no composition segment for new source.
  This left crop unavailable and old confirmation teardown timed out. fb6e461 adds only missing pending-row segments,
  preserving other layout and full structural validation. Original failing test independently passed in13.49s exit0.
- Existing schema tests revealed missing new request fields; three schemas extended with backward-compatible defaults.
- Ruff/Pyright/import contracts passed after fixes. Frozen third-party files alone have scoped lint/type exclusions;
  wrapper and all application code remain checked. WB explicitly declares already-locked scipy dependency.
- Local Qt harness initially used SVGElement.click (not available) and missed intended detail edit; corrected dispatchEvent
  and asserted editor presence. This was an invalid verification attempt, not product completion evidence.
- Synthetic group initial different detected crop widths correctly refused composition. Fixture corrected to equal geometry;
  final visual/group evidence pending. Refusal is not counted as successful montage verification.

## Independent reviews

Reference audit initial four findings fixed: detection warnings exposed, stable included-band ordering,
invalid-peak slots retained, full-lane border consensus on replan.
Review e8e5e21..dfd62e3 found layout-order sidebar numbering mismatch; f3882b9 uses shared rowOrder.
Incremental review dfd62e3..fb6e461 found no new issues; previous findings resolved. UI finish review requested quality badges/reasons and adjacent-Fig clipping;
fa5e5e3 fixes these, documenter updated three design documents. Final screenshot verdict ship on9be19b1; all three material findings resolved.

## Boundaries

Two specified originals are 3 and5 lanes, kept separate Fig groups; not paired as one biological experiment.
No original overwrite/resampling. Broad detection accuracy, biological normalization, clean-Windows packaging,
remote CI/PR/main integration not verified in this task. OCR/template/normalization still native advanced tools.
Private TIFFs, local screenshots/results and old software are not committed.

## Final full gate

2026-10-17 `uv run --locked --no-sync python dev.py check --all` exit0 on fb6e461: 594 passed in396.92s, Ruff/format/Pyright,9 import contracts, isolated wheels, desktop async close, bundled OCR and worker checks passed. Afterward 043103d changes only overview right clipping margin45→10; node syntax and real desktop recapture verify that delta.

## Final actual operation evidence (local/private)

2026-10-17 .local/t037_real.py exit0: specified original TIFFs unchanged by hash;3/5 lanes,8 filled Signals;
DOM baseline edit and actual Qt pointer drag both recomputed; XLSX/CSV saved; table click returned correct original;
legacy native quant host remained hidden. Reopened saved workspace in visible WebWorkbenchWindow (2rows).
.local/t037_group.py exit0 with explicitly synthetic inputs:2proteins×3lanes,6 values, current montage present,
6 mapped lane boxes, no manual confirmation. Initial fixture differing maximum intensity changed auto-crop width;
corrected fixture preserves common maximum and verifies montage rather than merely curve availability.
Screenshots quant-group/quant-desktop/quant-table/quant-narrow, synthetic-group/synthetic-narrow and opened-desktop
are local evidence, not committed images. Saved results remain under .local/t037/projects; launcher reads latest
successful verification.json. Old software folder and original source files remain read-only.

## Reopen correction and final review

Final desktop reopen exposed a load/compose race (source selection makes host busy before immediate compose).
9be19b1 defers one overview compose until idle, checks current project/row, clears pending on cancel or detail selection,
and does not retry failures. New source-load→montage test passed1/14.14s exit0; six existing bridge tests passed in
preceding targeted run. Test fixture now supplies its duplicated protein row composition (previous fixture failed
correctly for a missing layout segment); no timeout/expected-value weakening. Ruff/Pyright/Node syntax passed.
Actual saved two-source workspace reopened visibly with current Fig montage; final opened-desktop.png captured
2026-10-17 00:19:01. It retains a deliberate baseline edit (3027.39), distinct from initial automatic3557.70;
automatic initial measurements are recorded separately in verification.json. Full594 gate was before this focused
reopen/clip delta; not represented as a rerun on9be19b1.
Independent code review e8e5e21..9be19b1: no unresolved findings. Static finish reviewer: ship;
quality reason, current-Fig clipping and documentation resolved. Documenter retained incumbent visual tokens;
pre-existing design.json narrative drift was reported and not silently rewritten.
