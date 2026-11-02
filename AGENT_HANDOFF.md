# Agent Handoff Index

> Entry point for durable agent handoff memory in this repository.
> Read this file first, then follow the Recovery Reading Order below.

## Maintenance Contract

- Keep this file short. It is an index and recovery route, not a work log.
- Keep task status in `work/tasks/<ID>-*.md`; snapshot stores the current pointer and next actions, replacing stale fields.
- Store durable facts, decisions, validation, backlog, risks, and archives in the dedicated files listed below.
- Keep all content factual and repository-based. Mark uncertainty as `UNKNOWN`.
- Do not include secrets, credentials, long logs, full code blocks, or chat transcript dumps.
- Before final response for any non-trivial task, update the relevant `.agent-handoff/` files.

## Handoff Layout

- `.agent-handoff/snapshot.md`: Current objective, status, next actions, active files, blockers, and open questions.
- `.agent-handoff/workspace.md`: Repository map, entry points, test commands, docs, and stable project context.
- `.agent-handoff/decisions.md`: Important decisions with reasons and evidence.
- `.agent-handoff/work-log.md`: Recent operational work log.
- `.agent-handoff/validation.md`: Validation commands/checks, results, and caveats.
- `.agent-handoff/backlog.md`: Pending work and follow-ups.
- `.agent-handoff/risks.md`: Risks, blockers, unknowns, and user/source confirmations needed.
- `.agent-handoff/archive.md`: Compressed old history that is not part of normal startup.
- `.agent-handoff/archive/`: Automatically rotated history chunks, each capped at 128 KiB.

## Size And Rotation Policy

- Snapshot soft limit: 16 KiB or 240 lines. Hard limit: 32 KiB or 400 lines.
- Work log limit: 64 KiB or 30 dated sections. Validation limit: 64 KiB or 200 table rows.
- Backlog and risks limit: 32 KiB each. Only completed backlog items may be archived mechanically; risks require Agent review.
- After updating handoff state, run the installed `agent-handoff/scripts/maintain_handoff.py --repo <repo> --compact-if-needed` when available.
- Maintenance must archive before replacing, preserve complete records, and leave unparseable or semantically unsafe content unchanged for Agent repair.

## Recovery Reading Order

1. Read this file.
2. Read `.agent-handoff/snapshot.md`.
3. Read `.agent-handoff/risks.md`.
4. Read `.agent-handoff/backlog.md`.
5. Read `.agent-handoff/validation.md` only if validation state matters for the current task.
6. Read `.agent-handoff/decisions.md` only when changing architecture, behavior, dependencies, or prior decisions.
7. Read `.agent-handoff/workspace.md` only when orientation, commands, entry points, or subproject boundaries are needed.
8. Read `.agent-handoff/work-log.md` only when recent implementation details are needed.
9. Read `.agent-handoff/archive.md` only when explicitly needed for old context.

## Current Pointer

- 当前任务：[P002 成熟WB方法独立调用与真实成果对照](work/tasks/P-002-wb-headless-module.md)。P001已通过PR47合入main 29930f62；先读任务、研发总方案与阶段V0，再核对分支/HEAD。
- T082历史工程证据及科学/目标环境待办完整保留于其[任务](work/tasks/T-082-reliability-remediation.md)，不由V0自动关闭。
- 本轮本地工程交接：[T082 final-handoff](work/evidence/T-082/final-handoff.md)，区分冻结源码、隔离验收工件与后续交接HEAD；科学待办不由工程通过代替。
- 最近交付：[T081 R2](work/evidence/T-081/final-delivery.md)。当前源码/构建源码/主线集成/安装包区分见 [T082 baseline](work/evidence/T-082/baseline.md)。
- 旧 snapshot 保留于 `.agent-handoff/archive/T081-before-T082-snapshot.md`；原图、历史、既存 dirty 树及旧交付继续保护。
