# Handoff Snapshot

## Current State

- Last updated: 2026-10-13
- Last agent: Codex
- Workspace root: bioimage-tools-platform
- Current objective: F-002，公开仓库并安装无需逐次提醒的规则校验，不开始业务开发。
- Current status: 规则加载器与本地 28 项测试通过，准备 GitHub 失败/成功路径验证；唯一任务状态见 work/tasks/F-002-rule-enforcement.md。
- Immediate next actions:
  - 验证规则回执缺失时阻止 PR 合并，补齐后通过四项检查并集成。
- Active files:
  - work/tasks/F-002-rule-enforcement.md
  - docs/runbooks/rule-enforcement.md
  - tooling/rule_context.py
- Blockers: 无；用户已明确授权公开，原套餐限制解除。
- Open questions:
  - 产品 P0、科学样本和干净机打包尚未授权启动，不是当前安装任务的未决需求。

## Recovery Summary

GitHub 已依用户要求公开；PR #1 已合并，main 包含原始 PDF 与治理规则。main-quality ruleset 25008972 active，要求 PR、四项指定 Actions 检查、禁止强推/删除、无 bypass actor。当前 F-002 在验证新门禁。尚未授权产品实现；不要把原方案任务模板当作开始产品工作的命令。
