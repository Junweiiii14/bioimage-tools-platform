# T-063 采集组主流程与离线交付规划

- 状态：本轮P0–P8本机工程交付完成。分阶段产品PR21–24/26–28均四检查集成至main6080867；真实三目录主链/人工修正/新输出/重开、冻结检查、独立离线候选安装/双流程/PS5.1/SHA/manifest及绑定交付独审通过，细节与边界见[T069](T-069-grouped-intake-offline.md)和[交付记录](../../docs/wb-grouped-intake-delivery.md)。历史原生UNKNOWN、干净Win10/物理DPI与独立科学留出继续保留，不自动正式发布或扩其他工具。
- 授权：用户2026-10-20确认完整P0–P8计划并要求持续推进至独审、PR集成、新离线测试版；普通实现自主处理，只集中询问无法消解的数据歧义。
- 基线：main / HEAD `f3fb2ffe315af84980159745e5e6d5241b15a8c7`，分支 `codex/wb-grouped-intake`。
- 活动树：`C:/Users/70236/.codex/worktrees/wb-grouped-intake/bioimage-tools-platform`。t051树T062未提交资料保留原位；不在历史ResearchVault树开发。
- 范围：规划、任务和证据导航、README/交接。后继产品任务分别登记范围/规则回执。
- 完整实施与验收：[采集组交付计划](../../docs/wb-grouped-intake-plan.md)。状态唯一来源为任务文件，snapshot只保留当前指针。
- 不覆盖原图、参考裁剪、项目或历史结果；私图、模型和安装包不提交Git。旧缓存自动审批拒绝的残余保留，不绕过。

## 工作包与交付顺序

P0基线/需求映射→P1采集组与持久化→P2批准网格正式接入→P3既有主链衔接→P7必要验收→P8独审/集成/离线交付。P4快捷键在动作稳定后，P5先盘点后小步精简，P6仓库整理随阶段收尾。

## 当前验证

- Git状态/HEAD及GitHub API main核验：退出0，main同f3fb2ff；原t051 dirty保持。
- 受管工作树创建完成；Python3.12.14，`uv sync --locked --all-groups`退出0，锁文件未变。
- PR19实时核验MERGED，head9f5f94a、merge f3fb2ff、2026-10-20T06:28:21Z；四必需检查均SUCCESS。旧T061日志末尾“待验”为历史描述，最终事实以此实时读取为准。
- 本任务尚未运行产品测试/完整门禁、尚未独审或创建PR。

- P0离线policy与git diff --check实际0；交接容量检查changed0/warnings0/unresolved0。纯文档阶段不运行本地产品全门禁，不代表新产品通过。

- PR21 head52e7af6四检查SUCCESS，2026-10-20已精确merge main1625ae5；产品任务T064执行中，整体P0–P8尚未完成。
