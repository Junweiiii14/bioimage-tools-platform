# AI 非编码能力与规则可靠性补充

## 决策

2026-10-13 用户要求公开仓库并直接建立减少人工监督的机制。PR #1 已合并，仓库可见性已改 public；当前主分支已启用 ruleset 25008972。F-002 增加规则上下文回执，并将其加入必需检查。

保留当前模型和 medium 项目默认强度。主要优化方向是确定性加载、过期失效、显式任务范围和服务端验收，不用未测的模型切换来承诺稳定性或速度。

## 漏读的实际原因

本会话根目录是父工作区，目标仓库是其子目录。官方 AGENTS 发现算法不会自动向下遍历全部子项目；从根启动也不会自动加载将来修改的全部子目录规则。另有 override 优先级、长度限制和已有会话启动指令不刷新等因素。

已补父工作区路由；本仓库规则加载器显式收集范围内嵌套 AGENTS/override，展示基线与当前规则差异。CI 校验回执与本 PR 的 base/head，不依赖作者在 PR 正文写“已经读过”。普通克隆无需联网模型 API 即可执行校验。

## 备选取舍

| 方法 | 决定 | 理由 |
|---|---|---|
| 只增加 AGENTS 长度 | 不采用 | 更易截断，也无法阻止未通过的变更合并 |
| SessionStart/compact hook | 记录为可选，不作为已启用机制 | 官方支持，但非托管定义必须经宿主信任；不绕过信任流程 |
| 批量安装调研插件 | 不采用 | 已有 Web/Docs/PDF/文档工具，新增入口不能替代证据标准 |
| 自建持令牌 AI 审查机器人 | 不采用 | 带来服务运维、凭据和费用，不是当前最小可靠增益 |
| 确定性脚本 + 必需 CI + ruleset | 采用 | 自动拒绝缺失、过期和超范围的规则记录，结果可复现 |

非编码能力清单与研究产物要求见 [研究规范](../research-protocol.md)。非编码不代表不验证：需求用验收条件约束、科学结论用参考样例核对、性能用测量证明、跨会话状态用仓库事实恢复。

## 证据和限制

规则回执能被人为生成，不能证明模型的认知状态。CI 工作流也属于可修改的仓库文件，规则更改需要审查；管理员可编辑 ruleset。自然语言约束未全部转为程序检查，不能声称所有违规均被阻止。用户无需反复提醒读取规则，但业务决策与产品里程碑审查仍保留。

运行实测见 `work/evidence/F-002/validation.md`。来源为实际读取的 [Codex AGENTS 文档](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[hooks 文档](https://learn.chatgpt.com/docs/hooks)、[GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets) 与 [PR 事件安全](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)。最后一项也说明 public 的 pull_request_target 默认事件策略将收紧，因此本项目使用普通只读 pull_request。
