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

- 当前交付：[T-069](work/tasks/T-069-grouped-intake-offline.md)，总计划[T-063](work/tasks/T-063-grouped-intake-delivery-plan.md)与[采集组计划](docs/wb-grouped-intake-plan.md)；新候选及边界见[交付记录](docs/wb-grouped-intake-delivery.md)。
- 活动树：`C:/Users/70236/.codex/worktrees/wb-grouped-intake/bioimage-tools-platform`；产品/安装冻结main6080867，收尾分支codex/grouped-intake-delivery；启动时重新核验。
- E0–E7及T061已经工程集成，见[验收索引](docs/wb-execution-acceptance.md)与任务。干净Win10/物理DPI/科学留出仍独立待验，不宣称正式发布。
- t051树T062原型与交接未提交资料保留，桌面批准原型为BioImage-导入分组交互原型/index.html。历史ResearchVault树不作为当前开发入口。
- 当前状态与下一步：`.agent-handoff/snapshot.md`；风险：`.agent-handoff/risks.md`；长期待办：`.agent-handoff/backlog.md`。
- 旧原生异常UNKNOWN与旧缓存清理被自动审批拒绝的残余继续保留；不得借新版本自动删除历史树、原图或项目结果。

## Project Rule Targets

- Codex / DeepSeek Harness project rules: `AGENTS.md`
- 本仓库未启用 Claude Code 专属配置。

## Closeout Rule

For non-trivial work, update the relevant files before final response:

- Always update `.agent-handoff/snapshot.md`.
- Update `.agent-handoff/work-log.md` when files or task status changed.
- Update `.agent-handoff/validation.md` when checks were run or intentionally skipped.
- Update `.agent-handoff/decisions.md` when a durable decision was made.
- Update `.agent-handoff/backlog.md` and `.agent-handoff/risks.md` when follow-ups, blockers, risks, or unknowns changed.
- Run the handoff maintenance check and resolve hard-limit findings before final response.




