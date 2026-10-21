# T075 independent follow-up review — 1d872bf

- Reviewer: independent child agent t075_adapter_review.
- Product base: T074 0376f23ccbf8b8047d532ec7708a1fa85581c087.
- Reviewed head: 1d872bf2c09c9463b463f18412139da160f0be0d.
- Follow-up diff: fa746fa953eedc4b491091876dfe1d6830373a15..1d872bf2c09c9463b463f18412139da160f0be0d.
- HEAD matched and tracked worktree was clean at initial and final checks. Product/specification files were not modified by this reviewer; only this ignored report was written.
- Verdict: ACCEPTED for the scoped code follow-up. All three findings in t075-code-review-fa746fa.md are resolved. No new actionable P1/P2 finding was identified in the reviewed follow-up paths. This does not authorize merge/publication or claim complete visual, installed-product, scientific or target-machine acceptance.

## Rechecked findings

1. P1 OCR failure lost during auxiliary table refresh — resolved.
   - figure_window.py:982–985 terminates failed recognition using _error; it no longer launches a second operation that clears operation_error.
   - Successful recognition propagates the explicit after callback through recognize_composed_figure, _attach_ocr_source, recognize_project and _start_ocr. The callback is reached after candidate save and the guarded derived-table refresh, not merely after busy becomes false.
   - web_advanced.py:216–219 requires _saved for ocr_recognize/ocr_composed. saved_recognition at 567–569 checks the same host/session before acknowledging the operation. A stale/uninstalled/cancelled result does not obtain this callback.
   - The targeted bridge test injects failed OCR completion, checks failed receipt, preserved prior association and released busy. The save-failure/retry test checks no success callback on rejected CAS, exactly one on successful retry, and retained historical run evidence.

2. P1 Intake revision guard escaping direct Qt completion — resolved.
   - Both recognition entry points validate prepare_workbench_revision before starting processing (figure_window.py:857–927), so group editing remains prohibited rather than weakening the domain guard.
   - The direct session signal now connects safely_completed at 1043–1049; domain/validation/I/O failures become _error terminal state instead of escaping the Qt callback with busy still set.
   - Parameterized focused checks reject preflight and completion separately. Both retain the prior OCR association, emit no saved callback and leave the operation non-busy.
   - These parameterized tests inject the domain rejection into a real OCR host flow; they are not an additional full Intake batch integration test. The unchanged public Intake guard and invalidation implementation was reviewed/tested in the preceding bound review.

3. P2 cross-window appearance refresh only during shutdown — resolved.
   - web_window.py:498–500 now refreshes appearance in _poll_session with one-second throttling; the shutdown-only refresh has been removed.
   - The targeted two-window WebEngine test changes the theme through a real webpage button and waits for the other active host and its document theme to update, without explicitly calling second.refresh().

## Actual commands and results

Workdir: C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform.

- git rev-parse HEAD; git status --short: exit 0, exact reviewed head and clean tracked tree. Repeated after the test with the same result.
- git diff --stat fa746fa..1d872bf; targeted git diff for figure_window.py, web_advanced.py, web_window.py, the three affected test files, and the small UI/capture additions: exit 0. Related rg/Get-Content reads checked callback ownership, error reset, successful receipt routing and polling placement.
- PowerShell command:

  $env:QTWEBENGINE_CHROMIUM_FLAGS='--disable-gpu'; uv run --locked --no-sync pytest tests/test_workbench_advanced.py::test_web_advanced_save_reopen_and_import_receipts tests/test_workbench_appearance.py::test_open_windows_receive_theme_from_host_timer tests/test_ocr_late_installation.py::test_ocr_association_save_failure_preserves_old_and_allows_explicit_retry tests/test_ocr_late_installation.py::test_ocr_revision_guard_failure_ends_operation -q

  Exit 0: 5 passed in 21.99s. The guard test expands into two parameterized cases. Root conftest selects offscreen Qt; this run intentionally uses software rendering and does not assert hardware/GPU stability.
- Environment: same checked workspace/runtime as preceding review, Windows 11 x64, Python 3.12.14, PySide6 6.12.0. No dependency/lock changes in this follow-up.

## Scope and remaining acceptance boundaries

- The fa746fa review's other six-risk follow-up conclusions remain applicable to unchanged code: public Intake revision API, schema10 processing prohibition, immutable historical evidence, import-after-save receipts, cache invalidation, normalization draft guard and bounded metadata paging. No scientific algorithm/schema, original-input overwrite or test/gate weakening was introduced by this correction.
- Small UI changes were inspected for code impact: sidebar icon, scoped field/list styles, results layout, preview-only toolbar reservation and real CDP pointer actions in capture tooling. No scientific data path is changed. This is not a rendered visual/motion acceptance or a review of the resulting recording.
- No full suite or CI run, candidate install, physical DPI/GPU assessment, clean Windows 10 check or scientific holdout evaluation was performed here. Existing native/target-machine uncertainties remain as recorded.
- The preceding 34-file source/wheel equality report belongs to fa746fa. Since this commit changes frontend bytes, it must not be reused as proof of 1d872bf resource equality; the new candidate still needs its source/wheel/install comparison.
- No merge or publication was performed. Any later relevant product changes invalidate the associated portion of this review and require a new bound-commit check.
