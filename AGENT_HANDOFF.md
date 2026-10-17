# Agent Handoff Index

> Entry point for durable agent handoff memory in this repository.
> Read this file first, then follow the Recovery Reading Order below.

## Maintenance Contract

- Keep this file short. It is an index and recovery route, not a work log.
- Store current task state in `.agent-handoff/snapshot.md`; replace stale fields instead of appending historical snapshots.
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

- Last updated: 2026-10-17
- Active development checkout: `C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform`, branch `codex/t043-gate-and-staged-sync`; confirm current HEAD before use.
- Current desktop entry: this checkout's `Start-BioImage.ps1`, also linked by desktop “BioImage WB 工作台（当前开发）”. Default and historical normal CLI options open `WebWorkbenchWindow`.
- The original ResearchVault checkout preserves dirty historical development and old results. Do not launch it as the current product or overwrite it to synchronize versions. Compatibility tests run offscreen; explicit legacy windows are not the normal workbench.
- Current state file: `.agent-handoff/snapshot.md`
- Primary next-action source: `.agent-handoff/snapshot.md`
- Risk source: `.agent-handoff/risks.md`
- Backlog source: `.agent-handoff/backlog.md`

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
