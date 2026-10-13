# 自动加载与规则门禁

## 日常使用

从本仓库根创建 Codex 任务。根 `AGENTS.md` 自动进入项目指令；从父工作区启动时遵循父目录项目路由，进入本仓库再读取规则。已有会话不会因文件变更就重新构造全部启动指令，必须显式重读。

开始修改前，AI 建立任务文档，然后执行（例）：

```powershell
uv run --locked python dev.py context --task F-002 --scope . --record
```

`--scope` 可重复，建议写目标目录、任务/证据和需要更新的交接目录。`.` 适用于跨仓库治理变更；会加载所有自有嵌套指令。命令输出通用规则、适用目录规则、任务和最新交接；版本不同还输出 main 上的旧规则。

将生成的 `work/evidence/<ID>/rules-context.json` 随 PR 提交。它记录 main 基线、修改范围和规则内容摘要。更新 main、改规则、扩大修改范围或新建目录规则后重新执行。生成后仍要读命令输出，不能重定向并声称已理解。

## 自动阻止什么

GitHub 的 `rules-context` 必须通过：缺回执、错误任务、旧基线、遗漏新规则、规则版本过期、超出已加载范围都会失败。已有 Windows/Linux 检查执行格式、类型、边界与测试；桌面依赖检查验证环境。main 必须经 PR，禁止强推/删除，无 bypass actor，检查结果只接受 GitHub Actions 应用。

这些门禁不要求用户逐次提醒 AI。失败日志直接给 AI 修复方法。Dependabot 等机器人也须补符合要求的任务/证据，不设静默豁免；是否合并仍按具体任务授权，不能因 CI 通过就擅自发布或推进产品路线图。

## 明确的能力边界

回执只证明脚本输出过指定版本的规则，不证明模型阅读、理解或遵守每一条自然语言要求。已编码的不变量由检查强制执行；科学语义与体验仍需参考测试和独立审查。保持每次任务范围小，新增高价值规则同步考虑能否转成测试。

本仓库使用普通 `pull_request` 的只读工作流，不启用 `pull_request_target` 或对 fork 执行有凭据的代码。PR 可以修改自己的 workflow/检查脚本，因此这不是对恶意维护者的不可篡改合规系统。修改门禁必须单独解释并审查；拥有仓库管理员身份的人仍可更改服务器规则。本次不购买企业组织方案或部署持有高权限令牌的自建机器人。

Codex 官方 SessionStart/compact hook 支持注入上下文，但非托管 hook 需要用户信任具体定义。本方案不绕过 hook 信任，不依赖需要逐机确认的 hook；自动发现 + 加载器 + GitHub 门禁在普通克隆中即可使用。

## 官方依据（2026-10-13 核验）

- [Codex AGENTS 发现规则](https://learn.chatgpt.com/docs/agent-configuration/agents-md)：按根到当前目录发现，存在覆盖文件与长度上限；不会自动遍历全部后代。
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)：项目层信任及单个 hook 定义信任，SessionStart 可在恢复/压缩后补充上下文。
- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)：公开仓库可用，支持 PR 与必需状态检查。
- [GitHub PR 事件安全](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)：本项目不需要 elevated PR 工作流。
