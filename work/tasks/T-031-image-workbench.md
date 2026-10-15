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
