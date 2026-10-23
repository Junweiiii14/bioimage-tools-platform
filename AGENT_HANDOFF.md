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

- 当前任务：[T081](work/tasks/T-081-prominent-crop-stage-barrier.md)，固定N明显条带漏裁与全批裁剪barrier修复，活动树wb-lab-installer。T080已交付/PR41合入，当前状态以T081任务及其最终闭合谓词为准；本机R2交付已验，最终记录独审/CI/PR43合入仅据真实收据。
- T079旧快照保留在.agent-handoff/archive/T079-before-T080-snapshot.md，归档、dirty树及清理引用载荷继续保护。
- 旧T077指针归档.agent-handoff/archive/T077-before-T079-snapshot.md；视频研究是另一个已启动独立聊天，其wb-ui-system树整体保留。旧安装/生成物由T079按备份证明整理；T081保留旧包、未重复清理；旧dirty源码、原图/历史保持，不能沿用旧“安装保留”指针。
