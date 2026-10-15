# F-004：修复 Dependabot PR #5 的规则回执

- 状态：implementing
- base commit：221a2dff610554092a881fc396010f032b31ae33
- 初始 head：b826878279bbc5cd5b9c13cdb5e88408e46611be
- 授权：用户2026-10-15要求修复PR #5并验证通过。
- 目标：保留setup-uv固定SHA更新，补符合本仓库规则的任务、唯一回执和验证证据，使四项CI通过。
- 范围：work/tasks/F-004*、work/evidence/F-004、.agent-handoff；原PR仅改.github/workflows/quality.yml的两处setup-uv SHA。
- 必读：本分支AGENTS、handoff、module-map、development、rule-enforcement，以及upstream action.yml和新提交diff。
- 不变量：不降低CI、不豁免机器人、不引入本地产品分支改动，不改uv固定版本0.13.0或锁文件。
- 验收：check --all、smoke-env及rules-context本地通过；更新原PR后四项必需远程检查绑定同一head通过。
- 独立审查：未执行；这是基础设施依赖/证据修复，无产品代码。
- 回滚：revert本任务提交；不强推，不自动合并或发布。

## 已完成本地验证

check --all退出0：29测试/22.30秒；smoke-env退出0。见work/evidence/F-004/validation.md。待提交回执校验和远程四项CI，状态仍implementing。
