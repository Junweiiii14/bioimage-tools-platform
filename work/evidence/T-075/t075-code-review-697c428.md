# T075 independent diagnostic delta review — 697c428

- Reviewer: independent child agent `t075_adapter_review`, 2026-10-22.
- Reviewed head: `697c4287b4e35f048939828652bfe064e70e9718`.
- Delta base / installed candidate: `5c56f5509e8ad9381420e26af059e9c60501ebbb`; original product baseline remains T074 `0376f23ccbf8b8047d532ec7708a1fa85581c087`.
- Worktree: `C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform`; initial HEAD matched and tracked worktree was clean.
- Verdict: **ACCEPTED for this narrow diagnostic/documentation delta.** No new actionable P1/P2 identified in the changes. This does not fix or waive either CI180 failure and does not complete M6.
- Product/specification files were not edited; only this ignored reviewer report was written. No test suite, Qt session, build, install, merge or release was performed by this reviewer.

## Diagnostic preserves the test requirements

Reviewed `tests/test_intake_web_ui.py` around lines 1675–1780 and the exact 15-line diff:

- The original `angleInput.value === '4.8' && elementFromPoint(...).matches(...)` was replaced with one synchronous JavaScript evaluation returning JSON. It captures the live value and exact same hit-test coordinates, then the Python assertion still requires `value == '4.8'` and a true `runHit`.
- The `!!` conversion makes a missing hit explicitly false; it does not allow a missing element or another element to pass. Both diagnostic fields come from the same JavaScript invocation, so a failure can identify the relevant condition without separate event-loop turns between observations.
- Active element, hit element, connected state, fonts status, viewport and animation count are diagnostic reads. No focus assignment, value replacement, DOM click, layout mutation, resource wait, animation cancellation, timeout extension, retry, skip or tolerance was added.
- Existing QTest keyboard entry, coordinate extraction, real `QTest.mouseClick`, single-request wait and `intake_sequence_continue`/numeric `displayAngle === 4.8` output assertion remain unchanged. The wide and narrow parametrizations remain enabled.
- The extra reads/JSON serialization have some execution cost, as any instrumentation does. A future pass cannot establish that the old failure is fixed; the change is suitable for collecting discriminating evidence on a future failure.
- `test_repeated_window_close_and_collection` remains unchanged: 20 create/show/close/collect cycles with the original `resources_closed` wait. This commit adds no diagnostic or behavioral change to its native retirement path.

## Product and capture boundary

- `git diff --exit-code 5c56f55 697c428 -- apps/desktop packages tools` independently returned 0 with no output. Product Python, frontend assets, scientific implementation and package declarations are unchanged from the independently reviewed/installed candidate.
- No workflow, lockfile, test gate, timeout configuration or native-lifecycle implementation appears in the changed-path inventory.
- `tooling/capture_workbench.py` contains the same four-line diagnostic increment already inspected in the 5c56 delivery audit: a normal preview-session refresh before static capture and a `fixture_settle` report field. No pixel processing, font replacement, product style override or scientific value change was added. This diagnostic code is now committed; the candidate package identity remains 5c56f55.
- The installed-resource/fidelity conclusions therefore remain bound to the unchanged 5c56 product. A package must not be relabeled as built from 697c428 merely because its product tree is equal.

## CI180 failures and documentation boundary

Read the raw Windows and Linux logs and independently recomputed their SHA256 values. Both match `work/evidence/T-075/ci-180.json`:

- Windows: `d70523647d6927c33af134195b865a2a3aea1d27d079eeeb07f1aeb431dcf706`. The log records `test_rotation_preview_and_one_real_click_commit[False]` failing the old conjunction at coordinates 1306.5/746.0, 1 failed / 1191 passed in 746.36 s, and observed child exit 1. It does not record the live input value or which conjunct failed.
- Ubuntu: `f48c40d9b88a43c9ed4d7904c9acd45f93397abe455e27bd49e19c38e57c3fda`. The 60-second dump records a background thread in `wb_tool/ui/background.py:60 retire`, another in `bioimage_app/storage.py:129 execute`, and the main thread in pytest-qt waiting at `test_wb_desktop.py:530`. The later runner cancellation is recorded. Those Python frames do not identify a precise native lock owner, establish a deadlock cause, or prove a common cause with Windows.
- Both platform runs stopped before the wheel stage. Prior installation/fidelity evidence is separate and cannot substitute for the failed/incomplete required checks.
- The task, delivery document, validation record and current handoff explicitly retain CI180 as failed/unresolved and M6 unfinished. They do not claim the new diagnostic repairs the product or that local three-test success establishes the remote root cause.
- The author reports the two angle cases plus the unchanged 20-cycle close test passing locally in 4.57 s. This reviewer inspected their changes and existing assertions but did not rerun them or independently observe that earlier local execution. CI181 is a new observation, not a retroactive successful CI180; no CI181 completion claim is made here.

## Actual commands and scope limits

All commands ran in the activity worktree on local Windows 11:

- `git rev-parse HEAD`, `git status --short`, `git show --stat --oneline 697c428`, `git diff --name-status 5c56f55 697c428`: exit 0; expected head, clean tracked tree, only diagnostic tests/tools and documentation/evidence changed.
- `git diff 5c56f55 697c428 -- tests/test_intake_web_ui.py tooling/capture_workbench.py`: exit 0; exact diagnostic increments inspected together with surrounding test code.
- `git diff --exit-code 5c56f55 697c428 -- apps/desktop packages tools`: exit 0, no product difference.
- `git diff --check 5c56f55 697c428`: exit 0.
- Targeted `Get-Content` / `rg` reads of the test bodies, CI record, raw logs, task, validation and delivery/handoff boundaries. Broad log output was followed by a bounded Python extraction to read the relevant failure and stack lines without truncation.
- PowerShell literal here-string piped to `uv run --locked --no-sync python -`: exit 0; recomputed both raw-log hashes and extracted exact failure/stack/exit lines.

No full suite or redundant targeted Qt execution was justified for this review-only diagnostic change. The next required evidence is the actual diagnostic CI outcome; if it identifies a product or test-harness defect, that specific fix requires its own explanation and bound review. Existing physical-input, clean-Windows, scientific holdout and native UNKNOWN limitations remain unchanged.
