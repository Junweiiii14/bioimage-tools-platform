# T076 independent incremental code review — Accepted

- Reviewer: independent delegated code reviewer, not the implementation author.
- Incremental range: `e7eb3a2851efa8b43bbefb34b5b56ce8738a39fc..d3aff15d53bf04c822976af0dd6b261f2b4dd6a1`.
- Branch: `codex/t076-platform-home-scroll`; verified HEAD was the requested `d3aff15d53bf04c822976af0dd6b261f2b4dd6a1`.
- Earlier complete-range review: `.local/t076-code-review-e7eb3a2.md` (base `7fcb8192ada7acf5695e74f23cbe010ffd862966`). Its failed reproductions remain historical evidence.
- Environment: Windows 11 build 26200, Python 3.12.14, PySide6 6.12.0, `QT_QPA_PLATFORM=offscreen`, `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`.
- Read all six changed files, surrounding native session/transition code and the current task. `PRODUCT.md` and untracked `docs/design/` changes remain outside this commit-bound code conclusion and were not modified by this reviewer.

## Finding disposition

### Prior P1 — Resolved

`desktop_session.js:87` now sends `new_images` / `new_folder` with the explicit workflow. `web_window.py` validates that workflow against `quant` and `review`, selects files/folders without mutating the current project, and calls `start_from_images()`, which reuses the existing project replacement transition. The existing project-local append branches remain unchanged. Cancelling the native picker leaves the current host untouched by inspection; a selected path reaches the existing busy/draft/dirty ordering rather than appending first.

The original independent runtime probe now produced `sameHost=True`, unchanged project ID `0c6adba911694ec890f3a885ae603f22`, row count 1, `stage='confirm_draft'`, and `draft=True`. This directly reverses the former unexpected row-count-2 append. The committed four-way files/folders × quant/review guard tests passed; their return/cancel path retains the current project. The committed successful quant-image creation path also passed and checks a distinct host/workspace/project plus preserved input/project directories.

The independent probe setup now explicitly waits for frontend `mode==='quant'` before constructing a user draft, because native import completion precedes initial frontend routing. Cleanup now answers the expected draft dialog before disposing the owned fixture. Neither adjustment changes the guard assertion or any timeout/expected numerical value.

### Prior P2 — Resolved

`intake_quant.js:102–113` retains the pending reveal until the animation-frame callback, rechecks pending/anchor/context/row/lane/surface at execution, and resolves the current editor DOM inside that callback. It consumes the pending reveal only after finding a matching current editor/main. This removes the old detached-element early exit while preserving stale-selection/page protection.

The original consecutive-snapshot probe now matches its no-snapshot control: main scrollTop 682→1243; editor top 279.0625; first-field bottom 699.25 inside main bottom 906. The committed regression also independently checks actual element hit-testing, and passed.

## Independent validation

Command from the requested worktree:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
$env:QTWEBENGINE_CHROMIUM_FLAGS='--disable-gpu'
uv run --locked --no-sync pytest tests/test_platform_home_scroll.py tests/test_project_navigation_session.py .local/t076_review_probes.py -q -s -o faulthandler_timeout=45
```

Result: **21 passed in 19.06s, process exit 0**. This includes both original independent counterexamples, the reveal control, the new four-path guard coverage and the existing navigation/scroll/lifecycle cases. Product source and committed tests were not modified by the reviewer. No test expectation, tolerance, timeout, skip or gate was relaxed.

WebEngine emitted offscreen GLES/shared-image diagnostics while the run completed successfully; this does not close historical native-driver/physical-input UNKNOWNs. Full CI, packaging, physical DPI/screen-reader and scientific validation were not run by this reviewer. The incremental diff does not alter scientific calculations, schema or dependency locks.

Conclusion: **Accepted** for this incremental commit-bound code review. Both earlier actionable findings are resolved, and no new actionable regression was identified in the increment. This acceptance plus the earlier complete-range inspection covers the reviewed T076 product changes through `d3aff15`; it does not claim completion of the task's separate visual, CI or delivery requirements.
