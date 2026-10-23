# T075 independent code review — fa746fa

- Reviewer: independent child agent t075_adapter_review; read-only product/specification review. Only this report and an ignored resource comparison report were written.
- Base: 0376f23ccbf8b8047d532ec7708a1fa85581c087 (T074).
- Reviewed head: fa746fa953eedc4b491091876dfe1d6830373a15, branch codex/t075-ui-system. HEAD matched at the start and final environment check; tracked worktree was clean throughout the reviewed reads/tests. While this report was being finalized, the author began follow-up edits to figure_window.py, web_advanced.py and web_window.py. Those uncommitted edits are not covered by this bound-commit conclusion.
- Scope: advanced web template/metadata/OCR/normalization commands and receipts; new workbench revision public use cases; host callbacks and save guards; appearance persistence; frontend drafts, conflict handling and stale-response isolation; frontend resource packaging.
- Verdict: changes requested. Two P1 findings and one P2 finding below. This is not a merge, publication or full-product acceptance authorization. Subsequent relevant changes require review against the new commit.

## Findings

### P1 — OCR recognition failure is cleared by the subsequent table refresh

- Location: apps/desktop/src/bioimage_app/figure_window.py:973–980; related refresh_ocr_table at 704–731, _start at 1643–1647, and web_advanced.py:177–222.
- Trigger: ocr_recognize / ocr_composed reaches ProjectOCRSession completion with loaded=None, for example an OCR engine or result verification failure, while the previous valid OCR/table state remains available.
- Path: completed stores the failure in operation_error, then calls refresh_ocr_table(message). That calls _start(), which resets operation_error to the empty string. Successful derivation of the old table then ends busy. AdvancedCommands.poll has no independent OCR recognition completion/save receipt and emits done. advanced.js uses the earlier persisted input state to show saved.
- Impact: a failed scientific operation is acknowledged as successful; the user can believe recognition was updated while the prior OCR state is still in use. Existing verified numbers are not directly rewritten, but operation status is false.
- Required correction: preserve a request-specific terminal OCR error through auxiliary refresh, and acknowledge recognition success only after the matching installed candidate has received the real save callback. Refreshing old tables must not overwrite the recognition outcome. Cover a failed OCR completion followed by a successful old-table refresh.

### P1 — Intake group-editing OCR completion can escape the Qt callback and leave busy set

- Location: apps/desktop/src/bioimage_app/figure_window.py:1024–1036, specifically prepare_workbench_revision at 1028; related session.finished.connect(completed) at 1037 and web_advanced.py OCR host routing.
- Trigger: an Intake project already has OCR state, then a structural metadata edit enters workflow.editing=True. The web command still permits ocr_recognize and starts OCR. A successful recognition reaches completed.
- Path: prepare_workbench_revision rejects workflow.editing, as required by the public contract. This call runs directly in ProjectOCRSession.finished -> completed, not in _storage_reply or _wb_reply. Their newly added exception catches do not protect this callback. The ValueError therefore escapes while _busy remains true and no matching advanced failure receipt is emitted.
- Impact: the advanced request and host can remain in a permanent busy state after a normal supported project edit. The correct scientific editing guard must be preserved.
- Required correction: validate the allowed Intake phase before starting recognition; also catch domain/validation failures while processing this session completion and end the operation with its matching failure receipt. Do not solve it by allowing processing during grouping review.

### P2 — Appearance refresh is attached to shutdown instead of the regular poll

- Location: apps/desktop/src/bioimage_app/web_window.py:384–386 inside _begin_shutdown; _poll_session at 500 has no appearance refresh.
- Trigger: two open workbench windows share the same release-channel QSettings, and one changes theme/density/motion.
- Impact: the other active window never refreshes its WorkbenchAppearance.values; its periodic snapshots continue publishing the previous appearance. The documented one-second cross-window synchronization only happens when shutting down.
- Required correction: put the throttled refresh in the normal session poll and publish the updated snapshot. The existing settings unit test explicitly calls second.refresh(), so it does not verify host integration. Add a focused host-level two-window/poll check.

## Previous six findings recheck

