# T-063 采集组主流程与离线交付规划

- 状态：执行中；P0 PR21、P1/P2 PR22、T065裁剪修订PR23及T066快捷键PR24均四检查合main367ba2b。T067执行后分组失效已独审接受、PR26检查中；T068算法盘点/仓库导航独审无纠正项；T069独立发行/分组安装诊断已实现、绑定独审无新P0–P2，真实三目录正式链执行中。最终本地全门禁、后继PR集成、构建安装及新离线交付尚未完成。
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
