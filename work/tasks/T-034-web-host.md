# T-034 Same-source desktop web host
Status: implementing. Parent T-033.
Scope: apps/desktop, tests, docs, work.
Implement bounded local Qt WebEngine/WebChannel presentation bridge over existing WB host; no numerical/schema changes. Preserve native advanced tools and lifecycle. Validate stale commands, local navigation, real import/output.

Implemented (2026-10-16): explicit same-source WebEngine shell, local-only navigation/request
filter, off-the-record profile, QWebChannel adapter, native advanced fallback and lifecycle.
No dependency, numerical formula or schema changes. Public display raster accessor committed
separately. Validation: ruff scoped and pyright scoped passed; pytest test_web_bridge.py and
test_project_start.py: 7 passed in 5.22s, exit 0. Tests cover real import/output/unchanged input,
preview encoding, stale crop rejection, original coordinate edit/undo, malformed/busy actions,
actual WebChannel handshake, local navigation restrictions, advanced hide and shell drainage.
Initial test source was incorrectly placed above the target project parent and correctly
rejected by production overlap protection; fixture moved to separate originals directory.
Full root integration/visual review remain parent T-033 responsibilities.

Follow-up: advanced analysis route and snapshot bitDepth added. File/folder imports into an
existing workspace append through public asynchronous APIs and automatically process new rows;
tests preserve project ID/workspace and original bytes across both append forms. Initial
combined multiple-WebEngine-window regression hit Windows native 0x80000003 during GC twice.
Lifecycle correction now explicitly deletes the page after backend drain and keeps its
profile application-owned until page destruction, then schedules profile deletion. Added
forced-GC cleanup checks. Final targeted bridge+project-start suite: 8 passed in 8.29s exit0;
scoped Ruff/Pyright passed. This reproduction/fix does not resolve historical unrelated Qt
native failures or establish standalone Windows packaging stability.

Independent-review corrections: workspace_opened now loads the saved WB document and its
verified evidence, matching native platform behavior. Attempting open_project with an active
workspace reports an explicit new-window instruction instead of silently ignoring it. Added
real save/close/reopen regression verifying project ID, rows, results and selected raster.
Confirm now advances to the next unreviewed source (wrapping), using existing asynchronous
preview selection; two consecutive confirmations covered. Final web suite 5 passed in 7.40s,
exit0; Ruff/Pyright passed. No frontend assets changed.