1. Latest Intake direct mutation: principally corrected by prepare_workbench_revision/apply_workbench_metadata/revise_workbench_figure_order; stable identities, schema, crop/figure/output invalidation and existing grouping revision APIs are retained. The OCR phase/callback hole above remains.
2. Import host paths: font import now validates an immutable prepared candidate before installation; OCR import prepares revision and storage/background callbacks catch validation errors. Direct ProjectOCRSession completion still has the P1 gap above.
3. False save receipts: font/OCR/template imports now chain real host.save; normalization create/remove require _saved; UI checks persisted. Recognition failure is still misreported as described above.
4. Stale result tables: cache now binds project/generation/verified result object identities; frontend clears visible derived tables when the main revision changes. No remaining issue found within reviewed paths.
5. Normalization draft loss: create/remove are blocked while dirty; switching the active relation is blocked while its draft is dirty. Reload uses explicit three-way comparison/conflict selection. No remaining issue found within reviewed paths.
6. Whole-workbook serialization: book stays server-side; only sheet summary/header plus 20-entry preview pages cross the bridge, with preview identity and cross-page draft preservation. No remaining issue found within reviewed paths.

Earlier file-dialog premature completion and unmatched busy-error receipts also remain corrected: waiting is established after dialog/context verification, advanced_ui handles its own busy/closing error, and client payload length is checked.

## Commands and actual results

Workdir for all commands: C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform.

- git rev-parse HEAD; git status --short; git branch --show-current: exit 0; exact reviewed head, codex/t075-ui-system, clean tracked tree. Repeated HEAD/status at the final environment check with the same result. A post-report verification then observed author follow-up edits in figure_window.py, web_advanced.py and web_window.py; they require a new commit and follow-up review.
- git diff --stat 0376f23ccbf8b8047d532ec7708a1fa85581c087..fa746fa953eedc4b491091876dfe1d6830373a15 and targeted git diff/git show, rg/Get-Content reads: inspected the committed code, task/rules, contracts and tests. Initial combined file searches included nonexistent wildcard/file paths; these were corrected by rg --files and direct current paths; no result was inferred from failed searches.
- PowerShell: $env:QTWEBENGINE_CHROMIUM_FLAGS='--disable-gpu'; uv run --locked --no-sync pytest tools/wb/tests/test_workbench_revision.py tests/test_workbench_advanced.py tests/test_workbench_appearance.py -q: exit 0, 12 passed in 11.05s. Root conftest selects QT_QPA_PLATFORM=offscreen. This was one bounded affected suite, not full regression.
- uv run --locked --no-sync python tooling/verify_workbench_resources.py --source apps/desktop/src/bioimage_app/web_ui --wheel .local/t075-wheel-probe/bioimage_app-0.14.0-py3-none-any.whl --output .local/t075-review-resources-fa746fa.json: exit 0; 34 frontend files, no missing/extra/changed wheel resources. Includes local font, license, SVG, CSS, JS and HTML. This verifies bytes of this wheel resource tree, not the installed product or all wheel Python code.
- uv run --locked --no-sync python -c "import platform, sys, PySide6; print(platform.platform()); print(sys.version); print('PySide6', PySide6.__version__)": exit 0; Windows-11-10.0.26200-SP0, Python 3.12.14 x64 MSC v.1944, PySide6 6.12.0.
- git check-ignore .local/t075-code-review-fa746fa.md: exit 0, review report is ignored local evidence.

## Limits

- Findings are grounded in committed control flow; the two newly identified failing OCR branches were not injected into a live OCR engine in this review. The focused tests exercise existing successful real-worker/CAS/web/reopen paths and public scientific invalidation cases.
- No new broad/full test run, CI, installed candidate execution, physical DPI assessment, GPU stability assessment, full visual/motion comparison, clean Windows 10 run, independent scientific truth/holdout test or merge/publication was performed.
- The new build profile keeps an independent AppId/settings namespace/install directory. Source-to-wheel frontend bytes match; source-to-installed comparison is still required for delivery.
- Reviewed application changes preserve original source assets and historical runs/outputs; no scientific algorithm, project schema, hidden-widget-value injection, arbitrary-module load or test/gate weakening was found in this scope. This does not supersede the outstanding findings or pre-existing recorded native/target-machine limitations.
