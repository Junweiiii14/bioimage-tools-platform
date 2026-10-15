# T-032 Contextual WB tools

Status: implemented; awaiting coordinator integration and independent review.
Base: a802b0f7e7ea08f9426190b49aed9baeae4165b7. Branch: codex/t032-context-tools.
Authorization: user approved T-028 implementation, including aesthetics and purposeful motion.
Scope: four WB UI panels and new contextual UI tests. Shared theme/motion, host navigation, auto project lifecycle and final real-resource acceptance belong to coordinator/T030/T031.

## Changes

- Metadata: choose common values, filename extraction or table; preview before explicit field/row application; input section collapses for review; clear actions for notes/empty lanes preserve existing semantics.
- OCR: large image plus contextual correction/binding pane; no empty tables/actions before source; full recognition, editing, raw evidence, binding, results and export preserved.
- Normalization: sources, explicit sample pairing and results in sequential views; missing reviewed sources explained. Preparing a new relationship no longer changes the active relationship type.
- Layout: selected segment controls synchronize with existing table; full segment table is advanced; splitting preserves scientific geometry and existing signals.
- Existing public widget attributes, signals and host-facing methods retained. No schema, algorithm, semantic default, dependency or gate changes.

## Validation (Windows, Python 3.12.14 / locked PySide6 6.12.0)

- uv sync --locked --all-groups: exit 0.
- Scoped Ruff check/format and Pyright for four panels plus new test: exit 0, zero type errors.
- pytest tests/test_project_metadata_ui.py tests/test_laboratory_layout_ui.py tests/test_project_measurements.py -q: exit 0, 25 passed / 66.82 s (before final relationship-type separation).
- pytest tools/wb/tests/test_contextual_panels_ui.py tests/test_project_measurements.py -q: exit 0, 20 passed / 36.76 s after relationship-type separation.
- Final contextual tests after single-source empty-state improvement: exit 0, 4 passed / 0.66 s.
- First new-test run failed because test called make_normalization_plan with wrong signature; corrected test call to actual public contract, no product semantics or expected values weakened.
- Standalone actual Qt screenshots: .local/t032-screens (ignored), examined 4 panels with synthetic evidence. Layout minimum 265x469, shown 280x700; other panels 1100x700. These use OS default palette, not final coordinator theme. Screenshot helper initially needed repository PYTHONPATH; corrected, exit 0.
- Full integration, motion, real private WB resource processing, 125/200% DPI and independent review remain coordinator acceptance work. No claim that isolated panels are a completed product.

Coordinator owns shared handoff update to avoid cross-worktree snapshot conflicts; this task is the handoff for this subtask.
