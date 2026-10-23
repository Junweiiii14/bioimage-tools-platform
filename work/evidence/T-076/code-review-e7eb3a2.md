# T076 independent code review — changes requested

- Reviewer: independent delegated code reviewer, not the implementation author.
- Reviewed base: `7fcb8192ada7acf5695e74f23cbe010ffd862966`.
- Reviewed head: `e7eb3a2851efa8b43bbefb34b5b56ce8738a39fc` on `codex/t076-platform-home-scroll`.
- Review date/environment: 2026-10-22; Windows 11 build 26200; Python 3.12.14; PySide6 6.12.0; `QT_QPA_PLATFORM=offscreen`; `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`.
- Read root AGENTS, task T076, existing scope receipt, handoff pointer/risks/backlog, module map, desktop README, architecture/coding/workflow rules, and batch-supervision/workbench-revision contracts. Reviewed the full product diff and the added tests/capture changes. The old T075 handoff pointer is not evidence of T076 completion.
- Initial reviewed worktree was clean. Later `PRODUCT.md` and `docs/design/` changes belong to parallel author work and are outside this commit-bound conclusion. Product source and repository tests were not modified by this reviewer. Local probes are in `.local/t076_review_probes.py`.

## Findings

### 1. [P1] Route WB-home independent imports through project replacement

Changed entry point: `apps/desktop/src/bioimage_app/web_ui/platform_home.js:30–36` (especially line 35), and the now-live WB home in `index.html:48–50`. Existing downstream action paths: `desktop_session.js:86–89`; `web_window.py:198–210,227–233,337–344`.

Trigger: open project A, keep an unapplied manual-grayscale draft, browse to WB home, expand “独立灰度与裁图”, and use “选择原图” to select a new TIFF B. The new shell correctly keeps A alive, but these home actions still call the old append commands (`quant_import`, `import`, `folder`/`import_folder`). `_import_paths()` sees an existing workspace and imports B into A. The home still promises “选择 TIFF 后自动创建独立项目”. The folder and crop variants use the same append semantics by inspection.

Impact: the home action unexpectedly changes the existing experiment project instead of creating an independent project, and does not invoke the existing project replacement draft/save/cancel guard. This is newly reachable through the project-preserving WB-home navigation; the previous home route retired the active host.

Independent reproduction used the real WebWorkbenchWindow, async storage, synthetic TIFFs, DOM button click and a patched native file chooser only. The first project ID remained `9ce8f397c15d423380350991e52f830b`; `sameHost=True`; row count changed from 1 to 2; `stage='opening'`; `desktopSession.hasDraft()=True`. No `confirm_draft` stage preceded the mutation. Probe `test_wb_home_new_images_keep_project_replacement_guard` failed its guard assertion (exit 1).

Requested correction: make every WB-home independent import variant explicitly start a new project through the existing transition guard, retaining append operations only for project-local actions. Cover both files/folders and quant/crop choices, including cancellation and a successful independent-project creation.

### 2. [P2] Do not consume the editor reveal before its animation-frame callback succeeds

Location: `apps/desktop/src/bioimage_app/web_ui/intake_quant.js:103–107`.

Trigger: click a matrix cell; before the scheduled animation frame, a new valid state snapshot changes the measurement markup (for example a busy-state transition or preview arrival). `afterRender()` clears `pendingEditor` at line 105 and captures the current DOM editor. The next render replaces that element. The callback then exits on `!editor.isConnected`, and subsequent renders cannot retry because the pending request was already consumed.

Impact: the intended editor reveal is lost even though project, row and lane are still the same. For the last cell of a 10×18 matrix, the user remains at the matrix position with the edit fields below the viewport and has to find them by additional scrolling. This does not change numerical data, and manual scrolling remains available, but it regresses the intended asynchronous selection/reveal behavior.

Independent controlled reproduction used the real WebEngine page, reduced motion and the same starting cell/position. Without intervening snapshots: main `scrollTop` changed 682→1243, editor top was 279.0625 and the first field bottom 699.25, inside main bottom 906. With `setState({busy:true}); setState({busy:false})` immediately after the cell click: `scrollTop` stayed 682, editor top 840.0625 and first field bottom 1260.25, below main bottom 906. The stronger reveal probe failed while the no-snapshot control passed. The first exploratory version checked only whether any editor header pixel was visible and passed both; that weak probe is not used as successful reveal evidence.

Requested correction: retain or reschedule the reveal until a matching current editor has actually been positioned. Resolve the current element inside the callback, recheck project/session/row/lane/surface there, and preserve the existing protections against a stale reveal moving another page or selection.

## Independent validation

All commands were run using `uv run --locked --no-sync` from the reviewed worktree, with the offscreen/disable-gpu variables above. No expected values, production tests, skips, timeouts or gates were weakened.

| Command after `uv run --locked --no-sync` | Result |
|---|---|
| `pytest tests/test_platform_home_scroll.py tests/test_project_navigation_session.py -q -o faulthandler_timeout=45` | 13 passed in 11.63s; exit 0 |
| `pytest tests/test_intake_web_ui.py::test_batch_curve_draft_cannot_fill_changed_source_or_geometry tests/test_intake_web_ui.py::test_batch_lane_overview_cards_open_bounded_editor_and_drag_preview tests/test_intake_web_ui.py::test_fig_matrix_shows_all_proteins_and_waits_for_selected_row_snapshot -q -o faulthandler_timeout=45` | 4 passed in 3.52s; exit 0 (one selected test is parametrized) |
| `pytest .local/t076_review_probes.py -k wb_home -q -s -o faulthandler_timeout=45` | 1 failed, 2 deselected in 2.53s; exit 1; finding 1 |
| `pytest .local/t076_review_probes.py -k reveal -q -s -o faulthandler_timeout=45` | 1 failed, 1 passed, 1 deselected in 4.76s; exit 1; finding 2 and control |

WebEngine printed GLES/shared-image diagnostics in these offscreen runs; processes completed with the actual exits above. These runs do not establish physical input, screen-reader, DPI, installer or general native-driver stability. Full CI, installation and scientific validation were not run by this reviewer. The reviewed product diff does not alter scientific computation or schema implementations.

Conclusion: **Changes requested** for the two reproducible issues above. This report does not cover subsequent fixes; those require review bound to their new commit.
