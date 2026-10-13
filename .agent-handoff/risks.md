# Risks, Blockers, And Unknowns

## Current Blockers

- 无。用户已明确要求公开；仓库已公开，服务器 ruleset 已 active。此前私有套餐限制已解除。

## Current Risks

- P0 仍未进行，Qt/worker/standalone 和真实数据行为不因环境安装而成立。
- AST 边界检查仅检查直接导入；首个真实包必须启用 import-linter 与隔离 wheel 测试。
- 本任务作者自验不是独立审查；后续产品变更须有绑定 head 的审查证据。
- Python 3.12 生命周期至预计 2028-10，P0 需评估长期基线。
- 规则回执只证明加载器输出与版本一致，不能证明模型理解。普通 PR 可修改检查文件，管理员仍可修改服务器规则；不宣称防恶意篡改。

## Unknowns / Confirmations Needed

- 发布编译器最终路线、真实样本、签名/许可证、目标机性能和数据迁移：未实现产品阶段的待验证事项。
