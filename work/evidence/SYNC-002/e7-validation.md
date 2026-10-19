# E7 WB core dependency validation

Actual predecessor main: e09ba01412edd8e718d39e2ae0ed36a65b8d817a (PR3 merged after four required server checks and bound non-author review). Original branch dd929960c4886e882d282490fd9ed59fdc8d2e50; merged main a1aeedb. Scope . context loaded/read before integration and again against actual main after merge; all historical receipts retained through explicit manifest.

Windows local auxiliary environment: uv sync --locked --all-groups actual0. Initial static invocation before syncing the P0-only environment produced missing-product-import type errors (1957), not an accepted check. After the locked environment sync: Ruff check0, Ruff format0, Pyright0 errors. No lock/dependency edit or expectation change. Product source/tests remain identical to dd92996; only main planning/governance history, current task/evidence and conflict-resolved handoff/README change.

Local full pytest/Qt/wheels NOT RUN in this batch: primary product Qt full check is active and local Qt is serial. Four exact-base/head server checks and bound non-author review are required before merge. Prior 192-test product record is historical and does not substitute this batch CI. Scientific truth, original native-exit UNKNOWN, clean Windows/physical DPI remain pending. Original inputs/history/old installations untouched.
