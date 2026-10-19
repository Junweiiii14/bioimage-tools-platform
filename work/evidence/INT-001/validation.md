# INT001 validation

Base43d520f49507f12995eb3220beab9fd78f4adda7; original governance source0b786cb5aa0770eaf546d452e6a7a72469015756. Temporary integration tree only; no WB product files in this batch.

- uv sync --locked --all-groups: actual0; unchanged lock; .local/env-sync.log.
- Context before merge at221a2df, then after actual merge at43d520f with --integration: actual0. All rules/BASE exact contents matched already read primary sections after whitespace normalization; changed recovery files/task read directly. Scope . covers complete batch. RULE001 receipt immutable original source0b7 retained, no historical deletion or gate exemption.
- uv run --locked --no-sync python dev.py check --all: actual0, Ruff/format48/Pyright,44 governance tests/133.40s, .local/int001-fullcheck.txt. Negative rules cases cover missing/extra receipts, historical content/source/ancestry/base/current scope and rule drift. Product scan0 means product absent, not product acceptance. No Qt tests run in parallel with primary product gate.
- Snapshot updated only after archiving T050 old text. PR16 actual merged state stated; no false product or remote acceptance.
- Exact final committed rule validation, non-author review and four GitHub checks/merge are pending. No ruleset/lock/assertion/skip changes.
