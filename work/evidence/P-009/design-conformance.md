# P-009 design conformance

2026-11-02 · ordinary Operate extension of the existing Windows workbench. Documentation check by the shipped `impeccable_documenter` instructions and `reference/document.md`; no new visual world or system refresh authorized or needed.

## Evidence and source boundary

Checked `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json`, `.impeccable/surfaces/workflow-authoring.md`, `design_tokens.css`, and the workflow authoring/graph JS and CSS under `apps/desktop/src/bioimage_app/web_ui`. Compared source component patterns, not new computed-style/browser measurements. Read `work/evidence/P-009/visual-review.md` and the existing `.local/p009-ui-detect.json`; did not rerun detect or capture screenshots.

Repository `bioimage-v0`, branch `codex/p009-visual-workflow`, HEAD `bb42d6b9116ecf05085bc5a0e076d334d02f3f28`, with the final responsive fix still uncommitted. At inspection, authoring JS/CSS, graph JS and the visibility-aware test were modified; graph CSS was unchanged. B-012 files were unrelated and untouched.

Source SHA256 at check (relative to the web_ui directory):

| File | SHA256 |
|---|---|
| workflow_authoring.js | c3b89a6ee7d0d361abdf1dd7221a8426d549e54433d6f9ff96595f68e3650125 |
| workflow_authoring.css | 61585953e56c72dd1abf104ad39e56f35c8087c25a6b9c974cc0d8b76a11d9d8 |
| workflow_graph.js | 426b86474bb69a302d422f5d23947282d5705762c673d3f996da56055ee39379 |
| workflow_graph.css | b06abec81ab669895bbd0f8e8782290f6a83aef27ee925e50997a9616136f804 |

## Conformance observations

The incumbent system remains aligned for this extension. Preserve existing PRODUCT/DESIGN/sidecar and the surface brief; no global tokens or rules were rewritten.

- Palette: catalogue, graph, inspector, fields, status and connections use incumbent `paper`, `ground`, `ink`, `muted`, `line`, `accent`, `accent-light` and danger roles; forest, ember, iris and neutral remain defined by the existing shared token sheet. No new raster assets.
- Type: inherited local `WB Sans` / Noto Sans SC, genuine variable weights and no synthesis. Body inherits 14px/1.5; section titles 16px/550, dialog title 22px/550, auxiliary text mainly 12px. Responsive title 18px and path 11px are local density choices, not additions to the public type ramp.
- Components: public primary/subtle buttons and theme surfaces persist. Editor buttons, selects and non-checkbox inputs retain at least 40px; checkbox geometry remains 20px. Fields/ports use 6px corners, nodes/dialog 12px, focus is 2px accent with 3px offset. Neutral result-image backing does not imply theme transformations of scientific content.
- Task layout: desktop catalogue + graph + inspector, local scrolling, 1100px view switching and 650px narrow layout preserve task access. The final short/narrow rule compresses persistent chrome without shrinking ordinary controls. Current-step selection stays available in parameters; concise fields precede advanced module/version/replacement/method information and full JSON/schema details. These are surface rules, not global breakpoint changes.
- State language: source keeps saved revision, unsaved edits, preflight errors and frozen batch/current draft distinct; graph geometry is represented separately from parameters. Save/freeze uses host commands and receipt handling. This documents visible intent and structure only; it is not a concurrency, transaction or scientific correctness review.

The Scientific Neutrality, One Font, Stable Position, Evidence Stays Still and Real Receipt rules remain the applicable incumbent rules. No new prohibitions or craft defects were canonized.

## Existing drift and advisory, left unchanged

The sidecar narrative overview still describes T075 CI and delivery review as pending, whereas DESIGN.md records CI181/review success; PRODUCT.md's Evidence on Hand still points to historical T076. These pre-existing provenance/status statements are not P-009 task authority and were not repaired in this ordinary extension. The surface brief's unaccepted probe wording is also historical; use the task and scoped evidence for current status.

The existing detector reports zero primary findings and one advisory: `rgb(24 60 52 / .24)` on the workflow dialog backdrop is outside the recorded palette. DESIGN.md records another historic drawer backdrop. Keep the workflow literal as a local observation; do not promote it into a shared palette token or silently repair it. The independent visual review did not score it as material.

## Exact visual verdict boundary

The fresh independent reviewer opened all 12 required current detailed captures, initially scored narrow-window task density as the sole material fix, and reopened all 12 after one fix batch. The reviewer marked that finding resolved and returned **ship for the scored fix only**: 960x640 parameters now expose signal polarity immediately; 640x720 graph shows a complete preflight node and readable ports; title, save/run, status, saved revision and local scrolling remain visible. Four-theme identity was preserved with no material regression identified from that batch.

That is the verdict reported in `visual-review.md`, not a new visual inspection by this documenter. Captures are native Windows active-window/software-GPU static evidence at CSS viewports 1440x940, 960x640 and 640x720; no animation sequence is evidenced. It does not approve the whole surface, performance, scientific validity, physical IME, installation or target-machine acceptance. This check runs no tests, code review, browser/server or new captures; existing reports retain their own limits. Subsequent relevant source changes require renewed evidence.
