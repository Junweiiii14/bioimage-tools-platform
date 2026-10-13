# Handoff Snapshot

## Current State

- Last updated: 2026-10-13
- Last agent: Codex
- Workspace root: bioimage-tools-platform
- Current objective: F-002，公开仓库并安装无需逐次提醒的规则校验，不开始业务开发。
- Current status: 配置与正反例验收完成；29 个本地测试及四项远程检查通过。交付 PR #2，最终集成状态以 GitHub PR 为准；任务见 work/tasks/F-002-rule-enforcement.md。
- Immediate next actions:
  - PR #2 已获用户集成授权；若尚未合并，核对最新 head 必需检查后完成集成。已合并则等待明确的新任务，不启动产品路线图。
- Active files:
  - work/tasks/F-002-rule-enforcement.md
  - docs/runbooks/rule-enforcement.md
  - tooling/rule_context.py
- Blockers: 无；用户已明确授权公开，原套餐限制解除。
- Open questions:
  - 产品 P0、科学样本和干净机打包尚未授权启动，不是当前安装任务的未决需求。

## Recovery Summary

GitHub 已依用户要求公开；PR #1 已合并，main 包含原始 PDF 与治理规则。main-quality ruleset 25008972 active，要求 PR、四项指定 Actions 检查、禁止强推/删除、无 bypass actor。F-002 已验证缺回执时其余检查通过仍 BLOCKED，补回执后全部通过；证据见 work/evidence/F-002/validation.md。尚未授权产品实现；不要把原方案任务模板当作开始产品工作的命令。
