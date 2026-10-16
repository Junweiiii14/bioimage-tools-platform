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
