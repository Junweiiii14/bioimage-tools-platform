# E7 P0 stage integration validation

Actual base7730bcd6bc6889567bcb01d772e4368378caf6d6 (governance PR7 merged), original source66e0240bc211e5d9f08e1019cf686df249adbd97. Source P0 unchanged; README/decision/snapshot conflicts reconciled without discarding either side, P0 snapshot archived before replacement.

- Premerge context at original0b7, postmerge context at actualmain773 with scope . / --integration: actual0. Current/BASE rules and task/recovery read; unchanged sections matched earlier reads. Sole current manifest is existing SYNC001; original T002 receipt source d813508 retained, previous INT001 manifest comes from main unchanged. No deletion/renaming of receipts or extra current manifest.
- uv sync --locked --all-groups0; Ruff0/format73/Pyright0. Pure test command explicitly selecting rule_context,policy_digest,boundaries,p0_core:47passed/154.01s/actual0, .local/sync001-pure-tests.txt. Local full check / test_p0_process (3 Qt tests) NOT RUN while primary Qt suite active; no skips or test/gate modifications. Server required full checks remain mandatory before merge.
- P0 is disposable technical code, not WB numerical/scientific or installer acceptance. Historical Esc stop, clean Windows and physical/DPI gaps remain. New installer build is separate primary T060 work.
- Final committed rule validation and non-author review / latest four server checks pending. Only merge integration preserves immutable source ancestors; no squash/rebase.
